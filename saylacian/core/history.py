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
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError(
                "Saved history is damaged; file left untouched."
            ) from error

        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unknown history format; file left untouched.")

        items = data.get("items")
        if not isinstance(items, list) or not all(
            self._is_valid_item(item) for item in items
        ):
            raise ValueError("Saved history has invalid entries; file left untouched.")
        return items

    @staticmethod
    def _is_valid_item(item):
        if not isinstance(item, dict):
            return False
        required_text = ("source", "target", "text", "result")
        if any(not isinstance(item.get(key), str) for key in required_text):
            return False
        if not isinstance(item.get("favourite"), bool):
            return False
        return "mode" not in item or isinstance(item["mode"], str)

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
