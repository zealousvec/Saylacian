# SPDX-License-Identifier: AGPL-3.0-or-later
"""Show whether Kivy's SDL text provider renders the bundled Coptic font."""

from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.uix.label import Label

ROOT = Path(__file__).resolve().parents[1]
FONT = str(ROOT / "assets/NotoSansCoptic-Regular.ttf")
LabelBase.register(name="SaylacianCoptic", fn_regular=FONT)


class FontProbe(App):
    def build(self):
        return Label(text="ⲁⲃⲅ ⳟⳡⳣⳝ ϣϫϭϯ", font_name="SaylacianCoptic", font_size=48)

    def on_start(self):
        Clock.schedule_once(self.capture, 1)

    def capture(self, dt):
        Window.screenshot(name=str(ROOT / "docs/previews/coptic-font-probe.png"))
        Clock.schedule_once(lambda _: self.stop(), 0.4)


FontProbe().run()
