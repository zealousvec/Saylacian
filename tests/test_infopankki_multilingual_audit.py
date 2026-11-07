# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check multilingual InfoPankki audit rules without corpus downloads."""

from __future__ import annotations

import zipfile
from pathlib import Path

from tools.translation_lab.infopankki_multilingual_audit import PAIR_ARTIFACTS
from tools.translation_lab.infopankki_multilingual_audit import _group_and_split
from tools.translation_lab.infopankki_multilingual_audit import _language_id_probe
from tools.translation_lab.infopankki_multilingual_audit import _load_tico_dev_targets
from tools.translation_lab.infopankki_multilingual_audit import _verify_catalog_source
from tools.translation_lab.infopankki_multilingual_audit import audit_pair_rows
from tools.translation_lab.sources import load_catalog


def test_pair_audit_reports_duplicates_and_cross_corpus_overlap():
    rows = [
        {"translation": {"fr": "Bonjour", "so": "Salaan"}},
        {"translation": {"fr": "Bonjour", "so": "Salaan"}},
        {"translation": {"fr": "Salut", "so": "Maalin wanaagsan"}},
        {"translation": {"fr": "  ", "so": ""}},
        {"translation": {"fr": "Maqan", "so": 5}},
    ]

    report = audit_pair_rows(
        rows,
        source_language="fr",
        mixture_somali={"salaan"},
        tico_dev_somali={"maalin wanaagsan"},
    )

    assert report == {
        "rows": 5,
        "malformed_rows": 1,
        "empty_pairs": 1,
        "duplicate_pairs_after_first": 1,
        "repeated_somali_rows_after_first": 1,
        "unique_somali_strings": 2,
        "somali_overlap_with_mixture_all_splits": 2,
        "somali_overlap_with_tico_dev": 1,
        "pairs_over_256_words": 0,
        "median_somali_to_source_character_ratio": 0.86,
    }


def test_tico_audit_reader_only_loads_dev_split(tmp_path: Path):
    archive = tmp_path / "tico.zip"
    dev_tsv = (
        "sourceLang\ttargetLang\tsourceString\ttargetString\nen\tso\tHello\tSalaan\n"
    )
    with zipfile.ZipFile(archive, "w") as source:
        source.writestr("tico19-testset/dev/dev.en-so.tsv", dev_tsv)
        source.writestr(
            "tico19-testset/test/test.en-so.tsv",
            "en\tso\tPrivate test input\tPrivate test reference\n",
        )

    assert _load_tico_dev_targets(archive) == {"salaan"}


def test_exact_pair_duplicate_key_normalizes_unicode_and_whitespace():
    report = audit_pair_rows(
        [
            {"translation": {"fr": "e\u0301cole", "so": "  Wanaag   "}},
            {"translation": {"fr": "ÉCOLE", "so": "wanaag"}},
        ],
        source_language="fr",
        mixture_somali=set(),
        tico_dev_somali=set(),
    )

    assert report["duplicate_pairs_after_first"] == 1


def test_group_split_keeps_shared_somali_targets_in_one_partition():
    rows = [
        {
            "record_id": "fr:1",
            "source_text": "Bonjour tout le monde",
            "target_text": "Salaan dhammaantiin",
        },
        {
            "record_id": "ar:1",
            "source_text": "مرحبا بالجميع",
            "target_text": "Salaan dhammaantiin",
        },
        {
            "record_id": "fr:2",
            "source_text": "Bonne journée",
            "target_text": "Maalin wanaagsan",
        },
        {
            "record_id": "ar:2",
            "source_text": "صباح الخير",
            "target_text": "Subax wanaagsan",
        },
    ]

    splits, group_count = _group_and_split(rows, seed=1729)
    record_splits = {
        row["record_id"]: split
        for split, split_rows in splits.items()
        for row in split_rows
    }

    assert group_count == 3
    assert record_splits["fr:1"] == record_splits["ar:1"]


def test_language_id_probe_reports_without_filtering_rows():
    probe = _language_id_probe(
        [
            {
                "source_language": "fr",
                "source_text": (
                    "Bonjour à toutes et à tous, bienvenue dans notre "
                    "ville aujourd'hui."
                ),
                "target_text": "Salaan dhammaan, kusoo dhowaada magaaladeenna maanta.",
            }
        ]
    )

    assert probe["version"] == "py3langid 0.4.0"
    assert probe["minimum_characters"] == 50
    assert probe["filtering_applied"] is False
    assert probe["sides"]["source:fr"]["checked"] == 1
    assert probe["sides"]["somali:so"]["checked"] == 1


def test_catalog_pins_both_source_pairs_without_approving_training():
    repository = Path(__file__).resolve().parents[1]
    catalog = load_catalog(repository / "research" / "sources.catalog.json")

    for pair in PAIR_ARTIFACTS:
        approval = _verify_catalog_source(pair, catalog)
        assert approval["owner_approved"] is False
        assert approval["train_right"] == "allowed"
