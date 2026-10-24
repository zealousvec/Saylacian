# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline alphabet information derived from the actual conversion resource."""

import unicodedata

from .transliteration import RESOURCE


def osmanya_letters():
    """Group ambiguous Latin readings under each assigned Osmanya letter."""
    readings = {}
    for latin, glyph in RESOURCE["mapping"].items():
        readings.setdefault(glyph, []).append(latin)
    return [
        {
            "glyph": glyph,
            "readings": "/".join(readings[glyph]),
            "codepoint": f"U+{ord(glyph):04X}",
            "name": unicodedata.name(glyph),
        }
        for glyph in sorted(readings)
    ]
