# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate short-input language detection on Amazon's pinned MASSIVE 1.1 corpus."""

import argparse
import hashlib
import heapq
import json
import sys
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saylacian.core import language_detection

DATASET_ID = "AmazonScience/MASSIVE"
DATASET_REVISION = "1.1"
DATASET_URL = "https://amazon-massive-nlu-dataset.s3.amazonaws.com/amazon-massive-dataset-1.1.tar.gz"
DATASET_LICENSE = "CC-BY-4.0"
EXPECTED_SHA256 = "4cba5faa11c71437928e17cb1b9b3d8b8e727e7ea363a3a9a8045e19c0491577"
SUPPORTED_LABELS = {"en-US": "en", "fr-FR": "fr"}
THRESHOLDS = (0.70, 0.75, 0.80, 0.85, 0.90)
REQUIRED_FIELDS = {"id", "locale", "partition", "utt"}


def load_test_samples(
    path: Path,
    per_language_limit: int = 500,
    expected_sha256: str | None = EXPECTED_SHA256,
) -> tuple[dict[str, list[tuple[str, str]]], dict[str, dict[str, int]], str]:
    """Read the app-length gate from locale-labeled test rows."""
    if per_language_limit < 1:
        raise ValueError("Per-language sample limit must be at least one.")

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    file_sha256 = digest.hexdigest()
    if expected_sha256 is not None and file_sha256 != expected_sha256:
        raise ValueError("MASSIVE archive SHA-256 does not match the pinned release.")

    stats: dict[str, dict[str, int]] = {}
    samples: dict[str, list[tuple[int, str, str]]] = {}
    try:
        with tarfile.open(path, "r:gz") as archive:
            for member in archive:
                member_path = PurePosixPath(member.name)
                if (
                    not member.isfile()
                    or member_path.parent != PurePosixPath("1.1/data")
                    or member_path.suffix != ".jsonl"
                ):
                    continue
                locale = member_path.stem
                counts = stats.setdefault(
                    locale,
                    {
                        "test_rows": 0,
                        "short_gate_rows": 0,
                        "sampled_rows": 0,
                    },
                )
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ValueError(f"MASSIVE data file {locale} could not be read.")
                with extracted:
                    for line_number, line in enumerate(extracted, start=1):
                        try:
                            row = json.loads(line)
                        except (UnicodeDecodeError, json.JSONDecodeError) as error:
                            raise ValueError(
                                f"Invalid MASSIVE row in {locale} at line {line_number}."
                            ) from error
                        if not isinstance(row, dict) or not REQUIRED_FIELDS.issubset(
                            row
                        ):
                            raise ValueError(
                                f"MASSIVE row in {locale} at line {line_number} has an invalid schema."
                            )
                        if row["partition"] != "test":
                            continue
                        counts["test_rows"] += 1
                        text = row["utt"]
                        row_id = row["id"]
                        if not isinstance(text, str) or not isinstance(row_id, str):
                            raise TypeError(
                                f"MASSIVE row in {locale} at line {line_number} has invalid text or ID."
                            )
                        if row["locale"] != locale:
                            raise ValueError(
                                f"MASSIVE row in {locale} at line {line_number} has a mismatched locale."
                            )
                        text = text.strip()
                        if not 12 <= len(text) < 20 or len(text.split()) < 3:
                            continue
                        counts["short_gate_rows"] += 1
                        rank = int.from_bytes(
                            hashlib.sha256(f"{locale}\0{row_id}".encode()).digest()[:8],
                            "big",
                        )
                        sample = samples.setdefault(locale, [])
                        candidate = (-rank, row_id, text)
                        if len(sample) < per_language_limit:
                            heapq.heappush(sample, candidate)
                        elif candidate > sample[0]:
                            heapq.heapreplace(sample, candidate)
    except (tarfile.TarError, OSError) as error:
        raise ValueError("MASSIVE archive is not a readable gzip tar file.") from error

    if not {"en-US", "fr-FR"}.issubset(stats):
        raise ValueError("MASSIVE archive is missing English or French test data.")

    datasets = {}
    for locale, sample in samples.items():
        records = sorted(((row_id, text) for _, row_id, text in sample))
        datasets[locale] = records
        stats[locale]["sampled_rows"] = len(records)
    return datasets, stats, file_sha256


