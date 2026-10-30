# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compatibility adapter for oldest recovered KV; core stays unchanged."""

from pathlib import Path

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp

from saylacian.core.transliteration import transliterate

PROJECT = Path(__file__).resolve().parents[1]


class MainScreen(Screen):
    pass


class SecondWindow(Screen):
    pass


class MainLayout(ScreenManager):
    pass


class Translator(TextInput):
    def on_text(self, *args):
        if self.readonly:
            return
        Clock.schedule_once(lambda dt: MDApp.get_running_app().convert_original(), 0)


Factory.register("Translator", cls=Translator)


class OriginalApp(MDApp):
    def build(self):
        self.title = "Saylacian - original UI with current core"
        self.theme_cls.theme_style = "Dark"
        self.reverse = False

        from kivy.resources import resource_add_path

        resource_add_path(str(PROJECT / "assets/original"))
        return Builder.load_file(str(PROJECT / "app/original.kv"))

    def convert_original(self):
        if not self.root:
            return
        screen = self.root.get_screen("first")
        try:
            source, target = (
                ("Osmanya", "Somali Latin")
                if self.reverse
                else ("Somali Latin", "Osmanya")
            )
            screen.ids.second_input.text = transliterate(
                screen.ids.first_input.text, source, target
            ).text
        except ValueError as error:
            screen.ids.second_input.text = str(error)

    def copy_first(self):
        Clipboard.copy(self.root.get_screen("first").ids.first_input.text)

    def copy_second(self):
        Clipboard.copy(self.root.get_screen("first").ids.second_input.text)

    def switch_language(self, button):
        self.reverse = not self.reverse
        screen = self.root.get_screen("first")
        screen.ids.btn1.text, screen.ids.btn2.text = (
            screen.ids.btn2.text,
            screen.ids.btn1.text,
        )
        self.convert_original()
