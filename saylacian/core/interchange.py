# SPDX-License-Identifier: AGPL-3.0-or-later
"""Portable Saylacian Text and rich clipboard representations for chart scripts."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import struct
import textwrap
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .transliteration import (
    SCRIPT_PUA_TO_LATIN,
    detect_chart_script,
    is_private_use_character,
    transliterate,
)

MAGIC = "SAYLACIAN-TEXT/1\n"
ENCODING = "saylacian-chart-pua-v1"
MAX_TEXT_LENGTH = 4000
SCRIPT_FONTS = {
    "Borama": "BoramaChart-Regular.ttf",
    "Kaddare": "KaddareChart-Regular.ttf",
}
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SaylacianText:
    script: str
    text: str
    latin: str


def identify_chart_text(text: str) -> str | None:
    detected = detect_chart_script(text)
    script = detected[0] if detected else None
    return script if script in SCRIPT_FONTS else None


def _validate_script_text(text: str, script: str) -> None:
    if script not in SCRIPT_FONTS:
        raise ValueError("Only Borama and Kaddare have Saylacian Text format support.")
    if not isinstance(text, str) or not text or len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"Text must contain between 1 and {MAX_TEXT_LENGTH} characters."
        )
    known = set(SCRIPT_PUA_TO_LATIN[script].keys())
    other_chart = set().union(
        *(
            set(mapping.keys())
            for name, mapping in SCRIPT_PUA_TO_LATIN.items()
            if name != script
        )
    )
    for char in text:
        if is_private_use_character(char) and char not in known:
            raise ValueError(f"Unrecognized private-use character U+{ord(char):04X}.")
        if char in other_chart:
            raise ValueError("Text mixes glyphs from different chart scripts.")


def encode_saylacian_text(text: str, script: str) -> str:
    """Return an ASCII-only, integrity-checked text envelope for sharing/import."""
    _validate_script_text(text, script)
    latin = transliterate(text, script, "Somali Latin").text
    digest = hashlib.sha256(f"{ENCODING}\0{script}\0{text}".encode("utf-8")).hexdigest()
    payload = {
        "format": "Saylacian Text",
        "version": 1,
        "script": script,
        "encoding": ENCODING,
        "text": text,
        "latin": latin,
        "sha256": digest,
    }
    return MAGIC + json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def decode_saylacian_text(value: str) -> SaylacianText | None:
    """Decode a Saylacian envelope; return None when input is ordinary text."""
    if not value.startswith("SAYLACIAN-TEXT/"):
        return None
    if not value.startswith(MAGIC):
        raise ValueError("Unsupported Saylacian Text version.")
    try:
        payload = json.loads(value[len(MAGIC) :])
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("Saylacian Text package is not valid JSON.") from error
    if not isinstance(payload, dict) or payload.get("format") != "Saylacian Text":
        raise ValueError("Saylacian Text package header is invalid.")
    if payload.get("version") != 1 or payload.get("encoding") != ENCODING:
        raise ValueError(
            "Saylacian Text package uses an unsupported version or encoding."
        )
    script, text = payload.get("script"), payload.get("text")
    _validate_script_text(text, script)
    expected = hashlib.sha256(
        f"{ENCODING}\0{script}\0{text}".encode("utf-8")
    ).hexdigest()
    if payload.get("sha256") != expected:
        raise ValueError(
            "Saylacian Text package checksum does not match; paste was changed."
        )
    latin = transliterate(text, script, "Somali Latin").text
    if payload.get("latin") != latin:
        raise ValueError(
            "Saylacian Text package Latin reading does not match its glyphs."
        )
    return SaylacianText(script, text, latin)


def _rtf_escape(value: str) -> str:
    parts = []
    for char in value:
        code = ord(char)
        if char in "\\{}":
            parts.append("\\" + char)
        elif char == "\n":
            parts.append("\\line ")
        elif char == "\r":
            continue
        elif code < 128:
            parts.append(char)
        else:
            units = char.encode("utf-16-le")
            for index in range(0, len(units), 2):
                unit = int.from_bytes(units[index : index + 2], "little")
                signed = unit if unit < 32768 else unit - 65536
                parts.append(f"\\u{signed}?")
    return "".join(parts)


def rtf_for_chart(text: str, script: str, latin: str) -> bytes:
    _validate_script_text(text, script)
    family = f"Saylacian {script} Chart"
    value = (
        r"{\rtf1\ansi\deff0\uc1"
        + r"{\fonttbl{\f0\fmodern "
        + _rtf_escape(family)
        + r";}{\f1\fswiss Arial;}}"
        + r"\f0\fs40 "
        + _rtf_escape(text)
        + r"\par\f1\fs20 "
        + _rtf_escape("Latin reading: " + latin)
        + "}"
    )
    return value.encode("ascii")


def html_for_chart(text: str, script: str, latin: str) -> bytes:
    _validate_script_text(text, script)
    glyphs = "".join(f"&#x{ord(char):X};" for char in text)
    family = html.escape(f"Saylacian {script} Chart", quote=True)
    fragment = (
        f'<div style="font-family:{family};font-size:30pt">{glyphs}</div>'
        f"<div>Latin reading: {html.escape(latin)}</div>"
    )
    start_marker, end_marker = "<!--StartFragment-->", "<!--EndFragment-->"
    body = (
        "<html><body><!--StartFragment-->"
        + fragment
        + "<!--EndFragment--></body></html>"
    ).encode("utf-8")
    header_template = (
        "Version:1.0\r\nStartHTML:{:010d}\r\nEndHTML:{:010d}\r\n"
        "StartFragment:{:010d}\r\nEndFragment:{:010d}\r\n"
    )
    header_size = len(header_template.format(0, 0, 0, 0).encode("ascii"))
    html_start = header_size
    fragment_start = html_start + body.index(start_marker.encode()) + len(start_marker)
    fragment_end = html_start + body.index(end_marker.encode())
    html_end = html_start + len(body)
    return (
        header_template.format(
            html_start, html_end, fragment_start, fragment_end
        ).encode("ascii")
        + body
    )


def render_chart_png(text: str, script: str, latin: str) -> bytes:
    """Rasterize script glyphs with licensed bundled font for font-independent sharing."""
    _validate_script_text(text, script)
    font_path = PROJECT_ROOT / "assets" / SCRIPT_FONTS[script]
    glyph_font = ImageFont.truetype(str(font_path), 46)
    title_font = ImageFont.truetype(str(font_path), 24)
    try:
        latin_font = ImageFont.truetype("arial.ttf", 21)
    except OSError:
        latin_font = ImageFont.load_default(size=21)
    width, margin = 1500, 64
    max_line = width - 2 * margin
    lines, current = [], ""

    for word in text.split(" "):
        candidate = word if not current else current + " " + word
        if glyph_font.getlength(candidate) <= max_line:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        fragment = ""
        for char in word:
            if fragment and glyph_font.getlength(fragment + char) > max_line:
                lines.append(fragment)
                fragment = char
            else:
                fragment += char
        current = fragment
    if current:
        lines.append(current)
    line_height = 70
    image_height = margin * 2 + 42 + 18 + len(lines) * line_height + 28 + 34 + margin
    if image_height > 12000:
        raise ValueError(
            "Image copy is too long; shorten text to under 4,000 characters."
        )
    image = Image.new("RGB", (width, image_height), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (margin, margin),
        f"{script} · Saylacian chart glyphs",
        fill="#222222",
        font=title_font,
    )
    y = margin + 55
    for line in lines:
        draw.text((margin, y), line, fill="#111111", font=glyph_font)
        y += line_height
    draw.line((margin, y + 4, width - margin, y + 4), fill="#d0d0d0", width=2)
    y += 20
    latin_lines = textwrap.wrap("Latin reading: " + latin, width=100)
    for line in latin_lines:
        draw.text((margin, y), line, fill="#555555", font=latin_font)
        y += 32
    stream = BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def png_to_dib(png: bytes) -> bytes:
    """Convert PNG bytes into standard CF_DIB (24-bit bottom-up BGR)."""
    with Image.open(BytesIO(png)) as source:
        image = source.convert("RGB")
    width, height = image.size
    stride = ((width * 3 + 3) // 4) * 4
    pixels = bytearray()
    raw = image.tobytes()
    raw_stride = width * 3
    for y in range(height - 1, -1, -1):
        row = raw[y * raw_stride : (y + 1) * raw_stride]
        for offset in range(0, len(row), 3):
            red, green, blue = row[offset : offset + 3]
            pixels.extend((blue, green, red))
        pixels.extend(b"\0" * (stride - width * 3))
    header = struct.pack(
        "<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixels), 0, 0, 0, 0
    )
    return header + pixels
