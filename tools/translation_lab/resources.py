# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only hardware and disk guards for explicit research operations."""

from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path


def gpu_preflight(
    *, max_vram_gib: float, max_temperature_c: float, minimum_free_gib: float
) -> dict:
    if (
        not all(
            math.isfinite(value)
            for value in (max_vram_gib, max_temperature_c, minimum_free_gib)
        )
        or max_vram_gib <= 0
        or max_temperature_c <= 0
        or minimum_free_gib < 0
    ):
        raise ValueError(
            "GPU budgets must be finite and positive; free reserve may be zero"
        )
    command = [
        "nvidia-smi",
        "--query-gpu=memory.total,memory.free,temperature.gpu,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=4, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(
            "GPU telemetry is unavailable; model work was not started."
        ) from error
    if result.returncode or not result.stdout.strip():
        raise RuntimeError(
            "nvidia-smi could not report GPU state; model work was not started."
        )
    try:
        total_mib, free_mib, temperature_c, utilization = (
            int(value.strip()) for value in result.stdout.splitlines()[0].split(",")
        )
    except (ValueError, IndexError) as error:
        raise RuntimeError(
            "GPU telemetry was incomplete; model work was not started."
        ) from error
    total_gib = total_mib / 1024
    free_gib = free_mib / 1024
    if temperature_c >= max_temperature_c:
        raise RuntimeError(
            f"GPU temperature {temperature_c}°C is at/above the configured "
            f"{max_temperature_c}°C stop; model work was not started."
        )
    if free_gib < minimum_free_gib:
        raise RuntimeError(
            f"GPU has {free_gib:.2f} GiB free; at least {minimum_free_gib:.2f} "
            "GiB is required. Close/stop other applications yourself or retry later."
        )
    return {
        "gpu_total_mib": total_mib,
        "gpu_free_mib": free_mib,
        "gpu_temperature_c": temperature_c,
        "gpu_utilization_percent": utilization,
        "max_vram_gib": min(max_vram_gib, total_gib),
        "max_process_fraction": min(1.0, max_vram_gib / total_gib),
        "max_temperature_c": max_temperature_c,
        "minimum_free_gib": minimum_free_gib,
    }


def gpu_temperature_c() -> int:
    """Return current NVIDIA GPU temperature or fail closed if unavailable."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("nvidia-smi could not read GPU temperature")
        temperature = int(result.stdout.splitlines()[0].strip())
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as error:
        raise RuntimeError("GPU temperature telemetry is unavailable") from error
    if not 0 <= temperature <= 130:
        raise RuntimeError("GPU temperature telemetry returned an invalid value")
    return temperature


def directory_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _directories, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError as error:
                raise RuntimeError(
                    f"Cannot measure workspace file {Path(root) / name}; "
                    "disk guard stopped."
                ) from error
    return total


def assert_workspace_disk_budget(
    workspace: Path, *, additional_bytes: int, maximum_gib: float
) -> dict:
    used = directory_size_bytes(workspace)
    projected = used + additional_bytes
    maximum = int(maximum_gib * 1024**3)
    if maximum_gib <= 0 or additional_bytes < 0:
        raise ValueError("Disk budgets must be positive")
    if projected > maximum:
        raise RuntimeError(
            f"Workspace disk budget would be exceeded: {projected / 1024**3:.2f} "
            f"GiB projected above {maximum_gib:.2f} GiB."
        )
    return {
        "workspace_used_bytes": used,
        "projected_workspace_bytes": projected,
        "maximum_workspace_gib": maximum_gib,
        "disk_free_gib": round(shutil.disk_usage(workspace).free / 1024**3, 2),
    }
