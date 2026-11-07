# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check source-preserving parsing and leakage guards for TICO-19 splits."""

import io
import unittest

from tools.translation_lab.tico19_benchmark import audit_exact_overlap
from tools.translation_lab.tico19_benchmark import paired_sentence_chrf
from tools.translation_lab.tico19_benchmark import parse_tsv


class Tico19BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.header = (
            "sourceLang\ttargetLang\tsourceString\ttargetString\tstringID"
            "\turl\tlicense\ttranslator_ID\n"
        )

    def test_parser_keeps_row_license_and_provenance(self):
        content = (
            self.header + "en\tso\tGood morning.\tSubax wanaagsan.\tID-1"
            "\thttps://example.org\tCC_BY-SA_3.0\ttranslator-4\n"
        )

        rows = parse_tsv(io.BytesIO(content.encode("utf-8")))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_text"], "Good morning.")
        self.assertEqual(rows[0]["target_text"], "Subax wanaagsan.")
        self.assertEqual(rows[0]["license"], "CC_BY-SA_3.0")
        self.assertEqual(rows[0]["source_url"], "https://example.org")

    def test_parser_rejects_language_mismatch(self):
        content = (
            self.header + "en\tfr\tGood morning.\tBonjour.\tID-1"
            "\thttps://example.org\tCC BY 4.0\ttranslator-4\n"
        )

        with self.assertRaisesRegex(ValueError, "language pair"):
            parse_tsv(io.BytesIO(content.encode("utf-8")))

    def test_parser_rejects_duplicate_ids(self):
        row = (
            "en\tso\tGood morning.\tSubax wanaagsan.\tID-1"
            "\thttps://example.org\tpublic\ttranslator-4\n"
        )
        content = self.header + row + row

        with self.assertRaisesRegex(ValueError, "Duplicate TICO-19"):
            parse_tsv(io.BytesIO(content.encode("utf-8")))

    def test_overlap_audit_counts_source_target_and_pair_separately(self):
        evaluated = [
            {"source_text": "Good morning.", "target_text": "Subax wanaagsan."},
            {"source_text": "Thank you.", "target_text": "Mahadsanid."},
        ]
        training = [
            {"source_text": " GOOD   MORNING. ", "target_text": "Other text."},
            {"source_text": "Another source.", "target_text": "Mahadsanid."},
        ]

        result = audit_exact_overlap(evaluated, training)

        self.assertEqual(result["exact_pair_overlap"], 0)
        self.assertEqual(result["exact_english_overlap"], 1)
        self.assertEqual(result["exact_somali_overlap"], 1)

    def test_paired_sentence_analysis_is_seeded_and_counts_wins(self):
        references = ["hello world", "good day", "thank you"]
        base = ["hello world", "other words", "thanks"]
        candidate = ["hello world", "good day", "unrelated"]

        result = paired_sentence_chrf(
            references,
            base,
            candidate,
            bootstrap_samples=200,
            seed=17,
        )

        self.assertEqual(result["n"], 3)
        self.assertEqual(result["candidate_wins"], 1)
        self.assertEqual(result["base_wins"], 1)
        self.assertEqual(result["ties"], 1)
        self.assertEqual(
            result,
            paired_sentence_chrf(
                references,
                base,
                candidate,
                bootstrap_samples=200,
                seed=17,
            ),
        )

    def test_paired_sentence_analysis_rejects_unequal_or_empty_inputs(self):
        with self.assertRaisesRegex(ValueError, "equal, non-empty"):
            paired_sentence_chrf(["hello"], [], ["hello"])
        with self.assertRaisesRegex(ValueError, "equal, non-empty"):
            paired_sentence_chrf([], [], [])


if __name__ == "__main__":
    unittest.main()
