# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validate and split a pinned Google SMOL English–Somali corpus."""

from __future__ import annotations

import hashlib
import json
import random
import re
import unicodedata
from pathlib import Path


def prepare_google_smol(
    artifact: Path,
    workspace: Path,
    *,
    seed: int = 1729,
) -> dict:
    """Validate source bytes, remove exact benchmark overlap, and group-split pairs."""
    catalog_path = (
        Path(__file__).resolve().parents[2] / "research" / "sources.catalog.json"
    )
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    source = next(item for item in catalog if item["source_id"] == "google-smol-en-so")
    spec = source["artifacts"][0]
    digest = _sha256(artifact)
    if artifact.stat().st_size != spec["expected_bytes"] or digest != spec["sha256"]:
        raise ValueError("Google SMOL bytes do not match the pinned corpus artifact.")

    repository = catalog_path.parents[1]
    tico = repository / "tests/data/somali_translation_tico19_test_150.jsonl"
    if not tico.is_file():
        raise ValueError(
            "The local TICO holdout fixture is required for leakage checks."
        )
    heldout_english = set()
    heldout_somali = set()
    for line in tico.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        heldout_english.add(_normalize(row["source_en"]))
        heldout_somali.add(_normalize(row["reference_so"]))

    rows = []
    seen_pairs = set()
    duplicate_pairs = 0
    overlap_pairs = 0
    for line_number, line in enumerate(
        artifact.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        if (
            row.get("sl") != "en"
            or row.get("tl") != "so"
            or row.get("is_src_orig") is not True
        ):
            raise ValueError(
                f"Unexpected language or source status on line {line_number}."
            )
        source_text = _clean_text(row.get("src"))
        target_text = _clean_text(row.get("trg"))
        source_key = _normalize(source_text)
        target_key = _normalize(target_text)
        if not source_key or not target_key:
            raise ValueError(f"Empty translation pair on line {line_number}.")
        if source_key in heldout_english or target_key in heldout_somali:
            overlap_pairs += 1
            continue
        pair_key = source_key, target_key
        if pair_key in seen_pairs:
            duplicate_pairs += 1
            continue
        seen_pairs.add(pair_key)
        rows.append(
            {
                "record_id": row["id"],
                "source_text": source_text,
                "target_text": target_text,
                "source_id": source["source_id"],
                "license": source["license"],
                "dataset_revision": source["revision"],
            }
        )

    if len(rows) < 10:
        raise ValueError(
            "Too few unique, non-overlapping pairs remain to split safely."
        )
    groups = _duplicate_components(rows)
    random.Random(seed).shuffle(groups)
    splits = _assign_splits(groups)
    output = workspace / "data/prepared/google-smol-en-so" / source["revision"]
    output.mkdir(parents=True, exist_ok=True)
    split_counts = {}
    file_hashes = {}
    for name, group_rows in splits.items():
        path = output / f"{name}.jsonl"
        temporary = path.with_suffix(".jsonl.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for row in group_rows:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        temporary.replace(path)
        split_counts[name] = len(group_rows)
        file_hashes[path.name] = _sha256(path)

    manifest = {
        "schema_version": 1,
        "source_id": source["source_id"],
        "dataset_revision": source["revision"],
        "source_sha256": digest,
        "source_bytes": artifact.stat().st_size,
        "license": source["license"],
        "attribution": (
            "Google SMOL dataset and its cited contributors; see source page."
        ),
        "source_page": source["source_page"],
        "seed": seed,
        "split_policy": (
            "80/10/10 target by duplicate-connected components; exact normalized "
            "sentence overlap groups stay together."
        ),
        "benchmark_leakage_policy": (
            "Drop a pair if its exact normalized English or Somali text appears "
            "in the tracked TICO test fixture."
        ),
        "input_pairs": len(rows) + duplicate_pairs + overlap_pairs,
        "unique_pairs": len(rows),
        "duplicate_pairs_removed": duplicate_pairs,
        "tico_overlap_pairs_removed": overlap_pairs,
        "group_count": len(groups),
        "split_counts": split_counts,
        "split_sha256": file_hashes,
        "automatic_quality_review": (
            "Not performed; this split is not fluent-speaker validation."
        ),
        "model_training": (
            "Not run; the M2M100 candidate has not yet been trained or integrated."
        ),
    }
    manifest_path = output / "manifest.json"
    manifest_tmp = manifest_path.with_suffix(".json.tmp")
    manifest_tmp.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_tmp.replace(manifest_path)
    return {**manifest, "output_directory": str(output)}


def _clean_text(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("Translation sides must be text strings.")
    return " ".join(unicodedata.normalize("NFC", value).split())


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value).casefold()).strip()


def _duplicate_components(rows: list[dict]) -> list[list[dict]]:
    parents = list(range(len(rows)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(first: int, second: int) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parents[second_root] = first_root

    seen_sentences = {}
    for index, row in enumerate(rows):
        for field in ("source_text", "target_text"):
            key = _normalize(row[field])
            if key in seen_sentences:
                union(index, seen_sentences[key])
            else:
                seen_sentences[key] = index

    components = {}
    for index, row in enumerate(rows):
        components.setdefault(find(index), []).append(row)
    return list(components.values())


def _assign_splits(groups: list[list[dict]]) -> dict[str, list[dict]]:
    targets = {"train": 0.8, "validation": 0.1, "test": 0.1}
    result = {name: [] for name in targets}
    total = sum(len(group) for group in groups)
    for group in groups:
        name = min(
            targets,
            key=lambda split: len(result[split]) / (targets[split] * total),
        )
        result[name].extend(group)
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
