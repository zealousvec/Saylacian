# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for private, approved-corpus transliteration coverage audits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.translation_lab.transliteration_corpus_audit import _add_text
from tools.translation_lab.transliteration_corpus_audit import _check_roundtrip
from tools.translation_lab.transliteration_corpus_audit import _new_script_stats
from tools.translation_lab.transliteration_corpus_audit import _retain_sample_text
from tools.translation_lab.transliteration_corpus_audit import audit_corpus


def _write_jsonl(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    encoded = payload.encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def _source_fixture(workspace: Path) -> SimpleNamespace:
    source_id = "approved-en-so"
    revision = "revision-1"
    source = {
        "source_id": source_id,
        "revision": revision,
        "languages": ["en", "so"],
        "license": "CC-BY-4.0",
        "rights_status": "verified",
        "owner_approved": True,
        "gated": False,
        "split_role": "training",
        "rights": {
            "download": "allowed",
            "train": "allowed",
            "evaluate": "allowed",
        },
    }
    registry = workspace / "registry" / "sources.jsonl"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps(source) + "\n", encoding="utf-8")

    root = workspace / "data" / "prepared" / source_id / revision
    train_hash = _write_jsonl(
        root / "train.jsonl",
        [{"source_text": "Hello", "target_text": "af Soomaali"}],
    )
    validation_hash = _write_jsonl(
        root / "validation.jsonl",
        [{"source_text": "A day", "target_text": "maalin qurux badan"}],
    )
    _write_jsonl(root / "test.jsonl", [{"target_text": "must remain unread"}])
    manifest = {
        "source_id": source_id,
        "dataset_revision": revision,
        "license": source["license"],
        "source_page": "https://example.org/data",
        "attribution": "Example source attribution",
        "split_sha256": {
            "train.jsonl": train_hash,
            "validation.jsonl": validation_hash,
            "test.jsonl": "intentionally-invalid-and-unused",
        },
    }
    root.joinpath("manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return SimpleNamespace(
        training_enabled=True,
        approved_source_ids=(source_id,),
        allow_noncommercial_training=False,
    )


def test_audit_reads_only_approved_train_validation_and_saves_no_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    config = _source_fixture(tmp_path)
    opened_paths = []
    original_open = Path.open

    def tracking_open(path: Path, *args, **kwargs):
        opened_paths.append(path)
        if path.name == "test.jsonl":
            raise AssertionError("Test split must not be opened.")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)

    report = audit_corpus(tmp_path, config)

    assert all(path.name != "test.jsonl" for path in opened_paths)
    assert report["source_text_saved"] is False
    assert "must remain unread" not in json.dumps(report)
    assert (
        report["sources"]["approved-en-so"]["splits"]["train"]["Borama"]["sentences"]
        == 1
    )
    assert report["totals"]["Osmanya"]["primary_roundtrip_matches"] == 2


def test_audit_rejects_source_without_owner_approval(tmp_path: Path):
    config = _source_fixture(tmp_path)
    registry_path = tmp_path / "registry" / "sources.jsonl"
    source = json.loads(registry_path.read_text(encoding="utf-8"))
    source["owner_approved"] = False
    registry_path.write_text(json.dumps(source) + "\n", encoding="utf-8")

    with pytest.raises(PermissionError, match="explicit owner approval"):
        audit_corpus(tmp_path, config)


def test_osmanya_audit_counts_long_vowels_recovered_by_alternatives():
    stats = _new_script_stats()

    text = "uu ii"
    _add_text(stats, text, "Osmanya")
    _check_roundtrip(stats, text, "Osmanya")

    assert stats["primary_roundtrip_mismatches"] == 1
    assert stats["alternative_roundtrip_recoveries"] == 1
    assert stats["unresolved_roundtrip_mismatches"] == 0


def test_sample_is_deterministic_deduplicated_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "tools.translation_lab.transliteration_corpus_audit.ROUNDTRIP_SAMPLE_LIMIT",
        3,
    )
    texts = ["same", "same", "one", "two", "three", "four"]
    sample_heaps = {}
    selected_hashes = {}

    for text in texts:
        _retain_sample_text(sample_heaps, selected_hashes, ("source", "train"), text)

    expected = {
        text
        for _priority, text in sorted(
            (
                int(
                    hashlib.sha256(f"1729\0source\0train\0{text}".encode()).hexdigest(),
                    16,
                ),
                text,
            )
            for text in set(texts)
        )[:3]
    }
    sampled = {entry[2] for entry in sample_heaps[("source", "train")]}

    assert len(sample_heaps[("source", "train")]) == 3
    assert selected_hashes[("source", "train")] == {
        entry[1] for entry in sample_heaps[("source", "train")]
    }
    assert sampled == expected
