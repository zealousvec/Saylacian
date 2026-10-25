# SPDX-License-Identifier: AGPL-3.0-or-later
"""Experimental Somali Latin/Osmanya conversion; never semantic translation."""

import json
import unicodedata
from dataclasses import dataclass
from itertools import islice, product
from pathlib import Path

from .capabilities import get_capability

RESOURCE = json.loads(
    (Path(__file__).parent / "data/osmanya.json").read_text(encoding="utf-8")
)
SCRIPT_DATA = {
    name: json.loads(
        (Path(__file__).parent / "data/scripts" / f"{name.lower()}.json").read_text(
            encoding="utf-8"
        )
    )
    for name in ("Borama", "Kaddare")
}
SCRIPT_LATIN_TO_PUA = {
    name: {
        record["grapheme"]: chr(int("0x" + record["pua"][2:], 0))
        for record in data["records"]
    }
    for name, data in SCRIPT_DATA.items()
}
SCRIPT_PUA_TO_LATIN = {
    name: {glyph: grapheme for grapheme, glyph in mapping.items()}
    for name, mapping in SCRIPT_LATIN_TO_PUA.items()
}
SOMALI_TO_OSMANYA = RESOURCE["mapping"]
OSMANYA_TO_SOMALI = {value: key for key, value in SOMALI_TO_OSMANYA.items()}
OSMANYA_REVERSE_VARIANTS = {
    chr(0x10493): ("uu",),
    chr(0x10495): ("ii",),
}
OLD_NUBIAN_TO_LATIN = {
    "ⲁ": "a",
    "ⲃ": "b",
    "ⲅ": "g",
    "ⲇ": "d",
    "ⲉ": "e",
    "ⲍ": "z",
    "ⲏ": "ē",
    "ⲑ": "th",
    "ⲓ": "i",
    "ⲕ": "k",
    "ⲗ": "l",
    "ⲙ": "m",
    "ⲛ": "n",
    "ⲝ": "x",
    "ⲟ": "o",
    "ⲡ": "p",
    "ⲣ": "r",
    "ⲥ": "s",
    "ⲧ": "t",
    "ⲩ": "u",
    "ⲫ": "ph",
    "ⲭ": "ch",
    "ⲯ": "ps",
    "ⲱ": "ō",
    "ϣ": "sh",
    "ϥ": "f",
    "ϩ": "h",
    "ϫ": "dj",
    "ϭ": "ky",
    "ϯ": "ti",
    "ⳟ": "ng",
    "ⳡ": "ny",
    "ⳣ": "w",
    "ⳝ": "j",
}
OLD_NUBIAN_CASED_TO_LATIN = dict(OLD_NUBIAN_TO_LATIN)
for character, reading in OLD_NUBIAN_TO_LATIN.items():
    uppercase = character.upper()
    if len(uppercase) == 1 and uppercase != character:
        OLD_NUBIAN_CASED_TO_LATIN[uppercase] = reading.upper()

OLD_NUBIAN_FORWARD_VARIANTS = {"ⳣ": ("ou",)}
OLD_NUBIAN_REVERSE = {
    reading: character for character, reading in OLD_NUBIAN_TO_LATIN.items()
}
OLD_NUBIAN_REVERSE["ou"] = "ⳣ"
OLD_NUBIAN_REVERSE_VARIANTS = {
    "ou": ("ⲟⲩ",),
    "ng": ("ⲛⲅ",),
    "dj": ("ⲇⳝ",),
    "sh": ("ⲥϩ",),
    "th": ("ⲧϩ",),
    "ph": ("ⲡϩ",),
    "ps": ("ⲡⲥ",),
    "ti": ("ⲧⲓ",),
}
OLD_NUBIAN_REVERSE_TOKENS = tuple(sorted(OLD_NUBIAN_REVERSE, key=len, reverse=True))
OLD_NUBIAN_AMBIGUOUS_TOKENS = frozenset(OLD_NUBIAN_REVERSE_VARIANTS)
SOMALI_FORWARD_TOKENS = tuple(sorted(SOMALI_TO_OSMANYA, key=len, reverse=True))


@dataclass(frozen=True)
class Conversion:
    text: str
    warnings: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()


def _match_case(pattern: str, value: str) -> str:
    if pattern.isupper():
        return value.upper()
    if pattern.istitle():
        return value[:1].upper() + value[1:].lower()
    if pattern.islower():
        return value.lower()
    return value


def is_private_use_character(char: str) -> bool:
    codepoint = ord(char)
    return (
        0xE000 <= codepoint <= 0xF8FF
        or 0xF0000 <= codepoint <= 0xFFFFD
        or 0x100000 <= codepoint <= 0x10FFFD
    )


