# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate short Somali detection on a pinned, licensed Qor corpus export."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saylacian.core import language_detection

DATASET_ID = "unkadlabs/qor-af-soomaali"
DATASET_REVISION = "5234876e5019cc4b1c79096c9f046fe2f8113b1e"
DATASET_URL = (
    "https://huggingface.co/datasets/unkadlabs/qor-af-soomaali/resolve/"
    f"{DATASET_REVISION}/data/sentences.jsonl"
)
DATASET_LICENSE = "CC-BY-SA-4.0"
EXPECTED_SHA256 = "f53ec99fbbd620ac65412d0c26c62a80faa534b9a939e95a0da6c53d5b38c60c"
REQUIRED_FIELDS = {"id", "text_so", "verified", "license"}
THRESHOLDS = (0.70, 0.75, 0.80, 0.85, 0.90)


def load_short_somali_rows(
    path: Path,
    expected_sha256: str | None = EXPECTED_SHA256,
) -> tuple[list[str], dict[str, int], str]:
    """Load licensed, verified rows that satisfy the app's short-input gate."""
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("Qor corpus SHA-256 does not match the pinned revision.")

    counts = {"rows": 0, "verified_licensed": 0, "eligible": 0}
    texts = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON row at line {line_number}.") from error
        if not isinstance(row, dict) or not REQUIRED_FIELDS.issubset(row):
            raise ValueError(f"Qor corpus row {line_number} has an invalid schema.")
        counts["rows"] += 1
        if row["verified"] is not True or row["license"] != DATASET_LICENSE:
            continue
        counts["verified_licensed"] += 1
        text = row["text_so"]
        if not isinstance(text, str):
            raise TypeError(f"Qor corpus row {line_number} has invalid text data.")
        text = text.strip()
        if 12 <= len(text) < 20 and len(text.split()) >= 3:
            counts["eligible"] += 1
            texts.append(text)
    return texts, counts, digest


def evaluate(texts: list[str]) -> dict[str, dict[str, int | float]]:
    """Classify each row once and report Somali recall-like aggregate counts."""
    identifier = language_detection._identifier()
    scored = [identifier.classify(text) for text in texts]
    reports = {}
    for threshold in THRESHOLDS:
        predicted_somali = sum(
            code == "so" and confidence >= threshold for code, confidence in scored
        )
        predicted_other = sum(
            code != "so" and confidence >= threshold for code, confidence in scored
        )
        abstained = len(texts) - predicted_somali - predicted_other
        reports[f"{threshold:.2f}"] = {
            "eligible_somali_rows": len(texts),
            "predicted_somali": predicted_somali,
            "predicted_other_language": predicted_other,
            "abstained_below_threshold": abstained,
            "somali_detection_share": (
                round(predicted_somali / len(texts), 4) if texts else 0.0
            ),
        }
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Authorized data/sentences.jsonl from the pinned Qor dataset revision.",
    )
    arguments = parser.parse_args()
    try:
        texts, counts, digest = load_short_somali_rows(arguments.data)
        results = evaluate(texts)
    except (OSError, UnicodeError, TypeError, ValueError) as error:
        parser.error(str(error))

    print(
        json.dumps(
            {
                "source": DATASET_ID,
                "revision": DATASET_REVISION,
                "source_url": DATASET_URL,
                "license": DATASET_LICENSE,
                "file_sha256": digest,
                "source_counts": counts,
                "criteria": (
                    "verified CC BY-SA 4.0 rows; 12-19 Unicode code points and "
                    "at least three whitespace-separated words"
                ),
                "thresholds": results,
                "interpretation": (
                    "Somali-only detection share on this source; not precision, "
                    "overall accuracy, translation quality, or specialist review "
                    "of each short sentence."
                ),
                "data_handling": (
                    "Aggregate results only; do not publish sentence text."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
