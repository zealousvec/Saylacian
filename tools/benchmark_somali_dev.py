# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare AfriSLM with Saylacian's standard offline route on pinned TICO-19 dev data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import socket
import sys
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.benchmark_output import (
    checkpoint_for,
    new_benchmark_output,
    require_external_output,
    save_json_atomic,
)
from tools.benchmark_somali_quality import (
    diagnostic_flags,
    get_qvac_translation,
    model_file_sha256,
    score,
)

TICO_DEV_ARCHIVE_SHA256 = (
    "0e82fc7ceaa877606c8934f32ead185716c9d2c54b3818f2a7ae655f5e7a08d8"
)
TICO_DEV_MEMBER = "tico19-testset/dev/dev.en-so.tsv"
TICO_DEV_ROW_COUNT = 971
TICO_SAMPLE_SEED = "20261025"


def load_dev_pairs(archive_path: Path) -> tuple[list[dict[str, str]], str]:
    """Read the hash-pinned English-Somali dev TSV without extracting it."""
    archive_hash = model_file_sha256(archive_path)
    if archive_hash != TICO_DEV_ARCHIVE_SHA256:
        raise ValueError(
            "TICO-19 archive SHA-256 does not match the pinned dev dataset."
        )
    with zipfile.ZipFile(archive_path) as archive:
        try:
            member = archive.open(TICO_DEV_MEMBER)
        except KeyError as error:
            raise ValueError(
                "Pinned TICO-19 archive is missing the dev TSV."
            ) from error
        with member, io.TextIOWrapper(member, encoding="utf-8", newline="") as text:
            rows = list(csv.DictReader(text, delimiter="\t"))

    required = {"sourceLang", "targetLang", "sourceString", "targetString", "stringID"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("TICO-19 dev TSV has an unexpected schema.")
    pairs = [
        {
            "id": row["stringID"],
            "source_en": row["sourceString"],
            "reference_so": row["targetString"],
        }
        for row in rows
        if row["sourceLang"] == "en"
        and row["targetLang"] == "so"
        and row["sourceString"].strip()
        and row["targetString"].strip()
    ]
    if len(pairs) != TICO_DEV_ROW_COUNT:
        raise ValueError(
            f"Expected {TICO_DEV_ROW_COUNT} pinned English-Somali dev pairs; found {len(pairs)}."
        )
    return pairs, archive_hash


def select_stratified_sample(
    rows: list[dict[str, str]], limit: int
) -> list[dict[str, str]]:
    """Choose a deterministic, equal-size sample from three source-length bands."""
    if not 3 <= limit <= len(rows) or limit % 3:
        raise ValueError(
            "Sample limit must be divisible by 3 and between 3 and dataset size."
        )
    groups: dict[str, list[dict[str, str]]] = {"short": [], "medium": [], "long": []}
    for row in rows:
        token_count = len(row["source_en"].split())
        group = (
            "short" if token_count <= 10 else "medium" if token_count <= 22 else "long"
        )
        groups[group].append(row)

    per_group = limit // 3
    selected = []
    for group in ("short", "medium", "long"):
        ranked = sorted(
            groups[group],
            key=lambda row: hashlib.sha256(
                f"{TICO_SAMPLE_SEED}:{row['id']}".encode()
            ).digest(),
        )
        if len(ranked) < per_group:
            raise ValueError(f"Not enough rows in {group} source-length band.")
        selected.extend(ranked[:per_group])
    return sorted(selected, key=lambda row: row["id"])


def _checkpoint(
    path: Path, archive_hash: str, model_hash: str, limit: int, sample_ids: list[str]
) -> dict:
    empty = {
        "afrislm": {"en_so": [], "so_en": []},
        "standard": {"en_so": [], "so_en": []},
    }
    if not path.is_file():
        return empty
    saved = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "archive_sha256": archive_hash,
        "model_sha256": model_hash,
        "sample_limit": limit,
        "sample_ids": sample_ids,
    }
    if any(saved.get(key) != value for key, value in expected.items()):
        return empty
    for system, directions in empty.items():
        for direction in directions:
            if not isinstance(
                saved.get("results", {}).get(system, {}).get(direction), list
            ):
                return empty
            if len(saved["results"][system][direction]) > limit:
                return empty
    return saved["results"]


def _save_checkpoint(
    path: Path,
    archive_hash: str,
    model_hash: str,
    limit: int,
    sample_ids: list[str],
    results: dict,
) -> None:
    save_json_atomic(
        path,
        {
            "archive_sha256": archive_hash,
            "model_sha256": model_hash,
            "sample_limit": limit,
            "sample_ids": sample_ids,
            "results": results,
        },
    )


