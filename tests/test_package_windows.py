import tempfile
import unittest
from pathlib import Path

from tools.package_windows import (
    _create_store_assets,
    inspect_payload,
    manifest_xml,
    verify_msix,
)


class WindowsPackageTests(unittest.TestCase):
    def test_manifest_contains_store_identity_and_minimal_full_trust_permissions(self):
        manifest = manifest_xml(
            "Test.Saylacian",
            "CN=Saylacian Local Test",
            "Saylacian Test",
            "0.1.0.0",
        )

        self.assertIn('Name="Test.Saylacian"', manifest)
        self.assertIn('EntryPoint="Windows.FullTrustApplication"', manifest)
        self.assertIn('Name="runFullTrust"', manifest)
        self.assertIn('Name="internetClient"', manifest)
        self.assertNotIn("@@", manifest)

        from xml.etree import ElementTree

        ElementTree.fromstring(manifest)

    def test_manifest_rejects_missing_or_malformed_store_identity(self):
        for identity, publisher, version in (
            ("", "CN=Publisher", "0.1.0.0"),
            ("invalid id", "CN=Publisher", "0.1.0.0"),
            ("Test.Saylacian", "Publisher", "0.1.0.0"),
            ("Test.Saylacian", "CN=Publisher", "1.2.3"),
        ):
            with (
                self.subTest(identity=identity, publisher=publisher, version=version),
                self.assertRaises(ValueError),
            ):
                manifest_xml(identity, publisher, "Publisher", version)

    def test_store_assets_use_approved_black_and_white_palette(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            _create_store_assets(folder)

            for filename, size in (
                ("StoreLogo.png", 50),
                ("Square44x44Logo.png", 44),
                ("Square150x150Logo.png", 150),
            ):
                with self.subTest(filename=filename):
                    image = __import__("PIL.Image", fromlist=["Image"]).open(
                        folder / filename
                    )
                    self.assertEqual(image.size, (size, size))
                    self.assertEqual(image.getpixel((0, 0)), (0, 0, 0))

    def test_payload_rejects_model_weights_and_keeps_required_runtime_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            internal = root / "_internal"
            (internal / "app").mkdir(parents=True)
            (internal / "assets").mkdir()
            (internal / "saylacian" / "core" / "data").mkdir(parents=True)
            (internal / "app" / "main.kv").write_text("Screen:", encoding="utf-8")
            (internal / "assets" / "NotoSansOsmanya.ttf").write_bytes(b"font")
            (
                internal / "saylacian" / "core" / "data" / "model_manifest.json"
            ).write_text("{}", encoding="utf-8")
            (root / "Saylacian.exe").write_bytes(b"app")
            (internal / "LICENSE").write_text("license", encoding="utf-8")
            (internal / "THIRD_PARTY_NOTICES.md").write_text(
                "notices", encoding="utf-8"
            )
            self.assertEqual(inspect_payload(root), [])

            (internal / "models").mkdir()
            (internal / "models" / "model.gguf").write_bytes(b"weights")
            self.assertTrue(any("weights" in item for item in inspect_payload(root)))

    def test_msix_verifier_requires_expected_identity_and_release_files(self):
        import zipfile

        with tempfile.TemporaryDirectory() as temporary:
            package_path = Path(temporary) / "Saylacian.msix"
            manifest = manifest_xml(
                "Test.Saylacian",
                "CN=Saylacian Local Test",
                "Saylacian Test",
                "0.1.0.0",
            )
            required = (
                "Assets/StoreLogo.png",
                "Assets/Square44x44Logo.png",
                "Assets/Square150x150Logo.png",
                "Saylacian.exe",
                "_internal/LICENSE",
                "_internal/THIRD_PARTY_NOTICES.md",
            )
            with zipfile.ZipFile(package_path, "w") as package:
                package.writestr("AppxManifest.xml", manifest)
                for name in required:
                    package.writestr(name, "present")

            verify_msix(
                package_path,
                "Test.Saylacian",
                "CN=Saylacian Local Test",
                "0.1.0.0",
            )
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                verify_msix(
                    package_path,
                    "Different.Identity",
                    "CN=Saylacian Local Test",
                    "0.1.0.0",
                )


if __name__ == "__main__":
    unittest.main()
