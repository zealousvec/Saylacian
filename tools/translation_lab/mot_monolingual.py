# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit a pinned Somali MOT archive for private back-translation research."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import tarfile
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Iterator
from pathlib import Path
from pathlib import PurePosixPath

SOURCE_ID = "mot-v1.11-somali-monolingual"
ARCHIVE_BYTES = 29_548_191
ARCHIVE_SHA256 = "4da691619afad7057cfc4a7be792ff97391050bfbe2348f2c0d8974c05c25b1a"
SOURCE_LICENSE = "CC-BY-4.0"
MIN_WORDS = 3
MAX_WORDS = 96
MIN_CLD3_PROBABILITY = 0.70
MIN_CLD3_PROPORTION = 0.50
MIN_NEAR_DUPLICATE_JACCARD = 0.90
MINHASH_PERMUTATIONS = 16
MINHASH_BAND_SIZE = 4
MINHASH_PRIME = (1 << 61) - 1
_coefficient_rng = random.Random(1729)
_MINHASH_COEFFICIENTS = tuple(
    (
        _coefficient_rng.randrange(1, MINHASH_PRIME),
        _coefficient_rng.randrange(MINHASH_PRIME),
    )
    for _ in range(MINHASH_PERMUTATIONS)
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: str) -> str:
    """Normalize whitespace and Unicode for exact overlap detection."""
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _word_shingles(value: str) -> tuple[int, ...] | None:
    words = re.findall(r"\w+", normalize_text(value))
    if len(words) < 6:
        return None
    fingerprints = {
        int.from_bytes(
            hashlib.blake2b(
                " ".join(words[index : index + 3]).encode("utf-8"), digest_size=8
            ).digest(),
            "big",
        )
        for index in range(len(words) - 2)
    }
    return tuple(sorted(fingerprints))


