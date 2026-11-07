# SPDX-License-Identifier: AGPL-3.0-or-later
"""Atomic run records, cooperative pause requests and process locks."""

from __future__ import annotations

import ctypes
import json
import os
import socket
import time
import uuid
from datetime import UTC
from datetime import datetime
from pathlib import Path


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def new_run(
    config_hash: str, source_revision: str | None, effective_config: dict
) -> dict:
    return {
        "schema_version": 1,
        "run_id": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8],
        "revision": 0,
        "status": "NEW",
        "stage": "PREFLIGHT",
        "created_utc": utc_now(),
        "updated_utc": utc_now(),
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "config_sha256": config_hash,
        "effective_config": effective_config,
        "source_revision": source_revision,
        "completed_steps": {},
        "counts": {
            "generated_checks": 0,
            "executed_checks": 0,
            "reference_scored_translations": 0,
            "human_reviewed_examples": 0,
        },
        "last_safe_checkpoint": None,
        "error": None,
    }


def checkpoint(path: Path, state: dict, *, stage: str | None = None) -> None:
    state["revision"] += 1
    state["updated_utc"] = utc_now()
    state["pid"] = os.getpid()
    if stage:
        state["stage"] = stage
    state["last_safe_checkpoint"] = state["stage"]
    atomic_json(path, state)


def request_pause(workspace: Path) -> None:
    pause_file = workspace / "locks" / "pause.requested"
    pause_file.parent.mkdir(parents=True, exist_ok=True)
    pause_file.write_text(utc_now() + "\n", encoding="utf-8")


def pause_requested(workspace: Path) -> bool:
    return (workspace / "locks" / "pause.requested").exists()


def clear_pause(workspace: Path) -> None:
    (workspace / "locks" / "pause.requested").unlink(missing_ok=True)


class RunLock:
    def __init__(self, workspace: Path, *, recover_stale: bool = False):
        self.path = workspace / "locks" / "active.lock"
        self.recover_stale = recover_stale
        self.owned = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "created_utc": utc_now(),
        }
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            existing = read_json(self.path) or {}
            pid = existing.get("pid")
            if _process_is_running(pid):
                raise RuntimeError(
                    f"Research runner already holds the lock (PID {pid})."
                )
            if not self.recover_stale:
                raise RuntimeError(
                    "A stale run lock exists. Inspect it, then run "
                    "resume --recover-stale-lock."
                )
            archive = self.path.with_name(f"active.stale-{int(time.time())}.lock")
            os.replace(self.path, archive)
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        self.owned = True
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.owned:
            existing = read_json(self.path) or {}
            if existing.get("pid") == os.getpid():
                self.path.unlink(missing_ok=True)


def _process_is_running(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() == 5
        try:
            exit_code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True
