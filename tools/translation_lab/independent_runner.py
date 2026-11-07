# SPDX-License-Identifier: AGPL-3.0-or-later
"""Durable, resumable checks using Saylacian's production transliterators."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
import subprocess
import time
import unicodedata
from datetime import UTC
from datetime import datetime
from pathlib import Path

from saylacian.core.transliteration import transliterate

from .state import _process_is_running
from .transliteration_eval import ROUTES
from .transliteration_eval import _make_input
from .transliteration_eval import verify_static_evidence


def _case(seed: int, ordinal: int) -> tuple[str, str, str, str, str, str]:
    source, target = ROUTES[ordinal % len(ROUTES)]
    # Replaying from the seed makes a case addressable without storing RNG state.
    rng = random.Random((seed << 32) ^ ordinal)
    value = _make_input(rng, source)
    kinds = (
        "seeded-random-invariance",
        "unicode-normalization",
        "punctuation-whitespace",
        "mixed-script-unknown-preservation",
        "empty-input",
        "bounded-long-input",
        "grapheme-longest-match",
        "seeded-random-invariance",
    )
    test_type = kinds[(ordinal // len(ROUTES)) % len(kinds)]
    if test_type == "unicode-normalization":
        value = unicodedata.normalize("NFD", "a\u0304 e\u0301 sh")
        expected_rule = "normalization variant remains deterministic and un-erased"
    elif test_type == "punctuation-whitespace":
        value += "\t\n!? /"
        expected_rule = "whitespace and punctuation remain at the outer boundaries"
    elif test_type == "mixed-script-unknown-preservation":
        value += "🙂漢\u0378"
        expected_rule = "unmapped mixed-script suffix is preserved"
    elif test_type == "empty-input":
        value = ""
        expected_rule = "empty input stays empty inside preserved outer punctuation"
    elif test_type == "bounded-long-input":
        value = (value * (128 // max(len(value), 1) + 1))[:128]
        expected_rule = "bounded 128-codepoint input completes deterministically"
    elif test_type == "grapheme-longest-match" and (source, target) == (
        "Somali Latin",
        "Osmanya",
    ):
        value = "dh sh kh"
        expected_rule = "Somali multigraphs use longest-token matching"
    else:
        test_type = "seeded-random-invariance"
        expected_rule = "determinism, non-erasure and punctuation preservation"
    cid = hashlib.sha256(
        f"v2\0{seed}\0{ordinal}\0{source}\0{target}\0{test_type}\0{value}".encode()
    ).hexdigest()
    return cid, source, target, value, test_type, expected_rule


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs(
            run_id TEXT PRIMARY KEY,
            seed INTEGER NOT NULL,
            target INTEGER NOT NULL,
            status TEXT NOT NULL,
            created REAL NOT NULL,
            generator_version TEXT NOT NULL DEFAULT 'seeded-python-rng-v1'
        );
        CREATE TABLE IF NOT EXISTS cases(
            run_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            case_id TEXT NOT NULL,
            input_hash TEXT NOT NULL,
            source TEXT NOT NULL,
            target_script TEXT NOT NULL,
            input TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            PRIMARY KEY(run_id, ordinal),
            UNIQUE(run_id, case_id)
        );
        CREATE TABLE IF NOT EXISTS attempts(
            run_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            attempt_no INTEGER NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            PRIMARY KEY(run_id, ordinal, attempt_no)
        );
        """
    )
    columns = {row[1] for row in db.execute("PRAGMA table_info(cases)")}
    migrations = {
        "route": "TEXT NOT NULL DEFAULT ''",
        "seed": "INTEGER NOT NULL DEFAULT 0",
        "test_type": "TEXT NOT NULL DEFAULT 'seeded-random-invariance'",
        "generator_version": "TEXT NOT NULL DEFAULT 'seeded-python-rng-v2'",
        "duration_ms": "REAL NOT NULL DEFAULT 0",
        "expected_rule": "TEXT NOT NULL DEFAULT 'determinism-and-preservation'",
        "evidence_level": "TEXT NOT NULL DEFAULT 'implementation-invariant'",
    }
    for name, declaration in migrations.items():
        if name not in columns:
            db.execute(f"ALTER TABLE cases ADD COLUMN {name} {declaration}")
    run_columns = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
    if "generator_version" not in run_columns:
        db.execute(
            "ALTER TABLE runs ADD COLUMN generator_version "
            "TEXT NOT NULL DEFAULT 'seeded-python-rng-v1'"
        )
    return db


