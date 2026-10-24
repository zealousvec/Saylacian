# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit local saves; schema version and atomic writes protect existing records."""

import json
import tempfile
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
        self._write(items[:100])

    def clear(self):
        self.read()
        self._write([])

    def _write(self, items):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(
                    {"version": 1, "items": items},
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )
            temporary_path.replace(self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
