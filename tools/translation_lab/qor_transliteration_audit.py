# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit script-table coverage on the pinned Qor Somali corpus release."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import unicodedata
from collections import Counter
from datetime import UTC
from datetime import datetime
from pathlib import Path

from saylacian.core.transliteration import SCRIPT_LATIN_TO_PUA
from saylacian.core.transliteration import SOMALI_TO_OSMANYA
from saylacian.core.transliteration import transliterate
from tools.benchmark_output import new_benchmark_output
from tools.benchmark_output import require_external_output
from tools.benchmark_output import save_json_atomic
from tools.translation_lab.sources import load_catalog

REPOSITORY = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPOSITORY / "research" / "sources.catalog.json"
SOURCE_ID = "unkadlabs-qor-af-soomaali-mono"
EXPECTED_REVISION = "5234876e5019cc4b1c79096c9f046fe2f8113b1e"
SAMPLE_LIMIT = 200
MAPPINGS = {"Osmanya": SOMALI_TO_OSMANYA, **SCRIPT_LATIN_TO_PUA}
TOKENS = {
    script: tuple(sorted(mapping, key=len, reverse=True))
    for script, mapping in MAPPINGS.items()
}


def load_source_record(catalog_path: Path = CATALOG_PATH) -> dict:
    """Require the pinned, process-approved record; training stays unapproved."""
    matches = [
        item for item in load_catalog(catalog_path) if item["source_id"] == SOURCE_ID
    ]
    if len(matches) != 1:
        raise ValueError("The pinned Qor source record is missing or duplicated.")
    source = matches[0]
    if source.get("revision") != EXPECTED_REVISION:
        raise ValueError("The Qor source revision changed; review it before auditing.")
    if source.get("license") != "CC-BY-SA-4.0":
        raise ValueError("The Qor dataset licence changed; review it before auditing.")
    rights = source.get("rights", {})
    if rights.get("download") != "allowed" or rights.get("process") != "allowed":
        raise PermissionError("The Qor source is not approved for local processing.")
    if source.get("owner_approved") is not False:
        raise ValueError("Unexpected Qor owner-approval state; review the source.")
    if rights.get("train") != "approval_required":
        raise ValueError("Training permission changed; review the source record.")
    return source


def _sentence_artifact(source: dict) -> dict:
    artifacts = [
        item
        for item in source.get("artifacts", [])
        if item.get("filename") == "qor-af-soomaali-5234876e-data-sentences.jsonl"
    ]
    if len(artifacts) != 1:
        raise ValueError("The pinned sentence artifact is missing or duplicated.")
    return artifacts[0]


def _count_coverage(text: str, mapping: dict[str, str], tokens: tuple[str, ...]):
    mapped = 0
    units = 0
    unmapped = Counter()
    index = 0
    while index < len(text):
        token = next(
            (
                item
                for item in tokens
                if text[index : index + len(item)].casefold() == item
            ),
            None,
        )
        if token:
            mapped += 1
            units += 1
            index += len(token)
            continue

        character = text[index]
        if character.isalpha():
            units += 1
            unmapped[f"U+{ord(character):04X}"] += 1
        index += 1
    return mapped, units, unmapped


def _retain_sample(heap: list, seen: set[str], text: str) -> None:
    normalized = unicodedata.normalize("NFC", text).casefold()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    if digest in seen:
        return
    priority = int(digest, 16)
    entry = (-priority, digest, text)
    if len(heap) < SAMPLE_LIMIT:
        heapq.heappush(heap, entry)
        seen.add(digest)
    elif priority < -heap[0][0]:
        removed = heapq.heapreplace(heap, entry)
        seen.remove(removed[1])
        seen.add(digest)


