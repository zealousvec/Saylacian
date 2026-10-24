# SPDX-License-Identifier: AGPL-3.0-or-later
"""Clipboard payload builders; Windows provides the format transport separately."""

from __future__ import annotations

from .interchange import (
    encode_saylacian_text,
    html_for_chart,
    png_to_dib,
    render_chart_png,
    rtf_for_chart,
)


def unicode_clipboard_bytes(text: str) -> bytes:
    return (text + "\0").encode("utf-16-le")


def formats_as_latin(latin: str) -> list[tuple[str, bytes]]:
    return [("CF_UNICODETEXT", unicode_clipboard_bytes(latin))]


def formats_as_image(script: str, glyphs: str, latin: str) -> list[tuple[str, bytes]]:
    png = render_chart_png(glyphs, script, latin)
    alt_text = f"{script} image. Latin reading: {latin}"
    return [
        ("PNG", png),
        ("CF_DIB", png_to_dib(png)),
        ("CF_UNICODETEXT", unicode_clipboard_bytes(alt_text)),
    ]


def formats_as_saylacian_text(
    script: str, glyphs: str, latin: str
) -> list[tuple[str, bytes]]:
    envelope = encode_saylacian_text(glyphs, script)
    return [
        ("Saylacian Text v1", envelope.encode("ascii")),
        ("Rich Text Format", rtf_for_chart(glyphs, script, latin)),
        ("HTML Format", html_for_chart(glyphs, script, latin)),
        ("CF_UNICODETEXT", unicode_clipboard_bytes(envelope)),
    ]
