# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests language and script detection."""

import unittest

from saylacian.core.language_detection import detect_language


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

    def test_abstains_on_unsupported_language(self):
        language, _, _ = detect_language(
            "Ola, como estás? Espero que te encuentres muy bien hoy."
        )
        self.assertIsNone(language)


if __name__ == "__main__":
    unittest.main()
