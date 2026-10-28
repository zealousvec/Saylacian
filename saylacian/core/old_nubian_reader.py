# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small, source-linked tools for inspecting Old Nubian character readings."""

import hashlib
import hmac
import json
import unicodedata
from dataclasses import dataclass

from saylacian.core.transliteration import (
    OLD_NUBIAN_AMBIGUOUS_TOKENS,
    OLD_NUBIAN_FORWARD_VARIANTS,
    OLD_NUBIAN_TO_LATIN,
    transliterate,
)

CONVENTION = "van Gerven Oei 2024, Old Nubian alphabet, Table 1"
SOURCE_URL = "https://doi.org/10.5070/G9.3919"
LEGACY_CONVENTION = "DBMNT transliteration table, page 1"
LEGACY_SOURCE_URL = "https://dbmnt.uw.edu.pl/static/pdf/transliteration_tables.pdf"
FORMAT = "saylacian-old-nubian-reading"
FORMAT_VERSION = 2
MAX_RECORD_BYTES = 128_000
PHONETIC_VALUES = {
    "ⲁ": ("a", "aː"),
    "ⲃ": ("b", "w"),
    "ⲅ": ("g",),
    "ⲇ": ("d", "r"),
    "ⲉ": ("e", "eː"),
    "ⲍ": ("s",),
    "ⲏ": ("i", "iː"),
    "ⲑ": ("t",),
    "ⲓ": ("i", "iː"),
    "ⲕ": ("k", "g"),
    "ⲗ": ("l",),
    "ⲙ": ("m",),
    "ⲛ": ("n",),
    "ⲝ": ("(k)s",),
    "ⲟ": ("o", "oː"),
    "ⲡ": ("b",),
    "ⲣ": ("r",),
    "ⲥ": ("s",),
    "ⲧ": ("t",),
    "ⲩ": ("i", "u"),
    "ⲫ": ("b", "f"),
    "ⲭ": ("k", "g", "h"),
    "ⲯ": ("(p)s",),
    "ⲱ": ("o", "oː"),
    "ϣ": ("ʃ",),
    "ⳝ": ("ɟ",),
    "ⳟ": ("ŋ",),
    "ⳡ": ("ɲ",),
    "ⳣ": ("w",),
}


@dataclass(frozen=True)
class ReadingRecord:
    original: str
    latin: str
    lines: tuple[tuple[str, str], ...]
    warnings: tuple[str, ...]
    alternatives: tuple[str, ...] = ()
    convention: str = CONVENTION
    source_url: str = SOURCE_URL


def alphabet_entries(query: str = "") -> tuple[dict[str, object], ...]:
    """Return only letters in the current cited table, searchable by glyph or name."""
    if not isinstance(query, str):
        raise TypeError("Alphabet search text must be a string.")
    needle = query.strip().casefold()
    rows = []
    for glyph, reading in OLD_NUBIAN_TO_LATIN.items():
        codepoint = f"U+{ord(glyph):04X}"
        name = unicodedata.name(glyph, "UNKNOWN CHARACTER")
        reverse_ambiguous = reading in OLD_NUBIAN_AMBIGUOUS_TOKENS
        row = {
            "glyph": glyph,
            "reading": reading,
            "codepoint": codepoint,
            "name": name,
            "convention": CONVENTION,
            "source_url": SOURCE_URL,
            "confidence": "Listed in peer-reviewed CC BY 4.0 table; needs specialist review",
            "ambiguous": reverse_ambiguous,
            "alternative_readings": OLD_NUBIAN_FORWARD_VARIANTS.get(glyph, ()),
            "phonetic_values": PHONETIC_VALUES[glyph],
        }
        searchable = (
            f"{glyph} {reading} {' '.join(PHONETIC_VALUES[glyph])} {codepoint} {name}"
        ).casefold()
        if not needle or needle in searchable:
            rows.append(row)
    return tuple(rows)


