# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the private, train/validation-only mixture language audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.translation_lab.mixture_language_audit import audit_mixture_languages


def _write_jsonl(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row) + "\n" for row in rows).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _write_fixture(workspace: Path) -> tuple[SimpleNamespace, str, Path]:
    source_id = "approved-source"
    revision = "pinned-revision"
    source = {
        "source_id": source_id,
        "revision": "source-revision",
        "languages": ["en", "so"],
        "license": "CC-BY-4.0",
        "rights_status": "verified",
        "owner_approved": True,
        "gated": False,
        "split_role": "training",
        "rights": {"download": "allowed", "train": "allowed"},
    }
    registry = workspace / "registry" / "sources.jsonl"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps(source) + "\n", encoding="utf-8")

    root = workspace / "data" / "prepared" / "marian-mixture" / revision
    row = {
        "record_id": "row-1",
        "source_id": source_id,
        "license": "CC-BY-4.0",
        "dataset_revision": source["revision"],
        "source_text": "English source text with enough characters",
        "target_text": "Somali target text with enough characters",
    }
    train_hash = _write_jsonl(root / "train.jsonl", [row])
    validation_row = {
        **row,
        "record_id": "row-2",
        "source_text": "Somali text mistakenly placed on English side",
    }
    validation_hash = _write_jsonl(root / "validation.jsonl", [validation_row])
    _write_jsonl(root / "test.jsonl", [{**row, "source_text": "sealed test text"}])
    manifest = {
        "source_id": "marian-mixture",
        "dataset_revision": revision,
        "source_revisions": {source_id: source["revision"]},
        "source_licenses": {source_id: source["license"]},
        "split_sha256": {
            "train.jsonl": train_hash,
            "validation.jsonl": validation_hash,
            "test.jsonl": "must-not-be-checked",
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    experiment_id = "fixture-run"
    experiment = workspace / "experiments" / experiment_id
    experiment.mkdir(parents=True)
    metadata = {
        "experiment_id": experiment_id,
        "fingerprint": {
            "dataset_id": "marian-mixture",
            "dataset_revision": revision,
            "source_revisions": manifest["source_revisions"],
            "source_licenses": manifest["source_licenses"],
            "train_sha256": train_hash,
            "validation_sha256": validation_hash,
        },
    }
    (experiment / "experiment.json").write_text(json.dumps(metadata), encoding="utf-8")
    config = SimpleNamespace(
        training_enabled=True,
        approved_source_ids=(source_id,),
        allow_noncommercial_training=False,
    )
    return config, experiment_id, root


def test_audit_verifies_train_validation_and_never_opens_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    config, experiment_id, root = _write_fixture(tmp_path)
    opened_paths = []
    original_open = Path.open

    def tracking_open(path: Path, *args, **kwargs):
        opened_paths.append(path)
        if path.name == "test.jsonl":
            raise AssertionError("The sealed test split must not be opened.")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)
    monkeypatch.setattr(
        "tools.translation_lab.mixture_language_audit.MINIMUM_CHARACTERS", 1
    )

    def classify(text: str) -> tuple[str, float]:
        return ("so" if text.startswith("Somali") else "en", 0.0)

    report = audit_mixture_languages(
        tmp_path,
        config,
        experiment_id,
        sample_limit=5,
        classifier=classify,
    )

    source_report = report["sources"]["approved-source"]["splits"]
    assert source_report["train"]["english"]["mismatch_rate"] == 0
    assert source_report["validation"]["english"]["mismatch_rate"] == 1
    assert all(path.name != "test.jsonl" for path in opened_paths)
    assert report["test_split_opened"] is False
    assert report["filtering_applied"] is False
    serialized = json.dumps(report)
    assert "sealed test text" not in serialized
    assert "English source text" not in serialized
    assert root.joinpath("test.jsonl").exists()


def test_audit_rejects_mixture_license_mismatch(tmp_path: Path):
    config, experiment_id, root = _write_fixture(tmp_path)
    rows = [
        json.loads(line)
        for line in root.joinpath("train.jsonl").read_text().splitlines()
    ]
    rows[0]["license"] = "UNKNOWN"
    _write_jsonl(root / "train.jsonl", rows)
    manifest = json.loads(root.joinpath("manifest.json").read_text())
    updated_hash = _sha256(root / "train.jsonl")
    manifest["split_sha256"]["train.jsonl"] = updated_hash
    root.joinpath("manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    metadata_path = tmp_path / "experiments" / experiment_id / "experiment.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["fingerprint"]["train_sha256"] = updated_hash
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="Row license mismatch"):
        audit_mixture_languages(
            tmp_path,
            config,
            experiment_id,
            classifier=lambda _text: ("en", 0.0),
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
