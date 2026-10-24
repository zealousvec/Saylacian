# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import unittest

from saylacian.core.old_nubian_reader import (
    FORMAT,
    alphabet_entries,
    describe_combining_marks,
    export_reading_record,
    import_reading_record,
    make_reading_record,
)


class OldNubianReaderTests(unittest.TestCase):
    def test_mark_details_name_marks_and_show_original_code_point_positions(self):
        self.assertEqual(
            describe_combining_marks("ⲁ⳯⳰⳱"),
            "Display note only; no reading rule applied. "
            "U+2CEF COPTIC COMBINING NI ABOVE (code point 2); "
            "U+2CF0 COPTIC COMBINING SPIRITUS ASPER (code point 3); "
            "U+2CF1 COPTIC COMBINING SPIRITUS LENIS (code point 4)",
        )

    def test_mark_details_are_empty_without_combining_marks(self):
        self.assertEqual(describe_combining_marks("ⲁab!"), "")

    def test_mark_details_limit_long_runs(self):
        details = describe_combining_marks("ⲁ" + "⳯" * 8, limit=2)
        self.assertIn("code point 2", details)
        self.assertIn("code point 3", details)
        self.assertIn("and 6 more", details)
        self.assertNotIn("code point 4", details)

    def test_mark_details_reject_invalid_limit(self):
        with self.assertRaises(ValueError):
            describe_combining_marks("⳯", limit=0)

    def test_alphabet_is_limited_to_cited_entries_and_searchable(self):
        entries = alphabet_entries()
        self.assertEqual(len(entries), 34)
        ngi = alphabet_entries("2cdf")
        self.assertEqual(len(ngi), 1)
        self.assertEqual((ngi[0]["glyph"], ngi[0]["reading"]), ("ⳟ", "ng"))
        self.assertEqual(
            ngi[0]["confidence"], "Listed in cited table; not independently reviewed"
        )
        self.assertEqual(alphabet_entries("not-a-letter"), ())

    def test_reader_pairs_lines_and_preserves_original_exactly(self):
        original = "ⲙⲏⲛⲁ\nⳟⳡⳣ\n"
        record = make_reading_record(original)
        self.assertEqual(record.original, original)
        self.assertEqual(record.latin, "mēna\nngnyw\n")
        self.assertEqual(record.lines, (("ⲙⲏⲛⲁ\n", "mēna\n"), ("ⳟⳡⳣ\n", "ngnyw\n")))

    def test_versioned_record_roundtrips_and_checksum_detects_edits(self):
        payload = export_reading_record(make_reading_record("ⲁ\nⲃ"))
        restored = import_reading_record(payload)
        self.assertEqual((restored.original, restored.latin), ("ⲁ\nⲃ", "a\nb"))
        envelope = json.loads(payload)
        self.assertEqual(envelope["format"], FORMAT)
        envelope["latin"] = "invented"
        with self.assertRaisesRegex(ValueError, "checksum"):
            import_reading_record(json.dumps(envelope))

    def test_record_rejects_unknown_schema_and_empty_text(self):
        with self.assertRaisesRegex(ValueError, "Enter Old Nubian"):
            make_reading_record("  \n")
        with self.assertRaisesRegex(ValueError, "not recognized"):
            import_reading_record('{"format":"future"}')
        with self.assertRaisesRegex(ValueError, "invalid Unicode"):
            import_reading_record("\ud800")
        with self.assertRaisesRegex(TypeError, "must be text"):
            import_reading_record(None)


if __name__ == "__main__":
    unittest.main()
