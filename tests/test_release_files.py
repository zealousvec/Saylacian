# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests release file safety and repository packaging rules."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseFileTests(unittest.TestCase):
    def test_kivy_runtime_does_not_pull_optional_flask_site(self):
        runtime = (
            (ROOT / "requirements-runtime-lock.txt")
            .read_text(encoding="utf-8")
            .casefold()
        )
        website = (
            (ROOT / "requirements-website.txt").read_text(encoding="utf-8").casefold()
        )
        self.assertNotIn("flask", runtime)
        self.assertIn("flask", website)

    def test_model_weights_are_ignored_but_manifests_are_kept(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("models/**", ignore)
        self.assertIn("!models/manifest.json", ignore)
        self.assertIn("!models/somali-manifest.json", ignore)
        self.assertTrue(
            (ROOT / "saylacian/core/data/afrislm_2b_model_manifest.json").is_file()
        )


if __name__ == "__main__":
    unittest.main()
