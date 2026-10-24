# SPDX-License-Identifier: AGPL-3.0-or-later
"""Write one Saylacian sharing option to the real Windows clipboard (test helper)."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from saylacian.core.clipboard_repr import (
    formats_as_image,
    formats_as_latin,
    formats_as_saylacian_text,
)
from saylacian.core.interchange import identify_chart_text
from saylacian.core.transliteration import transliterate
from saylacian.core.windows_clipboard import publish


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.input_json).read_text(encoding="utf-8-sig"))
    mode, text, script = request["mode"], request["text"], request.get("script")
    detected = identify_chart_text(text)
    if detected:
        script = detected
        glyphs = text
    else:
        if script not in ("Borama", "Kaddare"):
            raise ValueError("Select Borama or Kaddare.")
        glyphs = transliterate(text, "Somali Latin", script).text
    latin = transliterate(glyphs, script, "Somali Latin").text
    if mode == "latin":
        formats = formats_as_latin(latin)
    elif mode == "image":
        formats = formats_as_image(script, glyphs, latin)
    elif mode == "saylacian":
        formats = formats_as_saylacian_text(script, glyphs, latin)
    else:
        raise ValueError("Unknown copy mode.")
    publish(formats)
    result = {
        "mode": mode,
        "script": script,
        "latin": latin,
        "formats": [name for name, _ in formats],
    }
    Path(request["result_path"]).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
