from __future__ import annotations

import subprocess

import pytest

from tools.translation_lab import resources


def test_gpu_preflight_reports_metrics_and_cap(monkeypatch):
    monkeypatch.setattr(
        resources.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="8151, 7000, 61, 22\n", stderr=""
        ),
    )
    result = resources.gpu_preflight(
        max_vram_gib=5.0, max_temperature_c=82, minimum_free_gib=3
    )
    assert result["gpu_temperature_c"] == 61
    assert result["gpu_free_mib"] == 7000
    assert result["max_process_fraction"] < 0.65


def test_gpu_preflight_blocks_hot_gpu_and_missing_telemetry(monkeypatch):
    monkeypatch.setattr(
        resources.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="8151, 7000, 82, 22\n", stderr=""
        ),
    )
    with pytest.raises(RuntimeError, match="temperature"):
        resources.gpu_preflight(
            max_vram_gib=5.0, max_temperature_c=82, minimum_free_gib=3
        )
    monkeypatch.setattr(
        resources.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    with pytest.raises(RuntimeError, match="telemetry is unavailable"):
        resources.gpu_preflight(
            max_vram_gib=5.0, max_temperature_c=82, minimum_free_gib=3
        )


def test_gpu_temperature_reader_returns_single_value_and_fails_closed(monkeypatch):
    monkeypatch.setattr(
        resources.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="51\n", stderr=""
        ),
    )
    assert resources.gpu_temperature_c() == 51
    monkeypatch.setattr(
        resources.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    with pytest.raises(RuntimeError, match="telemetry is unavailable"):
        resources.gpu_temperature_c()


def test_workspace_disk_budget_includes_existing_files(tmp_path):
    (tmp_path / "blob.bin").write_bytes(b"x" * 100)
    result = resources.assert_workspace_disk_budget(
        tmp_path, additional_bytes=50, maximum_gib=1
    )
    assert result["workspace_used_bytes"] == 100
    with pytest.raises(RuntimeError, match="budget would be exceeded"):
        resources.assert_workspace_disk_budget(
            tmp_path, additional_bytes=1024, maximum_gib=1 / 1024**3
        )
