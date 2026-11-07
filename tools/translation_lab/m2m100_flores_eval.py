# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent FLORES-200 devtest evaluation of a private M2M100 LoRA."""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path

from tools.translation_lab.flores_eval import ARCHIVE_SHA256
from tools.translation_lab.flores_eval import load_flores_devtest
from tools.translation_lab.flores_eval import sha256_file

CHECKPOINT_FIELDS = (
    "en-so-base",
    "en-so-candidate",
    "so-en-base",
    "so-en-candidate",
)


def _read_checkpoint(path: Path, header: dict, *, resume: bool) -> dict:
    if not path.exists():
        return {}
    if not resume:
        raise FileExistsError(f"Prediction checkpoint exists: {path}; pass --resume.")
    content = path.read_bytes()
    header_end = content.find(b"\n")
    if header_end < 0 or json.loads(content[:header_end].decode("utf-8")) != header:
        raise ValueError("M2M100 FLORES checkpoint fingerprint changed.")
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
        row = json.loads(line)
        identifier = row.get("id")
        if (
            not identifier
            or identifier in records
            or not all(row.get(key) for key in CHECKPOINT_FIELDS)
        ):
            raise ValueError("M2M100 FLORES checkpoint has an invalid row.")
        records[identifier] = row
    return records


def evaluate_m2m100_flores_devtest(
    workspace: Path,
    *,
    archive_path: Path,
    experiment_id: str,
    run_id: str,
    resume: bool = False,
) -> dict:
    """Compare a frozen M2M100 base with its private adapter on clean devtest."""
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

    from tools.translation_lab.m2m100_training import MAX_SEQUENCE_LENGTH
    from tools.translation_lab.m2m100_training import MODEL_ID
    from tools.translation_lab.m2m100_training import MODEL_REVISION
    from tools.translation_lab.m2m100_training import _preflight
    from tools.translation_lab.m2m100_training import _verify_model_bundle
    from tools.translation_lab.tico19_benchmark import audit_exact_overlap
    from tools.translation_lab.tico19_benchmark import load_training_rows
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
        raise PermissionError(
            "The experiment manifest does not confirm private status."
        )
    fingerprint = experiment.get("fingerprint", {})
    if (
        fingerprint.get("model_id") != MODEL_ID
        or fingerprint.get("model_revision") != MODEL_REVISION
    ):
        raise ValueError("Candidate does not match the pinned M2M100 base model.")
    model_dir = workspace / "cache" / "models" / "facebook-m2m100-418M" / MODEL_REVISION
    adapter_dir = experiment_dir / "adapter-final"
    adapter_path = adapter_dir / "adapter_model.safetensors"
    if not adapter_path.is_file():
        raise FileNotFoundError("Private M2M100 adapter weights are missing.")
    adapter_sha256 = sha256_file(adapter_path)
    model_manifest = _verify_model_bundle(workspace, model_dir)
    model_fingerprint = {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
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
    overlap_rows = [
        {"source_text": row["english"], "target_text": row["somali"]} for row in rows
    ]
    overlap = audit_exact_overlap(overlap_rows, train_rows)
    if any(
        overlap[key]
        for key in (
            "exact_pair_overlap",
            "exact_english_overlap",
            "exact_somali_overlap",
        )
    ):
        raise ValueError(
            f"FLORES devtest overlaps the candidate's training data: {overlap}"
        )

    report_dir = workspace / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = report_dir / f"{run_id}-predictions.jsonl"
    report_path = report_dir / f"{run_id}.json"
    if report_path.exists():
        raise FileExistsError(f"M2M100 FLORES report already exists: {report_path}")
    header = {
        "schema_version": 1,
        "archive_sha256": ARCHIVE_SHA256,
        "experiment_id": experiment_id,
        "model_fingerprint": model_fingerprint,
    }
    completed = _read_checkpoint(predictions_path, header, resume=resume)
    known_ids = {row["id"] for row in rows}
    if not set(completed).issubset(known_ids):
        raise ValueError("M2M100 checkpoint contains IDs outside FLORES devtest.")
    if not predictions_path.exists():
        predictions_path.write_text(
            json.dumps(header, sort_keys=True) + "\n", encoding="utf-8"
        )

    hardware = _preflight(torch, max_gpu_fraction=0.5)
    tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = M2M100ForConditionalGeneration.from_pretrained(
        str(model_dir),
        local_files_only=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    )
    candidate = PeftModel.from_pretrained(model, str(adapter_dir), is_trainable=False)
    candidate.eval()

    def generate(texts, source_language, target_language, *, adapted):
        tokenizer.src_lang = source_language
        outputs = []
        for start in range(0, len(texts), 8):
            batch = texts[start : start + 8]
            encoded = tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=MAX_SEQUENCE_LENGTH,
            ).to("cuda")
            with torch.inference_mode():
                if adapted:
                    generated = candidate.generate(
                        **encoded,
                        forced_bos_token_id=tokenizer.get_lang_id(target_language),
                        max_new_tokens=128,
                        num_beams=4,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.1,
                    )
                else:
                    with candidate.disable_adapter():
                        generated = candidate.generate(
                            **encoded,
                            forced_bos_token_id=tokenizer.get_lang_id(target_language),
                            max_new_tokens=128,
                            num_beams=4,
                            no_repeat_ngram_size=3,
                            repetition_penalty=1.1,
                        )
            outputs.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
        return outputs

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline candidate evaluation attempted network access.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    started = time.monotonic()
    initial_completed = len(completed)
    try:
        with predictions_path.open("a", encoding="utf-8", newline="\n") as stream:
            pending = [row for row in rows if row["id"] not in completed]
            for start in range(0, len(pending), 8):
                batch = pending[start : start + 8]
                english = [row["english"] for row in batch]
                somali = [row["somali"] for row in batch]
                en_so_base = generate(english, "en", "so", adapted=False)
                so_en_base = generate(somali, "so", "en", adapted=False)
                en_so_candidate = generate(english, "en", "so", adapted=True)
                so_en_candidate = generate(somali, "so", "en", adapted=True)
                for row, values in zip(
                    batch,
                    zip(
                        en_so_base,
                        en_so_candidate,
                        so_en_base,
                        so_en_candidate,
                        strict=True,
                    ),
                    strict=True,
                ):
                    record = {"id": row["id"]}
                    record.update(zip(CHECKPOINT_FIELDS, values, strict=True))
                    stream.write(
                        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                    )
                    stream.flush()
                    completed[row["id"]] = record
                elapsed = max(time.monotonic() - started, 1e-9)
                new_rows = len(completed) - initial_completed
                print(
                    f"M2M100 FLORES rows {len(completed)}/{len(rows)} | "
                    f"{new_rows / elapsed:.2f} new rows/s",
                    flush=True,
                )
    finally:
        socket.socket.connect = original_connect

    references = {
        "en-so": [row["somali"] for row in rows],
        "so-en": [row["english"] for row in rows],
    }
    metrics = {}
    for route, reference in references.items():
        base_key = f"{route}-base"
        candidate_key = f"{route}-candidate"
        base = [completed[row["id"]][base_key] for row in rows]
        adapted = [completed[row["id"]][candidate_key] for row in rows]
        bleu = BLEU()
        chrf = CHRF(word_order=2)
        metrics[route] = {
            "examples": len(rows),
            "base": {
                "bleu": round(bleu.corpus_score(base, [reference]).score, 4),
                "chrf_plus_plus": round(chrf.corpus_score(base, [reference]).score, 4),
            },
            "candidate": {
                "bleu": round(bleu.corpus_score(adapted, [reference]).score, 4),
                "chrf_plus_plus": round(
                    chrf.corpus_score(adapted, [reference]).score, 4
                ),
            },
        }
        metrics[route]["delta"] = {
            metric: round(
                metrics[route]["candidate"][metric] - metrics[route]["base"][metric],
                4,
            )
            for metric in ("bleu", "chrf_plus_plus")
        }

    report = {
        "schema_version": 1,
        "status": "COMPLETED",
        "benchmark": "FLORES-200",
        "split": "devtest",
        "license": "CC-BY-SA-4.0 evaluation-only",
        "rows_per_direction": len(rows),
        "archive_sha256": ARCHIVE_SHA256,
        "experiment_id": experiment_id,
        "model_fingerprint": model_fingerprint,
        "hardware": hardware,
        "exact_training_overlap": overlap,
        "metrics": metrics,
        "prediction_sha256": sha256_file(predictions_path),
        "predictions_path": str(predictions_path),
        "network_during_inference": "blocked",
        "automatic_promotion": False,
        "human_review": False,
        "limitations": [
            "Automatic overlap metrics do not measure human fluency.",
            "FLORES-200 devtest is evaluation-only and must not guide repeated sweeps.",
            "This candidate covers English and Somali only.",
        ],
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
