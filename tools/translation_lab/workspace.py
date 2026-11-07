# SPDX-License-Identifier: AGPL-3.0-or-later
"""Create a private, user-local workspace without touching existing data."""

from __future__ import annotations

import os
from pathlib import Path

WORKSPACE_DIRS = (
    "config",
    "registry",
    "cache/downloads",
    "data/raw",
    "data/staged",
    "data/train",
    "data/dev",
    "data/test",
    "data/review_queue",
    "checkpoints",
    "experiments",
    "reports",
    "proposals",
    "locks",
)


def default_workspace() -> Path:
    override = os.environ.get("SAYLACIAN_LAB_HOME")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA")
        if root:
            return Path(root) / "SaylacianResearchLab"
    return Path.home() / ".local" / "share" / "SaylacianResearchLab"


def ensure_outside_repository(workspace: Path, repository: Path) -> None:
    destination = workspace.resolve()
    source = repository.resolve()
    if destination == source or source in destination.parents:
        raise ValueError("Research workspace must be outside the repository.")


def initialize_workspace(
    workspace: Path, repository: Path, config_template: Path
) -> Path:
    ensure_outside_repository(workspace, repository)
    workspace.mkdir(parents=True, exist_ok=True)
    for name in WORKSPACE_DIRS:
        (workspace / name).mkdir(parents=True, exist_ok=True)
    active_config = workspace / "config" / "active.toml"
    if not active_config.exists():
        active_config.write_bytes(config_template.read_bytes())
    (workspace / "registry" / "sources.jsonl").touch(exist_ok=True)
    return active_config
