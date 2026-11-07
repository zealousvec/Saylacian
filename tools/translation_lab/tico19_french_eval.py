# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate Saylacian's installed English/French routes on TICO-19 dev only."""

from __future__ import annotations

import csv
import io
import json
import socket
import time
import zipfile
from pathlib import Path

from tools.translation_lab.marian_candidate import _score
from tools.translation_lab.tico19_benchmark import ARCHIVE_BYTES
from tools.translation_lab.tico19_benchmark import ARCHIVE_SHA256
from tools.translation_lab.tico19_benchmark import sha256_file

DEV_ROWS = 971
DEV_MEMBER = "tico19-testset/dev/dev.en-fr.tsv"
TSV_COLUMNS = (
    "sourceLang",
    "targetLang",
    "sourceString",
    "targetString",
    "stringID",
    "url",
    "license",
    "translator_ID",
)
SCHEMA_VERSION = 1


def load_french_dev(archive_path: Path) -> list[dict[str, str]]:
    """Load the pinned English→French development rows with row terms intact."""
    if not archive_path.is_file() or archive_path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("TICO-19 archive size does not match the pinned source.")
    if sha256_file(archive_path) != ARCHIVE_SHA256:
        raise ValueError("TICO-19 archive SHA-256 does not match the pin.")
    with zipfile.ZipFile(archive_path) as archive:
        try:
            stream = archive.open(DEV_MEMBER)
        except KeyError as error:
            raise ValueError(
                f"Pinned TICO-19 archive is missing {DEV_MEMBER}."
            ) from error
        with stream:
            rows = parse_french_dev(stream)
    if len(rows) != DEV_ROWS:
        raise ValueError(
            f"Expected {DEV_ROWS} TICO-19 French dev rows; found {len(rows)}."
        )
    return rows


def parse_french_dev(stream) -> list[dict[str, str]]:
    """Validate one TICO-19 English/French TSV and retain its row metadata."""
    reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8"), delimiter="\t")
    if tuple(reader.fieldnames or ()) != TSV_COLUMNS:
        raise ValueError("TICO-19 TSV header differs from the published schema.")
    rows = []
    seen = set()
    for line_number, row in enumerate(reader, start=2):
        if (row.get("sourceLang"), row.get("targetLang")) != ("en", "fr"):
            raise ValueError(f"Unexpected language pair on line {line_number}.")
        for field in ("sourceString", "targetString", "stringID", "license"):
            if not (row.get(field) or "").strip():
                raise ValueError(f"Empty required field {field} on line {line_number}.")
        if row["stringID"] in seen:
            raise ValueError(f"Duplicate TICO-19 string ID: {row['stringID']}")
        seen.add(row["stringID"])
        rows.append(
            {
                "id": row["stringID"],
                "english": row["sourceString"],
                "french": row["targetString"],
                "source_url": row["url"],
                "license": row["license"],
                "translator_id": row["translator_ID"],
            }
        )
    return rows


def _model_fingerprint(routes=(("English", "French"), ("French", "English"))) -> dict:
    from saylacian.core.translation import model_directory

    files = {}
    for source, target in routes:
        folder = model_directory(source, target)
        model = folder / "model" / "model.bin"
        if not model.is_file():
            model = folder / "model.bin"
        tokenizer_files = (
            (folder / "source.spm", folder / "target.spm")
            if (folder / "source.spm").is_file()
            else (folder / "sentencepiece.model",)
        )
        pack_root = next(
            (
                parent
                for parent in (folder.parent, folder.parent.parent)
                if (parent / "installed.json").is_file()
            ),
            None,
        )
        if pack_root is None:
            raise ValueError(
                f"Installed model pack manifest missing for {source}->{target}."
            )
        install_manifest = json.loads(
            (pack_root / "installed.json").read_text(encoding="utf-8")
        )
        expected_files = {
            item["path"]: item["sha256"] for item in install_manifest.get("files", [])
        }
        relative_model = model.relative_to(pack_root).as_posix()
        relative_tokenizers = [
            path.relative_to(pack_root).as_posix() for path in tokenizer_files
        ]
        if expected_files.get(relative_model) != sha256_file(model) or any(
            expected_files.get(relative) != sha256_file(path)
            for relative, path in zip(relative_tokenizers, tokenizer_files, strict=True)
        ):
            raise ValueError(
                f"Installed {source}->{target} model failed its pack hash check."
            )
        files[f"{source}->{target}"] = {
            "pack_id": install_manifest.get("pack_id"),
            "pack_version": install_manifest.get("version"),
            "model_sha256": expected_files[relative_model],
            "tokenizer_sha256": [expected_files[path] for path in relative_tokenizers],
        }
    from saylacian.core.translation import _model_roots

    candidate = next(
        (
            root / "somali" / "en_so_synthetic"
            for root in _model_roots()
            if (root / "somali" / "en_so_synthetic" / "model.bin").is_file()
        ),
        None,
    )
    if candidate is not None:
        files["English->Somali Latin optional candidate"] = {
            "model_sha256": sha256_file(candidate / "model.bin"),
            "source_tokenizer_sha256": sha256_file(candidate / "source.spm"),
            "target_tokenizer_sha256": sha256_file(candidate / "target.spm"),
        }
    return files


