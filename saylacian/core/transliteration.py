# SPDX-License-Identifier: AGPL-3.0-or-later
"""Character-based Somali Latin/Osmanya conversion; never semantic translation."""

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
SCRIPT_LATIN_ALIASES = {
    name: {alias["grapheme"]: alias["canonical"] for alias in data.get("aliases", ())}
    for name, data in SCRIPT_DATA.items()
}
SCRIPT_LATIN_TO_PUA = {
    name: {
        record["grapheme"]: chr(int("0x" + record["pua"][2:], 0))
        for record in data["records"]
    }
    for name, data in SCRIPT_DATA.items()
}
# The first Kaddare chart slots remain readable for text created before case
# forms were added. New Latin-to-Kaddare output uses the chart's cursive forms.
for record in SCRIPT_DATA["Kaddare"]["records"]:
    if "lowercase_pua" in record:
        SCRIPT_LATIN_TO_PUA["Kaddare"][record["grapheme"]] = chr(
            int("0x" + record["lowercase_pua"][2:], 0)
        )
SCRIPT_PUA_TO_LATIN = {
    name: {glyph: grapheme for grapheme, glyph in mapping.items()}
    for name, mapping in SCRIPT_LATIN_TO_PUA.items()
}
SCRIPT_KADDARE_UPPERCASE_TO_PUA = {}
# Preserve legacy Kaddare glyphs as lowercase readings and add the chart's
# separately encoded uppercase forms.
for record in SCRIPT_DATA["Kaddare"]["records"]:
    grapheme = record["grapheme"]
    legacy = chr(int("0x" + record["pua"][2:], 0))
    SCRIPT_PUA_TO_LATIN["Kaddare"][legacy] = grapheme
    if "uppercase_pua" in record:
        uppercase = chr(int("0x" + record["uppercase_pua"][2:], 0))
        SCRIPT_PUA_TO_LATIN["Kaddare"][uppercase] = grapheme.upper()
        SCRIPT_KADDARE_UPPERCASE_TO_PUA[grapheme] = uppercase
SCRIPT_PUA_REVERSE_VARIANTS = {}
for script, aliases in SCRIPT_LATIN_ALIASES.items():
    variants = {}
    for alias, canonical in aliases.items():
        glyph = SCRIPT_LATIN_TO_PUA[script][canonical]
        variants.setdefault(glyph, []).append(alias)
    SCRIPT_PUA_REVERSE_VARIANTS[script] = {
        glyph: tuple(readings) for glyph, readings in variants.items()
    }
SOMALI_TO_OSMANYA = RESOURCE["mapping"]
OSMANYA_TO_SOMALI = {value: key for key, value in SOMALI_TO_OSMANYA.items()}
OSMANYA_DIGITS_TO_LATIN = {
    chr(int(codepoint.removeprefix("U+"), 16)): digit
    for digit, codepoint in RESOURCE["digits"].items()
}
LATIN_DIGITS_TO_OSMANYA = {
    digit: glyph for glyph, digit in OSMANYA_DIGITS_TO_LATIN.items()
}
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
    "ⲭ": "kh",
    "ⲯ": "ps",
    "ⲱ": "ō",
    "ϣ": "š",
    "ⳝ": "j",
    "ⳟ": "ŋ",
    "ⳡ": "ñ",
    "ⳣ": "w",
}
OLD_NUBIAN_CASED_TO_LATIN = dict(OLD_NUBIAN_TO_LATIN)
for character, reading in OLD_NUBIAN_TO_LATIN.items():
    uppercase = character.upper()
    if len(uppercase) == 1 and uppercase != character:
        OLD_NUBIAN_CASED_TO_LATIN[uppercase] = reading.upper()

