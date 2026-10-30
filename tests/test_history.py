# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests local translation history storage and retrieval."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from saylacian.core.history import MAX_HISTORY_BYTES
from saylacian.core.history import DamagedHistoryError
from saylacian.core.history import History


class HistoryTests(unittest.TestCase):
    def test_save_restore_clear(self):
        with tempfile.TemporaryDirectory() as folder:
            h = History(Path(folder) / "history.json")
            h.save("Somali Latin", "Osmanya", "b", "𐒁", True)
            self.assertEqual(h.read()[0]["result"], "𐒁")
            h.clear()
            self.assertEqual(h.read(), [])

    def test_save_rejects_invalid_field_types_without_changing_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            history = History(path)
            history.save("English", "French", "hello", "bonjour")
            original = path.read_bytes()
            invalid_entries = (
                (None, "French", "hello", "bonjour", False, "Translate meaning"),
                ("English", [], "hello", "bonjour", False, "Translate meaning"),
                ("English", "French", None, "bonjour", False, "Translate meaning"),
                ("English", "French", "hello", 5, False, "Translate meaning"),
                ("English", "French", "hello", "bonjour", "false", "Translate meaning"),
                ("English", "French", "hello", "bonjour", False, None),
            )

            for entry in invalid_entries:
                with self.subTest(entry=entry):
                    with self.assertRaisesRegex(ValueError, "invalid field types"):
                        history.save(*entry[:5], mode=entry[5])
                    self.assertEqual(path.read_bytes(), original)

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

            with self.assertRaisesRegex(
                DamagedHistoryError, "damaged; file left untouched"
            ):
                History(path).read()

            self.assertEqual(path.read_bytes(), original)

    def test_oversized_history_is_rejected_before_reading_full_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            original = b"x" * (MAX_HISTORY_BYTES + 1)
            path.write_bytes(original)

            with (
                patch.object(Path, "read_bytes", side_effect=AssertionError),
                self.assertRaisesRegex(DamagedHistoryError, "too large"),
            ):
                History(path).read()

            self.assertEqual(path.stat().st_size, len(original))

    def test_oversized_history_can_be_backed_up_and_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            original = b"invalid history " * (MAX_HISTORY_BYTES // 16 + 1)
            path.write_bytes(original)

            backup = History(path).backup_and_reset()

            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(History(path).read(), [])

    def test_oversized_save_keeps_existing_history_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            history = History(path)
            history.save("English", "French", "hello", "bonjour")
            original = path.read_bytes()

            with self.assertRaisesRegex(ValueError, "exceeds its size limit"):
                history.save("English", "French", "hello", "x" * MAX_HISTORY_BYTES)

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(folder).iterdir()), [path])

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

    def test_backup_and_reset_preserves_damaged_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            original = b'{"version":1,"items":[broken'
            path.write_bytes(original)

            backup = History(path).backup_and_reset()

            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(History(path).read(), [])
            self.assertNotEqual(backup, path)

    def test_recovery_refuses_valid_and_unknown_version_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            history = History(path)
            history.save("English", "French", "hello", "bonjour")
            valid_bytes = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "readable"):
                history.backup_and_reset()
            self.assertEqual(path.read_bytes(), valid_bytes)

            future_format = b'{"version":2,"items":[]}'
            path.write_bytes(future_format)
            with self.assertRaisesRegex(ValueError, "Unknown history format"):
                history.backup_and_reset()
            self.assertEqual(path.read_bytes(), future_format)
            self.assertEqual(list(Path(folder).glob("*.backup-*")), [])

    def test_reset_failure_keeps_original_and_complete_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.json"
            original = b'{"version":1,"items":[broken'
            path.write_bytes(original)
            history = History(path)

            with (
                patch.object(Path, "replace", side_effect=OSError("disk full")),
                self.assertRaisesRegex(OSError, "disk full"),
            ):
                history.backup_and_reset()

            backups = list(Path(folder).glob("history.json.backup-*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), original)
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
