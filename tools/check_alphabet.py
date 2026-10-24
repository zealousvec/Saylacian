# SPDX-License-Identifier: AGPL-3.0-or-later
"""Live alphabet/input-aid check; no operating-system input automation."""

import json
import socket
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from kivy.clock import Clock
from kivy.core.window import Window

from main import SaylacianApp

socket.socket.connect = lambda *args, **kwargs: (_ for _ in ()).throw(
    AssertionError("network")
)


class CheckAlphabet(SaylacianApp):
    def on_start(self):
        super().on_start()
        Clock.schedule_once(self.check, 0.5)

    def check(self, dt):
        home = self.root.get_screen("home")
        home.ids.input_text.text = "dhagax!"
        self.show_alphabet()
        assert self.root.current == "alphabet"
        assert len(self.root.get_screen("alphabet").ids.letters.children) == 30
        self.insert_letter("𐒁")
        assert home.ids.input_text.text == "dhagax!"
        self.close_picker()
        self.open_picker("source")
        self.choose("Osmanya")
        assert self.source == "Osmanya" and self.target == "Somali Latin"
        assert home.ids.input_text.text == "𐒊𐒖𐒌𐒖𐒄!"
        home.ids.input_text.cursor = home.ids.input_text.get_cursor_from_index(
            len(home.ids.input_text.text)
        )
        self.show_alphabet()
        self.insert_letter("𐒁")
        assert home.ids.output_text.text == "dhagax!b"
        Window.size = (390, 780)
        Clock.schedule_once(self.capture, 0.5)

    def capture(self, dt):
        Window.screenshot(name=str(PROJECT / "docs/previews/osmanya-alphabet.png"))
        (PROJECT / "docs/alphabet-ui-results.json").write_text(
            json.dumps(
                {
                    "pass": True,
                    "checks": [
                        "30 assigned letter cells",
                        "Latin input preserved when insertion disallowed",
                        "selecting opposite language swaps actual output",
                        "Osmanya insertion updates live reverse conversion",
                    ],
                    "network": "blocked",
                },
                indent=2,
            )
        )
        self.stop()


CheckAlphabet().run()
