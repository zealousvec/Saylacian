# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests language-pack manifests, downloads, checksums, installation, and storage."""

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from saylacian.core.model_packs import ModelPackManager, get_pack_specs
from saylacian.core.translation import model_directory


class ModelPackTests(unittest.TestCase):
    def test_pinned_packs_include_reproducible_sources_and_sizes(self):
        first = get_pack_specs()
        second = get_pack_specs()
        self.assertEqual(set(first), {"somali", "french"})
        for pack_id in first:
            self.assertEqual(first[pack_id]["version"], second[pack_id]["version"])
            self.assertGreater(first[pack_id]["download_bytes"], 0)
            self.assertTrue(first[pack_id]["license"])
            self.assertIn("ctranslate2", first[pack_id]["runtimes"])
            self.assertTrue(first[pack_id]["model_repositories"])
            self.assertTrue(
                all(
                    item["url"].startswith("https://")
                    for item in first[pack_id]["assets"]
                    if "url" in item
                )
            )
        self.assertEqual(
            {asset["pair"] for asset in first["french"]["assets"]}, {"en_fr", "fr_en"}
        )

    def test_download_verifies_hash_installs_version_and_reports_progress(self):
        content = b"model bytes"
        item = {
            "kind": "file",
            "url": "https://huggingface.co/test/model.bin",
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "destination": "somali/en_so/model.bin",
        }
        spec = {
            "somali": {
                "id": "somali",
                "title": "Somali",
                "version": "1-test",
                "license": "Apache-2.0",
                "runtimes": {"ctranslate2": "4.8.3"},
                "model_repositories": ["test/model"],
                "download_bytes": len(content),
                "assets": [item],
            }
        }
        progress = []
        with tempfile.TemporaryDirectory() as temporary:
            manager = ModelPackManager(Path(temporary), spec)
            with patch(
                "saylacian.core.model_packs.urllib.request.urlopen",
                return_value=io.BytesIO(content),
            ):
                installed = manager.install(
                    "somali",
                    lambda done, total, label: progress.append((done, total, label)),
                )
            self.assertTrue((installed / "installed.json").is_file())
            manifest = json.loads(
                (installed / "installed.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["license"], "Apache-2.0")
            self.assertEqual(manifest["runtimes"]["ctranslate2"], "4.8.3")
            self.assertEqual(manifest["model_repositories"], ["test/model"])
            self.assertEqual(
                (installed / "somali/en_so/model.bin").read_bytes(), content
            )
            self.assertEqual(manager.active_model_roots(), [installed])
            self.assertEqual(manager.list_packs()[0]["installed_bytes"], len(content))
            self.assertEqual(progress[-1][:2], (len(content), len(content)))
            self.assertIn("Installed and verified", progress[-1][2])

    def test_generated_compatibility_config_is_checksum_verified(self):
        content = {
            "add_source_bos": False,
            "add_source_eos": False,
            "bos_token": "<s>",
            "decoder_start_token": "</s>",
            "eos_token": "</s>",
            "layer_norm_epsilon": 0.00001,
            "unk_token": "<unk>",
            "model_type": "marian",
        }
        data = json.dumps(content, ensure_ascii=False).encode("utf-8")
        asset = {
            "kind": "generated-json",
            "content": content,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "destination": "somali/en_so/config.json",
        }
        spec = {
            "somali": {
                "id": "somali",
                "title": "Somali",
                "version": "1-config",
                "download_bytes": 0,
                "assets": [asset],
            }
        }
        with tempfile.TemporaryDirectory() as temporary:
            manager = ModelPackManager(Path(temporary), spec)
            installed = manager.install("somali")
            self.assertEqual((installed / asset["destination"]).read_bytes(), data)
            self.assertEqual(manager.list_packs()[0]["installed_bytes"], len(data))

    def test_bad_hash_leaves_no_active_partial_pack(self):
        content = b"wrong bytes"
        item = {
            "kind": "file",
            "url": "https://huggingface.co/test/model.bin",
            "bytes": len(content),
            "sha256": "0" * 64,
            "destination": "somali/en_so/model.bin",
        }
        spec = {
            "somali": {
                "id": "somali",
                "title": "Somali",
                "version": "1-test",
                "download_bytes": len(content),
                "assets": [item],
            }
        }
        with tempfile.TemporaryDirectory() as temporary:
            manager = ModelPackManager(Path(temporary), spec)
            with patch(
                "saylacian.core.model_packs.urllib.request.urlopen",
                return_value=io.BytesIO(content),
            ):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    manager.install("somali")
            self.assertEqual(manager.active_model_roots(), [])
            self.assertEqual(list((Path(temporary) / "somali").glob("1-test")), [])

    def test_installed_pack_is_used_by_offline_route_and_removal_is_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = Path(temporary) / "packs"
            pack_root = store / "somali" / "1-test"
            folder = pack_root / "somali" / "en_so"
            folder.mkdir(parents=True)
            names = (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            )
            files = []
            for name in names:
                path = folder / name
                path.write_bytes(b"x")
                files.append(
                    {
                        "path": f"somali/en_so/{name}",
                        "bytes": 1,
                        "sha256": hashlib.sha256(b"x").hexdigest(),
                    }
                )
            (pack_root / "installed.json").write_text(
                json.dumps({"version": "1-test", "files": files}), encoding="utf-8"
            )
            home = store / "somali"
            home.mkdir(parents=True, exist_ok=True)
            (home / "current.json").write_text(
                json.dumps({"version": "1-test"}), encoding="utf-8"
            )
            with (
                patch(
                    "saylacian.core.model_packs.default_store_root", return_value=store
                ),
                patch(
                    "saylacian.core.translation.MODEL_ROOT",
                    Path(temporary) / "empty-bundled-models",
                ),
            ):
                self.assertEqual(
                    model_directory("English", "Somali Latin"), folder.resolve()
                )
            manager = ModelPackManager(
                store,
                {
                    "somali": {
                        "title": "Somali",
                        "version": "1-test",
                        "assets": [],
                        "download_bytes": 0,
                    }
                },
            )
            manager.remove("somali")
            self.assertFalse(home.exists())
            self.assertFalse((Path(temporary) / "empty-bundled-models").exists())


if __name__ == "__main__":
    unittest.main()
