# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, atomic persistence for the desktop app's last visible session."""

import json
import os
from pathlib import Path

SESSION_VERSION = 1
MAX_SESSION_BYTES = 64_000
MAX_INPUT_CHARS = 4_000
MAX_OUTPUT_CHARS = 16_000
VALID_MODES = frozenset({"Convert writing system", "Translate meaning"})


def read_session(path):
    """Read a valid session snapshot, returning None for missing or invalid data."""
    session_path = Path(path)
    try:
        if session_path.stat().st_size > MAX_SESSION_BYTES:
            return None
        snapshot = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    if not isinstance(snapshot, dict) or snapshot.get("version") != SESSION_VERSION:
        return None
    if snapshot.get("mode") not in VALID_MODES:
        return None
    for key, maximum in (
        ("source", 100),
        ("target", 100),
        ("status", 1000),
        ("alternatives", 2000),
    ):
        if key in snapshot and (
            not isinstance(snapshot[key], str) or len(snapshot[key]) > maximum
        ):
            return None
    for key, maximum in (("input", MAX_INPUT_CHARS), ("output", MAX_OUTPUT_CHARS)):
        if not isinstance(snapshot.get(key), str) or len(snapshot[key]) > maximum:
            return None
    if not all(isinstance(snapshot.get(key), str) for key in ("source", "target")):
        return None
    return snapshot


def write_session(path, snapshot):
    """Write one bounded session snapshot atomically; return False on I/O failure."""
    session_path = Path(path)
    try:
        payload = json.dumps(snapshot, ensure_ascii=False)
        if len(payload.encode("utf-8")) > MAX_SESSION_BYTES:
            return False
        temporary = session_path.with_suffix(".tmp")
        session_path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, session_path)
        return True
    except (OSError, TypeError, ValueError, UnicodeError):
        try:
            temporary.unlink(missing_ok=True)
        except (OSError, UnboundLocalError):
            pass
        return False
