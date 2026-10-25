import unittest

from saylacian.core.old_nubian_reader import (
    alphabet_entries,
    export_reading_record,
    import_reading_record,
    make_reading_record,
)
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
        self.assertTrue(
            any(
                "Only some alternative readings are shown" in item
                for item in reading.warnings
            )
        )

    def test_every_chart_entry_round_trips_in_its_table_subset(self):
        for script, data in SCRIPT_DATA.items():
            for record in data["records"]:
                with self.subTest(script=script, grapheme=record["grapheme"]):
                    grapheme = record["grapheme"]
                    glyph = transliterate(grapheme, "Somali Latin", script).text
                    reading = transliterate(glyph, script, "Somali Latin")
                    self.assertEqual(reading.text, grapheme)

    def test_unmapped_private_use_glyphs_are_preserved_and_flagged(self):
        glyphs = "".join(chr(codepoint) for codepoint in (0xE200, 0xF0000, 0x100000))
        for script in ("Borama", "Kaddare"):
            result = transliterate(glyphs, script, "Somali Latin")
            with self.subTest(script=script):
                self.assertEqual(result.text, glyphs)
            for codepoint in (0xE200, 0xF0000, 0x100000):
                with self.subTest(script=script, codepoint=f"U+{codepoint:04X}"):
                    self.assertIn(
                        f"No {script} chart entry for U+{codepoint:04X}; preserved.",
                        result.warnings,
                    )

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

    def test_old_nubian_w_glyph_shows_both_cited_readings(self):
        reading = transliterate(
            "ⳣ", "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
        )
        self.assertEqual(reading.text, "w")
        self.assertIn("ou", reading.alternatives)
        entry = next(item for item in alphabet_entries() if item["glyph"] == "ⳣ")
        self.assertEqual(entry["alternative_readings"], ("ou",))

    def test_old_nubian_keeps_case_spaces_and_punctuation(self):
        reading = transliterate(
            "Ⲁ ⳣ, Ϯ!",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )
        self.assertEqual(reading.text, "A w, TI!")
        self.assertIn("A ou, TI!", reading.alternatives)

    def test_old_nubian_preserves_and_flags_combining_diacritics(self):
        source = "ⲁ\u0301"

        reading = transliterate(
            source,
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertEqual(reading.text, "a\u0301")
        self.assertTrue(
            any("Combining marks are preserved" in item for item in reading.warnings)
        )

    def test_old_nubian_reader_keeps_alternative_after_record_round_trip(self):
        record = make_reading_record("ⳣ")
        self.assertIn("ou", record.alternatives)
        restored = import_reading_record(export_reading_record(record))
        self.assertIn("ou", restored.alternatives)

    def test_old_nubian_only_warns_for_sequences_with_a_real_alternative(self):
        unique_sequences = ("ch", "ky", "ny")
        for text in unique_sequences:
            with self.subTest(text=text):
                result = transliterate(
                    text, "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
                )
                self.assertFalse(result.alternatives)
                self.assertFalse(
                    any(
                        "letter boundaries can be ambiguous" in w
                        for w in result.warnings
                    )
                )

        ambiguous = transliterate(
            "ng", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )
        self.assertTrue(ambiguous.alternatives)
        self.assertTrue(
            any("letter boundaries can be ambiguous" in w for w in ambiguous.warnings)
        )

    def test_old_nubian_preserves_unmapped_latin_and_keeps_other_readings(self):
        result = transliterate(
            "ng v", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )

        self.assertEqual(result.text, "ⳟ v")
        self.assertIn("ⲛⲅ v", result.alternatives)
        self.assertTrue(
            any(
                "Unmapped Latin letters preserved: v." in item
                for item in result.warnings
            )
        )

    def test_old_nubian_flags_truncated_alternative_lists(self):
        result = transliterate(
            "ng ng ng ng ng",
            "Old Nubian scholarly Latin",
            "Old Nubian (Coptic)",
        )

        self.assertEqual(len(result.alternatives), 11)
        self.assertTrue(
            any(
                "Only some alternative readings are shown" in item
                for item in result.warnings
            )
        )

    def test_every_unique_osmanya_mapping_can_be_read_back(self):
        for grapheme, glyph in SOMALI_TO_OSMANYA.items():
            with self.subTest(grapheme=grapheme):
                reading = transliterate(glyph, "Osmanya", "Somali Latin")
                self.assertIn(grapheme, (reading.text, *reading.alternatives))


if __name__ == "__main__":
    unittest.main()
