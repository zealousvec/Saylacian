# SPDX-License-Identifier: AGPL-3.0-or-later
"""Train a private M2M100 LoRA candidate on approved, prepared Somali data."""

from __future__ import annotations

import gc
import hashlib
import json
import math
import os
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from .config import LabConfig
from .resources import gpu_temperature_c
from .sources import read_owner_registry
from .sources import verify_approved_source

MODEL_ID = "meta-m2m100-418m"
MODEL_REVISION = "55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636"
DATASET_ID = "google-smol-en-so"
DATASET_REVISION = "fdaff3a1a019f89fa30a562a85d7c1d3e9150444"
MODEL_FILES = (
    "config.json",
    "generation_config.json",
    "pytorch_model.bin",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "vocab.json",
)
MAX_SEQUENCE_LENGTH = 256
MIN_FREE_RAM_GIB = 1.5
MIN_FREE_GPU_MIB = 5_500
GPU_MEMORY_FRACTION = 0.65


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _prepared_data(
    workspace: Path, config: LabConfig, *, dataset_id: str = DATASET_ID
) -> tuple[dict, dict, dict]:
    if not config.training_enabled:
        raise PermissionError("Training is disabled in the active lab config.")

    if dataset_id == "marian-mixture":
        from tools.translation_lab.mixture_data import prepare_marian_mixture

        manifest, train_rows, validation_rows, _test_rows = prepare_marian_mixture(
            workspace, config
        )
        return manifest, train_rows, validation_rows

    if dataset_id not in config.approved_source_ids:
        raise PermissionError("Training data is not approved in the active config.")

    registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
    source = next(
        (item for item in registry if item.get("source_id") == dataset_id),
        None,
    )
    if source is None:
        raise PermissionError("Approved Google SMOL source record is missing.")
    verify_approved_source(source, set(config.approved_source_ids), purpose="train")

    revision = source.get("revision")
    if not revision:
        raise ValueError("Approved source has no pinned dataset revision.")
    root = workspace / "data" / "prepared" / dataset_id / revision
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Prepared Google SMOL manifest is missing.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("source_id") != dataset_id
        or manifest.get("dataset_revision") != revision
        or manifest.get("license") != source.get("license")
    ):
        raise ValueError("Prepared corpus identity or license does not match.")

    splits = {}
    for name in ("train", "validation", "test"):
        path = root / f"{name}.jsonl"
        expected = manifest.get("split_sha256", {}).get(path.name)
        if not expected or _sha256(path) != expected:
            raise ValueError(f"Prepared {name} split checksum failed.")
        if name != "test":
            splits[name] = _read_jsonl(path)
    if not splits["train"] or not splits["validation"]:
        raise ValueError("Training and validation splits must both be nonempty.")
    return manifest, splits["train"], splits["validation"]


def bidirectional_examples(rows: list[dict]) -> list[dict]:
    """Expand approved English–Somali pairs into separate translation routes."""
    examples = []
    for row in rows:
        english = row.get("source_text")
        somali = row.get("target_text")
        if not isinstance(english, str) or not isinstance(somali, str):
            raise TypeError("Prepared translation sides must be strings.")
        if not english.strip() or not somali.strip():
            raise ValueError("Prepared translation sides cannot be empty.")
        examples.extend(
            (
                {
                    "source_text": english,
                    "target_text": somali,
                    "source_language": "en",
                    "target_language": "so",
                },
                {
                    "source_text": somali,
                    "target_text": english,
                    "source_language": "so",
                    "target_language": "en",
                },
            )
        )
    return examples