def score_thresholds(
    datasets: dict[str, list[tuple[str, str]]],
    thresholds: tuple[float, ...] = THRESHOLDS,
) -> dict[str, object]:
    """Classify each sampled text once and report aggregate counts only."""
    identifier = language_detection._identifier()
    scored = []
    for source_locale, records in datasets.items():
        expected = SUPPORTED_LABELS.get(source_locale)
        for _row_id, text in records:
            detected, confidence = identifier.classify(text)
            predicted = detected if detected in language_detection.SUPPORTED else None
            scored.append((source_locale, expected, predicted, confidence))

    results = {}
    for threshold in thresholds:
        counts = {
            "eligible": 0,
            "supported_label_eligible": 0,
            "correct_supported": 0,
            "supported_label_disagreement": 0,
            "unsupported_label_eligible": 0,
            "false_supported": 0,
            "unsupported_label_not_supported_by_app": 0,
            "abstained": 0,
            "by_source_locale": {},
        }
        for locale, expected, predicted, confidence in scored:
            counts["eligible"] += 1
            by_locale = counts["by_source_locale"].setdefault(
                locale,
                {
                    "eligible": 0,
                    "correct_supported": 0,
                    "disagreement": 0,
                    "false_supported": 0,
                    "not_supported_by_app": 0,
                    "abstained": 0,
                },
            )
            by_locale["eligible"] += 1
            if expected is None:
                counts["unsupported_label_eligible"] += 1
            else:
                counts["supported_label_eligible"] += 1

            if confidence < threshold:
                counts["abstained"] += 1
                by_locale["abstained"] += 1
            elif expected is None:
                if predicted is None:
                    counts["unsupported_label_not_supported_by_app"] += 1
                    by_locale["not_supported_by_app"] += 1
                else:
                    counts["false_supported"] += 1
                    by_locale["false_supported"] += 1
            elif predicted == expected:
                counts["correct_supported"] += 1
                by_locale["correct_supported"] += 1
            else:
                counts["supported_label_disagreement"] += 1
                by_locale["disagreement"] += 1
        results[f"{threshold:.2f}"] = counts
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        required=True,
        help="Official amazon-massive-dataset-1.1.tar.gz archive.",
    )
    parser.add_argument(
        "--per-language-limit",
        type=int,
        default=500,
        help="Maximum deterministic sample per locale (default: 500).",
    )
    arguments = parser.parse_args()
    try:
        datasets, source_stats, digest = load_test_samples(
            arguments.archive, arguments.per_language_limit
        )
        results = score_thresholds(datasets)
    except (OSError, TypeError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    print(
        json.dumps(
            {
                "source": DATASET_ID,
                "revision": DATASET_REVISION,
                "source_url": DATASET_URL,
                "license": DATASET_LICENSE,
                "archive_sha256": digest,
                "split": "test",
                "source_stats_by_locale": dict(sorted(source_stats.items())),
                "supported_source_labels": SUPPORTED_LABELS,
                "criteria": "12-19 Unicode code points, at least three words, and test split locale label",
                "sampling": "Lowest SHA-256 ranks of locale and row ID, capped per locale.",
                "per_language_limit": arguments.per_language_limit,
                "thresholds": results,
                "interpretation": (
                    "MASSIVE test locale is the source label; raw archive has no per-row "
                    "language-identification judgments. Only English and French are "
                    "supported source classes; Somali is absent. Intent-domain and "
                    "localized phrases do not establish fluent-Somali quality or "
                    "general translation quality."
                ),
                "data_handling": "Aggregate results only; corpus text is not emitted or bundled.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
