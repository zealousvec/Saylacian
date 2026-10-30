# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests chart-based Borama and Kaddare script mappings."""

import json
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

from saylacian.core.capabilities import get_capability
from saylacian.core.transliteration import detect_chart_script, transliterate

ROOT = Path(__file__).resolve().parents[1]


class HistoricalChartScriptTests(unittest.TestCase):
    def test_chart_mappings_are_traceable_and_keep_unreviewed_status(self):
        for script, expected_count in (("borama", 27), ("kaddare", 26)):
            with self.subTest(script=script):
                path = ROOT / "saylacian/core/data/scripts" / f"{script}.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(len(data["records"]), expected_count)
                self.assertEqual(data["review"]["reviewer_status"], "unreviewed")
                self.assertEqual(data["source"]["license"], "CC BY-SA 4.0")
                self.assertTrue(
                    all(item["source"]["url"].startswith("https://") for item in [data])
                )
                self.assertTrue(
                    all(
                        record["confidence"] == "chart-label only"
                        for record in data["records"]
                    )
                )

    def test_borama_partial_chart_round_trip_and_unknown(self):
        encoded = transliterate("dhag! q", "Somali Latin", "Borama")
        self.assertEqual(encoded.text, "\ue00a\ue000\ue00b! q")
        self.assertTrue(
            any("Unmapped letters" in warning for warning in encoded.warnings)
        )
        decoded = transliterate(encoded.text, "Borama", "Somali Latin")
        self.assertEqual(decoded.text, "dhag! q")
        self.assertEqual(detect_chart_script(encoded.text)[0], "Borama")

    def test_kaddare_longest_grapheme_and_round_trip(self):
        encoded = transliterate("shadh!", "Somali Latin", "Kaddare")
        self.assertEqual(encoded.text, "\ue10d\ue100\ue10e!")
        self.assertEqual(
            transliterate(encoded.text, "Kaddare", "Somali Latin").text,
            "shadh!",
        )

    def test_user_reported_borama_clipboard_text_decodes_readably(self):
        pasted = ",     ,"
        self.assertEqual(
            transliterate(pasted, "Borama", "Somali Latin").text,
            "hello, what is wrong with you,",
        )

    def test_chart_pua_is_not_claimed_as_standard_unicode(self):
        result = transliterate("q", "Somali Latin", "Borama")
        self.assertTrue(
            any("Limited conversion" in warning for warning in result.warnings)
        )
        self.assertTrue(any("no Q label" in warning for warning in result.warnings))
        with self.assertRaises(ValueError):
            transliterate("x", "Borama", "English")

    def test_bundle_fonts_render_every_supported_private_use_letter(self):
        for script in ("Borama", "Kaddare"):
            data = json.loads(
                (
                    ROOT / "saylacian/core/data/scripts" / f"{script.lower()}.json"
                ).read_text(encoding="utf-8")
            )
            cmap = TTFont(ROOT / "assets" / f"{script}Chart-Regular.ttf").getBestCmap()
            expected = {int("0x" + record["pua"][2:], 0) for record in data["records"]}
            self.assertTrue(expected <= set(cmap))

    def test_partial_chart_routes_are_registered_both_ways(self):
        self.assertEqual(
            get_capability("Somali Latin", "Borama", "transliteration")["status"],
            "alpha limited",
        )
        self.assertIsNotNone(
            get_capability("Kaddare", "Somali Latin", "transliteration")
        )


if __name__ == "__main__":
    unittest.main()
