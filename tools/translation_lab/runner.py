# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checkpointed offline stages for the user-launched research process."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

from .acquisition import acquire_approved_sources
from .capabilities import build_inventory
from .config import LabConfig
from .config import config_digest
from .prepare_data import prepare_google_smol
from .state import RunLock
from .state import atomic_json
from .state import checkpoint
from .state import clear_pause
from .state import new_run
from .state import pause_requested
from .state import read_json
from .state import utc_now
from .translation_eval import evaluate_prepared_google_smol
from .transliteration_eval import evaluate_script_cases
from .workspace import initialize_workspace


def source_revision(repository: Path) -> str | None:
    import hashlib
    import subprocess

    try:
        head = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    digest = hashlib.sha256()
    targets = [repository / "tools/local_translation_lab.py"]
    targets.extend(sorted((repository / "tools/translation_lab").glob("*.py")))
    targets.extend(
        repository / name
        for name in (
            "saylacian/core/translation.py",
            "saylacian/core/transliteration.py",
            "saylacian/core/capabilities.py",
            "saylacian/core/data/osmanya.json",
            "saylacian/core/data/scripts/borama.json",
            "saylacian/core/data/scripts/kaddare.json",
            "research/sources.catalog.json",
            "research/translation_lab.example.toml",
        )
    )
    for path in targets:
        if path.is_file():
            digest.update(path.relative_to(repository).as_posix().encode())
            digest.update(path.read_bytes())
    return f"{head}:{digest.hexdigest()}"


