# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test Common Voice LID parsing without downloading its dataset."""

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.evaluate_common_voice_lid import load_test_sentences, score_thresholds


class FakeIdentifier:
    def __init__(self):
        self.calls = 0

    def classify(self, text):
        self.calls += 1
        return {
            "english": ("en", 0.91),
            "french": ("fr", 0.91),
            "discordant": ("en", 0.82),
            "somali": ("so", 0.96),
            "german": ("de", 0.99),
        }[text]


class CommonVoiceLidEvaluatorTests(unittest.TestCase):
    def test_loads_only_short_test_rows_and_hashes_source(self):
        rows = [
            ("3", "English source test", "en", "test"),
            ("2", "French source test", "fr", "test"),
            ("1", "Somali source test", "so", "dev"),
            ("4", "A longer English source sentence", "en", "test"),
            ("5", "Too short", "en", "test"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mcv_text_lid.tsv"
            with path.open("w", encoding="utf-8", newline="") as output:
                writer = csv.writer(output, delimiter="\t")
                writer.writerow(("id", "sentence", "lang", "split"))
                writer.writerows(rows)

            expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            datasets, eligible_counts, digest = load_test_sentences(path)

        self.assertEqual(eligible_counts, {"en": 1, "fr": 1})
        self.assertEqual(
            datasets,
            {"en": [("3", "English source test")], "fr": [("2", "French source test")]},
        )
        self.assertEqual(digest, expected_digest)

    def test_bounds_samples_per_language_deterministically(self):
        rows = [
            ("1", "English row one", "en", "test"),
            ("2", "English row two", "en", "test"),
            ("3", "English row three", "en", "test"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.tsv"
            with path.open("w", encoding="utf-8", newline="") as output:
                writer = csv.writer(output, delimiter="\t")
                writer.writerow(("id", "sentence", "lang", "split"))
                writer.writerows(rows)

            first = load_test_sentences(path, per_language_limit=1)
            second = load_test_sentences(path, per_language_limit=1)

        self.assertEqual(first, second)
        self.assertEqual(first[1], {"en": 3})
        self.assertEqual(len(first[0]["en"]), 1)

    def test_rejects_incomplete_header(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "incomplete.tsv"
            path.write_text(
                "id\tsentence\tlang\n1\tEnglish source test\ten\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                load_test_sentences(path)

    def test_scores_supported_and_unsupported_source_labels_once(self):
        identifier = FakeIdentifier()
        datasets = {
            "en": [("1", "english")],
            "fr": [("2", "discordant")],
            "so": [("3", "somali")],
            "de": [("4", "german")],
        }
        with patch(
            "tools.evaluate_common_voice_lid.language_detection._identifier",
            return_value=identifier,
        ):
            results = score_thresholds(datasets, thresholds=(0.80, 0.85))

        self.assertEqual(identifier.calls, 4)
        self.assertEqual(results["0.80"]["correct_supported"], 2)
        self.assertEqual(results["0.80"]["supported_label_disagreement"], 1)
        self.assertEqual(results["0.80"]["unsupported_label_unidentified"], 1)
        self.assertEqual(results["0.80"]["by_source_label"]["de"]["unidentified"], 1)
        self.assertEqual(results["0.85"]["abstained"], 1)


if __name__ == "__main__":
    unittest.main()
