# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate a private M2M100 candidate on TICO-19 development data only."""

from __future__ import annotations

import argparse
import json
import socket
from collections import Counter
from pathlib import Path

from tools.benchmark_output import require_external_output
from tools.benchmark_output import save_json_atomic
from tools.translation_lab.m2m100_training import MODEL_ID
from tools.translation_lab.m2m100_training import MODEL_REVISION
from tools.translation_lab.m2m100_training import _read_jsonl
from tools.translation_lab.m2m100_training import _verify_model_bundle
from tools.translation_lab.marian_candidate import _score
from tools.translation_lab.prepare_data import _normalize
from tools.translation_lab.tico19_benchmark import ARCHIVE_BYTES
from tools.translation_lab.tico19_benchmark import ARCHIVE_SHA256
from tools.translation_lab.tico19_benchmark import SPLIT_ROWS
from tools.translation_lab.tico19_benchmark import load_split
from tools.translation_lab.tico19_benchmark import paired_sentence_chrf
from tools.translation_lab.tico19_benchmark import sha256_file

DEFAULT_EXPERIMENT_ID = "m2m100-smol-lora-20261031"
DEFAULT_BATCH_SIZE = 8
MAX_LENGTH = 256


def _load_training_rows(workspace: Path, experiment_id: str) -> list[dict]:
    """Load the verified training split recorded in candidate metadata."""
    experiment_dir = workspace / "experiments" / experiment_id
    metadata = json.loads((experiment_dir / "experiment.json").read_text("utf-8"))
    fingerprint = metadata.get("fingerprint", {})
    if (
        fingerprint.get("model_id") != MODEL_ID
        or fingerprint.get("model_revision") != MODEL_REVISION
        or fingerprint.get("dataset_id") not in {"google-smol-en-so", "marian-mixture"}
    ):
        raise ValueError("Candidate metadata does not match the pinned M2M100 setup.")

    dataset_id = fingerprint["dataset_id"]
    revision = fingerprint["dataset_revision"]
    dataset_dir = workspace / "data" / "prepared" / dataset_id / revision
    manifest_path = dataset_dir / "manifest.json"
    train_path = dataset_dir / "train.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hash = manifest.get("split_sha256", {}).get(train_path.name)
    if (
        manifest.get("dataset_revision") != revision
        or not expected_hash
        or sha256_file(train_path) != expected_hash
        or fingerprint.get("train_sha256") != expected_hash
        or fingerprint.get("source_revisions", {})
        != manifest.get("source_revisions", {})
        or fingerprint.get("source_licenses", {}) != manifest.get("source_licenses", {})
    ):
        raise ValueError("Candidate training data failed revision or hash checks.")
    rows = _read_jsonl(train_path)
    if dataset_id == "marian-mixture":
        source_licenses = manifest.get("source_licenses", {})
        if not source_licenses or any(
            row.get("license") != source_licenses.get(row.get("source_id"))
            for row in rows
        ):
            raise ValueError("Mixture row-level source licenses failed verification.")
    return rows


def _check_overlap(dev_rows: list[dict], training_rows: list[dict]) -> dict:
    """Reject exact source, target, or pair overlap before scoring."""
    train_pairs = {
        (_normalize(row["source_text"]), _normalize(row["target_text"]))
        for row in training_rows
    }
    train_sources = {source for source, _ in train_pairs}
    train_targets = {target for _, target in train_pairs}
    overlap = Counter()
    for row in dev_rows:
        source = _normalize(row["source_text"])
        target = _normalize(row["target_text"])
        overlap["exact_pair"] += (source, target) in train_pairs
        overlap["exact_english"] += source in train_sources
        overlap["exact_somali"] += target in train_targets
    result = dict(overlap)
    for key in ("exact_pair", "exact_english", "exact_somali"):
        result.setdefault(key, 0)
    if any(result.values()):
        raise ValueError(f"Exact training overlap detected: {result}")
    return result


def _make_routes(rows: list[dict]) -> dict[str, list[dict]]:
    """Build evaluation examples for both directions from aligned TICO rows."""
    return {
        "en-so": [
            {"source": row["source_text"], "reference": row["target_text"]}
            for row in rows
        ],
        "so-en": [
            {"source": row["target_text"], "reference": row["source_text"]}
            for row in rows
        ],
    }


def _generate(
    model,
    tokenizer,
    examples: list[dict],
    torch,
    *,
    source_language: str,
    target_language: str,
    batch_size: int,
) -> list[str]:
    predictions = []
    tokenizer.src_lang = source_language
    for start in range(0, len(examples), batch_size):
        batch = examples[start : start + batch_size]
        tokens = tokenizer(
            [item["source"] for item in batch],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
        ).to("cuda")
        with torch.inference_mode():
            generated = model.generate(
                **tokens,
                forced_bos_token_id=tokenizer.get_lang_id(target_language),
                max_new_tokens=128,
                num_beams=4,
                no_repeat_ngram_size=3,
                repetition_penalty=1.1,
            )
        predictions.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
        complete = min(start + len(batch), len(examples))
        if complete == len(examples) or complete % 160 == 0:
            print(
                f"Generated {source_language}->{target_language} "
                f"{complete}/{len(examples)}",
                flush=True,
            )
    return predictions


