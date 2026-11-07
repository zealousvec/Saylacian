# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit official pinned Somali-French and Somali-Arabic InfoPankki shards."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import random
import statistics
import unicodedata
import zipfile
from pathlib import Path

from .prepare_data import _assign_splits
from .prepare_data import _duplicate_components
from .sources import load_catalog
from .workspace import default_workspace
from .workspace import ensure_outside_repository

CORPUS_REVISION = "52339513e7ee4d1896c804ca4f61d7ee3b35ea93"
CORPUS_PAGE = "https://huggingface.co/datasets/Helsinki-NLP/opus_infopankki"
CORPUS_LICENSE = "CC-BY-4.0"
TICO_SHA256 = "0e82fc7ceaa877606c8934f32ead185716c9d2c54b3818f2a7ae655f5e7a08d8"
TICO_BYTES = 15_168_404
MIXTURE_REVISION = "ba95192b949215c943959dbe"
PAIR_ARTIFACTS = {
    "fr-so": {
        "source_language": "fr",
        "bytes": 2_344_399,
        "sha256": "3aea232ad1aa63df1816fa4922072b79f064a0eb4cb465b6b533b4e902823c9c",
    },
    "ar-so": {
        "source_language": "ar",
        "bytes": 2_614_055,
        "sha256": "7187b0e91abd14c59ccc052c7d9831e875f95ca9b5c0f66a043ec52c3267cf50",
    },
}
ATTRIBUTION = (
    "InfoFinland; OPUS/Helsinki-NLP; cite Tiedemann (2012), Parallel Data, "
    "Tools and Interfaces in OPUS."
)
SPLIT_SEED = 1729
LANGUAGE_ID_VERSION = "0.4.0"
REPOSITORY = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_catalog_source(pair: str, catalog: list[dict]) -> dict:
    """Match a pinned pair artifact to its rights and provenance record."""
    spec = PAIR_ARTIFACTS[pair]
    source_id = f"opus-infopankki-{pair}"
    source = next(
        (record for record in catalog if record.get("source_id") == source_id),
        None,
    )
    if source is None:
        raise ValueError(f"Source catalog entry is missing: {source_id}.")
    if (
        source.get("revision") != CORPUS_REVISION
        or source.get("languages") != [spec["source_language"], "so"]
        or source.get("license") != CORPUS_LICENSE
        or source.get("rights_status") != "verified"
    ):
        raise ValueError(f"Source catalog identity does not match: {source_id}.")
    artifact = next(
        (
            item
            for item in source.get("artifacts", [])
            if item.get("sha256") == spec["sha256"]
        ),
        None,
    )
    if (
        artifact is None
        or artifact.get("expected_bytes") != spec["bytes"]
        or f"/{pair}/train-00000-of-00001.parquet" not in artifact.get("url", "")
    ):
        raise ValueError(f"Source catalog artifact pin does not match: {source_id}.")
    return {
        "source_id": source_id,
        "owner_approved": source.get("owner_approved") is True,
        "train_right": source.get("rights", {}).get("train"),
        "license": source["license"],
    }


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _load_tico_dev_targets(archive: Path) -> set[str]:
    """Read only the official Somali development references, never the test set."""
    with (
        zipfile.ZipFile(archive) as source,
        source.open("tico19-testset/dev/dev.en-so.tsv") as stream,
    ):
        rows = csv.DictReader(
            io.TextIOWrapper(stream, encoding="utf-8"), delimiter="\t"
        )
        return {
            _normalize(row["targetString"])
            for row in rows
            if row.get("targetLang") == "so" and row.get("targetString")
        }


def _load_mixture_somali(workspace: Path) -> set[str]:
    """Verify and read Somali targets from all pinned mixture splits."""
    root = workspace / "data" / "prepared" / "marian-mixture" / MIXTURE_REVISION
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("dataset_revision") != MIXTURE_REVISION:
        raise ValueError("Pinned mixture revision does not match its manifest.")

    somali = set()
    for split in ("train", "validation", "test"):
        path = root / f"{split}.jsonl"
        expected = manifest.get("split_sha256", {}).get(path.name)
        if not expected or _sha256(path) != expected:
            raise ValueError(f"Pinned mixture checksum failed for {split}.")
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    row = json.loads(line)
                    somali.add(_normalize(row["target_text"]))
    return somali


