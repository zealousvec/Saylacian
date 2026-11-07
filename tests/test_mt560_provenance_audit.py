# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the text-free MT560 provenance index audit."""

from __future__ import annotations

import gzip
import hashlib
from pathlib import Path

import pytest

from tools.translation_lab.mt560_provenance_audit import audit_provenance


def _set_fixture_pins(
    monkeypatch: pytest.MonkeyPatch,
    inputs: tuple[Path, Path, Path],
) -> None:
    pins = {}
    for name, path in zip(
        ("language", "provenance", "statistics"), inputs, strict=True
    ):
        pins[name] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    monkeypatch.setattr(
        "tools.translation_lab.mt560_provenance_audit.SOURCE_FILE_PINS", pins
    )


def _write_inputs(
    root: Path,
    languages: list[str],
    provenance: list[str],
    *,
    somali_count: int,
) -> tuple[Path, Path, Path]:
    language_path = root / "train.v1.lang.gz"
    provenance_path = root / "train.v1.prov.gz"
    stats_path = root / "train.v1.tok.stats.tsv"
    with gzip.open(language_path, "wt", encoding="utf-8") as stream:
        stream.writelines(f"{language}\n" for language in languages)
    with gzip.open(provenance_path, "wt", encoding="utf-8") as stream:
        stream.writelines(f"{source}\n" for source in provenance)
    stats_path.write_text(f"Lang\tSents\nSOM\t{somali_count}\n", encoding="utf-8")
    return language_path, provenance_path, stats_path


def test_audit_counts_somali_sources_without_retaining_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "tools.translation_lab.mt560_provenance_audit.EXPECTED_SOMALI_ROWS", 2
    )
    inputs = _write_inputs(
        tmp_path,
        ["eng", "som", "som", "fra"],
        ["source-a", "source-b", "source-a", "source-c"],
        somali_count=2,
    )
    _set_fixture_pins(monkeypatch, inputs)

    report = audit_provenance(*inputs)

    assert report["total_aligned_index_rows"] == 4
    assert report["somali_rows"] == 2
    assert report["somali_source_counts"] == {"source-a": 1, "source-b": 1}
    assert report["mirror_row_identity_verified"] is False
    assert report["training_authorized"] is False
    assert all("text" not in key for key in report)


def test_audit_rejects_unaligned_index_lengths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "tools.translation_lab.mt560_provenance_audit.EXPECTED_SOMALI_ROWS", 1
    )
    inputs = _write_inputs(
        tmp_path,
        ["som", "eng"],
        ["source-a"],
        somali_count=1,
    )
    _set_fixture_pins(monkeypatch, inputs)

    with pytest.raises(ValueError, match="different row counts"):
        audit_provenance(*inputs)


def test_audit_rejects_somali_count_disagreement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "tools.translation_lab.mt560_provenance_audit.EXPECTED_SOMALI_ROWS", 1
    )
    inputs = _write_inputs(
        tmp_path,
        ["som", "eng"],
        ["source-a", "source-b"],
        somali_count=2,
    )
    _set_fixture_pins(monkeypatch, inputs)

    with pytest.raises(ValueError, match="expected Somali count"):
        audit_provenance(*inputs)


def test_audit_rejects_empty_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "tools.translation_lab.mt560_provenance_audit.EXPECTED_SOMALI_ROWS", 1
    )
    inputs = _write_inputs(
        tmp_path,
        ["som"],
        [""],
        somali_count=1,
    )
    _set_fixture_pins(monkeypatch, inputs)

    with pytest.raises(ValueError, match="Empty index field"):
        audit_provenance(*inputs)


def test_audit_rejects_changed_pinned_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    inputs = _write_inputs(
        tmp_path,
        ["som"],
        ["source-a"],
        somali_count=1,
    )
    _set_fixture_pins(monkeypatch, inputs)
    pins = {
        "language": {
            "bytes": inputs[0].stat().st_size,
            "sha256": "0" * 64,
        },
        "provenance": {
            "bytes": inputs[1].stat().st_size,
            "sha256": hashlib.sha256(inputs[1].read_bytes()).hexdigest(),
        },
        "statistics": {
            "bytes": inputs[2].stat().st_size,
            "sha256": hashlib.sha256(inputs[2].read_bytes()).hexdigest(),
        },
    }
    monkeypatch.setattr(
        "tools.translation_lab.mt560_provenance_audit.SOURCE_FILE_PINS", pins
    )

    with pytest.raises(ValueError, match="SHA-256"):
        audit_provenance(*inputs)
