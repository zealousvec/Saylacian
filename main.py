# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saylacian Kivy/KivyMD app."""

import json
import os
import sys
import threading
import zipfile
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
from kivy.config import Config

Config.set("graphics", "minimum_width", "320")
Config.set("graphics", "minimum_height", "360")
from concurrent.futures import ThreadPoolExecutor

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Keyboard, Window
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
from kivymd.uix.list import OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.tooltip import MDTooltip

from saylacian.core.capabilities import get_capability, list_capabilities
from saylacian.core.clipboard_repr import (
    formats_as_image,
    formats_as_latin,
    formats_as_saylacian_text,
)
from saylacian.core.diagnostics import PrivateDiagnostics, install_exception_hooks
from saylacian.core.history import DamagedHistoryError, History
from saylacian.core.interchange import (
    decode_saylacian_text,
    encode_saylacian_text,
    identify_chart_text,
)
from saylacian.core.language_detection import detect_language
from saylacian.core.model_packs import ModelPackManager
from saylacian.core.old_nubian_reader import (
    alphabet_entries,
    describe_combining_marks,
    export_reading_record,
    import_reading_record,
    make_reading_record,
)
from saylacian.core.online_translation import (
    online_provider_label,
    online_translation_enabled,
)
from saylacian.core.presentation import (
    display_name,
    pack_download_error_message,
    pack_removal_error_message,
    picker_choices,
    translation_error_message,
)
from saylacian.core.script_info import osmanya_letters
from saylacian.core.translation import (
    clear_model_cache,
    model_directory,
    translate_meaning,
)
from saylacian.core.transliteration import (
    detect_script,
    is_private_use_character,
    transliterate,
)
from saylacian.core.windows_clipboard import publish as _publish_windows_clipboard


class HomeScreen(Screen):
    pass


class PickerScreen(Screen):
    pass


class SavedScreen(Screen):
    pass


class ScriptInfoScreen(Screen):
    pass


class OldNubianStudioScreen(Screen):
    pass


class PacksScreen(Screen):
    pass


def clipboard_text(text, script=None):
    """Return portable text without guessing the meaning of private-use characters."""
    has_private_characters = any(is_private_use_character(char) for char in text)
    if script in ("Borama", "Kaddare") and has_private_characters:
        if identify_chart_text(text) != script:
            return None, None
        return transliterate(text, script, "Somali Latin").text, script
    if has_private_characters:
        return None, None
    return text, None


def publish_windows_clipboard(formats):
    """Publish clipboard formats owned by Saylacian's native window."""
    window_info = Window.get_window_info()
    owner = getattr(window_info, "window", None)
    if not owner:
        raise OSError("Windows clipboard is unavailable until the app window is ready.")
    _publish_windows_clipboard(formats, owner=int(owner))


