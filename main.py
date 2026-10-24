# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saylacian Kivy/KivyMD app."""

import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
os.environ.setdefault("KIVY_NO_ARGS", "1")
runtime_home = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Saylacian/kivy-v1"
)
os.environ.setdefault(
    "KIVY_HOME",
    str(runtime_home if getattr(sys, "frozen", False) else PROJECT / ".kivy"),
)
if "--self-test" in sys.argv:
    import socket

    os.environ.setdefault("SAYLACIAN_TRANSLATION_PROVIDER", "offline")

    def deny_network(*args, **kwargs):
        raise AssertionError("Network access attempted during offline test")

    socket.socket.connect = deny_network
from concurrent.futures import ThreadPoolExecutor

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.tooltip import MDTooltip

from saylacian.core.capabilities import get_capability, list_capabilities
from saylacian.core.clipboard_repr import (
    formats_as_image,
    formats_as_latin,
    formats_as_saylacian_text,
)
from saylacian.core.diagnostics import PrivateDiagnostics, install_exception_hooks
from saylacian.core.history import History
from saylacian.core.interchange import (
    decode_saylacian_text,
    identify_chart_text,
)
from saylacian.core.language_detection import detect_language
from saylacian.core.model_packs import ModelPackManager
from saylacian.core.online_translation import (
    online_provider_label,
    online_translation_enabled,
)
from saylacian.core.script_info import osmanya_letters
from saylacian.core.translation import model_directory, translate_meaning
from saylacian.core.transliteration import detect_script, transliterate
from saylacian.core.windows_clipboard import publish as publish_windows_clipboard


class HomeScreen(Screen):
    pass


class PickerScreen(Screen):
    pass


class SavedScreen(Screen):
    pass


class ScriptInfoScreen(Screen):
    pass


class PacksScreen(Screen):
    pass


def clipboard_text(text):
    """Use readable Latin for nonstandard chart glyphs copied outside the app."""
    script, _ = detect_script(text)
    if script in ("Borama", "Kaddare"):
        return transliterate(text, script, "Somali Latin").text, script
    if any(0xE000 <= ord(char) <= 0xF8FF for char in text):
        return None, None
    return text, None


class SaylacianTextInput(TextInput):
    def copy(self, data=""):
        selected = data or self.selection_text
        portable, _ = clipboard_text(selected)
        if portable is None:
            app = MDApp.get_running_app()
            app.status = "Unknown private-use text was not copied."
            return None
        return super().copy(portable)


Factory.register("SaylacianTextInput", cls=SaylacianTextInput)


class ActionIcon(MDIconButton, MDTooltip):
    """Material action with a readable hover/long-press label."""


