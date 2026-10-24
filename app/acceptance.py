# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check live Kivy widgets and paste handling without OS input injection."""

import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.button import Button

from saylacian.core.history import History
from saylacian.core.interchange import encode_saylacian_text
from saylacian.core.old_nubian_reader import (
    export_reading_record,
    make_reading_record,
)
from saylacian.core.transliteration import Conversion


def start(app):
    folder = Path(
        os.environ.get("SAYLACIAN_EVIDENCE", str(Path.home() / "Saylacian-evidence"))
    )
    folder.mkdir(parents=True, exist_ok=True)
    home = app.root.get_screen("home")
    assert list(home.ids.input_text.hint_text_color) == [0.35, 0.35, 0.35, 1]
    assert list(home.ids.output_text.hint_text_color) == [0.35, 0.35, 0.35, 1]
    input_field = home.ids.input_text
    assert input_field._focus_outline.width == dp(2)
    assert list(input_field._focus_outline_color.rgba) == [0, 0, 0, 0]
    input_field.focus = True
    assert list(input_field._focus_outline_color.rgba) == [0, 0, 0, 1]
    input_field.focus = False
    assert home.ids.app_header.orientation == (
        "vertical" if home.width < dp(420) else "horizontal"
    )
    assert home.ids.brand_title.texture_size[1] <= home.ids.brand_title.height + 1
    assert home.ids.status_label.texture_size[1] <= home.ids.status_label.height + 1
    app.update_layout(Window, dp(320), dp(700))
    assert not app.wide_layout
    assert home.ids.translation_panels.orientation == "vertical"
    app.update_layout(Window, dp(800), dp(700))
    assert app.wide_layout
    assert home.ids.translation_panels.orientation == "horizontal"
    app.update_layout(Window, dp(500), dp(500))
    assert app.wide_layout
    assert home.ids.translation_panels.orientation == "horizontal"
    app.update_layout(Window, *Window.size)
    try:
        pack_screen = app.root.get_screen("packs")
        app.root.current = "packs"
        app.pack_busy = True
        app.pack_cancel_event = threading.Event()
        app.pack_cancel_requested = False
        cancel_button = pack_screen.ids.pack_cancel_button
        assert cancel_button.height > 0 and not cancel_button.disabled
        cancel_text = next(
            widget
            for widget in cancel_button.walk()
            if type(widget).__name__ == "MDLabel"
            and getattr(widget, "text", "") == "Cancel download"
        )
        app.cancel_pack_download()
        assert app.pack_cancel_event.is_set()
        assert cancel_button.disabled
        assert cancel_text.disabled
        assert list(cancel_text.disabled_color) == [1, 1, 1, 0.5]
        assert app.pack_status == "Stopping download..."
        assert app.keyboard(Window, 108, None, 108, ["ctrl"])
        assert app.root.current == "home"
        assert home.ids.input_text.focus
        app.pack_busy = False
        app.pack_cancel_event = None
        app.pack_cancel_requested = False
        app.mode = "Translate meaning"
        app.source, app.target = "English", "Somali Latin"
        app.open_picker("target")
        app.filter_languages("e")
        assert app.picker_options
        assert app.keyboard(Window, 274, None, None, ["down"])
        assert app.picker_index == 0
        assert app.keyboard(Window, 274, None, None, ["down"])
        selected_target = app.picker_options[app.picker_index][0]
        assert app.picker_options[app.picker_index][1].text.startswith("› ")
        assert app.keyboard(Window, 13, None, 13, [])
        assert app.target == selected_target
        assert selected_target == "French"
        assert app.root.current == "home"
        current_mode = app.mode
        assert app.keyboard(Window, 109, None, 109, ["ctrl", "shift"])
        assert app.mode != current_mode
        pack_rows = [
            {
                "id": "somali",
                "title": "Somali / English",
                "installed": False,
                "version": "2-test",
                "installed_version": "1-test",
                "installed_bytes": 300,
                "download_bytes": 2 * 1024 * 1024,
                "storage_bytes": 3 * 1024 * 1024,
            },
            {
                "id": "french",
                "title": "French / English",
                "installed": False,
                "installed_bytes": 0,
                "download_bytes": 5 * 1024 * 1024,
                "storage_bytes": 1024 * 1024,
            },
        ]
        saved_mode = app.mode
        app.mode = "Translate meaning"
        app.source, app.target = "Somali Latin", "English"
        app_module = app.__class__.__module__
        with (
            patch(f"{app_module}.online_translation_enabled", return_value=False),
            patch(
                f"{app_module}.model_directory",
                side_effect=ValueError(
                    "No local model installed for this pair. Download its offline language pack first."
                ),
            ),
        ):
            app.convert("Tijaabo kooban.")
        assert "Download its offline language pack first" in app.status, app.status
        assert home.ids.output_text.text == ""
        app.mode = saved_mode
        with (
            patch.object(app.pack_manager, "list_packs", return_value=pack_rows),
            patch.object(app, "start_pack_download") as start_download,
        ):
            assert app.keyboard(Window, 112, None, 112, ["ctrl"])
            assert app.root.current == "packs"
            assert app.pack_storage.startswith("Using 4 MB.")
            somali_note = next(
                widget
                for widget in app.root.get_screen("packs").ids.pack_rows.walk()
                if type(widget).__name__ == "MDLabel"
                and widget.text.startswith("Download 5 MB")
            )
            assert "works offline" in somali_note.text
            assert app.keyboard(Window, 274, None, None, ["down"])
            assert app.pack_index == 0
            update_button = next(
                widget
                for widget in app.root.get_screen("packs").ids.pack_rows.walk()
                if isinstance(widget, Button) and widget.text == "Update"
            )
            update_note = next(
                widget
                for widget in app.root.get_screen("packs").ids.pack_rows.walk()
                if type(widget).__name__ == "MDLabel"
                and widget.text.startswith("Update available")
            )
            assert not update_button.disabled
            assert "2 MB download" in update_note.text
            assert app.keyboard(Window, 13, None, 13, [])
            start_download.assert_called_once_with("somali")
            assert app.keyboard(Window, 274, None, None, ["down"])
            assert app.pack_index == 1
            assert app.pack_options[1]["title"].text.startswith("› ")
            assert app.keyboard(Window, 13, None, 13, [])
            assert start_download.call_count == 2
            start_download.assert_any_call("french")
        installed_pack = [
            {
                "id": "somali",
                "title": "Somali / English",
                "installed": True,
                "installed_bytes": 300,
                "download_bytes": 300,
                "storage_bytes": 300,
            }
        ]
        with (
            patch.object(app.pack_manager, "list_packs", return_value=installed_pack),
            patch.object(app, "remove_pack") as remove_pack,
        ):
            app.open_packs()
            assert app.keyboard(Window, 274, None, None, ["down"])
            assert app.keyboard(Window, 13, None, 13, [])
            keep_dialog = app.pack_dialog
            assert keep_dialog is not None
            assert app.pack_dialog_index == 0
            assert app.pack_dialog_buttons[0].text.startswith("› ")
            assert app.keyboard(Window, 13, None, 13, [])
            assert app.pack_dialog is None
            remove_pack.assert_not_called()
            assert app.keyboard(Window, 13, None, 13, [])
            dialog = app.pack_dialog
            assert dialog is not None
            assert app.keyboard(Window, 275, None, None, [])
            assert app.pack_dialog_index == 1
            assert app.pack_dialog_buttons[1].text.startswith("› ")
            assert app.keyboard(Window, 13, None, 13, [])
            remove_pack.assert_called_once_with(dialog, "somali")
            app.dismiss_pack_dialog(dialog)
        app.pack_busy = True
        app.pack_cancel_event = threading.Event()
        app.pack_cancel_requested = False
        assert app.keyboard(Window, 27)
        assert app.pack_cancel_event.is_set()
        assert app.root.current == "packs"
        app.pack_busy = False
        app.pack_cancel_event = None
        app.pack_cancel_requested = False
        assert app.keyboard(Window, 27)
        assert app.root.current == "home"
        home.ids.input_text.focus = False

        saved_history = app.history
        saved_items = [
            {
                "favourite": False,
                "text": "first saved text",
                "source": "English",
                "target": "French",
                "mode": "Translate meaning",
            },
            {
                "favourite": True,
                "text": "second saved text",
                "source": "English",
                "target": "French",
                "mode": "Translate meaning",
            },
        ]
        with (
            patch.object(app.history, "read", return_value=saved_items),
            patch.object(app, "restore_saved") as restore_saved,
        ):
            app.show_history()
            assert app.root.current == "saved"
            assert app.keyboard(Window, 274, None, None, ["down"])
            assert app.saved_index == 0
            assert app.keyboard(Window, 274, None, None, ["down"])
            assert app.saved_index == 1
            assert (
                app.root.get_screen("saved")
                .ids.saved_items.children[0]
                .text.startswith("› ")
            )
            assert app.keyboard(Window, 13, None, 13, [])
            restore_saved.assert_called_once_with(saved_items[1])
            app.close_picker()
        damaged_history_path = folder / "damaged-history.json"
        damaged_history_path.write_text('{"version":1,"items":[', encoding="utf-8")
        damaged_history_bytes = damaged_history_path.read_bytes()
        app.history = History(damaged_history_path)
        app.show_history()
        assert "Saved history is damaged" in app.status
        assert app.root.current == "home"
        assert damaged_history_path.read_bytes() == damaged_history_bytes
        assert app.history_recovery_dialog is not None
        assert app.history_recovery_index == 0
        assert app.keyboard(Window, 13, None, 13, [])
        assert app.history_recovery_dialog is None
        assert damaged_history_path.read_bytes() == damaged_history_bytes
        previous_backups = set(folder.glob("damaged-history.json.backup-*"))
        app.show_history()
        assert app.history_recovery_dialog is not None
        assert app.keyboard(Window, 275, None, None, [])
        assert app.history_recovery_index == 1
        assert app.keyboard(Window, 13, None, 13, [])
        new_backups = (
            set(folder.glob("damaged-history.json.backup-*")) - previous_backups
        )
        assert len(new_backups) == 1
        assert next(iter(new_backups)).read_bytes() == damaged_history_bytes
        assert app.history.read() == []
        assert app.root.current == "home"
        assert "Open Saved to continue" in app.status
        app.show_history()
        assert app.root.current == "saved"
        app.history = saved_history

        saved_mode, saved_source, saved_target = app.mode, app.source, app.target
        app.mode = "Translate meaning"
        app.source, app.target = "Detect language/script", "English"
        app.convert("𐒠𐒡")
        assert "Osmanya script detected" in app.status
        assert "not meaning translation" in app.status
        app.mode, app.source, app.target = saved_mode, saved_source, saved_target
        app.refresh_fonts()

        saved_mode, saved_source, saved_target = app.mode, app.source, app.target
        saved_detected_language = app.detected_language
        app.mode = "Translate meaning"
        app.source, app.target = "Detect language/script", "English"
        with patch("main.model_directory"):
            app.convert("Waan ku jeclahay")
        assert app.detected_language[0] == "Somali Latin"
        assert "Detected Somali Latin" in app.status
        app.translate_trigger.cancel()
        with patch("main.model_directory"):
            app.convert("Ou est la gare")
        assert app.detected_language[0] == "French"
        assert "Detected French (82% confidence)" in app.status
        app.translate_trigger.cancel()
        app.detected_language = None
        caution = "Somali translation may be inaccurate; check important details."
        app.show_translation(
            app.generation, Conversion("Somali output", (caution,)), None
        )
        assert app.status == caution
        assert home.ids.status_label.text == caution
        app.mode, app.source, app.target = saved_mode, saved_source, saved_target
        app.detected_language = saved_detected_language
        app.refresh_fonts()
        with patch.object(Path, "is_file", return_value=False):
            app.show_script_reference("Borama")
        assert app.root.current == "alphabet"
        chart_status = app.root.get_screen("alphabet").ids.chart_status.text
        assert chart_status == (
            "Chart image unavailable. You can still enter text for limited conversion."
        ), repr(chart_status)
        app.root.current = "home"

        failed_download = Mock()
        failed_download.result.side_effect = OSError("C:\\private\\pack.zip")
        app.pack_busy = True
        app.pack_cancel_event = threading.Event()
        with patch.object(app, "refresh_pack_screen"):
            app.finish_pack_download(failed_download, "somali")
        assert app.pack_status == (
            "Download failed. Check your connection and available storage, then try again."
        )
        failed_dialog = Mock()
        with (
            patch.object(
                app.pack_manager, "remove", side_effect=OSError("C:\\private\\packs")
            ),
            patch.object(app, "refresh_pack_screen"),
        ):
            app.remove_pack(failed_dialog, "somali")
        assert app.pack_status == (
            "Could not remove the pack. Close Saylacian and try again."
        )
        assert failed_dialog.dismiss.called

        app.mode = "Convert writing system"
        app.source, app.target = "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
        app.open_old_nubian_studio()
        studio = app.root.get_screen("old_nubian_studio")
        studio.ids.reader_original.text = "ⲁ\nⲃ"
        assert app.keyboard(Window, 13, None, 13, [])
        assert studio.ids.reader_latin.text == "a\nb"
        assert app.keyboard(Window, 27)
        assert app.root.current == "home"

        app.mode = "Convert writing system"
        app.source, app.target = "Somali Latin", "Osmanya"
        app.refresh_fonts()
        home.ids.input_text.text = "dhagax!"
        assert home.ids.output_text.text == "𐒊𐒖𐒌𐒖𐒄!"
        home.ids.input_text.text = "ii uu"
        assert home.ids.output_text.text == "𐒕 𐒓"
        assert "reverse conversion may read" in app.status

        app.source, app.target = "Somali Latin", "Borama"
        app.refresh_fonts()
        home.ids.input_text.text = "dhag!"
        borama = "\ue00a\ue000\ue00b!"
        assert home.ids.output_text.text == borama
        assert home.ids.output_text.font_name == "SaylacianBorama"
        module = app.__class__.__module__
        with patch(f"{module}.publish_windows_clipboard") as published:
            app.copy(borama)
            published.assert_not_called()
        assert "no script label" in app.status
        package = encode_saylacian_text(borama, "Borama")
        with patch("main.Clipboard.paste", return_value=package):
            app.source, app.target = "Somali Latin", "Osmanya"
            app.refresh_fonts()
            app.paste()
        assert (app.source, app.target) == ("Borama", "Somali Latin")
        assert home.ids.input_text.font_name == "SaylacianBorama"
        assert home.ids.output_text.text == "dhag!"

        app.source, app.target = "Somali Latin", "Osmanya"
        app.refresh_fonts()
        home.ids.input_text.text = "plain text"
        home.ids.input_text.text = borama
        assert "no script label" in app.status
        assert home.ids.output_text.text == ""
        app.open_copy_menu(home.ids.input_copy_button, borama)
        assert [item["text"] for item in app.copy_menu.items] == ["Copy text"]
        app.copy_menu.dismiss()
        app.target = "Borama"
        app.refresh_fonts()
        app.open_copy_menu(home.ids.input_copy_button, borama)
        assert [item["text"] for item in app.copy_menu.items] == ["Copy text"]
        app.copy_menu.dismiss()
        home.ids.input_text.text = package
        assert app.source == "Borama" and app.target == "Somali Latin"
        assert home.ids.input_text.text == borama
        assert home.ids.output_text.text == "dhag!"
        assert "Imported Saylacian Text v1" in app.status
        (folder / "pasted-borama.json").write_text(
            json.dumps(
                {
                    "input": borama,
                    "font": home.ids.input_text.font_name,
                    "output": home.ids.output_text.text,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        app.source, app.target = "Somali Latin", "Kaddare"
        app.refresh_fonts()
        home.ids.input_text.text = "shadh!"
        kaddare = "\ue10d\ue100\ue10e!"
        assert home.ids.output_text.text == kaddare
        assert home.ids.output_text.font_name == "SaylacianKaddare"
        with patch("kivy.core.clipboard.Clipboard.copy") as copied:
            home.ids.output_text.select_all()
            home.ids.output_text.copy()
            assert copied.call_args is not None, (
                home.ids.output_text.selection_text,
                app.source,
                app.target,
                app.mode,
                app.status,
            )
            assert copied.call_args.args[0] == "shadh!"
        with patch("main.Clipboard.paste", return_value=kaddare):
            app.source, app.target = "Somali Latin", "Osmanya"
            app.refresh_fonts()
            app.paste()
        assert (app.source, app.target) == ("Somali Latin", "Osmanya")
        assert "no script label" in app.status
        with patch(
            "main.Clipboard.paste",
            return_value=encode_saylacian_text(kaddare, "Kaddare"),
        ):
            app.paste()
        assert (app.source, app.target) == ("Kaddare", "Somali Latin")
        assert home.ids.input_text.font_name == "SaylacianKaddare"
        assert home.ids.output_text.text == "shadh!"
        assert home.ids.input_text.font_name == "SaylacianKaddare"
        assert home.ids.output_text.text == "shadh!"
        (folder / "pasted-kaddare.json").write_text(
            json.dumps(
                {
                    "input": kaddare,
                    "font": home.ids.input_text.font_name,
                    "output": home.ids.output_text.text,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        home.ids.input_text.text = "\ue999"
        assert "no script label" in app.status

        app.source, app.target = "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        app.refresh_fonts()
        home.ids.input_text.text = "ng dj"
        assert home.ids.output_text.text == "ⳟ ϫ"
        assert "Other Coptic readings" in app.alternative_readings

        app.source, app.target = "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
        app.refresh_fonts()
        home.ids.input_text.text = "ⲀⲂⲄ\nⳜⳞⳠⳢ\nⲁ⳯⳰⳱"
        assert home.ids.output_text.text == "ABG\nJNGNYW\na⳯⳰⳱"
        assert home.ids.output_text.font_name == app.font_for("Old Nubian (Coptic)")
        assert "placement with Latin are not interpreted" in app.status
        app.open_picker("target")
        app.filter_languages("Old Nubian")
        assert any(
            "Old Nubian" in item.text
            for item in app.root.get_screen("picker").ids.options.children
        )
        assert any(
            item.text.endswith("Latin reading")
            and item.secondary_text == "Limited character readings"
            for item in app.root.get_screen("picker").ids.options.children
        )
        app.filter_languages("Nobiin")
        assert not app.root.get_screen("picker").ids.options.children
        app.close_picker()
        app.source, app.target = "Somali Latin", "Borama"
        app.refresh_fonts()
        home.ids.input_text.text = "dhag!"
        app.open_copy_menu(home.ids.output_copy_button, home.ids.output_text.text)
        assert [item["text"] for item in app.copy_menu.items] == [
            "Copy text",
            "Copy image",
            "Copy Latin",
        ]
        with patch(f"{module}.publish_windows_clipboard") as published:
            app.copy_menu.items[0]["on_release"]()
            assert [name for name, _ in published.call_args.args[0]] == [
                "Saylacian Text v1",
                "Rich Text Format",
                "HTML Format",
                "CF_UNICODETEXT",
            ]
        app.open_copy_menu(home.ids.output_copy_button, home.ids.output_text.text)
        with patch(f"{module}.publish_windows_clipboard") as published:
            app.copy_menu.items[1]["on_release"]()
            assert [name for name, _ in published.call_args.args[0]] == [
                "PNG",
                "CF_DIB",
                "CF_UNICODETEXT",
            ]
        app.open_copy_menu(home.ids.output_copy_button, home.ids.output_text.text)
        with patch(f"{module}.publish_windows_clipboard") as published:
            app.copy_menu.items[2]["on_release"]()
            assert (
                dict(published.call_args.args[0])["CF_UNICODETEXT"]
                .decode("utf-16-le")
                .rstrip("\0")
                == "dhag!"
            )
    except (
        AssertionError,
        AttributeError,
        IndexError,
        ImportError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ):
        import traceback

        (folder / "result.json").write_text(
            json.dumps({"pass": False, "error": traceback.format_exc()}),
            encoding="utf-8",
        )
        app.stop()
        return

    def begin_meaning(dt=0):
        app.source, app.target = "English", "French"
        app.mode = "Translate meaning"
        app.refresh_fonts()
        home.ids.input_text.text = "Hello, how are you?"
        app.convert(home.ids.input_text.text)
        started = time.monotonic()

        def inspect(result_dt):
            result = home.ids.output_text.text
            if result:
                app.open_copy_menu(home.ids.output_copy_button, result)
                assert [item["text"] for item in app.copy_menu.items] == ["Copy text"]
                with patch(f"{module}.publish_windows_clipboard") as published:
                    app.copy_menu.items[0]["on_release"]()
                    assert (
                        dict(published.call_args.args[0])["CF_UNICODETEXT"]
                        .decode("utf-16-le")
                        .rstrip("\0")
                        == result
                    )
                Window.screenshot(name=str(folder / "packaged-meaning.png"))
                checks = [
                    "live Kivy UI",
                    "mode-specific picker labels",
                    "standard-text copy menu",
                    "Osmanya",
                    "Borama/Kaddare bundled font rendering",
                    "Borama/Kaddare tagged-package import, font selection, and reverse conversion",
                    "three Borama/Kaddare copy actions",
                    "offline pack cancellation control and request state",
                    "keyboard-only mode, language, offline-pack, safe removal, and pack-update actions",
                    "missing-pack recovery and estimated offline download guidance",
                    "translator hint contrast, visible keyboard focus, text-scale fit, and compact/wide/short-landscape breakpoints",
                    "Old Nubian reverse alternatives",
                    "Old Nubian paired reading with case and line-break preservation",
                    "Old Nubian searchable alphabet and reading studio",
                    "Old Nubian copy actions and versioned record import/export",
                    "picker search",
                    "local meaning model",
                    "short French detection route with visible confidence",
                    "plain Somali translation caution in the live status label",
                    "clear chart-image recovery guidance in the alphabet screen",
                    "limited-coverage wording in the Old Nubian Latin-reading picker",
                    "safe recovery guidance for pack download and removal failures",
                ]
                (folder / "result.json").write_text(
                    json.dumps(
                        {
                            "pass": result == "Bonjour, comment allez-vous ?",
                            "output": result,
                            "checks": checks,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                app.stop()
                return False
            if time.monotonic() - started > 30:
                (folder / "result.json").write_text(
                    json.dumps({"pass": False, "status": app.status}), encoding="utf-8"
                )
                app.stop()
                return False

        Clock.schedule_interval(inspect, 0.2)

    def capture_old_nubian_reader(dt):
        app.root.get_screen("home").ids.input_text.focus = False
        Window.screenshot(name=str(folder / "old-nubian-reading.png"))
        app.open_old_nubian_studio()
        studio = app.root.get_screen("old_nubian_studio")
        assert studio.ids.reader_latin.text == "ABG\nJNGNYW\na⳯⳰⳱"
        assert studio.ids.reader_latin.font_name == app.font_for("Old Nubian (Coptic)")
        assert "U+2CEF COPTIC COMBINING NI ABOVE" in app.reader_mark_details
        assert "code point 11" in app.reader_mark_details
        assert studio.ids.reader_mark_details.height > 0
        studio.ids.alphabet_search.text = "2cdf"
        assert len(studio.ids.reader_alphabet.children) == 1
        studio.ids.reader_alphabet.children[0].trigger_action(duration=0)
        assert "U+2CDF" in app.reader_detail
        saved_record = export_reading_record(make_reading_record("ⲁ\nⲃ"))
        with patch("main.Clipboard.paste", return_value=saved_record):
            app.import_old_nubian_reading()
        assert studio.ids.reader_original.text == "ⲁ\nⲃ"
        assert studio.ids.reader_latin.text == "a\nb"
        with patch("main.Clipboard.copy") as copied:
            app.copy_old_nubian_reading("original")
            copied.assert_called_once_with("ⲁ\nⲃ")
        with patch("main.Clipboard.copy") as copied:
            app.copy_old_nubian_reading("latin")
            copied.assert_called_once_with("a\nb")
        studio.ids.reader_original.text = home.ids.input_text.text
        app.read_old_nubian_passage()

        def capture_studio(result_dt):
            Window.screenshot(name=str(folder / "old-nubian-reading-studio.png"))

            def leave_studio(after_capture_dt):
                app.close_picker()
                app.source, app.target = "Somali Latin", "Borama"
                app.refresh_fonts()
                home.ids.input_text.text = "dhag!"
                Clock.schedule_once(capture_borama, 0.7)

            Clock.schedule_once(leave_studio, 0.3)

        Clock.schedule_once(capture_studio, 1.0)

    def show_old_nubian_reader(dt):
        app.source, app.target = "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
        app.refresh_fonts()
        home.ids.output_text.cancel_selection()
        home.ids.input_text.text = "ⲀⲂⲄ\nⳜⳞⳠⳢ\nⲁ⳯⳰⳱"
        Clock.schedule_once(capture_old_nubian_reader, 0.2)

    def capture_kaddare(dt):
        home.ids.output_text.cancel_selection()
        Window.screenshot(name=str(folder / "chart-kaddare.png"))
        begin_meaning()

    def capture_borama(dt):
        home.ids.output_text.cancel_selection()
        Window.screenshot(name=str(folder / "chart-borama.png"))
        app.source, app.target = "Somali Latin", "Kaddare"
        app.refresh_fonts()
        home.ids.input_text.text = "shadh!"
        Clock.schedule_once(capture_kaddare, 0.7)

    app.mode = "Convert writing system"
    app.source, app.target = "Somali Latin", "Borama"
    app.refresh_fonts()
    home.ids.input_text.text = "dhag!"
    Clock.schedule_once(show_old_nubian_reader, 0.1)
