# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests language and script detection."""

import unittest
from unittest.mock import patch

from saylacian.core import language_detection
from saylacian.core.language_detection import detect_language


class FakeIdentifier:
    def __init__(self, code, confidence):
        self.code = code
        self.confidence = confidence

    def classify(self, _text):
        return self.code, self.confidence


class LanguageDetectionTests(unittest.TestCase):
    def test_detects_supported_latin_languages(self):
        samples = (
            ("The child is reading a book and learning every day.", "English"),
            (
                "Bonjour, comment allez-vous aujourd’hui ? Je vais bien, merci.",
                "French",
            ),
            (
                "Salaan, sidee tahay? Waxaan rajeynayaa inaad fiican tahay.",
                "Somali Latin",
            ),
        )
        for text, expected in samples:
            with self.subTest(language=expected):
                language, confidence, message = detect_language(text)
                self.assertEqual(language, expected, message)
                self.assertGreaterEqual(confidence, 0.70)

    def test_abstains_on_short_text(self):
        language, confidence, message = detect_language("Salaan")
        self.assertIsNone(language)
        self.assertEqual(confidence, 0.0)
        self.assertIn("three words", message)

    def test_abstains_on_punctuation_masquerading_as_three_words(self):
        with patch.object(language_detection, "_identifier") as identifier:
            language, confidence, message = detect_language("!!! ??? ... !!!")

        self.assertIsNone(language)
        self.assertEqual(confidence, 0.0)
        self.assertIn("five letters", message)
        identifier.assert_not_called()

    def test_detects_high_confidence_short_text_in_supported_languages(self):
        samples = (
            ("Where is my phone?", "English"),
            ("Ou est la gare", "French"),
            ("Je suis heureux", "French"),
            ("Waan ku jeclahay", "Somali Latin"),
        )
        for text, expected in samples:
            with self.subTest(language=expected):
                language, confidence, message = detect_language(text)
                self.assertEqual(language, expected, message)
                self.assertGreaterEqual(confidence, 0.80)

    def test_abstains_on_low_confidence_short_text(self):
        language, _, message = detect_language("Bonjour mon ami")
        self.assertIsNone(language)
        self.assertIn("Short text is uncertain", message)

    def test_short_text_uses_evidence_backed_confidence_boundary(self):
        with patch.object(
            language_detection,
            "_identifier",
            return_value=FakeIdentifier("en", 0.70),
        ):
            language, confidence, message = detect_language("Where is my phone?")

        self.assertEqual(language, "English")
        self.assertEqual(confidence, 0.70)
        self.assertEqual(message, "")

        with patch.object(
            language_detection,
            "_identifier",
            return_value=FakeIdentifier("en", 0.699),
        ):
            language, confidence, message = detect_language("Where is my phone?")

        self.assertIsNone(language)
        self.assertEqual(confidence, 0.699)
        self.assertIn("Short text is uncertain", message)

    def test_short_somali_text_uses_same_confidence_boundary(self):
        with patch.object(
            language_detection,
            "_identifier",
            return_value=FakeIdentifier("so", 0.699),
        ):
            language, confidence, message = detect_language("Waan ku jeclahay")

        self.assertIsNone(language)
        self.assertEqual(confidence, 0.699)
        self.assertIn("Short text is uncertain", message)

        with patch.object(
            language_detection,
            "_identifier",
            return_value=FakeIdentifier("so", 0.70),
        ):
            language, confidence, message = detect_language("Waan ku jeclahay")

        self.assertEqual(language, "Somali Latin")
        self.assertEqual(confidence, 0.70)
        self.assertEqual(message, "")

    def test_short_high_confidence_unsupported_language_stays_unsupported(self):
        language, confidence, message = detect_language("Guten Tag mein Freund")
        self.assertIsNone(language)
        self.assertGreaterEqual(confidence, 0.85)
        self.assertIn("not supported", message)

    def test_abstains_on_unsupported_language(self):
        language, _, _ = detect_language(
            "Ola, como estás? Espero que te encuentres muy bien hoy."
        )
        self.assertIsNone(language)


if __name__ == "__main__":
    unittest.main()
