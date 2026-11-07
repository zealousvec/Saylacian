# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run a small, resumable M2M100 pilot search and one gated full candidate."""

from __future__ import annotations

import gc
import json
import math
import re
import subprocess
import sys
import time
from datetime import UTC
from datetime import datetime
from pathlib import Path

from tools.translation_lab.config import LabConfig
from tools.translation_lab.state import atomic_json

PILOT_LEARNING_RATES = (5e-5, 1e-4, 2e-4)
DEFAULT_PILOT_STEPS = 250
MAX_PILOT_STEPS = 2_000
FULL_RUN_MARGIN = 1.2
TICO_EVALUATION_RESERVE_HOURS = 1.5


def _validate_campaign_id(campaign_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", campaign_id):
        raise ValueError("Campaign ID must be a path-safe name of at most 80 chars.")


def _rate_id(rate: float) -> str:
    return f"{rate:.0e}".replace("+", "")


def _can_resume_experiment(workspace: Path, experiment_id: str, resume: bool) -> bool:
    """Resume only when the trainer's immutable experiment metadata exists."""
    return (
        resume
        and (workspace / "experiments" / experiment_id / "experiment.json").is_file()
    )


def _release_cuda_cache() -> None:
    """Synchronize and release cached allocations between sequential runs."""
    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()


def _train_isolated(
    workspace: Path,
    *,
    model_dir: Path,
    experiment_id: str,
    resume: bool,
    learning_rate: float,
    max_steps: int | None,
    max_gpu_fraction: float,
    max_vram_gib: float,
    max_temperature_c: float,
) -> dict:
    """Run one trainer in a child process so CUDA memory is fully released."""
    repository = Path(__file__).resolve().parents[1].parent
    config_path = workspace / "config" / "active.toml"
    if not config_path.is_file():
        config_path = repository / "research" / "translation_lab.example.toml"
    command = [
        sys.executable,
        str(repository / "tools" / "local_translation_lab.py"),
        "--workspace",
        str(workspace),
        "train",
        "--config",
        str(config_path),
        "--execute",
        "--experiment-id",
        experiment_id,
        "--dataset-id",
        "marian-mixture",
        "--model-dir",
        str(model_dir),
        "--max-gpu-fraction",
        str(max_gpu_fraction),
        "--max-vram-gb",
        str(max_vram_gib),
        "--gpu-max-temp-c",
        str(max_temperature_c),
        "--learning-rate",
        str(learning_rate),
        "--num-train-epochs",
        "1",
        "--lora-rank",
        "8",
    ]
    if max_steps is not None:
        command.extend(("--max-steps", str(max_steps)))
    if resume:
        command.append("--resume")
    completed = subprocess.run(command, cwd=repository, check=False)
    report = _load_report(workspace, experiment_id)
    if completed.returncode != 0 or report is None:
        failure_path = (
            workspace / "experiments" / experiment_id / "training-failure.json"
        )
        detail = (
            failure_path.read_text(encoding="utf-8")[:1_000]
            if failure_path.is_file()
            else f"trainer exit code {completed.returncode}; report not found"
        )
        raise RuntimeError(f"Isolated training process failed: {detail}")
    return report


def _evaluate_isolated(
    workspace: Path,
    *,
    model_dir: Path,
    experiment_id: str,
    archive_path: Path,
    output_path: Path,
) -> dict:
    """Evaluate one adapter in a child process and always release its GPU state."""
    repository = Path(__file__).resolve().parents[1].parent
    command = [
        sys.executable,
        "-m",
        "tools.translation_lab.m2m100_tico19",
        "--workspace",
        str(workspace),
        "--archive",
        str(archive_path),
        "--model-dir",
        str(model_dir),
        "--experiment-id",
        experiment_id,
        "--output",
        str(output_path),
    ]
    completed = subprocess.run(command, cwd=repository, check=False)
    if completed.returncode != 0 or not output_path.is_file():
        raise RuntimeError(
            f"Isolated TICO-19 dev evaluation failed for {experiment_id} "
            f"(exit code {completed.returncode})."
        )
    return json.loads(output_path.read_text(encoding="utf-8"))


def _campaign_fingerprint(workspace: Path, config: LabConfig, model_dir: Path) -> dict:
    from tools.translation_lab.m2m100_training import MODEL_ID
    from tools.translation_lab.m2m100_training import MODEL_REVISION
    from tools.translation_lab.m2m100_training import _prepared_data

    manifest, train_rows, validation_rows = _prepared_data(
        workspace, config, dataset_id="marian-mixture"
    )
    return {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "model_dir": str(model_dir.resolve()),
        "dataset_revision": manifest["dataset_revision"],
        "train_sha256": manifest["split_sha256"]["train.jsonl"],
        "validation_sha256": manifest["split_sha256"]["validation.jsonl"],
        "training_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "approved_source_ids": sorted(config.approved_source_ids),
    }


def _load_report(workspace: Path, experiment_id: str) -> dict | None:
    path = workspace / "experiments" / experiment_id / "training-report.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _estimated_full_hours(workspace: Path) -> float:
    report = _load_report(workspace, "m2m100-mixture-1x-20261101")
    if report and isinstance(report.get("elapsed_seconds"), (int, float)):
        return max(1.0, report["elapsed_seconds"] / 3600 * FULL_RUN_MARGIN)
    return 4.0


def _evaluate_improvement(report: dict) -> tuple[bool, dict]:
    """Require non-regressing direction scores and positive paired chrF CI."""
    routes = report.get("metrics", {})
    decisions = {}
    for route in ("en-so", "so-en"):
        result = routes.get(route, {})
        delta = result.get("delta", {})
        paired = result.get("paired_sentence_chrf", {})
        interval = paired.get("mean_delta_bootstrap_95_ci", [])
        passes = (
            len(interval) == 2
            and interval[0] > 0
            and delta.get("chrf_plus_plus", 0) > 0
            and delta.get("bleu", -math.inf) >= 0
        )
        decisions[route] = {
            "passes": passes,
            "bleu_delta": delta.get("bleu"),
            "chrf_plus_plus_delta": delta.get("chrf_plus_plus"),
            "paired_chrf_95_ci": interval,
        }
    return all(item["passes"] for item in decisions.values()), decisions


def _find_tico_archive(workspace: Path) -> Path:
    candidates = (
        workspace / "cache" / "data" / "tico19" / "tico19-testset-2021-02-26.zip",
        workspace / "candidates" / "tico19-testset-official.zip",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Pinned TICO-19 archive is missing from the private cache.")


def run_campaign(
    workspace: Path,
    config: LabConfig,
    *,
    campaign_id: str,
    model_dir: Path,
    pilot_steps: int = DEFAULT_PILOT_STEPS,
    max_hours: float = 8.0,
    resume: bool = False,
    dry_run: bool = False,
    max_vram_gib: float = 5.3,
    max_temperature_c: float = 82.0,
) -> dict:
    """Pilot three rates, fully train the validation winner, and gate on dev."""
    _validate_campaign_id(campaign_id)
    if not 50 <= pilot_steps <= MAX_PILOT_STEPS:
        raise ValueError(f"pilot_steps must be between 50 and {MAX_PILOT_STEPS}.")
    if not math.isfinite(max_hours) or not 0 < max_hours <= config.max_runtime_hours:
        raise ValueError("max_hours must be positive and within the configured limit.")
    if not math.isfinite(max_vram_gib) or max_vram_gib <= 0:
        raise ValueError("max_vram_gib must be finite and positive.")
    if not math.isfinite(max_temperature_c) or max_temperature_c <= 0:
        raise ValueError("max_temperature_c must be finite and positive.")
    if not config.training_enabled:
        raise PermissionError("Training is disabled in the active lab config.")

    plan = {
        "campaign_id": campaign_id,
        "dataset_id": "marian-mixture",
        "pilot_steps_per_rate": pilot_steps,
        "pilot_learning_rates": list(PILOT_LEARNING_RATES),
        "full_candidate_epochs": 1,
        "max_hours": max_hours,
        "max_hours_scope": (
            "per foreground invocation; resume receives a fresh bounded window"
        ),
        "independent_evaluation": (
            "compare all pilots and the full candidate to the base model on "
            "the pinned TICO-19 development split"
        ),
        "acceptance": (
            "Both directions must have positive chrF++ deltas, nonnegative BLEU "
            "deltas, and positive paired chrF++ 95% confidence lower bounds."
        ),
        "automatic_promotion": False,
    }
    if dry_run:
        return {"status": "DRY_RUN", "plan": plan}

    fingerprint = _campaign_fingerprint(workspace, config, model_dir)
    campaign_dir = workspace / "campaigns" / campaign_id
    state_path = campaign_dir / "campaign.json"
    if state_path.exists():
        if not resume:
            raise FileExistsError("Campaign already exists; use --resume or a new ID.")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if (
            state.get("fingerprint") != fingerprint
            or state.get("pilot_steps") != pilot_steps
        ):
            raise ValueError("Campaign inputs changed; use a new campaign ID.")
        state["max_hours"] = max_hours
        state["plan"] = plan
    else:
        if resume:
            raise FileNotFoundError("No campaign exists to resume.")
        campaign_dir.mkdir(parents=True, exist_ok=False)
        state = {
            "schema_version": 1,
            "campaign_id": campaign_id,
            "status": "RUNNING",
            "created_utc": datetime.now(UTC).isoformat(),
            "started_epoch": time.time(),
            "max_hours": max_hours,
            "pilot_steps": pilot_steps,
            "fingerprint": fingerprint,
            "plan": plan,
            "pilots": {},
            "pilot_evaluations": {},
            "winner_learning_rate": None,
            "full_experiment_id": None,
            "evaluation_report": None,
            "acceptance": None,
        }

    atomic_json(state_path, state)
    state.setdefault("pilot_evaluations", {})
    invocation_started = time.monotonic()

    def elapsed_hours() -> float:
        return (time.monotonic() - invocation_started) / 3600

    for rate in PILOT_LEARNING_RATES:
        key = _rate_id(rate)
        previous = state["pilots"].get(key, {})
        experiment_id = f"{campaign_id}-pilot-{key}"
        if previous.get("status") == "COMPLETED":
            continue
        if elapsed_hours() >= max_hours:
            state["status"] = "PAUSED_BUDGET"
            atomic_json(state_path, state)
            return state
        state["status"] = "RUNNING_PILOTS"
        state["pilots"][key] = {"status": "RUNNING", "experiment_id": experiment_id}
        atomic_json(state_path, state)
        result = _load_report(workspace, experiment_id)
        if result and result.get("status") == "PAUSED_RESOURCE":
            result = None
        if result is None:
            from tools.translation_lab.resources import gpu_preflight

            _release_cuda_cache()
            gpu = gpu_preflight(
                max_vram_gib=max_vram_gib,
                max_temperature_c=max_temperature_c,
                minimum_free_gib=config.min_free_vram_gib,
            )
            result = _train_isolated(
                workspace,
                model_dir=model_dir,
                experiment_id=experiment_id,
                resume=(
                    _can_resume_experiment(workspace, experiment_id, resume)
                    and previous.get("status") in {"RUNNING", "PAUSED_RESOURCE"}
                ),
                max_gpu_fraction=min(0.65, gpu["max_process_fraction"]),
                learning_rate=rate,
                max_steps=pilot_steps,
                max_vram_gib=max_vram_gib,
                max_temperature_c=max_temperature_c,
            )
        if result.get("status") == "PAUSED_RESOURCE":
            state["pilots"][key] = {
                "status": "PAUSED_RESOURCE",
                "experiment_id": experiment_id,
                "resource_stop_reason": result.get("resource_stop_reason"),
                "completed_steps": result.get("completed_steps"),
                "planned_steps": result.get("planned_steps"),
            }
            state["status"] = "PAUSED_RESOURCE"
            atomic_json(state_path, state)
            return state
        state["pilots"][key] = {
            "status": "COMPLETED",
            "experiment_id": experiment_id,
            "validation_loss": result.get("validation_loss"),
            "completed_steps": result.get("completed_steps"),
            "planned_steps": result.get("planned_steps"),
            "elapsed_seconds": result.get("elapsed_seconds"),
        }
        atomic_json(state_path, state)

    # Compare every trained pilot to the frozen base model on the same pinned
    # dev split. These diagnostics never alter the learning-rate winner.
    pilot_archive = _find_tico_archive(workspace)
    for rate in PILOT_LEARNING_RATES:
        key = _rate_id(rate)
        pilot = state["pilots"].get(key, {})
        if pilot.get("status") != "COMPLETED":
            continue
        existing = state["pilot_evaluations"].get(key, {})
        report_path = (
            workspace / "reports" / f"{campaign_id}-pilot-{key}-tico19-dev.json"
        )
        report_path_value = existing.get("report_path")
        if report_path_value and Path(report_path_value).is_file():
            evaluation = json.loads(Path(report_path_value).read_text(encoding="utf-8"))
        elif report_path.is_file():
            evaluation = json.loads(report_path.read_text(encoding="utf-8"))
        else:
            if elapsed_hours() >= max_hours:
                state["status"] = "PAUSED_BUDGET"
                atomic_json(state_path, state)
                return state
            state["status"] = "RUNNING_PILOT_DEV_EVALUATIONS"
            atomic_json(state_path, state)
            from tools.translation_lab.resources import gpu_preflight

            _release_cuda_cache()
            gpu_preflight(
                max_vram_gib=max_vram_gib,
                max_temperature_c=max_temperature_c,
                minimum_free_gib=config.min_free_vram_gib,
            )
            evaluation = _evaluate_isolated(
                workspace,
                model_dir=model_dir,
                experiment_id=pilot["experiment_id"],
                archive_path=pilot_archive,
                output_path=report_path,
            )
        improved, gate = _evaluate_improvement(evaluation)
        state["pilot_evaluations"][key] = {
            "experiment_id": pilot["experiment_id"],
            "report_path": str(report_path),
            "passes_improvement_gate": improved,
            "acceptance": gate,
        }
        atomic_json(state_path, state)

    eligible = [
        (float(item["validation_loss"]), key)
        for key, item in state["pilots"].items()
        if item.get("status") == "COMPLETED"
        and isinstance(item.get("validation_loss"), (int, float))
        and math.isfinite(item["validation_loss"])
    ]
    if len(eligible) != len(PILOT_LEARNING_RATES):
        state["status"] = "FAILED_NO_VALID_PILOT_METRICS"
        atomic_json(state_path, state)
        raise RuntimeError("Pilot run did not produce all required validation losses.")
    _, winning_key = min(eligible)
    winning_rate = next(
        rate for rate in PILOT_LEARNING_RATES if _rate_id(rate) == winning_key
    )
    state["winner_learning_rate"] = winning_rate
    full_id = f"{campaign_id}-full-{winning_key}"
    state["full_experiment_id"] = full_id

    full_report = _load_report(workspace, full_id)
    if full_report and full_report.get("status") == "PAUSED_RESOURCE":
        full_report = None
    evaluation_path = workspace / "reports" / f"{campaign_id}-tico19-dev.json"
    needs_final_evaluation = not evaluation_path.is_file()
    estimated_remaining = (
        _estimated_full_hours(workspace) if full_report is None else 0
    ) + (TICO_EVALUATION_RESERVE_HOURS if needs_final_evaluation else 0)
    if max_hours - elapsed_hours() < estimated_remaining:
        state["status"] = "PAUSED_BUDGET"
        state["estimated_hours_needed_for_full_and_evaluation"] = round(
            estimated_remaining, 2
        )
        atomic_json(state_path, state)
        return state

    if full_report is None:
        state["status"] = "RUNNING_FULL_TRAINING"
        atomic_json(state_path, state)
        from tools.translation_lab.resources import gpu_preflight

        _release_cuda_cache()
        gpu = gpu_preflight(
            max_vram_gib=max_vram_gib,
            max_temperature_c=max_temperature_c,
            minimum_free_gib=config.min_free_vram_gib,
        )
        full_report = _train_isolated(
            workspace,
            model_dir=model_dir,
            experiment_id=full_id,
            resume=_can_resume_experiment(workspace, full_id, resume),
            max_gpu_fraction=min(0.65, gpu["max_process_fraction"]),
            learning_rate=winning_rate,
            max_steps=None,
            max_vram_gib=max_vram_gib,
            max_temperature_c=max_temperature_c,
        )
    if full_report.get("status") == "PAUSED_RESOURCE":
        state["status"] = "PAUSED_RESOURCE"
        state["resource_stop_reason"] = full_report.get("resource_stop_reason")
        atomic_json(state_path, state)
        return state

    existing_evaluation = state.get("evaluation_report")
    if evaluation_path.is_file():
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        state["evaluation_report"] = str(evaluation_path)
    elif existing_evaluation and Path(existing_evaluation).is_file():
        evaluation = json.loads(Path(existing_evaluation).read_text(encoding="utf-8"))
    else:
        state["status"] = "RUNNING_INDEPENDENT_DEV_EVALUATION"
        atomic_json(state_path, state)
        from tools.translation_lab.resources import gpu_preflight

        _release_cuda_cache()
        gpu_preflight(
            max_vram_gib=max_vram_gib,
            max_temperature_c=max_temperature_c,
            minimum_free_gib=config.min_free_vram_gib,
        )
        evaluation = _evaluate_isolated(
            workspace,
            model_dir=model_dir,
            experiment_id=full_id,
            archive_path=_find_tico_archive(workspace),
            output_path=evaluation_path,
        )
        state["evaluation_report"] = str(evaluation_path)

    improved, gate = _evaluate_improvement(evaluation)
    state["acceptance"] = gate
    state["status"] = "COMPLETED" if improved else "NO_IMPROVEMENT"
    state["best_verified_candidate"] = full_id if improved else None
    state["automatic_promotion"] = False
    state["completed_utc"] = datetime.now(UTC).isoformat()
    atomic_json(state_path, state)
    return state
