# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import unittest

from saylacian.core.old_nubian_reader import (
    FORMAT,
    alphabet_entries,
    export_reading_record,
    import_reading_record,
    make_reading_record,
)


class OldNubianReaderTests(unittest.TestCase):
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