def _run_model_batch(texts: list[str], folder: Path) -> list[str]:
    """Batch the app's tokenization and decoding path without changing its model."""
    from saylacian.core.translation import MODEL_TOKEN_LIMIT
    from saylacian.core.translation import _clean_model_markers
    from saylacian.core.translation import _join_model_segments
    from saylacian.core.translation import _model_token_segments
    from saylacian.core.translation import load_model

    tokenizer, engine = load_model(str(folder))
    multilingual = isinstance(tokenizer, tuple)
    if multilingual:
        source_tokenizer, target_tokenizer = tokenizer
    else:
        source_tokenizer = target_tokenizer = tokenizer
    prepared = []
    flattened = []
    for text in texts:
        segments, separators, leading, trailing, _chunked = _model_token_segments(
            text, source_tokenizer
        )
        start = len(flattened)
        if multilingual:
            flattened.extend([">>som<<", *segment, "</s>"] for segment in segments)
        else:
            flattened.extend(segments)
        prepared.append((start, len(segments), separators, leading, trailing))

    outputs = []
    for start in range(0, len(flattened), 24):
        token_batch = flattened[start : start + 24]
        if multilingual and any(
            len(tokens) > MODEL_TOKEN_LIMIT for tokens in token_batch
        ):
            raise ValueError("A segmented input exceeds this model's 400-token limit.")
        options = {"max_input_length": 0, "max_decoding_length": 512}
        if multilingual:
            options["beam_size"] = 4
        translated = engine.translate_batch(token_batch, **options)
        outputs.extend(
            target_tokenizer.decode(result.hypotheses[0]) for result in translated
        )

    results = []
    for start, count, separators, leading, trailing in prepared:
        text = _join_model_segments(
            outputs[start : start + count], separators, leading, trailing
        )
        results.append(_clean_model_markers(text) if multilingual else text)
    return results


def _translate_many_direct(texts: list[str], source: str, target: str) -> list[str]:
    from saylacian.core.translation import model_directory
    from saylacian.core.translation import translate_meaning

    if (source, target) == ("English", "Somali Latin"):
        return [
            translate_meaning(text, source, target, provider_override="offline").text
            for text in texts
        ]
    return _run_model_batch(texts, model_directory(source, target))


def _read_checkpoint(
    path: Path,
    fingerprint: dict,
    *,
    resume: bool,
    required_fields=("english_to_french", "french_to_english"),
) -> dict[str, dict]:
    if not path.exists():
        return {}
    if not resume:
        raise FileExistsError(
            f"Prediction checkpoint already exists: {path}; pass --resume."
        )
    content = path.read_bytes()
    header_end = content.find(b"\n")
    if header_end < 0:
        raise ValueError("Prediction checkpoint header is incomplete.")
    header = json.loads(content[:header_end].decode("utf-8"))
    if header != {
        "schema_version": SCHEMA_VERSION,
        "archive_sha256": ARCHIVE_SHA256,
        "model_fingerprint": fingerprint,
    }:
        raise ValueError("Prediction checkpoint source/model fingerprint changed.")

    body_start = header_end + 1
    if len(content) > body_start and not content.endswith(b"\n"):
        tail_start = content.rfind(b"\n") + 1
        try:
            tail = json.loads(content[tail_start:].decode("utf-8"))
            tail_complete = bool(tail.get("id")) and all(
                tail.get(key) for key in required_fields
            )
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            tail_complete = False
        if tail_complete:
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
        if not identifier or identifier in records:
            raise ValueError("Prediction checkpoint has a missing or duplicate ID.")
        if not all(record.get(key) for key in required_fields):
            raise ValueError("Prediction checkpoint contains an incomplete row.")
        records[identifier] = record
    return records


