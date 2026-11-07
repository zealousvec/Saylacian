# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare a provenance-preserving, leakage-checked Somali training mixture."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from tools.translation_lab.config import LabConfig
from tools.translation_lab.m2m100_training import _read_jsonl
from tools.translation_lab.prepare_data import _assign_splits
from tools.translation_lab.prepare_data import _duplicate_components
from tools.translation_lab.prepare_data import _normalize
from tools.translation_lab.sources import read_owner_registry
from tools.translation_lab.sources import verify_approved_source

MIXTURE_ID = "marian-mixture"
SOURCE_IDS = (
    "opus-infopankki-en-so",
    "opus-paracrawl-en-so",
    "google-smol-en-so",
)
GOOGLE_ID = "google-smol-en-so"
SEED = 1729
POLICY_VERSION = "grouped-trainval-unweighted-v1"
TRAIN_SAMPLE_MULTIPLIERS = {}
REPOSITORY = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _revision_for(identity: dict) -> str:
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _load_source_splits(workspace: Path, config: LabConfig, source_id: str):
    registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
    source = next(
        (item for item in registry if item.get("source_id") == source_id), None
    )
    if source is None:
        raise PermissionError(f"Approved source record is missing: {source_id}")
    verify_approved_source(
        source,
        set(config.approved_source_ids),
        purpose="train",
        allow_noncommercial=config.allow_noncommercial_training,
    )
    revision = source.get("revision")
    root = workspace / "data" / "prepared" / source_id / str(revision)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Prepared source is missing: {source_id}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("source_id") != source_id
        or manifest.get("dataset_revision") != revision
        or manifest.get("license") != source.get("license")
    ):
        raise ValueError(f"Prepared source identity changed: {source_id}")
    splits = {}
    for name in ("train", "validation", "test"):
        path = root / f"{name}.jsonl"
        expected = manifest.get("split_sha256", {}).get(path.name)
        if not expected or _sha256(path) != expected:
            raise ValueError(f"Prepared split checksum failed: {source_id}/{name}")
        splits[name] = _read_jsonl(path)
    return source, manifest, splits


def _heldout_rows(workspace: Path, config: LabConfig, datasets: dict):
    heldout = []
    heldout_metadata = {"source_tests": {}}
    for source_id in SOURCE_IDS:
        source, manifest, splits = datasets[source_id]
        verify_approved_source(
            source, set(config.approved_source_ids), purpose="evaluate"
        )
        if manifest.get("license") != source.get("license"):
            raise ValueError(f"Source test license does not match: {source_id}")
        heldout.extend(splits["test"])
        heldout_metadata["source_tests"][source_id] = {
            "revision": manifest["dataset_revision"],
            "sha256": manifest["split_sha256"]["test.jsonl"],
        }

    tico_path = (
        REPOSITORY / "tests" / "data" / "somali_translation_tico19_test_150.jsonl"
    )
    tico_rows = _read_jsonl(tico_path)
    heldout.extend(
        {
            "source_text": row["source_en"],
            "target_text": row["reference_so"],
        }
        for row in tico_rows
    )
    heldout_metadata["tico_test_sha256"] = _sha256(tico_path)
    return heldout, heldout_metadata


def _write_split(path: Path, rows: list[dict]) -> str:
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if path.exists():
        if _sha256(path) != digest:
            raise ValueError(
                f"Refusing to overwrite an immutable dataset split: {path}"
            )
        return digest

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return digest


def _weight_training_rows(rows: list[dict]) -> list[dict]:
    """Repeat only in-train examples after leakage-free split assignment."""
    weighted = []
    for row in rows:
        multiplier = TRAIN_SAMPLE_MULTIPLIERS.get(row["source_id"], 1)
        if multiplier < 1:
            raise ValueError(f"Invalid training sample multiplier: {row['source_id']}")
        weighted.extend([row] * multiplier)
    return weighted


