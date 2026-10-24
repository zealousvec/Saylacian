# SPDX-License-Identifier: AGPL-3.0-or-later

"""Checks concise picker labels without changing internal route identifiers."""

import unittest

from saylacian.core.capabilities import list_capabilities
from saylacian.core.presentation import display_name, picker_choices


class PresentationTests(unittest.TestCase):
    def test_concise_labels_keep_route_names_internal(self):
        self.assertEqual(display_name("Somali Latin"), "Somali")
        self.assertEqual(display_name("Old Nubian (Coptic)"), "Old Nubian")
        self.assertEqual(display_name("Old Nubian scholarly Latin"), "Latin reading")
        self.assertEqual(display_name("Osmanya"), "Osmanya")

    def test_translation_picker_contains_only_meaning_routes(self):
        choices = picker_choices(list_capabilities(), "translation")
        names = {name for name, _ in choices}
        self.assertTrue({"English", "French", "Somali Latin"}.issubset(names))
        self.assertNotIn("Osmanya", names)
        self.assertNotIn("Nobiin (Nubian)", names)
        self.assertTrue(any("needs fluent review" in note for _, note in choices))

    def test_script_picker_keeps_old_nubian_separate_and_hides_modern_research(self):
        choices = picker_choices(list_capabilities(), "transliteration")
        names = {name for name, _ in choices}
        self.assertTrue(
            {
                "Somali Latin",
                "Osmanya",
                "Old Nubian (Coptic)",
                "Old Nubian scholarly Latin",
                "Borama",
                "Kaddare",
            }.issubset(names)
        )
        self.assertNotIn("Nobiin (Nubian)", names)
        self.assertNotIn("Dongolawi / Andaandi (Nubian)", names)


if __name__ == "__main__":
    unittest.main()
