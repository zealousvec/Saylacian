# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests the public core capabilities and shared application behavior."""

import unittest

from saylacian.core.capabilities import get_capability, list_capabilities
from saylacian.core.transliteration import detect_script, transliterate


class CoreTests(unittest.TestCase):
    def test_multigraphs(self):
        self.assertEqual(
            transliterate("dh sh kh aa ee oo", "Somali Latin", "Osmanya").text,
            "𐒊 𐒉 𐒅 𐒛 𐒜 𐒝",
        )

    def test_twelve_somali_osmanya_examples(self):
        examples = {
            "salaan": "𐒈𐒖𐒐𐒛𐒒",
            "Somali": "𐒈𐒙𐒑𐒖𐒐𐒘",
            "af soomaali": "𐒖𐒍 𐒈𐒝𐒑𐒛𐒐𐒘",
            "Waa nabad!": "𐒓𐒛 𐒒𐒖𐒁𐒖𐒆!",
            "dhul": "𐒊𐒚𐒐",
            "xaraf": "𐒄𐒖𐒇𐒖𐒍",
            "qalin": "𐒎𐒖𐒐𐒘𐒒",
            "caano": "𐒋𐒛𐒒𐒙",
            "shimbir": "𐒉𐒘𐒑𐒁𐒘𐒇",
            "Osmanya": "𐒙𐒈𐒑𐒖𐒒𐒕𐒖",
            "w iyo y": "𐒓 𐒘𐒕𐒙 𐒕",
            "ma aqaan?": "𐒑𐒖 𐒖𐒎𐒛𐒒?",
        }
        for source, expected in examples.items():
            with self.subTest(source=source):
                self.assertEqual(
                    transliterate(source, "Somali Latin", "Osmanya").text, expected
                )

    def test_no_invented_letters(self):
        r = transliterate("pvz", "Somali Latin", "Osmanya")
        self.assertEqual(r.text, "pvz")
        self.assertEqual(len(r.warnings), 3)

    def test_case_multigraph_warning(self):
        self.assertTrue(transliterate("DH", "Somali Latin", "Osmanya").warnings)

    def test_whitespace_punctuation(self):
        self.assertEqual(
            transliterate("b!\n  t?", "Somali Latin", "Osmanya").text, "𐒁!\n  𐒂?"
        )

    def test_ambiguous_reverse(self):
        r = transliterate("𐒓𐒕", "Osmanya", "Somali Latin")
        self.assertEqual(r.text, "wy")
        self.assertTrue(r.warnings)

    def test_round_trip_unambiguous(self):
        t = "dhagax!"
        self.assertEqual(
            transliterate(
                transliterate(t, "Somali Latin", "Osmanya").text,
                "Osmanya",
                "Somali Latin",
            ).text,
            t,
        )

    def test_unsupported_english(self):
        with self.assertRaises(ValueError):
            transliterate("hello", "English", "Osmanya")

    def test_unsupported_nubian(self):
        with self.assertRaises(ValueError):
            transliterate("text", "Nobiin", "Osmanya")

    def test_unsupported_modern_nubian_routes_stay_explicit(self):
        for source in ("Dongolawi / Andaandi (Nubian)",):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "no validated mapping"):
                    transliterate("text", source, "Somali Latin")

    def test_script_not_language_detection(self):
        self.assertEqual(detect_script("𐒁! ")[0], "Osmanya")
        self.assertIsNone(detect_script("bonjour")[0])
        self.assertIsNone(detect_script("a𐒁")[0])

    def test_old_nubian_script_detection(self):
        self.assertEqual(detect_script("ⲁⲃⲅ")[0], "Coptic script")

    def test_old_nubian_documented_table_cases(self):
        cases = {
            "ⲁⲃⲅⲇ": "abgd",
            "ⲉⲍⲏ": "ezē",
            "ⲑⲓⲕ": "thik",
            "ⲗⲙⲛ": "lmn",
            "ⲝⲟⲡ": "xop",
            "ⲣⲥⲧ": "rst",
            "ⲩⲫⲭ": "uphch",
            "ⲯⲱ": "psō",
            "ϣϥϩ": "shfh",
            "ϫϭϯ": "djkyti",
            "ⳟⳡⳣⳝ": "ngnywj",
            "ⲁ, ⲃ!\nϣ": "a, b!\nsh",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(
                    transliterate(
                        source, "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
                    ).text,
                    expected,
                )

    def test_old_nubian_reverse_and_ambiguity_notice(self):
        result = transliterate(
            "ng, ny! dj", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )
        self.assertEqual(result.text, "ⳟ, ⳡ! ϫ")
        self.assertTrue(result.warnings)
        self.assertIn("ⲛⲅ, ⳡ! ϫ", result.alternatives)
        self.assertIn("ⳟ, ⳡ! ⲇⳝ", result.alternatives)
        self.assertEqual(
            transliterate(
                "ou", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
            ).text,
            "ⳣ",
        )
        self.assertIn(
            "ⲟⲩ",
            transliterate(
                "ou", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
            ).alternatives,
        )

    def test_unlisted_coptic_letters_are_preserved_and_warned(self):
        result = transliterate(
            "Ⲳ!", "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
        )
        self.assertEqual(result.text, "Ⲳ!")
        self.assertTrue(result.warnings)

    def test_capability_registry_labels_specific_routes(self):
        routes = list_capabilities("transliteration")
        self.assertIn("Old Nubian (Coptic)", {route["source"] for route in routes})
        self.assertNotIn("Nobiin", {route["source"] for route in routes})
        borama_reference = next(
            route
            for route in routes
            if route.get("kind") == "script" and route.get("source") == "Borama"
        )
        self.assertIn("experimental", borama_reference["status"])
        self.assertIsNotNone(
            get_capability("Borama", "Somali Latin", "transliteration")
        )


if __name__ == "__main__":
    unittest.main()
