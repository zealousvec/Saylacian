import hashlib
import json
import unicodedata
import unittest

from saylacian.core.capabilities import get_capability
from saylacian.core.old_nubian_reader import (
    CONVENTION,
    FORMAT,
    LEGACY_CONVENTION,
    LEGACY_SOURCE_URL,
    PHONETIC_VALUES,
    SOURCE_URL,
    alphabet_entries,
    describe_combining_marks,
    export_reading_record,
    import_reading_record,
    make_reading_record,
)
from saylacian.core.transliteration import (
    OLD_NUBIAN_TO_LATIN,
    SCRIPT_DATA,
    SOMALI_TO_OSMANYA,
    detect_script,
    transliterate,
)


class TransliterationTests(unittest.TestCase):
    def test_osmanya_decimal_digits_round_trip(self):
        latin = "0123456789"

        encoded = transliterate(latin, "Somali Latin", "Osmanya")
        decoded = transliterate(encoded.text, "Osmanya", "Somali Latin")

        expected_digits = "".join(
            chr(codepoint) for codepoint in range(0x104A0, 0x104AA)
        )
        self.assertEqual(encoded.text, expected_digits)
        self.assertEqual(
            [unicodedata.digit(character) for character in encoded.text],
            list(range(10)),
        )
        self.assertEqual(decoded.text, latin)
        self.assertFalse(decoded.alternatives)
        self.assertFalse(encoded.warnings)

        other_numerals = "١२"
        preserved = transliterate(other_numerals, "Somali Latin", "Osmanya")
        self.assertEqual(preserved.text, other_numerals)

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

    def test_osmanya_macron_vowels_use_long_vowel_letters(self):
        for macron, doubled in (
            ("ā", "aa"),
            ("ē", "ee"),
            ("ī", "ii"),
            ("ō", "oo"),
            ("ū", "uu"),
        ):
            forms = (
                macron,
                macron.upper(),
                unicodedata.normalize("NFD", macron),
            )
            for source in forms:
                with self.subTest(source=source):
                    converted = transliterate(source, "Somali Latin", "Osmanya")
                    doubled_result = transliterate(doubled, "Somali Latin", "Osmanya")

                    self.assertEqual(converted.text, doubled_result.text)
                    self.assertFalse(
                        any("Unmapped input" in item for item in converted.warnings)
                    )
                    self.assertTrue(
                        any(
                            "read back as doubled Latin vowels" in item
                            for item in converted.warnings
                        )
                    )
                    decoded = transliterate(converted.text, "Osmanya", "Somali Latin")
                    if doubled in {"ii", "uu"}:
                        self.assertIn(doubled, decoded.alternatives)
                    else:
                        self.assertEqual(decoded.text, doubled)

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
        expected_local_readings = tuple(
            "w" * position + "uu" + "w" * (3999 - position) for position in range(11)
        )
        self.assertEqual(reading.alternatives, expected_local_readings)

    def test_every_chart_entry_round_trips_in_its_table_subset(self):
        for script, data in SCRIPT_DATA.items():
            for record in data["records"]:
                with self.subTest(script=script, grapheme=record["grapheme"]):
                    grapheme = record["grapheme"]
                    glyph = transliterate(grapheme, "Somali Latin", script).text
                    reading = transliterate(glyph, script, "Somali Latin")
                    self.assertEqual(reading.text, grapheme)

    def test_chart_data_has_unique_slots_and_valid_alias_targets(self):
        for script, data in SCRIPT_DATA.items():
            with self.subTest(script=script):
                records = data["records"]
                graphemes = [item["grapheme"] for item in records]
                private_slots = [item["pua"] for item in records]
                aliases = data.get("aliases", ())

                self.assertEqual(len(graphemes), len(set(graphemes)))
                self.assertEqual(len(private_slots), len(set(private_slots)))
                self.assertTrue(all(item["canonical"] in graphemes for item in aliases))
                self.assertTrue(
                    all(item["grapheme"] not in graphemes for item in aliases)
                )
                if script == "Kaddare":
                    case_slots = [
                        item[key]
                        for item in records
                        for key in ("uppercase_pua", "lowercase_pua")
                    ]
                    self.assertEqual(len(case_slots), len(set(case_slots)))
                    self.assertFalse(set(private_slots) & set(case_slots))

                for slot in private_slots + (case_slots if script == "Kaddare" else []):
                    codepoint = int(slot.removeprefix("U+"), 16)
                    self.assertTrue(0xE000 <= codepoint <= 0xF8FF)

    def test_somali_scripts_preserve_mixed_punctuation_and_whitespace(self):
        source = "qurux\tbadan, 123!\r\n"

        for script in ("Osmanya", "Borama", "Kaddare"):
            with self.subTest(script=script):
                encoded = transliterate(source, "Somali Latin", script)
                decoded = transliterate(encoded.text, script, "Somali Latin")

                self.assertEqual(decoded.text, source)

    def test_somali_script_case_loss_and_unmapped_letters_are_reported(self):
        expected_readings = {
            "Osmanya": "qurux V!",
            "Borama": "quruX V!",
            "Kaddare": "QURUX V!",
        }

        for script, expected in expected_readings.items():
            with self.subTest(script=script):
                converted = transliterate("QURUX V!", "Somali Latin", script)
                reading = transliterate(converted.text, script, "Somali Latin")

                self.assertEqual(reading.text, expected)
                if script == "Kaddare":
                    self.assertFalse(
                        any(
                            "Capitalization" in warning
                            for warning in converted.warnings
                        )
                    )
                else:
                    self.assertTrue(
                        any(
                            "Capitalization" in warning
                            for warning in converted.warnings
                        )
                    )
                self.assertTrue(
                    any("Unmapped" in warning for warning in converted.warnings)
                )

    def test_kaddare_uses_lowercase_cursive_and_separate_uppercase_slots(self):
        source = "KAddare KH QURUX"
        encoded = transliterate(source, "Somali Latin", "Kaddare")
        decoded = transliterate(encoded.text, "Kaddare", "Somali Latin")

        self.assertEqual(decoded.text, source)
        self.assertFalse(
            any("Capitalization" in warning for warning in encoded.warnings)
        )
        self.assertIn(
            "Saylacian shows Kaddare lowercase forms separately; it does not join cursive writing.",
            encoded.warnings,
        )
        self.assertNotEqual(
            transliterate("a", "Somali Latin", "Kaddare").text,
            transliterate("A", "Somali Latin", "Kaddare").text,
        )

    def test_kaddare_joining_note_only_appears_when_lowercase_forms_are_used(self):
        lowercase = transliterate("abc", "Somali Latin", "Kaddare")
        uppercase = transliterate("ABC", "Somali Latin", "Kaddare")
        note = (
            "Saylacian shows Kaddare lowercase forms separately; "
            "it does not join cursive writing."
        )

        self.assertIn(note, lowercase.warnings)
        self.assertNotIn(note, uppercase.warnings)

    def test_kaddare_macron_vowels_use_the_doubled_long_vowel_form(self):
        for marked, doubled in (
            ("ā", "aa"),
            ("ē", "ee"),
            ("ī", "ii"),
            ("ō", "oo"),
            ("ū", "uu"),
        ):
            for source, expected in (
                (marked, doubled),
                (marked.upper(), doubled.upper()),
                (unicodedata.normalize("NFD", marked), doubled),
            ):
                with self.subTest(source=source):
                    encoded = transliterate(source, "Somali Latin", "Kaddare")
                    self.assertEqual(len(encoded.text), 2)
                    self.assertFalse(
                        any("Unmapped" in warning for warning in encoded.warnings)
                    )
                    decoded = transliterate(encoded.text, "Kaddare", "Somali Latin")
                    self.assertEqual(decoded.text, expected)

    def test_kaddare_warns_when_multiletter_grapheme_case_cannot_round_trip(self):
        cases = (("Dh", "DH"), ("dH", "dh"))

        for source, expected_reading in cases:
            with self.subTest(source=source):
                encoded = transliterate(source, "Somali Latin", "Kaddare")
                decoded = transliterate(encoded.text, "Kaddare", "Somali Latin")

                self.assertEqual(decoded.text, expected_reading)
                self.assertTrue(
                    any(
                        "cannot preserve titlecase or mixed case" in warning
                        for warning in encoded.warnings
                    )
                )

        all_lowercase = transliterate("dh", "Somali Latin", "Kaddare")
        all_uppercase = transliterate("DH", "Somali Latin", "Kaddare")
        self.assertFalse(
            any(
                "cannot preserve titlecase or mixed case" in warning
                for warning in all_lowercase.warnings + all_uppercase.warnings
            )
        )

    def test_kaddare_legacy_chart_slots_remain_readable(self):
        for record in SCRIPT_DATA["Kaddare"]["records"]:
            with self.subTest(grapheme=record["grapheme"]):
                legacy_glyph = chr(int("0x" + record["pua"][2:], 0))
                reading = transliterate(legacy_glyph, "Kaddare", "Somali Latin")
                self.assertEqual(reading.text, record["grapheme"])

    def test_kaddare_font_contains_distinct_case_forms_for_every_chart_entry(self):
        from PIL import ImageFont

        font = ImageFont.truetype("assets/KaddareChart-Regular.ttf", 48)
        for record in SCRIPT_DATA["Kaddare"]["records"]:
            with self.subTest(grapheme=record["grapheme"]):
                lower = chr(int("0x" + record["lowercase_pua"][2:], 0))
                upper = chr(int("0x" + record["uppercase_pua"][2:], 0))
                self.assertNotEqual(font.getmask(lower).getbbox(), None)
                self.assertNotEqual(font.getmask(upper).getbbox(), None)
                lower_mask = font.getmask(lower)
                upper_mask = font.getmask(upper)
                self.assertNotEqual(
                    (lower_mask.size, tuple(lower_mask)),
                    (upper_mask.size, tuple(upper_mask)),
                )

    def test_unsupported_letters_are_preserved_while_supported_letters_convert(self):
        cases = (
            ("Somali Latin", "Osmanya", "qv", "v"),
            ("Somali Latin", "Borama", "qx", "x"),
        )

        for source, target, text, unsupported in cases:
            with self.subTest(target=target):
                result = transliterate(text, source, target)
                supported = transliterate(text[0], source, target).text

                self.assertEqual(result.text, supported + unsupported)
                self.assertTrue(
                    any(unsupported in warning for warning in result.warnings)
                )

    def test_borama_chart_omissions_are_not_guessed(self):
        result = transliterate("xp vz", "Somali Latin", "Borama")

        self.assertEqual(result.text, "xp vz")
        self.assertIn("Unmapped letters preserved: x p v z.", result.warnings)

    def test_borama_q_uses_the_chart_glyph_and_o_uses_the_shared_u_sign(self):
        record = next(
            item for item in SCRIPT_DATA["Borama"]["records"] if item["grapheme"] == "q"
        )
        glyph = transliterate("q", "Somali Latin", "Borama").text

        self.assertEqual(record["pua"], f"U+{ord(glyph):04X}")
        self.assertEqual(transliterate(glyph, "Borama", "Somali Latin").text, "q")
        result = transliterate("o", "Somali Latin", "Borama")
        u_glyph = transliterate("u", "Somali Latin", "Borama").text
        self.assertEqual(result.text, u_glyph)
        self.assertTrue(any("short o/u" in w for w in result.warnings))
        reading = transliterate(result.text, "Borama", "Somali Latin")
        self.assertEqual(reading.text, "u")
        self.assertIn("o", reading.alternatives)

    def test_borama_macron_vowels_use_existing_chart_labels(self):
        for macron, doubled in (
            ("ā", "aa"),
            ("ē", "ee"),
            ("ī", "ii"),
            ("ō", "oo"),
            ("ū", "uu"),
        ):
            for source in (
                macron,
                macron.upper(),
                unicodedata.normalize("NFD", macron),
            ):
                with self.subTest(source=source):
                    converted = transliterate(source, "Somali Latin", "Borama")
                    doubled_result = transliterate(doubled, "Somali Latin", "Borama")

                    self.assertEqual(converted.text, doubled_result.text)
                    self.assertFalse(
                        any(
                            "Unmapped letters preserved" in item
                            for item in converted.warnings
                        )
                    )
                    if doubled in {"aa", "ee"}:
                        self.assertTrue(
                            any(
                                "Borama shares chart signs" in item
                                for item in converted.warnings
                            )
                        )

    def test_borama_vowel_aliases_reuse_chart_glyphs_and_report_reading_loss(self):
        cases = (("aa", "a"), ("ee", "e"), ("o", "u"))

        for alias, canonical in cases:
            with self.subTest(alias=alias):
                alias_glyph = transliterate(alias, "Somali Latin", "Borama")
                canonical_glyph = transliterate(canonical, "Somali Latin", "Borama")

                self.assertEqual(alias_glyph.text, canonical_glyph.text)
                self.assertTrue(
                    any("short o/u" in warning for warning in alias_glyph.warnings)
                )
                reading = transliterate(alias_glyph.text, "Borama", "Somali Latin")
                self.assertEqual(reading.text, canonical)
                self.assertIn(alias, reading.alternatives)

    def test_borama_ambiguous_vowel_readings_are_bounded_and_local_first(self):
        glyphs = transliterate("a e u", "Somali Latin", "Borama").text
        reading = transliterate(glyphs, "Borama", "Somali Latin")

        self.assertEqual(reading.text, "a e u")
        self.assertIn("aa e u", reading.alternatives)
        self.assertIn("a ee u", reading.alternatives)
        self.assertIn("a e o", reading.alternatives)
        self.assertLessEqual(len(reading.alternatives), 12)

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

    def test_repeated_unknown_chart_glyph_has_one_warning(self):
        glyph = chr(0xE200)
        result = transliterate(glyph * 20_000, "Borama", "Somali Latin")

        self.assertEqual(result.text, glyph * 20_000)
        self.assertEqual(
            result.warnings.count("No Borama chart entry for U+E200; preserved."),
            1,
        )

    def test_repeated_unmapped_chart_letter_is_collected_once(self):
        result = transliterate("p" * 20_000, "Somali Latin", "Kaddare")

        self.assertEqual(len(result.text), 20_000)
        self.assertTrue(result.text.isalpha())
        self.assertIn("Unmapped letters preserved: p.", result.warnings)

    def test_every_old_nubian_table_reading_keeps_its_source_as_an_option(self):
        self.assertEqual(len(alphabet_entries()), 29)
        self.assertEqual(set(PHONETIC_VALUES), set(OLD_NUBIAN_TO_LATIN))
        self.assertEqual(
            next(item for item in alphabet_entries("ⳟ") if item["glyph"] == "ⳟ")[
                "phonetic_values"
            ],
            ("ŋ",),
        )
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

    def test_old_nubian_w_glyph_uses_the_open_table_reading(self):
        reading = transliterate(
            "ⳣ", "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
        )
        self.assertEqual(reading.text, "w")
        self.assertFalse(reading.alternatives)
        entry = next(item for item in alphabet_entries() if item["glyph"] == "ⳣ")
        self.assertEqual(entry["alternative_readings"], ())
        self.assertEqual(entry["phonetic_values"], ("w",))

    def test_old_nubian_digraphs_show_published_phonetic_readings(self):
        cases = (
            ("ⲉⲓ", "ei", ("i", "iː", "j")),
            ("ⲟⲩ", "ou", ("u", "uː", "w", "wu")),
        )

        for source, primary, alternatives in cases:
            with self.subTest(source=source):
                reading = transliterate(
                    source,
                    "Old Nubian (Coptic)",
                    "Old Nubian scholarly Latin",
                )

                self.assertEqual(reading.text, primary)
                for alternative in alternatives:
                    self.assertIn(alternative, reading.alternatives)
                self.assertTrue(
                    any(
                        "digraphs have multiple published" in warning
                        for warning in reading.warnings
                    )
                )

    def test_old_nubian_digraph_readings_preserve_case_and_context(self):
        reading = transliterate(
            "ⲈⲒⲛ ⲟⲩⲣ",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertEqual(reading.text, "EIn our")
        self.assertIn("In our", reading.alternatives)
        self.assertIn("Iːn our", reading.alternatives)
        self.assertIn("Jn our", reading.alternatives)

    def test_old_nubian_digraph_ending_before_supralinear_stroke_is_not_grouped(self):
        reading = transliterate(
            "ⲉⲓ\u0304",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertEqual(reading.text, "ei\u0304")
        self.assertFalse(
            any(
                "digraphs have multiple published" in warning
                for warning in reading.warnings
            )
        )

    def test_old_nubian_lists_readings_from_a_second_scholarly_table(self):
        cases = (
            ("ⲭ", "kh"),
            ("ϣ", "š"),
            ("ⳟ", "ŋ"),
            ("ⳡ", "ñ"),
        )
        for glyph, primary in cases:
            with self.subTest(glyph=glyph):
                reading = transliterate(
                    glyph, "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
                )
                self.assertEqual(reading.text, primary)
                self.assertFalse(reading.alternatives)
                reverse = transliterate(
                    primary, "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
                )
                self.assertEqual(reverse.text, glyph)

    def test_old_nubian_characters_outside_the_open_29_entry_table_are_flagged(self):
        for glyph in ("ϥ", "ϩ", "ϫ", "ϭ", "ϯ"):
            with self.subTest(glyph=glyph):
                reading = transliterate(
                    glyph, "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
                )
                self.assertEqual(reading.text, glyph)
                self.assertTrue(
                    any(
                        "No verified table entry" in warning
                        for warning in reading.warnings
                    )
                )
                self.assertEqual(detect_script(glyph)[0], "Coptic script")

    def test_old_nubian_vowels_show_published_phonetic_alternatives(self):
        cases = (
            ("ⲏ", "ē", ("i", "iː")),
            ("ⲩ", "u", ("i",)),
        )
        for glyph, primary, alternatives in cases:
            with self.subTest(glyph=glyph):
                reading = transliterate(
                    glyph, "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
                )
                self.assertEqual(reading.text, primary)
                for alternative in alternatives:
                    self.assertIn(alternative, reading.alternatives)

    def test_script_detection_recognizes_old_nubian_specific_letters(self):
        for text in ("ⳝ", "ⳟⳡ", "ⳣ", "ⳜⳞⳠⳢ"):
            with self.subTest(text=text):
                script, message = detect_script(text)
                self.assertEqual(script, "Old Nubian (Coptic)")
                self.assertIn("language is not inferred", message)

    def test_script_detection_keeps_common_coptic_letters_generic(self):
        script, message = detect_script("ⲁⲃⲅ")

        self.assertEqual(script, "Coptic script")
        self.assertIn("language is not inferred", message)

    def test_detected_old_nubian_route_converts_using_verified_mapping(self):
        source, message = detect_script("ⳝⲁⳣ")
        capability = get_capability(
            source,
            "Old Nubian scholarly Latin",
            "transliteration",
        )
        result = transliterate(
            "ⳝⲁⳣ",
            source,
            "Old Nubian scholarly Latin",
        )

        self.assertIsNotNone(capability)
        self.assertEqual(result.text, "jaw")
        self.assertIn("language is not inferred", message)

    def test_old_nubian_keeps_case_spaces_and_punctuation(self):
        reading = transliterate(
            "Ⲁ ⳣ, ⳝ!",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )
        self.assertEqual(reading.text, "A w, j!")

    def test_old_nubian_preserves_and_flags_combining_diacritics(self):
        source = "ⲁ\u0301"

        reading = transliterate(
            source,
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertEqual(reading.text, "a\u0301")
        self.assertTrue(
            any(
                "Other combining marks are preserved" in item
                for item in reading.warnings
            )
        )

    def test_old_nubian_supralinear_stroke_offers_i_reading(self):
        source = "ⲧⲗ\u0304ⲗⲛ\u0304"

        reading = transliterate(
            source,
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertEqual(reading.text, "tl\u0304ln\u0304")
        self.assertIn("tillin", reading.alternatives)
        self.assertTrue(
            any("mark a numeral" in warning for warning in reading.warnings)
        )

    def test_old_nubian_dot_mark_is_preserved_without_an_i_reading(self):
        reading = transliterate(
            "ⲁ\u0307",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertEqual(reading.text, "a\u0307")
        self.assertFalse(reading.alternatives)
        self.assertTrue(
            any("Other combining marks are preserved" in w for w in reading.warnings)
        )

    def test_old_nubian_mixed_marks_explain_only_uninterpreted_marks(self):
        reading = transliterate(
            "ⲁ\u0304ⲃ\u0307",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertNotIn("ia\u0304b\u0307", reading.alternatives)
        self.assertTrue(
            any("Other combining marks are preserved" in w for w in reading.warnings)
        )

    def test_old_nubian_vowel_stroke_can_insert_i_before_preceding_n(self):
        cases = {"ⲗ": "l", "ⲛ": "n", "ⲣ": "r", "ⳝ": "j"}
        for character, reading in cases.items():
            with self.subTest(character=character):
                result = transliterate(
                    character + "ⲁ\u0304",
                    "Old Nubian (Coptic)",
                    "Old Nubian scholarly Latin",
                )
                self.assertIn("i" + reading + "a\u0304", result.alternatives)

        published_example = transliterate(
            "ⲟⲕⲧⲁⲕⲛⲁ\u0304",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )
        self.assertEqual(published_example.text, "oktakna\u0304")
        self.assertIn("oktakina\u0304", published_example.alternatives)
        uncontextualized = transliterate(
            "ⲁ\u0304",
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )
        self.assertFalse(
            any(
                candidate.startswith("i") for candidate in uncontextualized.alternatives
            )
        )

    def test_old_nubian_mark_description_distinguishes_stroke_and_dot(self):
        details = describe_combining_marks("ⲗ\u0304 ⲃ\u0307")

        self.assertIn("i-insertion before ⲗ is available", details)
        self.assertIn("does not convert", details)
        self.assertIn("preserved without interpretation", details)

    def test_old_nubian_stroke_readings_are_bounded_and_report_truncation(self):
        source = "ⲗ\u0304" * 8

        reading = transliterate(
            source,
            "Old Nubian (Coptic)",
            "Old Nubian scholarly Latin",
        )

        self.assertLessEqual(len(reading.alternatives), 12)
        self.assertTrue(
            any(
                "Only some alternative readings are shown" in w
                for w in reading.warnings
            )
        )

    def test_old_nubian_reader_keeps_alternative_after_record_round_trip(self):
        record = make_reading_record("ⲏ")
        self.assertIn("i", record.alternatives)
        restored = import_reading_record(export_reading_record(record))
        self.assertIn("i", restored.alternatives)

    def test_legacy_old_nubian_record_imports_with_current_reading(self):
        body = {
            "format": FORMAT,
            "version": 1,
            "original": "ⳣ",
            "latin": "ou",
            "convention": LEGACY_CONVENTION,
            "source_url": LEGACY_SOURCE_URL,
            "warnings": [],
        }
        canonical = json.dumps(
            body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        payload = json.dumps(
            {
                **body,
                "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            },
            ensure_ascii=False,
        )

        record = import_reading_record(payload)

        self.assertEqual(record.latin, "w")
        self.assertEqual(record.convention, CONVENTION)
        self.assertEqual(record.source_url, SOURCE_URL)
        self.assertTrue(
            any("updated to the current cited table" in w for w in record.warnings)
        )

    def test_old_nubian_reader_exposes_stroke_reading_alternative(self):
        record = make_reading_record("ⲧⲗ\u0304ⲗⲛ\u0304")

        self.assertEqual(record.latin, "tl\u0304ln\u0304")
        self.assertIn("tillin", record.alternatives)
        restored = import_reading_record(export_reading_record(record))
        self.assertIn("tillin", restored.alternatives)

    def test_old_nubian_only_warns_for_sequences_with_a_real_alternative(self):
        unique_sequences = ("kh", "š", "ŋ", "ñ")
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
            "ou", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )
        self.assertTrue(ambiguous.alternatives)
        self.assertTrue(
            any("letter boundaries can be ambiguous" in w for w in ambiguous.warnings)
        )
        self.assertIn("ⳣ", ambiguous.alternatives)

    def test_old_nubian_preserves_unmapped_latin_and_keeps_other_readings(self):
        result = transliterate(
            "ŋ v", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )

        self.assertEqual(result.text, "ⳟ v")
        self.assertTrue(
            any(
                "Unmapped Latin letters preserved: v." in item
                for item in result.warnings
            )
        )

    def test_old_nubian_mixed_script_does_not_call_coptic_latin(self):
        result = transliterate(
            "ŋ V—ⲁ", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )

        self.assertEqual(result.text, "ⳟ V—ⲁ")
        self.assertTrue(
            any(
                "Unmapped Latin letters preserved: V." in item
                for item in result.warnings
            )
        )
        self.assertFalse(any("ⲁ" in item for item in result.warnings))

    def test_old_nubian_case_round_trip_keeps_coptic_letter_case(self):
        latin = transliterate("Ⲃⲁ", "Old Nubian (Coptic)", "Old Nubian scholarly Latin")
        coptic = transliterate(
            latin.text, "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )

        self.assertEqual(latin.text, "Ba")
        self.assertEqual(coptic.text, "Ⲃⲁ")

    def test_old_nubian_reverse_accepts_decomposed_macron_vowel(self):
        composed = transliterate(
            "ē", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )
        decomposed = transliterate(
            "e\u0304", "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        )

        self.assertEqual(decomposed, composed)
        self.assertEqual(decomposed.text, "ⲏ")

    def test_old_nubian_flags_truncated_alternative_lists(self):
        source = "ou ou ou ou ou"
        result = transliterate(
            source,
            "Old Nubian scholarly Latin",
            "Old Nubian (Coptic)",
        )

        self.assertEqual(len(result.alternatives), 12)
        self.assertIn("ⳣ" + result.text[2:], result.alternatives)
        self.assertIn(result.text[:-2] + "ⳣ", result.alternatives)
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
