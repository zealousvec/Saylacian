# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep generated benchmark predictions in private local app data."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def benchmark_data_directory() -> Path:
    """Return the user's local application-data folder for private results."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "Saylacian" / "benchmark"


def new_benchmark_output(name: str) -> Path:
    """Create a unique default path so new runs never overwrite prior results."""
    return benchmark_data_directory() / f"{name}-{uuid.uuid4().hex}.json"


def checkpoint_for(output_path: Path, name: str = "checkpoint") -> Path:
    """Choose a stable, non-identifying checkpoint path for one output file."""
    resolved = Path(output_path).expanduser().resolve()
    digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:24]
    return benchmark_data_directory() / f"{name}-{digest}.json"


def require_external_output(path: Path) -> Path:
    """Reject paths inside the source tree, including paths through symlinks."""
    resolved = Path(path).expanduser().resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    raise ValueError("Benchmark results must be saved outside the source repository.")


def save_json_atomic(path: Path, result: dict) -> None:
    """Write JSON atomically outside the source tree without partial results."""
    destination = require_external_output(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f"{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(result, temporary_file, ensure_ascii=False, indent=2)
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
