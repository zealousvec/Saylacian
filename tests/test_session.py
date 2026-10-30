# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import tempfile
import unittest
from pathlib import Path

from saylacian.core.session import read_session, write_session


class SessionTests(unittest.TestCase):
    def test_session_survives_restart_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "last-session-v1.json"
            original = {
                "version": 1,
                "mode": "Translate meaning",
                "source": "English",
                "target": "French",
                "input": "Hello",
                "output": "Bonjour",
                "status": "Machine translation; check important details.",
                "alternatives": "",
            }
            self.assertTrue(write_session(path, original))
            restored = read_session(path)

        self.assertEqual(restored, original)

    def test_invalid_or_oversized_session_is_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "last-session-v1.json"
            path.write_text('{"version": 2}', encoding="utf-8")
            self.assertIsNone(read_session(path))
            path.write_text(" " * 64_001, encoding="utf-8")
            self.assertIsNone(read_session(path))

    def test_invalid_fields_and_oversized_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "last-session-v1.json"
            value = {
                "version": 1,
                "mode": "Translate meaning",
                "source": "English",
                "target": "French",
                "input": "Hello",
                "output": "Bonjour",
            }
            path.write_text(json.dumps({**value, "mode": "Unknown"}), encoding="utf-8")
            self.assertIsNone(read_session(path))
            path.write_text(
                json.dumps({**value, "output": "x" * 16_001}), encoding="utf-8"
            )
            self.assertIsNone(read_session(path))

    def test_write_failure_keeps_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "last-session-v1.json"
            original = {
                "version": 1,
                "mode": "Convert writing system",
                "source": "Somali Latin",
                "target": "Osmanya",
                "input": "dhagax",
                "output": "𐒊𐒖𐒌𐒖𐒄",
            }
            self.assertTrue(write_session(path, original))
            self.assertFalse(write_session(path, {"bad": object()}))
            self.assertEqual(read_session(path), original)


if __name__ == "__main__":
    unittest.main()
