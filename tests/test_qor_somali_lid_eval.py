# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test the aggregate-only Qor short-Somali evaluation path."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.evaluate_qor_somali_lid import evaluate, load_short_somali_rows


class FakeIdentifier:
    def __init__(self):
        self.calls = 0

    def classify(self, text):
        self.calls += 1
        return {
            "somali": ("so", 0.91),
            "weak_somali": ("so", 0.76),
            "other": ("om", 0.93),
        }[text]


class QorSomaliLidEvaluatorTests(unittest.TestCase):
    def test_filters_to_verified_licensed_native_short_somali_rows(self):
        rows = [
            {
                "id": "1",
                "text_so": "This is Somali",
                "verified": True,
                "license": "CC-BY-SA-4.0",
            },
            {
                "id": "2",
                "text_so": "This is not verified",
                "verified": False,
                "license": "CC-BY-SA-4.0",
            },
            {
                "id": "3",
                "text_so": "This is not licensed",
                "verified": True,
                "license": "Unknown",
            },
            {
                "id": "4",
                "text_so": "A much longer sentence that does not meet the short input length criteria",
                "verified": True,
                "license": "CC-BY-SA-4.0",
            },
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sentences.jsonl"
            payload = "\n".join(json.dumps(row) for row in rows).encode()
            path.write_bytes(payload)
            texts, counts, digest = load_short_somali_rows(
                path, expected_sha256=hashlib.sha256(payload).hexdigest()
            )

        self.assertEqual(texts, ["This is Somali"])
        self.assertEqual(counts, {"rows": 4, "verified_licensed": 2, "eligible": 1})
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())

    def test_rejects_wrong_pinned_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sentences.jsonl"
            path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_short_somali_rows(path, expected_sha256="0" * 64)

    def test_evaluates_each_short_row_once_and_reports_threshold_tradeoff(self):
        fake_identifier = FakeIdentifier()
        with patch(
            "tools.evaluate_qor_somali_lid.language_detection._identifier",
            return_value=fake_identifier,
        ):
            results = evaluate(["somali", "weak_somali", "other"])

        self.assertEqual(fake_identifier.calls, 3)
        self.assertEqual(results["0.80"]["predicted_somali"], 1)
        self.assertEqual(results["0.80"]["predicted_other_language"], 1)
        self.assertEqual(results["0.80"]["abstained_below_threshold"], 1)
        self.assertEqual(results["0.70"]["predicted_somali"], 2)


if __name__ == "__main__":
    unittest.main()
