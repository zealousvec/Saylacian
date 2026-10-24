# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests local translation, route selection, and experimental Somali behavior."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from saylacian.core.translation import (
    MODEL_ROOT,
    _clean_model_markers,
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

    def test_no_hidden_download(self):
        with (
            TemporaryDirectory() as folder,
            patch("socket.socket.connect", side_effect=AssertionError("Network")),
        ):
            with self.assertRaisesRegex(ValueError, "No local model"):
                translate_meaning("hello", "English", "French", folder)

    def test_script_not_meaning_language(self):
        with self.assertRaises(ValueError):
            translate_meaning("b", "Osmanya", "French")

    def test_length_limit(self):
        with self.assertRaises(ValueError):
            translate_meaning("a" * 4001, "English", "French")

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
