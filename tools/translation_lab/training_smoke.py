# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tiny deterministic gradient-training smoke with an external JSON checkpoint."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .independent_runner import _validate_run_id
from .state import atomic_json


def _loss(
    weight: float, bias: float, examples: tuple[tuple[float, float], ...]
) -> float:
    return sum((weight * x + bias - y) ** 2 for x, y in examples) / len(examples)


def run_training_smoke(
    workspace: Path,
    *,
    run_id: str = "training-smoke",
    steps: int = 40,
    resume: bool = False,
    stop_after: int | None = None,
) -> dict:
    if steps < 1 or (stop_after is not None and stop_after < 1):
        raise ValueError("steps and stop_after must be positive")
    _validate_run_id(run_id)
    path = Path(workspace) / "runs" / run_id / "training-smoke.json"
    # Synthetic, locally generated data: y = 2x + 1. Final points are held out.
    train = tuple((x / 10, 2 * (x / 10) + 1) for x in range(-8, 9, 2))
    heldout = ((-0.9, -0.8), (-0.3, 0.4), (0.4, 1.8), (0.9, 2.8))
    dataset_hash = hashlib.sha256(repr((train, heldout)).encode()).hexdigest()
    if path.exists():
        if not resume:
            raise FileExistsError(f"Training smoke {run_id} exists; use --resume")
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["dataset_sha256"] != dataset_hash or state["target_steps"] != steps:
            raise ValueError("Training smoke checkpoint does not match this run")
        weight, bias, completed = (
            state["weight"],
            state["bias"],
            state["completed_steps"],
        )
    else:
        if resume:
            raise FileNotFoundError(f"No training smoke checkpoint for {run_id}")
        weight, bias, completed = 0.0, 0.0, 0
    initial = (0.0, 0.0)
    started = time.perf_counter()
    while completed < steps:
        grad_w = sum(2 * x * (weight * x + bias - y) for x, y in train) / len(train)
        grad_b = sum(2 * (weight * x + bias - y) for x, y in train) / len(train)
        weight -= 0.08 * grad_w
        bias -= 0.08 * grad_b
        completed += 1
        state = {
            "schema_version": 1,
            "run_id": run_id,
            "dataset_sha256": dataset_hash,
            "target_steps": steps,
            "completed_steps": completed,
            "weight": weight,
            "bias": bias,
            "train_loss": _loss(weight, bias, train),
            "updated_utc": time.time(),
        }
        atomic_json(path, state)
        if stop_after is not None and completed >= stop_after:
            return {**state, "status": "INTERRUPTED", "checkpoint": str(path)}
    return {
        **state,
        "status": "COMPLETED",
        "initial_parameters": {"weight": initial[0], "bias": initial[1]},
        "parameters_changed": (weight, bias) != initial,
        "heldout_examples": len(heldout),
        "heldout_mse": _loss(weight, bias, heldout),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "checkpoint": str(path),
        "dataset": "locally generated synthetic linear regression; no external rights",
    }
