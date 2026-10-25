# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit local saves; schema version and atomic writes protect existing records."""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path

MAX_HISTORY_BYTES = 16 * 1024 * 1024


class DamagedHistoryError(ValueError):
    """Indicate malformed history that can be backed up before recovery."""


class History:
    def __init__(self, path):
        self.path = Path(path)

    def read(self):
        if not self.path.exists():
            return []
        try:
            with self.path.open("rb") as history_file:
                content = history_file.read(MAX_HISTORY_BYTES + 1)
            if len(content) > MAX_HISTORY_BYTES:
                raise DamagedHistoryError(
                    "Saved history is too large; file left untouched."
                )
            data = json.loads(content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise DamagedHistoryError(
                "Saved history is damaged; file left untouched."
            ) from error

        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Unknown history format; file left untouched.")

        items = data.get("items")
        if not isinstance(items, list) or not all(
            self._is_valid_item(item) for item in items
        ):
            raise DamagedHistoryError(
                "Saved history has invalid entries; file left untouched."
            )
        return items

    def backup_and_reset(self):
        """Preserve malformed history, then atomically start a fresh file."""
        try:
            self.read()
        except DamagedHistoryError:
            pass
        else:
            raise ValueError("Saved history is readable; recovery was not needed.")

        for attempt in range(10):
            backup_path = self.path.with_name(
                f"{self.path.name}.backup-{time.time_ns()}-{attempt}"
            )
            try:
                with (
                    self.path.open("rb") as source,
                    backup_path.open("xb") as backup_file,
                ):
                    shutil.copyfileobj(source, backup_file, length=1024 * 1024)
                    backup_file.flush()
                    os.fsync(backup_file.fileno())
                break
            except FileExistsError:
                continue
            except OSError:
                backup_path.unlink(missing_ok=True)
                raise
        else:
            raise FileExistsError("Could not create a unique saved-history backup.")

        try:
            self._write([])
        except OSError as error:
            raise OSError(
                f"Could not reset saved history; original remains. Backup: {backup_path.name}. {error}"
            ) from error
        return backup_path

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
            if temporary_path.stat().st_size > MAX_HISTORY_BYTES:
                raise ValueError("Saved history exceeds its size limit.")
            temporary_path.replace(self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
