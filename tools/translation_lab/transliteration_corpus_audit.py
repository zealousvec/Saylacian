# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure script-mapping coverage on approved Somali corpus train/val rows."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import unicodedata
from collections import Counter
from collections.abc import Iterator
from datetime import UTC
from datetime import datetime
from pathlib import Path

from saylacian.core.transliteration import SCRIPT_LATIN_TO_PUA
from saylacian.core.transliteration import SOMALI_TO_OSMANYA
from saylacian.core.transliteration import transliterate
from tools.translation_lab.config import LabConfig
from tools.translation_lab.config import load_config
from tools.translation_lab.sources import read_owner_registry
from tools.translation_lab.sources import verify_approved_source

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = ("Osmanya", "Borama", "Kaddare")
ROUNDTRIP_SAMPLE_LIMIT = 200
ROUNDTRIP_SAMPLE_SEED = 1729


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _approved_source_records(workspace: Path, config: LabConfig) -> dict[str, dict]:
    if not config.training_enabled:
        raise PermissionError("Corpus processing is disabled in the private config.")

    registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
    records = {item["source_id"]: item for item in registry}
    approved = set(config.approved_source_ids)
    somali_sources = {}

    for source_id in config.approved_source_ids:
        source = records.get(source_id)
        if source is None:
            raise PermissionError(f"Approved source record is missing: {source_id}")
        languages = source.get("languages", [])
        if "so" not in languages:
            continue
        verify_approved_source(
            source,
            approved,
            purpose="train",
            allow_noncommercial=config.allow_noncommercial_training,
        )
        if len(languages) != 2:
            raise ValueError(f"Unsupported language pair in source: {source_id}")
        somali_sources[source_id] = source

    if not somali_sources:
        raise ValueError("No approved Somali source is available for the audit.")
    return somali_sources


