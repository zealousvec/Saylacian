# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression checks for the pinned Somali MOT corpus audit."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from tools.translation_lab.mot_monolingual import _document_is_verified_somali
from tools.translation_lab.mot_monolingual import _filter_near_duplicates
from tools.translation_lab.mot_monolingual import _is_safe_member
from tools.translation_lab.mot_monolingual import _jaccard_at_least
from tools.translation_lab.mot_monolingual import _minhash_signature
from tools.translation_lab.mot_monolingual import _word_shingles
from tools.translation_lab.mot_monolingual import iter_sentence_strings
from tools.translation_lab.mot_monolingual import load_excluded_texts
from tools.translation_lab.mot_monolingual import load_tico_exclusions
from tools.translation_lab.mot_monolingual import normalize_text


def test_normalize_and_flatten_nested_mot_sentences():
    assert normalize_text("  Qoysaska\u00a0 Deegaanka  ") == "qoysaska deegaanka"
    assert list(iter_sentence_strings([["kow", "laba"], "saddex"])) == [
        "kow",
        "laba",
        "saddex",
    ]


def test_verified_somali_filter_requires_confident_site_and_model_labels():
    record = {
        "content_type": "article",
        "site_language": "som",
        "predicted_language": "som",
        "cld3_detected_languages": {
            "som": {
                "cld3_language": "so",
                "is_reliable": True,
                "probability": 0.99,
                "proportion": 0.95,
            }
        },
    }
    assert _document_is_verified_somali(record)
    record["predicted_language"] = "eng"
    assert not _document_is_verified_somali(record)


def test_archive_path_guard_rejects_traversal_and_links():
    safe = tarfile.TarInfo("som_voasomali/article/a_1.json")
    traversal = tarfile.TarInfo("som_voasomali/article/../../outside.json")
    link = tarfile.TarInfo("som_voasomali/article/link.json")
    link.type = tarfile.SYMTYPE
    assert _is_safe_member(safe)
    assert not _is_safe_member(traversal)
    assert not _is_safe_member(link)


def test_minhash_finds_near_duplicate_with_punctuation_change():
    first = _word_shingles(
        "Dowladdu waxay maanta ku dhawaaqday qorshe cusub oo lagu taageerayo qoysaska."
    )
    second = _word_shingles(
        "Dowladdu waxay maanta ku dhawaaqday qorshe cusub oo lagu taageerayo qoysaska!"
    )
    assert first is not None
    assert second is not None
    assert _minhash_signature(first) == _minhash_signature(second)
    assert _jaccard_at_least(first, second, 0.90)


def test_near_duplicate_filter_removes_duplicates_and_holdout_overlap(tmp_path: Path):
    path = tmp_path / "sentences.jsonl"
    original = (
        "Dowladdu waxay maanta ku dhawaaqday qorshe cusub oo taageeraya qoysaska."
    )
    near_duplicate = (
        "Dowladdu waxay maanta ku dhawaaqday qorshe cusub oo taageeraya qoysaska!"
    )
    holdout = "Xukuumadda ayaa qorshe gaar ah u dejisay daryeelka bulshada deegaanka."
    unrelated = "Roobab xooggan ayaa ka da'ay qaybo badan oo dalka ka mid ah maanta."
    rows = [
        {"text": original, "document_id": "first"},
        {"text": near_duplicate, "document_id": "second"},
        {"text": holdout, "document_id": "third"},
        {"text": unrelated, "document_id": "fourth"},
    ]
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    counts = _filter_near_duplicates(path, {normalize_text(holdout)})

    kept = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["document_id"] for row in kept] == ["first", "fourth"]
    assert counts["near_duplicate_sentences_removed"] == 1
    assert counts["near_overlap_sentences_removed"] == 1


def test_exclusion_loader_uses_only_somali_target_text(tmp_path: Path):
    path = tmp_path / "split.jsonl"
    row = {"source_text": "English source", "target_text": "Somali target"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    excluded, hashes = load_excluded_texts([path])

    assert excluded == {"somali target"}
    assert set(hashes) == {"split.jsonl"}
    assert len(hashes["split.jsonl"]) == 64


def test_tico_corpus_filter_reads_dev_only(tmp_path: Path, monkeypatch):
    from tools.translation_lab import tico19_benchmark

    requested_splits = []

    def fake_load_split(_archive: Path, split: str) -> list[dict]:
        requested_splits.append(split)
        return [{"target_text": f"  {split} target  "}]

    monkeypatch.setattr(tico19_benchmark, "load_split", fake_load_split)

    excluded = load_tico_exclusions(tmp_path / "tico.zip")

    assert excluded == {"dev target"}
    assert requested_splits == ["dev"]