def _clean_pair_rows(
    pair: str,
    rows: list[dict],
    *,
    mixture_somali: set[str],
    tico_dev_somali: set[str],
) -> tuple[list[dict], dict[str, int]]:
    spec = PAIR_ARTIFACTS[pair]
    source_language = spec["source_language"]
    stats = {
        "malformed_rows_removed": 0,
        "empty_rows_removed": 0,
        "over_256_words_removed": 0,
        "mixture_somali_overlap_removed": 0,
        "tico_dev_somali_overlap_removed": 0,
        "exact_duplicate_pairs_removed": 0,
    }
    retained = []
    seen_pairs = set()
    for index, row in enumerate(rows):
        translations = row.get("translation")
        if not isinstance(translations, dict):
            stats["malformed_rows_removed"] += 1
            continue
        source_text = translations.get(source_language)
        somali_text = translations.get("so")
        if not isinstance(source_text, str) or not isinstance(somali_text, str):
            stats["malformed_rows_removed"] += 1
            continue
        source_text = " ".join(unicodedata.normalize("NFC", source_text).split())
        somali_text = " ".join(unicodedata.normalize("NFC", somali_text).split())
        if not source_text or not somali_text:
            stats["empty_rows_removed"] += 1
            continue
        if max(len(source_text.split()), len(somali_text.split())) > 256:
            stats["over_256_words_removed"] += 1
            continue

        source_key = _normalize(source_text)
        somali_key = _normalize(somali_text)
        if somali_key in mixture_somali:
            stats["mixture_somali_overlap_removed"] += 1
            continue
        if somali_key in tico_dev_somali:
            stats["tico_dev_somali_overlap_removed"] += 1
            continue

        pair_key = (source_language, source_key, somali_key)
        if pair_key in seen_pairs:
            stats["exact_duplicate_pairs_removed"] += 1
            continue
        seen_pairs.add(pair_key)
        retained.append(
            {
                "record_id": f"{pair}:{index}",
                "source_text": source_text,
                "target_text": somali_text,
                "source_language": source_language,
                "target_language": "so",
                "source_id": f"opus-infopankki-{pair}",
                "dataset_revision": CORPUS_REVISION,
                "license": CORPUS_LICENSE,
            }
        )
    return retained, stats


def _write_split(path: Path, rows: list[dict]) -> str:
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    if path.exists():
        if _sha256(path) != digest:
            raise ValueError(f"Refusing to replace an immutable split: {path}")
        return digest
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return digest


def _group_and_split(rows: list[dict], *, seed: int) -> tuple[dict, int]:
    """Keep exact shared sentences together across all language pairs."""
    groups = _duplicate_components(rows)
    random.Random(seed).shuffle(groups)
    splits = _assign_splits(groups)
    split_sentences = {
        name: {
            _normalize(row[field])
            for row in split_rows
            for field in ("source_text", "target_text")
        }
        for name, split_rows in splits.items()
    }
    split_pairs = (
        ("train", "validation"),
        ("train", "test"),
        ("validation", "test"),
    )
    if any(
        split_sentences[first] & split_sentences[second]
        for first, second in split_pairs
    ):
        raise ValueError("Exact sentences leaked across multilingual splits.")
    return splits, len(groups)


def _language_id_probe(rows: list[dict]) -> dict:
    """Report labels for long rows without dropping data based on the heuristic."""
    try:
        from py3langid import classify
    except ImportError as error:
        raise RuntimeError(
            "Install py3langid==0.4.0 to reproduce the language-ID probe."
        ) from error
    version = importlib.metadata.version("py3langid")
    if version != LANGUAGE_ID_VERSION:
        raise RuntimeError(
            f"The language-ID probe requires py3langid {LANGUAGE_ID_VERSION}; "
            f"found {version}."
        )

    sides = {}
    for row in rows:
        source_language = row["source_language"]
        for field, expected, side in (
            ("source_text", source_language, "source"),
            ("target_text", "so", "somali"),
        ):
            text = row[field]
            if len(text) < 50:
                continue
            key = f"{side}:{expected}"
            counts = sides.setdefault(
                key,
                {"expected_language": expected, "checked": 0, "mismatch_labels": {}},
            )
            counts["checked"] += 1
            predicted, _score = classify(text)
            if predicted != expected:
                labels = counts["mismatch_labels"]
                labels[predicted] = labels.get(predicted, 0) + 1

    return {
        "version": f"py3langid {version}",
        "minimum_characters": 50,
        "filtering_applied": False,
        "sides": sides,
        "interpretation": (
            "Heuristic labels only; mismatches may be dialects or classifier "
            "errors and require linguistic review."
        ),
    }


