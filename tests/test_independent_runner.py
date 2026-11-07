from __future__ import annotations

import sqlite3
import subprocess
import sys
import time

import pytest

from tools.translation_lab import independent_runner
from tools.translation_lab.independent_runner import _case
from tools.translation_lab.independent_runner import _evaluate_case
from tools.translation_lab.independent_runner import run_transliteration_check
from tools.translation_lab.runner import current_status
from tools.translation_lab.training_smoke import run_training_smoke


def test_transliteration_run_recovers_without_duplicate_case_ids(tmp_path):
    first = run_transliteration_check(
        tmp_path, target=1_000, seed=83, run_id="recover-me", stop_after=500
    )
    assert first["status"] == "INTERRUPTED"
    assert first["completed"] == 500

    result = run_transliteration_check(tmp_path, target=1_000, seed=83, resume=True)
    assert result["status"] == "COMPLETED"
    assert result["completed"] == result["unique_case_ids"] == 1_000
    with sqlite3.connect(result["database"]) as db:
        assert db.execute(
            "SELECT COUNT(*), COUNT(DISTINCT case_id) FROM cases"
        ).fetchone() == (1_000, 1_000)
        taxonomy = db.execute(
            "SELECT COUNT(DISTINCT test_type),MIN(seed),MAX(seed),"
            "MIN(duration_ms),COUNT(DISTINCT generator_version) FROM cases"
        ).fetchone()
        assert taxonomy[:3] == (7, 83, 83)
        assert taxonomy[3] >= 0
        assert taxonomy[4] == 1
    assert sum(result["test_type_counts"].values()) == 1_000
    latest = current_status(tmp_path)["latest_transliteration_run"]
    assert latest["run_id"] == "recover-me"


def test_resume_requires_original_seed_and_target(tmp_path):
    run_transliteration_check(
        tmp_path, target=10, seed=7, run_id="pinned", stop_after=5
    )
    with pytest.raises(ValueError, match="must match"):
        run_transliteration_check(
            tmp_path, target=11, seed=7, run_id="pinned", resume=True
        )


def test_resume_rejects_mixed_generator_versions(tmp_path):
    result = run_transliteration_check(
        tmp_path, target=4, seed=12, run_id="generator", stop_after=2
    )
    with sqlite3.connect(result["database"]) as db:
        db.execute(
            "UPDATE runs SET generator_version='seeded-python-rng-v1' "
            "WHERE run_id='generator'"
        )
    with pytest.raises(ValueError, match="older case generator"):
        run_transliteration_check(
            tmp_path, target=4, seed=12, run_id="generator", resume=True
        )


def test_training_smoke_changes_weights_and_resumes(tmp_path):
    interrupted = run_training_smoke(tmp_path, run_id="weights", steps=12, stop_after=4)
    assert interrupted["status"] == "INTERRUPTED"
    result = run_training_smoke(tmp_path, run_id="weights", steps=12, resume=True)
    assert result["status"] == "COMPLETED"
    assert result["completed_steps"] == 12
    assert result["parameters_changed"] is True
    assert result["train_loss"] < 5


def test_graceful_pause_resumes_at_committed_checkpoint(tmp_path):
    def request_pause(counts):
        if counts["completed"] == 250:
            (tmp_path / "runs" / "pause-me" / "pause.requested").write_text("pause")

    paused = run_transliteration_check(
        tmp_path,
        target=1_000,
        seed=99,
        run_id="pause-me",
        progress=request_pause,
    )
    assert paused["status"] == "PAUSED"
    result = run_transliteration_check(
        tmp_path, target=1_000, seed=99, run_id="pause-me", resume=True
    )
    assert result["status"] == "COMPLETED"
    assert result["unique_case_ids"] == 1_000


def test_retry_failure_preserves_attempt_history(tmp_path, monkeypatch):
    real_transliterate = independent_runner.transliterate
    first_call = True

    def fail_once(value, source, target):
        nonlocal first_call
        if first_call:
            first_call = False
            raise ValueError("injected recoverable failure")
        return real_transliterate(value, source, target)

    monkeypatch.setattr(independent_runner, "transliterate", fail_once)
    result = run_transliteration_check(
        tmp_path, target=1, seed=22, run_id="retry-me", retry_failures=True
    )
    assert result["status"] == "COMPLETED"
    assert result["attempted"] == 2
    assert result["completed"] == result["unique_case_ids"] == 1
    assert result["retried"] == 1
    assert result["passed"] == 1
    assert result["failed"] == 0


def test_case_records_cover_generator_taxonomy_and_focused_rules():
    cases = [_case(17, ordinal) for ordinal in range(64)]
    assert {case[4] for case in cases} == {
        "seeded-random-invariance",
        "unicode-normalization",
        "punctuation-whitespace",
        "mixed-script-unknown-preservation",
        "empty-input",
        "bounded-long-input",
        "grapheme-longest-match",
    }
    for _case_id, source, target, value, test_type, _expected in cases:
        status, _error = _evaluate_case(source, target, value, test_type)
        assert status == "PASS"


def test_abrupt_process_termination_recovers_committed_cases(tmp_path):
    script = """
import sys, time
import tools.translation_lab.independent_runner as runner
real = runner.transliterate
def slow(value, source, target):
    time.sleep(0.001)
    return real(value, source, target)
runner.transliterate = slow
runner.run_transliteration_check(
    sys.argv[1], target=1000, seed=901, run_id='killed', progress=None
)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=__import__("pathlib").Path(__file__).resolve().parents[1],
    )
    database = tmp_path / "runs" / "killed" / "run_state.sqlite"
    deadline = time.time() + 20
    committed = 0
    while time.time() < deadline and process.poll() is None:
        if database.exists():
            try:
                with sqlite3.connect(database, timeout=0.1) as db:
                    committed = db.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
            except sqlite3.OperationalError:
                pass
        if committed >= 250:
            break
        time.sleep(0.05)
    assert committed >= 250
    process.kill()
    process.wait(timeout=10)

    result = run_transliteration_check(
        tmp_path, target=1_000, seed=901, run_id="killed", resume=True
    )
    assert result["status"] == "COMPLETED"
    assert result["completed"] == result["unique_case_ids"] == 1_000
    with sqlite3.connect(database) as db:
        assert db.execute(
            "SELECT COUNT(*),COUNT(DISTINCT case_id) FROM cases"
        ).fetchone() == (1_000, 1_000)
