# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test aggregate-only short-input evaluation for the MASSIVE corpus."""

import hashlib
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.evaluate_massive_lid import load_test_samples
from tools.evaluate_massive_lid import score_thresholds


def massive_row(row_id, locale="en-US", text="Find nearby cafe"):
    return {
        "id": row_id,
        "locale": locale,
        "partition": "test",
        "utt": text,
    }


class FakeIdentifier:
    def __init__(self):
        self.calls = []

    def classify(self, text):
        self.calls.append(text)
        return {
            "supported_en": ("en", 0.91),
            "wrong_supported": ("fr", 0.93),
            "unsupported_prediction": ("so", 0.92),
            "unidentified": ("zz", 0.95),
            "uncertain": ("en", 0.72),
        }[text]


class MassiveLidEvaluatorTests(unittest.TestCase):
    def make_archive(self, root, rows_by_locale):
        archive_path = root / "massive.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            for locale, rows in rows_by_locale.items():
                payload = "\n".join(json.dumps(row) for row in rows).encode()
                member_path = root / f"{locale}.jsonl"
                member_path.write_bytes(payload)
                archive.add(member_path, arcname=f"1.1/data/{locale}.jsonl")
        return archive_path

    def test_filters_test_locale_rows_through_app_gate(self):
        rows_by_locale = {
            "en-US": [
                massive_row("1"),
                massive_row("2", text="Too short"),
                massive_row("3", text="This is a longer sentence beyond the app limit"),
                massive_row("4", text="Find a nearby coffee shop", locale="en-US"),
                massive_row("7", text="Read blue books", locale="en-US"),
            ],
            "fr-FR": [massive_row("5", locale="fr-FR")],
            "af-ZA": [massive_row("6", locale="af-ZA")],
        }
        rows_by_locale["en-US"][3]["partition"] = "train"
        rows_by_locale["en-US"][4]["partition"] = "dev"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_archive(root, rows_by_locale)
            datasets, stats, digest = load_test_samples(
                path,
                per_language_limit=10,
                expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()

        self.assertEqual(len(datasets["en-US"]), 1)
        self.assertEqual(len(datasets["fr-FR"]), 1)
        self.assertEqual(len(datasets["af-ZA"]), 1)
        self.assertEqual(stats["en-US"]["test_rows"], 3)
        self.assertEqual(stats["en-US"]["short_gate_rows"], 1)
        self.assertEqual(stats["af-ZA"]["short_gate_rows"], 1)
        self.assertEqual(digest, expected_digest)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_archive(root, rows_by_locale)
            datasets, stats, _ = load_test_samples(
                path,
                per_language_limit=10,
                expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                partition="dev",
            )

        self.assertEqual(datasets["en-US"], [("7", "Read blue books")])
        self.assertEqual(stats["en-US"]["dev_rows"], 1)

    def test_rejects_wrong_archive_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_archive(
                root,
                {"en-US": [massive_row("1")], "fr-FR": [massive_row("2", "fr-FR")]},
            )
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_test_samples(path, expected_sha256="0" * 64)

    def test_rejects_training_partition(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.make_archive(
                root,
                {"en-US": [massive_row("1")], "fr-FR": [massive_row("2", "fr-FR")]},
            )
            with self.assertRaisesRegex(ValueError, "dev or test"):
                load_test_samples(path, expected_sha256=None, partition="train")

    def test_scores_supported_disagreements_unsupported_and_abstentions(self):
        identifier = FakeIdentifier()
        data = {
            "en-US": [
                ("1", "supported_en"),
                ("2", "wrong_supported"),
                ("3", "uncertain"),
            ],
            "af-ZA": [
                ("4", "unsupported_prediction"),
                ("5", "unidentified"),
            ],
        }
        with patch(
            "tools.evaluate_massive_lid.language_detection._identifier",
            return_value=identifier,
        ):
            results = score_thresholds(data, thresholds=(0.80,))

        counts = results["0.80"]
        self.assertEqual(len(identifier.calls), 5)
        self.assertEqual(counts["correct_supported"], 1)
        self.assertEqual(counts["supported_label_disagreement"], 1)
        self.assertEqual(counts["false_supported"], 1)
        self.assertEqual(counts["unsupported_label_not_supported_by_app"], 1)
        self.assertEqual(counts["abstained"], 1)


if __name__ == "__main__":
    unittest.main()
