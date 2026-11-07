# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent FLORES-200 devtest evaluation of a private Marian LoRA."""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path

from tools.translation_lab.flores_eval import ARCHIVE_SHA256
from tools.translation_lab.flores_eval import load_flores_devtest
from tools.translation_lab.flores_eval import sha256_file

CHECKPOINT_FIELDS = ("base", "candidate")


def _read_checkpoint(path: Path, header: dict, *, resume: bool) -> dict:
    if not path.exists():
        return {}
    if not resume:
        raise FileExistsError(f"Prediction checkpoint exists: {path}; pass --resume.")
    content = path.read_bytes()
    header_end = content.find(b"\n")
    if header_end < 0 or json.loads(content[:header_end].decode("utf-8")) != header:
        raise ValueError("Marian FLORES checkpoint fingerprint changed.")
    body_start = header_end + 1
    if len(content) > body_start and not content.endswith(b"\n"):
        tail_start = content.rfind(b"\n") + 1
        try:
            tail = json.loads(content[tail_start:].decode("utf-8"))
            complete = bool(tail.get("id")) and all(
                tail.get(key) for key in CHECKPOINT_FIELDS
            )
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            complete = False
        if complete:
            with path.open("ab") as stream:
                stream.write(b"\n")
            content += b"\n"
        else:
            with path.open("r+b") as stream:
                stream.truncate(tail_start)
            content = content[:tail_start]
    records = {}
    for line in content[body_start:].decode("utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        identifier = record.get("id")
        if (
            not identifier
            or identifier in records
            or not all(record.get(key) for key in CHECKPOINT_FIELDS)
        ):
            raise ValueError("Marian FLORES checkpoint has a duplicate or invalid row.")
        records[identifier] = record
    return records


def evaluate_marian_flores_devtest(
    workspace: Path,
    *,
    archive_path: Path,
    experiment_id: str,
    run_id: str,
    resume: bool = False,
) -> dict:
    """Compare an existing Marian adapter/base on clean English-Somali devtest."""
    try:
        import torch
        from peft import PeftModel
        from transformers import MarianMTModel
        from transformers import MarianTokenizer
    except ImportError as error:
        raise RuntimeError(
            "Install the isolated training requirements before evaluation."
        ) from error

    from tools.translation_lab.m2m100_training import _preflight
    from tools.translation_lab.marian_candidate import GPU_MEMORY_FRACTION
    from tools.translation_lab.marian_candidate import MAX_SEQUENCE_LENGTH
    from tools.translation_lab.marian_candidate import MODEL_ID
    from tools.translation_lab.marian_candidate import MODEL_LICENSE
    from tools.translation_lab.marian_candidate import MODEL_REVISION
    from tools.translation_lab.marian_candidate import _score
    from tools.translation_lab.marian_candidate import verify_model_bundle
    from tools.translation_lab.tico19_benchmark import audit_exact_overlap
    from tools.translation_lab.tico19_benchmark import load_training_rows
    from tools.translation_lab.tico19_benchmark import paired_sentence_chrf
    from tools.translation_lab.workspace import ensure_outside_repository

    ensure_outside_repository(workspace, Path(__file__).resolve().parents[2])
    for label, value in (("experiment_id", experiment_id), ("run_id", run_id)):
        if (
            not value
            or value != Path(value).name
            or not all(
                char
                in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                for char in value
            )
        ):
            raise ValueError(f"{label} must be a path-safe identifier.")

    rows = load_flores_devtest(archive_path)
    experiment_dir = workspace / "experiments" / experiment_id
    experiment = json.loads(
        (experiment_dir / "experiment.json").read_text(encoding="utf-8")
    )
    if experiment.get("automatic_promotion") is not False:
        raise PermissionError("Experiment manifest does not confirm private status.")
    fingerprint = experiment.get("fingerprint", {})
    if (
        fingerprint.get("model_id") != MODEL_ID
        or fingerprint.get("model_revision") != MODEL_REVISION
    ):
        raise ValueError("Candidate does not match the pinned Marian base model.")
    model_dir = workspace / "cache" / "models" / MODEL_ID / MODEL_REVISION
    adapter_path = experiment_dir / "adapter-final" / "adapter_model.safetensors"
    if not adapter_path.is_file():
        raise FileNotFoundError("Private Marian adapter weights are missing.")
    adapter_sha256 = sha256_file(adapter_path)
    model_manifest = verify_model_bundle(model_dir)
    model_fingerprint = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_license": MODEL_LICENSE,
        "model_files": {
            item["name"]: item["sha256"] for item in model_manifest["files"]
        },
        "adapter_sha256": adapter_sha256,
        "training_sha256": fingerprint.get("train_sha256"),
        "dataset_revision": fingerprint.get("dataset_revision"),
    }
    if not model_fingerprint["training_sha256"]:
        raise ValueError("Candidate manifest is missing its training fingerprint.")

    train_rows = load_training_rows(workspace, experiment_id)
    overlap = audit_exact_overlap(
        [{"source_text": row["english"], "target_text": row["somali"]} for row in rows],
        train_rows,
    )
    if any(
        overlap[key]
        for key in (
            "exact_pair_overlap",
            "exact_english_overlap",
            "exact_somali_overlap",
        )
    ):
        raise ValueError(f"FLORES devtest overlaps candidate training data: {overlap}")

    report_dir = workspace / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = report_dir / f"{run_id}-predictions.jsonl"
    report_path = report_dir / f"{run_id}.json"
    if report_path.exists():
        raise FileExistsError(f"Marian FLORES report already exists: {report_path}")
    header = {
        "schema_version": 1,
        "archive_sha256": ARCHIVE_SHA256,
        "experiment_id": experiment_id,
        "model_fingerprint": model_fingerprint,
    }
    completed = _read_checkpoint(predictions_path, header, resume=resume)
    known_ids = {row["id"] for row in rows}
    if not set(completed).issubset(known_ids):
        raise ValueError("Marian checkpoint contains IDs outside FLORES devtest.")
    if not predictions_path.exists():
        predictions_path.write_text(
            json.dumps(header, sort_keys=True) + "\n", encoding="utf-8"
        )

    hardware = _preflight(torch, max_gpu_fraction=GPU_MEMORY_FRACTION)
    tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    base = MarianMTModel.from_pretrained(
        str(model_dir),
        local_files_only=True,
        torch_dtype=torch.float16,
        use_safetensors=False,
        device_map={"": 0},
    ).eval()
    candidate = PeftModel.from_pretrained(
        base, str(experiment_dir / "adapter-final"), is_trainable=False
    ).eval()

    def generate(texts: list[str], *, adapted: bool) -> list[str]:
        outputs = []
        for start in range(0, len(texts), 16):
            batch = texts[start : start + 16]
            encoded = tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=MAX_SEQUENCE_LENGTH,
            ).to("cuda")
            with torch.inference_mode():
                if adapted:
                    tokens = candidate.generate(
                        **encoded,
                        max_new_tokens=128,
                        num_beams=4,
                        no_repeat_ngram_size=3,
                    )
                else:
                    with candidate.disable_adapter():
                        tokens = candidate.generate(
                            **encoded,
                            max_new_tokens=128,
                            num_beams=4,
                            no_repeat_ngram_size=3,
                        )
            outputs.extend(tokenizer.batch_decode(tokens, skip_special_tokens=True))
        return outputs

    def deny_network(*_args, **_kwargs):
        raise AssertionError(
            "Offline Marian FLORES evaluation attempted network access."
        )

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    started = time.monotonic()
    initial_completed = len(completed)
    try:
        with predictions_path.open("a", encoding="utf-8", newline="\n") as stream:
            pending = [row for row in rows if row["id"] not in completed]
            for start in range(0, len(pending), 16):
                batch = pending[start : start + 16]
                english = [row["english"] for row in batch]
                base_outputs = generate(english, adapted=False)
                candidate_outputs = generate(english, adapted=True)
                for row, before, after in zip(
                    batch, base_outputs, candidate_outputs, strict=True
                ):
                    record = {"id": row["id"], "base": before, "candidate": after}
                    stream.write(
                        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                    )
                    stream.flush()
                    completed[row["id"]] = record
                elapsed = max(time.monotonic() - started, 1e-9)
                new_rows = len(completed) - initial_completed
                print(
                    f"Marian FLORES rows {len(completed)}/{len(rows)} | "
                    f"{new_rows / elapsed:.2f} new rows/s",
                    flush=True,
                )
    finally:
        socket.socket.connect = original_connect

    references = [row["somali"] for row in rows]
    base_outputs = [completed[row["id"]]["base"] for row in rows]
    candidate_outputs = [completed[row["id"]]["candidate"] for row in rows]
    base_metrics = _score(references, base_outputs)
    candidate_metrics = _score(references, candidate_outputs)
    installed_report_path = report_dir / "flores200-route-matrix-devtest-20261103.json"
    installed_metrics = None
    if installed_report_path.is_file():
        installed_metrics = json.loads(
            installed_report_path.read_text(encoding="utf-8")
        )["metrics"]["en-so"]
    report = {
        "schema_version": 1,
        "status": "COMPLETED",
        "benchmark": "FLORES-200",
        "split": "devtest",
        "license": "CC-BY-SA-4.0 evaluation-only",
        "rows": len(rows),
        "archive_sha256": ARCHIVE_SHA256,
        "experiment_id": experiment_id,
        "model_fingerprint": model_fingerprint,
        "hardware": hardware,
        "exact_training_overlap": overlap,
        "base": base_metrics,
        "candidate": candidate_metrics,
        "delta": {
            key: round(candidate_metrics[key] - base_metrics[key], 4)
            for key in ("bleu", "chrf_plus_plus")
        },
        "paired_sentence_chrf": paired_sentence_chrf(
            references, base_outputs, candidate_outputs
        ),
        "prediction_sha256": sha256_file(predictions_path),
        "predictions_path": str(predictions_path),
        "network_during_inference": "blocked",
        "automatic_promotion": False,
        "human_review": False,
        "installed_app_route_comparison": {
            "metrics": installed_metrics,
            "candidate_minus_app_chrf_plus_plus": (
                round(
                    candidate_metrics["chrf_plus_plus"]
                    - installed_metrics["chrf_plus_plus"],
                    4,
                )
                if installed_metrics is not None
                else None
            ),
        },
        "limitations": [
            "Automatic overlap metrics do not measure human fluency.",
            "FLORES devtest is evaluation-only and must not guide repeated sweeps.",
            "The experiment covers English-to-Somali only.",
        ],
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
