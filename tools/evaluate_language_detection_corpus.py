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
        "CC0 1.0",
    ),
    "fra": (
        "fra.tsv.bz2",
        "cf4509f2f3fd542222be2cf085d0d814ce3f9405263c5746bcc965d7e83dfd08",
        "French",
        "CC0 1.0",
    ),
    "som": (
        "som.tsv.bz2",
        "badcbfc4cf1d2e8eaef4e0ef09f8f3cc3442fe85e6d533eaa64de1d2eabf0fdb",
        "Somali Latin",
        "CC BY 2.0 France",
    ),
    "deu": (
        "deu.tsv.bz2",
        "ce1f925b5fa76535f970f0ff02dc35899a4dec6c2eefd526cf832b4c791625ea",
        None,
        "CC BY 2.0 France",
    ),
    "spa": (
        "spa.tsv.bz2",
        "29efd66854f11ad3480720ceda6e7b42563d40df4e660d9b0721c56a61753e9a",
        None,
        "CC BY 2.0 France",
    ),
    "ita": (
        "ita.tsv.bz2",
        "1cccd6614ee66899ebf6d22549a29a2b52531c68483e508c60decc7135a0c7cc",
        None,
        "CC BY 2.0 France",
    ),
    "por": (
        "por.tsv.bz2",
        "ddb8dc071797c5e52d97e7b3f0d607290881ab2bfae4004a7c37007811f1c234",
        None,
        "CC BY 2.0 France",
    ),
    "nld": (
        "nld.tsv.bz2",
        "87431fcb868dd4d2ac2a691b3934ecda7e9cfbde7a22970419afb668252fa374",
        None,
        "CC BY 2.0 France",
    ),
    "pol": (
        "pol.tsv.bz2",
        "34a0d8105ced64ebc77dc82aec67f50434a6f484d725a5cb3ffd6755fa2b3751",
        None,
        "CC BY 2.0 France",
    ),
    "swe": (
        "swe.tsv.bz2",
        "8c366cf7f259f7f349565e3ce772dd8e79b7d054ec8e42c4f852d0a7d77b2112",
        None,
        "CC BY 2.0 France",
    ),
    "rus": (
        "rus.tsv.bz2",
        "4cc471dbea673819ffada4735a9eadb4cd360074f9feee2fd6481bc5c7081760",
        None,
        "CC BY 2.0 France",
    ),
    "ara": (
        "ara.tsv.bz2",
        "c8d9c09f2db910ee1fb05054f0badb7a38195ea952b39f9e4ce5b92ec8ec70bc",
        None,
        "CC BY 2.0 France",
    ),
    "jpn": (
        "jpn.tsv.bz2",
        "25d727283d297f812b2c9ec36f3a6812a8a60ed9d6d5427978c4e020a83782c3",
        None,
        "CC BY 2.0 France",
    ),
    "cmn": (
        "cmn.tsv.bz2",
        "edf090f0e0a043792e379560ddb56816757baa3dc99541fdca999c83b98a47ee",
        None,
        "CC BY 2.0 France",
    ),
    "hin": (
        "hin.tsv.bz2",
        "7e45c13ea3ccb15ed68bbc655f41b3be5f387bd42d2613efda179b32c540621c",
        None,
        "CC BY 2.0 France",
    ),
}
THRESHOLDS = (0.80, 0.82, 0.83, 0.84, 0.85, 0.90)


def load_short_sentences(data_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """Read eligible sentence IDs and text after verifying each export hash."""
    datasets = {}
    for language, (filename, expected_hash, _label, _license) in DATASETS.items():
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
                sentence_id, text = fields[0], fields[2].strip()
                if 12 <= len(text) < 20 and len(text.split()) >= 3:
                    records.append((sentence_id, text))
        records.sort(key=lambda record: int(record[0]))
        datasets[language] = records
    return datasets


def score_thresholds(
    datasets: dict[str, list[tuple[str, str]]],
    thresholds: tuple[float, ...] = THRESHOLDS,
) -> dict[str, object]:
    """Sweep thresholds from one classification pass and report aggregates only."""
    scored = []
    identifier = language_detection._identifier()
    for code, records in datasets.items():
        expected = DATASETS[code][2]
        for index, (_sentence_id, text) in enumerate(records):
            detected, confidence = identifier.classify(text)
            scored.append(
                (
                    code,
                    "holdout" if index % 5 == 0 else "development",
                    expected,
                    language_detection.SUPPORTED.get(detected),
                    confidence,
                )
            )

    results = {}
    for threshold in thresholds:
        split_results = {
            split_name: {
                "eligible": 0,
                "correct_supported": 0,
                "source_label_disagreement": 0,
                "abstained": 0,
                "disagreement_by_source_label": {},
            }
            for split_name in ("development", "holdout")
        }
        for source, split_name, expected, predicted, confidence in scored:
            score = split_results[split_name]
            score["eligible"] += 1
            if confidence < threshold or predicted is None:
                score["abstained"] += 1
            elif predicted == expected:
                score["correct_supported"] += 1
            else:
                score["source_label_disagreement"] += 1
                by_source = score["disagreement_by_source_label"]
                by_source[source] = by_source.get(source, 0) + 1
        results[f"{threshold:.2f}"] = split_results
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Folder containing hash-pinned per-language Tatoeba TSV.bz2 exports.",
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
                "attribution": "Tatoeba (https://tatoeba.org); see license_by_language for each export",
                "license_by_language": {
                    code: license_name
                    for code, (
                        _filename,
                        _digest,
                        _label,
                        license_name,
                    ) in DATASETS.items()
                },
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
