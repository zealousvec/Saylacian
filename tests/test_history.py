# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests local translation history storage and retrieval."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from saylacian.core.history import History


class HistoryTests(unittest.TestCase):
    def test_save_restore_clear(self):
        with tempfile.TemporaryDirectory() as folder:
            h = History(Path(folder) / "history.json")
            h.save("Somali Latin", "Osmanya", "b", "𐒁", True)
            self.assertEqual(h.read()[0]["result"], "𐒁")
            h.clear()
            self.assertEqual(h.read(), [])

    def test_unknown_version_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "history.json"
            p.write_text('{"version":2,"items":[]}')
            h = History(p)
            with self.assertRaises(ValueError):
                h.save("a", "b", "c", "d")
            self.assertIn('"version":2', p.read_text())

    def test_damaged_json_is_reported_without_modifying_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            path.write_text('{"version":1,"items":[', encoding="utf-8")
            original = path.read_bytes()

            with self.assertRaisesRegex(ValueError, "damaged; file left untouched"):
                History(path).read()

            self.assertEqual(path.read_bytes(), original)

    def test_save_and_clear_leave_damaged_history_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            for operation in ("save", "clear"):
                with self.subTest(operation=operation):
                    path.write_text('{"version":1,"items":[', encoding="utf-8")
                    original = path.read_bytes()
                    history = History(path)

                    with self.assertRaisesRegex(ValueError, "file left untouched"):
                        if operation == "save":
                            history.save("English", "French", "hello", "bonjour")
                        else:
                            history.clear()

                    self.assertEqual(path.read_bytes(), original)

    def test_invalid_history_schema_is_reported_without_modifying_file(self):
        invalid_documents = (
            [],
            {"version": 1, "items": {}},
            {"version": 1, "items": [None]},
            {
                "version": 1,
                "items": [
                    {
                        "source": "English",
                        "target": "French",
                        "text": "hello",
                        "result": "bonjour",
                        "favourite": "false",
                    }
                ],
            },
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            for document in invalid_documents:
                with self.subTest(document=document):
                    path.write_text(json.dumps(document), encoding="utf-8")
                    original = path.read_bytes()

                    with self.assertRaisesRegex(ValueError, "file left untouched"):
                        History(path).read()

                    self.assertEqual(path.read_bytes(), original)

    def test_clear_write_failure_preserves_existing_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            history = History(path)
            history.save("English", "French", "hello", "bonjour")
            original = path.read_bytes()

            with (
                patch.object(Path, "replace", side_effect=OSError("disk full")),
                self.assertRaisesRegex(OSError, "disk full"),
            ):
                history.clear()

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).iterdir()), [path])
