# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen a pinned Somali-to-English Marian model on private test splits.

The model, predictions, and scores stay in the external research workspace.
The script blocks socket connections during inference and never promotes a
screened model into Saylacian's model packs.
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
from tools.translation_lab.marian_candidate import MAX_SEQUENCE_LENGTH
from tools.translation_lab.marian_candidate import _dataset_rows
from tools.translation_lab.marian_candidate import _file_sha256
from tools.translation_lab.marian_candidate import _score
from tools.translation_lab.marian_candidate import _tokenize_rows
from tools.translation_lab.mixture_data import MIXTURE_ID
from tools.translation_lab.mixture_data import SOURCE_IDS
from tools.translation_lab.mixture_data import prepare_marian_mixture

MODEL_ID = "Helsinki-NLP/opus-mt-cus-en"
MODEL_REVISION = "90178461a746d80e84a454e642d062afa1315eae"
MODEL_LICENSE = "Apache-2.0"
MODEL_URL = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}"
MODEL_FILES = {
    ".gitattributes": (399, "git", "9a0990c5c0e00e26cc5ca4ba5c1c3ad533de7018"),
    "README.md": (2127, "git", "0213a611a9376e367f54353b1ae30c62dac9a225"),
    "config.json": (1395, "git", "c82a23d64dc06fe78bf06bdcb74715f6aceb9a2f"),
    "generation_config.json": (293, "git", "be984453a1bf25a01ee5ba0bb66a913978da2423"),
    "metadata.json": (1101, "git", "6a8bffcc62f8ac9c88ef06902d7d9ca8e51a7e84"),
    "model.safetensors": (
        226_646_028,
        "sha256",
        "5dead6180c93b24191ec73f46dfd6c79bcf2c19f68934a3efb4ecf19ec62d056",
    ),
    "source.spm": (
        453_945,
        "git",
        "d6935b67eadbb82d54091f82265ffef1a3407816",
    ),
    "target.spm": (
        450_961,
        "git",
        "60c6d9e545372df4abb1b612633d9dcee9d63f32",
    ),
    "tokenizer_config.json": (44, "git", "edceaebbf1e2450bd8993f363f9b0de1a7042627"),
    "vocab.json": (516_426, "git", "038b4285a8fab43348784c22c0345600d6661fad"),
}
MAX_DOWNLOAD_BYTES = 300_000_000
DATASET_IDS = (
    "google-smol-en-so",
    "tico19-somali-test-sample",
)


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


def verify_model_bundle(model_dir: Path) -> None:
    """Reject partial or altered model bundles before loading weights."""
    for name, pin in MODEL_FILES.items():
        if not _matches_pin(model_dir / name, pin):
            raise ValueError(f"Pinned Somali-to-English model file failed: {name}")


