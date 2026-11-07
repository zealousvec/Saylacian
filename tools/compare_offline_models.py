# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare installed app routes and frozen adapters on one private sample.

Each model runs in a separate process, so peak working set includes loading
without retaining another model. Outputs/checkpoints stay outside the checkout.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def private_path(path):
    path = path.resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("Samples and outputs must stay outside the repository.")
    return path


def read_sample(path):
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not rows or len(rows) > 1000:
        raise ValueError("Use 1..1000 fixed examples.")
    for row in rows:
        if row.get("route") not in {"en-so", "so-en", "fr-so", "so-fr"}:
            raise ValueError("Unsupported route.")
        if not all(
            isinstance(row.get(k), str) and row[k].strip()
            for k in ("source", "reference")
        ):
            raise ValueError("Each sample needs source and reference text.")
    return rows


def peak_rss():
    if os.name != "nt":
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value if sys.platform == "darwin" else value * 1024

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t)
            for name in (
                "peak_working_set",
                "working_set",
                "peak_paged",
                "paged",
                "peak_nonpaged",
                "nonpaged",
                "pagefile",
                "peak_pagefile",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]
    if not psapi.GetProcessMemoryInfo(
        kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.peak_working_set


def worker(args):
    rows = read_sample(args.sample)
    sample_hash = digest(args.sample)
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    identity = {
        "sample_sha256": sample_hash,
        "model": args.model,
        "experiment": args.experiment,
        "generation": (
            "installed-app-offline-defaults"
            if args.model == "installed"
            else "beam4-input256-output128-ngram3-penalty1.1-fp16"
        ),
    }
    model = tokenizer = torch = None
    loading_started = time.perf_counter()
    if args.model == "adapter":
        import torch
        from peft import PeftModel
        from transformers import M2M100ForConditionalGeneration
        from transformers import M2M100Tokenizer

        from tools.translation_lab.config import load_config
        from tools.translation_lab.m2m100_multilingual import (
            candidate_training_complete,
        )
        from tools.translation_lab.m2m100_training import MODEL_REVISION
        from tools.translation_lab.m2m100_training import _preflight
        from tools.translation_lab.m2m100_training import _verify_model_bundle
        from tools.translation_lab.resources import gpu_preflight

        config = load_config(args.workspace / "config/active.toml")
        gpu_preflight(
            max_vram_gib=config.max_vram_gib,
            max_temperature_c=config.gpu_max_temp_c,
            minimum_free_gib=config.min_free_vram_gib,
        )
        _preflight(torch, max_gpu_fraction=min(0.60, config.max_vram_gib / 8))
        torch.set_num_threads(config.max_cpu_threads)
        directory = args.workspace / "experiments" / args.experiment
        weights = directory / "adapter-final/adapter_model.safetensors"
        metadata = json.loads((directory / "experiment.json").read_text())
        report = json.loads((directory / "training-report.json").read_text())
        if not candidate_training_complete(metadata, report, weights):
            raise ValueError("Only complete frozen private adapters are eligible.")
        identity["adapter_sha256"] = digest(weights)
        model_dir = (
            args.workspace / "cache/models/facebook-m2m100-418M" / MODEL_REVISION
        )
        _verify_model_bundle(args.workspace, model_dir)
        tokenizer = M2M100Tokenizer.from_pretrained(model_dir, local_files_only=True)
        base = M2M100ForConditionalGeneration.from_pretrained(
            model_dir,
            local_files_only=True,
            torch_dtype=torch.float16,
            device_map={"": 0},
            low_cpu_mem_usage=True,
        )
        model = PeftModel.from_pretrained(
            base, directory / "adapter-final", is_trainable=False
        ).eval()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
    else:
        from saylacian.core.model_packs import ModelPackManager
        from saylacian.core.translation import translate_meaning

        manager = ModelPackManager()
        identity["packs"] = []
        for root in manager.active_model_roots():
            receipt = root / "installed.json"
            identity["packs"].append(
                {"root": str(root), "receipt_sha256": digest(receipt)}
            )
    identity_path = output / "identity.json"
    if identity_path.exists():
        if json.loads(identity_path.read_text()) != identity:
            raise ValueError("Resume fingerprint changed; use a new output directory.")
    else:
        identity_path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    load_seconds = time.perf_counter() - loading_started
    predictions_path = output / "predictions.jsonl"
    done = (
        [
            json.loads(s)
            for s in predictions_path.read_text(encoding="utf-8").splitlines()
        ]
        if predictions_path.exists()
        else []
    )
    if len(done) > len(rows):
        raise ValueError("Checkpoint has too many records.")
    for index, record in enumerate(done):
        if record["index"] != index or record["example"] != rows[index]:
            raise ValueError("Checkpoint example mismatch.")

    def deny(*_args, **_kwargs):
        raise RuntimeError("Network forbidden during offline evaluation.")

    socket.socket.connect = deny
    labels = {"en": "English", "so": "Somali Latin", "fr": "French"}
    for index in range(len(done), len(rows)):
        row = rows[index]
        source, target = row["route"].split("-")
        started = time.perf_counter()
        if args.model == "installed":
            result = translate_meaning(
                row["source"],
                labels[source],
                labels[target],
                provider_override="offline",
            )
            prediction = result.text
        else:
            tokenizer.src_lang = source
            encoded = tokenizer(
                row["source"], return_tensors="pt", truncation=True, max_length=256
            ).to("cuda")
            with torch.inference_mode():
                generated = model.generate(
                    **encoded,
                    forced_bos_token_id=tokenizer.get_lang_id(target),
                    max_new_tokens=128,
                    num_beams=4,
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.1,
                )
            torch.cuda.synchronize()
            prediction = tokenizer.decode(generated[0], skip_special_tokens=True)
        record = {
            "index": index,
            "example": row,
            "prediction": prediction,
            "seconds": time.perf_counter() - started,
        }
        with predictions_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        done.append(record)
        print(f"{args.model} {index + 1}/{len(rows)}", flush=True)
    stats = {
        "identity": identity,
        "load_seconds_this_invocation": load_seconds,
        "peak_process_working_set_bytes": peak_rss(),
        "peak_gpu_allocated_bytes": (torch.cuda.max_memory_allocated() if torch else 0),
        "peak_gpu_reserved_bytes": (torch.cuda.max_memory_reserved() if torch else 0),
        "network_during_inference": "blocked",
        "prediction_sha256": digest(predictions_path),
    }
    (output / "resources.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8"
    )


def compare(args):
    from sacrebleu.metrics import BLEU
    from sacrebleu.metrics import CHRF

    from tools.translation_lab.tico19_benchmark import paired_sentence_chrf

    rows = read_sample(args.sample)
    configurations = [("installed", args.python_app, None)] + [
        (name, args.python_training, name) for name in args.experiments
    ]
    outputs = {}
    for name, python, experiment in configurations:
        target = args.output / name
        command = [
            str(python),
            str(Path(__file__).resolve()),
            "--sample",
            str(args.sample),
            "--output",
            str(target),
            "--workspace",
            str(args.workspace),
            "--worker",
            "--model",
            "adapter" if experiment else "installed",
        ]
        if experiment:
            command.extend(["--experiment", experiment])
        subprocess.run(command, check=True, cwd=ROOT)
        predictions = [
            json.loads(s)
            for s in (target / "predictions.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        if len(predictions) != len(rows):
            raise ValueError("Incomplete model outputs.")
        outputs[name] = predictions
    report = {
        "scope": "fixed private diagnostic sample; not a general accuracy claim",
        "sample_sha256": digest(args.sample),
        "rows": len(rows),
        "automatic_promotion": False,
        "models": {},
        "routes": {},
    }
    for name in outputs:
        report["models"][name] = json.loads(
            (args.output / name / "resources.json").read_text()
        )
    for route in sorted({r["route"] for r in rows}):
        indices = [i for i, r in enumerate(rows) if r["route"] == route]
        refs = [rows[i]["reference"] for i in indices]
        metrics = {}
        for name, predictions in outputs.items():
            hypotheses = [predictions[i]["prediction"] for i in indices]
            metrics[name] = {
                "bleu": BLEU().corpus_score(hypotheses, [refs]).score,
                "chrf++": CHRF(word_order=2).corpus_score(hypotheses, [refs]).score,
                "mean_seconds": sum(predictions[i]["seconds"] for i in indices)
                / len(indices),
            }
            if name != "installed":
                metrics[name]["paired_vs_installed"] = paired_sentence_chrf(
                    refs,
                    [outputs["installed"][i]["prediction"] for i in indices],
                    hypotheses,
                    bootstrap_samples=2000,
                    seed=1729,
                )
        report["routes"][route] = metrics
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    lines = [
        "# Offline model comparison",
        "",
        report["scope"],
        "",
        "| Route | Model | BLEU | chrF++ | Mean seconds |",
        "|---|---|---:|---:|---:|",
    ]
    for route, metrics in report["routes"].items():
        for name, values in metrics.items():
            lines.append(
                f"| {route} | {name} | {values['bleu']:.3f} | "
                f"{values['chrf++']:.3f} | {values['mean_seconds']:.3f} |"
            )
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--python-app", type=Path, default=Path(sys.executable))
    parser.add_argument("--python-training", type=Path)
    parser.add_argument("--experiments", nargs="+", default=[])
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--model", choices=["installed", "adapter"], default="installed"
    )
    parser.add_argument("--experiment")
    args = parser.parse_args()
    args.sample = private_path(args.sample)
    args.output = private_path(args.output)
    for experiment in args.experiments:
        if Path(experiment).name != experiment or experiment in {".", ".."}:
            parser.error("Experiments must be single path components.")
    if args.experiment and (
        Path(args.experiment).name != args.experiment or args.experiment in {".", ".."}
    ):
        parser.error("Experiment must be a single path component.")
    if args.experiments and not args.python_training:
        parser.error("--python-training is required with --experiments")
    worker(args) if args.worker else compare(args)


if __name__ == "__main__":
    main()
