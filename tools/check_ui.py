# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise live Kivy widgets with network disabled; save actual framebuffers."""

import json
import os
import socket
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = Path(
    os.environ.get("SAYLACIAN_UI_EVIDENCE_DIR")
    or tempfile.mkdtemp(prefix="saylacian-ui-acceptance-")
).expanduser()
PREVIEW_DIR = EVIDENCE_DIR / "previews"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("SAYLACIAN_TRANSLATION_PROVIDER", "offline")
sys.path.insert(0, str(PROJECT))
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window

import main as app_module
from main import SaylacianApp
from saylacian.core.history import History
from tools.in_memory_clipboard import InMemoryClipboard

checks = []
test_clipboard = InMemoryClipboard()
app_module.Clipboard = test_clipboard
app_module.publish_windows_clipboard = test_clipboard.publish_windows_formats


def capture_after_present(path, continuation):
    """Capture after Kivy presents the updated frame, then continue the checks."""

    def presented(*args):
        Window.unbind(on_flip=presented)
        Window._saylacian_capture_callback = None

        def capture(dt):
            app = App.get_running_app()
            app.root.export_to_png(str(path))
            Clock.schedule_once(lambda dt: continuation(), 0.1)

        Clock.schedule_once(capture, 0.15)

    Window._saylacian_capture_callback = presented
    Window.bind(on_flip=presented)
    Window.canvas.ask_update()


def deny(*args, **kwargs):
    raise AssertionError("Network access attempted")


socket.socket.connect = deny


