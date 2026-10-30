# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real headless page tests through DOM events, without OS input injection."""

import json
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from saylacian.website.app import create_app

server = make_server("127.0.0.1", 0, create_app(), threaded=True)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_port}"
checks = []
errors = []
posts = []
try:
    with sync_playwright() as automation:
        browser = automation.chromium.launch(
            executable_path=(
                "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            ),
            headless=True,
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.route(
            "**/*",
            lambda route: (
                route.continue_()
                if urlparse(route.request.url).hostname == "127.0.0.1"
                else route.abort()
            ),
        )
        context.add_init_script(
            "Object.defineProperty(navigator,'clipboard',{configurable:true,value:{readText:async()=>window.__clipboard||'',writeText:async(text)=>{window.__clipboard=text}}});"
        )
        page = context.new_page()
        page.set_default_timeout(7000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on(
            "request", lambda r: posts.append(r.url) if r.method == "POST" else None
        )
        page.goto(base)
        page.wait_for_function("() => (document.fonts.status==='loaded')")
        assert page.locator("[data-glyph]").count() == 30
        page.evaluate(
            "document.querySelector('#input').value='Dhagax!';document.quer"
            "ySelector('#input').dispatchEvent(new "
            "Event('input',{bubbles:true}));"
        )
        assert not posts
        page.evaluate("document.querySelector('#convert').click()")
        page.wait_for_function(
            "() => (document.querySelector('#output').value==='𐒊𐒖𐒌𐒖𐒄!')"
        )
        checks.append("actual API conversion and no automatic text submission")
        page.screenshot(
            path=str(PROJECT / "docs/previews/website-desktop.png"), full_page=True
        )
        page.evaluate("document.querySelector('#copy').click()")
        page.wait_for_function("() => (window.__clipboard==='𐒊𐒖𐒌𐒖𐒄!')")
        page.evaluate("document.querySelector('#clear').click()")
        assert (
            page.locator("#input").input_value() == ""
            and page.locator("#output").input_value() == ""
        )
        page.evaluate("document.querySelector('#paste').click()")
        page.wait_for_function(
            "() => (document.querySelector('#input').value==='𐒊𐒖𐒌𐒖𐒄!')"
        )
        checks.append("copy/clear/paste DOM controls with isolated clipboard double")
        page.evaluate(
            "document.querySelector('#source').value='Osmanya';document.que"
            "rySelector('#target').value='Somali "
            "Latin';document.querySelector('#source').dispatchEvent(new "
            "Event('change'));document.querySelector('#convert').click()"
        )
        page.wait_for_function(
            "() => (document.querySelector('#output').value==='dhagax!')"
        )
        page.evaluate("document.querySelector('#swap').click()")
        assert (
            page.locator("#source").input_value() == "Somali Latin"
            and page.locator("#input").input_value() == "dhagax!"
        )
        checks.append("swap uses current output and correct language direction")
        page.evaluate(
            "document.querySelector('#source').value='English';document.que"
            "rySelector('#source').dispatchEvent(new "
            "Event('change'));document.querySelector('#convert').click()"
        )
        page.wait_for_function(
            "() => "
            "(document.querySelector('#status').textContent.includes('no "
            "validated mapping'))"
        )
        assert page.locator("#output").input_value() == ""
        checks.append("unsupported pair displays error without stale output")
        page.evaluate(
            "document.querySelector('#source').value='English';document.que"
            "rySelector('#target').value='French';document.querySelector('#"
            "mode').value='meaning';document.querySelector('#input').value="
            "'Hello, how are "
            "you?';document.querySelector('#input').dispatchEvent(new "
            "Event('input'));document.querySelector('#convert').click()"
        )
        page.wait_for_function(
            "() => document.querySelector('#output').value==='Bonjour, "
            "comment allez-vous ?'"
        )
        checks.append("real English/French model through website UI and API")
        page.evaluate(
            "document.querySelector('#mode').value='transliterate';document"
            ".querySelector('#target').value='Somali Latin'"
        )
        page.evaluate(
            "document.querySelector('#source').value='Osmanya';document.que"
            "rySelector('#source').dispatchEvent(new "
            "Event('change'));document.querySelector('details').open=true;d"
            "ocument.querySelector('#clear').click();document.querySelector"
            "('[data-glyph]').click()"
        )
        assert page.locator("#input").input_value() == "𐒀"
        checks.append("shared alphabet with input aid")
        page.evaluate(
            "Object.defineProperty(navigator,'clipboard',{value:{readText:a"
            "sync()=>{throw Error('denied')},writeText:async()=>{throw "
            "Error('denied')}}});document.querySelector('#paste').click()"
        )
        page.wait_for_function(
            "() => "
            "(document.querySelector('#status').textContent.includes('Clipb"
            "oard access unavailable'))"
        )
        assert page.locator("#input").input_value() == "𐒀"
        checks.append("clipboard denial preserves input and gives fallback")
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.evaluate("document.querySelector('details').open=false")
        page.screenshot(
            path=str(PROJECT / "docs/previews/website-mobile.png"), full_page=True
        )
        checks.append("390px layout without horizontal overflow")
        assert not errors, errors
        browser.close()
    (PROJECT / "docs/website-browser-results.json").write_text(
        json.dumps(
            {
                "pass": True,
                "checks": checks,
                "page_errors": errors,
                "network": "only loopback permitted",
                "input_method": (
                    "DOM events in isolated headless Edge; no OS mouse/keyboard input"
                ),
            },
            indent=2,
        )
    )
    print(json.dumps({"pass": True, "checks": checks}, indent=2))
finally:
    server.shutdown()
    thread.join(timeout=5)
