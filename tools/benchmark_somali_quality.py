# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare Saylacian Somali routes on a pinned, local TICO-19 sample.

The data and predictions are local. Candidate inference uses CPU-only llama.cpp.
Run once per system so peak memory and cold-start time stay interpretable:

  python tools/benchmark_somali_quality.py --system baseline
  python tools/benchmark_somali_quality.py --system afrislm --candidate-model PATH
  python tools/benchmark_somali_en_candidate.py --model-dir PATH
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.metadata
import json
import os
import socket
import sys
import time
from ctypes import wintypes
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests/data/somali_translation_tico19_test_150.jsonl"
OUTPUT = ROOT / "docs/somali_translation_quality_results.json"
CHECKPOINT = (
    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    / "Saylacian"
    / "benchmark"
    / "somali_translation_quality_checkpoint.json"
)
sys.path.insert(0, str(ROOT))


def deny_network(*_args, **_kwargs):
    raise AssertionError("Offline Somali benchmark attempted a network connection")


def peak_working_set_bytes():
    if os.name != "nt":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize",
                "WorkingSetSize",
                "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage",
                "PagefileUsage",
                "PeakPagefileUsage",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    get_info = psapi.GetProcessMemoryInfo
    get_info.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
    get_info.restype = wintypes.BOOL
    if not get_info(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return None
    return int(counters.PeakWorkingSetSize)


def clean_qvac_output(text: str) -> str:
    """Remove only Qwen's visible reasoning boundary; preserve translation text."""
    text = text.strip()
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[-1]
    return text.strip()


def get_qvac_translation(llm, text: str, source: str, target: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                f"You are a professional {source} to {target} translator. "
                f"Your goal is to accurately convey the meaning and nuances of the "
                f"original {source} text while adhering to {target} grammar, vocabulary, "
                f"and cultural sensitivities. Produce only the {target} translation, "
                "without any additional explanations or commentary."
            ),
        },
        {
            "role": "user",
            "content": f"Please translate the following {source} text into {target}: {text}\n\nTranslation:",
        },
    ]
    result = llm.create_chat_completion(
        messages=messages,
        max_tokens=160,
        temperature=0,
        top_p=1,
    )
    return clean_qvac_output(result["choices"][0]["message"]["content"])


def model_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_checkpoint(
    system: str, data_hash: str, model_hash: str | None = None, limit: int = 150
) -> dict:
    if not CHECKPOINT.is_file():
        return {"samples": {"en_so": [], "so_en": []}, "wall_seconds": 0.0}
    saved = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    if saved.get("system") != system or saved.get("data_sha256") != data_hash:
        return {"samples": {"en_so": [], "so_en": []}, "wall_seconds": 0.0}
    if saved.get("model_sha256") != model_hash:
        return {"samples": {"en_so": [], "so_en": []}, "wall_seconds": 0.0}
    if saved.get("limit") != limit:
        return {"samples": {"en_so": [], "so_en": []}, "wall_seconds": 0.0}
    return saved


def save_checkpoint(
    system: str,
    data_hash: str,
    model_hash: str | None,
    outputs: dict,
    wall_seconds: float,
    completed: int,
    limit: int,
    startup_seconds: float | None = None,
) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    temporary = CHECKPOINT.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "system": system,
                "data_sha256": data_hash,
                "model_sha256": model_hash,
                "limit": limit,
                "completed_pairs": completed,
                "wall_seconds": round(wall_seconds, 2),
                "startup_seconds": round(startup_seconds, 2)
                if startup_seconds is not None
                else None,
                "samples": outputs,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    temporary.replace(CHECKPOINT)


def diagnostic_flags(prediction: str, reference: str, direction: str) -> list[str]:
    """Raise review cues only; automated token checks do not judge meaning."""
    import re

    flags = []
    if re.findall(r"\d+(?:[.,]\d+)*", prediction) != re.findall(
        r"\d+(?:[.,]\d+)*", reference
    ):
        flags.append("numeric-token mismatch; review number preservation")
    if direction == "en_so":
        negations = {
            "ma",
            "maya",
            "marnaba",
            "aan",
            "lama",
            "no",
            "not",
            "never",
            "without",
        }
    else:
        negations = {"no", "not", "never", "without", "neither", "nor"}
    tokenize = lambda value: set(
        re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)
    )
    if bool(tokenize(prediction) & negations) != bool(tokenize(reference) & negations):
        flags.append("possible negation mismatch; fluent reviewer required")
    return flags


