# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only inventory of host resources, installed packs and source state."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.metadata
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _memory_gib() -> dict[str, float | None]:
    if os.name == "nt":

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_phys", ctypes.c_ulonglong),
                ("avail_phys", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("avail_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("avail_virtual", ctypes.c_ulonglong),
                ("avail_extended_virtual", ctypes.c_ulonglong),
            ]

        state = MemoryStatus()
        state.length = ctypes.sizeof(state)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
            unit = 1024**3
            return {
                "total": round(state.total_phys / unit, 2),
                "available": round(state.avail_phys / unit, 2),
            }
    return {"total": None, "available": None}


def _gpu_inventory() -> dict:
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free,driver_version,utilization.gpu,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=4, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "nvidia-smi unavailable or timed out"}
    if result.returncode:
        return {"available": False, "reason": "nvidia-smi returned an error"}
    devices = []
    for line in result.stdout.splitlines():
        values = [value.strip() for value in line.split(",")]
        if len(values) != 6:
            continue
        devices.append(
            {
                "name": values[0],
                "memory_total_mib": _number(values[1]),
                "memory_free_mib": _number(values[2]),
                "driver": values[3],
                "utilization_percent": _number(values[4]),
                "temperature_c": _number(values[5]),
            }
        )
    return {"available": bool(devices), "devices": devices}


def _number(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _git_value(repository: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def _pack_inventory() -> list[dict]:
    try:
        from saylacian.core.model_packs import ModelPackManager

        packs = ModelPackManager().list_packs()
        roots = ModelPackManager().active_model_roots()
    except (ImportError, OSError, ValueError, KeyError, TypeError) as error:
        return [{"available": False, "reason": type(error).__name__}]

    active = {path.parent.name: path for path in roots}
    result = []
    for pack in packs:
        record = {
            "id": pack["id"],
            "version": pack.get("installed_version"),
            "installed": bool(pack.get("installed")),
            "damaged": bool(pack.get("damaged")),
            "bytes": pack.get("installed_bytes", 0),
            "license": pack.get("license"),
            "runtime_versions": pack.get("runtimes", {}),
            "asset_hashes": [],
        }
        path = active.get(pack["id"])
        if path and path.is_dir():
            for artifact in sorted(path.rglob("*")):
                if artifact.is_file():
                    record["asset_hashes"].append(
                        {
                            "name": artifact.relative_to(path).as_posix(),
                            "bytes": artifact.stat().st_size,
                            "sha256": _sha256(artifact),
                        }
                    )
        result.append(record)
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(repository: Path) -> dict:
    free = shutil.disk_usage(repository).free
    distributions = {}
    for name in (
        "ctranslate2",
        "sentencepiece",
        "PyYAML",
        "sacrebleu",
        "torch",
        "transformers",
        "psutil",
    ):
        try:
            distributions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            distributions[name] = None
    try:
        from saylacian.core.capabilities import CAPABILITIES

        routes = list(CAPABILITIES)
    except (ImportError, AttributeError):
        routes = []
    return {
        "schema_version": 1,
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "cpu_threads": os.cpu_count(),
        "memory_gib": _memory_gib(),
        "repository": {
            "branch": _git_value(repository, "branch", "--show-current"),
            "head": _git_value(repository, "rev-parse", "HEAD"),
            "dirty_files": (
                _git_value(repository, "status", "--porcelain") or ""
            ).splitlines(),
        },
        "disk_free_gib": round(free / 1024**3, 2),
        "gpu": _gpu_inventory(),
        "packages": distributions,
        "installed_packs": _pack_inventory(),
        "supported_capabilities": routes,
        "research_workspace_scope": "user-local, outside repository",
    }
