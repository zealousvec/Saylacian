# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests metadata describing supported scripts and their limitations."""

import struct
import unittest
from pathlib import Path

from saylacian.core.script_info import osmanya_letters
from saylacian.core.transliteration import OLD_NUBIAN_TO_LATIN, transliterate


class ScriptInfoTests(unittest.TestCase):
    def test_inventory_assigned_letters(self):
        rows = osmanya_letters()
        self.assertEqual(len(rows), 30)
        self.assertTrue(all(r["name"].startswith("OSMANYA LETTER") for r in rows))

    def test_ambiguity_visible(self):
        rows = {r["glyph"]: r for r in osmanya_letters()}
        self.assertEqual(rows["𐒓"]["readings"], "uu/w")
        self.assertEqual(rows["𐒕"]["readings"], "ii/y")

    def test_old_nubian_font_covers_every_converter_glyph(self):
        path = Path(__file__).resolve().parents[1] / "assets/NotoSansCoptic-Regular.ttf"
        font = path.read_bytes()
        table_count = struct.unpack_from(">H", font, 4)[0]
        cmap_offset = next(
            struct.unpack_from(">I", font, 12 + 16 * index + 8)[0]
            for index in range(table_count)
            if font[12 + 16 * index : 16 + 16 * index] == b"cmap"
        )
        subtables = struct.unpack_from(">H", font, cmap_offset + 2)[0]
        codepoints = set()
        for index in range(subtables):
            offset = (
                cmap_offset
                + struct.unpack_from(">I", font, cmap_offset + 8 + 8 * index)[0]
            )
            if struct.unpack_from(">H", font, offset)[0] != 4:
                continue
            count = struct.unpack_from(">H", font, offset + 6)[0] // 2
            ends = offset + 14
            starts = ends + count * 2 + 2
            deltas = starts + count * 2
            ranges = deltas + count * 2
            for segment in range(count):
                end = struct.unpack_from(">H", font, ends + 2 * segment)[0]
                start = struct.unpack_from(">H", font, starts + 2 * segment)[0]
                delta = struct.unpack_from(">h", font, deltas + 2 * segment)[0]
                range_offset = struct.unpack_from(">H", font, ranges + 2 * segment)[0]
                for char_code in range(start, min(end, 0xFFFF) + 1):
                    if range_offset:
                        glyph_address = (
                            ranges
                            + 2 * segment
                            + range_offset
                            + 2 * (char_code - start)
                        )
                        glyph = struct.unpack_from(">H", font, glyph_address)[0]
                        if glyph:
                            glyph = (glyph + delta) & 0xFFFF
                    else:
                        glyph = (char_code + delta) & 0xFFFF
                    if glyph:
                        codepoints.add(char_code)
        for character in OLD_NUBIAN_TO_LATIN:
            with self.subTest(character=character):
                self.assertIn(ord(character), codepoints)

    def test_old_nubian_conversion_uses_bundled_fonted_script(self):
        self.assertTrue(
            (
                Path(__file__).resolve().parents[1]
                / "assets/NotoSansCoptic-Regular.ttf"
            ).is_file()
        )
        self.assertEqual(
            transliterate(
                "ⲁⲃⲅ", "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
            ).text,
            "abg",
        )
