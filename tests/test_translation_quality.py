# SPDX-License-Identifier: AGPL-3.0-or-later
"""Routing regressions with synthetic model fixtures, never private text."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from saylacian.core import translation
from saylacian.core.transliteration import detect_script


@pytest.fixture
def offline_models(tmp_path, monkeypatch):
    monkeypatch.delenv("SAYLACIAN_EXPERIMENTAL_SYNTHETIC", raising=False)
    base = tmp_path / "somali/en_so"
    base.mkdir(parents=True)
    for name in (
        "model.bin",
        "config.json",
        "shared_vocabulary.json",
        "source.spm",
        "target.spm",
    ):
        (base / name).touch()
    candidate = tmp_path / "somali/en_so_synthetic"
    candidate.mkdir()
    (candidate / "model.bin").touch()
    monkeypatch.setattr(translation, "_model_roots", lambda *_args: [tmp_path])
    tokenizer = Mock()
    tokenizer.encode.return_value = ["token"]
    engines = {}

    def load(folder):
        target = Mock()
        target.decode.return_value = (
            "Natiijo tijaabo." if str(folder) == str(candidate) else "Natiijo caadi ah."
        )
        engine = Mock()
        engine.translate_batch.return_value = [SimpleNamespace(hypotheses=[["result"]])]
        engines[str(folder)] = (target, engine)
        return (tokenizer, target), engine

    loader = Mock(side_effect=load)
    monkeypatch.setattr(translation, "load_model", loader)
    return tmp_path, base, candidate, tokenizer, loader, engines


def test_local_synthetic_presence_does_not_override_default_pack(offline_models):
    root, base, _candidate, _, loader, _ = offline_models
    result = translation.translate_meaning(
        "Hello, friend.", "English", "Somali Latin", root
    )
    assert result.text == "Natiijo caadi ah."
    loader.assert_called_once_with(str(base))


def test_existing_mapped_shei_is_detected_as_coptic_without_inferring_language():
    assert detect_script("ϣϢ ⲁ!")[0] == "Coptic script"
    assert detect_script("ϣ Latin")[0] is None


@pytest.mark.parametrize("setting", ["", "0", "true", "synthetic"])
def test_synthetic_requires_explicit_one(offline_models, monkeypatch, setting):
    root, base, _, _, loader, _ = offline_models
    monkeypatch.setenv(translation.EXPERIMENTAL_SYNTHETIC_ENV, setting)
    translation.translate_meaning("Hello.", "English", "Somali Latin", root)
    loader.assert_called_once_with(str(base))


def test_explicit_experiment_keeps_access_and_does_not_get_preempted_by_afrislm(
    offline_models, monkeypatch
):
    root, _, candidate, _, loader, _ = offline_models
    monkeypatch.setenv(translation.EXPERIMENTAL_SYNTHETIC_ENV, "1")
    afri = Mock(side_effect=AssertionError("Explicit synthetic choice must win"))
    monkeypatch.setattr(translation, "_afrislm_model_path", afri)
    result = translation.translate_meaning("Hello.", "English", "Somali Latin", root)
    assert result.text == "Natiijo tijaabo."
    loader.assert_called_once_with(str(candidate))
    afri.assert_not_called()


def test_missing_opted_in_model_keeps_standard_fallback(offline_models, monkeypatch):
    root, base, candidate, _, loader, _ = offline_models
    monkeypatch.setenv(translation.EXPERIMENTAL_SYNTHETIC_ENV, "1")
    (candidate / "model.bin").unlink()
    result = translation.translate_meaning("Hello.", "English", "Somali Latin", root)
    assert result.text == "Natiijo caadi ah."
    loader.assert_called_once_with(str(base))


@pytest.mark.parametrize(
    "source,output",
    [
        ("John Johnson lives here.", "John Johnson halkan ayuu joogaa."),
        ("Somali and Somaliland are names.", "Somali Somaliland waa magacyo."),
    ],
)
def test_source_supplied_names_are_not_mistaken_for_corrupt_prefixes(source, output):
    assert not translation._synthetic_candidate_is_degenerate(source, output)


@pytest.mark.parametrize(
    "output",
    [
        "Broken brokenword result.",
        "Tarjumid sax ah. Tarjumid sax ah.",
        "Tarjumid \u2047 calaamad",
    ],
)
def test_uncorroborated_prefix_corruption_and_existing_guards_remain(output):
    assert translation._synthetic_candidate_is_degenerate("A useful sentence.", output)


def test_numbers_and_names_are_not_rewritten_and_original_input_reaches_model(
    offline_models,
):
    root, _, _, tokenizer, _, _ = offline_models
    source = "José Álvarez has 12 tablets, not 20."
    result = translation.translate_meaning(source, "English", "Somali Latin", root)
    tokenizer.encode.assert_called_once_with(source, out_type=str)
    assert result.text == "Natiijo caadi ah."
    assert any("Numbers or number formatting" in w for w in result.warnings)
    assert any("negation" in w for w in result.warnings)


def test_numeric_review_is_order_insensitive_and_accepts_unicode_digits():
    notes = translation._translation_review_warnings(
        "12 and ٣", "3 iyo １２", "English"
    )
    assert not notes


@pytest.mark.parametrize(
    "source,output",
    [
        ("Take 12 tablets.", "Qaado 2 kaniini."),
        ("Dose 2.5 mg.", "Dose 25 mg."),
        ("No number.", "12."),
        ("12, 12", "12"),
    ],
)
def test_numeric_review_catches_changed_added_missing_and_repeated_numbers(
    source, output
):
    assert any(
        "Numbers or number formatting" in w
        for w in translation._translation_review_warnings(source, output, "English")
    )


def test_french_negation_review_and_positive_sentence():
    assert any(
        "negation" in w
        for w in translation._translation_review_warnings(
            "N'oubliez pas le rendez-vous.", "Remember the appointment.", "French"
        )
    )
    assert not translation._translation_review_warnings("Bonjour.", "Hello.", "French")


def test_coptic_detection_covers_existing_table_and_rejects_greek_mix():
    from saylacian.core.transliteration import OLD_NUBIAN_CASED_TO_LATIN

    assert detect_script("".join(OLD_NUBIAN_CASED_TO_LATIN))[0] == "Coptic script"
    assert detect_script("ϣΣ")[0] is None


def test_review_cues_reach_website_without_substituting_translation(offline_models):
    from saylacian.website.app import create_app

    response = (
        create_app()
        .test_client()
        .post(
            "/process",
            json={
                "text": "Amina has 12 tablets, not 20.",
                "source": "English",
                "target": "Somali Latin",
                "mode": "meaning",
            },
        )
    )
    assert response.status_code == 200
    assert response.json["text"] == "Natiijo caadi ah."
    assert any("Numbers or number formatting" in w for w in response.json["warnings"])
    assert any("negation" in w for w in response.json["warnings"])


@pytest.mark.parametrize("pieces", [398, 399, 400, 401])
def test_somali_segmentation_reserves_markers_and_preserves_all_input(
    offline_models, monkeypatch, pieces
):
    root, _, _, tokenizer, _, _ = offline_models
    engine = Mock()
    monkeypatch.setattr(
        translation, "load_model", lambda _: ((tokenizer, tokenizer), engine)
    )
    tokenizer.decode.return_value = "Natiijo caadi ah."
    tokenizer.encode.side_effect = lambda text, **kwargs: text.split()
    engine.translate_batch.side_effect = lambda batch, **kwargs: [
        SimpleNamespace(hypotheses=[["result"]]) for _ in batch
    ]
    source = " ".join(f"word{i}" for i in range(pieces))
    result = translation.translate_meaning(source, "English", "Somali Latin", root)
    batch = engine.translate_batch.call_args.args[0]
    assert all(len(segment) <= 400 for segment in batch)
    assert all(segment[0] == ">>som<<" and segment[-1] == "</s>" for segment in batch)
    assert [piece for segment in batch for piece in segment[1:-1]] == source.split()
    assert bool(any("split into independent" in w for w in result.warnings)) == (
        pieces > 398
    )


@pytest.mark.parametrize("finish_reason", ["length", "stop"])
def test_afrislm_rejects_only_reported_truncation(monkeypatch, finish_reason):
    model = Mock()
    model.tokenize.return_value = [1]
    model.create_chat_completion.return_value = {
        "choices": [
            {
                "message": {"content": "Partial translation"},
                "finish_reason": finish_reason,
            }
        ]
    }
    monkeypatch.setattr(translation, "load_afrislm_model", lambda _: model)
    result, warning = translation._translate_afrislm(
        "Source text", "English", "Somali Latin", "model.gguf"
    )
    if finish_reason == "length":
        assert result is None
        assert "cut short" in warning
        assert "standard offline model" in warning
    else:
        assert result.text == "Partial translation"
        assert warning is None


def test_cut_short_optional_translation_uses_complete_standard_route(
    offline_models, monkeypatch
):
    root, base, _, _, loader, _ = offline_models
    model = Mock()
    model.tokenize.return_value = [1]
    model.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Incomplete"}, "finish_reason": "length"}]
    }
    monkeypatch.setattr(translation, "_afrislm_model_path", lambda: "model.gguf")
    monkeypatch.setattr(translation, "load_afrislm_model", lambda _: model)
    result = translation.translate_meaning(
        "A complete source sentence.", "English", "Somali Latin", root
    )
    assert result.text == "Natiijo caadi ah."
    assert any("cut short" in warning for warning in result.warnings)
    loader.assert_called_once_with(str(base))
