import struct
import unittest
from io import BytesIO

from PIL import Image

from saylacian.core.clipboard_repr import (
    formats_as_image,
    formats_as_saylacian_text,
)
from saylacian.core.interchange import (
    MAGIC,
    MAX_PACKAGE_LENGTH,
    decode_saylacian_text,
    encode_saylacian_text,
)
from saylacian.core.transliteration import transliterate


class InterchangeTests(unittest.TestCase):
    def test_saylacian_text_round_trips_chart_glyphs(self):
        original = encode_saylacian_text("\ue000 \ue005!", "Borama")

        decoded = decode_saylacian_text(original)

        self.assertEqual(decoded.script, "Borama")
        self.assertEqual(decoded.text, "\ue000 \ue005!")
        self.assertEqual(decoded.latin, "a uu!")

    def test_kaddare_case_forms_survive_tagged_copy_and_import(self):
        glyphs = transliterate("Qurux", "Somali Latin", "Kaddare").text
        package = encode_saylacian_text(glyphs, "Kaddare")
        decoded = decode_saylacian_text(package)

        self.assertEqual(decoded.text, glyphs)
        self.assertEqual(decoded.latin, "Qurux")

    def test_saylacian_text_rejects_changed_payload(self):
        package = encode_saylacian_text("\ue000", "Borama")
        changed = package.replace('"text":"\\ue000"', '"text":"\\ue001"')

        with self.assertRaisesRegex(ValueError, "checksum"):
            decode_saylacian_text(changed)

    def test_saylacian_text_rejects_oversized_envelope_before_json_parsing(self):
        package = MAGIC + (" " * MAX_PACKAGE_LENGTH)

        with self.assertRaisesRegex(ValueError, "too large"):
            decode_saylacian_text(package)

    def test_ordinary_text_and_non_string_values_are_not_packages(self):
        self.assertIsNone(decode_saylacian_text("hello"))
        self.assertIsNone(decode_saylacian_text(None))

    def test_copy_image_payload_includes_png_dib_and_latin_alt_text(self):
        formats = dict(formats_as_image("Borama", "\ue000", "a"))

        with Image.open(BytesIO(formats["PNG"])) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size[0], 1500)
            self.assertGreater(image.size[1], 0)
        header_size, width, height, planes, bits_per_pixel = struct.unpack(
            "<IiiHH", formats["CF_DIB"][:16]
        )
        self.assertEqual(
            (header_size, width, planes, bits_per_pixel), (40, 1500, 1, 24)
        )
        self.assertGreater(height, 0)
        self.assertIn("Latin reading: a", formats["CF_UNICODETEXT"].decode("utf-16-le"))

    def test_copy_text_payload_has_tagged_plain_text_rtf_and_html_forms(self):
        formats = dict(formats_as_saylacian_text("Borama", "\ue000", "a"))

        self.assertEqual(
            decode_saylacian_text(
                formats["CF_UNICODETEXT"].decode("utf-16-le").rstrip("\0")
            ).text,
            "\ue000",
        )
        self.assertIn(b"Saylacian Borama Chart", formats["Rich Text Format"])
        self.assertIn(b"font-family:Saylacian Borama Chart", formats["HTML Format"])
        self.assertTrue(formats["Saylacian Text v1"].startswith(MAGIC.encode("ascii")))


if __name__ == "__main__":
    unittest.main()
