# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline baseline evaluation through Saylacian's real production routes."""

from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path
from unittest.mock import patch

from saylacian.core.translation import translate_meaning


class NetworkDisabled:
    def __enter__(self):
        def deny(*args, **kwargs):
            raise AssertionError("Network access attempted during offline evaluation.")

        self.patch_connect = patch.object(socket.socket, "connect", deny)
        self.patch_connect_ex = patch.object(socket.socket, "connect_ex", deny)
        self.patch_connect.start()
        self.patch_connect_ex.start()

    def __exit__(self, exc_type, exc, traceback):
        self.patch_connect_ex.stop()
        self.patch_connect.stop()


def evaluate_tico_sample(
    repository: Path,
    workspace: Path,
    sample_size: int = 20,
    seed: int = 1729,
    experiment_id: str = "manual",
) -> dict:
    fixture = repository / "tests/data/somali_translation_tico19_test_150.jsonl"
    metadata = (
        repository / "tests/data/somali_translation_tico19_test_150.metadata.json"
    )
    if not fixture.is_file() or not metadata.is_file():
        return {"status": "BLOCKED", "reason": "TICO-19 local fixture is unavailable."}
    meta = json.loads(metadata.read_text(encoding="utf-8"))
    if meta.get("upstream_split") != "test" or not str(
        meta.get("translation_license", "")
    ).startswith("CC0-1.0"):
        return {
            "status": "BLOCKED",
            "reason": "Fixture metadata failed its evaluation-only licence gate.",
        }
    rows = [
        json.loads(line)
        for line in fixture.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if any(row.get("split") != "test" for row in rows):
        raise ValueError("TICO fixture contains a row outside its upstream test split.")
    if any(row.get("translation_license") != "CC0-1.0" for row in rows):
        raise ValueError(
            "TICO fixture has rows outside the reviewed translation licence."
        )
    if sample_size <= 0:
        return {"status": "SKIPPED", "reason": "Translation sample count is zero."}
    try:
        from sacrebleu.metrics import BLEU
        from sacrebleu.metrics import CHRF
    except ImportError:
        return {
            "status": "BLOCKED",
            "reason": "Install the pinned evaluation extra from requirements-dev.txt.",
        }
    import random

    chosen = random.Random(seed).sample(rows, min(sample_size, len(rows)))
    experiment_dir = workspace / "experiments" / experiment_id
    experiment_dir.mkdir(parents=True, exist_ok=True)
    outputs_private = experiment_dir / "outputs-private.jsonl"
    directions = (
        ("en_so", "English", "Somali Latin", "source_en", "reference_so"),
        ("so_en", "Somali Latin", "English", "reference_so", "source_en"),
    )
    report = {
        "status": "PASS",
        "dataset": meta["dataset"],
        "upstream_split": meta["upstream_split"],
        "domain": "health / COVID-19",
        "license": meta["translation_license"],
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "sample_size_per_direction": len(chosen),
        "seed": seed,
        "network_during_inference": "blocked by socket guard",
        "directions": {},
        "reference_scored_translations": 0,
        "human_reviewed_examples": 0,
        "limitations": [
            "Health-domain sample is not representative of ordinary conversation.",
            "Training overlap for upstream models is not fully established.",
            "Automatic BLEU/chrF scores do not substitute for fluent-speaker review.",
            (
                "Original source materials have mixed rights; use rows only "
                "for local evaluation."
            ),
        ],
    }

    with outputs_private.open("w", encoding="utf-8", newline="\n") as private_output:
        for route, source, target, source_key, reference_key in directions:
            hypotheses = []
            references = []
            for row in chosen:
                value = row[source_key]
                reference = row[reference_key]
                with NetworkDisabled():
                    translated = translate_meaning(
                        value,
                        source,
                        target,
                        provider_override="offline",
                    )
                hypotheses.append(translated.text)
                references.append(reference)
                private_output.write(
                    json.dumps(
                        {
                            "case_id": row["id"],
                            "route": route,
                            "source": value,
                            "reference": reference,
                            "output": translated.text,
                            "warnings": list(translated.warnings),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            bleu_metric = BLEU()
            bleu = bleu_metric.corpus_score(hypotheses, [references])
            chrf_metric = CHRF(word_order=2)
            chrf = chrf_metric.corpus_score(hypotheses, [references])
            report["directions"][route] = {
                "n": len(chosen),
                "bleu": round(bleu.score, 4),
                "bleu_signature": str(bleu_metric.get_signature()),
                "chrf_plus_plus": round(chrf.score, 4),
                "chrf_signature": str(chrf_metric.get_signature()),
            }
            report["reference_scored_translations"] += len(chosen)
    return report


def evaluate_prepared_google_smol(
    workspace: Path,
    sample_size: int = 20,
    seed: int = 1729,
) -> dict:
    """Score the prepared held-out Google SMOL pairs through offline app routes."""
    prepared = (
        workspace
        / "data/prepared/google-smol-en-so/fdaff3a1a019f89fa30a562a85d7c1d3e9150444"
    )
    manifest_path = prepared / "manifest.json"
    test_path = prepared / "test.jsonl"
    if not manifest_path.is_file() or not test_path.is_file():
        return {
            "status": "BLOCKED",
            "reason": "Prepare the pinned Google SMOL corpus before evaluation.",
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(test_path.read_bytes()).hexdigest()
    if (
        manifest.get("source_id") != "google-smol-en-so"
        or manifest.get("license") != "CC-BY-4.0"
        or digest != manifest.get("split_sha256", {}).get("test.jsonl")
    ):
        return {
            "status": "BLOCKED",
            "reason": "Prepared corpus provenance or test split checksum failed.",
        }
    rows = [
        json.loads(line)
        for line in test_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if sample_size <= 0:
        return {"status": "SKIPPED", "reason": "Evaluation sample count is zero."}
    try:
        from sacrebleu.metrics import BLEU
        from sacrebleu.metrics import CHRF
    except ImportError:
        return {
            "status": "BLOCKED",
            "reason": (
                "Install the pinned evaluation dependency from requirements-dev.txt."
            ),
        }

    import random

    chosen = random.Random(seed).sample(rows, min(sample_size, len(rows)))
    output_path = workspace / "reports/google-smol-test-outputs-private.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    directions = (
        ("en_so", "English", "Somali Latin", "source_text", "target_text"),
        ("so_en", "Somali Latin", "English", "target_text", "source_text"),
    )
    report = {
        "status": "PASS",
        "dataset": "Google SMOL English-Somali",
        "source_id": manifest["source_id"],
        "revision": manifest["dataset_revision"],
        "license": manifest["license"],
        "domain": (
            "Mixed sentence translation; source domain balance is not "
            "independently audited"
        ),
        "test_split_sha256": digest,
        "sample_size_per_direction": len(chosen),
        "seed": seed,
        "network_during_inference": "blocked by socket guard",
        "directions": {},
        "reference_scored_translations": 0,
        "human_reviewed_examples": 0,
        "limitations": [
            "The held-out split is small and was created from 862 source pairs.",
            "No fluent-speaker quality review has been performed.",
            "Training overlap for the installed models is not established.",
            "BLEU and chrF++ do not establish translation correctness.",
        ],
    }
    with output_path.open("w", encoding="utf-8", newline="\n") as private_output:
        for route, source, target, source_key, reference_key in directions:
            hypotheses = []
            references = []
            for row in chosen:
                value = row[source_key]
                reference = row[reference_key]
                with NetworkDisabled():
                    translated = translate_meaning(
                        value,
                        source,
                        target,
                        provider_override="offline",
                    )
                hypotheses.append(translated.text)
                references.append(reference)
                private_output.write(
                    json.dumps(
                        {
                            "case_id": row["record_id"],
                            "route": route,
                            "source": value,
                            "reference": reference,
                            "output": translated.text,
                            "warnings": list(translated.warnings),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
            bleu_metric = BLEU()
            bleu = bleu_metric.corpus_score(hypotheses, [references])
            chrf_metric = CHRF(word_order=2)
            chrf = chrf_metric.corpus_score(hypotheses, [references])
            report["directions"][route] = {
                "n": len(chosen),
                "bleu": round(bleu.score, 4),
                "bleu_signature": str(bleu_metric.get_signature()),
                "chrf_plus_plus": round(chrf.score, 4),
                "chrf_signature": str(chrf_metric.get_signature()),
            }
            report["reference_scored_translations"] += len(chosen)
    return report
