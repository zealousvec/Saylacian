# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate synthetic EN->SO rejection heuristics on a separate TICO-19 dev split.

Install pyarrow only in the evaluation environment. Data must be the official or
CC0 mirror TICO-19 English/Somali validation Parquet file.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import socket
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.benchmark_output import (
    new_benchmark_output,
    require_external_output,
    save_json_atomic,
)

OUTPUT = new_benchmark_output("somali-repetition-dev")


def repetition_flags(source: str, output: str) -> dict[str, bool]:
    words = re.findall(r"[^\W_]+", output.casefold(), flags=re.UNICODE)
    source_words = re.findall(r"[^\W_]+", source.casefold(), flags=re.UNICODE)
    trigrams = list(zip(words, words[1:], words[2:]))
    repeated_trigram = len(trigrams) != len(set(trigrams))
    repeated_content_word = any(
        len(word) > 3 and words.count(word) >= 4 for word in set(words)
    )
    runaway_length = len(words) > len(source_words) * 2 + 10
    return {
        "repeated_trigram": repeated_trigram,
        "repeated_content_word": repeated_content_word,
        "runaway_length": runaway_length,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="result JSON path (default: unique file under local app data)",
    )
    args = parser.parse_args()
    try:
        output_path = require_external_output(args.output)
    except ValueError as error:
        parser.error(str(error))
    import pyarrow.parquet as pq

    from saylacian.core import translation
    from tools.benchmark_somali_quality import score

    rows = pq.read_table(args.parquet).to_pylist()
    rows = [
        row for row in rows if row["sourceLang"] == "en" and row["targetlang"] == "so"
    ]
    if len(rows) < args.limit:
        raise SystemExit(f"Need {args.limit} English/Somali dev pairs; got {len(rows)}")
    rows.sort(key=lambda row: row["stringID"])

    bins = {"short": [], "mid": [], "long": []}
    for row in rows:
        count = len(row["sourceString"].split())
        bins["short" if count <= 10 else "mid" if count <= 22 else "long"].append(row)
    import random

    rng = random.Random(20261024)
    selected = []
    each = args.limit // 3
    remainder = args.limit - each * 3
    for index, name in enumerate(("short", "mid", "long")):
        pool = bins[name]
        rng.shuffle(pool)
        selected.extend(pool[: each + (1 if index < remainder else 0)])
    selected.sort(key=lambda row: row["stringID"])

    old_guard = translation._synthetic_candidate_is_degenerate
    current, fallback = [], []
    started = time.perf_counter()

    def deny_network(*_args, **_kwargs):
        raise AssertionError("Offline dev evaluation attempted network access")

    with patch.object(socket.socket, "connect", deny_network):
        for index, row in enumerate(selected, 1):
            source = row["sourceString"]
            current.append(
                translation.translate_meaning(
                    source, "English", "Somali Latin", provider_override="offline"
                ).text
            )
            translation._synthetic_candidate_is_degenerate = lambda _source, _output: (
                True
            )
            fallback.append(
                translation.translate_meaning(
                    source, "English", "Somali Latin", provider_override="offline"
                ).text
            )
            translation._synthetic_candidate_is_degenerate = old_guard
            if index % 25 == 0 or index == len(selected):
                print(f"TICO-19 dev: {index}/{len(selected)} examples", flush=True)
    translation._synthetic_candidate_is_degenerate = old_guard

    refs = [row["targetString"] for row in selected]
    configurations = {
        "current": (),
        "repeated_trigram": ("repeated_trigram",),
        "repeated_content_word": ("repeated_content_word",),
        "runaway_length": ("runaway_length",),
        "word_or_length": ("repeated_content_word", "runaway_length"),
        "all_three": ("repeated_trigram", "repeated_content_word", "runaway_length"),
    }
    results = {}
    for name, triggers in configurations.items():
        used_fallback = 0
        predictions = []
        for row, candidate, rescue in zip(selected, current, fallback):
            flags = repetition_flags(row["sourceString"], candidate)
            use_rescue = any(flags[trigger] for trigger in triggers)
            used_fallback += int(use_rescue)
            predictions.append(rescue if use_rescue else candidate)
        results[name] = {
            "fallback_count": used_fallback,
            "metrics": score(refs, predictions),
            "repetition_cues": {
                cue: sum(
                    repetition_flags(row["sourceString"], candidate)[cue]
                    for row, candidate in zip(selected, current)
                )
                for cue in (
                    "repeated_trigram",
                    "repeated_content_word",
                    "runaway_length",
                )
            },
        }

    result = {
        "dataset": "TICO-19 dev / validation, separate from held-out test sample",
        "dataset_source": "gmnlp/tico19 CC0 mirror of TICO-19; en-so validation Parquet",
        "data_sha256": hashlib.sha256(args.parquet.read_bytes()).hexdigest(),
        "population_rows": len(rows),
        "sample_count": len(selected),
        "sample_ids": [row["stringID"] for row in selected],
        "runtime_seconds": round(time.perf_counter() - started, 2),
        "network": "blocked during inference",
        "candidate_route": "Saylacian synthetic EN->SO, then current multilingual OPUS fallback",
        "results": results,
        "samples": [
            {
                "id": row["stringID"],
                "source": row["sourceString"],
                "reference": row["targetString"],
                "current": candidate,
                "fallback": rescue,
                "flags": repetition_flags(row["sourceString"], candidate),
            }
            for row, candidate, rescue in zip(selected, current, fallback)
        ],
        "review_limit": "Automatic metrics and repetition cues only; no fluent-speaker semantic rating.",
    }
    save_json_atomic(output_path, result)
    for name, stats in results.items():
        metric = stats["metrics"]
        print(
            name,
            "fallbacks",
            stats["fallback_count"],
            "BLEU",
            metric["bleu"],
            "chrF++",
            metric["chrf_plus_plus"],
        )
    print("saved", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
