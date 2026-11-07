# SPDX-License-Identifier: AGPL-3.0-or-later
"""Train and evaluate one private M2M100 adapter across English/French/Somali."""

from __future__ import annotations

import hashlib
import json
import math
import socket
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from .config import LabConfig
from .m2m100_training import MAX_SEQUENCE_LENGTH
from .m2m100_training import MODEL_ID
from .m2m100_training import MODEL_REVISION
from .m2m100_training import _preflight
from .m2m100_training import _sha256
from .m2m100_training import _thermal_callback_type
from .m2m100_training import _verify_model_bundle
from .sources import read_owner_registry
from .sources import verify_approved_source

FRENCH_SOURCE_ID = "opus-infopankki-fr-so"
FRENCH_DATASET_REVISION = "82141c0274b1ec8e05e49e16"
FRENCH_OVERSAMPLE = 4
SUPPORTED_PAIRS = {"en-so": ("en", "so"), "fr-so": ("fr", "so")}


def _safe_experiment_id(value: str) -> bool:
    return bool(
        value
        and value not in {".", ".."}
        and Path(value).name == value
        and "/" not in value
        and "\\" not in value
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def candidate_training_complete(
    metadata: dict, training_report: dict | None, adapter_path: Path
) -> bool:
    """Allow held-out scoring only for a complete, private adapter artifact."""
    pair_fingerprints = (
        metadata.get("fingerprint", {}).get("pair_data", {}).get("pairs", {})
    )
    return bool(
        metadata.get("automatic_promotion") is False
        and "fr-so" in pair_fingerprints
        and training_report
        and training_report.get("status") == "TRAINED_RESEARCH_CANDIDATE"
        and adapter_path.is_file()
    )


def _source_authorization_record(source: dict) -> dict:
    """Capture training permission separately from immutable source manifests."""
    approval = source.get("private_owner_approval") or {}
    rights = source.get("rights", {})
    return {
        "source_id": source["source_id"],
        "license": source.get("license"),
        "revision": source.get("revision"),
        "rights_status": source.get("rights_status"),
        "owner_approved": source.get("owner_approved") is True,
        "approval_date": approval.get("approved_utc"),
        "approval_scope": approval.get("scope"),
        "rights": {
            key: rights.get(key)
            for key in (
                "download",
                "process",
                "train",
                "evaluate",
                "redistribute_raw",
                "redistribute_derivative",
                "redistribute_weights",
            )
        },
    }


def build_route_examples(
    english_rows: list[dict],
    french_rows: list[dict],
    *,
    french_repeat: int = FRENCH_OVERSAMPLE,
) -> list[dict]:
    """Interleave both directions for each approved pair in one shared model."""
    if not 1 <= french_repeat <= 12:
        raise ValueError("French repeat must be between 1 and 12.")
    examples = []
    for source_rows, route, repeat in (
        (english_rows, SUPPORTED_PAIRS["en-so"], 1),
        (french_rows, SUPPORTED_PAIRS["fr-so"], french_repeat),
    ):
        for row in source_rows:
            source = row.get("source_text")
            target = row.get("target_text")
            if not isinstance(source, str) or not isinstance(target, str):
                raise TypeError("Parallel text fields must be strings.")
            if not source.strip() or not target.strip():
                raise ValueError("Parallel text fields cannot be empty.")
            for _ in range(repeat):
                examples.extend(
                    (
                        {
                            "source_text": source,
                            "target_text": target,
                            "source_language": route[0],
                            "target_language": route[1],
                        },
                        {
                            "source_text": target,
                            "target_text": source,
                            "source_language": route[1],
                            "target_language": route[0],
                        },
                    )
                )
    if not examples:
        raise ValueError("At least one approved parallel pair is required.")
    return examples


def _examples_by_direction(examples: list[dict]) -> dict[str, list[dict]]:
    """Group examples so shared-model validation reports every route separately."""
    grouped: dict[str, list[dict]] = {}
    for item in examples:
        source = item.get("source_language")
        target = item.get("target_language")
        if (source, target) not in {
            ("en", "so"),
            ("so", "en"),
            ("fr", "so"),
            ("so", "fr"),
        }:
            raise ValueError("Validation examples contain an unsupported route.")
        grouped.setdefault(f"{source}-{target}", []).append(item)
    if not grouped:
        raise ValueError("At least one validation example is required.")
    return dict(sorted(grouped.items()))


def _macro_validation_loss(validation_by_direction: dict[str, dict]) -> float:
    """Average route losses equally so large datasets cannot dominate the gate."""
    if not validation_by_direction:
        raise ValueError("At least one directional validation loss is required.")
    losses = [float(item["loss"]) for item in validation_by_direction.values()]
    if any(not math.isfinite(loss) for loss in losses):
        raise ValueError("Directional validation losses must be finite.")
    return math.fsum(losses) / len(losses)


def _directed_test_examples(rows: list[dict], source_lang: str, target_lang: str):
    """Build one test direction while retaining stable source row identities."""
    if (source_lang, target_lang) not in {
        ("en", "so"),
        ("so", "en"),
        ("fr", "so"),
        ("so", "fr"),
    }:
        raise ValueError("Unsupported evaluation route.")
    result = []
    for row in rows:
        row_source = row.get("source_language")
        row_target = row.get("target_language")
        if row_source is None and row_target is None:
            # The English mixture uses canonical English -> Somali text fields.
            row_source, row_target = "en", "so"
        if (row_source, row_target) == (source_lang, target_lang):
            source, target = row["source_text"], row["target_text"]
        elif (row_source, row_target) == (target_lang, source_lang):
            source, target = row["target_text"], row["source_text"]
        else:
            raise ValueError("Evaluation row language pair does not match route.")
        result.append(
            {
                "source_text": source,
                "target_text": target,
                "source_language": source_lang,
                "target_language": target_lang,
                "record_id": row.get("record_id"),
                "source_id": row.get("source_id"),
            }
        )
    return result


def _direction_batches(rows: list[dict], batch_size: int = 4):
    """Yield bounded batches without crossing a source/target language boundary."""
    if batch_size < 1:
        raise ValueError("Batch size must be positive.")
    batch = []
    direction = None
    for row in rows:
        row_direction = (row["source_language"], row["target_language"])
        if batch and (row_direction != direction or len(batch) >= batch_size):
            yield batch
            batch = []
        direction = row_direction
        batch.append(row)
    if batch:
        yield batch


def _load_french_split(workspace: Path, name: str) -> tuple[dict, list[dict]]:
    if name not in {"train", "validation", "test"}:
        raise ValueError("Unknown French–Somali split.")
    root = (
        workspace
        / "data"
        / "prepared"
        / "infopankki-multilingual"
        / FRENCH_DATASET_REVISION
    )
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Prepared French–Somali split manifest is missing.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("dataset_revision") != FRENCH_DATASET_REVISION
        or manifest.get("source_revision") != "52339513e7ee4d1896c804ca4f61d7ee3b35ea93"
        or manifest.get("license") != "CC-BY-4.0"
    ):
        raise ValueError("French–Somali split identity does not match its pin.")
    path = root / f"{name}.jsonl"
    if _sha256(path) != manifest.get("split_sha256", {}).get(path.name):
        raise ValueError(f"Prepared French–Somali {name} split hash failed.")
    rows = [row for row in _read_jsonl(path) if row.get("source_language") == "fr"]
    if any(
        row.get("target_language") != "so"
        or row.get("source_id") != FRENCH_SOURCE_ID
        or row.get("license") != "CC-BY-4.0"
        for row in rows
    ):
        raise ValueError("French split contains unexpected pair provenance.")
    return manifest, rows