OLD_NUBIAN_FORWARD_VARIANTS = {
    "ⲏ": ("i", "iː"),
    "ⲩ": ("i",),
}
OLD_NUBIAN_FORWARD_DIGRAPHS = {
    "ⲉⲓ": ("i", "iː", "j"),
    "ⲟⲩ": ("u", "uː", "w", "wu"),
}
OLD_NUBIAN_SUPRALINEAR_STROKE = "\u0304"
OLD_NUBIAN_STROKE_I_CONSONANTS = frozenset("ⲗⲛⲣⳝ")
OLD_NUBIAN_STROKE_VOWELS = frozenset("ⲁⲉⲏⲓⲟⲩⲱ")
OLD_NUBIAN_REVERSE = {
    reading: character for character, reading in OLD_NUBIAN_TO_LATIN.items()
}
OLD_NUBIAN_REVERSE["ou"] = "ⲟⲩ"
OLD_NUBIAN_REVERSE_VARIANTS = {
    "ou": ("ⳣ",),
    "ps": ("ⲡⲥ",),
}
OLD_NUBIAN_REVERSE_TOKENS = tuple(sorted(OLD_NUBIAN_REVERSE, key=len, reverse=True))
OLD_NUBIAN_AMBIGUOUS_TOKENS = frozenset(OLD_NUBIAN_REVERSE_VARIANTS)
SOMALI_FORWARD_TOKENS = tuple(sorted(SOMALI_TO_OSMANYA, key=len, reverse=True))
KADDARE_MACRON_VOWELS = {
    "ā": "a",
    "ē": "e",
    "ī": "i",
    "ō": "o",
    "ū": "u",
}
SOMALI_MACRON_TO_LONG_VOWEL = {
    "ā": "aa",
    "ē": "ee",
    "ī": "ii",
    "ō": "oo",
    "ū": "uu",
}