def _available_ram_gib() -> float | None:
    if os.name != "nt":
        return None

    import ctypes

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_phys", ctypes.c_ulonglong),
            ("avail_phys", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("avail_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("avail_virtual", ctypes.c_ulonglong),
            ("avail_extended_virtual", ctypes.c_ulonglong),
        ]

    state = MemoryStatus()
    state.length = ctypes.sizeof(state)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        return None
    return state.avail_phys / 1024**3


def _verify_model_bundle(workspace: Path, model_dir: Path) -> dict:
    registry_path = workspace / "registry" / "models.jsonl"
    records = [
        json.loads(line)
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    record = next(
        (item for item in records if item.get("model_id") == MODEL_ID),
        None,
    )
    if (
        record is None
        or record.get("revision") != MODEL_REVISION
        or record.get("license") != "MIT"
        or record.get("status") != "downloaded-and-hash-verified"
    ):
        raise PermissionError("Pinned, hash-verified M2M100 model record is missing.")

    hashes = {item["name"]: item for item in record.get("files", [])}
    for name in MODEL_FILES:
        expected = hashes.get(name)
        path = model_dir / name
        if (
            expected is None
            or not path.is_file()
            or path.stat().st_size != expected.get("bytes")
            or _sha256(path) != expected.get("sha256")
        ):
            raise ValueError(f"M2M100 model file failed verification: {name}")
    return record


def _thermal_callback_type(callback_base, max_temperature_c: float, read_temperature):
    class ThermalCheckpointCallback(callback_base):
        """Stop on sampled GPU temperature/telemetry loss at a saved step."""

        stop_reason: str | None = None

        def on_step_end(self, args, state, control, **kwargs):
            if state.global_step % 10:
                return control
            try:
                temperature = read_temperature()
            except RuntimeError:
                self.stop_reason = "GPU temperature telemetry became unavailable."
            else:
                if temperature >= max_temperature_c:
                    self.stop_reason = (
                        f"GPU temperature reached {temperature}°C, at/above the "
                        f"{max_temperature_c}°C configured stop."
                    )
            if self.stop_reason:
                control.should_save = True
                control.should_training_stop = True
            return control

    return ThermalCheckpointCallback


def _preflight(torch, *, max_gpu_fraction: float) -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("This 418M experiment requires the available CUDA GPU.")
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    free_mib = int(free_bytes / 1024**2)
    if free_mib < MIN_FREE_GPU_MIB:
        raise RuntimeError(
            f"Need {MIN_FREE_GPU_MIB} MiB free GPU memory; found {free_mib} MiB."
        )
    ram_gib = _available_ram_gib()
    if ram_gib is not None and ram_gib < MIN_FREE_RAM_GIB:
        raise RuntimeError(
            f"Need {MIN_FREE_RAM_GIB:.1f} GiB free system RAM; found {ram_gib:.2f} GiB."
        )
    if not 0.25 <= max_gpu_fraction <= 0.75:
        raise ValueError("GPU allocation fraction must be between 0.25 and 0.75.")
    torch.cuda.set_per_process_memory_fraction(max_gpu_fraction, 0)
    torch.set_num_threads(2)
    return {
        "device": torch.cuda.get_device_name(0),
        "gpu_free_mib": free_mib,
        "gpu_total_mib": int(total_bytes / 1024**2),
        "gpu_memory_fraction_cap": max_gpu_fraction,
        "free_system_ram_gib": round(ram_gib, 2) if ram_gib is not None else None,
        "cpu_threads": 2,
    }


def _tokenize_rows(rows: list[dict], tokenizer) -> list[dict]:
    encoded_rows = []
    for example in bidirectional_examples(rows):
        tokenizer.src_lang = example["source_language"]
        tokenizer.tgt_lang = example["target_language"]
        encoded = tokenizer(
            example["source_text"],
            text_target=example["target_text"],
            max_length=MAX_SEQUENCE_LENGTH,
            truncation=True,
        )
        encoded_rows.append(encoded)
    return encoded_rows


def train_m2m100_lora(
    workspace: Path,
    config: LabConfig,
    *,
    model_dir: Path,
    experiment_id: str,
    resume: bool = False,
    max_gpu_fraction: float = GPU_MEMORY_FRACTION,
    dataset_id: str = DATASET_ID,
    learning_rate: float = 1e-4,
    num_train_epochs: int = 1,
    lora_rank: int = 8,
    max_steps: int | None = None,
    max_gpu_temperature_c: float = 82.0,
) -> dict:
    """Train a resumable LoRA candidate; never modify or promote app models."""
    try:
        import torch
        from peft import LoraConfig
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
            "Install the isolated training requirements before training."
        ) from error

    if not config.training_enabled:
        raise PermissionError("Training is disabled in the active lab config.")
    if experiment_id != Path(experiment_id).name or not experiment_id.strip():
        raise ValueError("Experiment ID must be a nonempty path-safe name.")
    if learning_rate <= 0 or num_train_epochs < 1 or not 1 <= lora_rank <= 64:
        raise ValueError("Training settings are outside the supported range.")
    if not math.isfinite(learning_rate):
        raise ValueError("learning_rate must be finite.")
    if not math.isfinite(max_gpu_temperature_c) or max_gpu_temperature_c <= 0:
        raise ValueError("max_gpu_temperature_c must be finite and positive.")
    if max_steps is not None and max_steps < 1:
        raise ValueError("max_steps must be positive when specified.")

    training_settings = {
        "learning_rate": learning_rate,
        "num_train_epochs": num_train_epochs,
        "lora_rank": lora_rank,
        "max_steps": max_steps,
    }
    legacy_default_settings = {
        "learning_rate": 1e-4,
        "num_train_epochs": 1,
        "lora_rank": 8,
        "max_steps": None,
    }

    hardware = _preflight(torch, max_gpu_fraction=max_gpu_fraction)
    model_record = _verify_model_bundle(workspace, model_dir)
    dataset_manifest, train_rows, validation_rows = _prepared_data(
        workspace, config, dataset_id=dataset_id
    )
    experiment_dir = workspace / "experiments" / experiment_id
    checkpoint_dir = workspace / "checkpoints" / experiment_id
    adapter_dir = experiment_dir / "adapter-final"
    metadata_path = experiment_dir / "experiment.json"
    fingerprint = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dataset_id": dataset_manifest["source_id"],
        "dataset_revision": dataset_manifest["dataset_revision"],
        "train_sha256": dataset_manifest["split_sha256"]["train.jsonl"],
        "validation_sha256": dataset_manifest["split_sha256"]["validation.jsonl"],
        "test_sha256": dataset_manifest["split_sha256"]["test.jsonl"],
        "license": dataset_manifest["license"],
        "source_revisions": dataset_manifest.get("source_revisions", {}),
        "source_licenses": dataset_manifest.get("source_licenses", {}),
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
    }
    created_utc = datetime.now(UTC).isoformat()
    if metadata_path.exists():
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        if previous.get("fingerprint") != fingerprint:
            raise ValueError("Existing experiment inputs changed; use a new ID.")
        if (
            previous.get("training_settings", legacy_default_settings)
            != training_settings
        ):
            raise ValueError(
                "Existing experiment training settings changed; use a new ID."
            )
        if not resume:
            raise FileExistsError("Experiment exists; use resume or a new ID.")
        created_utc = previous.get("created_utc", created_utc)
    elif resume:
        raise FileNotFoundError("No saved experiment exists to resume.")

    experiment_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        metadata_path,
        {
            "schema_version": 1,
            "experiment_id": experiment_id,
            "created_utc": created_utc,
            "fingerprint": fingerprint,
            "training_settings": training_settings,
            "model_license": model_record["license"],
            "training_rows": len(train_rows),
            "validation_rows": len(validation_rows),
            "dataset_attribution": dataset_manifest["attribution"],
            "dataset_source_page": dataset_manifest.get("source_page"),
            "dataset_source_pages": dataset_manifest.get("source_pages", {}),
            "training_examples_after_bidirectional_expansion": 2 * len(train_rows),
            "validation_examples_after_bidirectional_expansion": 2
            * len(validation_rows),
            "hardware": hardware,
            "automatic_promotion": False,
            "weight_redistribution": (
                "not approved; review dataset attribution and derivative licensing"
            ),
        },
    )

    tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = M2M100ForConditionalGeneration.from_pretrained(
        str(model_dir),
        local_files_only=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    )
    model.config.use_cache = False
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
    train_data = _tokenize_rows(train_rows, tokenizer)
    validation_data = _tokenize_rows(validation_rows, tokenizer)
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100,
        pad_to_multiple_of=8,
    )
    training_args = Seq2SeqTrainingArguments(
        output_dir=str(checkpoint_dir),
        num_train_epochs=num_train_epochs,
        max_steps=max_steps if max_steps is not None else -1,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.03,
        logging_steps=10,
        eval_strategy="steps" if max_steps is not None else "epoch",
        eval_steps=max_steps,
        label_names=["labels"],
        save_strategy="steps",
        save_steps=50,
        save_total_limit=3,
        fp16=True,
        gradient_checkpointing=False,
        dataloader_num_workers=0,
        report_to=[],
        seed=1729,
        data_seed=1729,
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=validation_data,
        data_collator=data_collator,
        processing_class=tokenizer,
    )

    thermal_callback_class = _thermal_callback_type(
        TrainerCallback, max_gpu_temperature_c, gpu_temperature_c
    )
    thermal_callback = thermal_callback_class()
    trainer.add_callback(thermal_callback)
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
                "experiment_id": experiment_id,
                "status": "TRAINING_FAILED",
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "fingerprint": fingerprint,
                "resume_available": get_last_checkpoint(str(checkpoint_dir))
                is not None,
            },
        )
        raise
    report = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "status": (
            "PAUSED_RESOURCE"
            if thermal_callback.stop_reason
            else "TRAINED_RESEARCH_CANDIDATE"
        ),
        "fingerprint": fingerprint,
        "training_settings": training_settings,
        "training_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "hardware": hardware,
        "training_arguments": training_args.to_dict(),
        "train_metrics": result.metrics,
        "training_metric_scope": (
            "resumed segment only" if checkpoint is not None else "complete invocation"
        ),
        "completed_steps": trainer.state.global_step,
        "planned_steps": trainer.state.max_steps,
        "validation_loss": next(
            (
                item["eval_loss"]
                for item in reversed(trainer.state.log_history)
                if "eval_loss" in item
            ),
            None,
        ),
        "resource_stop_reason": thermal_callback.stop_reason,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "adapter_directory": str(adapter_dir),
        "checkpoints_directory": str(checkpoint_dir),
        "automatic_promotion": False,
        "linguistic_review": "not performed",
        "model_redistribution": "not approved",
    }
    _write_json(experiment_dir / "training-report.json", report)
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()
    return report


