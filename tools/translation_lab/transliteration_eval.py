# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seeded invariance checks against Saylacian's production converters."""

from __future__ import annotations

import hashlib
import random
import string
import time
from collections import Counter
from itertools import cycle

from saylacian.core.transliteration import OLD_NUBIAN_TO_LATIN
from saylacian.core.transliteration import SCRIPT_LATIN_TO_PUA
from saylacian.core.transliteration import SOMALI_TO_OSMANYA
from saylacian.core.transliteration import transliterate

OLD_NUBIAN_REFERENCE = {
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
    "ⳟ": "ŋ",
    "ⳡ": "ñ",
    "ⳣ": "w",
    "ⳝ": "j",
}

ROUTES = (
    ("Somali Latin", "Osmanya"),
    ("Osmanya", "Somali Latin"),
    ("Somali Latin", "Borama"),
    ("Borama", "Somali Latin"),
    ("Somali Latin", "Kaddare"),
    ("Kaddare", "Somali Latin"),
    ("Old Nubian (Coptic)", "Old Nubian scholarly Latin"),
    ("Old Nubian scholarly Latin", "Old Nubian (Coptic)"),
)


def verify_static_evidence() -> dict:
    if OLD_NUBIAN_TO_LATIN != OLD_NUBIAN_REFERENCE:
        raise AssertionError(
            "Old Nubian table differs from the static 29-letter fixture."
        )
    if len(OLD_NUBIAN_REFERENCE) != 29:
        raise AssertionError("The static Old Nubian fixture must contain 29 entries.")
    for script, mapping in SCRIPT_LATIN_TO_PUA.items():
        if not mapping or any(
            not 0xE000 <= ord(glyph) <= 0xF8FF for glyph in mapping.values()
        ):
            raise AssertionError(
                f"{script} mapping is empty or includes non-BMP PUA glyphs."
            )
        if len(set(mapping.values())) != len(mapping):
            raise AssertionError(f"{script} PUA entries collide within the chart.")
    glyph_sources = {}
    for grapheme, glyph in SOMALI_TO_OSMANYA.items():
        glyph_sources.setdefault(glyph, set()).add(grapheme)
    ambiguities = {
        frozenset(values) for values in glyph_sources.values() if len(values) > 1
    }
    expected_ambiguities = {frozenset({"ii", "y"}), frozenset({"uu", "w"})}
    if ambiguities != expected_ambiguities:
        raise AssertionError(
            "Osmanya inverse ambiguity differs from its documented pairs."
        )
    return {
        "old_nubian_entries_verified": 29,
        "borama_chart_entries": len(SCRIPT_LATIN_TO_PUA["Borama"]),
        "kaddare_chart_entries": len(SCRIPT_LATIN_TO_PUA["Kaddare"]),
        "osmanya_entries": len(SOMALI_TO_OSMANYA),
        "scope": "table integrity and chart implementation; "
        "not word-level spelling validation",
    }


def _make_input(rng: random.Random, source: str) -> str:
    if source == "Somali Latin":
        alphabet = (
            tuple(SOMALI_TO_OSMANYA)
            + tuple(string.ascii_letters)
            + tuple(" '\u2019-.,!?0123456789\n")
        )
    elif source == "Old Nubian (Coptic)":
        alphabet = tuple(OLD_NUBIAN_REFERENCE) + tuple("ⲀϢ,!? 012\n")
    elif source == "Old Nubian scholarly Latin":
        alphabet = (
            tuple(OLD_NUBIAN_REFERENCE.values())
            + tuple(string.ascii_letters)
            + tuple(" šŋñēō-.,!? 12\n")
        )
    elif source == "Osmanya":
        alphabet = tuple(SOMALI_TO_OSMANYA.values()) + tuple(" 012!?\n")
    else:
        script = source
        alphabet = tuple(SCRIPT_LATIN_TO_PUA[script].values()) + tuple(" 012!?\n")
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 30)))


def evaluate_script_cases(count: int, seed: int = 1729, progress=None) -> dict:
    if count < 0:
        raise ValueError("Case count cannot be negative.")
    evidence = verify_static_evidence()
    rng = random.Random(seed)
    routes = cycle(ROUTES)
    totals = Counter()
    failures = []
    seen = set()
    started = time.perf_counter()

    for index in range(count):
        source, target = next(routes)
        value = _make_input(rng, source)
        case_id = hashlib.sha256(
            f"{seed}\0{source}\0{target}\0{value}".encode()
        ).hexdigest()
        totals["generated_checks"] += 1
        if case_id in seen:
            totals["repeated_trials"] += 1
        else:
            seen.add(case_id)
        try:
            first = transliterate(value, source, target)
            second = transliterate(value, source, target)
            totals["executed_checks"] += 1
            if first != second:
                raise AssertionError("conversion is nondeterministic")
            if value and not first.text:
                raise AssertionError("nonempty input was silently erased")
            wrapped = transliterate("<" + value + ">", source, target)
            if not wrapped.text.startswith("<") or not wrapped.text.endswith(">"):
                raise AssertionError("outer punctuation was not preserved")
            totals["passed_checks"] += 1
        except (AssertionError, ValueError, KeyError, TypeError, IndexError) as error:
            failures.append(
                {
                    "case_id": case_id,
                    "route": f"{source} -> {target}",
                    "error_type": type(error).__name__,
                    "message": str(error)[:160],
                }
            )
            totals["failed_checks"] += 1
        totals[f"route:{source}->{target}"] += 1
        if progress and (index + 1) % 5_000 == 0:
            progress(index + 1, count)

    elapsed = time.perf_counter() - started
    return {
        **evidence,
        **dict(totals),
        "generated_checks": totals["generated_checks"],
        "unique_case_ids": len(seen),
        "seed": seed,
        "elapsed_seconds": round(elapsed, 3),
        "cases_per_second": round(count / elapsed, 1) if elapsed else None,
        "reference_scored_translations": 0,
        "human_reviewed_examples": 0,
        "failures": failures[:100],
        "failure_count": len(failures),
        "oracle": "determinism, non-erasure, outer punctuation and static "
        "table integrity; no semantic translation claim",
    }
