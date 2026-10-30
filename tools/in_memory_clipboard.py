# SPDX-License-Identifier: AGPL-3.0-or-later
"""Provide a clipboard stand-in for application acceptance checks."""

from __future__ import annotations


class InMemoryClipboard:
    """Round-trip clipboard text and Windows formats without OS clipboard access."""

    def __init__(self) -> None:
        self.text = ""
        self.formats: tuple[tuple[str, bytes], ...] = ()

    def copy(self, text: str) -> None:
        self.text = text

    def paste(self) -> str:
        return self.text

    def publish_windows_formats(self, formats: list[tuple[str, bytes]]) -> None:
        self.formats = tuple(formats)
        unicode_text = next(
            (data for name, data in formats if name == "CF_UNICODETEXT"), None
        )
        if unicode_text is None:
            raise ValueError("Windows clipboard payload lacks CF_UNICODETEXT.")
        self.text = unicode_text.decode("utf-16-le").rstrip("\0")