def describe_combining_marks(text: str, limit: int = 6) -> str:
    """Describe preserved marks and the optional supralinear-stroke reading."""
    if not isinstance(text, str):
        raise TypeError("Old Nubian text must be a string.")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Mark detail limit must be a positive integer.")
    marks = [
        (index, character)
        for index, character in enumerate(text, start=1)
        if unicodedata.category(character).startswith("M")
    ]
    if not marks:
        return ""
    details = []
    for index, character in marks[:limit]:
        detail = (
            f"U+{ord(character):04X} {unicodedata.name(character, 'UNNAMED MARK')} "
            f"(code point {index})"
        )
        if character == "\u0304":
            detail += "; an i-based alternative reading is available"
        else:
            detail += "; preserved without interpretation"
        details.append(detail)
    omitted = len(marks) - len(details)
    if omitted:
        details.append(f"and {omitted} more")
    return "Combining-mark details: " + "; ".join(details)


def make_reading_record(original: str) -> ReadingRecord:
    """Create line-paired character readings without claiming a translation."""
    if not isinstance(original, str):
        raise TypeError("Old Nubian text must be a string.")
    if not original.strip():
        raise ValueError("Enter Old Nubian text to make a reading record.")
    if len(original) > 4000:
        raise ValueError("Reading records are limited to 4,000 characters.")
    converted = transliterate(
        original, "Old Nubian (Coptic)", "Old Nubian scholarly Latin"
    )
    original_lines = original.splitlines(keepends=True)
    latin_lines = converted.text.splitlines(keepends=True)
    lines = tuple(zip(original_lines, latin_lines, strict=True))
    return ReadingRecord(
        original=original,
        latin=converted.text,
        lines=lines,
        warnings=converted.warnings,
        alternatives=converted.alternatives,
    )


def export_reading_record(record: ReadingRecord) -> str:
    """Serialize a reading with a checksum for accidental-corruption detection."""
    body = {
        "format": FORMAT,
        "version": FORMAT_VERSION,
        "original": record.original,
        "latin": record.latin,
        "convention": record.convention,
        "source_url": record.source_url,
        "warnings": list(record.warnings),
    }
    canonical = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    envelope = {**body, "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
    return json.dumps(envelope, ensure_ascii=False, indent=2) + "\n"


def import_reading_record(payload: str) -> ReadingRecord:
    """Validate a versioned record and recompute its reading before accepting it."""
    if not isinstance(payload, str):
        raise TypeError("Reading record must be text.")
    try:
        payload_bytes = payload.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("Reading record contains invalid Unicode text.") from error
    if len(payload_bytes) > MAX_RECORD_BYTES:
        raise ValueError("Reading record is invalid or too large.")
    try:
        envelope = json.loads(payload)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("Reading record is not valid JSON.") from error
    required = {
        "format",
        "version",
        "original",
        "latin",
        "convention",
        "source_url",
        "warnings",
        "sha256",
    }
    if not isinstance(envelope, dict) or set(envelope) != required:
        raise ValueError("Reading record fields are not recognized.")
    if envelope["format"] != FORMAT or envelope["version"] not in {1, FORMAT_VERSION}:
        raise ValueError("Reading record format is not supported.")
    body = {key: envelope[key] for key in required - {"sha256"}}
    canonical = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if not isinstance(envelope["sha256"], str) or not hmac.compare_digest(
        checksum, envelope["sha256"]
    ):
        raise ValueError("Reading record checksum does not match.")
    if not isinstance(body["original"], str) or not isinstance(body["latin"], str):
        raise TypeError("Reading record text fields must be strings.")
    legacy_record = (
        envelope["version"] == 1
        and body["convention"] == LEGACY_CONVENTION
        and body["source_url"] == LEGACY_SOURCE_URL
    )
    current_record = (
        envelope["version"] == FORMAT_VERSION
        and body["convention"] == CONVENTION
        and body["source_url"] == SOURCE_URL
    )
    if not (legacy_record or current_record):
        raise ValueError("Reading record uses an unrecognized convention or source.")
    if not isinstance(body["warnings"], list) or not all(
        isinstance(warning, str) for warning in body["warnings"]
    ):
        raise ValueError("Reading record warnings are invalid.")
    record = make_reading_record(body["original"])
    if legacy_record:
        return ReadingRecord(
            original=record.original,
            latin=record.latin,
            lines=record.lines,
            warnings=tuple(
                dict.fromkeys(
                    (
                        *record.warnings,
                        "Reading updated to the current cited table; the earlier Latin reading was replaced.",
                    )
                )
            ),
            alternatives=record.alternatives,
            convention=record.convention,
            source_url=record.source_url,
        )
    if record.latin != body["latin"] or list(record.warnings) != body["warnings"]:
        raise ValueError("Reading record Latin text does not match its original.")
    return record
