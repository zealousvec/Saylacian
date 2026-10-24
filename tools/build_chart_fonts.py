# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build private-use display fonts from the project's licensed script charts.

This build-time script needs Pillow and fontTools. It does not alter source
charts. Each output is a bitmap-derived outline font; the source chart and
CC BY-SA attribution are documented in notices/HISTORICAL_SCRIPT_CHARTS.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "saylacian/core/data/scripts"
ASSETS = ROOT / "assets"
FONT_SIZE = 1000
GLYPH_HEIGHT = 720
BASELINE = 40


def _rectangle(pen: TTGlyphPen, left: int, bottom: int, right: int, top: int) -> None:
    pen.moveTo((left, bottom))
    pen.lineTo((right, bottom))
    pen.lineTo((right, top))
    pen.lineTo((left, top))
    pen.closePath()


def _glyph_from_crop(image: Image.Image, box: list[int]):
    x, y, width, height = box
    sample = image.crop((x, y, x + width, y + height)).convert("L")

    mask = sample.point(lambda value: 255 if value < 145 else 0)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError(f"Empty glyph crop: {box}")
    mask = mask.crop(bounds)
    pixels = mask.load()
    pixel_width, pixel_height = mask.size
    scale = GLYPH_HEIGHT / pixel_height

    active: dict[tuple[int, int], int] = {}
    rectangles: list[tuple[int, int, int, int]] = []
    for row in range(pixel_height):
        runs = set()
        column = 0
        while column < pixel_width:
            if pixels[column, row] == 0:
                column += 1
                continue
            start = column
            while column < pixel_width and pixels[column, row] != 0:
                column += 1
            runs.add((start, column))
        for run, start_row in list(active.items()):
            if run not in runs:
                rectangles.append((run[0], start_row, run[1], row))
                del active[run]
        for run in runs:
            active.setdefault(run, row)
    for run, start_row in active.items():
        rectangles.append((run[0], start_row, run[1], pixel_height))

    pen = TTGlyphPen(None)
    for left, top, right, bottom in rectangles:
        x0 = round(left * scale + 40)
        x1 = round(right * scale + 40)
        y0 = round((pixel_height - bottom) * scale + BASELINE)
        y1 = round((pixel_height - top) * scale + BASELINE)
        _rectangle(pen, x0, y0, x1, y1)
    advance = round(pixel_width * scale + 100)
    return pen.glyph(), (advance, 40)


def build_font(
    script: str, source_image: Path, records: list[dict], destination: Path
) -> None:
    image = Image.open(source_image)
    names = [".notdef", "space"]
    cmap: dict[int, str] = {0x20: "space"}
    glyphs = {".notdef": TTGlyphPen(None).glyph(), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (500, 0), "space": (300, 0)}
    for index, record in enumerate(records):
        codepoint = int(record["pua"].removeprefix("U+"), 16)
        glyph_name = f"uni{codepoint:04X}"
        glyph, metric = _glyph_from_crop(image, record["chart_forms"][0]["crop"])
        names.append(glyph_name)
        cmap[codepoint] = glyph_name
        glyphs[glyph_name] = glyph
        metrics[glyph_name] = metric

    builder = FontBuilder(FONT_SIZE, isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=850, descent=-150)
    builder.setupNameTable(
        {
            "familyName": f"Saylacian {script} Chart",
            "styleName": "Regular",
            "uniqueFontIdentifier": f"Saylacian-{script}-Chart-1.0",
            "fullName": f"Saylacian {script} Chart Regular",
            "psName": f"Saylacian-{script}-Chart-Regular",
            "version": "Version 1.000",
            "copyright": "Derived from Jugydmort's chart; CC BY-SA 4.0. See project notices.",
        }
    )
    builder.setupOS2(
        sTypoAscender=850, sTypoDescender=-150, usWinAscent=850, usWinDescent=150
    )
    builder.setupPost()
    builder.setupMaxp()
    builder.save(destination)
    print(f"Built {destination.name}: {len(records)} chart glyphs")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for script, filename, chart in (
        ("Borama", "borama.json", "Borama_Alphabet_Chart.jpg"),
        ("Kaddare", "kaddare.json", "Kaddare_Alphabet_Chart.jpg"),
    ):
        data = json.loads((DATA / filename).read_text(encoding="utf-8"))
        build_font(
            script,
            ROOT / "assets/research" / chart,
            data["records"],
            ASSETS / f"{script}Chart-Regular.ttf",
        )


if __name__ == "__main__":
    main()