def download_model(workspace: Path, config) -> Path:
    """Download only immutable, hash-verified model files to the private cache."""
    model_dir = workspace / "cache" / "models" / MODEL_ID / MODEL_REVISION
    model_dir.mkdir(parents=True, exist_ok=True)
    hosts = set(config.allowed_download_hosts)
    opener = urllib.request.build_opener(AllowlistedRedirectHandler(hosts))
    total_size = sum(pin[0] for pin in MODEL_FILES.values())
    max_single_size = int(config.max_single_download_gib * 1024**3)
    max_total_size = int(config.max_download_gib * 1024**3)
    if any(pin[0] > max_single_size for pin in MODEL_FILES.values()):
        raise ValueError("A pinned model file exceeds the configured per-file cap.")
    if total_size > min(MAX_DOWNLOAD_BYTES, max_total_size):
        raise ValueError("Pinned Somali-to-English model exceeds its download cap.")

    for name, pin in MODEL_FILES.items():
        destination = model_dir / name
        if _matches_pin(destination, pin):
            continue
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
                received = 0
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > pin[0]:
                        raise ValueError(f"Download exceeded pinned size: {name}")
                    out.write(chunk)
            if received != pin[0] or not _matches_pin(temporary, pin):
                raise ValueError(f"Downloaded model file failed verification: {name}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    return model_dir


def _reverse_rows(rows: list[dict]) -> list[dict]:
    return [
        {"source_text": row["target_text"], "target_text": row["source_text"]}
        for row in rows
    ]


def _load_heldout(workspace: Path) -> dict[str, list[dict]]:
    return {
        dataset_id: _reverse_rows(_dataset_rows(workspace, dataset_id, "test"))
        for dataset_id in DATASET_IDS
    }


def train_candidate(
    model_dir: Path,
    workspace: Path,
    config,
    *,
    experiment_id: str,
    resume: bool,
    epochs: int,
) -> dict:
    """Train a private Somali-to-English LoRA adapter from the audited mixture."""
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

    if not config.training_enabled or not set(SOURCE_IDS).issubset(
        set(config.approved_source_ids)
    ):
        raise PermissionError("Private config does not approve the mixture sources.")
    if experiment_id != Path(experiment_id).name or not experiment_id.strip():
        raise ValueError("Experiment ID must be a nonempty path-safe name.")
    if not 1 <= epochs <= 5:
        raise ValueError("Epoch count must be between one and five.")
    manifest, train_rows, validation_rows, _ = prepare_marian_mixture(workspace, config)
    if not torch.cuda.is_available():
        raise RuntimeError("Reverse Marian training requires a CUDA GPU.")
    free_bytes, _total_bytes = torch.cuda.mem_get_info(0)
    if free_bytes < 4 * 1024**3:
        raise RuntimeError("At least 4 GiB free GPU memory is required.")
    torch.cuda.set_per_process_memory_fraction(0.50, 0)
    torch.set_num_threads(config.max_cpu_threads)

    experiment_dir = workspace / "experiments" / experiment_id
    checkpoint_dir = workspace / "checkpoints" / experiment_id
    adapter_dir = experiment_dir / "adapter-final"
    metadata_path = experiment_dir / "experiment.json"
    fingerprint = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dataset_id": MIXTURE_ID,
        "dataset_revision": manifest["dataset_revision"],
        "train_sha256": manifest["split_sha256"]["train.jsonl"],
        "validation_sha256": manifest["split_sha256"]["validation.jsonl"],
        "direction": "Somali-to-English",
        "epochs": epochs,
        "learning_rate": 1e-4,
        "train_batch_size": 2,
        "eval_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "lora_rank": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "v_proj"],
        "weight_decay": 0.01,
        "warmup_ratio": 0.03,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "checkpoint_steps": 500,
        "logging_steps": 25,
        "save_total_limit": 2,
        "seed": 1729,
        "fp16": True,
    }
    created_utc = datetime.now(UTC).isoformat()
    if metadata_path.exists():
        previous = json.loads(metadata_path.read_text(encoding="utf-8"))
        if previous.get("fingerprint") != fingerprint:
            raise ValueError("Existing experiment inputs changed; use a new ID.")
        if not resume:
            raise FileExistsError("Experiment exists; use --resume or choose a new ID.")
        created_utc = previous.get("created_utc", created_utc)
    elif resume:
        raise FileNotFoundError("No saved reverse candidate exists to resume.")

    experiment_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "created_utc": created_utc,
                "fingerprint": fingerprint,
                "model_license": MODEL_LICENSE,
                "dataset_attribution": manifest["attributions"],
                "training_rows": len(train_rows),
                "validation_rows": len(validation_rows),
                "automatic_promotion": False,
                "adapter_redistribution": "not reviewed",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    base_model = MarianMTModel.from_pretrained(
        str(model_dir),
        local_files_only=True,
        use_safetensors=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    )
    base_model.config.use_cache = False
    model = get_peft_model(
        base_model,
        LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            r=fingerprint["lora_rank"],
            lora_alpha=fingerprint["lora_alpha"],
            lora_dropout=fingerprint["lora_dropout"],
            target_modules=fingerprint["target_modules"],
            bias="none",
        ),
    )
    reverse_train = _reverse_rows(train_rows)
    reverse_validation = _reverse_rows(validation_rows)
    arguments = Seq2SeqTrainingArguments(
        output_dir=str(checkpoint_dir),
        num_train_epochs=fingerprint["epochs"],
        per_device_train_batch_size=fingerprint["train_batch_size"],
        per_device_eval_batch_size=fingerprint["eval_batch_size"],
        gradient_accumulation_steps=fingerprint["gradient_accumulation_steps"],
        learning_rate=fingerprint["learning_rate"],
        weight_decay=fingerprint["weight_decay"],
        warmup_ratio=fingerprint["warmup_ratio"],
        logging_steps=fingerprint["logging_steps"],
        eval_strategy="steps",
        eval_steps=fingerprint["checkpoint_steps"],
        label_names=["labels"],
        save_strategy="steps",
        save_steps=fingerprint["checkpoint_steps"],
        save_total_limit=fingerprint["save_total_limit"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=fingerprint["fp16"],
        dataloader_num_workers=0,
        report_to=[],
        seed=fingerprint["seed"],
        data_seed=fingerprint["seed"],
        save_safetensors=True,
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=arguments,
        train_dataset=_tokenize_rows(reverse_train, tokenizer),
        eval_dataset=_tokenize_rows(reverse_validation, tokenizer),
        data_collator=DataCollatorForSeq2Seq(
            tokenizer,
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
        "experiment_id": experiment_id,
        "fingerprint": fingerprint,
        "training_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "train_metrics": result.metrics,
        "best_validation_loss": trainer.state.best_metric,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "gpu": torch.cuda.get_device_name(0),
        "automatic_promotion": False,
    }
    (experiment_dir / "training-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def evaluate_model(
    model_dir: Path,
    workspace: Path,
    output_dir: Path,
    *,
    experiment_id: str | None = None,
) -> dict:
    """Score base and optional adapter on held-out Somali-to-English tests."""
    import torch
    from peft import PeftModel
    from transformers import MarianMTModel
    from transformers import MarianTokenizer

    tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = MarianMTModel.from_pretrained(
        str(model_dir),
        local_files_only=True,
        use_safetensors=True,
        device_map="cuda",
    ).eval()
    candidate = None
    if experiment_id:
        adapter_dir = workspace / "experiments" / experiment_id / "adapter-final"
        if not (adapter_dir / "adapter_model.safetensors").is_file():
            raise FileNotFoundError("The private reverse LoRA adapter is missing.")
        candidate = PeftModel.from_pretrained(
            model, str(adapter_dir), is_trainable=False
        ).eval()
    torch.set_num_threads(2)
    sets = _load_heldout(workspace)
    results = {}
    predictions = {}

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline Somali-to-English inference used the network.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    try:
        for name, rows in sets.items():
            if candidate is not None:
                with candidate.disable_adapter():
                    base_outputs = _generate(candidate, tokenizer, rows, torch)
                adapted_outputs = _generate(candidate, tokenizer, rows, torch)
            else:
                base_outputs = _generate(model, tokenizer, rows, torch)
                adapted_outputs = None
            references = [row["target_text"] for row in rows]
            results[name] = {"n": len(rows), "base": _score(references, base_outputs)}
            results[name]["evidence_use"] = "independent-held-out-screen"
            results[name]["base_exact_matches"] = sum(
                base.strip() == reference.strip()
                for base, reference in zip(base_outputs, references, strict=True)
            )
            if adapted_outputs is not None:
                results[name]["candidate"] = _score(references, adapted_outputs)
                results[name]["candidate_exact_matches"] = sum(
                    candidate_text.strip() == reference.strip()
                    for candidate_text, reference in zip(
                        adapted_outputs, references, strict=True
                    )
                )
                results[name]["delta"] = {
                    metric: round(
                        results[name]["candidate"][metric]
                        - results[name]["base"][metric],
                        4,
                    )
                    for metric in ("bleu", "chrf_plus_plus")
                }
            predictions[name] = [
                {
                    "source": row["source_text"],
                    "reference": reference,
                    "base": base,
                    "candidate": adapted,
                }
                for row, reference, base, adapted in zip(
                    rows,
                    references,
                    base_outputs,
                    adapted_outputs or [None] * len(base_outputs),
                    strict=True,
                )
            ]
    finally:
        socket.socket.connect = original_connect

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": MODEL_LICENSE,
        "network_during_inference": "blocked",
        "automatic_promotion": False,
        "experiment_id": experiment_id,
        "metrics": results,
        "independent_datasets": list(DATASET_IDS),
        "excluded_probe": {
            "dataset_id": "opus-infopankki-en-so",
            "reason": "OPUS pretraining contamination: 1173 of 1273 exact matches "
            "in the prior base-model screen. See the private baseline report.",
        },
        "limitations": [
            "The model is multilingual for Cushitic input, not Somali-exclusive.",
            "Automatic overlap metrics do not verify meaning or fluency.",
            "Small and domain-specific tests cannot establish general quality.",
        ],
    }
    (output_dir / "evaluation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "predictions.json").write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _generate(model, tokenizer, rows, torch) -> list[str]:
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
            tokens = model.generate(
                **encoded,
                max_new_tokens=128,
                num_beams=4,
                no_repeat_ngram_size=3,
            )
        outputs.extend(tokenizer.batch_decode(tokens, skip_special_tokens=True))
    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--train-mixture", action="store_true")
    parser.add_argument("--experiment-id")
    parser.add_argument("--evaluate-experiment-id")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from tools.translation_lab.workspace import default_workspace
    from tools.translation_lab.workspace import ensure_outside_repository

    workspace = args.workspace or default_workspace()
    config_path = args.config or workspace / "config" / "active.toml"
    config = load_config(config_path)
    if args.train_mixture and args.evaluate_experiment_id:
        raise ValueError("Choose training or evaluating an existing experiment.")
    experiment_id = args.experiment_id
    if args.train_mixture and not experiment_id:
        experiment_id = "opus-cus-en-lora-" + datetime.now(UTC).strftime(
            "%Y%m%d-%H%M%S"
        )
    output_dir = args.output_dir or workspace / "experiments" / (
        experiment_id
        or "opus-cus-en-screen-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    )
    repository = Path(__file__).resolve().parents[2]
    ensure_outside_repository(workspace, repository)
    ensure_outside_repository(output_dir, repository)
    model_dir = workspace / "cache" / "models" / MODEL_ID / MODEL_REVISION
    if not args.skip_download:
        model_dir = download_model(workspace, config)
    verify_model_bundle(model_dir)
    training_report = None
    if args.train_mixture:
        if experiment_id is None:
            raise RuntimeError("Training experiment ID was not initialized.")
        training_report = train_candidate(
            model_dir,
            workspace,
            config,
            experiment_id=experiment_id,
            resume=args.resume,
            epochs=args.epochs,
        )
    report = evaluate_model(
        model_dir,
        workspace,
        output_dir,
        experiment_id=(
            experiment_id if training_report else args.evaluate_experiment_id
        ),
    )
    print(
        json.dumps(
            {"training": training_report, "evaluation": report},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