def _minhash_signature(shingles: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(
        min((multiplier * value + offset) % MINHASH_PRIME for value in shingles)
        for multiplier, offset in _MINHASH_COEFFICIENTS
    )


def _jaccard_at_least(
    first: tuple[int, ...], second: tuple[int, ...], threshold: float
) -> bool:
    left = right = intersection = 0
    while left < len(first) and right < len(second):
        if first[left] == second[right]:
            intersection += 1
            left += 1
            right += 1
        elif first[left] < second[right]:
            left += 1
        else:
            right += 1
    union = len(first) + len(second) - intersection
    return intersection / union >= threshold


def _band_keys(signature: tuple[int, ...]):
    for start in range(0, MINHASH_PERMUTATIONS, MINHASH_BAND_SIZE):
        yield start, signature[start : start + MINHASH_BAND_SIZE]


def _candidate_indices(index: dict, signature: tuple[int, ...]) -> set[int]:
    matches = set()
    for band_key in _band_keys(signature):
        matches.update(index.get(band_key, ()))
    return matches


def _add_to_index(index: dict, signature: tuple[int, ...], item_index: int) -> None:
    for band_key in _band_keys(signature):
        index[band_key].append(item_index)


def _filter_near_duplicates(path: Path, excluded_texts: set[str]) -> dict[str, int]:
    """Remove close lexical duplicates and overlaps using MinHash candidates."""
    excluded_shingles = []
    excluded_index = defaultdict(list)
    for value in sorted(excluded_texts):
        shingles = _word_shingles(value)
        if shingles is None:
            continue
        signature = _minhash_signature(shingles)
        _add_to_index(excluded_index, signature, len(excluded_shingles))
        excluded_shingles.append(shingles)

    retained_shingles = []
    retained_index = defaultdict(list)
    counts = {
        "near_duplicate_sentences_removed": 0,
        "near_overlap_sentences_removed": 0,
    }
    temporary = path.with_suffix(path.suffix + ".near.part")
    try:
        with (
            path.open("r", encoding="utf-8") as source,
            temporary.open("w", encoding="utf-8", newline="\n") as destination,
        ):
            for line in source:
                row = json.loads(line)
                shingles = _word_shingles(row["text"])
                if shingles is not None:
                    signature = _minhash_signature(shingles)
                    candidates = _candidate_indices(excluded_index, signature)
                    if any(
                        _jaccard_at_least(
                            shingles,
                            excluded_shingles[candidate],
                            MIN_NEAR_DUPLICATE_JACCARD,
                        )
                        for candidate in candidates
                    ):
                        counts["near_overlap_sentences_removed"] += 1
                        continue

                    candidates = _candidate_indices(retained_index, signature)
                    if any(
                        _jaccard_at_least(
                            shingles,
                            retained_shingles[candidate],
                            MIN_NEAR_DUPLICATE_JACCARD,
                        )
                        for candidate in candidates
                    ):
                        counts["near_duplicate_sentences_removed"] += 1
                        continue

                    _add_to_index(retained_index, signature, len(retained_shingles))
                    retained_shingles.append(shingles)
                destination.write(line)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return counts


def iter_sentence_strings(value: object) -> Iterator[str]:
    """Yield sentence strings from MOT's nested paragraph structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_sentence_strings(item)


def load_excluded_texts(paths: Iterable[Path]) -> tuple[set[str], dict[str, str]]:
    """Load source and target text from local JSONL files for leakage filtering."""
    excluded: set[str] = set()
    hashes: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Exclusion data file is missing: {path}")
        hashes[path.name] = sha256_file(path)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("target_text", "reference_so"):
                text = row.get(key)
                if isinstance(text, str) and text.strip():
                    excluded.add(normalize_text(text))
    return excluded, hashes


def load_tico_exclusions(archive: Path) -> set[str]:
    """Load TICO-19 development targets for corpus overlap screening.

    The final test split must remain reserved for a single final evaluation and
    is never opened by the reusable corpus preparation pipeline.
    """
    from tools.translation_lab.tico19_benchmark import load_split

    excluded = set()
    for row in load_split(archive, "dev"):
        excluded.add(normalize_text(row["target_text"]))
    return excluded


def _is_safe_member(member: tarfile.TarInfo) -> bool:
    path = PurePosixPath(member.name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not member.issym()
        and not member.islnk()
        and not member.isdev()
    )


def _document_is_verified_somali(record: dict) -> bool:
    if record.get("content_type") != "article":
        return False
    if (
        record.get("site_language") != "som"
        or record.get("predicted_language") != "som"
    ):
        return False
    somali_detection = record.get("cld3_detected_languages", {}).get("som", {})
    return (
        somali_detection.get("cld3_language") == "so"
        and somali_detection.get("is_reliable") is True
        and somali_detection.get("probability", 0) >= MIN_CLD3_PROBABILITY
        and somali_detection.get("proportion", 0) >= MIN_CLD3_PROPORTION
    )


def audit_archive(
    archive: Path,
    output: Path,
    *,
    excluded_texts: set[str] | None = None,
) -> dict:
    """Verify and screen article sentences, retaining source attribution fields."""
    if (
        archive.stat().st_size != ARCHIVE_BYTES
        or sha256_file(archive) != ARCHIVE_SHA256
    ):
        raise ValueError("MOT v1.11 Somali archive does not match its pinned bytes.")

    excluded = excluded_texts or set()
    counts = {
        "archive_members": 0,
        "article_documents": 0,
        "verified_somali_documents": 0,
        "rejected_language_documents": 0,
        "sentences_seen": 0,
        "sentences_outside_length_range": 0,
        "duplicate_sentences_removed": 0,
        "exact_overlap_sentences_removed": 0,
        "near_duplicate_sentences_removed": 0,
        "near_overlap_sentences_removed": 0,
        "sentences_retained": 0,
    }
    seen: set[str] = set()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")

    try:
        with (
            tarfile.open(archive, "r:gz") as source,
            temporary.open("w", encoding="utf-8", newline="\n") as destination,
        ):
            for member in source:
                counts["archive_members"] += 1
                if not _is_safe_member(member):
                    raise ValueError(f"Unsafe MOT archive member: {member.name}")
                path = PurePosixPath(member.name)
                if not member.isfile() or path.suffix != ".json":
                    continue
                if path.parts[:2] != ("som_voasomali", "article"):
                    continue
                if len(path.parts) != 3 or member.size > 8 * 1024 * 1024:
                    raise ValueError(f"Unexpected MOT article entry: {member.name}")

                counts["article_documents"] += 1
                stream = source.extractfile(member)
                if stream is None:
                    raise ValueError(f"MOT article cannot be read: {member.name}")
                with stream:
                    record = json.load(stream)
                if not isinstance(record, dict):
                    raise TypeError(f"MOT article is not a JSON object: {member.name}")
                if not _document_is_verified_somali(record):
                    counts["rejected_language_documents"] += 1
                    continue

                counts["verified_somali_documents"] += 1
                for sentence in iter_sentence_strings(record.get("sentences")):
                    counts["sentences_seen"] += 1
                    sentence = " ".join(sentence.split())
                    word_count = len(sentence.split())
                    if not MIN_WORDS <= word_count <= MAX_WORDS:
                        counts["sentences_outside_length_range"] += 1
                        continue

                    normalized = normalize_text(sentence)
                    if normalized in seen:
                        counts["duplicate_sentences_removed"] += 1
                        continue
                    seen.add(normalized)
                    if normalized in excluded:
                        counts["exact_overlap_sentences_removed"] += 1
                        continue

                    row = {
                        "text": sentence,
                        "source_id": SOURCE_ID,
                        "license": SOURCE_LICENSE,
                        "document_id": path.stem,
                        "title": record.get("title", ""),
                        "source_url": record.get("url", ""),
                        "published": record.get("time_published", ""),
                    }
                    destination.write(
                        json.dumps(row, ensure_ascii=False, separators=(",", ":"))
                        + "\n"
                    )
                    counts["sentences_retained"] += 1
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    counts.update(_filter_near_duplicates(output, excluded))
    counts["sentences_retained"] -= (
        counts["near_duplicate_sentences_removed"]
        + counts["near_overlap_sentences_removed"]
    )

    return {
        "source_id": SOURCE_ID,
        "source_revision": "v1.11",
        "source_license": SOURCE_LICENSE,
        "archive_sha256": ARCHIVE_SHA256,
        "archive_bytes": ARCHIVE_BYTES,
        "direct_parallel_pairs": 0,
        "purpose": "private back-translation candidate; not direct bitext",
        "minimum_cld3_probability": MIN_CLD3_PROBABILITY,
        "minimum_cld3_proportion": MIN_CLD3_PROPORTION,
        "near_duplicate_method": (
            "64-bit BLAKE2b token 3-gram MinHash with 4x4 bands; "
            f"verified Jaccard threshold {MIN_NEAR_DUPLICATE_JACCARD:.2f}; "
            "lexical only, not semantic deduplication"
        ),
        "excluded_file_sha256": {},
        "counts": counts,
        "output_sha256": sha256_file(output),
        "output_bytes": output.stat().st_size,
        "attribution": (
            "Palen-Michel, Kim, and Lignos (2022), Multilingual Open Text "
            "Release 1; VOA Somali source articles."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exclude-jsonl", type=Path, action="append", default=[])
    parser.add_argument("--tico-archive", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exclusions, exclusion_hashes = load_excluded_texts(args.exclude_jsonl)
    if args.tico_archive:
        exclusions.update(load_tico_exclusions(args.tico_archive))
    report = audit_archive(args.archive, args.output, excluded_texts=exclusions)
    report["excluded_file_sha256"] = exclusion_hashes
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
