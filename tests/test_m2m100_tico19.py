# SPDX-License-Identifier: AGPL-3.0-or-later
"""Safety and data-integrity checks for M2M100 TICO-19 dev evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.translation_lab.config import LabConfig
from tools.translation_lab.m2m100_tico19 import _check_overlap
from tools.translation_lab.m2m100_tico19 import _load_training_rows
from tools.translation_lab.m2m100_tico19 import _make_routes
from tools.translation_lab.m2m100_training import _prepared_data
from tools.translation_lab.mixture_data import MIXTURE_ID


def test_make_routes_includes_both_directions() -> None:
    routes = _make_routes([{"source_text": "Hello", "target_text": "Salaan"}])

    assert routes == {
        "en-so": [{"source": "Hello", "reference": "Salaan"}],
        "so-en": [{"source": "Salaan", "reference": "Hello"}],
    }


def test_check_overlap_reports_all_exact_overlap_counts() -> None:
    training = [{"source_text": "Hello", "target_text": "Salaan"}]

    with pytest.raises(ValueError) as error:
        _check_overlap([{"source_text": "hello", "target_text": "salaan"}], training)

    assert "'exact_pair': 1" in str(error.value)
    assert "'exact_english': 1" in str(error.value)
    assert "'exact_somali': 1" in str(error.value)


def test_check_overlap_rejects_any_exact_leakage() -> None:
    training = [{"source_text": "Hello", "target_text": "Salaan"}]

    with pytest.raises(ValueError, match="Exact training overlap"):
        _check_overlap(
            [{"source_text": "Hello", "target_text": "Different Somali"}],
            training,
        )


def test_check_overlap_reports_zero_without_leakage() -> None:
    overlap = _check_overlap(
        [{"source_text": "Good morning", "target_text": "Subax wanaagsan"}],
        [{"source_text": "Good night", "target_text": "Habeen wanaagsan"}],
    )

    assert overlap == {"exact_pair": 0, "exact_english": 0, "exact_somali": 0}


def test_load_training_rows_verifies_manifest_and_candidate_fingerprint(
    tmp_path: Path,
) -> None:
    experiment_id = "candidate"
    revision = "pinned-revision"
    train_rows = [{"source_text": "Hello", "target_text": "Salaan"}]
    train_contents = (json.dumps(train_rows[0], ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    train_hash = hashlib.sha256(train_contents).hexdigest()
    dataset_dir = tmp_path / "data" / "prepared" / "google-smol-en-so" / revision
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "train.jsonl").write_bytes(train_contents)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "dataset_revision": revision,
                "split_sha256": {"train.jsonl": train_hash},
            }
        ),
        encoding="utf-8",
    )
    experiment_dir = tmp_path / "experiments" / experiment_id
    experiment_dir.mkdir(parents=True)
    (experiment_dir / "experiment.json").write_text(
        json.dumps(
            {
                "fingerprint": {
                    "model_id": "meta-m2m100-418m",
                    "model_revision": "55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636",
                    "dataset_id": "google-smol-en-so",
                    "dataset_revision": revision,
                    "train_sha256": train_hash,
                }
            }
        ),
        encoding="utf-8",
    )

    assert _load_training_rows(tmp_path, experiment_id) == train_rows

    (dataset_dir / "train.jsonl").write_bytes(train_contents + train_contents)
    with pytest.raises(ValueError, match="hash checks"):
        _load_training_rows(tmp_path, experiment_id)


def test_m2m_training_accepts_verified_mixture_without_aggregate_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.translation_lab import mixture_data

    manifest = {"source_id": MIXTURE_ID, "dataset_revision": "mixture-revision"}
    train_rows = [{"source_text": "Hello", "target_text": "Salaan"}]
    validation_rows = [{"source_text": "Goodbye", "target_text": "Nabadgelyo"}]
    monkeypatch.setattr(
        mixture_data,
        "prepare_marian_mixture",
        lambda workspace, config: (manifest, train_rows, validation_rows, []),
    )
    config = LabConfig(
        approved_source_ids=(
            "google-smol-en-so",
            "opus-infopankki-en-so",
            "opus-paracrawl-en-so",
        ),
        training_enabled=True,
    )

    prepared, train, validation = _prepared_data(
        tmp_path, config, dataset_id=MIXTURE_ID
    )

    assert prepared is manifest
    assert train == train_rows
    assert validation == validation_rows


def test_mixture_tico_loader_checks_row_license_provenance(tmp_path: Path) -> None:
    experiment_id = "mixture-candidate"
    revision = "mixture-revision"
    train_rows = [
        {
            "source_text": "Hello",
            "target_text": "Salaan",
            "source_id": "google-smol-en-so",
            "license": "CC-BY-4.0",
        }
    ]
    train_contents = (json.dumps(train_rows[0], ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    train_hash = hashlib.sha256(train_contents).hexdigest()
    dataset_dir = tmp_path / "data" / "prepared" / MIXTURE_ID / revision
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "train.jsonl").write_bytes(train_contents)
    source_revisions = {"google-smol-en-so": "source-revision"}
    source_licenses = {"google-smol-en-so": "CC-BY-4.0"}
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "dataset_revision": revision,
                "source_revisions": source_revisions,
                "source_licenses": source_licenses,
                "split_sha256": {"train.jsonl": train_hash},
            }
        ),
        encoding="utf-8",
    )
    experiment_dir = tmp_path / "experiments" / experiment_id
    experiment_dir.mkdir(parents=True)
    (experiment_dir / "experiment.json").write_text(
        json.dumps(
            {
                "fingerprint": {
                    "model_id": "meta-m2m100-418m",
                    "model_revision": "55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636",
                    "dataset_id": MIXTURE_ID,
                    "dataset_revision": revision,
                    "train_sha256": train_hash,
                    "source_revisions": source_revisions,
                    "source_licenses": source_licenses,
                }
            }
        ),
        encoding="utf-8",
    )

    assert _load_training_rows(tmp_path, experiment_id) == train_rows

    train_rows[0]["license"] = "wrong-license"
    invalid_contents = (json.dumps(train_rows[0], ensure_ascii=False) + "\n").encode(
        "utf-8"
    )
    invalid_hash = hashlib.sha256(invalid_contents).hexdigest()
    (dataset_dir / "train.jsonl").write_bytes(invalid_contents)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "dataset_revision": revision,
                "source_revisions": source_revisions,
                "source_licenses": source_licenses,
                "split_sha256": {"train.jsonl": invalid_hash},
            }
        ),
        encoding="utf-8",
    )
    (experiment_dir / "experiment.json").write_text(
        json.dumps(
            {
                "fingerprint": {
                    "model_id": "meta-m2m100-418m",
                    "model_revision": "55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636",
                    "dataset_id": MIXTURE_ID,
                    "dataset_revision": revision,
                    "train_sha256": invalid_hash,
                    "source_revisions": source_revisions,
                    "source_licenses": source_licenses,
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="row-level source licenses"):
        _load_training_rows(tmp_path, experiment_id)
