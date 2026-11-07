# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit language labels in a pinned mixture without retaining sentence text."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.metadata
import json
import unicodedata
from collections import Counter
from collections.abc import Callable
from datetime import UTC
from datetime import datetime
from pathlib import Path

from tools.benchmark_output import require_external_output
from tools.benchmark_output import save_json_atomic
from tools.translation_lab.config import LabConfig
from tools.translation_lab.config import load_config
from tools.translation_lab.sources import read_owner_registry
from tools.translation_lab.sources import verify_approved_source

REPOSITORY = Path(__file__).resolve().parents[2]
LANGUAGE_ID_VERSION = "0.4.0"
SAMPLE_LIMIT = 250
SAMPLE_SEED = 1729
MINIMUM_CHARACTERS = 50


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _classifier() -> Callable[[str], tuple[str, float]]:
    try:
        from py3langid import classify
    except ImportError as error:
        raise RuntimeError("Install py3langid==0.4.0 to run this audit.") from error

    version = importlib.metadata.version("py3langid")
    if version != LANGUAGE_ID_VERSION:
        raise RuntimeError(
            f"This audit requires py3langid {LANGUAGE_ID_VERSION}; found {version}."
        )
    return classify


def _retain_sample(
    heaps: dict,
    selected_hashes: dict,
    key: tuple[str, str],
    row: dict,
    limit: int,
) -> None:
    normalized_pair = "\0".join(
        unicodedata.normalize("NFC", row[field]).casefold()
        for field in ("source_text", "target_text")
    )
    digest = hashlib.sha256(
        f"{SAMPLE_SEED}\0{key[0]}\0{key[1]}\0{normalized_pair}".encode()
    ).hexdigest()
    heap = heaps.setdefault(key, [])
    retained = selected_hashes.setdefault(key, set())
    if digest in retained:
        return

    priority = int(digest, 16)
    entry = (-priority, digest, row)
    if len(heap) < limit:
        heapq.heappush(heap, entry)
        retained.add(digest)
    elif priority < -heap[0][0]:
        removed = heapq.heapreplace(heap, entry)
        retained.remove(removed[1])
        retained.add(digest)


def _load_verified_splits(
    workspace: Path,
    config: LabConfig,
    experiment_id: str,
) -> tuple[dict, dict[str, dict], dict[str, Path]]:
    if not config.training_enabled:
        raise PermissionError("Corpus processing is disabled in the private config.")

    experiment_dir = workspace / "experiments" / experiment_id
    metadata = json.loads((experiment_dir / "experiment.json").read_text("utf-8"))
    fingerprint = metadata.get("fingerprint", {})
    if (
        metadata.get("experiment_id") != experiment_id
        or fingerprint.get("dataset_id") != "marian-mixture"
    ):
        raise ValueError("This audit accepts only a pinned marian-mixture run.")

    revision = fingerprint.get("dataset_revision")
    if not revision:
        raise ValueError("Experiment metadata has no dataset revision.")
    dataset_dir = workspace / "data" / "prepared" / "marian-mixture" / revision
    manifest = json.loads((dataset_dir / "manifest.json").read_text("utf-8"))
    if (
        manifest.get("source_id") != "marian-mixture"
        or manifest.get("dataset_revision") != revision
        or fingerprint.get("source_revisions") != manifest.get("source_revisions")
        or fingerprint.get("source_licenses") != manifest.get("source_licenses")
        or fingerprint.get("train_sha256")
        != manifest.get("split_sha256", {}).get("train.jsonl")
        or fingerprint.get("validation_sha256")
        != manifest.get("split_sha256", {}).get("validation.jsonl")
    ):
        raise ValueError("Experiment and mixture manifest identities do not match.")

    registry = {
        source["source_id"]: source
        for source in read_owner_registry(workspace / "registry" / "sources.jsonl")
    }
    source_ids = tuple(sorted(manifest.get("source_revisions", {})))
    if not source_ids:
        raise ValueError("Mixture manifest contains no source revisions.")

    for source_id in source_ids:
        source = registry.get(source_id)
        if source is None:
            raise PermissionError(f"Approved source record is missing: {source_id}")
        verify_approved_source(
            source,
            set(config.approved_source_ids),
            purpose="train",
            allow_noncommercial=config.allow_noncommercial_training,
        )
        if source.get("revision") != manifest["source_revisions"].get(
            source_id
        ) or source.get("license") != manifest["source_licenses"].get(source_id):
            raise ValueError(f"Mixture source identity changed: {source_id}")

    split_paths = {
        split: dataset_dir / f"{split}.jsonl" for split in ("train", "validation")
    }
    for split, path in split_paths.items():
        expected = manifest.get("split_sha256", {}).get(path.name)
        if not expected or _sha256(path) != expected:
            raise ValueError(f"Mixture split checksum failed: {split}")
    return manifest, registry, split_paths


