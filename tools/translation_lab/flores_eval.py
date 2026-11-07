# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline evaluation of installed Saylacian routes on FLORES-200 devtest."""

from __future__ import annotations

import hashlib
import json
import socket
import tarfile
import time
from pathlib import Path

from tools.translation_lab.marian_candidate import _score

ARCHIVE_BYTES = 25_585_843
ARCHIVE_SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"
ARCHIVE_URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
REVISION = "facebookresearch/flores FLORES-200 author release"
LANGUAGE_FILES = {
    "english": "./flores200_dataset/devtest/eng_Latn.devtest",
    "french": "./flores200_dataset/devtest/fra_Latn.devtest",
    "somali": "./flores200_dataset/devtest/som_Latn.devtest",
}
ROW_COUNT = 1012
SCHEMA_VERSION = 1
ROUTES = ("en-fr", "fr-en", "en-so", "so-en", "fr-so", "so-fr")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_flores_lines(contents: bytes, language: str) -> list[str]:
    """Decode one pinned UTF-8 language file without normalizing its text."""
    if language not in LANGUAGE_FILES:
        raise ValueError(f"Unsupported FLORES language: {language}")
    text = contents.decode("utf-8", errors="strict")
    lines = text.splitlines()
    if len(lines) != ROW_COUNT or any(not line.strip() for line in lines):
        raise ValueError(
            f"Expected {ROW_COUNT} non-empty FLORES {language} devtest rows; "
            f"found {len(lines)}."
        )
    return lines


