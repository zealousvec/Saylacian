# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests portable clipboard encoding, decoding, and Saylacian text interchange."""

import json
import struct
import unittest
from io import BytesIO

from PIL import Image

from saylacian.core.clipboard_repr import formats_as_image
from saylacian.core.clipboard_repr import formats_as_saylacian_text
from saylacian.core.clipboard_repr import unicode_clipboard_bytes
from saylacian.core.interchange import MAGIC
from saylacian.core.interchange import decode_saylacian_text
from saylacian.core.interchange import encode_saylacian_text
from saylacian.core.interchange import html_for_chart
from saylacian.core.interchange import identify_chart_text
from saylacian.core.interchange import png_to_dib
from saylacian.core.interchange import render_chart_png
from saylacian.core.interchange import rtf_for_chart
from saylacian.core.transliteration import transliterate


class ClipboardInterchangeTests(unittest.TestCase):
    def setUp(self):
        self.borama = transliterate("hello!", "Somali Latin", "Borama").text
        self.kaddare = transliterate("shadh?", "Somali Latin", "Kaddare").text

    def test_saylacian_text_v1_ascii_envelope_round_trips_exact_glyphs(self):
        for script, glyphs, latin in (
            ("Borama", self.borama, "hello!"),
            ("Kaddare", self.kaddare, "shadh?"),
        ):
            with self.subTest(script=script):
                envelope = encode_saylacian_text(glyphs, script)
                self.assertTrue(envelope.startswith(MAGIC))
                self.assertTrue(envelope.isascii())
                decoded = decode_saylacian_text(envelope)
                self.assertEqual(
                    (decoded.script, decoded.text, decoded.latin),
                    (script, glyphs, latin),
                )

    def test_chart_detection_rejects_unknown_and_mixed_private_use_text(self):
        self.assertEqual(identify_chart_text(self.borama), "Borama")
        self.assertEqual(identify_chart_text(self.kaddare), "Kaddare")
        self.assertIsNone(identify_chart_text(self.borama + self.kaddare))
        self.assertIsNone(identify_chart_text(self.borama + "\ue999"))
        self.assertIsNone(identify_chart_text(self.borama + "\U000f0000"))
        with self.assertRaisesRegex(ValueError, "private-use character"):
            encode_saylacian_text(self.borama + "\U000f0000", "Borama")

    def test_envelope_rejects_corruption_and_wrong_script(self):
        envelope = encode_saylacian_text(self.borama, "Borama")
        changed = envelope.replace("hello", "hullo")
        self.assertIsNone(decode_saylacian_text("ordinary pasted words"))
        if changed != envelope:
            with self.assertRaises(ValueError):
                decode_saylacian_text(changed)
        payload = json.loads(envelope[len(MAGIC) :])
        payload["script"] = "Kaddare"
        tampered = MAGIC + json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        with self.assertRaises(ValueError):
            decode_saylacian_text(tampered)

    def test_saylacian_text_carries_rtf_html_and_plain_import_fallback(self):
        parts = formats_as_saylacian_text("Borama", self.borama, "hello!")
        self.assertEqual(
            [name for name, _ in parts],
            ["Saylacian Text v1", "Rich Text Format", "HTML Format", "CF_UNICODETEXT"],
        )
        values = dict(parts)
        self.assertIn(b"\\fonttbl", values["Rich Text Format"])
        self.assertIn(b"Saylacian Borama Chart", values["Rich Text Format"])
        self.assertIn(b"hello!", values["Rich Text Format"])
        rtf = rtf_for_chart(self.borama, "Borama", "hello!")
        signed_first_glyph = ord(self.borama[0]) - 0x10000
        self.assertIn(f"\\u{signed_first_glyph}?".encode(), rtf)
        html_value = values["HTML Format"]
        header, body = html_value.split(b"<html>", 1)
        fields = {
            line.split(b":", 1)[0]: int(line.split(b":", 1)[1])
            for line in header.splitlines()
            if line.startswith((b"Start", b"End"))
        }
        html_start = fields[b"StartHTML"]
        self.assertEqual(html_value[html_start:], b"<html>" + body)
        self.assertIn(b"Saylacian Borama Chart", html_value)
        self.assertIn(b"Latin reading: hello!", html_value)
        plain = values["CF_UNICODETEXT"].decode("utf-16-le").rstrip("\0")
        self.assertEqual(decode_saylacian_text(plain).text, self.borama)

    def test_image_copy_contains_real_glyph_pixels_and_standard_dib(self):
        png = render_chart_png(self.borama, "Borama", "hello!")
        with Image.open(BytesIO(png)) as image:
            self.assertGreater(image.width, 500)
            self.assertGreater(
                len(image.getcolors(image.width * image.height) or []), 2
            )
        dib = png_to_dib(png)
        header = struct.unpack("<IiiHHIIiiII", dib[:40])
        self.assertEqual(header[0], 40)
        self.assertEqual((header[3], header[4], header[5]), (1, 24, 0))
        self.assertEqual(len(dib), 40 + header[6])
        formats = dict(formats_as_image("Borama", self.borama, "hello!"))
        self.assertTrue(formats["PNG"].startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(formats["CF_DIB"][:40], dib[:40])
        self.assertTrue(unicode_clipboard_bytes("hello").endswith(b"\0\0"))

    def test_image_copy_wraps_long_unbroken_text(self):
        image_bytes = render_chart_png(self.borama * 30, "Borama", "long sample")
        with Image.open(BytesIO(image_bytes)) as image:
            self.assertGreater(image.height, 500)

    def test_html_fragment_offsets_point_inside_fragment(self):
        value = html_for_chart(self.borama, "Borama", "hello!")
        header = value.split(b"<html>", 1)[0]
        fields = {
            line.split(b":", 1)[0]: int(line.split(b":", 1)[1])
            for line in header.splitlines()
            if line.startswith((b"Start", b"End"))
        }
        self.assertEqual(
            value[fields[b"StartFragment"] : fields[b"EndFragment"]],
            b'<div style="font-family:Saylacian Borama Chart;font-size:30pt">'
            + "".join(f"&#x{ord(ch):X};" for ch in self.borama).encode()
            + b"</div><div>Latin reading: hello!</div>",
        )


if __name__ == "__main__":
    unittest.main()
