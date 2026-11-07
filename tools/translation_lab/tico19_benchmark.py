# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate private English-to-Somali candidates on official TICO-19 splits."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import socket
import statistics
import zipfile
from collections import Counter
from pathlib import Path

from tools.benchmark_output import require_external_output
from tools.benchmark_output import save_json_atomic
from tools.translation_lab.marian_candidate import MAX_SEQUENCE_LENGTH
from tools.translation_lab.marian_candidate import MODEL_ID
from tools.translation_lab.marian_candidate import MODEL_LICENSE
from tools.translation_lab.marian_candidate import MODEL_REVISION
from tools.translation_lab.marian_candidate import _score
from tools.translation_lab.marian_candidate import verify_model_bundle
from tools.translation_lab.prepare_data import _normalize

ARCHIVE_SHA256 = "0e82fc7ceaa877606c8934f32ead185716c9d2c54b3818f2a7ae655f5e7a08d8"
ARCHIVE_BYTES = 15_168_404
SPLIT_ROWS = {"dev": 971, "test": 2_100}
TSV_COLUMNS = (
    "sourceLang",
    "targetLang",
    "sourceString",
    "targetString",
    "stringID",
    "url",
    "license",
    "translator_ID",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(path: Path) -> None:
    if not path.is_file() or path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("TICO-19 archive size does not match the pinned source.")
    if sha256_file(path) != ARCHIVE_SHA256:
        raise ValueError("TICO-19 archive SHA-256 does not match the pin.")


def parse_tsv(stream) -> list[dict[str, str]]:
    """Read aligned English–Somali rows and retain each source's terms."""
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8"), delimiter="\t")
    if tuple(reader.fieldnames or ()) != TSV_COLUMNS:
        raise ValueError("TICO-19 TSV header differs from the published schema.")

    rows = []
    identifiers = set()
    for line_number, row in enumerate(reader, start=2):
        if row.get("sourceLang") != "en" or row.get("targetLang") != "so":
            raise ValueError(f"Unexpected language pair on TICO-19 line {line_number}.")
        required_text = ("sourceString", "targetString", "stringID", "license")
        if any(not (row.get(key) or "").strip() for key in required_text):
            raise ValueError(f"Required TICO-19 field is empty on line {line_number}.")
        identifier = row["stringID"]
        if identifier in identifiers:
            raise ValueError(f"Duplicate TICO-19 string ID: {identifier}")
        identifiers.add(identifier)
        rows.append(
            {
                "source_text": row["sourceString"],
                "target_text": row["targetString"],
                "record_id": identifier,
                "source_url": row["url"],
                "license": row["license"],
                "translator_id": row["translator_ID"],
            }
        )
    return rows


def load_split(archive_path: Path, split: str) -> list[dict[str, str]]:
    if split not in SPLIT_ROWS:
        raise ValueError("TICO-19 split must be dev or test.")
    verify_archive(archive_path)
    member = f"tico19-testset/{split}/{split}.en-so.tsv"
    with zipfile.ZipFile(archive_path) as archive:
        try:
            with archive.open(member) as stream:
                rows = parse_tsv(stream)
        except KeyError as error:
            raise ValueError(f"Pinned TICO-19 archive is missing {member}.") from error
    if len(rows) != SPLIT_ROWS[split]:
        raise ValueError(
            f"TICO-19 {split} row count changed: expected {SPLIT_ROWS[split]}, "
            f"found {len(rows)}."
        )
    return rows


def audit_exact_overlap(rows: list[dict], training_rows: list[dict]) -> dict:
    """Count exact source, target and pair overlaps against training data."""
    training_pairs = {
        (_normalize(row["source_text"]), _normalize(row["target_text"]))
        for row in training_rows
    }
    training_sources = {source for source, _ in training_pairs}
    training_targets = {target for _, target in training_pairs}
    pair_overlap = source_overlap = target_overlap = 0
    for row in rows:
        source = _normalize(row["source_text"])
        target = _normalize(row["target_text"])
        pair_overlap += (source, target) in training_pairs
        source_overlap += source in training_sources
        target_overlap += target in training_targets
    return {
        "training_pair_rows": len(training_rows),
        "unique_training_pairs": len(training_pairs),
        "exact_pair_overlap": pair_overlap,
        "exact_english_overlap": source_overlap,
        "exact_somali_overlap": target_overlap,
    }


def paired_sentence_chrf(
    references: list[str],
    base_predictions: list[str],
    candidate_predictions: list[str],
    *,
    bootstrap_samples: int = 2_000,
    seed: int = 1_729,
) -> dict:
    """Estimate paired sentence chrF++ change with a seeded bootstrap.

    The interval describes mean per-sentence chrF++ change. It complements,
    and does not replace, the corpus-level BLEU and chrF++ scores.
    """
    if not references or not (
        len(references) == len(base_predictions) == len(candidate_predictions)
    ):
        raise ValueError("Paired sentence scoring needs equal, non-empty inputs.")
    if bootstrap_samples < 1:
        raise ValueError("At least one bootstrap sample is required.")

    from sacrebleu.metrics import CHRF

    scorer = CHRF(word_order=2)
    deltas = [
        scorer.sentence_score(candidate, [reference]).score
        - scorer.sentence_score(base, [reference]).score
        for reference, base, candidate in zip(
            references, base_predictions, candidate_predictions, strict=True
        )
    ]
    rng = random.Random(seed)
    sample_count = len(deltas)
    bootstrap_means = sorted(
        statistics.mean(rng.choice(deltas) for _ in range(sample_count))
        for _ in range(bootstrap_samples)
    )
    lower_index = int(0.025 * bootstrap_samples)
    upper_index = min(int(0.975 * bootstrap_samples), bootstrap_samples - 1)
    return {
        "metric": "mean_sentence_chrf++",
        "n": sample_count,
        "mean_delta": round(statistics.mean(deltas), 4),
        "median_delta": round(statistics.median(deltas), 4),
        "candidate_wins": sum(delta > 0 for delta in deltas),
        "base_wins": sum(delta < 0 for delta in deltas),
        "ties": sum(delta == 0 for delta in deltas),
        "mean_delta_bootstrap_95_ci": [
            round(bootstrap_means[lower_index], 4),
            round(bootstrap_means[upper_index], 4),
        ],
        "bootstrap_samples": bootstrap_samples,
        "seed": seed,
    }


def load_training_rows(workspace: Path, experiment_id: str) -> list[dict]:
    experiment_path = workspace / "experiments" / experiment_id / "experiment.json"
    metadata = json.loads(experiment_path.read_text(encoding="utf-8"))
    fingerprint = metadata["fingerprint"]
    dataset_id = fingerprint["dataset_id"]
    revision = fingerprint["dataset_revision"]
    if dataset_id != "marian-mixture":
        raise ValueError(
            "The full TICO evaluator expects the Marian mixture candidate."
        )

    dataset_root = workspace / "data" / "prepared" / dataset_id / revision
    manifest = json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("dataset_revision") != revision:
        raise ValueError("Training mixture revision does not match its manifest.")
    train_path = dataset_root / "train.jsonl"
    expected_hash = manifest.get("split_sha256", {}).get(train_path.name)
    if not expected_hash or sha256_file(train_path) != expected_hash:
        raise ValueError("Training mixture checksum does not match its manifest.")
    if fingerprint.get("train_sha256") != expected_hash:
        raise ValueError("Candidate fingerprint does not match its training split.")
    return [
        json.loads(line)
        for line in train_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _generate(
    model,
    tokenizer,
    rows: list[dict],
    torch,
    *,
    device: str,
    batch_size: int,
) -> list[str]:
    outputs = []
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        encoded = tokenizer(
            [row["source_text"] for row in batch],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=MAX_SEQUENCE_LENGTH,
        ).to(device)
        with torch.inference_mode():
            tokens = model.generate(
                **encoded,
                max_length=128,
                num_beams=4,
                no_repeat_ngram_size=3,
            )
        outputs.extend(tokenizer.batch_decode(tokens, skip_special_tokens=True))
        completed = min(start + len(batch), len(rows))
        if completed == len(rows) or completed % 160 == 0:
            print(f"Generated {completed}/{len(rows)} TICO-19 rows", flush=True)
    return outputs


def evaluate_tico_split(
    workspace: Path,
    *,
    experiment_id: str,
    archive_path: Path,
    split: str = "dev",
    confirm_test: bool = False,
    limit: int | None = None,
    output_path: Path | None = None,
) -> dict:
    """Compare base and adapter on an isolated official development split."""
    if split == "test" and not confirm_test:
        raise PermissionError("Use --confirm-test only for a final test evaluation.")
    rows = load_split(archive_path, split)
    full_row_count = len(rows)
    if limit is not None:
        if split != "dev":
            raise ValueError("A row limit is allowed only for development runs.")
        if limit < 1:
            raise ValueError("The evaluation row limit must be positive.")
        rows = rows[:limit]
    train_rows = load_training_rows(workspace, experiment_id)
    overlap = audit_exact_overlap(rows, train_rows)
    if any(
        overlap[key]
        for key in (
            "exact_pair_overlap",
            "exact_english_overlap",
            "exact_somali_overlap",
        )
    ):
        raise ValueError(
            "Exact overlap with the training split prevents clean scoring."
        )

    model_dir = workspace / "cache" / "models" / MODEL_ID / MODEL_REVISION
    adapter_dir = workspace / "experiments" / experiment_id / "adapter-final"
    if not (adapter_dir / "adapter_model.safetensors").is_file():
        raise FileNotFoundError("Private candidate adapter is missing.")
    verify_model_bundle(model_dir)

    import torch
    from peft import PeftModel
    from transformers import MarianMTModel
    from transformers import MarianTokenizer

    torch.set_num_threads(2)

    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"
    batch_size = 16 if use_cuda else 2
    model_options = {"device_map": {"": 0}} if use_cuda else {}
    if use_cuda:
        free_memory, _ = torch.cuda.mem_get_info(0)
        if free_memory < 2 * 1024**3:
            raise RuntimeError("At least 2 GiB of free GPU memory is required.")
        torch.cuda.set_per_process_memory_fraction(0.50, 0)
        model_options["torch_dtype"] = torch.float16
    else:
        print("CUDA unavailable; evaluating on CPU with batch size 2.", flush=True)

    tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    base_model = MarianMTModel.from_pretrained(
        str(model_dir),
        local_files_only=True,
        use_safetensors=False,
        **model_options,
    ).eval()
    if not use_cuda:
        base_model.to(device)
    candidate = PeftModel.from_pretrained(
        base_model, str(adapter_dir), is_trainable=False
    ).eval()

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline TICO-19 evaluation attempted network access.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    try:
        with candidate.disable_adapter():
            base_predictions = _generate(
                candidate,
                tokenizer,
                rows,
                torch,
                device=device,
                batch_size=batch_size,
            )
        candidate_predictions = _generate(
            candidate,
            tokenizer,
            rows,
            torch,
            device=device,
            batch_size=batch_size,
        )
    finally:
        socket.socket.connect = original_connect

    references = [row["target_text"] for row in rows]
    report = {
        "experiment_id": experiment_id,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_license": MODEL_LICENSE,
        "inference_device": device,
        "dataset": "TICO-19 English-Somali",
        "split": split,
        "split_role": "development" if split == "dev" else "final-test",
        "row_count": len(rows),
        "split_row_count": full_row_count,
        "archive_bytes": ARCHIVE_BYTES,
        "archive_sha256": ARCHIVE_SHA256,
        "row_license_counts": dict(Counter(row["license"] for row in rows)),
        "exact_training_overlap": overlap,
        "network_during_inference": "blocked",
        "automatic_promotion": False,
        "metrics": {
            "base": _score(references, base_predictions),
            "candidate": _score(references, candidate_predictions),
            "paired_sentence_analysis": paired_sentence_chrf(
                references,
                base_predictions,
                candidate_predictions,
            ),
        },
        "predictions_file": None,
        "limitations": [
            "TICO-19 is health and COVID-19 domain text, not general language.",
            "BLEU and chrF++ are overlap metrics, not fluency judgments.",
            "Source licenses are per row; output remains private.",
            "No fluent Somali-speaker review was performed.",
        ],
    }
    report["metrics"]["delta"] = {
        metric: round(
            report["metrics"]["candidate"][metric] - report["metrics"]["base"][metric],
            4,
        )
        for metric in ("bleu", "chrf_plus_plus")
    }
    predictions = [
        {
            **row,
            "base": base,
            "candidate": adapted,
        }
        for row, base, adapted in zip(
            rows, base_predictions, candidate_predictions, strict=True
        )
    ]
    output = output_path or (
        workspace / "experiments" / experiment_id / f"tico19-{split}-report.json"
    )
    output = require_external_output(output)
    prediction_path = output.with_name(f"{output.stem}-predictions.json")
    report["predictions_file"] = str(prediction_path)
    save_json_atomic(prediction_path, predictions)
    save_json_atomic(output, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--split", choices=tuple(SPLIT_ROWS), default="dev")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Evaluate only the first N development rows for a quick hardware check.",
    )
    parser.add_argument(
        "--confirm-test",
        action="store_true",
        help="Allow the final test split to be scored; do not tune on it.",
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    from tools.translation_lab.workspace import default_workspace
    from tools.translation_lab.workspace import ensure_outside_repository

    args = build_parser().parse_args(argv)
    workspace = args.workspace or default_workspace()
    repository = Path(__file__).resolve().parents[2]
    ensure_outside_repository(workspace, repository)
    if not args.archive.is_file():
        raise SystemExit(f"TICO-19 archive not found: {args.archive}")
    if args.output:
        ensure_outside_repository(args.output, repository)
    report = evaluate_tico_split(
        workspace,
        experiment_id=args.experiment_id,
        archive_path=args.archive,
        split=args.split,
        confirm_test=args.confirm_test,
        limit=args.limit,
        output_path=args.output,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