def load_flores_devtest(archive_path: Path) -> list[dict[str, str]]:
    """Read only the three named FLORES devtest members from the official tar."""
    if not archive_path.is_file() or archive_path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("FLORES-200 archive size does not match the pin.")
    archive_hash = sha256_file(archive_path)
    if archive_hash != ARCHIVE_SHA256:
        raise ValueError("FLORES-200 archive SHA-256 does not match the pin.")
    with tarfile.open(archive_path, "r:*") as archive:
        rows_by_language = {}
        for language, member_name in LANGUAGE_FILES.items():
            try:
                member = archive.getmember(member_name)
            except KeyError as error:
                raise ValueError(
                    f"Official FLORES archive is missing {member_name}."
                ) from error
            if not member.isfile():
                raise ValueError(f"FLORES member is not a regular file: {member_name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"Could not read FLORES member: {member_name}")
            with stream:
                rows_by_language[language] = parse_flores_lines(stream.read(), language)
    lengths = {len(rows) for rows in rows_by_language.values()}
    if lengths != {ROW_COUNT}:
        raise ValueError("FLORES language files do not have matching row counts.")
    return [
        {
            "id": str(index),
            "english": rows_by_language["english"][index - 1],
            "french": rows_by_language["french"][index - 1],
            "somali": rows_by_language["somali"][index - 1],
        }
        for index in range(1, ROW_COUNT + 1)
    ]


def _read_checkpoint(path: Path, fingerprint: dict, *, resume: bool) -> dict:
    if not path.exists():
        return {}
    if not resume:
        raise FileExistsError(f"Prediction checkpoint exists: {path}; pass --resume.")
    content = path.read_bytes()
    header_end = content.find(b"\n")
    if header_end < 0:
        raise ValueError("FLORES checkpoint header is incomplete.")
    header = json.loads(content[:header_end].decode("utf-8"))
    if header != {
        "schema_version": SCHEMA_VERSION,
        "archive_sha256": ARCHIVE_SHA256,
        "model_fingerprint": fingerprint,
    }:
        raise ValueError("FLORES checkpoint archive/model fingerprint changed.")
    body_start = header_end + 1
    if len(content) > body_start and not content.endswith(b"\n"):
        tail_start = content.rfind(b"\n") + 1
        try:
            tail = json.loads(content[tail_start:].decode("utf-8"))
            complete = bool(tail.get("id")) and all(tail.get(key) for key in ROUTES)
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            complete = False
        if complete:
            with path.open("ab") as stream:
                stream.write(b"\n")
            content += b"\n"
        else:
            with path.open("r+b") as stream:
                stream.truncate(tail_start)
            content = content[:tail_start]
    records = {}
    for line in content[body_start:].decode("utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        identifier = record.get("id")
        if (
            not identifier
            or identifier in records
            or not all(record.get(key) for key in ROUTES)
        ):
            raise ValueError("FLORES checkpoint has a duplicate or incomplete row.")
        records[identifier] = record
    return records


def evaluate_flores_devtest(
    workspace: Path,
    *,
    archive_path: Path,
    run_id: str = "flores200-route-matrix-devtest",
    resume: bool = False,
) -> dict:
    """Score every installed direct/pivot route and save a resumable private report."""
    from tools.translation_lab.tico19_french_eval import _model_fingerprint
    from tools.translation_lab.tico19_french_eval import _translate_many_direct
    from tools.translation_lab.workspace import ensure_outside_repository

    ensure_outside_repository(workspace, Path(__file__).resolve().parents[2])
    if not run_id or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for char in run_id
    ):
        raise ValueError(
            "run_id may contain only letters, digits, hyphens and underscores."
        )
    rows = load_flores_devtest(archive_path)
    fingerprint = _model_fingerprint(
        (
            ("English", "French"),
            ("French", "English"),
            ("English", "Somali Latin"),
            ("Somali Latin", "English"),
        )
    )
    report_dir = workspace / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = report_dir / f"{run_id}-predictions.jsonl"
    report_path = report_dir / f"{run_id}.json"
    if report_path.exists():
        raise FileExistsError(f"FLORES report already exists: {report_path}")
    completed = _read_checkpoint(predictions_path, fingerprint, resume=resume)
    known_ids = {row["id"] for row in rows}
    if not set(completed).issubset(known_ids):
        raise ValueError("FLORES checkpoint contains rows outside devtest.")
    if not predictions_path.exists():
        predictions_path.write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "archive_sha256": ARCHIVE_SHA256,
                    "model_fingerprint": fingerprint,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    initial_completed = len(completed)

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline FLORES evaluation attempted network access.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    started = time.monotonic()
    try:
        with predictions_path.open("a", encoding="utf-8", newline="\n") as stream:
            pending = [row for row in rows if row["id"] not in completed]
            for start in range(0, len(pending), 24):
                batch = pending[start : start + 24]
                english = [row["english"] for row in batch]
                french = [row["french"] for row in batch]
                somali = [row["somali"] for row in batch]
                en_fr = _translate_many_direct(english, "English", "French")
                fr_en = _translate_many_direct(french, "French", "English")
                en_so = _translate_many_direct(english, "English", "Somali Latin")
                so_en = _translate_many_direct(somali, "Somali Latin", "English")
                fr_so = _translate_many_direct(fr_en, "English", "Somali Latin")
                so_fr = _translate_many_direct(so_en, "English", "French")
                for row, outputs in zip(
                    batch,
                    zip(en_fr, fr_en, en_so, so_en, fr_so, so_fr, strict=True),
                    strict=True,
                ):
                    record = {"id": row["id"]}
                    record.update(zip(ROUTES, outputs, strict=True))
                    stream.write(
                        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                    )
                    stream.flush()
                    completed[row["id"]] = record
                elapsed = max(time.monotonic() - started, 1e-9)
                new_rows = len(completed) - initial_completed
                print(
                    f"FLORES devtest rows {len(completed)}/{len(rows)} | "
                    f"{new_rows / elapsed:.2f} new rows/s",
                    flush=True,
                )
    finally:
        socket.socket.connect = original_connect

    references = {
        "en-fr": [row["french"] for row in rows],
        "fr-en": [row["english"] for row in rows],
        "en-so": [row["somali"] for row in rows],
        "so-en": [row["english"] for row in rows],
        "fr-so": [row["somali"] for row in rows],
        "so-fr": [row["french"] for row in rows],
    }
    metrics = {
        route: _score(references[route], [completed[row["id"]][route] for row in rows])
        for route in ROUTES
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "COMPLETED",
        "benchmark": "FLORES-200",
        "revision": REVISION,
        "split": "devtest",
        "license": "CC-BY-SA-4.0",
        "rows": len(rows),
        "archive_bytes": ARCHIVE_BYTES,
        "archive_sha256": ARCHIVE_SHA256,
        "model_fingerprint": fingerprint,
        "metrics": metrics,
        "prediction_sha256": sha256_file(predictions_path),
        "predictions_path": str(predictions_path),
        "network": "blocked during inference",
        "extracted_members": list(LANGUAGE_FILES.values()),
        "hidden_test_split_loaded": False,
        "training_or_promotion": False,
        "interpretation": (
            "Automatic metrics on the public 1,012-row devtest split. This is a "
            "multidomain research benchmark, not a general accuracy percentage or "
            "fluent-speaker review. French/Somali routes pivot through English."
        ),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
