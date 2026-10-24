# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit local saves; schema version and atomic writes protect existing records."""

import json
from pathlib import Path


class History:
    def __init__(self, path):
        self.path = Path(path)

    def read(self):
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("version") != 1:
            raise ValueError("Unknown history format; file left untouched.")
        return data["items"]

    def save(
        self,
        source,
        target,
        text,
        result,
        favourite=False,
        mode="Convert writing system",
    ):
        items = self.read()
        items.insert(
            0,
            {
                "source": source,
                "target": target,
                "text": text,
                "result": result,
                "favourite": favourite,
                "mode": mode,
            },
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(
                {"version": 1, "items": items[:100]}, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def clear(self):

        self.read()
        self.path.write_text(json.dumps({"version": 1, "items": []}), encoding="utf-8")
