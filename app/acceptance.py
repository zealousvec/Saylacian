# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check live Kivy widgets and paste handling without OS input injection."""

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

from kivy.clock import Clock
from kivy.core.window import Window

from saylacian.core.interchange import encode_saylacian_text


def start(app):
    folder = Path(
        os.environ.get("SAYLACIAN_EVIDENCE", str(Path.home() / "Saylacian-evidence"))
    )
    folder.mkdir(parents=True, exist_ok=True)
    home = app.root.get_screen("home")
    try:
        app.mode = "Convert writing system"
        app.source, app.target = "Somali Latin", "Osmanya"
        app.refresh_fonts()
        home.ids.input_text.text = "dhagax!"
        assert home.ids.output_text.text == "𐒊𐒖𐒌𐒖𐒄!"

        app.source, app.target = "Somali Latin", "Borama"
        app.refresh_fonts()
        home.ids.input_text.text = "dhag!"
        borama = "\ue00a\ue000\ue00b!"
        assert home.ids.output_text.text == borama
        assert home.ids.output_text.font_name == "SaylacianBorama"
        module = app.__class__.__module__
        with patch(f"{module}.publish_windows_clipboard") as published:
            app.copy(borama)
            text_data = dict(published.call_args.args[0])["CF_UNICODETEXT"]
            assert text_data.decode("utf-16-le").rstrip("\0") == "dhag!"
        assert "Somali Latin" in app.status
        reported = ",     ,"
        with patch(f"{module}.publish_windows_clipboard") as published:
            app.copy(reported)
            text_data = dict(published.call_args.args[0])["CF_UNICODETEXT"]
            assert (
                text_data.decode("utf-16-le").rstrip("\0")
                == "hello, what is wrong with you,"
            )
        with patch("main.Clipboard.paste", return_value=borama):
            app.source, app.target = "Somali Latin", "Osmanya"
            app.refresh_fonts()
            app.paste()
        assert (app.source, app.target) == ("Borama", "Somali Latin")
        assert home.ids.input_text.font_name == "SaylacianBorama"
        assert home.ids.output_text.text == "dhag!"

        home.ids.input_text.text = borama
        assert home.ids.input_text.font_name == "SaylacianBorama"
        assert home.ids.output_text.text == "dhag!"
        package = encode_saylacian_text(borama, "Borama")
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
            assert copied.call_args.args[0] == "shadh!"
        with patch("main.Clipboard.paste", return_value=kaddare):
            app.source, app.target = "Somali Latin", "Osmanya"
            app.refresh_fonts()
            app.paste()
        assert (app.source, app.target) == ("Kaddare", "Somali Latin")
        assert home.ids.input_text.font_name == "SaylacianKaddare"
        assert home.ids.output_text.text == "shadh!"
        home.ids.input_text.text = kaddare
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
        assert "Unrecognized private-use text" in app.status

        app.source, app.target = "Old Nubian scholarly Latin", "Old Nubian (Coptic)"
        app.refresh_fonts()
        home.ids.input_text.text = "ng dj"
        assert home.ids.output_text.text == "ⳟ ϫ"
        assert "Other Coptic readings" in app.alternative_readings
        app.open_picker("target")
        app.filter_languages("French")
        assert any(
            item.text == "French"
            for item in app.root.get_screen("picker").ids.options.children
        )
        app.close_picker()
        app.source, app.target = "Somali Latin", "Borama"
        app.refresh_fonts()
        home.ids.input_text.text = "dhag!"
        app.open_copy_menu(home.ids.output_copy_button, home.ids.output_text.text)
        assert [item["text"] for item in app.copy_menu.items] == [
            "Copy as Latin",
            "Copy as Image",
            "Copy as Saylacian Text",
        ]
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
            assert [name for name, _ in published.call_args.args[0]] == [
                "Saylacian Text v1",
                "Rich Text Format",
                "HTML Format",
                "CF_UNICODETEXT",
            ]
    except Exception:
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
                Window.screenshot(name=str(folder / "packaged-meaning.png"))
                checks = [
                    "live Kivy UI",
                    "Osmanya",
                    "Borama/Kaddare bundled font rendering",
                    "Borama/Kaddare paste detection, font selection, and reverse conversion",
                    "Old Nubian reverse alternatives",
                    "picker search",
                    "local meaning model",
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
    Clock.schedule_once(capture_borama, 0.7)