def _new_counts(expected_language: str) -> dict:
    return {
        "expected_language": expected_language,
        "checked": 0,
        "below_minimum_length": 0,
        "mismatch_labels": Counter(),
    }


def _finalize_counts(counts: dict) -> dict:
    checked = counts["checked"]
    mismatches = sum(counts["mismatch_labels"].values())
    return {
        **counts,
        "mismatch_labels": dict(sorted(counts["mismatch_labels"].items())),
        "mismatch_rate": round(mismatches / checked, 6) if checked else None,
    }


def audit_mixture_languages(
    workspace: Path,
    config: LabConfig,
    experiment_id: str,
    *,
    sample_limit: int = SAMPLE_LIMIT,
    classifier: Callable[[str], tuple[str, float]] | None = None,
) -> dict:
    """Sample train/validation pairs, report heuristic labels, and save no text."""
    if sample_limit < 1 or sample_limit > 2000:
        raise ValueError("Sample size must be between 1 and 2,000 per source/split.")
    label_text = classifier or _classifier()
    manifest, registry, split_paths = _load_verified_splits(
        workspace, config, experiment_id
    )

    sample_heaps: dict = {}
    sample_hashes: dict = {}
    source_ids = tuple(sorted(manifest["source_revisions"]))
    for split, path in split_paths.items():
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"Invalid JSON in mixture {split} line {line_number}."
                    ) from error
                source_id = row.get("source_id")
                if source_id not in source_ids:
                    raise ValueError(f"Unknown mixture source in {split}.")
                if row.get("license") != registry[source_id].get("license"):
                    raise ValueError(f"Row license mismatch in mixture {split}.")
                if (
                    row.get("dataset_revision")
                    != manifest["source_revisions"][source_id]
                ):
                    raise ValueError(f"Row revision mismatch in mixture {split}.")
                if not all(
                    isinstance(row.get(field), str) and row[field].strip()
                    for field in ("source_text", "target_text")
                ):
                    raise ValueError(f"Empty or invalid text in mixture {split}.")
                _retain_sample(
                    sample_heaps,
                    sample_hashes,
                    (source_id, split),
                    row,
                    sample_limit,
                )

    results = {}
    for source_id in source_ids:
        results[source_id] = {
            "revision": manifest["source_revisions"][source_id],
            "license": manifest["source_licenses"][source_id],
            "splits": {},
        }
        for split in ("train", "validation"):
            heap = sample_heaps.get((source_id, split), [])
            side_counts = {
                "english": _new_counts("en"),
                "somali": _new_counts("so"),
            }
            for _priority, _digest, row in heap:
                for side, field, expected in (
                    ("english", "source_text", "en"),
                    ("somali", "target_text", "so"),
                ):
                    text = row[field]
                    counts = side_counts[side]
                    if len(text) < MINIMUM_CHARACTERS:
                        counts["below_minimum_length"] += 1
                        continue
                    predicted, _score = label_text(text)
                    counts["checked"] += 1
                    if predicted != expected:
                        counts["mismatch_labels"][predicted] += 1

            results[source_id]["splits"][split] = {
                "sampled_unique_pairs": len(heap),
                "english": _finalize_counts(side_counts["english"]),
                "somali": _finalize_counts(side_counts["somali"]),
            }

    return {
        "schema_version": 1,
        "created_utc": datetime.now(UTC).isoformat(),
        "experiment_id": experiment_id,
        "dataset_revision": manifest["dataset_revision"],
        "sample_seed": SAMPLE_SEED,
        "sample_limit_per_source_split": sample_limit,
        "minimum_characters": MINIMUM_CHARACTERS,
        "language_identifier": f"py3langid {LANGUAGE_ID_VERSION}",
        "sources": results,
        "source_text_saved": False,
        "test_split_opened": False,
        "filtering_applied": False,
        "interpretation": (
            "Language-ID labels are heuristic and are reported only; they do "
            "not prove sentence alignment or translation quality and do not "
            "remove any data. Short text is not classified."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sample-limit", type=int, default=SAMPLE_LIMIT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = args.output or (
        args.workspace
        / "reports"
        / f"mixture-language-audit-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json"
    )
    require_external_output(output)
    report = audit_mixture_languages(
        args.workspace,
        load_config(args.config),
        args.experiment_id,
        sample_limit=args.sample_limit,
    )
    save_json_atomic(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Aggregate report saved outside the repository: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