def load_training_splits(workspace: Path, config: LabConfig) -> tuple[dict, ...]:
    """Load only approved English/French train and validation rows."""
    if not config.training_enabled:
        raise PermissionError("Training is disabled in the active lab config.")
    registry_path = workspace / "registry" / "sources.jsonl"
    registry_records = read_owner_registry(registry_path)
    source = next(
        (row for row in registry_records if row.get("source_id") == FRENCH_SOURCE_ID),
        None,
    )
    if source is None:
        raise PermissionError("French–Somali source approval is missing.")
    verify_approved_source(source, set(config.approved_source_ids), purpose="train")
    from .mixture_data import prepare_marian_mixture

    english_manifest, english_train, english_validation, _ = prepare_marian_mixture(
        workspace, config
    )
    french_manifest, french_train = _load_french_split(workspace, "train")
    _, french_validation = _load_french_split(workspace, "validation")
    if (
        not english_train
        or not english_validation
        or not french_train
        or not french_validation
    ):
        raise ValueError("Both language pairs require train and validation rows.")
    source_by_id = {row["source_id"]: row for row in registry_records}
    training_source_ids = sorted(
        {FRENCH_SOURCE_ID, *english_manifest["source_revisions"]}
    )
    source_authorizations = {}
    for source_id in training_source_ids:
        authorized_source = source_by_id.get(source_id)
        if authorized_source is None:
            raise PermissionError(f"Approved source record is missing: {source_id}")
        verify_approved_source(
            authorized_source,
            set(config.approved_source_ids),
            purpose="train",
            allow_noncommercial=config.allow_noncommercial_training,
        )
        source_authorizations[source_id] = _source_authorization_record(
            authorized_source
        )
    metadata = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "source_registry_sha256": _sha256(registry_path),
        "source_authorizations": source_authorizations,
        "pairs": {
            "en-so": {
                "dataset_revision": english_manifest["dataset_revision"],
                "train_sha256": english_manifest["split_sha256"]["train.jsonl"],
                "validation_sha256": english_manifest["split_sha256"][
                    "validation.jsonl"
                ],
                "training_rows": len(english_train),
                "validation_rows": len(english_validation),
                "attribution": english_manifest["attribution"],
            },
            "fr-so": {
                "dataset_revision": FRENCH_DATASET_REVISION,
                "source_revision": french_manifest["source_revision"],
                "train_sha256": french_manifest["split_sha256"]["train.jsonl"],
                "validation_sha256": french_manifest["split_sha256"][
                    "validation.jsonl"
                ],
                "training_rows": len(french_train),
                "validation_rows": len(french_validation),
                "attribution": french_manifest["attribution"],
            },
        },
        "french_repeat": FRENCH_OVERSAMPLE,
    }
    return (
        metadata,
        build_route_examples(english_train, french_train),
        build_route_examples(english_validation, french_validation, french_repeat=1),
    )