def evaluate_m2m100_candidate(
    workspace: Path,
    config: LabConfig,
    *,
    model_dir: Path,
    experiment_id: str,
    dataset_id: str = DATASET_ID,
    evaluation_dataset_id: str | None = None,
) -> dict:
    """Compare the base model and LoRA candidate on the untouched test split."""
    try:
        import torch
        from peft import PeftModel
        from sacrebleu.metrics import BLEU
        from sacrebleu.metrics import CHRF
        from transformers import M2M100ForConditionalGeneration
        from transformers import M2M100Tokenizer
    except ImportError as error:
        raise RuntimeError(
            "Install the isolated training requirements before evaluation."
        ) from error

    if experiment_id != Path(experiment_id).name or not experiment_id.strip():
        raise ValueError("Experiment ID must be a nonempty path-safe name.")
    evaluation_dataset_id = evaluation_dataset_id or dataset_id
    source_registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
    source = next(
        (item for item in source_registry if item.get("source_id") == dataset_id),
        None,
    )
    if source is None:
        raise PermissionError("Approved training source record is missing.")
    verify_approved_source(source, set(config.approved_source_ids), purpose="evaluate")

    evaluation_source = next(
        (
            item
            for item in source_registry
            if item.get("source_id") == evaluation_dataset_id
        ),
        None,
    )
    if evaluation_source is None:
        raise PermissionError("Approved evaluation source record is missing.")
    verify_approved_source(
        evaluation_source,
        set(config.approved_source_ids),
        purpose="evaluate",
    )

    training_manifest, _training_rows, _training_validation = _prepared_data(
        workspace, config, dataset_id=dataset_id
    )
    manifest, _eval_rows, _eval_validation = _prepared_data(
        workspace, config, dataset_id=evaluation_dataset_id
    )
    evaluation_revision = manifest["dataset_revision"]
    test_path = (
        workspace
        / "data"
        / "prepared"
        / evaluation_dataset_id
        / evaluation_revision
        / "test.jsonl"
    )
    test_rows = _read_jsonl(test_path)
    examples = bidirectional_examples(test_rows)
    adapter_dir = workspace / "experiments" / experiment_id / "adapter-final"
    if not (adapter_dir / "adapter_model.safetensors").is_file():
        raise FileNotFoundError("Trained adapter weights are missing.")
    hardware = _preflight(torch, max_gpu_fraction=GPU_MEMORY_FRACTION)
    _verify_model_bundle(workspace, model_dir)
    tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = M2M100ForConditionalGeneration.from_pretrained(
        str(model_dir),
        local_files_only=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    )
    model.eval()

    def generate_predictions(active_model, route_examples: list[dict]) -> list[str]:
        predictions = []
        active_model.eval()
        for start in range(0, len(route_examples), 4):
            batch = route_examples[start : start + 4]
            tokenizer.src_lang = batch[0]["source_language"]
            encoded = tokenizer(
                [item["source_text"] for item in batch],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=MAX_SEQUENCE_LENGTH,
            ).to("cuda")
            target_language = batch[0]["target_language"]
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

    output_dir = workspace / "experiments" / experiment_id
    base_predictions = generate_predictions(model, examples)
    adapted_model = PeftModel.from_pretrained(
        model, str(adapter_dir), is_trainable=False
    )
    adapted_predictions = generate_predictions(adapted_model, examples)
    route_results = {}
    prediction_rows = []
    for route in (("en", "so"), ("so", "en")):
        indices = [
            index
            for index, item in enumerate(examples)
            if (item["source_language"], item["target_language"]) == route
        ]
        references = [examples[index]["target_text"] for index in indices]
        base = [base_predictions[index] for index in indices]
        adapted = [adapted_predictions[index] for index in indices]
        route_key = f"{route[0]}-{route[1]}"
        base_bleu = BLEU().corpus_score(base, [references]).score
        adapted_bleu = BLEU().corpus_score(adapted, [references]).score
        base_chrf = CHRF().corpus_score(base, [references]).score
        adapted_chrf = CHRF().corpus_score(adapted, [references]).score
        route_results[route_key] = {
            "examples": len(indices),
            "base_bleu": round(base_bleu, 4),
            "candidate_bleu": round(adapted_bleu, 4),
            "bleu_delta": round(adapted_bleu - base_bleu, 4),
            "base_chrf": round(base_chrf, 4),
            "candidate_chrf": round(adapted_chrf, 4),
            "chrf_delta": round(adapted_chrf - base_chrf, 4),
        }
        for index in indices:
            prediction_rows.append(
                {
                    "source_language": route[0],
                    "target_language": route[1],
                    "source": examples[index]["source_text"],
                    "reference": examples[index]["target_text"],
                    "base": base_predictions[index],
                    "candidate": adapted_predictions[index],
                }
            )
    predictions_path = output_dir / f"heldout-predictions-{evaluation_dataset_id}.jsonl"
    predictions_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in prediction_rows),
        encoding="utf-8",
    )
    report = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "status": "HELDOUT_EVALUATED_RESEARCH_CANDIDATE",
        "dataset_id": dataset_id,
        "dataset_revision": training_manifest["dataset_revision"],
        "dataset_license": training_manifest["license"],
        "dataset_attribution": training_manifest["attribution"],
        "dataset_source_page": training_manifest["source_page"],
        "evaluation_dataset_id": evaluation_dataset_id,
        "evaluation_dataset_revision": evaluation_revision,
        "evaluation_dataset_license": manifest["license"],
        "evaluation_dataset_attribution": manifest["attribution"],
        "evaluation_dataset_source_page": manifest["source_page"],
        "test_split_sha256": _sha256(test_path),
        "test_examples": len(test_rows),
        "directional_examples": len(examples),
        "routes": route_results,
        "generation": {
            "max_new_tokens": 128,
            "num_beams": 4,
            "no_repeat_ngram_size": 3,
            "repetition_penalty": 1.1,
        },
        "hardware": hardware,
        "predictions_path": str(predictions_path),
        "human_review": "not performed",
        "automatic_promotion": False,
        "model_redistribution": "not approved",
    }
    _write_json(output_dir / f"heldout-evaluation-{evaluation_dataset_id}.json", report)
    del adapted_model, model
    gc.collect()
    torch.cuda.empty_cache()
    return report