def _old_nubian_stroke_i_target(text: str, mark_position: int) -> int | None:
    if (
        not 0 <= mark_position < len(text)
        or text[mark_position] != OLD_NUBIAN_SUPRALINEAR_STROKE
    ):
        return None
    base_position = mark_position - 1
    if base_position < 0 or unicodedata.category(text[base_position]).startswith("M"):
        return None
    base = text[base_position].casefold()
    if base in OLD_NUBIAN_STROKE_I_CONSONANTS:
        return base_position
    if base in OLD_NUBIAN_STROKE_VOWELS:
        prior_position = base_position - 1
        if (
            prior_position >= 0
            and not unicodedata.category(text[prior_position]).startswith("M")
            and text[prior_position].casefold() in OLD_NUBIAN_STROKE_I_CONSONANTS
        ):
            return prior_position
    return None


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
        aliases = SCRIPT_LATIN_ALIASES[target]
        tokens = sorted((*mapping, *aliases), key=len, reverse=True)
        ambiguous_tokens = set(aliases) | set(aliases.values())
        index = 0
        upper_seen = False
        kaddare_grapheme_case_loss = False
        kaddare_lowercase_used = False
        ambiguous_vowel_seen = False
        missing = []
        missing_seen = set()
        while index < len(text):
            if target == "Borama":
                long_vowel = SOMALI_MACRON_TO_LONG_VOWEL.get(text[index].casefold())
                if long_vowel:
                    upper_seen |= text[index].isupper()
                    canonical = aliases.get(long_vowel, long_vowel)
                    output.append(mapping[canonical])
                    ambiguous_vowel_seen |= long_vowel in ambiguous_tokens
                    index += 1
                    continue
            if target == "Kaddare" and text[index].casefold() in KADDARE_MACRON_VOWELS:
                matched = text[index]
                canonical = KADDARE_MACRON_VOWELS[matched.casefold()]
                glyph = mapping[canonical]
                if matched.isupper():
                    glyph = SCRIPT_KADDARE_UPPERCASE_TO_PUA[canonical]
                else:
                    kaddare_lowercase_used = True
                output.extend((glyph, glyph))
                index += 1
                continue
            token = next(
                (
                    item
                    for item in tokens
                    if text[index : index + len(item)].casefold() == item
                ),
                None,
            )
            if token:
                matched = text[index : index + len(token)]
                upper_seen |= matched != token
                if target == "Kaddare" and len(token) > 1:
                    kaddare_grapheme_case_loss |= not (
                        matched.islower() or matched.isupper()
                    )
                canonical = aliases.get(token, token)
                glyph = mapping[canonical]
                if target == "Kaddare":
                    if matched.isupper() or matched.istitle():
                        glyph = SCRIPT_KADDARE_UPPERCASE_TO_PUA[canonical]
                    else:
                        kaddare_lowercase_used = True
                output.append(glyph)
                ambiguous_vowel_seen |= token in ambiguous_tokens
                index += len(token)
                continue
            char = text[index]
            output.append(char)
            index += 1
            if char.isalpha() and char not in missing_seen:
                missing_seen.add(char)
                missing.append(char)
        if upper_seen and target != "Kaddare":
            warnings.append("Capitalization is not represented in the chart glyphs.")
        if kaddare_grapheme_case_loss:
            warnings.append(
                "Kaddare chart forms cannot preserve titlecase or mixed case inside a multi-letter grapheme."
            )
        if kaddare_lowercase_used:
            warnings.append(
                "Saylacian shows Kaddare lowercase forms separately; it does not join cursive writing."
            )
        if ambiguous_vowel_seen:
            warnings.append(
                "Borama shares chart signs for a/aa, e/ee and short o/u; those vowel distinctions cannot be recovered."
            )
        if missing:
            warnings.append(
                "Unmapped letters preserved: " + " ".join(dict.fromkeys(missing)) + "."
            )
        return Conversion("".join(output), tuple(w for w in warnings if w))

    mapping = SCRIPT_PUA_TO_LATIN[source]
    unknown_glyphs = set()
    readings = []
    ambiguous_vowel_seen = False
    for char in text:
        if char in mapping:
            reading = mapping[char]
            output.append(reading)
            variants = SCRIPT_PUA_REVERSE_VARIANTS[source].get(char, ())
            readings.append((reading, *variants))
            ambiguous_vowel_seen |= bool(variants)
        else:
            output.append(char)
            readings.append((char,))
            if is_private_use_character(char) and char not in unknown_glyphs:
                unknown_glyphs.add(char)
                warnings.append(
                    f"No {source} chart entry for U+{ord(char):04X}; preserved."
                )
    alternatives = ()
    if ambiguous_vowel_seen:
        candidates, alternatives_truncated = _bounded_reading_candidates(readings)
        primary = "".join(output)
        alternatives = tuple(
            candidate for candidate in candidates if candidate != primary
        )
        warnings.append(
            f"{source} has shared vowel signs; the main reading uses chart labels and alternatives show other readings."
        )
        if alternatives_truncated:
            warnings.append(
                "Only some alternative readings are shown; other combinations may exist."
            )
    return Conversion("".join(output), tuple(dict.fromkeys(warnings)), alternatives)


def _old_nubian_reverse_candidates(
    text: str, limit: int = 12
) -> tuple[tuple[str, ...], bool]:
    """Return table-listed alternatives while leaving unmatched text unchanged."""
    readings = []
    index = 0
    while index < len(text):
        token = next(
            (
                item
                for item in OLD_NUBIAN_REVERSE_TOKENS
                if text[index : index + len(item)].casefold() == item
            ),
            None,
        )
        if token is None:
            readings.append((text[index],))
            index += 1
            continue
        source_token = text[index : index + len(token)]
        readings.append(
            tuple(
                _match_case(source_token, reading)
                for reading in (
                    OLD_NUBIAN_REVERSE[token],
                    *OLD_NUBIAN_REVERSE_VARIANTS.get(token, ()),
                )
            )
        )
        index += len(token)
    return _bounded_reading_candidates(readings, limit)


def _osmanya_reverse_candidates(
    text: str, limit: int = 12
) -> tuple[tuple[str, ...], bool]:
    """Return local-first bounded readings for ambiguous Osmanya glyphs."""
    readings = tuple(
        (
            OSMANYA_TO_SOMALI.get(
                character, OSMANYA_DIGITS_TO_LATIN.get(character, character)
            ),
            *OSMANYA_REVERSE_VARIANTS.get(character, ()),
        )
        for character in text
    )
    return _bounded_reading_candidates(list(readings), max(limit - 1, 0))