class CheckedApp(SaylacianApp):
    def on_start(self):
        super().on_start()
        self.temp = tempfile.TemporaryDirectory()
        self.history = History(Path(self.temp.name) / "history.json")
        Clock.schedule_once(self.check, 1)

    def check(self, dt):
        try:
            self.open_packs()
            pack_screen = self.root.get_screen("packs")
            assert self.root.current == "packs"
            assert len(pack_screen.ids.pack_rows.children) == len(
                self.pack_manager.list_packs()
            )
            assert any(
                "Somali" in str(getattr(widget, "text", ""))
                for row in pack_screen.ids.pack_rows.children
                for widget in row.walk()
            )
            checks.append(
                "offline model-pack screen, installed state, and storage summary"
            )
            capture_after_present(
                PREVIEW_DIR / "offline-language-packs.png",
                self.check_after_pack_screen,
            )
        except Exception:
            import traceback

            (EVIDENCE_DIR / "UI_TEST_FAILURE.txt").write_text(traceback.format_exc())
            self.stop()
            raise

    def check_after_pack_screen(self):
        try:
            self.close_picker()
            home = self.root.get_screen("home")
            self.source = "Detect language/script"
            self.target = "Old Nubian scholarly Latin"
            self.refresh_fonts()
            home.ids.input_text.text = "ⲁⲃⲅ ⳟⳡⳣⳝ!"
            assert home.ids.output_text.text == "abg ngnywj!"
            assert home.ids.input_text.font_name == "SaylacianCoptic"
            checks.append("Old Nubian Coptic script detection")
            self.source = "Old Nubian (Coptic)"
            self.refresh_fonts()
            home.ids.input_text.text = "ⲁⲃⲅ ⳟⳡⳣⳝ!"
            assert (
                home.ids.input_text._label_cached.options["font_name"]
                == "SaylacianCoptic"
            )
            assert home.ids.output_text.text == "abg ngnywj!"
            checks.append("Old Nubian Coptic live conversion and font")
            capture_after_present(
                PREVIEW_DIR / "oldnubian-live.png", self.check_after_nubian
            )
        except Exception:
            import traceback

            (EVIDENCE_DIR / "UI_TEST_FAILURE.txt").write_text(traceback.format_exc())
            self.stop()
            raise

    def check_after_nubian(self):
        try:
            home = self.root.get_screen("home")
            self.source = "Somali Latin"
            self.target = "Osmanya"
            self.refresh_fonts()
            home.ids.input_text.text = "Dhagax!"
            assert home.ids.output_text.text == "𐒊𐒖𐒌𐒖𐒄!"
            checks.append("input/output and case warning")
            self.open_picker("target")
            assert self.root.current == "picker"
            self.filter_languages("Borama")
            route_options = [
                button for name, button in self.picker_options if name == "Borama"
            ]
            assert len(route_options) == 1
            assert route_options[0].secondary_text == (
                "Limited conversion · needs Saylacian font"
            )
            chart_options = [
                button
                for name, button in self.picker_options
                if name == "Borama alphabet chart"
            ]
            assert len(chart_options) == 1
            chart_options[0].dispatch("on_release")
            assert self.target == "Osmanya" and not home.ids.output_text.text
            assert "chart opened for reference" in self.status
            assert self.root.current == "alphabet"
            images = self.root.get_screen("alphabet").ids.letters.children
            assert any(
                getattr(item, "source", "").endswith("Borama_Alphabet_Chart.jpg")
                for item in images
            )
            self.close_picker()
            assert self.root.current == "home"
            checks.append("picker/search/selection/unsupported")
            self.open_picker("source")
            self.close_picker()
            assert self.root.current == "home"
            checks.append("source picker/back")
            self.target = "Osmanya"
            self.refresh_fonts()
            self.convert(home.ids.input_text.text)
            self.copy(home.ids.input_text.text)
            assert test_clipboard.paste() == "Dhagax!"
            if os.name == "nt":
                assert ("CF_UNICODETEXT", "Dhagax!\0".encode("utf-16-le")) in (
                    test_clipboard.formats
                )
            self.clear()
            assert not home.ids.output_text.text
            self.paste()
            assert home.ids.input_text.text == "Dhagax!"
            checks.append("in-memory clipboard round trip; system clipboard untouched")
            self.swap()
            assert home.ids.output_text.text == "dhagax!"
            checks.append("swap/reverse")
            self.switch_mode()
            assert not home.ids.output_text.text and "language" in self.status.lower()
            checks.append("meaning unsupported script pair")
            self.switch_mode()
            self.swap()
            self.open_picker("source")
            self.choose("Detect language/script")
            assert "language" in self.status.lower()
            checks.append("Latin auto detection uncertainty")
            self.source = "Somali Latin"
            self.refresh_fonts()
            self.convert(home.ids.input_text.text)
            self.save_result()
            self.show_history()
            assert len(self.root.get_screen("saved").ids.saved_items.children) == 1
            self.root.get_screen("saved").ids.saved_items.children[0].dispatch(
                "on_release"
            )
            assert self.root.current == "home" and home.ids.input_text.text == "dhagax!"
            self.clear_history()
            assert not self.history.read()
            self.close_picker()
            checks.append("favourite/save/restore/delete in isolated store")
            Window.size = (390, 780)
            self.viewport_cases = [
                ((390, 780), False, "enhanced-mobile"),
                ((320, 640), False, "enhanced-small-mobile"),
                ((320, 500), False, "enhanced-compact-portrait"),
                ((780, 390), True, "enhanced-landscape"),
                ((768, 1024), True, "enhanced-tablet"),
                ((1366, 768), True, "enhanced-desktop"),
                ((390, 780), False, "enhanced-mobile"),
            ]
            self.viewport_index = 0
            Clock.schedule_once(self.capture, 1)
        except Exception:
            import traceback

            (EVIDENCE_DIR / "UI_TEST_FAILURE.txt").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            self.stop()
            raise

    def capture(self, dt):
        size, wide, _ = self.viewport_cases[self.viewport_index]
        Window.size = size
        Clock.schedule_once(lambda dt: self.check_viewport(wide), 0.35)

    def check_viewport(self, expected_wide):
        home = self.root.get_screen("home")
        panels = home.ids.translation_panels
        assert self.wide_layout is expected_wide, (Window.size, self.wide_layout)
        assert panels.orientation == ("horizontal" if expected_wide else "vertical")
        controls = home.ids.language_controls
        for control in controls.children:
            assert control.x >= controls.x - 1, (Window.size, control.x, controls.x)
            assert control.right <= controls.right + 1, (
                Window.size,
                control.right,
                controls.right,
            )
            assert control.y >= controls.y - 1
            assert control.top <= controls.top + 1
        _, _, screenshot_name = self.viewport_cases[self.viewport_index]
        path = PREVIEW_DIR / f"{screenshot_name}.png"
        self.viewport_index += 1
        if screenshot_name != "enhanced-mobile" or self.viewport_index == 1:
            capture_after_present(path, self.capture_next_viewport)
        else:
            self.capture_next_viewport()

    def capture_next_viewport(self, dt=0):
        if self.viewport_index < len(self.viewport_cases):
            Clock.schedule_once(self.capture, 0.2)
            return
        checks.append(
            "responsive layouts at 320x500, 320x640, 390x780, 780x390, 768x1024 and 1366x768"
        )
        (EVIDENCE_DIR / "ui-test-results.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "network": "socket.connect blocked",
                    "viewports": [case[0] for case in self.viewport_cases[:-1]],
                },
                indent=2,
            )
        )
        self.open_picker("target")
        Clock.schedule_once(self.capture_picker, 0.6)

    def capture_picker(self, dt):
        capture_after_present(
            PREVIEW_DIR / "enhanced-picker-mobile.png",
            self.capture_unavailable,
        )

    def capture_unavailable(self):
        self.choose("Borama alphabet chart")
        assert self.target == "Osmanya"
        assert "chart opened for reference" in self.status
        assert self.root.current == "alphabet"
        assert not self.root.get_screen("home").ids.output_text.text
        checks.append("Borama reference chart renders without claiming a converter")
        capture_after_present(
            PREVIEW_DIR / "enhanced-unavailable-mobile.png",
            self.start_english_french,
        )

    def start_english_french(self):
        self.close_picker()
        self.source = "English"
        self.target = "French"
        self.mode = "Translate meaning"
        self.refresh_fonts()
        self.root.get_screen("home").ids.input_text.text = "Hello, how are you?"
        self.convert("Hello, how are you?")
        self.deadline = 0
        Clock.schedule_interval(self.check_translation, 0.2)

    def check_translation(self, dt):
        self.deadline += dt
        home = self.root.get_screen("home")
        result = home.ids.output_text.text
        if result:
            assert result == "Bonjour, comment allez-vous ?", result
            checks.append("background English/French meaning translation offline")

            from saylacian.core.transliteration import Conversion

            self.show_translation(self.generation - 1, Conversion("STALE"), None)
            assert self.root.get_screen("home").ids.output_text.text == result
            checks.append("stale worker result ignored")
            capture_after_present(
                PREVIEW_DIR / "enhanced-meaning.png",
                self.start_english_somali,
            )
            return False
        if self.deadline > 20:
            raise AssertionError("Translation failed or timed out: " + self.status)

    def start_english_somali(self):
        home = self.root.get_screen("home")
        self.source = "English"
        self.target = "Somali Latin"
        home.ids.input_text.text = "The child is reading a book."
        self.deadline = 0
        self.convert(home.ids.input_text.text)
        Clock.schedule_interval(self.check_english_somali, 0.2)

    def check_english_somali(self, dt):
        self.deadline += dt
        home = self.root.get_screen("home")
        result = home.ids.output_text.text
        if result:
            assert result.strip() and result.strip() != home.ids.input_text.text
            assert "Somali translation may be inaccurate" in self.status, self.status
            checks.append("background English/Somali meaning translation offline")
            self.source = "Somali Latin"
            self.target = "English"
            home.ids.input_text.text = "Salaan, sidee tahay?"
            self.deadline = 0
            self.convert(home.ids.input_text.text)
            Clock.schedule_interval(self.check_somali_english, 0.2)
            return False
        if self.deadline > 20:
            raise AssertionError(
                "English/Somali translation failed or timed out: " + self.status
            )

    def check_somali_english(self, dt):
        self.deadline += dt
        home = self.root.get_screen("home")
        result = home.ids.output_text.text
        if result:
            assert result == "How are you?", result
            assert "Somali translation may be inaccurate" in self.status, self.status
            checks.append("background Somali/English meaning translation offline")
            self.source = "Detect language/script"
            home.ids.input_text.text = "Salaan, sidee tahay?"
            self.deadline = 0
            self.convert(home.ids.input_text.text)
            Clock.schedule_interval(self.check_auto_language, 0.2)
            return False
        if self.deadline > 20:
            raise AssertionError(
                "Somali/English translation failed or timed out: " + self.status
            )

    def check_auto_language(self, dt):
        self.deadline += dt
        home = self.root.get_screen("home")
        result = home.ids.output_text.text
        if result:
            assert "How are you?" in result, result
            assert "Detected Somali Latin" in self.status, self.status
            checks.append("automatic Somali detection and offline translation")
            self.target = "French"
            self.deadline = 0
            self.convert(home.ids.input_text.text)
            Clock.schedule_interval(self.check_somali_french, 0.2)
            return False
        if self.deadline > 20:
            raise AssertionError("Automatic Somali translation failed: " + self.status)

    def check_somali_french(self, dt):
        self.deadline += dt
        home = self.root.get_screen("home")
        result = home.ids.output_text.text
        if result:
            assert result == "Comment allez-vous ?", result
            assert "some meaning may change" in self.status, self.status
            checks.append("automatic Somali detection and offline French pivot")
            capture_after_present(
                PREVIEW_DIR / "enhanced-meaning-somali-french.png",
                lambda: self.finish_somali(0),
            )
            return False
        if self.deadline > 20:
            raise AssertionError("Somali/French pivot failed: " + self.status)

    def finish_somali(self, dt):
        (EVIDENCE_DIR / "ui-test-results.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "network": "socket.connect blocked",
                    "viewports": [case[0] for case in self.viewport_cases[:-1]],
                },
                indent=2,
            )
        )
        self.temp.cleanup()
        self.stop()


CheckedApp().run()
print(f"UI acceptance evidence: {EVIDENCE_DIR}")