class SaylacianTextInput(TextInput):
    def on_focus(self, instance, focused):
        if self.readonly and focused:
            self.focus = False

    def copy(self, data=""):
        selected = data or self.selection_text
        app = MDApp.get_running_app()
        selected_script = (
            app.source
            if app.mode == "Convert writing system"
            and app.source in ("Borama", "Kaddare")
            else None
        )
        if (
            selected_script is None
            and self.readonly
            and app.target in ("Borama", "Kaddare")
        ):
            selected_script = app.target
        portable, _ = clipboard_text(selected, selected_script)
        if portable is None:
            app.status = (
                "These private-use glyphs have no script label. "
                "Select Borama or Kaddare before copying."
            )
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
    reader_status = StringProperty("Choose a cited letter or enter a passage to read.")
    reader_mark_details = StringProperty("")
    reader_detail = StringProperty("Select a letter to see its code point and source.")
    reader_selected_glyph = StringProperty("")
    pack_status = StringProperty("Installed packs work offline.")
    pack_progress = NumericProperty(0)
    pack_storage = StringProperty("")
    pack_busy = BooleanProperty(False)
    pack_cancel_requested = BooleanProperty(False)

    def build(self):
        self.title = "Saylacian — Alpha testing"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"
        self.font = str(PROJECT / "assets/NotoSansOsmanya.ttf")
        self.output_font = self.font
        self.side = "source"
        self.mode_routes = {
            "Convert writing system": (self.source, self.target),
            "Translate meaning": ("English", "French"),
        }
        self.mode_routes_initialized = {self.mode}
        Window.bind(on_resize=self.update_layout)
        self.update_layout(Window, *Window.size)
        self.worker = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="saylacian-translation"
        )
        self.pack_worker = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="saylacian-model-packs"
        )
        self.pack_manager = ModelPackManager()
        self.pack_options = []
        self.pack_index = -1
        self.pending = None
        self.generation = 0
        self.translate_trigger = Clock.create_trigger(self.begin_translation, 0.45)
        return Builder.load_file(str(PROJECT / "app/main.kv"))

    def update_layout(self, window, width, height):
        """Use two panels when there is room, including short landscape windows."""
        self.wide_layout = width >= dp(760) or (height <= dp(520) and width >= dp(480))

    def on_start(self):
        Window.bind(on_keyboard=self.keyboard)
        self.diagnostics = PrivateDiagnostics(Path(self.user_data_dir) / "logs")
        try:
            self.diagnostics.start(version="source")
            install_exception_hooks(self.diagnostics)
        except OSError:
            self.diagnostics = None
        self.history = History(Path(self.user_data_dir) / "history-v1.json")
        self.session_path = Path(self.user_data_dir) / "last-session-v1.json"
        self.restore_session()

    def keyboard(self, window, key, *args):
        modifiers = (
            set(args[-1])
            if args and isinstance(args[-1], (list, tuple, set))
            else set()
        )
        key_name = next(
            (name for name, code in Keyboard.keycodes.items() if code == key),
            str(key),
        ).lower()
        if getattr(self, "pack_dialog", None) is not None:
            if key_name in {"left", "right", "tab"}:
                self.pack_dialog_index = 1 - self.pack_dialog_index
                self._update_pack_dialog_cursor()
            elif key_name in {"enter", "numpadenter"}:
                if self.pack_dialog_index == 0:
                    self.dismiss_pack_dialog(self.pack_dialog)
                else:
                    self.remove_pack(self.pack_dialog, self.pack_dialog_pack_id)
            elif key_name == "escape":
                self.dismiss_pack_dialog(self.pack_dialog)
            return True
        if getattr(self, "history_recovery_dialog", None) is not None:
            if key_name in {"left", "right", "tab"}:
                self.history_recovery_index = 1 - self.history_recovery_index
                self._update_history_recovery_cursor()
            elif key_name in {"enter", "numpadenter"}:
                if self.history_recovery_index == 0:
                    self.dismiss_history_recovery(self.history_recovery_dialog)
                else:
                    self.recover_saved_history(self.history_recovery_dialog)
            elif key_name == "escape":
                self.dismiss_history_recovery(self.history_recovery_dialog)
            return True
        if key_name == "m" and {"ctrl", "shift"}.issubset(modifiers):
            self.switch_mode()
            return True
        if key_name == "p" and "ctrl" in modifiers:
            self.open_packs()
            return True
        if key_name == "k" and "ctrl" in modifiers:
            side = "source" if "shift" in modifiers else "target"
            self.open_picker(side)
            return True
        if key_name == "l" and "ctrl" in modifiers:
            home = self.root.get_screen("home")
            self.root.current = "home"
            home.ids.input_text.focus = True
            return True
        if self.root.current == "saved" and key_name in {"up", "down"}:
            if not self.saved_options:
                return False
            offset = 1 if key_name == "down" else -1
            if self.saved_index < 0:
                self.saved_index = 0 if offset > 0 else len(self.saved_options) - 1
            else:
                self.saved_index = (self.saved_index + offset) % len(self.saved_options)
            self._update_saved_cursor()
            return True
        if self.root.current == "saved" and key_name in {"enter", "numpadenter"}:
            if not self.saved_options:
                return False
            self.restore_saved(self.saved_options[max(self.saved_index, 0)])
            return True
        if self.root.current == "old_nubian_studio" and key_name in {
            "enter",
            "numpadenter",
        }:
            self.read_old_nubian_passage()
            return True
        if self.root.current == "picker" and key_name in {"up", "down"}:
            if not self.picker_options:
                return False
            offset = 1 if key_name == "down" else -1
            if self.picker_index < 0:
                self.picker_index = 0 if offset > 0 else len(self.picker_options) - 1
            else:
                self.picker_index = (self.picker_index + offset) % len(
                    self.picker_options
                )
            self._update_picker_cursor()
            picker = self.root.get_screen("picker")
            button = self.picker_options[self.picker_index][1]
            picker.ids.picker_scroll.scroll_to(button, padding=dp(8), animate=False)
            return True
        if self.root.current == "picker" and key_name in {"enter", "numpadenter"}:
            if not self.picker_options:
                return False
            self.picker_index = max(self.picker_index, 0)
            self.choose(self.picker_options[self.picker_index][0])
            return True
        if self.root.current == "packs" and key_name in {"up", "down"}:
            if not self.pack_options:
                return False
            offset = 1 if key_name == "down" else -1
            if self.pack_index < 0:
                self.pack_index = 0 if offset > 0 else len(self.pack_options) - 1
            else:
                self.pack_index = (self.pack_index + offset) % len(self.pack_options)
            self._update_pack_cursor()
            return True
        if self.root.current == "packs" and key_name in {"enter", "numpadenter"}:
            if not self.pack_options:
                return False
            option = self.pack_options[max(self.pack_index, 0)]
            if self.pack_busy:
                self.pack_status = "Wait for the current download to finish."
            elif option["installed"] or option.get("damaged"):
                self.confirm_remove_pack(option["id"])
            else:
                self.start_pack_download(option["id"])
            return True
        if key == 27 and self.root.current != "home":
            if self.root.current == "packs" and self.pack_busy:
                self.cancel_pack_download()
                return True
            self.close_picker()
            return True

    def open_picker(self, side):
        self.side = side
        self.picker_heading = "Choose " + side
        self.root.get_screen("home").ids.input_text.focus = False
        self.root.get_screen("picker").ids.search.text = ""
        self.filter_languages("")
        self.root.current = "picker"
        self.root.get_screen("picker").ids.search.focus = True

    @staticmethod
    def display_name(route_name):
        return display_name(route_name)

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
        self.pack_options = []
        self.pack_index = -1
        packs = self.pack_manager.list_packs()
        for pack in packs:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, spacing=dp(8))
            damaged = pack.get("damaged", False)
            removable = pack["installed"] or damaged
            available_update = (
                not pack["installed"]
                and not damaged
                and bool(pack.get("installed_version"))
                and pack["installed_version"] != pack["version"]
            )
            details = BoxLayout(orientation="vertical")
            title = MDLabel(
                text=pack["title"],
                bold=True,
                size_hint_y=None,
                height=dp(34),
                halign="left",
                valign="middle",
                text_size=(None, None),
            )
            if damaged:
                note = "Files changed · remove and download again"
            elif pack["installed"]:
                note = f"Installed · {self._format_bytes(pack['installed_bytes'])} on device"
            elif available_update:
                note = f"Update available · {self._format_bytes(pack['download_bytes'])} download"
            else:
                note = f"Download {self._format_bytes(pack['download_bytes'])} · works offline"
            if pack.get("requires"):
                note += " · Needs Somali / English pack for fallback"
            if pack.get("runtime_note"):
                note += f" · {pack['runtime_note']}"
            subtitle = MDLabel(
                text=note,
                theme_text_color="Custom",
                text_color=(0.68, 0.68, 0.68, 1),
                font_style="Caption",
                size_hint_y=None,
                height=dp(28),
                halign="left",
                valign="middle",
                text_size=(None, None),
            )

            def fit_text(widget, width):
                widget.text_size = (max(dp(80), width - dp(112)), None)

            row.bind(
                width=lambda _row, width, title=title, subtitle=subtitle: (
                    fit_text(title, width),
                    fit_text(subtitle, width),
                )
            )
            fit_text(title, row.width)
            fit_text(subtitle, row.width)
            title.bind(
                texture_size=lambda widget, size: setattr(
                    widget, "height", size[1] + dp(4)
                )
            )
            subtitle.bind(
                texture_size=lambda widget, size: setattr(
                    widget, "height", size[1] + dp(4)
                )
            )
            details.add_widget(title)
            details.add_widget(subtitle)
            row.add_widget(details)
            button = Button(
                text=(
                    "Remove"
                    if removable
                    else "Update"
                    if available_update
                    else "Download"
                ),
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
            elif removable:
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
            row.height = max(dp(76), details.minimum_height, dp(48))
            details.bind(
                minimum_height=lambda _details, height, row=row: setattr(
                    row, "height", max(dp(76), height, dp(48))
                )
            )
            rows.add_widget(row)
            self.pack_options.append(
                {
                    "id": pack["id"],
                    "title": title,
                    "installed": pack["installed"],
                    "damaged": damaged,
                }
            )
        total_storage = sum(pack["storage_bytes"] for pack in packs)
        self.pack_storage = (
            f"Using {self._format_bytes(total_storage)}. Remove a pack to free storage."
        )

    def _update_pack_cursor(self):
        for index, option in enumerate(self.pack_options):
            pointer = "› " if index == self.pack_index else ""
            option["title"].text = pointer + option["title"].text.removeprefix("› ")

    def start_pack_download(self, pack_id):
        if self.pack_busy:
            return
        self.pack_busy = True
        self.pack_cancel_event = threading.Event()
        self.pack_cancel_requested = False
        self.pack_progress = 0
        self.pack_status = "Preparing download..."
        self.refresh_pack_screen()
        future = self.pack_worker.submit(
            self.pack_manager.install,
            pack_id,
            self._pack_download_progress,
            self.pack_cancel_event,
        )
        future.add_done_callback(
            lambda completed: Clock.schedule_once(
                lambda _dt: self.finish_pack_download(completed, pack_id), 0
            )
        )

    def cancel_pack_download(self):
        """Request cancellation; the installer removes its temporary staging tree."""
        if not self.pack_busy or self.pack_cancel_event is None:
            return
        self.pack_cancel_event.set()
        self.pack_cancel_requested = True
        self.pack_status = "Stopping download..."

    def _pack_download_progress(self, completed, total, message):
        if self.pack_cancel_requested:
            return
        percent = completed * 100 / total if total else 100
        Clock.schedule_once(
            lambda _dt, p=percent, m=message: self.update_pack_progress(p, m), 0
        )

    def update_pack_progress(self, percent, message):
        self.pack_progress = max(0, min(100, percent))
        self.pack_status = message

    def finish_pack_download(self, future, pack_id):
        self.pack_busy = False
        try:
            future.result()
        except InterruptedError:
            self.pack_status = "Download cancelled. No partial pack was installed."
        except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
            self.pack_status = pack_download_error_message(error)
        else:
            clear_model_cache()
            self.pack_progress = 100
            title = self.pack_manager.specs[pack_id]["title"]
            self.pack_status = f"{title} is ready to use offline."
        finally:
            self.pack_cancel_event = None
            self.pack_cancel_requested = False
        self.refresh_pack_screen()

    def confirm_remove_pack(self, pack_id):
        title = self.pack_manager.specs[pack_id]["title"]
        keep_button = MDFlatButton(
            text="KEEP", on_release=lambda *_: self.dismiss_pack_dialog(dialog)
        )
        remove_button = MDFlatButton(
            text="REMOVE",
            on_release=lambda *_: self.remove_pack(dialog, pack_id),
        )
        dialog = MDDialog(
            title="Remove offline pack?",
            text=f"Remove {title} and its downloaded files?",
            buttons=[keep_button, remove_button],
        )
        self.pack_dialog = dialog
        self.pack_dialog_pack_id = pack_id
        self.pack_dialog_index = 0
        self.pack_dialog_buttons = (keep_button, remove_button)
        self._update_pack_dialog_cursor()
        dialog.open()

    def _update_pack_dialog_cursor(self):
        for index, button in enumerate(self.pack_dialog_buttons):
            label = "KEEP" if index == 0 else "REMOVE"
            button.text = ("› " if index == self.pack_dialog_index else "") + label

    def dismiss_pack_dialog(self, dialog):
        dialog.dismiss()
        self.pack_dialog = None
        self.pack_dialog_pack_id = None
        self.pack_dialog_buttons = ()
        self.pack_dialog_index = 0

    def remove_pack(self, dialog, pack_id):
        self.dismiss_pack_dialog(dialog)
        try:
            self.pack_manager.remove(pack_id)
        except (OSError, ValueError) as error:
            self.pack_status = pack_removal_error_message(error)
        else:
            clear_model_cache()
            self.pack_status = "Offline pack removed."
        self.refresh_pack_screen()

    def filter_languages(self, query):
        if not self.root:
            return
        box = self.root.get_screen("picker").ids.options
        box.clear_widgets()
        self.picker_options = []
        self.picker_index = -1
        mode = "translation" if self.mode == "Translate meaning" else "transliteration"
        choices = picker_choices(list_capabilities(), mode)
        current = getattr(self, self.side)
        for name in choices:
            if self.side == "target" and name == "Detect language/script":
                continue
            if query.casefold() not in (name + display_name(name)).casefold():
                continue
            button = OneLineListItem(
                text=("[x] " if name == current else "") + display_name(name),
                size_hint_x=1,
                height=dp(56),
                on_release=lambda b, n=name: self.choose(n),
            )
            box.add_widget(button)
            self.picker_options.append((name, button))

    def _update_picker_cursor(self):
        current = getattr(self, self.side)
        for index, (name, button) in enumerate(self.picker_options):
            pointer = "› " if index == self.picker_index else ""
            selected = "[x] " if name == current else ""
            button.text = pointer + selected + display_name(name)

    def choose(self, name):
        if name.endswith(" alphabet chart"):
            self.show_script_reference(name.removesuffix(" alphabet chart"))
            return
        other_side = "target" if self.side == "source" else "source"
        if name == getattr(self, other_side) and self.source != self.target:
            self.swap()
            self.close_picker()
            return
        setattr(self, self.side, name)
        self.complete_supported_pair()
        self.remember_mode_route()
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

    def remember_mode_route(self):
        """Keep each mode's latest source and target when switching modes."""
        self.mode_routes[self.mode] = (self.source, self.target)
        self.mode_routes_initialized.add(self.mode)

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
        if self.mode == "Convert writing system" and {
            self.source,
            self.target,
        }.issuperset({"Old Nubian (Coptic)", "Old Nubian scholarly Latin"}):
            self.output_font = self.font_for("Old Nubian (Coptic)")
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
            self.save_session(text, "")
            return
        if len(text) > 4000:
            self.status = "Maximum 4,000 characters."
            self.save_session(text, "")
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
                    self.save_session(text, "")
                    return
                translation_source, confidence, message = detect_language(text)
                if translation_source is None:
                    self.status = message
                    self.save_session(text, "")
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
                    else "Translating..."
                )
                self.status = detected + route
                self.translate_trigger()
                self.save_session(text, "")
            except ValueError as error:
                self.status = translation_error_message(error)
                self.save_session(text, "")
            return
        source = self.source
        detection_note = ""
        if source == "Detect language/script":
            source, message = detect_script(text)
            if source is None:
                self.input_font = "Roboto"
                source, confidence, message = detect_language(text)
                if source is None:
                    self.status = message
                    self.save_session(text, "")
                    return
            else:
                coptic_script = source == "Coptic script"
                old_nubian_script = source == "Old Nubian (Coptic)"
                if coptic_script:
                    source = "Old Nubian (Coptic)"
                    detection_note = (
                        "Coptic-derived writing detected; language is unknown. "
                    )
                elif old_nubian_script:
                    detection_note = (
                        "Old Nubian-specific letters detected; language is unknown. "
                    )
                self.input_font = self.font_for(source)
                input_widget = self.root.get_screen("home").ids.input_text
                input_widget.font_name = self.input_font
                input_widget._refresh_line_options()
                if get_capability(source, self.target, "transliteration") is None:
                    self.status = (
                        "Coptic-derived writing found; language is unknown. Choose Latin reading to use the Old Nubian table."
                        if coptic_script
                        else f"Detected {source}. Choose another target to convert this text."
                    )
                    self.save_session(text, "")
                    return
                if self.target == source:
                    self.status = (
                        f"Detected {source}; choose a different script as target."
                    )
                    self.save_session(text, "")
                    return
        try:
            result = transliterate(text, source, self.target)
            output.text = result.text
            warnings = " ".join(result.warnings)
            if result.alternatives:
                self.alternative_readings = "\nOther readings: " + " / ".join(
                    result.alternatives[:3]
                )
            if source in ("Borama", "Kaddare") or self.target in (
                "Borama",
                "Kaddare",
            ):
                self.status = detection_note + "Partial chart mapping."
                chart_details = [
                    warning
                    for warning in result.warnings
                    if not warning.startswith("Limited conversion;")
                    and warning
                    != "Capitalization is not represented in the chart glyphs."
                ]
                if chart_details:
                    self.status += " " + " ".join(chart_details)
            else:
                self.status = (
                    detection_note
                    + (warnings + " " if warnings else "")
                    + "Writing converted; meaning unchanged."
                )
            self.save_session(text, output.text)
        except ValueError as error:
            self.status = str(error)
            self.save_session(text, "")

    def on_input_text(self, text):
        """Import tagged script text and reject unlabelled private-use text."""
        if getattr(self, "_importing_package", False) or getattr(
            self, "_restoring_session", False
        ):
            return
        if text:
            try:
                package = decode_saylacian_text(text)
            except ValueError as error:
                self.root.get_screen("home").ids.output_text.text = ""
                self.alternative_readings = ""
                self.status = str(error)
                self.save_session(text, "")
                return
            if package:
                input_widget = self.root.get_screen("home").ids.input_text
                self.mode = "Convert writing system"
                self.source, self.target = package.script, "Somali Latin"
                self.remember_mode_route()
                self.refresh_fonts()
                self._importing_package = True
                try:
                    input_widget.text = package.text
                finally:
                    self._importing_package = False
                input_widget.font_name = self.input_font
                input_widget._refresh_line_options()
                self.convert(package.text)
                self.status = (
                    f"Saylacian Text v1 imported for {package.script}. "
                    "Some letters may be unmapped; spelling has not been checked."
                )
                return
            if any(is_private_use_character(char) for char in text):
                detected_chart = identify_chart_text(text)
                if (
                    self.mode == "Convert writing system"
                    and self.source in ("Borama", "Kaddare")
                    and detected_chart == self.source
                ):
                    self.refresh_fonts()
                    self.convert(text)
                    return
                input_widget = self.root.get_screen("home").ids.input_text
                self.root.get_screen("home").ids.output_text.text = ""
                self.alternative_readings = ""
                input_widget.font_name = "Roboto"
                input_widget._refresh_line_options()
                self.status = (
                    "These private-use glyphs have no script label. Paste a "
                    "Saylacian Text package or select Borama/Kaddare as source."
                )
                self.save_session(text, "")
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
            except (
                ImportError,
                MemoryError,
                OSError,
                RuntimeError,
                ValueError,
            ) as error:
                if self.diagnostics:
                    self.diagnostics.record_exception("translation-worker", error)
                message = translation_error_message(error)
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
        self.save_session(self.root.get_screen("home").ids.input_text.text, result.text)

    def save_session(self, input_text=None, output_text=None):
        """Keep the last visible conversion so reopening the app restores it."""
        if not getattr(self, "session_path", None) or not self.root:
            return
        home = self.root.get_screen("home")
        snapshot = {
            "version": 1,
            "mode": self.mode,
            "source": self.source,
            "target": self.target,
            "input": home.ids.input_text.text if input_text is None else input_text,
            "output": home.ids.output_text.text if output_text is None else output_text,
            "status": self.status,
            "alternatives": self.alternative_readings,
        }
        temporary = self.session_path.with_suffix(".tmp")
        try:
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(
                json.dumps(snapshot, ensure_ascii=False), encoding="utf-8"
            )
            os.replace(temporary, self.session_path)
        except OSError:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def reset_status_scroll(self):
        """Show the start of each new status message in the fixed footer."""
        if not self.root:
            return
        Clock.schedule_once(
            lambda _dt: setattr(
                self.root.get_screen("home").ids.status_scroll, "scroll_y", 1
            ),
            0,
        )

    def restore_session(self):
        """Restore a bounded local snapshot without rerunning translation."""
        try:
            snapshot = json.loads(self.session_path.read_text(encoding="utf-8"))
            if snapshot.get("version") != 1:
                return
            mode = snapshot.get("mode")
            source = snapshot.get("source")
            target = snapshot.get("target")
            input_text = snapshot.get("input")
            output_text = snapshot.get("output")
            if (
                mode not in ("Convert writing system", "Translate meaning")
                or not isinstance(source, str)
                or not isinstance(target, str)
                or not isinstance(input_text, str)
                or not isinstance(output_text, str)
                or len(input_text) > 4000
                or len(output_text) > 16000
            ):
                return
            self.mode, self.source, self.target = mode, source, target
            self.remember_mode_route()
            self._restoring_session = True
            try:
                self.refresh_fonts()
                home = self.root.get_screen("home")
                home.ids.input_text.text = input_text
                home.ids.output_text.text = output_text
                self.status = str(snapshot.get("status", self.status))[:1000]
                self.alternative_readings = str(snapshot.get("alternatives", ""))[:2000]
            finally:
                self._restoring_session = False
        except (OSError, ValueError, TypeError, AttributeError):
            return

    def on_stop(self):
        self.save_session()
        self.generation += 1
        self.translate_trigger.cancel()
        self.worker.shutdown(wait=False, cancel_futures=True)
        if getattr(self, "diagnostics", None):
            self.diagnostics.close()

    def on_pause(self):
        self.save_session()
        return True

    def swap(self):
        screen = self.root.get_screen("home")
        if self.source == "Detect language/script":
            self.status = "Select explicit source before swapping."
            return
        text = screen.ids.output_text.text
        self.source, self.target = self.target, self.source
        self.remember_mode_route()
        self.refresh_fonts()
        if text:
            screen.ids.input_text.text = text
        else:
            self.convert(screen.ids.input_text.text)

    def switch_mode(self):
        self.remember_mode_route()
        next_mode = (
            "Translate meaning"
            if self.mode == "Convert writing system"
            else "Convert writing system"
        )
        capability_mode = (
            "translation" if next_mode == "Translate meaning" else "transliteration"
        )
        if next_mode in self.mode_routes_initialized:
            next_source, next_target = self.mode_routes[next_mode]
        else:
            routes = [
                route
                for route in list_capabilities()
                if route["kind"] == "route" and route["mode"] == capability_mode
            ]
            matching_detect_target = self.source == "Detect language/script" and any(
                route["target"] == self.target for route in routes
            )
            matching_source = next(
                (route for route in routes if route["source"] == self.source), None
            )
            matching_target = next(
                (route for route in routes if route["target"] == self.target), None
            )
            if matching_detect_target:
                next_source, next_target = self.source, self.target
            elif matching_source:
                next_source, next_target = (
                    matching_source["source"],
                    matching_source["target"],
                )
            elif matching_target:
                next_source, next_target = (
                    matching_target["source"],
                    matching_target["target"],
                )
            else:
                next_source, next_target = (
                    ("English", "French")
                    if next_mode == "Translate meaning"
                    else ("Somali Latin", "Osmanya")
                )
        self.mode = next_mode
        self.source, self.target = next_source, next_target
        has_route = get_capability(self.source, self.target, capability_mode)
        has_detect_target = self.source == "Detect language/script" and any(
            route["kind"] == "route"
            and route["mode"] == capability_mode
            and route["target"] == self.target
            for route in list_capabilities()
        )
        if not has_route and not has_detect_target:
            self.source, self.target = (
                ("English", "French")
                if self.mode == "Translate meaning"
                else ("Somali Latin", "Osmanya")
            )
        self.remember_mode_route()
        self.refresh_fonts()
        self.convert(self.root.get_screen("home").ids.input_text.text)

    def paste(self):
        pasted = Clipboard.paste()
        self.root.get_screen("home").ids.input_text.text = pasted

    def show_alphabet(self):
        screen = self.root.get_screen("alphabet")
        self.script_heading = "Osmanya alphabet"
        self.script_note = "Somali script. W/uu and y/ii share letters, so reverse readings can differ."
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
            "Limited letter conversion. Word spelling has not been reviewed. "
            "Copied text may need the Saylacian font."
        )
        screen.ids.chart_status.text = "Text may need the Saylacian font in other apps."
        if script == "Osmanya":
            self.show_alphabet()
            screen.ids.chart_status.text = (
                "Unicode letters. Select Osmanya as source to insert letters."
            )
            return
        grid = screen.ids.letters
        grid.clear_widgets()
        grid.cols = 1
        chart = PROJECT / "assets/research" / f"{script}_Alphabet_Chart.jpg"
        if not chart.is_file():
            screen.ids.chart_status.text = "Chart image unavailable. You can still enter text for limited conversion."
            self.root.get_screen("home").ids.input_text.focus = False
            self.root.current = "alphabet"
            return
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

    def open_old_nubian_studio(self):
        if self.mode != "Convert writing system" or not {
            self.source,
            self.target,
        }.issuperset({"Old Nubian (Coptic)", "Old Nubian scholarly Latin"}):
            self.status = (
                "Choose Old Nubian and Latin reading to open the reading studio."
            )
            return
        home = self.root.get_screen("home")
        studio = self.root.get_screen("old_nubian_studio")
        studio.ids.reader_original.text = home.ids.input_text.text
        self.read_old_nubian_passage()
        studio.ids.alphabet_search.text = ""
        self.filter_old_nubian_alphabet("")
        home.ids.input_text.focus = False
        self.root.current = "old_nubian_studio"

    def read_old_nubian_passage(self):
        studio = self.root.get_screen("old_nubian_studio")
        try:
            record = make_reading_record(studio.ids.reader_original.text)
        except ValueError as error:
            studio.ids.reader_latin.text = ""
            self.reader_mark_details = ""
            self.reader_status = str(error)
            return
        studio.ids.reader_latin.text = record.latin
        details = []
        if record.alternatives:
            details.append("Other readings: " + " / ".join(record.alternatives[:3]))
        mark_details = describe_combining_marks(record.original)
        if mark_details:
            details.append(mark_details)
        self.reader_mark_details = "\n".join(details)
        self.reader_status = (
            "Limited character reading · "
            + record.convention
            + (" · " + " ".join(record.warnings) if record.warnings else "")
        )

    def filter_old_nubian_alphabet(self, query):
        if not self.root:
            return
        grid = self.root.get_screen("old_nubian_studio").ids.reader_alphabet
        grid.clear_widgets()
        for entry in alphabet_entries(query):
            button = Button(
                text=f"{entry['glyph']}  {entry['reading']}",
                size_hint_y=None,
                height=dp(52),
                font_name=self.font_for("Old Nubian (Coptic)"),
                font_size="18sp",
                background_normal="",
                background_color=(0.95, 0.95, 0.95, 1),
                color=(0.08, 0.08, 0.08, 1),
                on_release=lambda _button, row=entry: self.show_old_nubian_letter(row),
            )
            grid.add_widget(button)

    def show_old_nubian_letter(self, entry):
        self.reader_selected_glyph = str(entry["glyph"])
        ambiguity = " · reverse reading may be ambiguous" if entry["ambiguous"] else ""
        alternatives = entry.get("alternative_readings", ())
        phonetic_values = entry.get("phonetic_values", ())
        other_readings = (
            " · other Latin reading: " + " / ".join(alternatives)
            if alternatives
            else ""
        )
        phonetic_detail = (
            " · phonetic value: [" + ", ".join(phonetic_values) + "]"
            if phonetic_values
            else ""
        )
        self.reader_detail = (
            f"{entry['glyph']} · {entry['reading']} · {entry['codepoint']}\n"
            f"{entry['name']}{ambiguity}{other_readings}{phonetic_detail}\n"
            f"{entry['confidence']} · {entry['convention']}"
        )

    def insert_old_nubian_letter(self):
        if not self.reader_selected_glyph:
            self.reader_status = "Choose a letter first."
            return
        field = self.root.get_screen("old_nubian_studio").ids.reader_original
        field.insert_text(self.reader_selected_glyph)

    def export_old_nubian_reading(self):
        from datetime import UTC, datetime

        studio = self.root.get_screen("old_nubian_studio")
        try:
            record = make_reading_record(studio.ids.reader_original.text)
            payload = export_reading_record(record)
            folder = Path(self.user_data_dir) / "old-nubian-readings"
            folder.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            destination = folder / f"reading-{stamp}.json"
            destination.write_text(payload, encoding="utf-8")
        except (OSError, ValueError) as error:
            self.reader_status = f"Could not export reading: {error}"
            return
        self.reader_status = f"Reading record saved: {destination}"

    def copy_old_nubian_reading(self, field_name):
        studio = self.root.get_screen("old_nubian_studio")
        fields = {
            "original": studio.ids.reader_original.text,
            "latin": studio.ids.reader_latin.text,
        }
        if field_name not in fields:
            self.reader_status = "Choose the original or Latin reading to copy."
            return
        text = fields[field_name]
        if not text:
            self.reader_status = "There is no reading to copy."
            return
        Clipboard.copy(text)
        self.reader_status = (
            "Original script copied."
            if field_name == "original"
            else "Latin reading copied."
        )

    def import_old_nubian_reading(self):
        payload = Clipboard.paste()
        studio = self.root.get_screen("old_nubian_studio")
        try:
            record = import_reading_record(payload)
        except (TypeError, ValueError) as error:
            self.reader_status = f"Could not import reading record: {error}"
            return
        studio.ids.reader_original.text = record.original
        studio.ids.reader_latin.text = record.latin
        self.reader_status = (
            "Imported and checked reading record · " + record.convention
        )

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
            self.status = (
                "These private-use glyphs have no script label. "
                "Select Borama or Kaddare before copying."
            )
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
        chart_route = self.source in ("Borama", "Kaddare") or self.target in (
            "Borama",
            "Kaddare",
        )
        input_contains_private = any(is_private_use_character(char) for char in text)
        chart_copy = self.mode == "Convert writing system" and chart_route
        if (
            caller is self.root.get_screen("home").ids.input_copy_button
            and self.source not in ("Borama", "Kaddare")
            and input_contains_private
        ):
            chart_copy = False
        self._copy_menu_from_output = (
            caller is self.root.get_screen("home").ids.output_copy_button
        )
        if chart_copy:
            entries = [("Copy text", "saylacian")]
            if os.name == "nt":
                entries.append(("Copy image", "image"))
            entries.append(("Copy Latin", "latin"))
        else:
            entries = [("Copy text", "text")]
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
        route_script = (
            self.source
            if self.source in ("Borama", "Kaddare")
            else self.target
            if self.target in ("Borama", "Kaddare")
            else None
        )
        if route_script is None:
            raise ValueError(
                "Choose a Borama/Kaddare route before copying script artwork."
            )

        script = identify_chart_text(text)
        if script and script != route_script:
            raise ValueError("Text does not match the selected Borama/Kaddare route.")
        if script:
            glyphs = text
        elif self.target in ("Borama", "Kaddare") and self.source == "Somali Latin":
            if any(is_private_use_character(char) for char in text):
                raise ValueError(
                    "Paste a tagged package or select its script as source."
                )
            script = self.target
            glyphs = transliterate(text, self.source, script).text
        elif self.source in ("Borama", "Kaddare") and self.target == "Somali Latin":
            if self._copy_menu_from_output:
                input_text = self.root.get_screen("home").ids.input_text.text
                if identify_chart_text(input_text) == self.source:
                    script = self.source
                    glyphs = input_text
                else:
                    raise ValueError("The original script text is unavailable.")
            else:
                raise ValueError(
                    "Paste a tagged package or select its script as source."
                )
        else:
            raise ValueError(
                "Choose a Borama/Kaddare route before copying script artwork."
            )
        latin = transliterate(glyphs, script, "Somali Latin").text
        return script, glyphs, latin

    def _copy_menu_action(self, mode):
        self.copy_menu.dismiss()
        text = self._copy_menu_text
        if mode == "text" and os.name != "nt":
            Clipboard.copy(text)
            self.status = "Copied to clipboard."
            return
        if mode == "text":
            try:
                publish_windows_clipboard(formats_as_latin(text))
            except (OSError, ValueError) as error:
                self.status = "Clipboard copy failed: " + str(error)
            else:
                self.status = "Copied to clipboard."
            return
        if mode == "latin":
            try:
                _, _, latin = self._chart_content_for_copy(text)
            except ValueError as error:
                self.status = str(error)
                return
            return self.copy(latin)
        try:
            script, glyphs, latin = self._chart_content_for_copy(text)
            if os.name != "nt" and mode == "image":
                raise OSError("Image clipboard is currently supported on Windows only.")
            if mode == "image":
                formats = formats_as_image(script, glyphs, latin)
                publish_windows_clipboard(formats)
                self.status = f"Copied {script} image."
            elif mode == "saylacian":
                if os.name == "nt":
                    publish_windows_clipboard(
                        formats_as_saylacian_text(script, glyphs, latin)
                    )
                else:
                    Clipboard.copy(encode_saylacian_text(glyphs, script))
                self.status = f"Copied {script} text package. Paste it here to restore the script."
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
                "Favourite saved on this device. Use Clear saved to remove it."
            )
        except (OSError, ValueError) as error:
            self.status = "Could not save: " + str(error)

    def show_history(self):
        screen = self.root.get_screen("saved")
        screen.ids.saved_items.clear_widgets()
        self.saved_options = []
        self.saved_index = -1
        try:
            items = self.history.read()
        except DamagedHistoryError as error:
            self.status = str(error)
            self.confirm_history_recovery()
            return
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
            self.saved_options.append(item)
        self._update_saved_cursor()
        self.root.current = "saved"

    def confirm_history_recovery(self):
        keep_button = MDFlatButton(
            text="KEEP FILE",
            on_release=lambda *_: self.dismiss_history_recovery(dialog),
        )
        recover_button = MDFlatButton(
            text="BACK UP & START FRESH",
            on_release=lambda *_: self.recover_saved_history(dialog),
        )
        dialog = MDDialog(
            title="Saved history needs recovery",
            text=(
                "Keep the original, or save a backup before starting a fresh history?"
            ),
            buttons=[keep_button, recover_button],
        )
        self.history_recovery_dialog = dialog
        self.history_recovery_index = 0
        self.history_recovery_buttons = (keep_button, recover_button)
        self._update_history_recovery_cursor()
        dialog.open()

    def _update_history_recovery_cursor(self):
        for index, button in enumerate(self.history_recovery_buttons):
            label = "KEEP FILE" if index == 0 else "BACK UP & START FRESH"
            button.text = ("› " if index == self.history_recovery_index else "") + label

    def dismiss_history_recovery(self, dialog):
        dialog.dismiss()
        self.history_recovery_dialog = None
        self.history_recovery_buttons = ()
        self.history_recovery_index = 0

    def recover_saved_history(self, dialog):
        self.dismiss_history_recovery(dialog)
        try:
            backup = self.history.backup_and_reset()
        except (OSError, ValueError) as error:
            self.status = f"Could not recover saved history: {error}"
            return
        self.status = (
            f"History restarted. Backup saved as {backup.name}. Open Saved to continue."
        )

    def _update_saved_cursor(self):
        screen = self.root.get_screen("saved")
        buttons = screen.ids.saved_items.children[::-1]
        for index, (item, button) in enumerate(zip(self.saved_options, buttons)):
            label = ("Favourite: " if item["favourite"] else "") + item["text"][:42]
            button.text = ("› " if index == self.saved_index else "") + label
        if 0 <= self.saved_index < len(buttons):
            screen.ids.saved_scroll.scroll_to(buttons[self.saved_index], animate=False)

    def restore_saved(self, item):
        self.mode = item.get("mode", "Convert writing system")
        self.source = item["source"]
        self.target = item["target"]
        self.remember_mode_route()
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
        self.alternative_readings = ""
        self.save_session("", "")


if __name__ == "__main__":
    SaylacianApp().run()
