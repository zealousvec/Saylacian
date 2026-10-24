# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish several standard and registered clipboard representations on Windows."""

from __future__ import annotations

import ctypes
import os
import time
from collections.abc import Sequence
from ctypes import wintypes

CF_UNICODETEXT = 13
CF_DIB = 8
GMEM_MOVEABLE = 0x0002
Formats = Sequence[tuple[str, bytes]]


def _dlls():
    if os.name != "nt":
        raise OSError("Multi-format clipboard publishing is available on Windows only.")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    return user32, kernel32


def _format_id(user32, name: str) -> int:
    standard = {"CF_UNICODETEXT": CF_UNICODETEXT, "CF_DIB": CF_DIB}
    if name in standard:
        return standard[name]
    result = user32.RegisterClipboardFormatW(name)
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


def publish(formats: Formats, *, owner: int | None = None) -> None:
    """Set ordered [(format-name, bytes)] data; ownership transfers to Windows."""
    if not formats:
        raise ValueError("At least one clipboard representation is required.")
    if not owner:
        raise ValueError(
            "A valid owner window handle is required for Windows clipboard publishing."
        )
    user32, kernel32 = _dlls()

    format_ids = [_format_id(user32, name) for name, _ in formats]
    prepared = []
    for (name, data), format_id in zip(formats, format_ids):
        if not isinstance(data, bytes):
            raise TypeError(f"Clipboard data for {name} must be bytes.")
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            kernel32.GlobalFree(handle)
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(pointer, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        prepared.append((format_id, handle))

    opened = False
    transferred = set()
    try:
        for attempt in range(12):
            if user32.OpenClipboard(owner):
                opened = True
                break
            time.sleep(0.025 * (attempt + 1))
        if not opened:
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())
        for index, (fmt, handle) in enumerate(prepared):
            if not user32.SetClipboardData(fmt, handle):
                raise ctypes.WinError(ctypes.get_last_error())
            transferred.add(index)
    finally:
        if opened:
            user32.CloseClipboard()
        for index, (_, handle) in enumerate(prepared):
            if index not in transferred:
                kernel32.GlobalFree(handle)
