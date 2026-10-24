# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests the offline corpus evaluator without downloading corpus data."""

import unittest
from unittest.mock import patch

from tools.evaluate_language_detection_corpus import score_thresholds


class FakeIdentifier:
    def __init__(self):
        self.calls = 0

    def classify(self, text):
        self.calls += 1
        return {
            "correct": ("en", 0.90),
            "discordant": ("fr", 0.81),
            "unsupported": ("de", 0.99),
        }[text]


class LanguageDetectionCorpusEvaluatorTests(unittest.TestCase):
    def test_reports_source_label_disagreement_and_reuses_classification(self):
        identifier = FakeIdentifier()
        datasets = {
            "eng": [("1", "correct"), ("2", "discordant")],
            "deu": [("3", "discordant"), ("4", "unsupported")],
        }
        with patch(
            "tools.evaluate_language_detection_corpus.language_detection._identifier",
            return_value=identifier,
        ):
            results = score_thresholds(datasets, thresholds=(0.80, 0.85))

        self.assertEqual(identifier.calls, 4)
        self.assertEqual(results["0.80"]["development"]["source_label_disagreement"], 1)
        self.assertEqual(
            results["0.80"]["development"]["disagreement_by_source_label"],
            {"eng": 1},
        )
        self.assertEqual(results["0.80"]["holdout"]["source_label_disagreement"], 1)
        self.assertEqual(results["0.85"]["development"]["source_label_disagreement"], 0)
        self.assertEqual(results["0.85"]["development"]["abstained"], 2)


if __name__ == "__main__":
    unittest.main()