def _metric_pair(rows: list[dict]) -> dict:
    return score([row["reference"] for row in rows], [row["text"] for row in rows])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-archive", type=Path, required=True)
    parser.add_argument("--candidate-model", type=Path, required=True)
    parser.add_argument("--packs-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument(
        "--output", type=Path, default=new_benchmark_output("somali-afrislm-dev")
    )
    args = parser.parse_args()

    try:
        output_path = require_external_output(args.output)
        checkpoint_path = require_external_output(
            checkpoint_for(output_path, "somali-afrislm-dev-checkpoint")
        )
        archive_path = args.dataset_archive.expanduser().resolve(strict=True)
        model_path = args.candidate_model.expanduser().resolve(strict=True)
        packs_dir = args.packs_dir.expanduser().resolve(strict=True)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if output_path.exists():
        parser.error("Output file already exists; choose a new --output path.")

    manifest = json.loads(
        (ROOT / "saylacian/core/data/afrislm_model_manifest.json").read_text(
            encoding="utf-8"
        )
    )[0]
    model_hash = model_file_sha256(model_path)
    if (
        model_path.stat().st_size != manifest["bytes"]
        or model_hash != manifest["sha256"]
    ):
        parser.error(
            "Candidate model size or SHA-256 does not match the pinned AfriSLM manifest."
        )
    try:
        all_rows, archive_hash = load_dev_pairs(archive_path)
        samples = select_stratified_sample(all_rows, args.limit)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.error(str(error))

    os.environ["SAYLACIAN_PACKS_DIR"] = str(packs_dir)
    from saylacian.core.model_packs import ModelPackManager
    from saylacian.core.translation import translate_meaning

    manager = ModelPackManager(packs_dir)
    installed = next(pack for pack in manager.list_packs() if pack["id"] == "somali")
    if not installed.get("installed_version") or installed.get("damaged"):
        parser.error(
            "A complete, verified standard Somali pack must be installed in --packs-dir."
        )
    roots = manager.active_model_roots()
    if not roots:
        parser.error(
            "The standard Somali model pack did not expose any active model files."
        )

    sample_ids = [row["id"] for row in samples]
    results = _checkpoint(
        checkpoint_path, archive_hash, model_hash, args.limit, sample_ids
    )
    from llama_cpp import Llama

    model = Llama(
        model_path=str(model_path),
        n_ctx=2048,
        n_threads=max(2, min(8, os.cpu_count() or 2)),
        n_gpu_layers=0,
        verbose=False,
    )

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline Somali benchmark attempted a network connection.")

    start = time.perf_counter()
    with patch.object(socket.socket, "connect", deny_network):
        for system in ("afrislm", "standard"):
            completed = min(
                len(results[system]["en_so"]), len(results[system]["so_en"])
            )
            results[system]["en_so"] = results[system]["en_so"][:completed]
            results[system]["so_en"] = results[system]["so_en"][:completed]
            for index, row in enumerate(samples[completed:], completed + 1):
                for direction, source_text, source, target, reference in (
                    (
                        "en_so",
                        row["source_en"],
                        "English",
                        "Somali",
                        row["reference_so"],
                    ),
                    (
                        "so_en",
                        row["reference_so"],
                        "Somali",
                        "English",
                        row["source_en"],
                    ),
                ):
                    started = time.perf_counter()
                    if system == "afrislm":
                        translated = get_qvac_translation(
                            model, source_text, source, target
                        )
                        warnings = []
                    else:
                        conversion = translate_meaning(
                            source_text,
                            "Somali Latin" if direction == "so_en" else "English",
                            "English" if direction == "so_en" else "Somali Latin",
                            provider_override="offline",
                        )
                        translated = conversion.text
                        warnings = list(conversion.warnings)
                    results[system][direction].append(
                        {
                            "id": row["id"],
                            "source": source_text,
                            "reference": reference,
                            "text": translated,
                            "elapsed_ms": round(
                                (time.perf_counter() - started) * 1000, 1
                            ),
                            "warnings": warnings,
                            "review_flags": diagnostic_flags(
                                translated, reference, direction
                            ),
                        }
                    )
                if index % 5 == 0 or index == len(samples):
                    _save_checkpoint(
                        checkpoint_path,
                        archive_hash,
                        model_hash,
                        args.limit,
                        sample_ids,
                        results,
                    )
                    print(f"{system}: {index}/{len(samples)} pairs", flush=True)

    report = {
        "benchmark": {
            "dataset": "TICO-19 English-Somali dev split",
            "archive_sha256": archive_hash,
            "archive_member": TICO_DEV_MEMBER,
            "upstream_row_count": len(all_rows),
            "sample_count": len(samples),
            "sample_seed": TICO_SAMPLE_SEED,
            "sampling": "Equal counts from <=10, 11-22, and >22 whitespace-token English-source bands; SHA-256 rank by seed and stringID.",
            "sample_ids": sample_ids,
            "directions": "English to Somali and Somali to English on the same parallel pairs.",
        },
        "candidate_model": {
            "repository": manifest["repository"],
            "revision": manifest["revision"],
            "license": manifest["license"],
            "bytes": model_path.stat().st_size,
            "sha256": model_hash,
        },
        "runtime": "llama-cpp-python 0.3.36 CPU; n_ctx=2048; temperature=0; socket connections blocked during inference.",
        "inference_seconds": round(time.perf_counter() - start, 2),
        "systems": {},
        "quality_limits": "Automatic single-reference metrics on a small medical-domain sample; not human-rated or representative of general Somali fluency.",
    }
    for system in ("afrislm", "standard"):
        report["systems"][system] = {
            "route": "Optional AfriSLM Q4 model"
            if system == "afrislm"
            else "Standard offline CTranslate2 pack",
            "metrics": {
                "en_to_so": _metric_pair(results[system]["en_so"]),
                "so_to_en": _metric_pair(results[system]["so_en"]),
            },
            "mean_latency_ms": {
                direction: round(
                    sum(row["elapsed_ms"] for row in results[system][direction])
                    / len(results[system][direction]),
                    1,
                )
                for direction in ("en_so", "so_en")
            },
            "review_cue_counts": {
                direction: {
                    cue.split(";")[0]: sum(
                        cue in row["review_flags"] for row in results[system][direction]
                    )
                    for cue in (
                        "numeric-token mismatch; review number preservation",
                        "possible negation mismatch; fluent reviewer required",
                    )
                }
                for direction in ("en_so", "so_en")
            },
            "predictions": results[system],
        }
    save_json_atomic(output_path, report)
    checkpoint_path.unlink(missing_ok=True)
    print(f"Saved paired development comparison: {output_path}")
    for name, values in report["systems"].items():
        print(name, json.dumps(values["metrics"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
