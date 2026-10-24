# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test Windows clipboard publishing against isolated Win32 API doubles."""

import ctypes
import unittest
from unittest.mock import patch

from saylacian.core.windows_clipboard import CF_UNICODETEXT, publish


class FakeUser32:
    def __init__(self):
        self.owner = None
        self.formats = []
        self.closed = False

    def RegisterClipboardFormatW(self, _name):
        return 0xC000

    def OpenClipboard(self, owner):
        self.owner = owner
        return 1

    def EmptyClipboard(self):
        return 1

    def SetClipboardData(self, format_id, handle):
        self.formats.append((format_id, handle))
        return handle

    def CloseClipboard(self):
        self.closed = True
        return 1


class FakeKernel32:
    def __init__(self):
        self.blocks = {}
        self.freed = []

    def GlobalAlloc(self, _flags, size):
        buffer = ctypes.create_string_buffer(max(size, 1))
        handle = ctypes.addressof(buffer)
        self.blocks[handle] = buffer
        return handle

    def GlobalLock(self, handle):
        return ctypes.addressof(self.blocks[handle])

    def GlobalUnlock(self, _handle):
        return 1

    def GlobalFree(self, handle):
        self.freed.append(handle)
        self.blocks.pop(handle, None)
        return 0


class FailingKernel32(FakeKernel32):
    def GlobalAlloc(self, flags, size):
        if self.blocks:
            return 0
        return super().GlobalAlloc(flags, size)


class WindowsClipboardTests(unittest.TestCase):
    def test_publishes_all_formats_with_valid_owner_and_transfers_handles(self):
        user32 = FakeUser32()
        kernel32 = FakeKernel32()
        data = "saylacian".encode("utf-16-le") + b"\0\0"
        with patch(
            "saylacian.core.windows_clipboard._dlls", return_value=(user32, kernel32)
        ):
            publish(
                [("CF_UNICODETEXT", data), ("Saylacian Text v1", b"portable")],
                owner=0x1234,
            )

        self.assertEqual(user32.owner, 0x1234)
        self.assertEqual(
            [format_id for format_id, _ in user32.formats],
            [CF_UNICODETEXT, 0xC000],
        )
        self.assertTrue(user32.closed)
        self.assertEqual(kernel32.freed, [])
        self.assertEqual(len(kernel32.blocks), 2)

    def test_rejects_null_owner_before_loading_or_calling_win32(self):
        with (
            patch("saylacian.core.windows_clipboard._dlls") as load_dlls,
            self.assertRaisesRegex(ValueError, "owner window handle"),
        ):
            publish([("CF_UNICODETEXT", b"text\0\0")])

        load_dlls.assert_not_called()

    def test_frees_prepared_buffers_when_later_allocation_fails(self):
        user32 = FakeUser32()
        kernel32 = FailingKernel32()
        with (
            patch(
                "saylacian.core.windows_clipboard._dlls",
                return_value=(user32, kernel32),
            ),
            self.assertRaises(OSError),
        ):
            publish(
                [("CF_UNICODETEXT", b"text\0\0"), ("Saylacian Text v1", b"tag")],
                owner=0x1234,
            )

        self.assertEqual(len(kernel32.freed), 1)
        self.assertEqual(kernel32.blocks, {})
        self.assertEqual(user32.owner, None)


if __name__ == "__main__":
    unittest.main()