def _chart_transliterate(text: str, source: str, target: str) -> Conversion:
    warnings = [
        "Limited conversion; word spelling is unreviewed. May need Saylacian font outside this app.",
    ]
    text = unicodedata.normalize("NFC", text)
    output = []
    if source == "Somali Latin":
        mapping = SCRIPT_LATIN_TO_PUA[target]
        tokens = sorted(mapping, key=len, reverse=True)
        index = 0
        upper_seen = False
        missing = []
        while index < len(text):
            token = next(
                (
                    item
                    for item in tokens
                    if text[index : index + len(item)].casefold() == item
                ),
                None,
            )
            if token:
                upper_seen |= text[index : index + len(token)] != token
                output.append(mapping[token])
                index += len(token)
                continue
            char = text[index]
            output.append(char)
            index += 1
            if char.isalpha():
                missing.append(char)
        if upper_seen:
            warnings.append("Capitalization is not represented in the chart glyphs.")
        if missing:
            warnings.append(
                "Unmapped letters preserved: " + " ".join(dict.fromkeys(missing)) + "."
            )
        if target == "Borama":
            warnings.append(
                "The supplied chart has no Q label; q stays Latin and is flagged."
            ) if "q" in {char.casefold() for char in missing} else None
        return Conversion("".join(output), tuple(w for w in warnings if w))

    mapping = SCRIPT_PUA_TO_LATIN[source]
    for char in text:
        if char in mapping:
            output.append(mapping[char])
        else:
            output.append(char)
            if 0xE000 <= ord(char) <= 0xE1FF:
                warnings.append(
                    f"No {source} chart entry for U+{ord(char):04X}; preserved."
                )
    return Conversion("".join(output), tuple(dict.fromkeys(warnings)))


def _old_nubian_reverse_candidates(text: str, limit: int = 12) -> tuple[str, ...]:
    """Enumerate distinct letter-boundary readings of scholarly Latin input."""
    paths = [()] * (len(text) + 1)
    paths[len(text)] = ("",)
    for index in range(len(text) - 1, -1, -1):
        matches = [
            token
            for token in OLD_NUBIAN_REVERSE_TOKENS
            if text[index : index + len(token)].casefold() == token
        ]
        if not matches:
            paths[index] = (
                ()
                if text[index].isalpha()
                else tuple(text[index] + tail for tail in paths[index + 1])[:limit]
            )
            continue
        outputs = []
        for token in matches:
            source_token = text[index : index + len(token)]
            readings = tuple(
                _match_case(source_token, reading)
                for reading in (
                    OLD_NUBIAN_REVERSE[token],
                    *OLD_NUBIAN_REVERSE_VARIANTS.get(token, ()),
                )
            )
            for reading in readings:
                outputs.extend(reading + tail for tail in paths[index + len(token)])
                if len(outputs) >= limit * 2:
                    break
            if len(outputs) >= limit * 2:
                break
        paths[index] = tuple(dict.fromkeys(outputs))[:limit]

    return paths[0]


def _osmanya_reverse_candidates(text: str, limit: int = 12) -> tuple[str, ...]:
    """Return bounded readings for Osmanya glyphs shared by short and long vowels."""
    readings = tuple(
        (
            OSMANYA_TO_SOMALI.get(character, character),
            *OSMANYA_REVERSE_VARIANTS.get(character, ()),
        )
        for character in text
    )
    return tuple("".join(candidate) for candidate in islice(product(*readings), limit))


def detect_chart_script(text):
    private = [c for c in text if is_private_use_character(c)]
    if private:
        for name, mapping in SCRIPT_PUA_TO_LATIN.items():
            if all(char in mapping for char in private):
                return (
                    name,
                    f"{name} private-use chart glyphs detected; language is not inferred.",
                )


def detect_script(text):
    letters = [c for c in text if c.isalpha()]
    if letters and all(0x2C80 <= ord(c) <= 0x2CFF for c in letters):
        return "Coptic script", "Coptic script detected; language is not inferred."
    alphanumeric = [c for c in text if c.isalnum()]
    if alphanumeric and all(
        0x10480 <= ord(c) <= 0x1049D or 0x104A0 <= ord(c) <= 0x104A9
        for c in alphanumeric
    ):
        return "Osmanya", "Osmanya script detected; language is not inferred."
    return (
        None,
        "Latin or mixed script: select language; English, French and Somali cannot be inferred reliably here.",
    )