def prepare_candidate_splits(workspace: Path, *, seed: int = SPLIT_SEED) -> dict:
    """Prepare private, duplicate-grouped splits without granting train approval."""
    try:
        from pyarrow import parquet
    except ImportError as error:
        raise RuntimeError(
            "Install the research Parquet requirements in an isolated environment."
        ) from error

    ensure_outside_repository(workspace, REPOSITORY)
    catalog = load_catalog(REPOSITORY / "research" / "sources.catalog.json")
    source_approval = {
        pair: _verify_catalog_source(pair, catalog) for pair in PAIR_ARTIFACTS
    }

    data_dir = workspace / "cache" / "data" / "opus-infopankki-multilingual"
    tico_archive = (
        workspace / "cache" / "data" / "tico19" / "tico19-testset-2021-02-26.zip"
    )
    if (
        tico_archive.stat().st_size != TICO_BYTES
        or _sha256(tico_archive) != TICO_SHA256
    ):
        raise ValueError("Pinned TICO-19 archive verification failed.")
    mixture_somali = _load_mixture_somali(workspace)
    tico_dev_somali = _load_tico_dev_targets(tico_archive)
    retained_rows = []
    source_hashes = {}
    pair_stats = {}
    input_rows = 0

    for pair, spec in PAIR_ARTIFACTS.items():
        path = data_dir / f"{pair}.parquet"
        digest = _sha256(path)
        if path.stat().st_size != spec["bytes"] or digest != spec["sha256"]:
            raise ValueError(f"Pinned InfoPankki artifact verification failed: {pair}.")
        rows = parquet.read_table(path).to_pylist()
        input_rows += len(rows)
        pair_rows, counts = _clean_pair_rows(
            pair,
            rows,
            mixture_somali=mixture_somali,
            tico_dev_somali=tico_dev_somali,
        )
        pair_stats[pair] = {
            "input_rows": len(rows),
            "retained_rows": len(pair_rows),
            **counts,
        }
        source_hashes[pair] = digest
        retained_rows.extend(pair_rows)

    splits, group_count = _group_and_split(retained_rows, seed=seed)

    builder_hash = _sha256(Path(__file__))
    revision_payload = json.dumps(
        {
            "source_revision": CORPUS_REVISION,
            "source_hashes": source_hashes,
            "mixture_revision": MIXTURE_REVISION,
            "tico_dev_archive_hash": TICO_SHA256,
            "builder_sha256": builder_hash,
            "seed": seed,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    revision = hashlib.sha256(revision_payload.encode("utf-8")).hexdigest()[:24]
    output = workspace / "data" / "prepared" / "infopankki-multilingual" / revision
    split_hashes = {
        f"{name}.jsonl": _write_split(output / f"{name}.jsonl", rows)
        for name, rows in splits.items()
    }
    manifest = {
        "schema_version": 1,
        "source_id": "infopankki-multilingual",
        "dataset_revision": revision,
        "source_revision": CORPUS_REVISION,
        "source_artifact_sha256": source_hashes,
        "source_approval_status": source_approval,
        "source_row_counts": pair_stats,
        "source_pages": {pair: CORPUS_PAGE for pair in PAIR_ARTIFACTS},
        "source_languages": ["fr", "ar"],
        "target_language": "so",
        "license": CORPUS_LICENSE,
        "attribution": ATTRIBUTION,
        "seed": seed,
        "input_rows": input_rows,
        "retained_rows": len(retained_rows),
        "duplicate_connected_groups": group_count,
        "split_counts": {name: len(rows) for name, rows in splits.items()},
        "split_sha256": split_hashes,
        "cross_split_exact_sentence_overlap": 0,
        "mixture_overlap_policy": (
            "remove every row whose Somali target occurs in any pinned mixture split"
        ),
        "tico_policy": (
            "read and exclude exact Somali references from TICO dev only; "
            "final test was not opened"
        ),
        "builder_sha256": builder_hash,
        "owner_approved_for_training": False,
        "quality_note": (
            "Automated structure and leakage screening; language-ID heuristic "
            "is reported but not used for filtering. No semantic or fluent review."
        ),
        "language_id_probe": _language_id_probe(retained_rows),
    }
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise ValueError("Refusing to replace an immutable candidate manifest.")
    else:
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(manifest_path)
    return {**manifest, "output_directory": str(output)}


def audit_pair_rows(
    rows: list[dict],
    *,
    source_language: str,
    mixture_somali: set[str],
    tico_dev_somali: set[str],
) -> dict:
    """Summarize structure, exact duplicates and Somali-side overlap."""
    seen_pairs = set()
    seen_somali = set()
    ratios = []
    duplicate_pairs = 0
    repeated_somali = 0
    mixture_overlap = 0
    tico_overlap = 0
    empty = 0
    malformed = 0
    too_long = 0

    for row in rows:
        translations = row.get("translation")
        if not isinstance(translations, dict):
            malformed += 1
            continue
        source_text = translations.get(source_language)
        somali_text = translations.get("so")
        if not isinstance(source_text, str) or not isinstance(somali_text, str):
            malformed += 1
            continue
        source_text = source_text.strip()
        somali_text = somali_text.strip()
        if not source_text or not somali_text:
            empty += 1
            continue

        source_key = _normalize(source_text)
        somali_key = _normalize(somali_text)
        pair_key = (source_key, somali_key)
        if pair_key in seen_pairs:
            duplicate_pairs += 1
        seen_pairs.add(pair_key)
        if somali_key in seen_somali:
            repeated_somali += 1
        seen_somali.add(somali_key)
        mixture_overlap += somali_key in mixture_somali
        tico_overlap += somali_key in tico_dev_somali
        too_long += len(source_text.split()) > 256 or len(somali_text.split()) > 256
        ratios.append(len(somali_text) / max(1, len(source_text)))

    return {
        "rows": len(rows),
        "malformed_rows": malformed,
        "empty_pairs": empty,
        "duplicate_pairs_after_first": duplicate_pairs,
        "repeated_somali_rows_after_first": repeated_somali,
        "unique_somali_strings": len(seen_somali),
        "somali_overlap_with_mixture_all_splits": mixture_overlap,
        "somali_overlap_with_tico_dev": tico_overlap,
        "pairs_over_256_words": too_long,
        "median_somali_to_source_character_ratio": (
            round(statistics.median(ratios), 2) if ratios else None
        ),
    }


def audit_workspace(workspace: Path, *, prepare_splits: bool = False) -> dict:
    """Verify the pinned official files and write no data inside the repo."""
    try:
        from pyarrow import parquet
    except ImportError as error:
        raise RuntimeError(
            "Install the research Parquet requirements in an isolated environment."
        ) from error

    ensure_outside_repository(workspace, REPOSITORY)
    catalog = load_catalog(REPOSITORY / "research" / "sources.catalog.json")
    source_approval = {
        pair: _verify_catalog_source(pair, catalog) for pair in PAIR_ARTIFACTS
    }

    data_dir = workspace / "cache" / "data" / "opus-infopankki-multilingual"
    tico_archive = (
        workspace / "cache" / "data" / "tico19" / "tico19-testset-2021-02-26.zip"
    )
    if (
        tico_archive.stat().st_size != TICO_BYTES
        or _sha256(tico_archive) != TICO_SHA256
    ):
        raise ValueError("Pinned TICO-19 archive verification failed.")

    mixture_somali = _load_mixture_somali(workspace)
    tico_dev_somali = _load_tico_dev_targets(tico_archive)
    results = {}
    for pair, spec in PAIR_ARTIFACTS.items():
        path = data_dir / f"{pair}.parquet"
        digest = _sha256(path)
        if path.stat().st_size != spec["bytes"] or digest != spec["sha256"]:
            raise ValueError(f"Pinned InfoPankki artifact verification failed: {pair}.")
        rows = parquet.read_table(path).to_pylist()
        results[pair] = {
            "source_language": spec["source_language"],
            "artifact_bytes": path.stat().st_size,
            "artifact_sha256": digest,
            **audit_pair_rows(
                rows,
                source_language=spec["source_language"],
                mixture_somali=mixture_somali,
                tico_dev_somali=tico_dev_somali,
            ),
        }

    report = {
        "source_page": CORPUS_PAGE,
        "source_revision": CORPUS_REVISION,
        "license": CORPUS_LICENSE,
        "source_approval_status": source_approval,
        "attribution": ATTRIBUTION,
        "tico_archive_sha256": TICO_SHA256,
        "tico_split_read": "dev only; final test split not opened",
        "current_mixture_revision": MIXTURE_REVISION,
        "mixture_split_hashes_verified": True,
        "quality_scope": (
            "Structural and exact-overlap checks plus an unfiltered language-ID "
            "probe; no semantic alignment scoring or fluent-speaker review."
        ),
        "training_approval": "not granted by this audit",
        "pairs": results,
    }
    if prepare_splits:
        report["candidate_splits"] = prepare_candidate_splits(workspace)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--prepare-splits",
        action="store_true",
        help="Create private cross-language grouped candidate splits after audit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_workspace(args.workspace, prepare_splits=args.prepare_splits)
    output = (
        args.output or args.workspace / "reports" / "infopankki-multilingual-audit.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
    print(f"Report: {output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
