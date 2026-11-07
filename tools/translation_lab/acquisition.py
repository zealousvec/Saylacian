# SPDX-License-Identifier: AGPL-3.0-or-later
"""Acquire only sources explicitly approved in the user's private workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

from .config import LabConfig
from .downloader import DownloadSpec
from .downloader import download_approved
from .sources import read_owner_registry


def acquire_approved_sources(workspace: Path, config: LabConfig) -> dict:
    registry = read_owner_registry(workspace / "registry/sources.jsonl")
    approved_ids = set(config.approved_source_ids)
    sources = [
        source
        for source in registry
        if source.get("source_id") in approved_ids
        and source.get("owner_approved") is True
    ]
    artifacts = [
        (source, artifact)
        for source in sources
        for artifact in source.get("artifacts", [])
    ]
    if not artifacts:
        return {
            "status": "SKIPPED",
            "reason": "No pinned artifacts have explicit local owner approval.",
            "downloaded": [],
        }
    total_bytes = sum(artifact.get("expected_bytes", -1) for _, artifact in artifacts)
    if total_bytes <= 0 or total_bytes > config.max_download_gib * 1024**3:
        raise ValueError("Selected downloads exceed the configured total byte budget.")
    if any(
        artifact.get("expected_bytes", -1) > config.max_single_download_gib * 1024**3
        for _, artifact in artifacts
    ):
        raise ValueError("An artifact exceeds the configured single-file size budget.")
    disk = shutil.disk_usage(workspace)
    minimum_free = config.keep_free_disk_gib * 1024**3
    if disk.free - total_bytes < minimum_free:
        raise ValueError("Download would use the configured keep-free disk reserve.")

    downloaded = []
    for source, artifact in artifacts:
        spec = DownloadSpec(
            source=source,
            url=artifact["url"],
            sha256=artifact["sha256"],
            expected_bytes=artifact["expected_bytes"],
            purpose=artifact.get("purpose", "train"),
        )
        path = download_approved(
            spec,
            workspace / "cache/downloads",
            set(config.allowed_download_hosts),
            approved_ids,
            max_bytes=int(config.max_single_download_gib * 1024**3),
            allow_noncommercial=config.allow_noncommercial_training,
        )
        downloaded.append(
            {
                "source_id": source["source_id"],
                "revision": source.get("revision"),
                "purpose": spec.purpose,
                "bytes": path.stat().st_size,
                "sha256": spec.sha256.lower(),
                "cache_path": str(path),
            }
        )
    return {"status": "PASS", "downloaded": downloaded}
