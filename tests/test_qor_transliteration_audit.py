# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests that the Qor transliteration audit stays pinned and text-private."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.translation_lab.qor_transliteration_audit import audit_qor_corpus


class QorTransliterationAuditTests(unittest.TestCase):
    def _fixture(self, rows):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        path = Path(temporary_directory.name) / "sentences.jsonl"
        content = "".join(json.dumps(row) + "\n" for row in rows).encode()
        path.write_bytes(content)
        artifact = {
            "expected_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        source = {
            "source_id": "unkadlabs-qor-af-soomaali-mono",
            "revision": "5234876e5019cc4b1c79096c9f046fe2f8113b1e",
            "license": "CC-BY-SA-4.0",
            "source_page": "https://example.invalid/qor",
            "artifacts": [
                {
                    **artifact,
                    "filename": "qor-af-soomaali-5234876e-data-sentences.jsonl",
                }
            ],
        }
        return path, source

    def test_aggregates_without_retaining_text_and_excludes_canaries(self):
        rows = [
            {
                "text_so": "Qorraxdu way soo baxday.",
                "license": "CC-BY-SA-4.0",
                "verified": True,
                "mode": "write",
                "sector": "general",
            }
        ]
        path, source = self._fixture(rows)
        report = audit_qor_corpus(path, source)
        serialized = json.dumps(report)
        self.assertEqual(report["sentence_count"], 1)
        self.assertEqual(
            report["scripts"]["Borama"]["roundtrip_sample"]["primary_matches"], 1
        )
        self.assertFalse(report["source_text_saved"])
        self.assertFalse(report["training_performed"])
        self.assertNotIn("Qorraxdu", serialized)
        self.assertIn("canary file was not read", report["scope"])

    def test_rejects_rows_that_fail_source_quality_or_license_checks(self):
        row = {
            "text_so": "Tusaale Somali ah.",
            "license": "CC-BY-SA-4.0",
            "verified": True,
            "mode": "write",
        }
        for key, value in (
            ("license", "unknown"),
            ("verified", False),
            ("mode", "translate"),
        ):
            with self.subTest(key=key):
                bad_row = {**row, key: value}
                path, source = self._fixture([bad_row])
                with self.assertRaises(ValueError):
                    audit_qor_corpus(path, source)

    def test_rejects_changed_artifact_hash(self):
        path, source = self._fixture(
            [
                {
                    "text_so": "Tusaale Somali ah.",
                    "license": "CC-BY-SA-4.0",
                    "verified": True,
                    "mode": "write",
                }
            ]
        )
        source["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            audit_qor_corpus(path, source)


if __name__ == "__main__":
    unittest.main()