def _step_path(workspace: Path, run_id: str) -> Path:
    path = workspace / "experiments" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_step(state: dict, state_path: Path, name: str, result: dict) -> None:
    encoded = json.dumps(
        result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    state["completed_steps"][name] = {
        "completed_utc": utc_now(),
        "sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "result": result,
    }
    for key in (
        "generated_checks",
        "executed_checks",
        "reference_scored_translations",
        "human_reviewed_examples",
    ):
        state["counts"][key] = sum(
            step.get("result", {}).get(key, 0)
            for step in state["completed_steps"].values()
        )
    checkpoint(state_path, state, stage=name.upper())


def run_overnight(
    repository: Path,
    workspace: Path,
    config_path: Path,
    config: LabConfig,
    *,
    resume: bool = False,
    recover_stale_lock: bool = False,
    fault_after: str | None = None,
) -> dict:
    initialize_workspace(workspace, repository, config_path)
    state_path = workspace / "locks" / "active_run.json"
    code_revision = source_revision(repository)
    with RunLock(workspace, recover_stale=recover_stale_lock):
        state = read_json(state_path) if resume else None
        config_hash = config_digest(config_path)
        if state:
            if state.get("config_sha256") != config_hash:
                raise ValueError(
                    "Saved run config changed; start a new run or restore "
                    "its exact config."
                )
            if state.get("source_revision") != code_revision:
                raise ValueError(
                    "Source revision changed since checkpoint; use a new run "
                    "to avoid incompatible resume."
                )
            if state.get("status") not in {"PAUSED", "FAILED", "RUNNING"}:
                raise ValueError(
                    f"No resumable run is available (state: {state.get('status')})."
                )
            clear_pause(workspace)
        else:
            state = new_run(config_hash, code_revision, asdict(config))
        state["status"] = "RUNNING"
        checkpoint(state_path, state, stage=state.get("stage", "PREFLIGHT"))
        started = time.monotonic()
        experiment = _step_path(workspace, state["run_id"])

        def execute(name: str, action):
            if name in state["completed_steps"]:
                return state["completed_steps"][name]["result"]
            if pause_requested(workspace):
                state["status"] = "PAUSED"
                checkpoint(state_path, state, stage=name.upper())
                raise PauseRun("Pause requested at safe stage boundary.")
            if time.monotonic() - started >= config.max_runtime_hours * 3600:
                state["status"] = "PAUSED"
                checkpoint(state_path, state, stage=name.upper())
                raise PauseRun(
                    "Configured runtime budget reached at safe stage boundary."
                )
            result = action()
            atomic_json(experiment / f"{name}.json", result)
            _save_step(state, state_path, name, result)
            if fault_after == name:
                raise RuntimeError(
                    f"Injected recovery test failure after {name} checkpoint."
                )
            return result

        try:
            execute("preflight", lambda: build_inventory(repository))
            acquisition_result = execute(
                "approved-data-acquisition",
                lambda: acquire_approved_sources(workspace, config),
            )
            preparation_result = execute(
                "corpus-preparation",
                lambda: _prepare_approved_data(repository, workspace, config),
            )
            script_result = execute(
                "script-evaluation",
                lambda: evaluate_script_cases(config.script_checks),
            )
            translation_result = execute(
                "translation-baseline",
                lambda: {
                    "status": "SKIPPED",
                    "reason": (
                        "TICO-19 final test references are reserved. Use the "
                        "separately guarded dev-only candidate evaluator."
                    ),
                    "reference_scored_translations": 0,
                },
            )
            model_evaluation = execute(
                "prepared-model-evaluation",
                lambda: evaluate_prepared_google_smol(
                    workspace,
                    config.translation_samples,
                    seed=1729,
                ),
            )
            training_result = execute(
                "training-gate", lambda: _training_gate(repository, config)
            )
            summary = {
                "schema_version": 1,
                "run_id": state["run_id"],
                "status": "COMPLETED_WITH_BLOCKERS"
                if training_result["status"] == "BLOCKED"
                else "COMPLETED",
                "source_revision": code_revision,
                "created_utc": state["created_utc"],
                "finished_utc": utc_now(),
                "counts": state["counts"],
                "transliteration": script_result,
                "translation": translation_result,
                "data_acquisition": acquisition_result,
                "data_preparation": preparation_result,
                "model_evaluation": model_evaluation,
                "training": training_result,
                "automatic_promotion": False,
            }
            execute("report", lambda: summary)
            state["status"] = summary["status"]
            state["error"] = None
            checkpoint(state_path, state, stage="COMPLETED")
            atomic_json(workspace / "reports" / "latest.json", summary)
            _write_markdown(workspace / "reports" / "latest.md", summary)
            return summary
        except PauseRun:
            raise
        except Exception as error:
            state["status"] = "FAILED"
            state["error"] = {"type": type(error).__name__, "message": str(error)[:300]}
            checkpoint(state_path, state, stage="FAILED")
            raise


class PauseRun(RuntimeError):
    pass


def _training_gate(repository: Path, config: LabConfig) -> dict:
    if not config.training_enabled:
        return {
            "status": "BLOCKED",
            "reason": "Training is disabled in the active lab config.",
        }
    try:
        import torch
        import transformers
    except ImportError:
        return {
            "status": "BLOCKED",
            "reason": "PyTorch/Transformers training extras are missing. "
            "The M2M100 LoRA trainer is available in the isolated training "
            "runtime; run tools/setup_translation_training.cmd there, then "
            "tools/run_translation_lab_training.cmd. App dependencies stay separate.",
        }
    if not config.approved_source_ids:
        return {
            "status": "BLOCKED",
            "reason": "No owner-approved training data source is configured.",
        }
    return {
        "status": "BLOCKED",
        "reason": "The M2M100 LoRA route is implemented, but training must "
        "still pass model/data hash and hardware preflight in the isolated "
        "training runtime. No candidate is promoted automatically.",
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "repository": str(repository.name),
    }


def _prepare_approved_data(
    repository: Path,
    workspace: Path,
    config: LabConfig,
) -> dict:
    source_id = "google-smol-en-so"
    if source_id not in config.approved_source_ids:
        return {
            "status": "SKIPPED",
            "reason": (
                "No locally approved English–Somali training source is configured."
            ),
        }
    catalog_path = repository / "research/sources.catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    source = next(item for item in catalog if item["source_id"] == source_id)
    artifact = source["artifacts"][0]
    cached_file = workspace / "cache/downloads" / artifact["sha256"] / "artifact"
    if not cached_file.is_file():
        return {
            "status": "BLOCKED",
            "reason": (
                "Approved corpus was not acquired; check the local registry "
                "and source rights."
            ),
        }
    return prepare_google_smol(cached_file, workspace)


def _write_markdown(path: Path, report: dict) -> None:
    script = report["transliteration"]
    translation = report["translation"]
    lines = [
        "# Saylacian local research run",
        "",
        f"- Run: `{report['run_id']}`",
        f"- Status: **{report['status']}**",
        (
            f"- Script checks: {script.get('executed_checks', 0)} executed; "
            f"{script.get('passed_checks', 0)} passed; "
            f"{script.get('failed_checks', 0)} failed."
        ),
        (
            f"- Reference-scored translations: "
            f"{translation.get('reference_scored_translations', 0)}; "
            "human-reviewed: 0."
        ),
        (
            "- Training: "
            + report["training"]["status"]
            + " — "
            + report["training"]["reason"]
        ),
        "- Promotion: disabled; no production model or app file was changed.",
        (
            "- Dataset acquisition and preparation use only sources explicitly "
            "approved in the private workspace config."
        ),
        "",
        "## Transliteration checks",
        "",
        (
            "These test determinism, preservation, table integrity and converter "
            "invariants. They are not translation-quality or word-orthography "
            "judgments."
        ),
        "",
        "## Translation baseline",
        "",
    ]
    if translation.get("status") != "PASS":
        lines.append(
            f"Baseline status: {translation.get('status')} — "
            f"{translation.get('reason', 'no detail')}"
        )
    else:
        lines.extend(
            [
                (
                    f"Evaluation-only sample: {translation['dataset']}, "
                    f"{translation['domain']}, "
                    f"N={translation['sample_size_per_direction']} per direction."
                ),
                "",
                "| Route | N | BLEU | chrF++ |",
                "|---|---:|---:|---:|",
            ]
        )
        for route, metrics in translation["directions"].items():
            lines.append(
                f"| {route} | {metrics['n']} | {metrics['bleu']:.4f} | "
                f"{metrics['chrf_plus_plus']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            *[f"- {item}" for item in translation.get("limitations", [])],
            "",
        ]
    )
    prepared = report.get("model_evaluation", {})
    lines.extend(
        [
            "## Prepared corpus evaluation",
            "",
            (
                f"Status: {prepared.get('status', 'SKIPPED')} — "
                f"{prepared.get('reference_scored_translations', 0)} "
                "reference-scored offline translations; no human review."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def current_status(workspace: Path) -> dict:
    import sqlite3

    from .state import _process_is_running

    overnight = read_json(workspace / "locks" / "active_run.json")
    script_runs = []
    for database in (workspace / "runs").glob("*/run_state.sqlite"):
        try:
            with sqlite3.connect(database) as connection:
                run = connection.execute(
                    "SELECT run_id,seed,target,status,created FROM runs "
                    "ORDER BY created DESC LIMIT 1"
                ).fetchone()
                if run is None:
                    continue
                status = run[3]
                lock = database.with_name("active.lock")
                if status == "RUNNING":
                    try:
                        lock_state = read_json(lock) if lock.exists() else None
                    except (OSError, ValueError):
                        lock_state = None
                    if not lock_state or not _process_is_running(lock_state.get("pid")):
                        status = "INTERRUPTED"
                completed, passed, failed, unique_inputs = connection.execute(
                    "SELECT COUNT(*),SUM(status='PASS'),SUM(status='FAIL'),"
                    "COUNT(DISTINCT input_hash) FROM cases WHERE run_id=?",
                    (run[0],),
                ).fetchone()
                attempts_table = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='attempts'"
                ).fetchone()
                retried = 0
                attempts = completed
                if attempts_table:
                    attempts, retried = connection.execute(
                        "SELECT COUNT(*),SUM(attempt_no>1) FROM attempts "
                        "WHERE run_id=?",
                        (run[0],),
                    ).fetchone()
                script_runs.append(
                    {
                        "run_id": run[0],
                        "seed": run[1],
                        "target": run[2],
                        "status": status,
                        "created_epoch": run[4],
                        "completed": completed,
                        "attempted": attempts or 0,
                        "retried": retried or 0,
                        "passed": passed or 0,
                        "failed": failed or 0,
                        "unique_case_ids": completed,
                        "unique_inputs": unique_inputs or 0,
                        "database": str(database),
                    }
                )
        except sqlite3.Error:
            continue
    script_runs.sort(key=lambda item: item["created_epoch"], reverse=True)
    active_script = next(
        (
            run
            for run in script_runs
            if run["status"] in {"RUNNING", "PAUSED", "INTERRUPTED"}
        ),
        None,
    )
    overnight_status = overnight.get("status") if overnight else None
    if overnight_status == "RUNNING" and not _process_is_running(overnight.get("pid")):
        overnight_status = "INTERRUPTED"
    overnight_summary = None
    if overnight:
        overnight_summary = {
            "run_id": overnight.get("run_id"),
            "status": overnight_status,
            "stage": overnight.get("stage"),
            "updated_utc": overnight.get("updated_utc"),
            "revision": overnight.get("revision"),
            "completed_steps": sorted(overnight.get("completed_steps", {})),
            "last_safe_checkpoint": overnight.get("last_safe_checkpoint"),
            "counts": overnight.get("counts", {}),
        }
    if overnight_status in {"RUNNING", "PAUSED", "INTERRUPTED"}:
        status = overnight_status
    elif active_script:
        status = active_script["status"]
    elif script_runs:
        status = script_runs[0]["status"]
    else:
        status = overnight_status or "NO_RUN"
    return {
        "status": status,
        "overnight": overnight_summary,
        "active_transliteration_run": active_script,
        "latest_transliteration_run": script_runs[0] if script_runs else None,
        "recent_transliteration_runs": script_runs[:10],
    }
