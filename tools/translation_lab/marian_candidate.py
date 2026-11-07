# SPDX-License-Identifier: AGPL-3.0-or-later
"""Download, fine-tune, and evaluate a private English-to-Somali Marian model.

The candidate is pinned to an immutable CC-BY-4.0 model revision and trained
only from a separately approved local corpus split. Checkpoints, predictions,
and reports stay in the user's research workspace; nothing is promoted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import time
import urllib.request
from datetime import UTC
from datetime import datetime
from pathlib import Path

from tools.translation_lab.config import load_config
from tools.translation_lab.downloader import AllowlistedRedirectHandler
from tools.translation_lab.downloader import _validate_url
from tools.translation_lab.m2m100_training import _prepared_data
from tools.translation_lab.mixture_data import MIXTURE_ID
from tools.translation_lab.mixture_data import SOURCE_IDS as MIXTURE_SOURCE_IDS
from tools.translation_lab.mixture_data import prepare_marian_mixture

MODEL_ID = "Helsinki-NLP/opus-mt-synthetic-en-so"
MODEL_REVISION = "49384e6b2c3ddd374f2cccc8efecb678724b739d"
MODEL_LICENSE = "CC-BY-4.0"
MODEL_URL = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}"
DATASET_ID = "opus-infopankki-en-so"
MAX_SEQUENCE_LENGTH = 256
MAX_MODEL_BYTES = 170_000_000
GPU_MEMORY_FRACTION = 0.50
CHECKPOINT_STEPS = 500
TRAIN_BATCH_SIZE = 2
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 1e-4
MODEL_FILES = {
    ".gitattributes": (1613, "git", "df42fd966679c0c1d0aa59d78d59140333618c78"),
    "README.md": (3795, "git", "bba1df14ccc784d07e6a65060787d98ea43d3a07"),
    "added_tokens.json": (19, "git", "7ee95d4462db25b34658c2d5bb13794c218a2cba"),
    "config.json": (1030, "git", "b2953d0e8aa161a56073b7de76cdcbdfed0e89a4"),
    "generation_config.json": (288, "git", "308cc81820aed9c0c27fa70498160d0cb0bbb91a"),
    "pytorch_model.bin": (
        153_962_630,
        "sha256",
        "96769b801fad0dab3c7142af3102655639fb40394a9c928d0cc49b040089c3d7",
    ),
    "source.spm": (
        842_939,
        "sha256",
        "324a71b7317b9f4e26a181a515d374fc31398e29cd240c4123a4a130b6fa31d8",
    ),
    "target.spm": (
        842_939,
        "sha256",
        "324a71b7317b9f4e26a181a515d374fc31398e29cd240c4123a4a130b6fa31d8",
    ),
    "tokenizer_config.json": (
        280,
        "git",
        "7619d534c8c452c2f9d697d9c49b63c3a200f62f",
    ),
    "vocab.json": (804_843, "git", "c0545af1f6480142c6d9cd82d08d1656b3ad3c18"),
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matches_pin(path: Path, pin: tuple[int, str, str]) -> bool:
    size, algorithm, expected = pin
    if not path.is_file() or path.stat().st_size != size:
        return False
    if algorithm == "sha256":
        return _file_sha256(path) == expected
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected


def verify_model_bundle(model_dir: Path) -> dict:
    """Verify every required file against its immutable upstream blob pin."""
    verified = []
    for name, pin in MODEL_FILES.items():
        path = model_dir / name
        if not _matches_pin(path, pin):
            raise ValueError(f"Pinned Marian model file failed verification: {name}")
        verified.append(
            {"name": name, "bytes": path.stat().st_size, "sha256": _file_sha256(path)}
        )
    return {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": MODEL_LICENSE,
        "source": f"https://huggingface.co/{MODEL_ID}",
        "files": verified,
    }


def download_model(workspace: Path, config) -> Path:
    """Fetch only pinned files from the exact allowlisted HTTPS source."""
    model_dir = workspace / "cache" / "models" / MODEL_ID / MODEL_REVISION
    model_dir.mkdir(parents=True, exist_ok=True)
    hosts = set(config.allowed_download_hosts)
    opener = urllib.request.build_opener(AllowlistedRedirectHandler(hosts))
    downloaded = 0
    max_single_bytes = int(config.max_single_download_gib * 1024**3)
    max_total_bytes = int(config.max_download_gib * 1024**3)
    for name, pin in MODEL_FILES.items():
        destination = model_dir / name
        if _matches_pin(destination, pin):
            continue
        size = pin[0]
        if size > max_single_bytes:
            raise ValueError(
                "A pinned Marian file exceeds the configured download cap."
            )
        downloaded += size
        if downloaded > min(MAX_MODEL_BYTES, max_total_bytes):
            raise ValueError("Pinned model bundle exceeds its download budget.")
        url = f"{MODEL_URL}/{name}"
        _validate_url(url, hosts)
        temporary = destination.with_suffix(destination.suffix + ".part")
        request = urllib.request.Request(
            url, headers={"User-Agent": "Saylacian-Research-Lab/0.1"}
        )
        try:
            with (
                opener.open(request, timeout=60) as response,
                temporary.open("wb") as out,
            ):
                _validate_url(response.geturl(), hosts)
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > size:
                        raise ValueError(f"Download exceeded pinned size: {name}")
                    out.write(chunk)
            if total != size or not _matches_pin(temporary, pin):
                raise ValueError(f"Downloaded Marian file failed verification: {name}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    verify_model_bundle(model_dir)
    return model_dir


def _read_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _dataset_rows(
    workspace: Path,
    dataset_id: str,
    split: str,
    *,
    revision: str | None = None,
) -> list[dict]:
    if dataset_id == "tico19-somali-test-sample":
        from tools.benchmark_output import ROOT

        path = ROOT / "tests" / "data" / "somali_translation_tico19_test_150.jsonl"
        rows = _read_rows(path)
        return [
            {"source_text": row["source_en"], "target_text": row["reference_so"]}
            for row in rows
        ]
    if dataset_id == MIXTURE_ID:
        if not revision:
            raise ValueError("A revision is required to load a generated mixture.")
        root = workspace / "data" / "prepared" / MIXTURE_ID / revision
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("dataset_revision") != revision:
            raise ValueError("Generated mixture revision does not match its manifest.")
        path = root / f"{split}.jsonl"
        expected = manifest.get("split_sha256", {}).get(path.name)
        if not expected or _file_sha256(path) != expected:
            raise ValueError(f"Generated mixture split checksum failed: {split}")
        return _read_rows(path)
    root = workspace / "data" / "prepared" / dataset_id
    candidates = list(root.glob(f"*/{split}.jsonl"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected one prepared {split} split for {dataset_id}."
        )
    return _read_rows(candidates[0])


def _training_data(workspace: Path, config, dataset_id: str):
    if dataset_id == MIXTURE_ID:
        manifest, train_rows, validation_rows, _ = prepare_marian_mixture(
            workspace, config
        )
        return manifest, train_rows, validation_rows
    if dataset_id == DATASET_ID:
        return _prepared_data(workspace, config, dataset_id=dataset_id)
    raise ValueError(f"Unsupported Marian training dataset: {dataset_id}")


def _tokenize_rows(rows: list[dict], tokenizer) -> list[dict]:
    encoded = []
    for row in rows:
        source = row.get("source_text")
        target = row.get("target_text")
        if not isinstance(source, str) or not isinstance(target, str):
            raise TypeError("Training pairs must contain source_text and target_text.")
        if not source.strip() or not target.strip():
            raise ValueError("Training pairs cannot contain empty text.")
        encoded.append(
            tokenizer(
                source,
                text_target=target,
                truncation=True,
                max_length=MAX_SEQUENCE_LENGTH,
            )
        )
    return encoded


def train_candidate(
    workspace: Path,
    config,
    *,
    model_dir: Path,
    experiment_id: str,
    resume: bool = False,
    epochs: int = 2,
    dataset_id: str = DATASET_ID,
    learning_rate: float = LEARNING_RATE,
) -> dict:
    """Fine-tune an isolated one-way LoRA candidate from approved rows."""
    try:
        import torch
        from peft import LoraConfig
        from peft import TaskType
        from peft import get_peft_model
        from transformers import DataCollatorForSeq2Seq
        from transformers import MarianMTModel
        from transformers import MarianTokenizer
        from transformers import Seq2SeqTrainer
        from transformers import Seq2SeqTrainingArguments
        from transformers.trainer_utils import get_last_checkpoint
    except ImportError as error:
        raise RuntimeError(
            "Install the isolated training requirements first."
        ) from error

    required_sources = (
        set(MIXTURE_SOURCE_IDS) | {"google-smol-en-so"}
        if dataset_id == MIXTURE_ID
        else {DATASET_ID}
    )
    if not config.training_enabled or not required_sources.issubset(
        set(config.approved_source_ids)
    ):
        raise PermissionError(
            "Training data is not approved in the private lab config."
        )
    if experiment_id != Path(experiment_id).name or not experiment_id.strip():
        raise ValueError("Experiment ID must be a nonempty path-safe name.")
    if not 1 <= epochs <= 5:
        raise ValueError("Epoch count must be between one and five.")
    if learning_rate not in {2.5e-5, 5e-5, 1e-4}:
        raise ValueError("Learning rate must be 2.5e-5, 5e-5 or 1e-4.")
    model_record = verify_model_bundle(model_dir)
    manifest, train_rows, validation_rows = _training_data(
        workspace, config, dataset_id
    )
    if not torch.cuda.is_available():
        raise RuntimeError("This Marian training run requires an available CUDA GPU.")
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    if free_bytes < 4 * 1024**3:
        raise RuntimeError("At least 4 GiB free GPU memory is required.")
    torch.cuda.set_per_process_memory_fraction(GPU_MEMORY_FRACTION, 0)
    torch.set_num_threads(config.max_cpu_threads)

    experiment_dir = workspace / "experiments" / experiment_id
    checkpoint_dir = workspace / "checkpoints" / experiment_id
    adapter_dir = experiment_dir / "adapter-final"
    metadata_path = experiment_dir / "experiment.json"
    fingerprint = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dataset_id": dataset_id,
        "dataset_revision": manifest["dataset_revision"],
        "train_sha256": manifest["split_sha256"]["train.jsonl"],
        "validation_sha256": manifest["split_sha256"]["validation.jsonl"],
        "license": manifest["license"],
        "source_revisions": manifest.get("source_revisions", {}),
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "training_parameters": {
            "epochs": epochs,
            "train_batch_size": TRAIN_BATCH_SIZE,
            "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
            "learning_rate": learning_rate,
            "lora_rank": 8,
            "lora_alpha": 16,
            "checkpoint_steps": CHECKPOINT_STEPS,
        },
    }
    created_utc = datetime.now(UTC).isoformat()
    if metadata_path.exists():
        prior = json.loads(metadata_path.read_text(encoding="utf-8"))
        if prior.get("fingerprint") != fingerprint or prior.get("epochs") != epochs:
            raise ValueError("Existing experiment inputs changed; use a new ID.")
        if not resume:
            raise FileExistsError("Experiment exists; use --resume or a new ID.")
        created_utc = prior.get("created_utc", created_utc)
    elif resume:
        raise FileNotFoundError("No saved candidate exists to resume.")

    experiment_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "created_utc": created_utc,
                "fingerprint": fingerprint,
                "model_license": MODEL_LICENSE,
                "model_source": model_record["source"],
                "dataset_attribution": manifest.get(
                    "attributions", [manifest.get("attribution", "")]
                ),
                "training_rows": len(train_rows),
                "validation_rows": len(validation_rows),
                "epochs": epochs,
                "automatic_promotion": False,
                "weight_redistribution": "not approved; requires separate review",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    base_model = MarianMTModel.from_pretrained(
        str(model_dir),
        local_files_only=True,
        torch_dtype=torch.float16,
        use_safetensors=False,
        device_map={"": 0},
    )
    base_model.config.use_cache = False
    model = get_peft_model(
        base_model,
        LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
            bias="none",
        ),
    )
    train_data = _tokenize_rows(train_rows, tokenizer)
    validation_data = _tokenize_rows(validation_rows, tokenizer)
    arguments = Seq2SeqTrainingArguments(
        output_dir=str(checkpoint_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.03,
        logging_steps=25,
        eval_strategy="steps",
        eval_steps=CHECKPOINT_STEPS,
        label_names=["labels"],
        save_strategy="steps",
        save_steps=CHECKPOINT_STEPS,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,
        gradient_checkpointing=False,
        dataloader_num_workers=0,
        report_to=[],
        seed=1729,
        data_seed=1729,
        save_safetensors=True,
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=arguments,
        train_dataset=train_data,
        eval_dataset=validation_data,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer=tokenizer,
            model=model,
            label_pad_token_id=-100,
            pad_to_multiple_of=8,
        ),
        processing_class=tokenizer,
    )
    checkpoint = get_last_checkpoint(str(checkpoint_dir)) if resume else None
    started = time.monotonic()
    result = trainer.train(resume_from_checkpoint=checkpoint)
    trainer.save_model(str(adapter_dir))
    trainer.save_state()
    report = {
        "status": "PRIVATE_RESEARCH_CANDIDATE_TRAINED",
        "experiment_id": experiment_id,
        "fingerprint": fingerprint,
        "training_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "train_metrics": result.metrics,
        "best_validation_loss": trainer.state.best_metric,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "gpu": torch.cuda.get_device_name(0),
        "gpu_memory_fraction_cap": GPU_MEMORY_FRACTION,
        "free_gpu_mib_at_start": free_bytes // 1024**2,
        "gpu_total_mib": total_bytes // 1024**2,
        "adapter_directory": str(adapter_dir),
        "automatic_promotion": False,
    }
    (experiment_dir / "training-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def _score(references: list[str], predictions: list[str]) -> dict:
    from sacrebleu.metrics import BLEU
    from sacrebleu.metrics import CHRF

    return {
        "bleu": round(BLEU().corpus_score(predictions, [references]).score, 4),
        "chrf_plus_plus": round(
            CHRF(word_order=2).corpus_score(predictions, [references]).score, 4
        ),
    }


def evaluate_candidate(
    workspace: Path,
    *,
    model_dir: Path,
    experiment_id: str,
    output_dir: Path,
    dataset_names: list[str] | None = None,
) -> dict:
    """Score the base and adapter on fixed Google SMOL and TICO test sets."""
    import torch
    from peft import PeftModel
    from transformers import MarianMTModel
    from transformers import MarianTokenizer

    verify_model_bundle(model_dir)
    adapter_dir = workspace / "experiments" / experiment_id / "adapter-final"
    if not (adapter_dir / "adapter_model.safetensors").is_file():
        raise FileNotFoundError("The private LoRA adapter is missing.")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for Marian evaluation.")
    free, _ = torch.cuda.mem_get_info(0)
    if free < 2 * 1024**3:
        raise RuntimeError(
            "At least 2 GiB free CUDA memory is required for evaluation."
        )
    torch.cuda.set_per_process_memory_fraction(GPU_MEMORY_FRACTION, 0)
    torch.set_num_threads(2)
    tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    base = MarianMTModel.from_pretrained(
        str(model_dir),
        local_files_only=True,
        torch_dtype=torch.float16,
        use_safetensors=False,
        device_map={"": 0},
    ).eval()
    candidate = PeftModel.from_pretrained(
        base, str(adapter_dir), is_trainable=False
    ).eval()
    experiment_metadata = json.loads(
        (workspace / "experiments" / experiment_id / "experiment.json").read_text(
            encoding="utf-8"
        )
    )
    fingerprint = experiment_metadata["fingerprint"]
    training_dataset = fingerprint["dataset_id"]
    training_revision = fingerprint["dataset_revision"]
    sets = {
        "google-smol-en-so-test": _dataset_rows(workspace, "google-smol-en-so", "test"),
        "tico19-health-test": _dataset_rows(
            workspace, "tico19-somali-test-sample", "test"
        ),
        "infopankki-en-so-test": _dataset_rows(workspace, DATASET_ID, "test"),
    }
    if training_dataset == MIXTURE_ID:
        sets["combined-corpus-heldout"] = _dataset_rows(
            workspace, MIXTURE_ID, "test", revision=training_revision
        )
    if dataset_names:
        unknown = set(dataset_names) - set(sets)
        if unknown:
            raise ValueError(
                "Unknown evaluation dataset(s): " + ", ".join(sorted(unknown))
            )
        sets = {name: rows for name, rows in sets.items() if name in dataset_names}

    def generate(active_model, rows, *, dataset_name: str, prediction_name: str):
        outputs = []
        for start in range(0, len(rows), 16):
            batch = rows[start : start + 16]
            encoded = tokenizer(
                [row["source_text"] for row in batch],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=MAX_SEQUENCE_LENGTH,
            ).to("cuda")
            with torch.inference_mode():
                tokens = active_model.generate(
                    **encoded,
                    max_new_tokens=128,
                    num_beams=4,
                    no_repeat_ngram_size=3,
                )
            outputs.extend(tokenizer.batch_decode(tokens, skip_special_tokens=True))
            completed = min(start + len(batch), len(rows))
            if completed == len(rows) or completed % 160 == 0:
                print(
                    f"Generated {completed}/{len(rows)} rows for {dataset_name} "
                    f"({prediction_name})",
                    flush=True,
                )
        return outputs

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline Marian evaluation attempted network access.")

    results, raw = {}, {}
    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    try:
        for name, rows in sets.items():
            references = [row["target_text"] for row in rows]
            with candidate.disable_adapter():
                base_outputs = generate(
                    candidate,
                    rows,
                    dataset_name=name,
                    prediction_name="base",
                )
            adapted_outputs = generate(
                candidate,
                rows,
                dataset_name=name,
                prediction_name="candidate",
            )
            results[name] = {
                "n": len(rows),
                "base": _score(references, base_outputs),
                "candidate": _score(references, adapted_outputs),
            }
            results[name]["delta"] = {
                metric: round(
                    results[name]["candidate"][metric] - results[name]["base"][metric],
                    4,
                )
                for metric in ("bleu", "chrf_plus_plus")
            }
            raw[name] = [
                {
                    "source": row["source_text"],
                    "reference": reference,
                    "base": before,
                    "candidate": after,
                }
                for row, reference, before, after in zip(
                    rows, references, base_outputs, adapted_outputs, strict=True
                )
            ]
    finally:
        socket.socket.connect = original_connect

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_license": MODEL_LICENSE,
        "experiment_id": experiment_id,
        "training_dataset": training_dataset,
        "training_dataset_revision": training_revision,
        "network_during_inference": "blocked",
        "automatic_promotion": False,
        "metrics": results,
        "predictions_file": str(output_dir / "predictions.json"),
        "limitations": [
            "Scores are automatic overlap metrics, not fluent-speaker judgments.",
            "TICO-19 covers health and COVID-19 text only.",
            "InfoFinland in-domain data may contain alignment noise.",
            "This model supports English-to-Somali only.",
        ],
    }
    (output_dir / "evaluation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "predictions.json").write_text(
        json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument(
        "--dataset-id",
        choices=[DATASET_ID, MIXTURE_ID],
        default=DATASET_ID,
    )
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument(
        "--learning-rate",
        type=float,
        choices=(2.5e-5, 5e-5, LEARNING_RATE),
        default=LEARNING_RATE,
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--evaluate-only", action="store_true")
    parser.add_argument(
        "--evaluation-dataset",
        action="append",
        choices=(
            "google-smol-en-so-test",
            "tico19-health-test",
            "infopankki-en-so-test",
            "combined-corpus-heldout",
        ),
        help="Score only selected held-out sets; repeat to select several.",
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Train and save the private candidate without running the broad scorer.",
    )
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    from tools.translation_lab.workspace import default_workspace
    from tools.translation_lab.workspace import ensure_outside_repository

    args = build_parser().parse_args(argv)
    if args.evaluate_only and args.skip_evaluation:
        raise SystemExit("--skip-evaluation cannot be combined with --evaluate-only.")
    workspace = args.workspace or default_workspace()
    repository = Path(__file__).resolve().parents[2]
    ensure_outside_repository(workspace, repository)
    config_path = args.config or workspace / "config" / "active.toml"
    config = load_config(config_path)
    required_sources = (
        set(MIXTURE_SOURCE_IDS) | {"google-smol-en-so"}
        if args.dataset_id == MIXTURE_ID
        else {DATASET_ID}
    )
    if not args.evaluate_only and (
        not config.training_enabled
        or not required_sources.issubset(set(config.approved_source_ids))
    ):
        print(
            "Marian training requires approved source IDs and an enabled "
            "private config.",
            flush=True,
        )
        return 2
    try:
        model_dir = workspace / "cache" / "models" / MODEL_ID / MODEL_REVISION
        if not args.skip_download and not args.evaluate_only:
            model_dir = download_model(workspace, config)
        verify_model_bundle(model_dir)
        if not args.evaluate_only:
            trained = train_candidate(
                workspace,
                config,
                model_dir=model_dir,
                experiment_id=args.experiment_id,
                resume=args.resume,
                epochs=args.epochs,
                dataset_id=args.dataset_id,
                learning_rate=args.learning_rate,
            )
            print(json.dumps(trained, ensure_ascii=False, indent=2), flush=True)
        if args.skip_evaluation:
            return 0
        report_dir = args.output_dir or workspace / "experiments" / args.experiment_id
        ensure_outside_repository(report_dir, repository)
        result = evaluate_candidate(
            workspace,
            model_dir=model_dir,
            experiment_id=args.experiment_id,
            output_dir=report_dir,
            dataset_names=args.evaluation_dataset,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    except (OSError, PermissionError, RuntimeError, ValueError) as error:
        print(f"Marian candidate stopped safely: {error}", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
