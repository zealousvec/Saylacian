# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare pinned English–Somali OPUS shards for controlled local research."""

from __future__ import annotations

import hashlib
import json
import random
import re
import unicodedata
from pathlib import Path

from py3langid import classify

from .prepare_data import _assign_splits
from .prepare_data import _duplicate_components

SOURCES = {
    "opus-paracrawl-en-so": {
        "revision": "8bb0bcf0c038a0cb762690b4dbce088b861423ed",
        "sha256": "f2bd66e42dfb05c0daf0e20e9dac0db0812c3f03f76643a94bcca7c5b0fccc7c",
        "bytes": 3_718_608,
        "license": "CC0-1.0",
        "source_page": "https://huggingface.co/datasets/Helsinki-NLP/opus_paracrawl",
        "attribution": "ParaCrawl project; see source page and dataset card.",
        "quality_note": (
            "Web-mined; automated filtering only; fluent review not performed."
        ),
    },
    "opus-infopankki-en-so": {
        "revision": "52339513e7ee4d1896c804ca4f61d7ee3b35ea93",
        "sha256": "3064daec6e19b82a860d725ceed1409c4d3caecebefc6d5cac2646ecb7392d04",
        "bytes": 2_317_274,
        "license": "CC-BY-4.0",
        "source_page": "https://huggingface.co/datasets/Helsinki-NLP/opus_infopankki",
        "attribution": "InfoFinland; OPUS/Helsinki-NLP; cite the OPUS corpus paper.",
        "quality_note": (
            "Public-information translations; automated filtering only; "
            "no Somali specialist review."
        ),
    },
}
MAX_CHARS = 500
URL_OR_TAG = re.compile(r"https?://|www\.|<[^>]+>", re.IGNORECASE)
MERGED_LANGUAGE_LABEL = re.compile(
    r"(?<=\w)(?:Finnish|Swedish|English)\b", re.IGNORECASE
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def _usable_pair(row: dict) -> tuple[str, str] | None:
    translations = row.get("translation")
    if not isinstance(translations, dict):
        return None
    english = translations.get("en")
    somali = translations.get("so")
    if not isinstance(english, str) or not isinstance(somali, str):
        return None
    english = " ".join(unicodedata.normalize("NFC", english).split())
    somali = " ".join(unicodedata.normalize("NFC", somali).split())
    if not english or not somali or max(len(english), len(somali)) > MAX_CHARS:
        return None
    if any(MERGED_LANGUAGE_LABEL.search(text) for text in (english, somali)):
        return None
    if URL_OR_TAG.search(english) or URL_OR_TAG.search(somali):
        return None
    if len(english) >= 50 and classify(english)[0] != "en":
        return None
    if len(somali) >= 50 and classify(somali)[0] != "so":
        return None
    english_words = len(english.split())
    somali_words = len(somali.split())
    if min(english_words, somali_words) == 0:
        return None
    if max(english_words, somali_words) / min(english_words, somali_words) > 3:
        return None
    return english, somali


def prepare_parallel_parquet(
    artifact: Path,
    workspace: Path,
    *,
    source_id: str,
    tico_test: Path,
    seed: int = 1729,
) -> dict:
    """Verify, filter, de-duplicate and group-split one pinned source shard."""
    try:
        from pyarrow import parquet
    except ImportError as error:
        raise RuntimeError(
            "Install requirements-research-parquet.txt to prepare Parquet sources."
        ) from error

    try:
        source = SOURCES[source_id]
    except KeyError as error:
        raise ValueError(
            "No Parquet preparation rule exists for this source."
        ) from error
    if (
        artifact.stat().st_size != source["bytes"]
        or _sha256(artifact) != source["sha256"]
    ):
        raise ValueError(f"{source_id} artifact does not match its pinned hash.")

    heldout = {"en": set(), "so": set()}
    for line in tico_test.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            heldout["en"].add(_normalize(item["source_en"]))
            heldout["so"].add(_normalize(item["reference_so"]))

    table = parquet.read_table(artifact)
    input_pairs = table.num_rows
    rows = []
    seen = set()
    stats = {"filtered_pairs": 0, "duplicates": 0, "heldout_overlap": 0}
    for index, row in enumerate(table.to_pylist()):
        pair = _usable_pair(row)
        if pair is None:
            stats["filtered_pairs"] += 1
            continue
        english, somali = pair
        english_key = _normalize(english)
        somali_key = _normalize(somali)
        if english_key in heldout["en"] or somali_key in heldout["so"]:
            stats["heldout_overlap"] += 1
            continue
        if (english_key, somali_key) in seen:
            stats["duplicates"] += 1
            continue
        seen.add((english_key, somali_key))
        rows.append(
            {
                "record_id": str(row.get("id", index)),
                "source_text": english,
                "target_text": somali,
                "source_id": source_id,
                "license": source["license"],
                "dataset_revision": source["revision"],
            }
        )

    if len(rows) < 100:
        raise ValueError("Fewer than 100 usable non-overlapping pairs remain.")
    groups = _duplicate_components(rows)
    random.Random(seed).shuffle(groups)
    splits = _assign_splits(groups)
    split_rows = splits
    split_sentences = {
        name: {
            _normalize(row[field])
            for row in split_rows[name]
            for field in ("source_text", "target_text")
        }
        for name in split_rows
    }
    if any(
        split_sentences[first] & split_sentences[second]
        for first, second in (
            ("train", "validation"),
            ("train", "test"),
            ("validation", "test"),
        )
    ):
        raise ValueError("A duplicate sentence leaked across prepared splits.")
    output = workspace / "data" / "prepared" / source_id / source["revision"]
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for split, rows_for_split in split_rows.items():
        path = output / f"{split}.jsonl"
        content = "".join(
            json.dumps(item, ensure_ascii=False) + "\n" for item in rows_for_split
        )
        path.write_text(content, encoding="utf-8", newline="\n")
        hashes[path.name] = _sha256(path)
    report = {
        "schema_version": 1,
        "source_id": source_id,
        "dataset_revision": source["revision"],
        "source_sha256": source["sha256"],
        "source_bytes": source["bytes"],
        "license": source["license"],
        "source_page": source["source_page"],
        "attribution": source["attribution"],
        "seed": seed,
        "input_pairs": input_pairs,
        "unique_pairs": len(rows),
        "filtered": stats,
        "duplicate_group_count": len(groups),
        "cross_split_exact_sentence_overlap": 0,
        "split_counts": {name: len(items) for name, items in split_rows.items()},
        "split_sha256": hashes,
        "quality_note": source["quality_note"],
        "filter_policy": (
            "Normalize Unicode and whitespace; remove URLs/tags, pairs longer "
            "than 500 characters, extreme length ratios, and language-ID "
            "mismatches on sides of 50 or more characters; remove merged "
            "Finnish/Swedish/English menu labels; exact-pair deduplicate; "
            "remove exact TICO test overlap; keep duplicate-linked sentences "
            "within one split. Language ID is a heuristic, not review."
        ),
        "language_identifier": "py3langid 0.4.0; only texts >=50 characters",
    }
    (output / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**report, "output_directory": str(output)}


def prepare_paracrawl(
    artifact: Path, workspace: Path, *, tico_test: Path, seed: int = 1729
) -> dict:
    """Backwards-compatible entry point for the pinned ParaCrawl shard."""
    return prepare_parallel_parquet(
        artifact,
        workspace,
        source_id="opus-paracrawl-en-so",
        tico_test=tico_test,
        seed=seed,
    )