def model_runtime_metadata(system: str, model_path: Path | None = None) -> dict:
    if system == "baseline":
        source_manifest = json.loads(
            (ROOT / "saylacian/core/data/somali_model_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        return {
            "software": {
                name: importlib.metadata.version(name)
                for name in ("ctranslate2", "sentencepiece", "sacrebleu")
            },
            "models": [
                {
                    "pair": item["pair"],
                    "repository": item["repository"],
                    "revision": item["revision"],
                    "license": item["license"],
                    "files": item["files"],
                }
                for item in source_manifest
            ],
            "experimental_en_to_so_candidate": json.loads(
                (ROOT / "saylacian/core/data/model_manifest.json").read_text(
                    encoding="utf-8"
                )
            )[2],
        }
    return {
        "software": {
            "llama-cpp-python": importlib.metadata.version("llama-cpp-python"),
            "sacrebleu": importlib.metadata.version("sacrebleu"),
        },
        "candidate_model": {
            "repository": "qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF",
            "revision": "14d6fd1e24c9f94a5e40c2e91c066241aede0dce",
            "license": "Apache-2.0 declared by model card; synthetic training mix is CC-BY-NC-4.0; distribution rights need review",
            "file": model_path.name,
            "bytes": model_path.stat().st_size,
            "sha256": model_file_sha256(model_path),
        },
    }


def score(references: list[str], predictions: list[str]) -> dict:
    from sacrebleu.metrics import BLEU, CHRF

    bleu = BLEU()
    chrf = CHRF(word_order=2)
    bleu_score = bleu.corpus_score(predictions, [references])
    chrf_score = chrf.corpus_score(predictions, [references])
    return {
        "sentence_count": len(references),
        "sacrebleu": str(bleu.get_signature()),
        "bleu": round(bleu_score.score, 3),
        "chrf_plus_plus": round(chrf_score.score, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", choices=("baseline", "afrislm"), required=True)
    parser.add_argument("--candidate-model", type=Path)
    parser.add_argument(
        "--limit",
        type=int,
        default=150,
        help="number of test pairs; subset is selected deterministically",
    )
    args = parser.parse_args()
    if not DATA.is_file():
        raise SystemExit(f"Missing benchmark data: {DATA}")
    all_samples = [
        json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines()
    ]
    if len(all_samples) != 150:
        raise SystemExit(f"Expected 150 pinned samples, found {len(all_samples)}")
    if not 1 <= args.limit <= len(all_samples):
        raise SystemExit("--limit must be between 1 and the benchmark size (150)")
    if args.limit == len(all_samples):
        samples = all_samples
    else:
        samples = sorted(
            all_samples,
            key=lambda row: hashlib.sha256(f"20261023:{row['id']}".encode()).digest(),
        )[: args.limit]

    if args.system == "baseline":
        from saylacian.core.translation import translate_meaning

        data_hash = hashlib.sha256(DATA.read_bytes()).hexdigest()
        checkpoint = load_checkpoint("baseline", data_hash, limit=args.limit)
        outputs = checkpoint["samples"]
        completed = min(len(outputs["en_so"]), len(outputs["so_en"]))
        outputs["en_so"] = outputs["en_so"][:completed]
        outputs["so_en"] = outputs["so_en"][:completed]
        durations = {
            key: [item["elapsed_ms"] for item in outputs[key]]
            for key in ("en_so", "so_en")
        }
        started = time.perf_counter()
        initial_rss = peak_working_set_bytes()
        with patch.object(socket.socket, "connect", deny_network):
            for i, row in enumerate(samples[completed:], completed + 1):
                for key, text, source, target in (
                    ("en_so", row["source_en"], "English", "Somali Latin"),
                    ("so_en", row["reference_so"], "Somali Latin", "English"),
                ):
                    tick = time.perf_counter()

                    conversion = translate_meaning(
                        text, source, target, provider_override="offline"
                    )
                    durations[key].append((time.perf_counter() - tick) * 1000)
                    reference = (
                        row["reference_so"] if key == "en_so" else row["source_en"]
                    )
                    outputs[key].append(
                        {
                            "source": text,
                            "reference": reference,
                            "text": conversion.text,
                            "warnings": list(conversion.warnings),
                            "elapsed_ms": round(durations[key][-1], 1),
                            "review_flags": diagnostic_flags(
                                conversion.text, reference, key
                            ),
                        }
                    )
                if i % 10 == 0 or i == len(samples):
                    wall = checkpoint["wall_seconds"] + time.perf_counter() - started
                    save_checkpoint(
                        "baseline", data_hash, None, outputs, wall, i, args.limit
                    )
                    print(f"baseline: {i}/{len(samples)} pairs", flush=True)
        system = {
            "model": "current Saylacian route (synthetic Helsinki EN→SO first; multilingual OPUS fallback)",
            **model_runtime_metadata("baseline"),
            "network": "blocked: socket.socket.connect raises",
            "sample_count": len(samples),
            "sample_ids": [row["id"] for row in samples],
            "wall_seconds": round(
                checkpoint["wall_seconds"] + time.perf_counter() - started, 2
            ),
            "initial_working_set_bytes": initial_rss,
            "peak_working_set_bytes": peak_working_set_bytes(),
            "metrics": {
                "en_to_so": score(
                    [r["reference_so"] for r in samples],
                    [r["text"] for r in outputs["en_so"]],
                ),
                "so_to_en": score(
                    [r["source_en"] for r in samples],
                    [r["text"] for r in outputs["so_en"]],
                ),
            },
            "latency_ms": {
                key: {
                    "median": round(sorted(values)[len(values) // 2], 1),
                    "p95": round(sorted(values)[int(len(values) * 0.95) - 1], 1),
                }
                for key, values in durations.items()
            },
            "samples": outputs,
            "quality_review": {
                key: {
                    "numeric_token_mismatch_cues": sum(
                        "numeric-token mismatch" in flag
                        for sample in outputs[key]
                        for flag in sample.get("review_flags", [])
                    ),
                    "possible_negation_mismatch_cues": sum(
                        "possible negation mismatch" in flag
                        for sample in outputs[key]
                        for flag in sample.get("review_flags", [])
                    ),
                    "semantic_errors_omissions_hallucinations": "not human-rated; see per-example review fields",
                }
                for key in ("en_so", "so_en")
            },
        }
        en_so_samples = outputs["en_so"]
        system["en_to_so_route_audit"] = {
            "synthetic_candidate_samples": sum(
                any(
                    "synthetic EN→SO candidate selected" in warning
                    for warning in sample.get("warnings", [])
                )
                for sample in en_so_samples
            ),
            "multilingual_fallback_samples": sum(
                any(
                    "used multilingual fallback" in warning
                    for warning in sample.get("warnings", [])
                )
                for sample in en_so_samples
            ),
            "runaway_length_fallback_samples": sum(
                any(
                    "output-length guard" in warning
                    for warning in sample.get("warnings", [])
                )
                for sample in en_so_samples
            ),
        }
    else:
        if not args.candidate_model or not args.candidate_model.is_file():
            raise SystemExit(
                "--candidate-model must name the downloaded local GGUF file"
            )
        from llama_cpp import Llama

        model = args.candidate_model.resolve()
        model_hash = model_file_sha256(model)
        data_hash = hashlib.sha256(DATA.read_bytes()).hexdigest()
        checkpoint = load_checkpoint("afrislm", data_hash, model_hash, args.limit)
        outputs = checkpoint["samples"]
        completed = min(len(outputs["en_so"]), len(outputs["so_en"]))
        outputs["en_so"] = outputs["en_so"][:completed]
        outputs["so_en"] = outputs["so_en"][:completed]
        durations = {
            key: [item["elapsed_ms"] for item in outputs[key]]
            for key in ("en_so", "so_en")
        }
        start_load = time.perf_counter()
        llm = Llama(
            model_path=str(model),
            n_ctx=2048,
            n_threads=max(2, min(8, os.cpu_count() or 2)),
            n_gpu_layers=0,
            verbose=False,
        )
        load_seconds = checkpoint.get(
            "startup_seconds", time.perf_counter() - start_load
        )
        initial_rss = peak_working_set_bytes()
        started = time.perf_counter()
        with patch.object(socket.socket, "connect", deny_network):
            for i, row in enumerate(samples[completed:], completed + 1):
                for key, text, source, target in (
                    ("en_so", row["source_en"], "English", "Somali"),
                    ("so_en", row["reference_so"], "Somali", "English"),
                ):
                    tick = time.perf_counter()
                    translated = get_qvac_translation(llm, text, source, target)
                    durations[key].append((time.perf_counter() - tick) * 1000)
                    reference = (
                        row["reference_so"] if key == "en_so" else row["source_en"]
                    )
                    outputs[key].append(
                        {
                            "source": text,
                            "reference": reference,
                            "text": translated,
                            "warnings": [],
                            "elapsed_ms": round(durations[key][-1], 1),
                            "review_flags": diagnostic_flags(
                                translated, reference, key
                            ),
                        }
                    )
                if i % 5 == 0 or i == len(samples):
                    wall = checkpoint["wall_seconds"] + time.perf_counter() - started
                    save_checkpoint(
                        "afrislm",
                        data_hash,
                        model_hash,
                        outputs,
                        wall,
                        i,
                        args.limit,
                        load_seconds,
                    )
                    print(f"TranslatePsy-AfriSLM: {i}/{len(samples)} pairs", flush=True)
        system = {
            "model": "qvac/TranslatePsy-AfriSLM-0.8B-Q4-GGUF",
            "model_sha256": model_hash,
            "model_bytes": model.stat().st_size,
            **model_runtime_metadata("afrislm", model),
            "runtime": "llama-cpp-python 0.3.36; CPU only; n_ctx=2048; temperature=0",
            "network": "blocked: socket.socket.connect raises; model loaded from a local file",
            "sample_count": len(samples),
            "sample_ids": [row["id"] for row in samples],
            "startup_seconds": round(load_seconds, 2),
            "wall_seconds": round(
                checkpoint["wall_seconds"] + time.perf_counter() - started, 2
            ),
            "initial_working_set_bytes": initial_rss,
            "peak_working_set_bytes": peak_working_set_bytes(),
            "metrics": {
                "en_to_so": score(
                    [r["reference_so"] for r in samples],
                    [r["text"] for r in outputs["en_so"]],
                ),
                "so_to_en": score(
                    [r["source_en"] for r in samples],
                    [r["text"] for r in outputs["so_en"]],
                ),
            },
            "latency_ms": {
                key: {
                    "median": round(sorted(values)[len(values) // 2], 1),
                    "p95": round(sorted(values)[int(len(values) * 0.95) - 1], 1),
                }
                for key, values in durations.items()
            },
            "samples": outputs,
            "quality_review": {
                key: {
                    "numeric_token_mismatch_cues": sum(
                        "numeric-token mismatch" in flag
                        for sample in outputs[key]
                        for flag in sample.get("review_flags", [])
                    ),
                    "possible_negation_mismatch_cues": sum(
                        "possible negation mismatch" in flag
                        for sample in outputs[key]
                        for flag in sample.get("review_flags", [])
                    ),
                    "semantic_errors_omissions_hallucinations": "not human-rated; see per-example review fields",
                }
                for key in ("en_so", "so_en")
            },
        }

        baseline = (
            json.loads(OUTPUT.read_text(encoding="utf-8"))
            .get("systems", {})
            .get("baseline")
        )
        if baseline:
            baseline_by_id = {
                sample_id: i for i, sample_id in enumerate(baseline["sample_ids"])
            }
            paired_indices = [
                baseline_by_id[row["id"]]
                for row in samples
                if row["id"] in baseline_by_id
            ]
            paired_rows = [row for row in samples if row["id"] in baseline_by_id]
            system["same_examples_as_baseline"] = len(paired_rows)
            system["paired_baseline_metrics"] = {
                "en_to_so": score(
                    [row["reference_so"] for row in paired_rows],
                    [baseline["samples"]["en_so"][i]["text"] for i in paired_indices],
                ),
                "so_to_en": score(
                    [row["source_en"] for row in paired_rows],
                    [baseline["samples"]["so_en"][i]["text"] for i in paired_indices],
                ),
            }

    prior = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    prior.setdefault(
        "benchmark",
        {
            "dataset": "TICO-19 Somali test set",
            "data_file": "tests/data/somali_translation_tico19_test_150.jsonl",
            "metadata_file": "tests/data/somali_translation_tico19_test_150.metadata.json",
            "sample_count": len(all_samples),
            "sample_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
            "directions": "English↔Somali; reverse references use the parallel English originals",
        },
    )
    prior.setdefault("systems", {})[args.system] = system
    temporary_output = OUTPUT.with_suffix(".tmp")
    temporary_output.write_text(
        json.dumps(prior, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_output.replace(OUTPUT)
    CHECKPOINT.unlink(missing_ok=True)
    print(f"Saved {args.system} results: {OUTPUT}")
    for direction, metric in system["metrics"].items():
        print(
            f"{args.system} {direction}: BLEU={metric['bleu']} chrF++={metric['chrf_plus_plus']}"
        )
    print(
        f"wall={system['wall_seconds']}s startup={system.get('startup_seconds', 0)}s peak_rss={system['peak_working_set_bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
