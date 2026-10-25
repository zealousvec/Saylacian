import unittest

from saylacian.core.transliteration import (
    OLD_NUBIAN_TO_LATIN,
    SCRIPT_DATA,
    SOMALI_TO_OSMANYA,
    transliterate,
)


class TransliterationTests(unittest.TestCase):
    def test_osmanya_shared_glyphs_show_both_readings(self):
        cases = (("w", "uu"), ("y", "ii"))
        for short_vowel, long_vowel in cases:
            with self.subTest(glyph_for=short_vowel):
                glyph = transliterate(short_vowel, "Somali Latin", "Osmanya").text
                reading = transliterate(glyph, "Osmanya", "Somali Latin")
                self.assertEqual(reading.text, short_vowel)
                self.assertIn(long_vowel, reading.alternatives)
                self.assertTrue(
                    any("Reverse ambiguity" in item for item in reading.warnings)
                )

    def test_osmanya_mixed_ambiguities_preserve_full_reading_options(self):
        source = "w y"
        glyphs = transliterate(source, "Somali Latin", "Osmanya").text
        reading = transliterate(glyphs, "Osmanya", "Somali Latin")
        self.assertEqual(reading.text, source)
        self.assertIn("uu y", reading.alternatives)
        self.assertIn("w ii", reading.alternatives)
        self.assertIn("uu ii", reading.alternatives)

    def test_osmanya_alternatives_are_bounded_for_long_input(self):
        glyph = transliterate("w", "Somali Latin", "Osmanya").text
        reading = transliterate(glyph * 4000, "Osmanya", "Somali Latin")
        self.assertEqual(len(reading.text), 4000)
        self.assertLessEqual(len(reading.alternatives), 11)
        self.assertTrue(
            all(4000 <= len(option) <= 8000 for option in reading.alternatives)
        )

    def test_every_chart_entry_round_trips_in_its_table_subset(self):
        for script, data in SCRIPT_DATA.items():
            for record in data["records"]:
                with self.subTest(script=script, grapheme=record["grapheme"]):
                    grapheme = record["grapheme"]
                    glyph = transliterate(grapheme, "Somali Latin", script).text
                    reading = transliterate(glyph, script, "Somali Latin")
                    self.assertEqual(reading.text, grapheme)

    def test_every_old_nubian_table_reading_keeps_its_source_as_an_option(self):
        for character, expected in OLD_NUBIAN_TO_LATIN.items():
            with self.subTest(character=character):
                reading = transliterate(
                    character,
                    "Old Nubian (Coptic)",
                    "Old Nubian scholarly Latin",
                )
                self.assertEqual(reading.text, expected)
                reverse = transliterate(
                    reading.text,
                    "Old Nubian scholarly Latin",
                    "Old Nubian (Coptic)",
                )
                self.assertIn(character, (reverse.text, *reverse.alternatives))

    def test_every_unique_osmanya_mapping_can_be_read_back(self):
        for grapheme, glyph in SOMALI_TO_OSMANYA.items():
            with self.subTest(grapheme=grapheme):
                reading = transliterate(glyph, "Osmanya", "Somali Latin")
                self.assertIn(grapheme, (reading.text, *reading.alternatives))


if __name__ == "__main__":
    unittest.main()
