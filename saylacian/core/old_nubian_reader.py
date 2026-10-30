# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small, source-linked tools for inspecting Old Nubian character readings."""

import hashlib
import hmac
import json
import unicodedata
from dataclasses import dataclass

from saylacian.core.transliteration import OLD_NUBIAN_AMBIGUOUS_TOKENS
from saylacian.core.transliteration import OLD_NUBIAN_LATIN_VARIANTS
from saylacian.core.transliteration import OLD_NUBIAN_TO_LATIN
from saylacian.core.transliteration import transliterate

CONVENTION = "van Gerven Oei, Old Nubian (2024), Table 1"
SOURCE_URL = "https://escholarship.org/uc/item/03x6d68h"
LEGACY_CONVENTION = "DBMNT transliteration table, page 1"
LEGACY_SOURCE_URL = "https://dbmnt.uw.edu.pl/static/pdf/transliteration_tables.pdf"
FORMAT = "saylacian-old-nubian-reading"
FORMAT_VERSION = 1
MAX_RECORD_BYTES = 128_000


@dataclass(frozen=True)
class ReadingRecord:
    original: str
    latin: str
    lines: tuple[tuple[str, str], ...]
    warnings: tuple[str, ...]
    convention: str = CONVENTION
    source_url: str = SOURCE_URL
    alternatives: tuple[str, ...] = ()


def alphabet_entries(query: str = "") -> tuple[dict[str, object], ...]:
    """Return only letters in the current cited table, searchable by glyph or name."""
    if not isinstance(query, str):
        raise TypeError("Alphabet search text must be a string.")
    needle = query.strip().casefold()
    rows = []
    for glyph, reading in OLD_NUBIAN_TO_LATIN.items():
        codepoint = f"U+{ord(glyph):04X}"
        name = unicodedata.name(glyph, "UNKNOWN CHARACTER")
        variants = OLD_NUBIAN_LATIN_VARIANTS.get(glyph, ())
        reading_label = " / ".join((reading, *variants))
        reverse_ambiguous = reading in OLD_NUBIAN_AMBIGUOUS_TOKENS or bool(variants)
        row = {
            "glyph": glyph,
            "reading": reading,
            "reading_label": reading_label,
            "codepoint": codepoint,
            "name": name,
            "convention": CONVENTION,
            "source_url": SOURCE_URL,
            "confidence": (
                "Listed in the attributed 2024 table; not independently reviewed"
            ),
            "ambiguous": reverse_ambiguous,
        }
        searchable = f"{glyph} {reading_label} {codepoint} {name}".casefold()
        if not needle or needle in searchable:
            rows.append(row)
    return tuple(rows)


def describe_combining_marks(text: str, limit: int = 6) -> str:
    """Describe preserved marks for display without assigning reading rules."""
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
    details = [
        f"U+{ord(character):04X} {unicodedata.name(character, 'UNNAMED MARK')} "
        f"(code point {index})"
        for index, character in marks[:limit]
    ]
    omitted = len(marks) - len(details)
    if omitted:
        details.append(f"and {omitted} more")
    return "Display note only; no reading rule applied. " + "; ".join(details)


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
    if envelope["format"] != FORMAT or envelope["version"] != FORMAT_VERSION:
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
        body["convention"] == LEGACY_CONVENTION
        and body["source_url"] == LEGACY_SOURCE_URL
    )
    if not legacy_record and (
        body["convention"] != CONVENTION or body["source_url"] != SOURCE_URL
    ):
        raise ValueError("Reading record uses an unrecognized convention or source.")
    if not isinstance(body["warnings"], list) or not all(
        isinstance(warning, str) for warning in body["warnings"]
    ):
        raise ValueError("Reading record warnings are invalid.")
    if legacy_record:
        warnings = tuple(body["warnings"]) + (
            (
                "Imported saved reading from the older DBMNT table; Saylacian "
                "preserved it without recalculating."
            ),
        )
        original_lines = body["original"].splitlines(keepends=True)
        latin_lines = body["latin"].splitlines(keepends=True)
        if len(original_lines) != len(latin_lines):
            raise ValueError("Legacy reading lines do not match the saved original.")
        return ReadingRecord(
            original=body["original"],
            latin=body["latin"],
            lines=tuple(zip(original_lines, latin_lines, strict=True)),
            warnings=warnings,
            convention=LEGACY_CONVENTION,
            source_url=LEGACY_SOURCE_URL,
        )
    record = make_reading_record(body["original"])
    if record.latin != body["latin"] or list(record.warnings) != body["warnings"]:
        raise ValueError("Reading record Latin text does not match its original.")
    return record