def iter_approved_somali_texts(
    workspace: Path,
    config: LabConfig,
    *,
    source_ids: tuple[str, ...] | None = None,
) -> Iterator[tuple[str, str, str, dict]]:
    """Yield Somali-side text from approved train and validation files only."""
    sources = _approved_source_records(workspace, config)
    selected = source_ids or tuple(sources)
    approved = set(config.approved_source_ids)

    for source_id in selected:
        source = sources.get(source_id)
        if source is None:
            raise PermissionError(f"Source is not approved for this audit: {source_id}")
        verify_approved_source(
            source,
            approved,
            purpose="train",
            allow_noncommercial=config.allow_noncommercial_training,
        )
        revision = source.get("revision")
        if not revision:
            raise ValueError(f"Approved source has no pinned revision: {source_id}")

        root = workspace / "data" / "prepared" / source_id / str(revision)
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Prepared source manifest is missing: {source_id}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("source_id") != source_id
            or manifest.get("dataset_revision") != revision
            or manifest.get("license") != source.get("license")
        ):
            raise ValueError(f"Prepared source identity changed: {source_id}")

        somali_field = (
            "source_text" if source["languages"][0] == "so" else "target_text"
        )
        for split_name in ("train", "validation"):
            path = root / f"{split_name}.jsonl"
            expected = manifest.get("split_sha256", {}).get(path.name)
            if not expected or _sha256(path) != expected:
                raise ValueError(
                    f"Prepared split checksum failed: {source_id}/{split_name}"
                )

            with path.open("r", encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise ValueError(
                            "Invalid JSON in "
                            f"{source_id}/{split_name} line {line_number}."
                        ) from error
                    text = row.get(somali_field)
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError(
                            "Missing Somali text in "
                            f"{source_id}/{split_name} line {line_number}."
                        )
                    yield source_id, split_name, text, manifest


def _mapping_for(script: str) -> dict[str, str]:
    return SOMALI_TO_OSMANYA if script == "Osmanya" else SCRIPT_LATIN_TO_PUA[script]


def _tokens_by_first_letter(mapping: dict[str, str]) -> dict[str, tuple[str, ...]]:
    tokens: dict[str, list[str]] = {}
    for token in sorted(mapping, key=len, reverse=True):
        tokens.setdefault(token[0], []).append(token)
    return {first: tuple(values) for first, values in tokens.items()}


MAPPING_TOKENS = {
    script: _tokens_by_first_letter(_mapping_for(script)) for script in SCRIPTS
}


def _count_mapping_units(text: str, script: str) -> tuple[int, Counter]:
    value = unicodedata.normalize("NFC", text)
    tokens = MAPPING_TOKENS[script]
    mapped = 0
    unmapped = Counter()
    index = 0

    while index < len(value):
        token = next(
            (
                item
                for item in tokens.get(value[index].casefold(), ())
                if value[index : index + len(item)].casefold() == item
            ),
            None,
        )
        if token is not None:
            mapped += 1
            index += len(token)
        else:
            character = value[index]
            if character.isalpha():
                unmapped[f"U+{ord(character):04X}"] += 1
            index += 1

    return mapped, unmapped


def _new_script_stats() -> dict:
    return {
        "sentences": 0,
        "alphabetic_units": 0,
        "mapped_units": 0,
        "unmapped_codepoints": Counter(),
        "roundtrip_sampled_sentences": 0,
        "primary_roundtrip_matches": 0,
        "primary_roundtrip_mismatches": 0,
        "alternative_roundtrip_recoveries": 0,
        "unresolved_roundtrip_mismatches": 0,
        "known_osmanya_ii_uu_ambiguities": 0,
    }


def _add_text(stats: dict, text: str, script: str) -> None:
    mapped, unmapped = _count_mapping_units(text, script)
    stats["sentences"] += 1
    stats["mapped_units"] += mapped
    stats["unmapped_codepoints"].update(unmapped)
    stats["alphabetic_units"] += mapped + sum(unmapped.values())

    if script == "Osmanya":
        stats["known_osmanya_ii_uu_ambiguities"] += sum(
            text.casefold().count(token) for token in ("ii", "uu")
        )


def _check_roundtrip(stats: dict, text: str, script: str) -> None:
    stats["roundtrip_sampled_sentences"] += 1
    converted = transliterate(text, "Somali Latin", script)
    restored = transliterate(converted.text, script, "Somali Latin")
    expected = unicodedata.normalize("NFC", text).casefold()
    actual = unicodedata.normalize("NFC", restored.text).casefold()
    if actual == expected:
        stats["primary_roundtrip_matches"] += 1
        return

    stats["primary_roundtrip_mismatches"] += 1
    alternatives = {
        unicodedata.normalize("NFC", value).casefold()
        for value in restored.alternatives
    }
    if expected in alternatives:
        stats["alternative_roundtrip_recoveries"] += 1
    else:
        stats["unresolved_roundtrip_mismatches"] += 1


def _retain_sample_text(
    sample_heaps: dict,
    selected_hashes: dict,
    sample_key: tuple[str, str],
    text: str,
) -> None:
    normalized = unicodedata.normalize("NFC", text).casefold()
    digest = hashlib.sha256(
        f"{ROUNDTRIP_SAMPLE_SEED}\0{sample_key[0]}\0{sample_key[1]}\0{normalized}".encode()
    ).hexdigest()
    heap = sample_heaps.setdefault(sample_key, [])
    retained = selected_hashes.setdefault(sample_key, set())
    if digest in retained:
        return

    priority = int(digest, 16)
    entry = (-priority, digest, text)
    if len(heap) < ROUNDTRIP_SAMPLE_LIMIT:
        heapq.heappush(heap, entry)
        retained.add(digest)
    elif priority < -heap[0][0]:
        removed = heapq.heapreplace(heap, entry)
        retained.remove(removed[1])
        retained.add(digest)


def _finalize_stats(stats: dict) -> dict:
    unmapped = stats["unmapped_codepoints"]
    total = stats["alphabetic_units"]
    return {
        **{key: value for key, value in stats.items() if key != "unmapped_codepoints"},
        "mapping_coverage": round(stats["mapped_units"] / total, 6) if total else None,
        "unmapped_codepoints": dict(sorted(unmapped.items())),
    }


def audit_corpus(
    workspace: Path,
    config: LabConfig,
    *,
    source_ids: tuple[str, ...] | None = None,
) -> dict:
    """Aggregate chart coverage without retaining any source sentence text."""
    sources = _approved_source_records(workspace, config)
    selected = source_ids or tuple(sources)
    records = {}
    totals = {script: _new_script_stats() for script in SCRIPTS}
    sample_heaps = {}
    selected_hashes = {}

    for source_id, split_name, text, manifest in iter_approved_somali_texts(
        workspace, config, source_ids=selected
    ):
        source_record = records.setdefault(
            source_id,
            {
                "revision": manifest["dataset_revision"],
                "license": manifest["license"],
                "source_page": manifest.get("source_page"),
                "attribution": manifest.get("attribution"),
                "input_split_sha256": {
                    name: manifest["split_sha256"][f"{name}.jsonl"]
                    for name in ("train", "validation")
                },
                "splits": {},
            },
        )
        split_stats = source_record["splits"].setdefault(
            split_name, {script: _new_script_stats() for script in SCRIPTS}
        )
        for script in SCRIPTS:
            _add_text(split_stats[script], text, script)
            _add_text(totals[script], text, script)

        _retain_sample_text(
            sample_heaps,
            selected_hashes,
            (source_id, split_name),
            text,
        )

    for (source_id, split_name), heap in sample_heaps.items():
        for _negative_priority, _digest, text in heap:
            for script in SCRIPTS:
                _check_roundtrip(
                    records[source_id]["splits"][split_name][script], text, script
                )
                _check_roundtrip(totals[script], text, script)

    return {
        "schema_version": 1,
        "created_utc": datetime.now(UTC).isoformat(),
        "sources": records,
        "totals": {script: _finalize_stats(stats) for script, stats in totals.items()},
        "scope": (
            "Approved source train and validation rows only; test files are not "
            "opened. Round trips use up to "
            f"{ROUNDTRIP_SAMPLE_LIMIT} unique texts per source and split, "
            f"selected by SHA-256 with seed {ROUNDTRIP_SAMPLE_SEED}. Coverage "
            "and round-trip counts assess table behavior, not word correctness "
            "or human transliteration quality."
        ),
        "source_text_saved": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--source", action="append", dest="source_ids")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    report = audit_corpus(
        args.workspace,
        config,
        source_ids=tuple(args.source_ids) if args.source_ids else None,
    )
    output = args.output or (
        args.workspace
        / "reports"
        / f"transliteration-coverage-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json"
    )
    if output.resolve().is_relative_to(REPOSITORY.resolve()):
        raise ValueError("Audit reports must remain outside the repository.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    print(f"Report saved outside the repository: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
