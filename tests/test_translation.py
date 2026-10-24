# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests local translation, route selection, and experimental Somali behavior."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from saylacian.core.translation import (
    MODEL_ROOT,
    _clean_model_markers,
    _synthetic_candidate_is_degenerate,
    translate_meaning,
)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.provider = patch.dict(
            os.environ, {"SAYLACIAN_TRANSLATION_PROVIDER": "offline"}
        )
        self.provider.start()
        self.addCleanup(self.provider.stop)

    def test_known_model_formatting_artifacts_are_removed_only_at_start(self):
        self.assertEqual(
            _clean_model_markers("○ A child will read a book."),
            "A child will read a book.",
        )
        self.assertEqual(_clean_model_markers("Text ○ remains."), "Text ○ remains.")

    def test_synthetic_candidate_unknown_token_marker_is_degenerate(self):
        self.assertTrue(
            _synthetic_candidate_is_degenerate("rare term", "Tarjumid \u2047 calaamad")
        )

    def test_synthetic_unknown_token_marker_uses_multilingual_fallback(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            fallback = root / "somali" / "en_so"
            fallback.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (fallback / filename).touch()
            candidate = root / "somali" / "en_so_synthetic"
            candidate.mkdir()
            (candidate / "model.bin").touch()

            candidate_source = Mock()
            candidate_source.encode.return_value = ["candidate-token"]
            candidate_target = Mock()
            candidate_target.decode.return_value = "Tarjumid \u2047 calaamad"
            candidate_engine = Mock()
            candidate_engine.translate_batch.return_value = [
                Mock(hypotheses=[["candidate-output"]])
            ]

            fallback_source = Mock()
            fallback_source.encode.return_value = ["fallback-token"]
            fallback_target = Mock()
            fallback_target.decode.return_value = "Qoraal tijaabo"
            fallback_engine = Mock()
            fallback_engine.translate_batch.return_value = [
                Mock(hypotheses=[["fallback-output"]])
            ]

            with patch(
                "saylacian.core.translation.load_model",
                side_effect=(
                    ((candidate_source, candidate_target), candidate_engine),
                    ((fallback_source, fallback_target), fallback_engine),
                ),
            ):
                result = translate_meaning(
                    "rare terminology", "English", "Somali Latin", root
                )

        self.assertEqual(result.text, "Qoraal tijaabo")
        self.assertTrue(
            any("unknown-token marker" in warning for warning in result.warnings)
        )
        fallback_engine.translate_batch.assert_called_once()

    def test_no_hidden_download(self):
        with (
            TemporaryDirectory() as folder,
            patch("socket.socket.connect", side_effect=AssertionError("Network")),
            self.assertRaisesRegex(ValueError, "No local model"),
        ):
            translate_meaning("hello", "English", "French", folder)

    def test_script_not_meaning_language(self):
        with self.assertRaises(ValueError):
            translate_meaning("b", "Osmanya", "French")

    def test_length_limit(self):
        with self.assertRaises(ValueError):
            translate_meaning("a" * 4001, "English", "French")

    def test_token_limit_rejects_without_model_inference(self):
        with TemporaryDirectory() as temporary:
            model = Path(temporary) / "en_fr"
            (model / "model").mkdir(parents=True)
            (model / "model" / "model.bin").touch()
            (model / "sentencepiece.model").touch()
            tokenizer = Mock()
            tokenizer.encode.return_value = ["piece"] * 401
            engine = Mock()

            with (
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=(tokenizer, engine),
                ),
                self.assertRaisesRegex(ValueError, "400-token limit"),
            ):
                translate_meaning(
                    "small enough by characters", "English", "French", temporary
                )

            engine.translate_batch.assert_not_called()

    def test_somali_token_limit_includes_language_markers(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary) / "somali" / "so_en"
            folder.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (folder / filename).touch()
            source_tokenizer = Mock()
            source_tokenizer.encode.return_value = ["piece"] * 399
            target_tokenizer = Mock()
            engine = Mock()

            with (
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=((source_tokenizer, target_tokenizer), engine),
                ),
                self.assertRaisesRegex(ValueError, "400-token limit"),
            ):
                translate_meaning("short passage", "Somali Latin", "English", temporary)

            engine.translate_batch.assert_not_called()

    def test_synthetic_somali_token_limit_rejects_before_inference(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "somali" / "en_so"
            model.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (model / filename).touch()
            synthetic = root / "somali" / "en_so_synthetic"
            synthetic.mkdir()
            (synthetic / "model.bin").touch()
            source_tokenizer = Mock()
            source_tokenizer.encode.return_value = ["piece"] * 401
            target_tokenizer = Mock()
            engine = Mock()

            with (
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=((source_tokenizer, target_tokenizer), engine),
                ),
                self.assertRaisesRegex(ValueError, "400-token limit"),
            ):
                translate_meaning("short passage", "English", "Somali Latin", temporary)

            engine.translate_batch.assert_not_called()

    @unittest.skipUnless(
        (MODEL_ROOT / "en_fr/model/model.bin").exists(), "Local model not installed"
    )
    def test_english_french_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            self.assertEqual(
                translate_meaning("Hello, how are you?", "English", "French").text,
                "Bonjour, comment allez-vous ?",
            )

    @unittest.skipUnless(
        (MODEL_ROOT / "fr_en/model/model.bin").exists(), "Local model not installed"
    )
    def test_french_english_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            self.assertEqual(
                translate_meaning(
                    "Bonjour, comment allez-vous ?", "French", "English"
                ).text,
                "Hello, how are you?",
            )

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so/model.bin").exists(), "Somali model not installed"
    )
    def test_english_somali_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "The child is reading a book.", "English", "Somali Latin"
            )
        self.assertTrue(result.text)
        self.assertTrue(any("review" in warning for warning in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so_synthetic/model.bin").exists(),
        "Synthetic EN→SO candidate not installed",
    )
    def test_synthetic_candidate_improves_verified_examples_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            thank_you = translate_meaning("Thank you.", "English", "Somali Latin")
            morning = translate_meaning("Good morning.", "English", "Somali Latin")
        self.assertEqual(thank_you.text, "Waad ku mahadsan tahay.")
        self.assertEqual(morning.text, "Subax wanaagsan.")
        self.assertTrue(any("synthetic" in warning for warning in thank_you.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so_synthetic/model.bin").exists(),
        "Synthetic EN→SO candidate not installed",
    )
    def test_synthetic_candidate_repetition_falls_back_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning("How are you?", "English", "Somali Latin")
        self.assertTrue(result.text)
        self.assertTrue(any("used multilingual fallback" in w for w in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so_synthetic/model.bin").exists(),
        "Synthetic EN→SO candidate not installed",
    )
    def test_synthetic_runaway_output_uses_multilingual_rescue(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "and i have a cough too", "English", "Somali Latin"
            )
        self.assertTrue(result.text)
        self.assertTrue(any("used multilingual fallback" in w for w in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/so_en/model.bin").exists(), "Somali model not installed"
    )
    def test_somali_english_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "Salaan, sidee tahay?", "Somali Latin", "English"
            )
        self.assertEqual(result.text, "How are you?")

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/so_en/model.bin").exists()
        and (MODEL_ROOT / "en_fr/model/model.bin").exists(),
        "Somali-English or English-French model not installed",
    )
    def test_somali_french_pivot_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning("Salaan, sidee tahay?", "Somali Latin", "French")
        self.assertEqual(result.text, "Comment allez-vous ?")
        self.assertTrue(any("errors may compound" in w for w in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "fr_en/model/model.bin").exists()
        and (MODEL_ROOT / "somali/en_so/model.bin").exists(),
        "French-English or English-Somali model not installed",
    )
    def test_french_somali_pivot_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "Bonjour, comment allez-vous ?", "French", "Somali Latin"
            )
        self.assertEqual(result.text, "Hello, sidee baad u tahay?")
        self.assertTrue(any("human review" in w for w in result.warnings))
        self.assertTrue(any("errors may compound" in w for w in result.warnings))
