# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validated, conservative settings for the local research runner."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LabConfig:
    version: int = 1
    max_runtime_hours: float = 8.0
    script_checks: int = 1_000_000
    translation_samples: int = 20
    max_cpu_threads: int = 2
    max_disk_gib: float = 20.0
    max_vram_gib: float = 5.3
    gpu_max_temp_c: float = 82.0
    min_free_vram_gib: float = 3.0
    keep_free_disk_gib: float = 15.0
    max_download_gib: float = 6.0
    max_single_download_gib: float = 2.0
    allowed_download_hosts: tuple[str, ...] = (
        "huggingface.co",
        "cdn-lfs.huggingface.co",
        "us.aws.cdn.hf.co",
        "raw.githubusercontent.com",
        "github.com",
        "opus.nlpl.eu",
        "object.pouta.csc.fi",
    )
    approved_source_ids: tuple[str, ...] = ()
    training_enabled: bool = False
    allow_noncommercial_training: bool = False
    automatic_promotion: bool = False

    def validate(self) -> LabConfig:
        if self.version != 1:
            raise ValueError("Unsupported research configuration version.")
        if not 0 < self.max_runtime_hours <= 24:
            raise ValueError("max_runtime_hours must be between 0 and 24.")
        if not 0 <= self.script_checks <= 1_000_000:
            raise ValueError("script_checks must be between 0 and 1,000,000.")
        if not 0 <= self.translation_samples <= 2_500:
            raise ValueError("translation_samples must be between 0 and 2,500.")
        if not 1 <= self.max_cpu_threads <= 8:
            raise ValueError("max_cpu_threads must be between 1 and 8.")
        if self.max_disk_gib <= 0 or self.keep_free_disk_gib < 0:
            raise ValueError("Disk budgets must be positive and keep-free nonnegative.")
        if not 0 < self.max_vram_gib <= 128:
            raise ValueError("max_vram_gib must be greater than zero and at most 128.")
        if not 40 <= self.gpu_max_temp_c <= 100:
            raise ValueError("gpu_max_temp_c must be between 40 and 100.")
        if not 0 <= self.min_free_vram_gib <= 128:
            raise ValueError("min_free_vram_gib must be between zero and 128.")
        if self.max_download_gib < 0:
            raise ValueError("max_download_gib cannot be negative.")
        if self.max_single_download_gib <= 0:
            raise ValueError("max_single_download_gib must be positive.")
        if self.max_single_download_gib > self.max_download_gib:
            raise ValueError(
                "Single-download budget cannot exceed total download budget."
            )
        if not self.allowed_download_hosts or any(
            not host or "/" in host or ":" in host or host != host.lower()
            for host in self.allowed_download_hosts
        ):
            raise ValueError(
                "Download allowlist must contain exact lowercase DNS host names."
            )
        if self.training_enabled and not self.approved_source_ids:
            raise ValueError("Training requires explicitly approved source IDs.")
        if self.automatic_promotion:
            raise ValueError("Automatic promotion is prohibited.")
        if len(set(self.approved_source_ids)) != len(self.approved_source_ids):
            raise ValueError("approved_source_ids must not contain duplicates.")
        return self


def load_config(path: Path) -> LabConfig:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    allowed = {
        "version",
        "max_runtime_hours",
        "script_checks",
        "translation_samples",
        "max_cpu_threads",
        "max_disk_gib",
        "max_vram_gib",
        "gpu_max_temp_c",
        "min_free_vram_gib",
        "keep_free_disk_gib",
        "max_download_gib",
        "max_single_download_gib",
        "allowed_download_hosts",
        "approved_source_ids",
        "training_enabled",
        "allow_noncommercial_training",
        "automatic_promotion",
    }
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"Unknown configuration keys: {', '.join(sorted(unknown))}")
    try:
        config = LabConfig(
            **{
                **data,
                "approved_source_ids": tuple(data.get("approved_source_ids", ())),
                "allowed_download_hosts": tuple(
                    data.get(
                        "allowed_download_hosts",
                        LabConfig.allowed_download_hosts,
                    )
                ),
            }
        )
    except TypeError as error:
        raise ValueError(f"Invalid configuration fields: {error}") from error
    return config.validate()


def config_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