def _bounded_reading_candidates(
    readings: list[tuple[str, ...]], limit: int = 12
) -> tuple[tuple[str, ...], bool]:
    """Prioritize each local reading before combinations of ambiguous tokens."""
    primary_parts = [choices[0] for choices in readings]
    candidates = ["".join(primary_parts)]
    seen = set(candidates)

    for index, choices in enumerate(readings):
        for choice in choices[1:]:
            candidate = "".join(
                choice if position == index else part
                for position, part in enumerate(primary_parts)
            )
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
                if len(candidates) > limit:
                    return tuple(candidates[: limit + 1]), True

    for combination in islice(product(*readings), limit * 2 + 1):
        candidate = "".join(combination)
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)
            if len(candidates) > limit:
                return tuple(candidates[: limit + 1]), True

    return tuple(candidates), False


def detect_chart_script(text):
    private = [c for c in text if is_private_use_character(c)]
    if private:
        for name, mapping in SCRIPT_PUA_TO_LATIN.items():
            if all(char in mapping for char in private):
                return (
                    name,
                    f"{name} private-use chart glyphs detected; language is not inferred.",
                )


def _is_coptic_character(character):
    codepoint = ord(character)
    return 0x03E2 <= codepoint <= 0x03EF or 0x2C80 <= codepoint <= 0x2CFF


OLD_NUBIAN_DISTINCTIVE_LETTERS = frozenset(
    character for letter in "ⳝⳟⳡⳣ" for character in (letter, letter.upper())
)