def audit_qor_corpus(path: Path, source: dict | None = None) -> dict:
    """Return aggregate mapping results without storing any source sentence."""
    source = source or load_source_record()
    artifact = _sentence_artifact(source)
    if path.stat().st_size != artifact["expected_bytes"]:
        raise ValueError("The Qor sentence file size does not match its catalog pin.")

    file_hash = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            file_hash.update(chunk)
    if file_hash.hexdigest() != artifact["sha256"]:
        raise ValueError("The Qor sentence file hash does not match its catalog pin.")

    totals = {
        script: {
            "sentences": 0,
            "mapped_units": 0,
            "alphabetic_units": 0,
            "unmapped": Counter(),
        }
        for script in MAPPINGS
    }
    sample_heap: list = []
    sample_hashes: set[str] = set()
    unique_hashes: set[str] = set()
    sectors = Counter()

    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid Qor JSON on line {line_number}.") from error
            if (
                row.get("license") != source["license"]
                or row.get("verified") is not True
                or row.get("mode") != "write"
            ):
                raise ValueError(f"Qor row {line_number} failed its source checks.")
            raw_text = row.get("text_so")
            if not isinstance(raw_text, str) or not raw_text.strip():
                raise ValueError(f"Qor row {line_number} has no Somali text.")

            text = unicodedata.normalize("NFC", raw_text)
            unique_hashes.add(hashlib.sha256(text.casefold().encode()).hexdigest())
            sectors[row.get("sector") or "unspecified"] += 1
            _retain_sample(sample_heap, sample_hashes, text)
            for script, mapping in MAPPINGS.items():
                stat = totals[script]
                mapped, units, unmapped = _count_coverage(text, mapping, TOKENS[script])
                stat["sentences"] += 1
                stat["mapped_units"] += mapped
                stat["alphabetic_units"] += units
                stat["unmapped"].update(unmapped)

    roundtrips = {script: Counter() for script in MAPPINGS}
    for _negative_priority, _digest, text in sample_heap:
        expected = unicodedata.normalize("NFC", text).casefold()
        for script in MAPPINGS:
            encoded = transliterate(text, "Somali Latin", script)
            decoded = transliterate(encoded.text, script, "Somali Latin")
            actual = unicodedata.normalize("NFC", decoded.text).casefold()
            if actual == expected:
                roundtrips[script]["primary_matches"] += 1
            elif expected in {
                unicodedata.normalize("NFC", item).casefold()
                for item in decoded.alternatives
            }:
                roundtrips[script]["alternative_recoveries"] += 1
            else:
                roundtrips[script]["unresolved"] += 1

    scripts = {}
    for script, stat in totals.items():
        units = stat["alphabetic_units"]
        scripts[script] = {
            "sentences": stat["sentences"],
            "mapped_units": stat["mapped_units"],
            "alphabetic_units": units,
            "mapping_coverage": round(stat["mapped_units"] / units, 6)
            if units
            else None,
            "unmapped_codepoints": dict(sorted(stat["unmapped"].items())),
            "roundtrip_sample": {
                **roundtrips[script],
                "unique_texts": len(sample_heap),
                "selection": "smallest SHA-256 hashes of normalized text",
            },
        }

    return {
        "schema_version": 1,
        "created_utc": datetime.now(UTC).isoformat(),
        "source_id": source["source_id"],
        "source_revision": source["revision"],
        "license": source["license"],
        "source_page": source["source_page"],
        "input_sha256": artifact["sha256"],
        "input_bytes": artifact["expected_bytes"],
        "sentence_count": sum(item["sentences"] for item in totals.values())
        // len(MAPPINGS),
        "unique_sentence_count": len(unique_hashes),
        "sector_counts": dict(sorted(sectors.items())),
        "scripts": scripts,
        "source_text_saved": False,
        "training_performed": False,
        "scope": (
            "Read only the pinned sentences.jsonl file; the separate canary file "
            "was not read. Mapping coverage and round trips assess table behavior, "
            "not spelling correctness or historical use. This source is not approved "
            "for model training."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = load_source_record()
    report = audit_qor_corpus(args.input, source)
    output = require_external_output(
        args.output or new_benchmark_output("qor-transliteration-audit")
    )
    save_json_atomic(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"Report saved outside the repository: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
