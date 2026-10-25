# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate a pinned CTranslate2 English-to-Somali candidate against current app route.

Example:
  python tools/benchmark_somali_en_candidate.py --model-dir PATH --results BASELINE_JSON

The model directory must contain CTranslate2 files plus source.spm and target.spm.
Inference runs locally with network sockets blocked.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import socket
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests/data/somali_translation_tico19_test_150.jsonl"
sys.path.insert(0, str(ROOT))

from tools.benchmark_output import require_external_output, save_json_atomic

MODEL_REPOSITORY = "maanka2/opus-mt-en-so-finetuned"
MODEL_REVISION = "af92fdea79083bbb6c9d753bd56b117bedff4c11"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_manifest(folder: Path) -> list[dict]:
    files = []
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        files.append(
            {
                "path": path.relative_to(folder).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--system-key", default="maanka2_en_to_so")
    parser.add_argument(
        "--results",
        type=Path,
        required=True,
        help="existing baseline result JSON outside the source repository",
    )
    parser.add_argument("--model-name", default=MODEL_REPOSITORY)
    parser.add_argument("--model-revision", default=MODEL_REVISION)
    parser.add_argument("--license", default="Apache-2.0 declared by model card")
    parser.add_argument(
        "--license-note",
        default=(
            "Upstream card reports Apache-2.0; base checkpoint card reports CC-BY-4.0. "
            "Both permit commercial use with attribution; retain both notices pending maintainer confirmation."
        ),
    )
    parser.add_argument("--no-repeat-ngram-size", type=int, default=0)
    args = parser.parse_args()
    try:
        output_path = require_external_output(args.results)
    except ValueError as error:
        parser.error(str(error))
    model_dir = args.model_dir.resolve()
    for name in (
        "model.bin",
        "config.json",
        "shared_vocabulary.json",
        "source.spm",
        "target.spm",
    ):
        if not (model_dir / name).is_file():
            raise SystemExit(f"Missing CTranslate2 candidate file: {model_dir / name}")

    import ctranslate2
    import sentencepiece

    from tools.benchmark_somali_quality import diagnostic_flags, score

    samples = [
        json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines()
    ]
    prior = json.loads(output_path.read_text(encoding="utf-8"))
    baseline = prior["systems"]["baseline"]
    baseline_samples = baseline["samples"]["en_so"]
    if len(samples) != 150 or len(baseline_samples) != len(samples):
        raise SystemExit("Expected paired 150-example source and baseline data.")

    source_tokenizer = sentencepiece.SentencePieceProcessor(
        model_file=str(model_dir / "source.spm")
    )
    target_tokenizer = sentencepiece.SentencePieceProcessor(
        model_file=str(model_dir / "target.spm")
    )
    start_load = time.perf_counter()
    translator = ctranslate2.Translator(
        str(model_dir), device="cpu", compute_type="int8", intra_threads=2
    )
    startup_seconds = time.perf_counter() - start_load
    predictions = []
    latencies = []

    def no_network(*_args, **_kwargs):
        raise AssertionError("Offline candidate evaluation attempted network access")

    with patch.object(socket.socket, "connect", no_network):
        for index, sample in enumerate(samples, 1):
            source = sample["source_en"]
            pieces = source_tokenizer.encode(source, out_type=str)
            started = time.perf_counter()
            result = translator.translate_batch(
                [pieces],
                beam_size=4,
                max_input_length=0,
                max_decoding_length=512,
                no_repeat_ngram_size=args.no_repeat_ngram_size,
            )[0]
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            translated = target_tokenizer.decode(result.hypotheses[0]).strip()
            latencies.append(elapsed_ms)
            predictions.append(
                {
                    "source": source,
                    "reference": sample["reference_so"],
                    "text": translated,
                    "elapsed_ms": elapsed_ms,
                    "review_flags": diagnostic_flags(
                        translated, sample["reference_so"], "en_so"
                    ),
                }
            )
            if index % 25 == 0 or index == len(samples):
                print(f"{args.model_name}: {index}/{len(samples)} examples", flush=True)

    candidate = {
        "model": args.model_name,
        "model_revision": args.model_revision,
        "license": args.license,
        "license_note": args.license_note,
        "source_framework": "Transformers Marian checkpoint converted locally to CTranslate2 int8",
        "candidate_files": tree_manifest(model_dir),
        "software": {
            "ctranslate2": importlib.metadata.version("ctranslate2"),
            "sentencepiece": importlib.metadata.version("sentencepiece"),
            "sacrebleu": importlib.metadata.version("sacrebleu"),
        },
        "runtime": {
            "device": "CPU",
            "compute_type": "int8",
            "beam_size": 4,
            "max_decoding_length": 512,
            "no_repeat_ngram_size": args.no_repeat_ngram_size,
        },
        "network": "blocked: socket.socket.connect raises; model loaded from local files",
        "sample_count": len(samples),
        "sample_ids": [row["id"] for row in samples],
        "startup_seconds": round(startup_seconds, 3),
        "wall_seconds": round(sum(latencies) / 1000, 2),
        "metrics": {
            "en_to_so": score(
                [row["reference_so"] for row in samples],
                [row["text"] for row in predictions],
            ),
        },
        "latency_ms": {
            "median": round(sorted(latencies)[len(latencies) // 2], 1),
            "p95": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 1),
        },
        "quality_review": {
            "numeric_token_mismatch_cues": sum(
                "numeric-token mismatch" in flag
                for row in predictions
                for flag in row["review_flags"]
            ),
            "possible_negation_mismatch_cues": sum(
                "possible negation mismatch" in flag
                for row in predictions
                for flag in row["review_flags"]
            ),
            "semantic_errors_omissions_hallucinations": "not human-rated; per-example outputs retained",
        },
        "same_examples_as_current_app_route": len(samples),
        "paired_baseline_metrics": {
            "en_to_so": score(
                [row["reference_so"] for row in samples],
                [row["text"] for row in baseline_samples],
            ),
        },
        "samples": {"en_so": predictions},
    }

    prior["systems"][args.system_key] = candidate
    save_json_atomic(output_path, prior)
    metric = candidate["metrics"]["en_to_so"]
    current = candidate["paired_baseline_metrics"]["en_to_so"]
    print(f"saved {output_path} as {args.system_key}")
    print(f"candidate BLEU={metric['bleu']} chrF++={metric['chrf_plus_plus']}")
    print(f"current   BLEU={current['bleu']} chrF++={current['chrf_plus_plus']}")
    print(
        f"startup={candidate['startup_seconds']}s wall={candidate['wall_seconds']}s latency={candidate['latency_ms']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