def prepare_marian_mixture(
    workspace: Path, config: LabConfig
) -> tuple[dict, list[dict], list[dict], list[dict]]:
    """Combine approved pairs with isolated tests and unweighted training."""
    if not config.training_enabled:
        raise PermissionError("Training is disabled in the private lab config.")
    required = set(SOURCE_IDS)
    if not required.issubset(set(config.approved_source_ids)):
        raise PermissionError("All mixture sources need explicit private approval.")

    datasets = {
        source_id: _load_source_splits(workspace, config, source_id)
        for source_id in SOURCE_IDS
    }
    heldout, heldout_metadata = _heldout_rows(workspace, config, datasets)
    heldout_english = {_normalize(row["source_text"]) for row in heldout}
    heldout_somali = {_normalize(row["target_text"]) for row in heldout}
    seen_pairs = set()
    rows = []
    duplicate_pairs = 0
    heldout_overlaps = 0
    source_counts = {source_id: 0 for source_id in SOURCE_IDS}

    for source_id in SOURCE_IDS:
        source, manifest, splits = datasets[source_id]
        for split_name in ("train", "validation"):
            for row in splits[split_name]:
                english = _normalize(row["source_text"])
                somali = _normalize(row["target_text"])
                if english in heldout_english or somali in heldout_somali:
                    heldout_overlaps += 1
                    continue
                pair = english, somali
                if pair in seen_pairs:
                    duplicate_pairs += 1
                    continue
                seen_pairs.add(pair)
                rows.append(
                    {
                        "record_id": row["record_id"],
                        "source_text": row["source_text"],
                        "target_text": row["target_text"],
                        "source_id": source_id,
                        "license": source["license"],
                        "dataset_revision": manifest["dataset_revision"],
                    }
                )
                source_counts[source_id] += 1

    if len(rows) < 100:
        raise ValueError("Too few unique, heldout-safe rows remain for training.")
    groups = _duplicate_components(rows)
    random.Random(SEED).shuffle(groups)
    splits = _assign_splits(groups)
    unique_split_counts = {name: len(value) for name, value in splits.items()}
    splits["train"] = _weight_training_rows(splits["train"])
    source_revisions = {
        source_id: datasets[source_id][1]["dataset_revision"]
        for source_id in SOURCE_IDS
    }
    identity = {
        "source_revisions": source_revisions,
        "source_split_hashes": {
            source_id: datasets[source_id][1]["split_sha256"]
            for source_id in SOURCE_IDS
        },
        "heldout": heldout_metadata,
        "seed": SEED,
        "policy": POLICY_VERSION,
        "train_sample_multipliers": TRAIN_SAMPLE_MULTIPLIERS,
        "input_trainval_rows": sum(
            len(datasets[source_id][2][name])
            for source_id in SOURCE_IDS
            for name in ("train", "validation")
        ),
        "heldout_overlap_rows_removed": heldout_overlaps,
        "duplicate_pairs_removed": duplicate_pairs,
        "builder_sha256": _sha256(Path(__file__)),
    }
    revision = _revision_for(identity)
    output = workspace / "data" / "prepared" / MIXTURE_ID / revision
    hashes = {
        f"{name}.jsonl": _write_split(output / f"{name}.jsonl", split_rows)
        for name, split_rows in splits.items()
    }
    manifest = {
        "schema_version": 1,
        "source_id": MIXTURE_ID,
        "dataset_revision": revision,
        "builder_sha256": identity["builder_sha256"],
        "source_revisions": source_revisions,
        "heldout": heldout_metadata,
        "source_licenses": {
            source_id: datasets[source_id][0]["license"] for source_id in SOURCE_IDS
        },
        "source_pages": {
            source_id: datasets[source_id][0]["source_page"] for source_id in SOURCE_IDS
        },
        "license": "CC-BY-4.0 and CC0-1.0; terms recorded per source row",
        "attributions": [
            datasets[source_id][1]["attribution"] for source_id in SOURCE_IDS
        ],
        "attribution": " ; ".join(
            datasets[source_id][1]["attribution"] for source_id in SOURCE_IDS
        ),
        "seed": SEED,
        "split_policy": (
            "Combine approved InfoFinland, ParaCrawl, and Google SMOL original "
            "train/validation rows; keep each source test and TICO held out; "
            "remove exact heldout sentence overlap; group duplicate-connected "
            "rows; assign seeded 80/10/10 splits; apply only explicitly recorded "
            "training-row multipliers after split assignment."
        ),
        "heldout_sources": [*SOURCE_IDS, "tico19-somali-test-sample"],
        "input_trainval_rows": identity["input_trainval_rows"],
        "heldout_overlap_rows_removed": heldout_overlaps,
        "duplicate_pairs_removed": duplicate_pairs,
        "unique_rows": len(rows),
        "duplicate_component_count": len(groups),
        "source_row_counts": source_counts,
        "unique_split_counts": unique_split_counts,
        "train_sample_multipliers": TRAIN_SAMPLE_MULTIPLIERS,
        "split_counts": {name: len(value) for name, value in splits.items()},
        "split_sha256": hashes,
        "quality_note": (
            "ParaCrawl is web-mined; automatic filters do not establish semantic "
            "alignment. The additional Google SMOL training split is small and "
            "its professional translation claim is not an evaluation of this model."
        ),
    }
    manifest_path = output / "manifest.json"
    temporary = manifest_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(manifest_path)
    return manifest, splits["train"], splits["validation"], splits["test"]
