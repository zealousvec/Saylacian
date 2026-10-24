# SPDX-License-Identifier: AGPL-3.0-or-later

"""Check the manual model-pack integration job without network downloads."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from saylacian.core.transliteration import Conversion
from tools.verify_pack_integration import verify_pack


class PackIntegrationTests(unittest.TestCase):
    def test_selected_pack_receipt_and_offline_routes_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "french" / "1-test"
            installed.mkdir(parents=True)
            (installed / "installed.json").write_text(
                json.dumps({"pack_id": "french", "version": "1-test"}),
                encoding="utf-8",
            )
            manager = SimpleNamespace(
                specs={"french": {"version": "1-test"}},
                install=Mock(return_value=installed),
                active_model_roots=Mock(return_value=[installed]),
            )
            translator = Mock(return_value=Conversion("translated"))

            routes = verify_pack("french", manager, translator)

        self.assertEqual(
            routes,
            [("English", "French", 10), ("French", "English", 10)],
        )
        self.assertEqual(translator.call_count, 2)
        self.assertTrue(
            all(
                call.kwargs["provider_override"] == "offline"
                for call in translator.call_args_list
            )
        )
        manager.install.assert_called_once_with("french", progress=None)

    def test_wrong_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "somali" / "1-test"
            installed.mkdir(parents=True)
            (installed / "installed.json").write_text(
                json.dumps({"pack_id": "french", "version": "1-test"}),
                encoding="utf-8",
            )
            manager = SimpleNamespace(
                specs={"somali": {"version": "1-test"}},
                install=Mock(return_value=installed),
                active_model_roots=Mock(return_value=[installed]),
            )

            with self.assertRaisesRegex(RuntimeError, "wrong pack id"):
                verify_pack("somali", manager, Mock())

    def test_unknown_pack_fails_before_install(self):
        manager = SimpleNamespace(install=Mock())

        with self.assertRaisesRegex(ValueError, "Unsupported pack"):
            verify_pack("nubian", manager, Mock())

        manager.install.assert_not_called()


if __name__ == "__main__":
    unittest.main()
