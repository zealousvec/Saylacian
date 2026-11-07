# SPDX-License-Identifier: AGPL-3.0-or-later
"""Count Somali source provenance in the official MT560 parallel indexes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from itertools import zip_longest
from pathlib import Path

from tools.benchmark_output import require_external_output
from tools.benchmark_output import save_json_atomic

SOURCE_PAGE = "https://opus.nlpl.eu/MT560"
LANGUAGE_URL = "https://object.pouta.csc.fi/OPUS-MT560/train.v1.lang.gz"
PROVENANCE_URL = "https://object.pouta.csc.fi/OPUS-MT560/train.v1.prov.gz"
STATS_URL = "https://object.pouta.csc.fi/OPUS-MT560/train.v1.tok.stats.tsv"
EXPECTED_SOMALI_ROWS = 161_865
SOURCE_FILE_PINS = {
    "language": {
        "bytes": 189_661_025,
        "sha256": "6acaded05cff515c72f24fc11a1aa09c29dc4425f3feaf074b198397f1c6f597",
    },
    "provenance": {
        "bytes": 544_325_160,
        "sha256": "38007e99d463dedd6ac3ef446fb7142f6dbf98716f538f3a1412618c917b691e",
    },
    "statistics": {
        "bytes": 12_638,
        "sha256": "95eb63cbd7c8783b429660ff792a60e2d7cb7882f42c99856c304ba7d893d257",
    },
}


def sha256_file(path: Path) -> str:
    """Hash a downloaded index without retaining its contents."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_stats(path: Path) -> dict[str, int]:
    counts = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.rstrip("\r\n").split("\t")
            if not fields or fields[0].lower() == "lang":
                continue
            if len(fields) < 2:
                raise ValueError(f"Malformed MT560 stats line {line_number}.")
            try:
                counts[fields[0].strip().lower()] = int(fields[1])
            except ValueError as error:
                raise ValueError(
                    f"Invalid sentence count on MT560 stats line {line_number}."
                ) from error
    return counts


def audit_provenance(
    language_path: Path,
    provenance_path: Path,
    stats_path: Path,
) -> dict:
    """Stream aligned indexes and summarize Somali row provenance only."""
    if not all(path.is_file() for path in (language_path, provenance_path, stats_path)):
        raise FileNotFoundError("All three pinned MT560 index files are required.")

    paths = {
        "language": language_path,
        "provenance": provenance_path,
        "statistics": stats_path,
    }
    for name, path in paths.items():
        expected = SOURCE_FILE_PINS[name]
        if path.stat().st_size != expected["bytes"]:
            raise ValueError(f"Pinned MT560 {name} file has an unexpected size.")
        if sha256_file(path) != expected["sha256"]:
            raise ValueError(f"Pinned MT560 {name} file failed its SHA-256 check.")

    stats = _read_stats(stats_path)
    if stats.get("som") != EXPECTED_SOMALI_ROWS:
        raise ValueError("Official MT560 stats do not match the expected Somali count.")

    language_counts = Counter()
    somali_sources = Counter()
    total_rows = 0
    with (
        gzip.open(language_path, "rt", encoding="utf-8", newline="") as languages,
        gzip.open(provenance_path, "rt", encoding="utf-8", newline="") as provenance,
    ):
        for row_number, pair in enumerate(zip_longest(languages, provenance), 1):
            language_line, provenance_line = pair
            if language_line is None or provenance_line is None:
                raise ValueError(
                    "MT560 language and provenance indexes have different row counts."
                )
            language = language_line.strip().lower()
            source = provenance_line.strip()
            if not language or not source:
                raise ValueError(f"Empty index field at MT560 row {row_number}.")
            language_counts[language] += 1
            if language == "som":
                somali_sources[source] += 1
            total_rows += 1

    if language_counts["som"] != EXPECTED_SOMALI_ROWS:
        raise ValueError("Somali row count differs from official MT560 statistics.")

    return {
        "schema_version": 1,
        "source": "OPUS MT560 official training indexes",
        "source_page": SOURCE_PAGE,
        "source_files": {
            "language": {
                "url": LANGUAGE_URL,
                "bytes": language_path.stat().st_size,
                "sha256": sha256_file(language_path),
            },
            "provenance": {
                "url": PROVENANCE_URL,
                "bytes": provenance_path.stat().st_size,
                "sha256": sha256_file(provenance_path),
            },
            "statistics": {
                "url": STATS_URL,
                "bytes": stats_path.stat().st_size,
                "sha256": sha256_file(stats_path),
            },
        },
        "total_aligned_index_rows": total_rows,
        "distinct_language_codes": len(language_counts),
        "somali_rows": language_counts["som"],
        "somali_source_counts": dict(
            sorted(somali_sources.items(), key=lambda item: (-item[1], item[0]))
        ),
        "official_somali_rows": stats["som"],
        "mirror_row_count_matches_official_somali_count": (
            stats["som"] == EXPECTED_SOMALI_ROWS
        ),
        "mirror_row_identity_verified": False,
        "training_authorized": False,
        "notes": [
            (
                "The official indexes identify source IDs and language labels, "
                "not sentence text."
            ),
            (
                "A matching row count does not prove the filtered mirror preserves "
                "official MT560 row identity or order."
            ),
            (
                "Source-level license and attribution review is still required "
                "before training."
            ),
            "No source or target text was read, emitted, or retained by this audit.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--languages", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = require_external_output(args.output)
    report = audit_provenance(args.languages, args.provenance, args.stats)
    save_json_atomic(output, report)
    print(json.dumps(report["somali_source_counts"], indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