def train_multilingual_lora(
    workspace: Path,
    config: LabConfig,
    *,
    model_dir: Path,
    experiment_id: str,
    resume: bool = False,
    max_gpu_fraction: float = 0.60,
    learning_rate: float = 5e-5,
    num_train_epochs: float = 1.0,
    lora_rank: int = 8,
    initial_adapter_experiment_id: str | None = None,
) -> dict:
    """Train a private resumable LoRA across English↔Somali and French↔Somali."""
    try:
        import torch
        from peft import LoraConfig
        from peft import PeftModel
        from peft import TaskType
        from peft import get_peft_model
        from transformers import DataCollatorForSeq2Seq
        from transformers import M2M100ForConditionalGeneration
        from transformers import M2M100Tokenizer
        from transformers import Seq2SeqTrainer
        from transformers import Seq2SeqTrainingArguments
        from transformers import TrainerCallback
        from transformers.trainer_utils import get_last_checkpoint
    except ImportError as error:
        raise RuntimeError(
            "Install the private training runtime before training."
        ) from error
    if not _safe_experiment_id(experiment_id):
        raise ValueError("Experiment ID must be a safe path component.")
    if not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError("Learning rate must be finite and positive.")
    if not math.isfinite(num_train_epochs) or not 0.25 <= num_train_epochs <= 3:
        raise ValueError("Epochs must be between 0.25 and 3.")
    if not 1 <= lora_rank <= 64:
        raise ValueError("LoRA rank must be between 1 and 64.")
    parent_adapter_dir = None
    parent_adapter_sha256 = None
    if initial_adapter_experiment_id is not None:
        if not _safe_experiment_id(initial_adapter_experiment_id):
            raise ValueError("Initial adapter experiment ID must be path-safe.")
        parent_experiment_dir = (
            workspace / "experiments" / initial_adapter_experiment_id
        )
        parent_metadata_path = parent_experiment_dir / "experiment.json"
        parent_report_path = parent_experiment_dir / "training-report.json"
        parent_adapter_dir = parent_experiment_dir / "adapter-final"
        parent_adapter_path = parent_adapter_dir / "adapter_model.safetensors"
        if not parent_metadata_path.is_file() or not parent_report_path.is_file():
            raise FileNotFoundError(
                "Initial adapter experiment artifacts are incomplete."
            )
        parent_metadata = json.loads(parent_metadata_path.read_text(encoding="utf-8"))
        parent_report = json.loads(parent_report_path.read_text(encoding="utf-8"))
        if parent_metadata.get(
            "experiment_id"
        ) != initial_adapter_experiment_id or not candidate_training_complete(
            parent_metadata, parent_report, parent_adapter_path
        ):
            raise PermissionError(
                "Initial adapter is not a complete private candidate."
            )
        parent_adapter_sha256 = _sha256(parent_adapter_path)
    from .resources import gpu_preflight

    preflight = gpu_preflight(
        max_vram_gib=config.max_vram_gib,
        max_temperature_c=config.gpu_max_temp_c,
        minimum_free_gib=config.min_free_vram_gib,
    )
    max_gpu_fraction = min(max_gpu_fraction, preflight["max_process_fraction"])
    if max_gpu_fraction < 0.25:
        raise RuntimeError("Configured GPU memory cap is too restrictive for M2M100.")
    hardware = _preflight(torch, max_gpu_fraction=max_gpu_fraction)
    model_record = _verify_model_bundle(workspace, model_dir)
    data_manifest, train_examples, validation_examples = load_training_splits(
        workspace, config
    )
    fingerprint = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_files_sha256": {
            item["name"]: item["sha256"] for item in model_record["files"]
        },
        "pair_data": data_manifest,
        "train_examples_sha256": hashlib.sha256(
            json.dumps(train_examples, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "validation_examples_sha256": hashlib.sha256(
            json.dumps(validation_examples, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
    }
    settings = {
        "learning_rate": learning_rate,
        "num_train_epochs": num_train_epochs,
        "lora_rank": lora_rank,
        "french_repeat": FRENCH_OVERSAMPLE,
        "validation_reporting": "direction_macro_v1",
        "initial_adapter_experiment_id": initial_adapter_experiment_id,
        "initial_adapter_sha256": parent_adapter_sha256,
    }
    experiment_dir = workspace / "experiments" / experiment_id
    checkpoint_dir = workspace / "checkpoints" / experiment_id
    metadata_path = experiment_dir / "experiment.json"
    adapter_dir = experiment_dir / "adapter-final"
    created = datetime.now(UTC).isoformat()
    if metadata_path.exists():
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        if (
            previous.get("fingerprint") != fingerprint
            or previous.get("training_settings") != settings
        ):
            raise ValueError(
                "Existing experiment inputs/settings changed; use a new ID."
            )
        if not resume:
            raise FileExistsError("Experiment exists; pass resume or choose a new ID.")
        created = previous.get("created_utc", created)
    elif resume:
        raise FileNotFoundError("No experiment metadata exists to resume.")
    experiment_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        metadata_path,
        {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "created_utc": created,
            "fingerprint": fingerprint,
            "training_settings": settings,
            "training_rows": len(train_examples),
            "validation_rows": len(validation_examples),
            "hardware": hardware,
            "attribution": {
                key: value["attribution"]
                for key, value in data_manifest["pairs"].items()
            },
            "automatic_promotion": False,
            "weight_redistribution": (
                "not approved; retain CC BY attribution and review before release"
            ),
        },
    )
    tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)

    def tokenize(examples):
        encoded_rows = []
        for item in examples:
            tokenizer.src_lang = item["source_language"]
            tokenizer.tgt_lang = item["target_language"]
            encoded_rows.append(
                tokenizer(
                    item["source_text"],
                    text_target=item["target_text"],
                    max_length=MAX_SEQUENCE_LENGTH,
                    truncation=True,
                )
            )
        return encoded_rows

    model = M2M100ForConditionalGeneration.from_pretrained(
        str(model_dir),
        local_files_only=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    )
    model.config.use_cache = False
    if parent_adapter_dir is not None:
        adapter_config = json.loads(
            (parent_adapter_dir / "adapter_config.json").read_text(encoding="utf-8")
        )
        if adapter_config.get("r") != lora_rank:
            raise ValueError("Initial adapter rank does not match the requested rank.")
        model = PeftModel.from_pretrained(
            model, str(parent_adapter_dir), is_trainable=True
        )
    else:
        model = get_peft_model(
            model,
            LoraConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                r=lora_rank,
                lora_alpha=2 * lora_rank,
                lora_dropout=0.05,
                target_modules=["q_proj", "v_proj"],
                bias="none",
            ),
        )
    collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer, model=model, label_pad_token_id=-100, pad_to_multiple_of=8
    )
    args = Seq2SeqTrainingArguments(
        output_dir=str(checkpoint_dir),
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.03,
        logging_steps=10,
        eval_strategy="no",
        save_strategy="steps",
        save_steps=500,
        save_total_limit=3,
        fp16=True,
        dataloader_num_workers=0,
        report_to=[],
        seed=1729,
        data_seed=1729,
        label_names=["labels"],
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=tokenize(train_examples),
        data_collator=collator,
        processing_class=tokenizer,
    )
    thermal_callback_type = _thermal_callback_type
    from .resources import gpu_temperature_c

    thermal_callback = thermal_callback_type(
        TrainerCallback, config.gpu_max_temp_c, gpu_temperature_c
    )()
    trainer.add_callback(thermal_callback)

    class RuntimeBudgetCallback(TrainerCallback):
        stop_reason = None

        def __init__(self):
            self.started = time.monotonic()
            self.limit = max(60, config.max_runtime_hours * 3600 - 60)

        def on_step_end(self, args, state, control, **kwargs):
            if time.monotonic() - self.started >= self.limit:
                self.stop_reason = "Configured runtime limit reached."
                control.should_save = True
                control.should_training_stop = True
            return control

    runtime_callback = RuntimeBudgetCallback()
    trainer.add_callback(runtime_callback)
    checkpoint = get_last_checkpoint(str(checkpoint_dir)) if resume else None
    started = time.monotonic()
    try:
        result = trainer.train(resume_from_checkpoint=checkpoint)
        trainer.save_model(str(adapter_dir))
        trainer.save_state()
    except Exception as error:
        _write_json(
            experiment_dir / "training-failure.json",
            {
                "status": "TRAINING_FAILED",
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "resume_available": get_last_checkpoint(str(checkpoint_dir))
                is not None,
            },
        )
        raise
    validation_by_direction = {}
    validation_error = None
    try:
        for direction, examples in _examples_by_direction(validation_examples).items():
            metrics = trainer.evaluate(
                eval_dataset=tokenize(examples),
                metric_key_prefix=f"eval_{direction.replace('-', '_')}",
            )
            loss_key = f"eval_{direction.replace('-', '_')}_loss"
            loss = metrics.get(loss_key)
            if loss is None or not math.isfinite(float(loss)):
                raise RuntimeError(
                    f"Validation loss is missing or invalid for {direction}."
                )
            validation_by_direction[direction] = {
                "examples": len(examples),
                "loss": float(loss),
            }
    except (
        KeyError,
        OSError,
        OverflowError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        _write_json(
            experiment_dir / "validation-failure.json",
            {
                "status": "DIRECTIONAL_VALIDATION_FAILED",
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "directions_completed": sorted(validation_by_direction),
            },
        )
        validation_error = f"{type(error).__name__}: {str(error)[:1000]}"
    report = {
        "status": "PAUSED_RESOURCE"
        if thermal_callback.stop_reason or runtime_callback.stop_reason
        else "TRAINED_RESEARCH_CANDIDATE",
        "experiment_id": experiment_id,
        "fingerprint": fingerprint,
        "training_settings": settings,
        "training_examples": len(train_examples),
        "validation_examples": len(validation_examples),
        "completed_steps": trainer.state.global_step,
        "planned_steps": trainer.state.max_steps,
        "train_metrics": result.metrics,
        "validation_status": "complete" if validation_error is None else "failed",
        "validation_error": validation_error,
        "validation_by_direction": validation_by_direction,
        "validation_loss": (
            _macro_validation_loss(validation_by_direction)
            if validation_error is None and validation_by_direction
            else None
        ),
        "validation_loss_aggregation": (
            "unweighted macro-average of directional token losses"
        ),
        "resource_stop_reason": (
            thermal_callback.stop_reason or runtime_callback.stop_reason
        ),
        "hardware": hardware,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "adapter_directory": str(adapter_dir),
        "parent_experiment_id": initial_adapter_experiment_id,
        "parent_adapter_sha256": parent_adapter_sha256,
        "automatic_promotion": False,
        "linguistic_review": "not performed",
    }
    _write_json(experiment_dir / "training-report.json", report)
    del trainer, model
    import gc

    gc.collect()
    torch.cuda.empty_cache()
    return report


def evaluate_multilingual_lora(
    workspace: Path,
    config: LabConfig,
    *,
    model_dir: Path,
    experiment_id: str,
    run_id: str,
) -> dict:
    """Compare a frozen adapter with its base on the pair-specific held-out tests."""
    try:
        import torch
        from peft import PeftModel
        from sacrebleu.metrics import BLEU
        from sacrebleu.metrics import CHRF
        from transformers import M2M100ForConditionalGeneration
        from transformers import M2M100Tokenizer
    except ImportError as error:
        raise RuntimeError(
            "Install the private training runtime before evaluation."
        ) from error
    if not run_id or run_id != Path(run_id).name:
        raise ValueError("Run ID must be a safe path component.")
    source = next(
        (
            row
            for row in read_owner_registry(workspace / "registry" / "sources.jsonl")
            if row.get("source_id") == FRENCH_SOURCE_ID
        ),
        None,
    )
    if source is None:
        raise PermissionError("French–Somali evaluation approval is missing.")
    verify_approved_source(source, set(config.approved_source_ids), purpose="evaluate")
    experiment_dir = workspace / "experiments" / experiment_id
    metadata_path = experiment_dir / "experiment.json"
    adapter_path = experiment_dir / "adapter-final" / "adapter_model.safetensors"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    training_report_path = experiment_dir / "training-report.json"
    training_report = (
        json.loads(training_report_path.read_text(encoding="utf-8"))
        if training_report_path.is_file()
        else None
    )
    if not candidate_training_complete(metadata, training_report, adapter_path):
        raise PermissionError("A frozen private candidate adapter is required.")
    from .mixture_data import prepare_marian_mixture

    _, _, _, english_test = prepare_marian_mixture(workspace, config)
    french_manifest, french_test = _load_french_split(workspace, "test")
    english_examples = _directed_test_examples(
        english_test, "en", "so"
    ) + _directed_test_examples(english_test, "so", "en")
    french_examples = _directed_test_examples(
        french_test, "fr", "so"
    ) + _directed_test_examples(french_test, "so", "fr")
    route_order = {("en", "so"): 0, ("so", "en"): 1, ("fr", "so"): 2, ("so", "fr"): 3}
    examples = sorted(
        english_examples + french_examples,
        key=lambda item: route_order[
            (item["source_language"], item["target_language"])
        ],
    )
    model_record = _verify_model_bundle(workspace, model_dir)
    from .resources import gpu_preflight

    preflight = gpu_preflight(
        max_vram_gib=config.max_vram_gib,
        max_temperature_c=config.gpu_max_temp_c,
        minimum_free_gib=config.min_free_vram_gib,
    )
    max_gpu_fraction = min(0.60, preflight["max_process_fraction"])
    if max_gpu_fraction < 0.25:
        raise RuntimeError("Configured GPU memory cap is too restrictive for M2M100.")
    hardware = _preflight(torch, max_gpu_fraction=max_gpu_fraction)
    tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)
    base = M2M100ForConditionalGeneration.from_pretrained(
        str(model_dir),
        local_files_only=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    ).eval()
    candidate = PeftModel.from_pretrained(
        base, str(experiment_dir / "adapter-final"), is_trainable=False
    ).eval()

    def generate(active_model, rows):
        predictions = []
        for batch in _direction_batches(rows):
            source_language = batch[0]["source_language"]
            target_language = batch[0]["target_language"]
            if any(
                item["source_language"] != source_language
                or item["target_language"] != target_language
                for item in batch
            ):
                raise ValueError("A generation batch cannot mix language directions.")
            tokenizer.src_lang = source_language
            encoded = tokenizer(
                [item["source_text"] for item in batch],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=MAX_SEQUENCE_LENGTH,
            ).to("cuda")
            with torch.inference_mode():
                generated = active_model.generate(
                    **encoded,
                    forced_bos_token_id=tokenizer.get_lang_id(target_language),
                    max_new_tokens=128,
                    num_beams=4,
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.1,
                )
            predictions.extend(
                tokenizer.batch_decode(generated, skip_special_tokens=True)
            )
        return predictions

    def deny_network(*_args, **_kwargs):
        raise AssertionError(
            "Offline multilingual evaluation attempted network access."
        )

    original_connect = socket.socket.connect
    started = time.monotonic()
    socket.socket.connect = deny_network
    try:
        with candidate.disable_adapter():
            base_predictions = generate(candidate, examples)
        candidate_predictions = generate(candidate, examples)
    finally:
        socket.socket.connect = original_connect
    routes = {}
    prediction_rows = []
    from .tico19_benchmark import paired_sentence_chrf

    for route in (("en", "so"), ("so", "en"), ("fr", "so"), ("so", "fr")):
        indices = [
            i
            for i, item in enumerate(examples)
            if (item["source_language"], item["target_language"]) == route
        ]
        if not indices:
            continue
        refs = [examples[i]["target_text"] for i in indices]
        before = [base_predictions[i] for i in indices]
        after = [candidate_predictions[i] for i in indices]
        key = f"{route[0]}-{route[1]}"
        bleu = BLEU()
        chrf = CHRF(word_order=2)
        base_metrics = {
            "bleu": round(bleu.corpus_score(before, [refs]).score, 4),
            "chrf_plus_plus": round(chrf.corpus_score(before, [refs]).score, 4),
        }
        candidate_metrics = {
            "bleu": round(bleu.corpus_score(after, [refs]).score, 4),
            "chrf_plus_plus": round(chrf.corpus_score(after, [refs]).score, 4),
        }
        routes[key] = {
            "rows": len(indices),
            "base": base_metrics,
            "candidate": candidate_metrics,
            "delta": {
                metric: round(candidate_metrics[metric] - base_metrics[metric], 4)
                for metric in base_metrics
            },
            "paired_sentence_chrf": paired_sentence_chrf(
                refs, before, after, bootstrap_samples=2_000, seed=1_729
            ),
        }
        prediction_rows.extend(
            {
                "source_language": route[0],
                "target_language": route[1],
                "source": examples[i]["source_text"],
                "reference": examples[i]["target_text"],
                "record_id": examples[i]["record_id"],
                "source_id": examples[i]["source_id"],
                "base": base_predictions[i],
                "candidate": candidate_predictions[i],
            }
            for i in indices
        )
    predictions_path = workspace / "reports" / f"{run_id}-predictions.jsonl"
    report_path = workspace / "reports" / f"{run_id}.json"
    if predictions_path.exists() or report_path.exists():
        raise FileExistsError("Evaluation output already exists; choose a new run ID.")
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    with predictions_path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in prediction_rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    report = {
        "status": "COMPLETED",
        "benchmark": "pair-specific held-out dataset tests",
        "experiment_id": experiment_id,
        "model_revision": MODEL_REVISION,
        "base_model_files": {
            item["name"]: item["sha256"] for item in model_record["files"]
        },
        "adapter_sha256": _sha256(adapter_path),
        "french_test_sha256": french_manifest["split_sha256"]["test.jsonl"],
        "rows": len(examples),
        "hardware": hardware,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "network_during_inference": "blocked",
        "routes": routes,
        "predictions_sha256": _sha256(predictions_path),
        "predictions_path": str(predictions_path),
        "automatic_promotion": False,
    }
    _write_json(report_path, report)
    return report