class SaylacianApp(MDApp):
    source = StringProperty("Somali Latin")
    target = StringProperty("Osmanya")
    mode = StringProperty("Convert writing system")
    wide_layout = BooleanProperty(False)
    status = StringProperty("Type Somali to convert its writing to Osmanya.")
    alternative_readings = StringProperty("")
    input_font = StringProperty("Roboto")
    output_font = StringProperty("Roboto")
    picker_heading = StringProperty("Choose source")
    script_heading = StringProperty("Osmanya alphabet")
    script_note = StringProperty("Select Osmanya as source to insert letters.")
    pack_status = StringProperty("Offline packs keep translating on this device.")
    pack_progress = NumericProperty(0)
    pack_storage = StringProperty("")
    pack_busy = BooleanProperty(False)

    def build(self):
        self.title = "Saylacian"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        self.font = str(PROJECT / "assets/NotoSansOsmanya.ttf")
        self.output_font = self.font
        self.side = "source"
        Window.minimum_width, Window.minimum_height = 320, 360
        Window.bind(on_resize=self.update_layout)
        self.update_layout(Window, *Window.size)
        self.worker = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="saylacian-translation"
        )
        self.pack_worker = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="saylacian-model-packs"
        )
        self.pack_manager = ModelPackManager()
        self.pending = None
        self.generation = 0
        self.translate_trigger = Clock.create_trigger(self.begin_translation, 0.45)
        return Builder.load_file(str(PROJECT / "app/main.kv"))

    def update_layout(self, window, width, height):
        """Use two panels when there is room, including short landscape windows."""
        self.wide_layout = width >= dp(760) or height <= dp(520)

    def on_start(self):
        Window.bind(on_keyboard=self.keyboard)
        self.diagnostics = PrivateDiagnostics(Path(self.user_data_dir) / "logs")
        try:
            self.diagnostics.start(version="source")
            install_exception_hooks(self.diagnostics)
        except OSError:
            self.diagnostics = None
        self.history = History(Path(self.user_data_dir) / "history-v1.json")
        if "--self-test" in sys.argv:
            from app.acceptance import start

            Clock.schedule_once(lambda dt: start(self), 1)

    def keyboard(self, window, key, *args):
        if key == 27 and self.root.current != "home":
            self.close_picker()
            return True

    def open_picker(self, side):
        self.side = side
        self.picker_heading = "Choose " + side
        self.root.get_screen("home").ids.input_text.focus = False
        self.root.get_screen("picker").ids.search.text = ""
        self.filter_languages("")
        self.root.current = "picker"

    def close_picker(self):
        self.root.current = "home"

    def open_packs(self):
        self.refresh_pack_screen()
        self.root.current = "packs"

    @staticmethod
    def _format_bytes(size):
        return f"{size / (1024 * 1024):.0f} MB"

    def refresh_pack_screen(self):
        if not self.root:
            return
        rows = self.root.get_screen("packs").ids.pack_rows
        rows.clear_widgets()
        packs = self.pack_manager.list_packs()
        for pack in packs:
            row = BoxLayout(
                orientation="horizontal", size_hint_y=None, height=dp(76), spacing=dp(8)
            )
            details = BoxLayout(orientation="vertical")
            title = MDLabel(
                text=pack["title"],
                bold=True,
                size_hint_y=0.55,
                halign="left",
                valign="middle",
            )
            if pack["installed"]:
                note = f"Installed v{pack['installed_version']} · {self._format_bytes(pack['installed_bytes'])} on device"
            else:
                note = f"Download {self._format_bytes(pack['download_bytes'])} · works offline"
            subtitle = MDLabel(
                text=note,
                theme_text_color="Custom",
                text_color=(0.68, 0.68, 0.68, 1),
                font_style="Caption",
                size_hint_y=0.45,
                halign="left",
                valign="middle",
            )
            details.add_widget(title)
            details.add_widget(subtitle)
            row.add_widget(details)
            button = Button(
                text="Remove" if pack["installed"] else "Download",
                size_hint=(None, None),
                size=(dp(96), dp(42)),
                color=(0.9, 0.95, 0.96, 1),
                background_normal="",
                background_down="",
                background_color=(0.12, 0.2, 0.22, 1),
                font_size="14sp",
            )
            if self.pack_busy:
                button.disabled = True
            elif pack["installed"]:
                button.bind(
                    on_release=lambda _button, pid=pack["id"]: self.confirm_remove_pack(
                        pid
                    )
                )
            else:
                button.bind(
                    on_release=lambda _button, pid=pack["id"]: self.start_pack_download(
                        pid
                    )
                )
            row.add_widget(button)
            rows.add_widget(row)
        total_storage = sum(pack["storage_bytes"] for pack in packs)
        self.pack_storage = f"Offline models use {self._format_bytes(total_storage)}. Older pack versions are kept until you remove the pack."

    def start_pack_download(self, pack_id):
        if self.pack_busy:
            return
        self.pack_busy = True
        self.pack_progress = 0
        self.pack_status = "Preparing verified model download..."
        self.refresh_pack_screen()
        future = self.pack_worker.submit(
            self.pack_manager.install, pack_id, self._pack_download_progress
        )
        future.add_done_callback(
            lambda completed: Clock.schedule_once(
                lambda _dt: self.finish_pack_download(completed), 0
            )
        )

    def _pack_download_progress(self, completed, total, message):
        percent = completed * 100 / total if total else 100
        Clock.schedule_once(
            lambda _dt, p=percent, m=message: self.update_pack_progress(p, m), 0
        )

    def update_pack_progress(self, percent, message):
        self.pack_progress = max(0, min(100, percent))
        self.pack_status = message

    def finish_pack_download(self, future):
        self.pack_busy = False
        try:
            installed = future.result()
        except Exception as error:
            self.pack_status = f"Download stopped: {error}"
        else:
            self.pack_progress = 100
            self.pack_status = f"Pack installed and checksum-verified: {installed.name}"
        self.refresh_pack_screen()

    def confirm_remove_pack(self, pack_id):
        title = self.pack_manager.specs[pack_id]["title"]
        dialog = MDDialog(
            title="Remove offline pack?",
            text=f"Remove {title} and all its saved versions to free storage? This does not affect your app or backups.",
            buttons=[
                MDFlatButton(text="KEEP", on_release=lambda *_: dialog.dismiss()),
                MDFlatButton(
                    text="REMOVE",
                    on_release=lambda *_: self.remove_pack(dialog, pack_id),
                ),
            ],
        )
        self.pack_dialog = dialog
        dialog.open()

    def remove_pack(self, dialog, pack_id):
        dialog.dismiss()
        try:
            self.pack_manager.remove(pack_id)
        except (OSError, ValueError) as error:
            self.pack_status = f"Could not remove pack: {error}"
        else:
            self.pack_status = "Offline pack removed."
        self.refresh_pack_screen()

    def filter_languages(self, query):
        if not self.root:
            return
        box = self.root.get_screen("picker").ids.options
        box.clear_widgets()
        capabilities = list_capabilities()
        route_names = list(
            dict.fromkeys(
                name
                for route in capabilities
                if route["kind"] == "route"
                for name in (route["source"], route["target"])
            )
        )
        choices = [("Detect language/script", "Detect English, French or Somali")]
        online = online_translation_enabled()
        for name in route_names:
            routes = [
                route
                for route in capabilities
                if route["kind"] == "route"
                and name in (route["source"], route["target"])
            ]
            statuses = sorted({route["status"] for route in routes})
            note = (online_provider_label() + ": ") if online else "Downloaded models: "
            choices.append((name, note + ", ".join(statuses)))
        choices += [
            (item["source"] + " alphabet chart", item["selector_note"])
            for item in capabilities
            if item["kind"] == "script"
        ]
        current = getattr(self, self.side)
        for name, note in choices:
            if self.side == "target" and name == "Detect language/script":
                continue
            if query.casefold() not in (name + note).casefold():
                continue
            button = TwoLineListItem(
                text=("Selected: " if name == current else "") + name,
                secondary_text=note,
                size_hint_x=1,
                height=dp(72),
                on_release=lambda b, n=name: self.choose(n),
            )
            box.add_widget(button)

    def choose(self, name):
        if name.endswith(" alphabet chart"):
            self.show_script_reference(name.removesuffix(" alphabet chart"))
            return
        unavailable = self._choice_note(name)
        if unavailable:
            self.root.get_screen("home").ids.output_text.text = ""
            self.status = unavailable
            self.close_picker()
            return
        other_side = "target" if self.side == "source" else "source"
        if name == getattr(self, other_side) and self.source != self.target:
            self.swap()
            self.close_picker()
            return
        setattr(self, self.side, name)
        self.complete_supported_pair()
        self.close_picker()
        self.refresh_fonts()
        self.convert(self.root.get_screen("home").ids.input_text.text)

    def complete_supported_pair(self):
        """Keep picker choices on a route implemented for the active mode."""
        mode = "translation" if self.mode == "Translate meaning" else "transliteration"
        routes = [item for item in list_capabilities(mode) if item["kind"] == "route"]
        if self.side == "source":
            targets = [
                route["target"] for route in routes if route["source"] == self.source
            ]
            if targets and self.target not in targets:
                self.target = targets[0]
        else:
            sources = [
                route["source"] for route in routes if route["target"] == self.target
            ]
            if sources and self.source not in sources:
                self.source = sources[0]

    @staticmethod
    def _choice_note(name):
        if name.endswith(" (Nubian)"):
            return f"{name[:-9]} conversion unavailable: variety-specific mapping not verified."
        return ""

    def font_for(self, language_or_script):
        chart_fonts = {
            "Borama": ("SaylacianBorama", "BoramaChart-Regular.ttf"),
            "Kaddare": ("SaylacianKaddare", "KaddareChart-Regular.ttf"),
        }
        if language_or_script in chart_fonts:
            name, filename = chart_fonts[language_or_script]
            LabelBase.register(name=name, fn_regular=str(PROJECT / "assets" / filename))
            return name
        if "Coptic" in language_or_script:
            LabelBase.register(
                name="SaylacianCoptic",
                fn_regular=str(PROJECT / "assets/NotoSansCoptic-Regular.ttf"),
            )
            return "SaylacianCoptic"
        if language_or_script == "Osmanya":
            return self.font
        return "Roboto"

    def refresh_fonts(self):
        self.input_font = self.font_for(self.source)
        self.output_font = self.font_for(self.target)
        if self.root:
            home = self.root.get_screen("home")
            home.ids.input_text.font_name = self.input_font
            home.ids.output_text.font_name = self.output_font

            home.ids.input_text._refresh_line_options()
            home.ids.output_text._refresh_line_options()

    def convert(self, text):
        if not self.root:
            return
        self.alternative_readings = ""
        self.generation += 1
        self.translate_trigger.cancel()
        if self.pending:
            self.pending.cancel()
        output = self.root.get_screen("home").ids.output_text
        output.text = ""
        if not text.strip():
            self.status = "Enter text to begin."
            return
        if len(text) > 4000:
            self.status = "Maximum 4,000 characters."
            return
        if self.mode == "Translate meaning":
            translation_source = self.source
            self.detected_language = None
            if self.source == "Detect language/script":
                detected_script, script_message = detect_script(text)
                if detected_script:
                    self.input_font = self.font_for(detected_script)
                    input_widget = self.root.get_screen("home").ids.input_text
                    input_widget.font_name = self.input_font
                    input_widget._refresh_line_options()
                    self.status = (
                        script_message + " Script detection is not meaning translation."
                    )
                    return
                translation_source, confidence, message = detect_language(text)
                if translation_source is None:
                    self.status = message
                    return
                self.detected_language = (translation_source, confidence)
            try:
                online = online_translation_enabled()
                if not online:
                    model_directory(translation_source, self.target)
                detected = ""
                if self.detected_language:
                    detected = (
                        f"Detected {translation_source} ({confidence:.0%} confidence). "
                    )
                route = (
                    "Sending text to " + online_provider_label() + "..."
                    if online
                    else "Translating with downloaded model..."
                )
                self.status = detected + route
                self.translate_trigger()
            except ValueError as error:
                self.status = str(error)
            return
        source = self.source
        detection_note = ""
        unavailable = self._choice_note(source) or self._choice_note(self.target)
        if unavailable:
            self.status = unavailable
            return
        if source == "Detect language/script":
            source, message = detect_script(text)
            if source is None:
                self.input_font = "Roboto"
                source, confidence, message = detect_language(text)
                if source is None:
                    self.status = message
                    return
            else:
                coptic_script = source == "Coptic script"
                if coptic_script:
                    source = "Old Nubian (Coptic)"
                    detection_note = (
                        "Coptic script detected; language is not inferred. "
                    )
                self.input_font = self.font_for(source)
                input_widget = self.root.get_screen("home").ids.input_text
                input_widget.font_name = self.input_font
                input_widget._refresh_line_options()
                if get_capability(source, self.target, "transliteration") is None:
                    self.status = (
                        "Coptic script detected; language is not inferred. Choose Old Nubian scholarly Latin for its table."
                        if coptic_script
                        else f"Detected {source}, but no verified writing conversion is available for the selected target."
                    )
                    return
                if self.target == source:
                    self.status = (
                        f"Detected {source}; choose a different script as target."
                    )
                    return
        try:
            result = transliterate(text, source, self.target)
            output.text = result.text
            warnings = " ".join(result.warnings)
            if result.alternatives:
                self.alternative_readings = "\nOther Coptic readings: " + " / ".join(
                    result.alternatives[:3]
                )
            self.status = (
                detection_note
                + (warnings + " " if warnings else "")
                + "Writing converted; meaning unchanged."
            )
        except ValueError as error:
            self.status = str(error)

    def on_input_text(self, text):
        """Choose the matching chart font when chart glyphs arrive by paste."""
        if text:
            try:
                package = decode_saylacian_text(text)
            except ValueError as error:
                self.status = str(error)
                return
            if package:
                input_widget = self.root.get_screen("home").ids.input_text
                self.mode = "Convert writing system"
                self.source, self.target = package.script, "Somali Latin"
                self.refresh_fonts()
                input_widget.text = package.text
                self.status = (
                    f"Imported Saylacian Text v1 ({package.script}); script preserved."
                )
                return
            detected, _ = detect_script(text)
            if detected in ("Borama", "Kaddare"):
                self.mode = "Convert writing system"
                self.source = detected
                self.target = "Somali Latin"
                self.refresh_fonts()
            elif any(0xE000 <= ord(char) <= 0xF8FF for char in text):
                input_widget = self.root.get_screen("home").ids.input_text
                input_widget.font_name = "Roboto"
                input_widget._refresh_line_options()
                self.status = (
                    "Unrecognized private-use text. Clipboard does not carry its font; "
                    "this text uses a different or unknown character mapping."
                )
                return
        self.convert(text)

    def begin_translation(self, dt):
        generation = self.generation
        text = self.root.get_screen("home").ids.input_text.text
        source = (
            self.detected_language[0]
            if self.mode == "Translate meaning" and self.detected_language
            else self.source
        )
        self.pending = self.worker.submit(translate_meaning, text, source, self.target)

        def finished(future):
            if future.cancelled():
                return
            try:
                result = future.result()
                Clock.schedule_once(
                    lambda dt, r=result: self.show_translation(generation, r, None)
                )
            except Exception as error:
                if self.diagnostics:
                    self.diagnostics.record_exception("translation-worker", error)
                message = (
                    str(error)
                    if isinstance(error, ValueError)
                    else "Translation could not complete. Check provider setup and local diagnostics."
                )
                Clock.schedule_once(
                    lambda dt, message=message: self.show_translation(
                        generation, None, message
                    )
                )

        self.pending.add_done_callback(finished)

    def show_translation(self, generation, result, error):
        if generation != self.generation:
            return
        if error:
            self.status = "Translation failed: " + error
            return
        self.root.get_screen("home").ids.output_text.text = result.text
        warnings = " ".join(result.warnings)
        if self.mode == "Translate meaning" and self.detected_language:
            language, confidence = self.detected_language
            warnings = f"Detected {language} ({confidence:.0%} confidence). " + warnings
        self.status = warnings

    def on_stop(self):
        self.generation += 1
        self.translate_trigger.cancel()
        self.worker.shutdown(wait=False, cancel_futures=True)
        if getattr(self, "diagnostics", None):
            self.diagnostics.close()

    def swap(self):
        screen = self.root.get_screen("home")
        if self.source == "Detect language/script":
            self.status = "Select explicit source before swapping."
            return
        text = screen.ids.output_text.text
        self.source, self.target = self.target, self.source
        self.refresh_fonts()
        if text:
            screen.ids.input_text.text = text
        else:
            self.convert(screen.ids.input_text.text)

    def switch_mode(self):
        self.mode = (
            "Translate meaning"
            if self.mode == "Convert writing system"
            else "Convert writing system"
        )
        self.convert(self.root.get_screen("home").ids.input_text.text)

    def paste(self):
        pasted = Clipboard.paste()
        self.root.get_screen("home").ids.input_text.text = pasted

    def show_alphabet(self):
        screen = self.root.get_screen("alphabet")
        self.script_heading = "Osmanya alphabet"
        self.script_note = "Somali writing system. The mapping is experimental; w/uu and y/ii share letters."
        grid = screen.ids.letters
        grid.cols = 3
        grid.clear_widgets()
        screen.ids.chart_status.text = "Select Osmanya as source to insert letters."
        for letter in osmanya_letters():
            cell = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(108))
            button = Button(
                text=letter["glyph"],
                font_name=self.font,
                font_size="28sp",
                background_normal="",
                background_color=(0.95, 0.95, 0.95, 1),
                color=(0.08, 0.08, 0.08, 1),
                on_release=lambda widget, glyph=letter["glyph"]: self.insert_letter(
                    glyph
                ),
            )
            cell.add_widget(button)
            cell.add_widget(
                Label(
                    text=letter["readings"] + "  " + letter["codepoint"],
                    font_size="12sp",
                    size_hint_y=None,
                    height=dp(28),
                )
            )
            grid.add_widget(cell)
        self.root.get_screen("home").ids.input_text.focus = False
        self.root.current = "alphabet"

    def show_script_reference(self, script):
        screen = self.root.get_screen("alphabet")
        self.root.get_screen("home").ids.output_text.text = ""
        self.status = script + " chart opened for reference."
        self.script_heading = script + " alphabet reference"
        self.script_note = (
            "Chart-label converter is partial and experimental. Output uses private-use code points; "
            "word spelling is unreviewed and text is not portable without the bundled font. "
            "Chart by Jugydmort, CC BY-SA 4.0. Source/license: notices/HISTORICAL_SCRIPT_CHARTS.md"
        )
        screen.ids.chart_status.text = "Experimental chart-label conversion is available; no standard Unicode encoding exists."
        grid = screen.ids.letters
        grid.clear_widgets()
        grid.cols = 1
        chart = PROJECT / "assets/research" / f"{script}_Alphabet_Chart.jpg"
        grid.add_widget(
            Image(
                source=str(chart),
                fit_mode="contain",
                size_hint=(1, None),
                height=dp(500),
            )
        )
        self.root.get_screen("home").ids.input_text.focus = False
        self.root.current = "alphabet"

    def insert_letter(self, glyph):
        if self.source != "Osmanya":
            self.root.get_screen(
                "alphabet"
            ).ids.chart_status.text = (
                "Choose Osmanya as source first; existing input is preserved."
            )
            return
        self.root.get_screen("home").ids.input_text.insert_text(glyph)
        self.root.get_screen(
            "alphabet"
        ).ids.chart_status.text = "Letter inserted. Back returns to your text."

    def copy(self, text):
        """Backward-compatible Copy as Latin action."""
        portable, script = clipboard_text(text)
        if not text:
            self.status = "Nothing to copy."
            return
        if portable is None:
            self.status = "Unknown private-use text was not copied."
            return
        try:
            if os.name == "nt":
                publish_windows_clipboard(formats_as_latin(portable))
            else:
                Clipboard.copy(portable)
        except (OSError, ValueError) as error:
            self.status = "Clipboard copy failed: " + str(error)
            return
        if script:
            self.status = f"Copied {script} reading in Somali Latin."
        else:
            self.status = "Copied to clipboard."

    def open_copy_menu(self, caller, text):
        if getattr(self, "copy_menu", None):
            self.copy_menu.dismiss()
        self._copy_menu_text = text
        entries = (
            ("Copy as Latin", "latin"),
            ("Copy as Image", "image"),
            ("Copy as Saylacian Text", "saylacian"),
        )
        self.copy_menu = MDDropdownMenu(
            caller=caller,
            width=dp(240),
            items=[
                {
                    "text": label,
                    "on_release": lambda mode=mode: self._copy_menu_action(mode),
                }
                for label, mode in entries
            ],
        )
        self.copy_menu.open()

    def _chart_content_for_copy(self, text):
        script = identify_chart_text(text)
        if script:
            glyphs = text
        elif self.target in ("Borama", "Kaddare") and self.source == "Somali Latin":
            script = self.target
            glyphs = transliterate(text, self.source, script).text
        elif self.source in ("Borama", "Kaddare") and self.target == "Somali Latin":
            script = self.source
            glyphs = transliterate(text, "Somali Latin", script).text
        else:
            raise ValueError(
                "Choose a Borama/Kaddare route before copying script artwork."
            )
        latin = transliterate(glyphs, script, "Somali Latin").text
        return script, glyphs, latin

    def _copy_menu_action(self, mode):
        self.copy_menu.dismiss()
        text = self._copy_menu_text
        if mode == "latin":
            return self.copy(text)
        try:
            script, glyphs, latin = self._chart_content_for_copy(text)
            if os.name != "nt":
                raise OSError(
                    "Rich clipboard formats are currently supported on Windows only."
                )
            if mode == "image":
                formats = formats_as_image(script, glyphs, latin)
                publish_windows_clipboard(formats)
                self.status = f"Copied {script} as an image; image works in apps that accept pasted pictures."
            elif mode == "saylacian":
                formats = formats_as_saylacian_text(script, glyphs, latin)
                publish_windows_clipboard(formats)
                self.status = f"Copied Saylacian Text v1 for {script}. Paste the package into Saylacian to restore its glyphs."
        except (OSError, ValueError) as error:
            self.status = "Clipboard copy failed: " + str(error)

    def save_result(self):
        home = self.root.get_screen("home")
        if not home.ids.output_text.text:
            self.status = "No result to save."
            return
        try:
            self.history.save(
                self.source,
                self.target,
                home.ids.input_text.text,
                home.ids.output_text.text,
                True,
                mode=self.mode,
            )
            self.status = (
                "Saved as favourite on this device. History > Clear saved removes it."
            )
        except (OSError, ValueError) as error:
            self.status = "Could not save: " + str(error)

    def show_history(self):
        screen = self.root.get_screen("saved")
        screen.ids.saved_items.clear_widgets()
        try:
            items = self.history.read()
        except (OSError, ValueError) as error:
            self.status = str(error)
            return
        for item in items:
            button = MDFlatButton(
                text=("Favourite: " if item["favourite"] else "") + item["text"][:42],
                size_hint_x=1,
                height=dp(52),
                on_release=lambda b, i=item: self.restore_saved(i),
            )
            screen.ids.saved_items.add_widget(button)
        self.root.current = "saved"

    def restore_saved(self, item):
        self.mode = item.get("mode", "Convert writing system")
        self.source = item["source"]
        self.target = item["target"]
        self.refresh_fonts()
        self.root.current = "home"
        self.root.get_screen("home").ids.input_text.text = item["text"]
        self.convert(item["text"])

    def clear_history(self):
        try:
            self.history.clear()
            self.show_history()
        except (OSError, ValueError) as error:
            self.status = str(error)

    def clear(self):
        screen = self.root.get_screen("home")
        screen.ids.input_text.text = ""
        screen.ids.output_text.text = ""
        self.status = "Cleared."


if __name__ == "__main__":
    import sys

    if "--original-ui" in sys.argv:
        from app.original_compat import OriginalApp

        OriginalApp().run()
    else:
        SaylacianApp().run()
