# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools.build_windows_portable import (
    build_environment,
    payload_manifest,
    restore_legacy_font_path,
    source_metadata,
    verify_zip,
    write_checksums,
)


class PortablePackageTests(unittest.TestCase):
    def test_manifest_records_tree_fingerprint_and_dirty_state(self):
        metadata = source_metadata()
        self.assertEqual(len(metadata["source_commit"]), 40)
        self.assertEqual(len(metadata["source_tree_sha256"]), 64)
        self.assertIsInstance(metadata["source_tree_dirty"], bool)

    @unittest.skipUnless(os.name == "nt", "Windows PATH separator test")
    def test_build_path_drops_unrelated_codex_and_poppler_dll_sources(self):
        with patch.dict(
            "os.environ",
            {
                "PATH": (
                    "C:\\Python;C:\\Users\\test\\.cache\\codex-runtimes\\poppler;"
                    "C:\\Windows\\System32"
                )
            },
        ):
            entries = build_environment()["PATH"].split(";")
        self.assertEqual(entries, ["C:\\Python", "C:\\Windows\\System32"])

    def test_builder_config_is_isolated_from_user_caches(self):
        with tempfile.TemporaryDirectory() as folder:
            config_root = Path(folder) / "builder-config"
            environment = build_environment(config_root)
        self.assertEqual(
            environment["PYINSTALLER_CONFIG_DIR"],
            str(config_root / "pyinstaller"),
        )
        self.assertEqual(environment["KIVY_HOME"], str(config_root / "kivy"))

    def test_legacy_font_is_copied_under_pyinstaller_internal_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            payload = Path(folder) / "Saylacian"
            assets = payload / "_internal" / "assets"
            assets.mkdir(parents=True)
            source = assets / "NotoSansOsmanya.ttf"
            source.write_bytes(b"font bytes")

            destination = restore_legacy_font_path(payload)

            self.assertEqual(
                destination.relative_to(payload).as_posix(),
                "_internal/assets/original/Fonts/Noto Sans Osmanya.ttf",
            )
            self.assertEqual(destination.read_bytes(), b"font bytes")

    def test_manifest_checksums_and_zip_match_exact_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = root / "Saylacian"
            payload.mkdir()
            (payload / "Saylacian.exe").write_bytes(b"test executable")
            (payload / "docs").mkdir()
            (payload / "docs" / "USER_GUIDE.txt").write_text(
                "User help", encoding="utf-8"
            )
            manifest = payload_manifest(payload)
            self.assertEqual(manifest["app_version"], "0.1.0a1")
            self.assertFalse(manifest["runtime_verified"])
            write_checksums(payload, manifest)
            archive = root / "Saylacian-Portable.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                for path in payload.rglob("*"):
                    if path.is_file():
                        bundle.write(
                            path,
                            f"Saylacian/{path.relative_to(payload).as_posix()}",
                        )

            verify_zip(archive, manifest)

    def test_manifest_detects_unlisted_archive_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = root / "Saylacian"
            payload.mkdir()
            (payload / "Saylacian.exe").write_bytes(b"expected")
            manifest = payload_manifest(payload)
            archive = root / "Saylacian-Portable.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("Saylacian/Saylacian.exe", b"expected")
                bundle.writestr("Saylacian/unexpected.txt", b"extra")
            with self.assertRaisesRegex(ValueError, "contents differ"):
                verify_zip(archive, manifest)


if __name__ == "__main__":
    unittest.main()
