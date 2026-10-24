# SPDX-License-Identifier: AGPL-3.0-or-later
"""Open and render the licensed Borama/Kaddare reference charts in live Kivy."""

import socket
import sys
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from main import SaylacianApp


def deny(*args, **kwargs):
    raise AssertionError("Network access attempted")


socket.socket.connect = deny


class ChartCheck(SaylacianApp):
    def on_start(self):
        super().on_start()
        name = sys.argv[1] if len(sys.argv) > 1 else "Borama"
        Clock.schedule_once(lambda dt: self.show_chart(name), 0.6)

    def show_chart(self, name):
        self.show_script_reference(name)
        image = self.root.get_screen("alphabet").ids.letters.children[0]
        assert Path(image.source).name == f"{name}_Alphabet_Chart.jpg"
        Clock.schedule_once(lambda dt: self.capture(name, image), 1.0)

    def capture(self, name, image):
        assert image.texture is not None and image.texture.width > 0
        Window.screenshot(
            name=str(PROJECT / f"docs/previews/{name.lower()}-reference.png")
        )
        Clock.schedule_once(lambda dt: self.stop(), 0.4)


ChartCheck().run()
