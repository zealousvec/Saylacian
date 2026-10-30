# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest

from tools.in_memory_clipboard import InMemoryClipboard


class InMemoryClipboardTests(unittest.TestCase):
    def test_copy_and_paste_round_trip_stays_in_memory(self):
        clipboard = InMemoryClipboard()

        clipboard.copy("Dhagax!")

        self.assertEqual(clipboard.paste(), "Dhagax!")
        self.assertEqual(clipboard.formats, ())

    def test_windows_formats_are_captured_without_os_clipboard(self):
        clipboard = InMemoryClipboard()
        formats = [
            ("Saylacian Text v1", b"portable-payload"),
            ("CF_UNICODETEXT", "ⲁⲃ\0".encode("utf-16-le")),
        ]

        clipboard.publish_windows_formats(formats)

        self.assertEqual(clipboard.formats, tuple(formats))
        self.assertEqual(clipboard.paste(), "ⲁⲃ")

    def test_windows_payload_requires_unicode_text(self):
        clipboard = InMemoryClipboard()

        with self.assertRaisesRegex(ValueError, "CF_UNICODETEXT"):
            clipboard.publish_windows_formats([("Saylacian Text v1", b"payload")])


if __name__ == "__main__":
    unittest.main()