def detect_script(text):
    letters = [c for c in text if c.isalpha()]
    if letters and all(_is_coptic_character(c) for c in letters):
        if any(character in OLD_NUBIAN_DISTINCTIVE_LETTERS for character in letters):
            return (
                "Old Nubian (Coptic)",
                "Old Nubian-specific letters detected; language is not inferred.",
            )
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
        supralinear_stroke_seen = False
        digraph_reading_seen = False
        previous_source_char = None
        index = 0
        while index < len(text):
            pair = text[index : index + 2]
            can_read_digraph = (
                pair.casefold() in OLD_NUBIAN_FORWARD_DIGRAPHS
                and previous_source_char != OLD_NUBIAN_SUPRALINEAR_STROKE
                and (
                    index + 2 == len(text)
                    or text[index + 2] != OLD_NUBIAN_SUPRALINEAR_STROKE
                )
            )
            if can_read_digraph:
                first, second = pair
                primary_reading = (
                    OLD_NUBIAN_CASED_TO_LATIN[first] + OLD_NUBIAN_CASED_TO_LATIN[second]
                )
                alternatives = tuple(
                    _match_case(pair, reading)
                    for reading in OLD_NUBIAN_FORWARD_DIGRAPHS[pair.casefold()]
                )
                output.append(primary_reading)
                readings.append((primary_reading, *alternatives))
                previous_source_char = second
                digraph_reading_seen = True
                index += 2
                continue

            char = text[index]
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
            elif (
                char == OLD_NUBIAN_SUPRALINEAR_STROKE
                and readings
                and previous_source_char in OLD_NUBIAN_CASED_TO_LATIN
            ):
                output.append(char)
                base_position = index - 1 if index > 0 else None
                i_target = _old_nubian_stroke_i_target(text, index)
                if i_target is not None and i_target == base_position:
                    previous_readings = readings[-1]
                    readings[-1] = (
                        *(reading + char for reading in previous_readings),
                        *(
                            ("I" if text[i_target].isupper() else "i") + reading
                            for reading in previous_readings
                        ),
                    )
                else:
                    readings[-1] = tuple(reading + char for reading in readings[-1])
                    if i_target is not None and len(readings) >= 2:
                        target_readings = readings[-2]
                        readings[-2] = (
                            *target_readings,
                            *(
                                ("I" if text[i_target].isupper() else "i") + reading
                                for reading in target_readings
                            ),
                        )
                supralinear_stroke_seen = True
            else:
                output.append(char)
                readings.append((char,))
                preserved_marks |= unicodedata.category(char).startswith("M")
                if char.isalpha() and _is_coptic_character(char):
                    warnings.append(f"No verified table entry for {char}; preserved.")
                elif 0x2C80 <= ord(char) <= 0x2CFF:
                    category = unicodedata.category(char)
                    preserved_punctuation |= category.startswith("P")
            previous_source_char = char
            index += 1
        if preserved_marks:
            warnings.append(
                "Other combining marks are preserved; their reading and placement with Latin are not interpreted."
            )
        if preserved_punctuation:
            warnings.append("Coptic punctuation is preserved without interpretation.")
        if supralinear_stroke_seen:
            warnings.append(
                "Supralinear-stroke i readings depend on context; the mark may "
                "also mark a numeral, which Saylacian does not convert. "
                "See supported alternatives."
            )
        if digraph_reading_seen:
            warnings.append(
                "Old Nubian digraphs have multiple published phonetic readings; see alternatives."
            )
        primary = "".join(output)
        candidates, alternatives_truncated = _bounded_reading_candidates(readings)
        alternatives = tuple(
            candidate for candidate in candidates if candidate != primary
        )[:12]
        if alternatives_truncated:
            warnings.append(
                "Only some alternative readings are shown; other combinations may exist."
            )
        if alternatives:
            warnings.append("Other scholarly readings are available; see alternatives.")
        return Conversion(primary, tuple(warnings), alternatives)
    if (source, target) == ("Old Nubian scholarly Latin", "Old Nubian (Coptic)"):
        text = unicodedata.normalize("NFC", text)
        output = []
        index = 0
        matched_tokens = []
        unmapped_letters = []
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
            if text[index].isalpha() and "LATIN" in unicodedata.name(text[index], ""):
                unmapped_letters.append(text[index])
            index += 1
        primary = "".join(output)
        candidates, alternatives_truncated = _old_nubian_reverse_candidates(text)
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
        if alternatives_truncated:
            warnings.append(
                "Only some alternative readings are shown; other combinations may exist."
            )
        if unmapped_letters:
            letters = " ".join(dict.fromkeys(unmapped_letters))
            warnings.append(f"Unmapped Latin letters preserved: {letters}.")
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
        macron_vowel_seen = False
        index = 0
        while index < len(text):
            macron_vowel = SOMALI_MACRON_TO_LONG_VOWEL.get(text[index].casefold())
            if macron_vowel:
                result.append(SOMALI_TO_OSMANYA[macron_vowel])
                macron_vowel_seen = True
                if macron_vowel in {"ii", "uu"}:
                    warnings.append(
                        "Long-vowel ii/uu use the same Osmanya letters as y/w; reverse conversion may read them as y/w."
                    )
                index += 1
                continue
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
                result.append(LATIN_DIGITS_TO_OSMANYA.get(char, char))
                index += 1
                if char.isalpha():
                    warnings.append("Unmapped input preserved: " + char)
        if macron_vowel_seen:
            warnings.append(
                "Macron vowels use Osmanya long-vowel letters and read back as doubled Latin vowels."
            )
    else:
        for char in text:
            result.append(
                OSMANYA_TO_SOMALI.get(char, OSMANYA_DIGITS_TO_LATIN.get(char, char))
            )
            if char in {chr(0x10493), chr(0x10495)}:
                warnings.append("Reverse ambiguity: w/uu or y/ii; output uses w and y.")
            elif char.isalpha() and char not in OSMANYA_TO_SOMALI:
                warnings.append("Unmapped input preserved: " + char)
    alternatives = ()
    if source == "Osmanya":
        primary = "".join(result)
        candidates, alternatives_truncated = _osmanya_reverse_candidates(text)
        alternatives = tuple(
            candidate for candidate in candidates if candidate != primary
        )
        if alternatives_truncated:
            warnings.append(
                "Only some alternative readings are shown; other combinations may exist."
            )
    return Conversion("".join(result), tuple(dict.fromkeys(warnings)), alternatives)


transliterate_script = transliterate