def run_transliteration_check(
    workspace: Path,
    *,
    target: int = 100_000,
    seed: int = 1729,
    run_id: str | None = None,
    resume: bool = False,
    stop_after: int | None = None,
    max_hours: float | None = None,
    pause_requested: bool = False,
    retry_failures: bool = False,
    progress=None,
) -> dict:
    if target <= 0 or (stop_after is not None and stop_after < 1):
        raise ValueError("target and stop_after must be positive")
    if max_hours is not None and max_hours <= 0:
        raise ValueError("max_hours must be positive")
    workspace = Path(workspace)
    if resume and run_id is None:
        run_id = _latest_incomplete(workspace)
    run_id = run_id or f"script-{seed}-{int(time.time())}"
    _validate_run_id(run_id)
    db_path = workspace / "runs" / run_id / "run_state.sqlite"
    commit = _git_commit()
    config_hash = hashlib.sha256(
        json.dumps(
            {"mode": "transliteration-invariants", "seed": seed, "target": target},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    lock_path = db_path.with_name("active.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            owner = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            owner = {}
        if _process_is_running(owner.get("pid")):
            raise RuntimeError(
                f"Run {run_id} is already active (PID {owner.get('pid')})."
            )
        lock_path.unlink(missing_ok=True)
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
        json.dump({"pid": os.getpid()}, lock_file)
    db = _connect(db_path)
    pause_path = db_path.parent / "pause.requested"
    try:
        exists = db.execute(
            "SELECT seed,target,status,generator_version FROM runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if exists:
            if not resume:
                raise ValueError(f"Run {run_id} already exists; use --resume")
            if exists[0] != seed or exists[1] != target:
                raise ValueError("resume seed and target must match the original run")
            if exists[3] != "seeded-python-rng-v2":
                raise ValueError(
                    "This run uses an older case generator; use a new run ID "
                    "instead of mixing generator versions."
                )
        else:
            db.execute(
                "INSERT INTO runs "
                "(run_id,seed,target,status,created,generator_version) "
                "VALUES(?,?,?,?,?,?)",
                (run_id, seed, target, "RUNNING", time.time(), "seeded-python-rng-v2"),
            )
            db.commit()
        verify_static_evidence()
        done = db.execute(
            "SELECT COUNT(*) FROM cases WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        passed, failed = db.execute(
            "SELECT SUM(status='PASS'), SUM(status='FAIL') FROM cases WHERE run_id=?",
            (run_id,),
        ).fetchone()
        passed, failed = passed or 0, failed or 0
        inputs = {
            row[0]
            for row in db.execute(
                "SELECT DISTINCT input_hash FROM cases WHERE run_id=?", (run_id,)
            )
        }
        test_type_counts = _test_type_counts(db, run_id)
        retried = db.execute(
            "SELECT COUNT(*) FROM attempts WHERE run_id=? AND attempt_no>1",
            (run_id,),
        ).fetchone()[0]
        if retry_failures:
            retried += _retry_failures(db, run_id)
            passed, failed = db.execute(
                "SELECT SUM(status='PASS'), SUM(status='FAIL') "
                "FROM cases WHERE run_id=?",
                (run_id,),
            ).fetchone()
            passed, failed = passed or 0, failed or 0
        if done >= target and not (retry_failures and failed):
            with db:
                db.execute(
                    "UPDATE runs SET status='COMPLETED' WHERE run_id=?", (run_id,)
                )
            return {
                "run_id": run_id,
                "checkpoint_timestamp": datetime.now(UTC).isoformat(),
                "phase": "TRANSLITERATION_INVARIANT_CHECKS",
                "git_commit": commit,
                "config_sha256": config_hash,
                "seed": seed,
                "target": target,
                "attempted": done + retried,
                "completed": done,
                "retried": retried,
                "unique_case_ids": done,
                "unique_inputs": len(inputs),
                "test_type_counts": test_type_counts,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "timeouts": 0,
                "resource_interruptions": 0,
                "cases_per_second": None,
                "oracle": "production transliterator invariants; not semantic accuracy",
                "status": "COMPLETED",
                "database": str(db_path),
                "progress_log": str(db_path.parent / "progress.jsonl"),
            }
        started = time.perf_counter()
        starting_count = done
        pause_path.unlink(missing_ok=True)
        jsonl = db_path.parent / "progress.jsonl"
        with jsonl.open("a", encoding="utf-8", buffering=1) as log:
            while done < target:
                end = min(target, done + 250)
                rows = []
                for ordinal in range(done, end):
                    cid, source, dest, value, test_type, expected_rule = _case(
                        seed, ordinal
                    )
                    input_hash = hashlib.sha256(value.encode()).hexdigest()
                    case_started = time.perf_counter()
                    status, error = _evaluate_case(source, dest, value, test_type)
                    duration_ms = (time.perf_counter() - case_started) * 1000
                    rows.append(
                        (
                            run_id,
                            ordinal,
                            cid,
                            input_hash,
                            source,
                            dest,
                            value,
                            status,
                            error,
                            f"{source} -> {dest}",
                            seed,
                            test_type,
                            "seeded-python-rng-v2",
                            duration_ms,
                            expected_rule,
                            "implementation-invariant; no semantic oracle",
                        )
                    )
                with db:
                    db.executemany(
                        "INSERT INTO cases "
                        "(run_id,ordinal,case_id,input_hash,source,target_script,input,"
                        "status,error,route,seed,test_type,generator_version,duration_ms,"
                        "expected_rule,evidence_level) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        rows,
                    )
                    db.executemany(
                        "INSERT INTO attempts VALUES(?,?,?,?,?)",
                        [(row[0], row[1], 1, row[7], row[8]) for row in rows],
                    )
                    db.execute(
                        "UPDATE runs SET status='RUNNING' WHERE run_id=?", (run_id,)
                    )
                done += len(rows)
                passed += sum(row[7] == "PASS" for row in rows)
                failed += sum(row[7] == "FAIL" for row in rows)
                inputs.update(row[3] for row in rows)
                for row in rows:
                    test_type_counts[row[11]] = test_type_counts.get(row[11], 0) + 1
                record = _snapshot(
                    run_id,
                    target,
                    seed,
                    done,
                    passed,
                    failed,
                    len(inputs),
                    started,
                    starting_count,
                    attempted=done + retried,
                    retried=retried,
                )
                record["checkpoint_timestamp"] = datetime.now(UTC).isoformat()
                record["phase"] = "TRANSLITERATION_INVARIANT_CHECKS"
                record["git_commit"] = commit
                record["config_sha256"] = config_hash
                record["test_type_counts"] = dict(sorted(test_type_counts.items()))
                record["job_id"] = f"{run_id}:{done - len(rows)}-{done}"
                log.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                if progress:
                    progress(record)
                if pause_requested or (
                    max_hours and time.perf_counter() - started >= max_hours * 3600
                ):
                    with db:
                        db.execute(
                            "UPDATE runs SET status='PAUSED' WHERE run_id=?", (run_id,)
                        )
                    return {
                        **record,
                        "status": "PAUSED",
                        "database": str(db_path),
                        "progress_log": str(jsonl),
                    }
                if pause_path.exists():
                    pause_path.unlink(missing_ok=True)
                    with db:
                        db.execute(
                            "UPDATE runs SET status='PAUSED' WHERE run_id=?", (run_id,)
                        )
                    return {
                        **record,
                        "status": "PAUSED",
                        "database": str(db_path),
                        "progress_log": str(jsonl),
                    }
                if stop_after is not None and done >= stop_after:
                    with db:
                        db.execute(
                            "UPDATE runs SET status='INTERRUPTED' WHERE run_id=?",
                            (run_id,),
                        )
                    return {
                        **record,
                        "status": "INTERRUPTED",
                        "database": str(db_path),
                        "progress_log": str(jsonl),
                    }
        if retry_failures:
            new_retries = _retry_failures(db, run_id)
            retried += new_retries
            passed, failed = db.execute(
                "SELECT SUM(status='PASS'), SUM(status='FAIL') "
                "FROM cases WHERE run_id=?",
                (run_id,),
            ).fetchone()
            passed, failed = passed or 0, failed or 0
        with db:
            db.execute("UPDATE runs SET status='COMPLETED' WHERE run_id=?", (run_id,))
        final_record = _snapshot(
            run_id,
            target,
            seed,
            done,
            passed,
            failed,
            len(inputs),
            started,
            starting_count,
            attempted=done + retried,
            retried=retried,
        )
        final_record["checkpoint_timestamp"] = datetime.now(UTC).isoformat()
        final_record["job_id"] = f"{run_id}:complete"
        final_record["git_commit"] = commit
        final_record["config_sha256"] = config_hash
        final_record["test_type_counts"] = dict(sorted(test_type_counts.items()))
        with (db_path.parent / "progress.jsonl").open(
            "a", encoding="utf-8", buffering=1
        ) as log:
            log.write(
                json.dumps(final_record, ensure_ascii=False, sort_keys=True) + "\n"
            )
        if progress:
            progress(final_record)
        return {
            **final_record,
            "git_commit": commit,
            "config_sha256": config_hash,
            "status": "COMPLETED",
            "database": str(db_path),
            "progress_log": str(jsonl),
        }
    except KeyboardInterrupt:
        with db:
            db.execute("UPDATE runs SET status='INTERRUPTED' WHERE run_id=?", (run_id,))
        raise
    finally:
        db.close()
        lock_path.unlink(missing_ok=True)


def _latest_incomplete(workspace: Path) -> str:
    candidates = []
    for path in (workspace / "runs").glob("*/run_state.sqlite"):
        try:
            with sqlite3.connect(path) as db:
                row = db.execute(
                    "SELECT run_id,target,status,created,generator_version FROM runs "
                    "ORDER BY created DESC LIMIT 1"
                ).fetchone()
                if row and row[2] != "COMPLETED" and row[4] == "seeded-python-rng-v2":
                    completed = db.execute(
                        "SELECT COUNT(*) FROM cases WHERE run_id=?", (row[0],)
                    ).fetchone()[0]
                    if completed < row[1]:
                        candidates.append((row[3], row[0]))
        except sqlite3.Error:
            continue
    if not candidates:
        raise ValueError("No incomplete transliteration run exists to resume")
    return max(candidates)[1]


def _validate_run_id(run_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", run_id):
        raise ValueError("run_id must be 1-100 safe filename characters")


def _test_type_counts(db: sqlite3.Connection, run_id: str) -> dict[str, int]:
    return {
        test_type: count
        for test_type, count in db.execute(
            "SELECT test_type,COUNT(*) FROM cases WHERE run_id=? GROUP BY test_type",
            (run_id,),
        )
    }


def _git_commit() -> str | None:
    repository = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def _retry_failures(db: sqlite3.Connection, run_id: str) -> int:
    failures = db.execute(
        "SELECT ordinal,source,target_script,input,test_type FROM cases "
        "WHERE run_id=? AND status='FAIL' ORDER BY ordinal",
        (run_id,),
    ).fetchall()
    for ordinal, source, target, value, test_type in failures:
        result, error = _evaluate_case(source, target, value, test_type)
        attempt = db.execute(
            "SELECT MAX(COALESCE(MAX(attempt_no),1),1)+1 FROM attempts "
            "WHERE run_id=? AND ordinal=?",
            (run_id, ordinal),
        ).fetchone()[0]
        with db:
            db.execute(
                "INSERT INTO attempts VALUES(?,?,?,?,?)",
                (run_id, ordinal, attempt, result, error),
            )
            db.execute(
                "UPDATE cases SET status=?,error=? WHERE run_id=? AND ordinal=?",
                (result, error, run_id, ordinal),
            )
    return len(failures)


def _evaluate_case(
    source: str, target: str, value: str, test_type: str
) -> tuple[str, str | None]:
    try:
        first = transliterate(value, source, target)
        second = transliterate(value, source, target)
        wrapped = transliterate("<" + value + ">", source, target)
        if (
            first != second
            or (value and not first.text)
            or not (wrapped.text.startswith("<") and wrapped.text.endswith(">"))
        ):
            raise AssertionError("determinism, non-erasure, or punctuation failed")
        if test_type == "mixed-script-unknown-preservation" and not first.text.endswith(
            "🙂漢\u0378"
        ):
            raise AssertionError("unmapped mixed-script suffix was not preserved")
        if test_type == "grapheme-longest-match" and (source, target) == (
            "Somali Latin",
            "Osmanya",
        ):
            for token in ("dh", "sh", "kh"):
                combined = transliterate(token, source, target).text
                separate = "".join(
                    transliterate(char, source, target).text for char in token
                )
                if combined == separate:
                    raise AssertionError(f"multigraph {token!r} was not matched whole")
        return "PASS", None
    except (AssertionError, ValueError, KeyError, TypeError, IndexError) as exc:
        return "FAIL", f"{type(exc).__name__}: {str(exc)[:160]}"


def _snapshot(
    run_id: str,
    target: int,
    seed: int,
    completed: int,
    passed: int,
    failed: int,
    unique_inputs: int,
    started: float,
    starting_count: int,
    *,
    attempted: int,
    retried: int,
) -> dict:
    return {
        "run_id": run_id,
        "checkpoint_timestamp": datetime.now(UTC).isoformat(),
        "phase": "TRANSLITERATION_INVARIANT_CHECKS",
        "seed": seed,
        "target": target,
        "attempted": attempted,
        "completed": completed,
        "retried": retried,
        "unique_case_ids": completed,
        "unique_inputs": unique_inputs,
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "timeouts": 0,
        "resource_interruptions": 0,
        "gpu_sampling": "not applicable to CPU-only transliteration checks",
        "cases_per_second": round(
            (attempted - starting_count) / max(time.perf_counter() - started, 0.001),
            1,
        ),
        "oracle": "production transliterator invariants; not semantic accuracy",
    }
