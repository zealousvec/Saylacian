# SPDX-License-Identifier: AGPL-3.0-or-later

"""Launches a preview of the recovered original Kivy interface."""

import os
from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp


class MainScreen(Screen):
    pass


class SecondWindow(Screen):
    pass


class MainLayout(ScreenManager):
    pass


Factory.register("Translator", cls=TextInput)


class OriginalPreview(MDApp):
    def build(self):
        self.title = "Saylacian — oldest original (94ded65), compatibility preview"
        self.theme_cls.theme_style = "Dark"
        return Builder.load_file("main.kv")

    def on_start(self):
        Clock.schedule_once(
            lambda dt: Window.screenshot(
                name=str(Path(os.environ["SAYLACIAN_PREVIEW"]) / "original.png")
            ),
            2,
        )

    def switch_language(self, button):
        pass

    def copy_first(self):
        pass

    def copy_second(self):
        pass


OriginalPreview().run()