def evaluate_tico19_dev(
    workspace: Path,
    *,
    model_dir: Path,
    experiment_id: str = DEFAULT_EXPERIMENT_ID,
    archive_path: Path,
    output_path: Path,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    """Score base and LoRA M2M100 on the official dev split, never the test."""
    if batch_size < 1 or batch_size > 16:
        raise ValueError("Batch size must be between 1 and 16.")
    rows = load_split(archive_path, "dev")
    if len(rows) != SPLIT_ROWS["dev"]:
        raise ValueError("TICO-19 development split has an unexpected row count.")
    training_rows = _load_training_rows(workspace, experiment_id)
    overlap = _check_overlap(rows, training_rows)

    experiment_dir = workspace / "experiments" / experiment_id
    adapter_dir = experiment_dir / "adapter-final"
    adapter_file = adapter_dir / "adapter_model.safetensors"
    if not adapter_file.is_file():
        raise FileNotFoundError("Private M2M100 adapter weights are missing.")
    _verify_model_bundle(workspace, model_dir)

    try:
        import torch
        from peft import PeftModel
        from transformers import M2M100ForConditionalGeneration
        from transformers import M2M100Tokenizer
    except ImportError as error:
        raise RuntimeError(
            "Install the isolated translation training runtime."
        ) from error

    if not torch.cuda.is_available():
        raise RuntimeError("This full M2M100 evaluation requires the CUDA GPU.")
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    if free_bytes < 3 * 1024**3:
        raise RuntimeError("At least 3 GiB of free GPU memory is required.")
    torch.cuda.set_per_process_memory_fraction(0.55, 0)
    torch.set_num_threads(2)

    tokenizer = M2M100Tokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = M2M100ForConditionalGeneration.from_pretrained(
        str(model_dir),
        local_files_only=True,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map={"": 0},
    ).eval()
    candidate = PeftModel.from_pretrained(
        model, str(adapter_dir), is_trainable=False
    ).eval()

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline TICO evaluation attempted network access.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    route_examples = _make_routes(rows)
    base_predictions = {}
    candidate_predictions = {}
    try:
        with candidate.disable_adapter():
            for route, languages in (("en-so", ("en", "so")), ("so-en", ("so", "en"))):
                base_predictions[route] = _generate(
                    candidate,
                    tokenizer,
                    route_examples[route],
                    torch,
                    source_language=languages[0],
                    target_language=languages[1],
                    batch_size=batch_size,
                )
        for route, languages in (("en-so", ("en", "so")), ("so-en", ("so", "en"))):
            candidate_predictions[route] = _generate(
                candidate,
                tokenizer,
                route_examples[route],
                torch,
                source_language=languages[0],
                target_language=languages[1],
                batch_size=batch_size,
            )
    finally:
        socket.socket.connect = original_connect

    route_report = {}
    prediction_rows = []
    for route, examples in route_examples.items():
        references = [item["reference"] for item in examples]
        base = base_predictions[route]
        adapted = candidate_predictions[route]
        base_score = _score(references, base)
        candidate_score = _score(references, adapted)
        route_report[route] = {
            "examples": len(examples),
            "base": base_score,
            "candidate": candidate_score,
            "delta": {
                "bleu": round(candidate_score["bleu"] - base_score["bleu"], 4),
                "chrf_plus_plus": round(
                    candidate_score["chrf_plus_plus"] - base_score["chrf_plus_plus"],
                    4,
                ),
            },
            "paired_sentence_chrf": paired_sentence_chrf(
                references,
                base,
                adapted,
            ),
        }
        prediction_rows.extend(
            {
                "route": route,
                "source": item["source"],
                "reference": item["reference"],
                "base": base_prediction,
                "candidate": candidate_prediction,
            }
            for item, base_prediction, candidate_prediction in zip(
                examples, base, adapted, strict=True
            )
        )

    output_path = require_external_output(output_path)
    predictions_path = output_path.with_name(f"{output_path.stem}-predictions.json")
    report = {
        "schema_version": 1,
        "status": "PRIVATE_DEV_EVALUATION_ONLY",
        "experiment_id": experiment_id,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "dataset": "TICO-19 English-Somali",
        "split": "dev",
        "split_role": "model-development-only",
        "archive_bytes": ARCHIVE_BYTES,
        "archive_sha256": ARCHIVE_SHA256,
        "row_count": len(rows),
        "license_counts": dict(Counter(row["license"] for row in rows)),
        "exact_training_overlap": overlap,
        "inference": {
            "network": "blocked",
            "device": torch.cuda.get_device_name(0),
            "gpu_free_mib_at_start": free_bytes // 1024**2,
            "gpu_total_mib": total_bytes // 1024**2,
            "memory_fraction_cap": 0.55,
            "batch_size": batch_size,
        },
        "automatic_promotion": False,
        "human_review": "not performed",
        "metrics": route_report,
        "predictions_file": str(predictions_path),
        "limitations": [
            "TICO-19 is health and COVID-19 domain text, not general language.",
            "BLEU and chrF++ are overlap measures, not fluency judgments.",
            "No fluent Somali-speaker review was performed.",
            "The held-out TICO-19 test split was not loaded or scored.",
            "The output remains private and candidate weights are not promoted.",
        ],
    }
    save_json_atomic(predictions_path, prediction_rows)
    save_json_atomic(output_path, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--experiment-id", default=DEFAULT_EXPERIMENT_ID)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate_tico19_dev(
        args.workspace,
        model_dir=args.model_dir,
        experiment_id=args.experiment_id,
        archive_path=args.archive,
        output_path=args.output,
        batch_size=args.batch_size,
    )
    print(json.dumps(report["metrics"], indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
