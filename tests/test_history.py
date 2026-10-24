# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests local translation history storage and retrieval."""

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
