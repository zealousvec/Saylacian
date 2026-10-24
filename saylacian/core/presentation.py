# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small user-facing labels and recoverable failure messages."""

from __future__ import annotations

DISPLAY_NAMES = {
    "Detect language/script": "Detect",
    "Somali Latin": "Somali",
    "Old Nubian (Coptic)": "Old Nubian",
    "Old Nubian scholarly Latin": "Latin reading",
}

CONTEXT_NOTES = {
    "Somali Latin": "Latin script",
    "Osmanya": "Somali script",
    "Borama": "Limited conversion · needs Saylacian font",
    "Kaddare": "Limited conversion · needs Saylacian font",
    "Old Nubian (Coptic)": "Original Coptic-derived script",
    "Old Nubian scholarly Latin": "Scholarly transliteration",
}


def display_name(route_name: str) -> str:
    """Map an internal route name to concise UI copy without changing its ID."""
    return DISPLAY_NAMES.get(route_name, route_name)


def picker_choices(capabilities, mode: str) -> list[tuple[str, str]]:
    """List implemented routes for one mode, plus script references when relevant."""
    detection_note = (
        "English, French or Somali"
        if mode == "translation"
        else "Languages and writing systems"
    )
    choices = [("Detect language/script", detection_note)]
    route_names = dict.fromkeys(
        name
        for route in capabilities
        if route["kind"] == "route" and route["mode"] == mode
        for name in (route["source"], route["target"])
    )
    for name in route_names:
        if mode == "transliteration":
            note = CONTEXT_NOTES.get(name, "Writing system")
        elif name == "Somali Latin":
            note = "Latin script · needs fluent review"
        else:
            note = "Language"
        choices.append((name, note))

    if mode == "transliteration":
        choices.extend(
            (name + " alphabet chart", "Alphabet reference")
            for name in ("Borama", "Kaddare")
        )
    return choices


def translation_error_message(error: Exception) -> str:
    """Give translation failures a next step without hiding explicit validation errors."""
    if isinstance(error, MemoryError):
        return "Not enough memory for this translation. Try a shorter passage or close other apps."
    if isinstance(error, ValueError):
        return str(error)
    return "Could not translate. Check your connection or installed language packs."