def transliterate(text: str, source: str, target: str) -> Conversion:
    if get_capability(source, target, "transliteration") is None:
        raise ValueError(
            "This pair has no validated mapping. Choose a listed offline route."
        )
    if (source == "Somali Latin" and target in SCRIPT_DATA) or (
        source in SCRIPT_DATA and target == "Somali Latin"
    ):
        return _chart_transliterate(text, source, target)
    if (source, target) == ("Old Nubian (Coptic)", "Old Nubian scholarly Latin"):
        output = []
        readings = []
        warnings = []
        preserved_marks = False
        preserved_punctuation = False
        for char in text:
            if char in OLD_NUBIAN_CASED_TO_LATIN:
                reading = OLD_NUBIAN_CASED_TO_LATIN[char]
                output.append(reading)
                readings.append(
                    (
                        reading,
                        *(
                            variant.upper() if char.isupper() else variant
                            for variant in OLD_NUBIAN_FORWARD_VARIANTS.get(
                                char.lower(), ()
                            )
                        ),
                    )
                )
            else:
                output.append(char)
                readings.append((char,))
                if char.isalpha() and 0x2C80 <= ord(char) <= 0x2CFF:
                    warnings.append(f"No verified table entry for {char}; preserved.")
                elif 0x2C80 <= ord(char) <= 0x2CFF:
                    category = unicodedata.category(char)
                    preserved_marks |= category.startswith("M")
                    preserved_punctuation |= category.startswith("P")
        if preserved_marks:
            warnings.append(
                "Combining marks are preserved; their reading and placement with Latin are not interpreted."
            )
        if preserved_punctuation:
            warnings.append("Coptic punctuation is preserved without interpretation.")
        primary = "".join(output)
        alternatives = tuple(
            candidate
            for candidate in (
                "".join(reading) for reading in islice(product(*readings), 12)
            )
            if candidate != primary
        )
        if alternatives:
            warnings.append("Other scholarly readings are available; see alternatives.")
        return Conversion(primary, tuple(warnings), alternatives)
    if (source, target) == ("Old Nubian scholarly Latin", "Old Nubian (Coptic)"):
        output = []
        index = 0
        matched_tokens = []
        while index < len(text):
            token = next(
                (
                    key
                    for key in OLD_NUBIAN_REVERSE_TOKENS
                    if text[index : index + len(key)].casefold() == key
                ),
                None,
            )
            if token:
                source_token = text[index : index + len(token)]
                output.append(_match_case(source_token, OLD_NUBIAN_REVERSE[token]))
                matched_tokens.append(token)
                index += len(token)
                continue
            output.append(text[index])
            index += 1
        primary = "".join(output)
        candidates = _old_nubian_reverse_candidates(text)
        alternatives = tuple(
            candidate for candidate in candidates if candidate != primary
        )
        warnings = []
        if any(token in OLD_NUBIAN_AMBIGUOUS_TOKENS for token in matched_tokens):
            warnings.append(
                "Latin-to-script conversion follows cited scholarly table; letter boundaries can be ambiguous."
            )
        if alternatives:
            warnings.append("Other script readings are available; see alternatives.")
        return Conversion(primary, tuple(warnings), alternatives)
    if (source, target) not in {
        ("Somali Latin", "Osmanya"),
        ("Osmanya", "Somali Latin"),
    }:
        raise ValueError("No implementation is installed for this verified route yet.")
    text = unicodedata.normalize("NFC", text)
    warnings = []
    result = []
    if source == "Somali Latin":
        if any(c.isupper() for c in text):
            warnings.append("Capitalization cannot be preserved in Osmanya.")
        index = 0
        while index < len(text):
            token = next(
                (
                    t
                    for t in SOMALI_FORWARD_TOKENS
                    if text[index : index + len(t)].lower() == t
                ),
                None,
            )
            if token:
                result.append(SOMALI_TO_OSMANYA[token])
                if token in {"ii", "uu"}:
                    warnings.append(
                        "Long-vowel ii/uu use the same Osmanya letters as y/w; reverse conversion may read them as y/w."
                    )
                index += len(token)
            else:
                char = text[index]
                result.append(char)
                index += 1
                if char.isalpha():
                    warnings.append("Unmapped input preserved: " + char)
    else:
        for char in text:
            result.append(OSMANYA_TO_SOMALI.get(char, char))
            if char in {chr(0x10493), chr(0x10495)}:
                warnings.append("Reverse ambiguity: w/uu or y/ii; output uses w and y.")
            elif char.isalpha() and char not in OSMANYA_TO_SOMALI:
                warnings.append("Unmapped input preserved: " + char)
    alternatives = ()
    if source == "Osmanya":
        primary = "".join(result)
        alternatives = tuple(
            candidate
            for candidate in _osmanya_reverse_candidates(text)
            if candidate != primary
        )
    return Conversion("".join(result), tuple(dict.fromkeys(warnings)), alternatives)


transliterate_script = transliterate
