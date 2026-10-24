# SPDX-License-Identifier: AGPL-3.0-or-later

"""Checks that the recovered original Kivy interface remains intact."""

import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("KIVY_HOME", str(Path(__file__).resolve().parents[1] / ".kivy"))
PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from kivy.clock import Clock

from app.original_compat import OriginalApp


class CheckOriginal(OriginalApp):
    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, dt):
        self.root.get_screen("first").ids.first_input.text = "dhagax!"
        Clock.schedule_once(self.verify, 0.2)

    def verify(self, dt):
        assert self.root.get_screen("first").ids.second_input.text == "𐒊𐒖𐒌𐒖𐒄!"
        (PROJECT / "docs/rollback-test.json").write_text(
            json.dumps(
                {
                    "original_ui_loaded": True,
                    "new_core_conversion": True,
                    "core_sha256": hashlib.sha256(
                        (PROJECT / "saylacian/core/transliteration.py").read_bytes()
                    ).hexdigest(),
                }
            )
        )
        self.stop()


CheckOriginal().run()
