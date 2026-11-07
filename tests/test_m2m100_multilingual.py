# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from tools.translation_lab.m2m100_multilingual import _direction_batches
from tools.translation_lab.m2m100_multilingual import _examples_by_direction
from tools.translation_lab.m2m100_multilingual import _macro_validation_loss
from tools.translation_lab.m2m100_multilingual import _source_authorization_record
from tools.translation_lab.m2m100_multilingual import build_route_examples
from tools.translation_lab.m2m100_multilingual import candidate_training_complete


def test_build_route_examples_interleaves_both_pairs_and_directions():
    english = [{"source_text": "hello", "target_text": "salaan"}]
    french = [{"source_text": "bonjour", "target_text": "salaan"}]

    examples = build_route_examples(english, french, french_repeat=2)

    assert len(examples) == 6
    assert {
        (item["source_language"], item["target_language"]) for item in examples
    } == {("en", "so"), ("so", "en"), ("fr", "so"), ("so", "fr")}
    assert sum(item["source_language"] == "fr" for item in examples) == 2
    assert (
        sum(
            item["source_language"] == "so" and item["target_language"] == "fr"
            for item in examples
        )
        == 2
    )


@pytest.mark.parametrize("repeat", [0, 13, -1])
def test_build_route_examples_rejects_unsafe_repeat_values(repeat):
    with pytest.raises(ValueError, match="French repeat"):
        build_route_examples(
            [],
            [{"source_text": "bonjour", "target_text": "salaan"}],
            french_repeat=repeat,
        )


def test_build_route_examples_rejects_empty_parallel_text():
    with pytest.raises(ValueError, match="cannot be empty"):
        build_route_examples([{"source_text": " ", "target_text": "salaan"}], [])


def test_build_route_examples_rejects_missing_text_fields():
    with pytest.raises(TypeError, match="must be strings"):
        build_route_examples([{"source_text": "hello"}], [])


def test_direction_batches_split_at_route_boundary_and_keep_batch_limit():
    rows = [
        {"source_language": "en", "target_language": "so", "n": n} for n in range(5)
    ] + [{"source_language": "so", "target_language": "en", "n": n} for n in range(3)]

    batches = list(_direction_batches(rows, batch_size=4))

    assert [[row["n"] for row in batch] for batch in batches] == [
        [0, 1, 2, 3],
        [4],
        [0, 1, 2],
    ]
    assert all(
        len({(row["source_language"], row["target_language"]) for row in batch}) == 1
        for batch in batches
    )


def test_examples_by_direction_preserves_every_validation_route():
    rows = [
        {"source_language": "en", "target_language": "so", "n": 1},
        {"source_language": "so", "target_language": "en", "n": 2},
        {"source_language": "fr", "target_language": "so", "n": 3},
        {"source_language": "so", "target_language": "fr", "n": 4},
        {"source_language": "fr", "target_language": "so", "n": 5},
    ]

    grouped = _examples_by_direction(rows)

    assert list(grouped) == ["en-so", "fr-so", "so-en", "so-fr"]
    assert {direction: len(items) for direction, items in grouped.items()} == {
        "en-so": 1,
        "fr-so": 2,
        "so-en": 1,
        "so-fr": 1,
    }
    assert sorted(item["n"] for items in grouped.values() for item in items) == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_examples_by_direction_rejects_missing_or_unsupported_routes():
    with pytest.raises(ValueError, match="(?i)at least one validation"):
        _examples_by_direction([])
    with pytest.raises(ValueError, match="(?i)unsupported route"):
        _examples_by_direction([{"source_language": "ar", "target_language": "so"}])


def test_macro_validation_loss_weights_each_direction_equally():
    result = _macro_validation_loss(
        {
            "en-so": {"examples": 100, "loss": 2.0},
            "fr-so": {"examples": 1, "loss": 4.0},
        }
    )

    assert result == 3.0


def test_macro_validation_loss_rejects_empty_or_nonfinite_values():
    with pytest.raises(ValueError, match="At least one directional"):
        _macro_validation_loss({})
    with pytest.raises(ValueError, match="must be finite"):
        _macro_validation_loss({"en-so": {"loss": float("inf")}})


def test_candidate_evaluation_requires_complete_training_report(tmp_path):
    adapter = tmp_path / "adapter_model.safetensors"
    adapter.write_bytes(b"candidate")
    metadata = {
        "automatic_promotion": False,
        "fingerprint": {"pair_data": {"pairs": {"fr-so": {}}}},
    }

    assert not candidate_training_complete(metadata, None, adapter)
    assert not candidate_training_complete(
        metadata, {"status": "PAUSED_RESOURCE"}, adapter
    )
    assert candidate_training_complete(
        metadata, {"status": "TRAINED_RESEARCH_CANDIDATE"}, adapter
    )


def test_candidate_evaluation_rejects_missing_adapter(tmp_path):
    metadata = {
        "automatic_promotion": False,
        "fingerprint": {"pair_data": {"pairs": {"fr-so": {}}}},
    }

    assert not candidate_training_complete(
        metadata,
        {"status": "TRAINED_RESEARCH_CANDIDATE"},
        tmp_path / "missing.safetensors",
    )


def test_source_authorization_record_separates_training_and_redistribution_rights():
    record = _source_authorization_record(
        {
            "source_id": "opus-infopankki-fr-so",
            "license": "CC-BY-4.0",
            "revision": "pinned-revision",
            "rights_status": "verified",
            "owner_approved": True,
            "private_owner_approval": {
                "approved_utc": "2026-11-05",
                "scope": "local private training",
            },
            "rights": {
                "download": "allowed",
                "process": "allowed",
                "train": "allowed",
                "evaluate": "allowed",
                "redistribute_raw": "approval_required",
                "redistribute_derivative": "approval_required",
                "redistribute_weights": "approval_required",
            },
        }
    )

    assert record["owner_approved"] is True
    assert record["rights"]["train"] == "allowed"
    assert record["rights"]["redistribute_weights"] == "approval_required"
    assert "authorized_by" not in record


@pytest.mark.parametrize("reverse", [False, True])
def test_heldout_direction_without_metadata_uses_canonical_english_somali(reverse):
    from tools.translation_lab.m2m100_multilingual import _directed_test_examples

    row = {"source_text": "hello", "target_text": "salaan", "record_id": "fixture"}
    route = ("so", "en") if reverse else ("en", "so")
    result = _directed_test_examples([row], *route)[0]
    assert result["source_text"] == ("salaan" if reverse else "hello")
    assert result["target_text"] == ("hello" if reverse else "salaan")
    assert result["record_id"] == "fixture"


@pytest.mark.parametrize(
    "metadata",
    [{"source_language": "en"}, {"source_language": "de", "target_language": "so"}],
)
def test_heldout_direction_rejects_partial_or_mismatched_metadata(metadata):
    from tools.translation_lab.m2m100_multilingual import _directed_test_examples

    with pytest.raises(ValueError, match="language pair"):
        _directed_test_examples(
            [dict(source_text="hello", target_text="salaan", **metadata)], "en", "so"
        )
