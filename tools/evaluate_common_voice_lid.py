# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate short-text detection on an authorized Common Voice LID TSV."""

import argparse
import csv
import hashlib
import heapq
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saylacian.core import language_detection

SUPPORTED_LABELS = {
    "en": "English",
    "fr": "French",
    "so": "Somali Latin",
}
THRESHOLDS = (0.80, 0.82, 0.83, 0.84, 0.85, 0.90)
REQUIRED_COLUMNS = {"id", "sentence", "lang", "split"}


def load_test_sentences(
    path: Path, per_language_limit: int = 500
) -> tuple[dict[str, list[tuple[str, str]]], dict[str, int], str]:
    """Load a stable bounded sample of short test rows and hash the full file."""
    if per_language_limit < 1:
        raise ValueError("Per-language sample limit must be at least one.")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    samples: dict[str, list[tuple[int, str, str]]] = {}
    eligible_counts: dict[str, int] = {}
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(
            reader.fieldnames
        ):
            raise ValueError("Common Voice TSV is missing required columns.")
        for row in reader:
            if row.get("split") != "test":
                continue
            language = (row.get("lang") or "").strip()
            row_id = (row.get("id") or "").strip()
            text = (row.get("sentence") or "").strip()
            if not language or not row_id:
                raise ValueError("Common Voice test row is missing its ID or language.")
            if 12 <= len(text) < 20 and len(text.split()) >= 3:
                eligible_counts[language] = eligible_counts.get(language, 0) + 1
                rank = int.from_bytes(
                    hashlib.sha256(f"{language}\0{row_id}".encode()).digest()[:8],
                    "big",
                )
                sample = samples.setdefault(language, [])
                candidate = (-rank, row_id, text)
                if len(sample) < per_language_limit:
                    heapq.heappush(sample, candidate)
                elif candidate > sample[0]:
                    heapq.heapreplace(sample, candidate)

    datasets = {
        language: sorted(
            ((row_id, text) for _, row_id, text in sample), key=lambda row: row[0]
        )
        for language, sample in samples.items()
    }
    return datasets, eligible_counts, digest.hexdigest()


def score_thresholds(
    datasets: dict[str, list[tuple[str, str]]],
    thresholds: tuple[float, ...] = THRESHOLDS,
) -> dict[str, object]:
    """Classify each eligible test row once and return aggregate counts only."""
    scored = []
    identifier = language_detection._identifier()
    for source_label, records in datasets.items():
        expected = SUPPORTED_LABELS.get(source_label)
        for _row_id, text in records:
            detected, confidence = identifier.classify(text)
            scored.append(
                (
                    source_label,
                    expected,
                    language_detection.SUPPORTED.get(detected),
                    confidence,
                )
            )

    results = {}
    for threshold in thresholds:
        counts = {
            "eligible": 0,
            "supported_label_eligible": 0,
            "correct_supported": 0,
            "supported_label_disagreement": 0,
            "unsupported_label_eligible": 0,
            "false_supported": 0,
            "unsupported_label_unidentified": 0,
            "abstained": 0,
            "by_source_label": {},
        }
        for source_label, expected, predicted, confidence in scored:
            counts["eligible"] += 1
            by_label = counts["by_source_label"].setdefault(
                source_label,
                {
                    "eligible": 0,
                    "correct_supported": 0,
                    "disagreement": 0,
                    "false_supported": 0,
                    "unidentified": 0,
                    "abstained": 0,
                },
            )
            by_label["eligible"] += 1
            if expected is not None:
                counts["supported_label_eligible"] += 1
            else:
                counts["unsupported_label_eligible"] += 1

            if confidence < threshold:
                counts["abstained"] += 1
                by_label["abstained"] += 1
            elif expected is not None:
                if predicted == expected:
                    counts["correct_supported"] += 1
                    by_label["correct_supported"] += 1
                else:
                    counts["supported_label_disagreement"] += 1
                    by_label["disagreement"] += 1
            elif predicted is None:
                counts["unsupported_label_unidentified"] += 1
                by_label["unidentified"] += 1
            else:
                counts["false_supported"] += 1
                by_label["false_supported"] += 1

        results[f"{threshold:.2f}"] = counts
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Authorized Mozilla Common Voice mcv_text_lid.tsv file.",
    )
    parser.add_argument(
        "--per-language-limit",
        type=int,
        default=500,
        help="Maximum deterministic short test rows evaluated per language (default: 500).",
    )
    arguments = parser.parse_args()
    try:
        datasets, eligible_counts, digest = load_test_sentences(
            arguments.data, arguments.per_language_limit
        )
        results = score_thresholds(datasets)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "source": "Mozilla Common Voice Text Language Identification dataset",
                "dataset_id": "cmj8ddapc02c8mb07l6wyr882",
                "license": "CC0-1.0",
                "file_sha256": digest,
                "split": "test",
                "criteria": "12-19 Unicode code points and at least three whitespace-separated words",
                "sampling": "Lowest SHA-256 ranks of language code and row ID, with a fixed per-language cap.",
                "per_language_limit": arguments.per_language_limit,
                "label_note": "Dataset language code is a source label, not a human review of each app prediction.",
                "thresholds": results,
                "eligible_counts_by_language": dict(sorted(eligible_counts.items())),
                "sampled_counts_by_language": {
                    language: len(records)
                    for language, records in sorted(datasets.items())
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
