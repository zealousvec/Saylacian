# SPDX-License-Identifier: AGPL-3.0-or-later
"""Machine-readable implemented routes and script research/reference targets."""

CAPABILITIES = (
    {
        "kind": "route",
        "source": "Somali Latin",
        "target": "Osmanya",
        "mode": "transliteration",
        "status": "alpha",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Osmanya",
        "target": "Somali Latin",
        "mode": "transliteration",
        "status": "alpha",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Old Nubian (Coptic)",
        "target": "Old Nubian scholarly Latin",
        "mode": "transliteration",
        "status": "working",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Old Nubian scholarly Latin",
        "target": "Old Nubian (Coptic)",
        "mode": "transliteration",
        "status": "alpha limited",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Somali Latin",
        "target": "Borama",
        "mode": "transliteration",
        "status": "alpha limited",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Borama",
        "target": "Somali Latin",
        "mode": "transliteration",
        "status": "alpha limited",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Somali Latin",
        "target": "Kaddare",
        "mode": "transliteration",
        "status": "alpha limited",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Kaddare",
        "target": "Somali Latin",
        "mode": "transliteration",
        "status": "alpha limited",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "English",
        "target": "French",
        "mode": "translation",
        "status": "working",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "French",
        "target": "English",
        "mode": "translation",
        "status": "working",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "English",
        "target": "Somali Latin",
        "mode": "translation",
        "status": "alpha",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Somali Latin",
        "target": "English",
        "mode": "translation",
        "status": "alpha",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "Somali Latin",
        "target": "French",
        "mode": "translation",
        "status": "alpha pivot",
        "offline": True,
    },
    {
        "kind": "route",
        "source": "French",
        "target": "Somali Latin",
        "mode": "translation",
        "status": "alpha pivot",
        "offline": True,
    },
)

SCRIPT_TARGETS = tuple(
    {
        "kind": "script",
        "source": label,
        "target": None,
        "mode": "transliteration",
        "status": status,
        "offline": offline,
        "selector_note": note,
    }
    for label, status, offline, note in (
        (
            "Borama",
            "partial chart-label conversion; alpha testing",
            True,
            "Partial chart-label mapping; PUA output uses bundled font",
        ),
        (
            "Kaddare",
            "partial chart-label conversion; alpha testing",
            True,
            "Partial chart-label mapping; PUA output uses bundled font",
        ),
        (
            "Nobiin (Nubian)",
            "research only",
            False,
            "Modern variety; orthography/model not verified",
        ),
        (
            "Kenzi / Mattokki (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Dongolawi / Andaandi (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Midob (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Birgid (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Dilling (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Karko (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Wali (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
        (
            "Kadaru (Nubian)",
            "research only",
            False,
            "Distinct modern variety; route not verified",
        ),
    )
)


def list_capabilities(mode=None):
    """Return fresh route and discovery records, optionally filtered by mode."""
    items = (*CAPABILITIES, *SCRIPT_TARGETS)
    return [dict(item) for item in items if mode is None or item["mode"] == mode]


def get_capability(source, target, mode):
    return next(
        (
            dict(item)
            for item in CAPABILITIES
            if item["kind"] == "route"
            and (item["source"], item["target"], item["mode"]) == (source, target, mode)
        ),
        None,
    )
