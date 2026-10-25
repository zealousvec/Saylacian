# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small user-facing labels and recoverable failure messages."""

from __future__ import annotations

import zipfile

DISPLAY_NAMES = {
    "Detect language/script": "Detect",
    "Somali Latin": "Somali",
    "Old Nubian (Coptic)": "Old Nubian",
    "Old Nubian scholarly Latin": "Latin reading",
}


def display_name(route_name: str) -> str:
    """Map an internal route name to concise UI copy without changing its ID."""
    return DISPLAY_NAMES.get(route_name, route_name)


def picker_choices(capabilities, mode: str) -> list[str]:
    """List implemented routes for one mode, plus script references when relevant."""
    choices = ["Detect language/script"]
    route_names = dict.fromkeys(
        name
        for route in capabilities
        if route["kind"] == "route" and route["mode"] == mode
        for name in (route["source"], route["target"])
    )
    choices.extend(route_names)

    if mode == "transliteration":
        choices.extend(name + " alphabet chart" for name in ("Borama", "Kaddare"))
    return choices


def pack_download_error_message(error: Exception) -> str:
    """Show recovery guidance without exposing local paths or hiding integrity failures."""
    if isinstance(error, ValueError):
        details = str(error)
        integrity_terms = ("sha-256", "checksum", "integrity", "unexpected size")
        if any(term in details.casefold() for term in integrity_terms):
            return "The downloaded pack failed an integrity check. Try downloading it again."
        return details
    if isinstance(error, zipfile.BadZipFile):
        return "The downloaded pack is damaged or incomplete. Try downloading it again."
    if isinstance(error, OSError):
        return "Download failed. Check your connection and available storage, then try again."
    return (
        "Could not install the pack. Close other apps using its files, then try again."
    )


def pack_removal_error_message(error: Exception) -> str:
    """Explain safe pack-removal failures without displaying machine-specific paths."""
    details = str(error)
    if isinstance(error, ValueError) and "escaped" in details.casefold():
        return "Pack files are outside the expected folder. Removal stopped for safety."
    if isinstance(error, ValueError) and "unknown language pack" in details.casefold():
        return "This pack is no longer available. Refresh the pack list and try again."
    if isinstance(error, ValueError) and "required by" in details.casefold():
        return details
    return "Could not remove the pack. Close Saylacian and try again."


def translation_error_message(error: Exception) -> str:
    """Give translation failures a next step without hiding explicit validation errors."""
    if isinstance(error, MemoryError):
        return "Not enough memory for this translation. Try a shorter passage or close other apps."
    if isinstance(error, ValueError):
        details = str(error)
        if "no local model installed" in details.casefold():
            if "downloaded-model fallback unavailable" in details.casefold():
                return "Online service unavailable. Open Packs for an offline pack."
            return "Open Packs to download an offline pack."
        if details == "Local translation runtime is not installed.":
            return "Translation support is missing. Reinstall Saylacian's Python dependencies."
        return details
    return "Could not translate. Check your connection or installed language packs."
