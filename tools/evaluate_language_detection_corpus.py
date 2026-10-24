# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score short-text detection against pinned, licensed Tatoeba sentence exports."""

import argparse
import bz2
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saylacian.core import language_detection

DATASETS = {
    "eng": (
        "eng.tsv.bz2",
        "a144a0c52f8be13bee7cc30eb109eb5836803f22128a8ef8376c1ca5c6c5cf8a",
        "English",
    ),
    "fra": (
        "fra.tsv.bz2",
        "cf4509f2f3fd542222be2cf085d0d814ce3f9405263c5746bcc965d7e83dfd08",
        "French",
    ),
    "som": (
        "som.tsv.bz2",
        "badcbfc4cf1d2e8eaef4e0ef09f8f3cc3442fe85e6d533eaa64de1d2eabf0fdb",
        "Somali Latin",
    ),
    "deu": (
        "deu.tsv.bz2",
        "df8c16713e5715a0e1343bc1195004463e7facee08863d3cd709cbf123a74587",
        None,
    ),
    "spa": (
        "spa.tsv.bz2",
        "e8cecab4e084fa4d9843f66c1dab90c5747057e0bc63a758c406235297b636c7",
        None,
    ),
}
THRESHOLDS = (0.80, 0.85)


def load_short_sentences(data_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Read eligible sentence IDs and text after verifying each export hash."""
    datasets = {}
    for language, (filename, expected_hash, _label) in DATASETS.items():
        path = data_dir / filename
        payload = path.read_bytes()
        actual_hash = hashlib.sha256(payload).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"SHA-256 mismatch for {filename}.")
        with bz2.open(path, mode="rt", encoding="utf-8") as source:
            records = []
            for line in source:
                fields = line.rstrip("\n").split("\t")
                if len(fields) < 3 or fields[1] != language:
                    continue
                sentence_id, text = fields[0], fields[2]
                if 12 <= len(text) < 20 and len(text.split()) >= 3:
                    records.append((sentence_id, text))
        records.sort(key=lambda record: int(record[0]))
        datasets[language] = records
    return datasets


def score_thresholds(
    datasets: dict[str, list[tuple[str, str]]],
    thresholds: tuple[float, ...] = THRESHOLDS,
) -> dict[str, object]:
    """Compare supported-language outputs and abstentions on deterministic splits."""
    results = {}
    original_threshold = language_detection.MIN_SHORT_CONFIDENCE
    try:
        for threshold in thresholds:
            language_detection.MIN_SHORT_CONFIDENCE = threshold
            split_results = {
                split_name: {
                    "eligible": 0,
                    "correct_supported": 0,
                    "false_supported": 0,
                    "abstained": 0,
                }
                for split_name in ("development", "holdout")
            }
            for code, records in datasets.items():
                expected = DATASETS[code][2]
                for index, (_sentence_id, text) in enumerate(records):
                    split_name = "holdout" if index % 5 == 0 else "development"
                    score = split_results[split_name]
                    score["eligible"] += 1
                    detected, _confidence, _message = (
                        language_detection.detect_language(text)
                    )
                    if detected is None:
                        score["abstained"] += 1
                    elif detected == expected:
                        score["correct_supported"] += 1
                    else:
                        score["false_supported"] += 1
            results[f"{threshold:.2f}"] = split_results
    finally:
        language_detection.MIN_SHORT_CONFIDENCE = original_threshold
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Folder containing eng.tsv.bz2, fra.tsv.bz2, som.tsv.bz2, deu.tsv.bz2, spa.tsv.bz2.",
    )
    arguments = parser.parse_args()
    try:
        datasets = load_short_sentences(arguments.data_dir)
        results = score_thresholds(datasets)
    except (OSError, EOFError, ValueError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "source": "Tatoeba per-language sentence exports",
                "attribution": "Tatoeba (https://tatoeba.org), CC BY 2.0 FR; *_CC0 exports where supplied",
                "criteria": "12-19 Unicode code points, at least three whitespace-separated words",
                "holdout": "Every fifth eligible sentence after sorting IDs numerically, within each language",
                "thresholds": results,
                "counts_by_language": {
                    code: len(records) for code, records in datasets.items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