def evaluate_french_dev(
    workspace: Path,
    *,
    archive_path: Path,
    run_id: str = "tico19-french-dev",
    resume: bool = False,
    limit: int | None = None,
) -> dict:
    """Run offline bidirectional dev scoring; checkpoint after every aligned row."""
    from tools.translation_lab.workspace import ensure_outside_repository

    ensure_outside_repository(workspace, Path(__file__).resolve().parents[2])
    if not run_id or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for char in run_id
    ):
        raise ValueError(
            "run_id may contain only letters, digits, hyphens and underscores."
        )
    if limit is not None and not 1 <= limit <= DEV_ROWS:
        raise ValueError(f"Development limit must be between 1 and {DEV_ROWS}.")
    rows = load_french_dev(archive_path)
    if limit is not None:
        rows = rows[:limit]
    fingerprint = _model_fingerprint()
    report_dir = workspace / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = report_dir / f"{run_id}-predictions.jsonl"
    report_path = report_dir / f"{run_id}.json"
    if report_path.exists():
        raise FileExistsError(f"Evaluation report already exists: {report_path}")
    completed = _read_checkpoint(predictions_path, fingerprint, resume=resume)
    known_ids = {row["id"] for row in rows}
    if not set(completed).issubset(known_ids):
        raise ValueError("Checkpoint contains rows outside this pinned dev split.")
    if not predictions_path.exists():
        header = {
            "schema_version": SCHEMA_VERSION,
            "archive_sha256": ARCHIVE_SHA256,
            "model_fingerprint": fingerprint,
        }
        predictions_path.write_text(
            json.dumps(header, sort_keys=True) + "\n", encoding="utf-8"
        )

    initial_completed = len(completed)
    from saylacian.core.translation import translate_meaning

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline French evaluation attempted network access.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    started = time.monotonic()
    try:
        with predictions_path.open("a", encoding="utf-8", newline="\n") as stream:
            for index, row in enumerate(rows, start=1):
                if row["id"] in completed:
                    continue
                en_fr = translate_meaning(
                    row["english"], "English", "French", provider_override="offline"
                )
                fr_en = translate_meaning(
                    row["french"], "French", "English", provider_override="offline"
                )
                record = {
                    "id": row["id"],
                    "english_to_french": en_fr.text,
                    "french_to_english": fr_en.text,
                }
                stream.write(
                    json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                )
                stream.flush()
                completed[row["id"]] = record
                if index == len(rows) or index % 25 == 0:
                    elapsed = max(time.monotonic() - started, 1e-9)
                    new_rows = len(completed) - initial_completed
                    print(
                        f"French dev rows {len(completed)}/{len(rows)} | "
                        f"{new_rows / elapsed:.2f} new rows/s",
                        flush=True,
                    )
    finally:
        socket.socket.connect = original_connect

    by_id = completed
    en_references = [row["french"] for row in rows]
    fr_references = [row["english"] for row in rows]
    en_predictions = [by_id[row["id"]]["english_to_french"] for row in rows]
    fr_predictions = [by_id[row["id"]]["french_to_english"] for row in rows]
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "COMPLETED",
        "benchmark": "TICO-19 French dev",
        "split": "dev",
        "domain": "health/COVID-19 public information",
        "rows": len(rows),
        "archive_sha256": ARCHIVE_SHA256,
        "model_fingerprint": fingerprint,
        "metrics": {
            "en-fr": _score(en_references, en_predictions),
            "fr-en": _score(fr_references, fr_predictions),
        },
        "prediction_sha256": sha256_file(predictions_path),
        "predictions_path": str(predictions_path),
        "network": "blocked",
        "training_or_promotion": False,
        "interpretation": (
            "Development-only automatic metrics; one health/COVID domain, not a "
            "general-language accuracy percentage or human fluency review."
        ),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def evaluate_somali_and_pivot_dev(
    workspace: Path,
    *,
    archive_path: Path,
    run_id: str = "tico19-somali-pivot-dev",
    resume: bool = False,
    limit: int | None = None,
) -> dict:
    """Score English/Somali and French/Somali product routes on matched dev IDs."""
    from tools.translation_lab.tico19_benchmark import load_split
    from tools.translation_lab.workspace import ensure_outside_repository

    ensure_outside_repository(workspace, Path(__file__).resolve().parents[2])
    if not run_id or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for char in run_id
    ):
        raise ValueError(
            "run_id may contain only letters, digits, hyphens and underscores."
        )
    if limit is not None and not 1 <= limit <= DEV_ROWS:
        raise ValueError(f"Development limit must be between 1 and {DEV_ROWS}.")

    french_rows = load_french_dev(archive_path)
    somali_rows = load_split(archive_path, "dev")
    french_by_id = {row["id"]: row for row in french_rows}
    somali_by_id = {row["record_id"]: row for row in somali_rows}
    if french_by_id.keys() != somali_by_id.keys():
        raise ValueError("TICO-19 French and Somali dev string IDs do not align.")
    rows = [
        {
            "id": french["id"],
            "english": french["english"],
            "french": french["french"],
            "somali": somali_by_id[french["id"]]["target_text"],
        }
        for french in french_rows
    ]
    if limit is not None:
        rows = rows[:limit]

    fingerprint = _model_fingerprint(
        (
            ("English", "Somali Latin"),
            ("Somali Latin", "English"),
            ("English", "French"),
            ("French", "English"),
        )
    )
    report_dir = workspace / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = report_dir / f"{run_id}-predictions.jsonl"
    report_path = report_dir / f"{run_id}.json"
    if report_path.exists():
        raise FileExistsError(f"Evaluation report already exists: {report_path}")
    required = ("en-so", "so-en", "fr-so", "so-fr")
    completed = _read_checkpoint(
        predictions_path, fingerprint, resume=resume, required_fields=required
    )
    known_ids = {row["id"] for row in rows}
    if not set(completed).issubset(known_ids):
        raise ValueError(
            "Prediction checkpoint contains rows outside this pinned dev split."
        )
    if not predictions_path.exists():
        header = {
            "schema_version": SCHEMA_VERSION,
            "archive_sha256": ARCHIVE_SHA256,
            "model_fingerprint": fingerprint,
        }
        predictions_path.write_text(
            json.dumps(header, sort_keys=True) + "\n", encoding="utf-8"
        )

    initial_completed = len(completed)

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline translation evaluation attempted network access.")

    original_connect = socket.socket.connect
    socket.socket.connect = deny_network
    started = time.monotonic()
    try:
        with predictions_path.open("a", encoding="utf-8", newline="\n") as stream:
            pending_rows = [row for row in rows if row["id"] not in completed]
            for start in range(0, len(pending_rows), 24):
                batch = pending_rows[start : start + 24]
                english = [row["english"] for row in batch]
                french = [row["french"] for row in batch]
                somali = [row["somali"] for row in batch]
                en_so = _translate_many_direct(english, "English", "Somali Latin")
                so_en = _translate_many_direct(somali, "Somali Latin", "English")
                fr_en = _translate_many_direct(french, "French", "English")
                fr_so = _translate_many_direct(fr_en, "English", "Somali Latin")
                so_fr = _translate_many_direct(so_en, "English", "French")
                for row, outputs in zip(
                    batch, zip(en_so, so_en, fr_so, so_fr, strict=True), strict=True
                ):
                    record = {
                        "id": row["id"],
                        "en-so": outputs[0],
                        "so-en": outputs[1],
                        "fr-so": outputs[2],
                        "so-fr": outputs[3],
                    }
                    stream.write(
                        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                    )
                    stream.flush()
                    completed[row["id"]] = record
                elapsed = max(time.monotonic() - started, 1e-9)
                new_rows = len(completed) - initial_completed
                print(
                    f"Somali/pivot dev rows {len(completed)}/{len(rows)} | "
                    f"{new_rows / elapsed:.2f} new rows/s",
                    flush=True,
                )
    finally:
        socket.socket.connect = original_connect

    references = {
        "en-so": [row["somali"] for row in rows],
        "so-en": [row["english"] for row in rows],
        "fr-so": [row["somali"] for row in rows],
        "so-fr": [row["french"] for row in rows],
    }
    metrics = {
        route: _score(references[route], [completed[row["id"]][route] for row in rows])
        for route in required
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "COMPLETED",
        "benchmark": "TICO-19 aligned French/Somali dev",
        "split": "dev",
        "domain": "health/COVID-19 public information",
        "rows": len(rows),
        "archive_sha256": ARCHIVE_SHA256,
        "matched_language_ids": len(french_by_id.keys() & somali_by_id.keys()),
        "model_fingerprint": fingerprint,
        "metrics": metrics,
        "prediction_sha256": sha256_file(predictions_path),
        "predictions_path": str(predictions_path),
        "network": "blocked",
        "training_or_promotion": False,
        "interpretation": (
            "Development-only automatic metrics. French/Somali routes pivot through "
            "English; scores are not a general-language accuracy percentage or "
            "human review."
        ),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
