# SPDX-License-Identifier: AGPL-3.0-or-later
"""One-command entry point for Saylacian's local research lab."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import replace
from datetime import UTC
from datetime import datetime
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from tools.translation_lab.capabilities import build_inventory
from tools.translation_lab.config import LabConfig
from tools.translation_lab.config import load_config
from tools.translation_lab.downloader import DownloadSpec
from tools.translation_lab.downloader import download_approved
from tools.translation_lab.prepare_data import prepare_google_smol
from tools.translation_lab.runner import PauseRun
from tools.translation_lab.runner import current_status
from tools.translation_lab.runner import run_overnight
from tools.translation_lab.sources import load_catalog
from tools.translation_lab.sources import read_owner_registry
from tools.translation_lab.translation_eval import evaluate_prepared_google_smol
from tools.translation_lab.transliteration_eval import evaluate_script_cases
from tools.translation_lab.workspace import default_workspace
from tools.translation_lab.workspace import initialize_workspace

DEFAULT_CONFIG = REPOSITORY / "research" / "translation_lab.example.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local_translation_lab",
        description="Run bounded, local Saylacian translation research checks.",
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser(
        "doctor", help="Read machine, source, pack and runtime status."
    )
    doctor.add_argument("--config", type=Path)
    commands.add_parser("init", help="Create a private user-local lab workspace.")
    commands.add_parser("status", help="Show persisted run state and counters.")
    commands.add_parser(
        "pause", help="Request a cooperative pause at the next stage boundary."
    ).add_argument("--run-id")

    sources = commands.add_parser("sources", help="Inspect source and rights records.")
    source_commands = sources.add_subparsers(dest="sources_command", required=True)
    source_commands.add_parser(
        "list", help="List source candidates and current rights state."
    )
    source_commands.add_parser(
        "verify", help="Validate source registry structure and gates."
    )

    script_tests = commands.add_parser(
        "test-scripts", help="Run seeded invariants on production transliterators."
    )
    script_tests.add_argument("--count", type=int, default=1_000_000)
    script_tests.add_argument("--seed", type=int, default=1729)

    transliteration = commands.add_parser(
        "transliteration-check",
        help="Run or resume durable production transliteration checks.",
    )
    transliteration.add_argument("--target", type=int, default=100_000)
    transliteration.add_argument("--seed", type=int, default=1729)
    transliteration.add_argument("--run-id")
    run_mode = transliteration.add_mutually_exclusive_group()
    run_mode.add_argument("--resume", action="store_true")
    run_mode.add_argument("--restart", action="store_true")
    transliteration.add_argument("--stop-after", type=int, help=argparse.SUPPRESS)
    transliteration.add_argument("--max-hours", type=float)
    transliteration.add_argument("--dry-run", action="store_true")
    transliteration.add_argument("--retry-failures", action="store_true")

    smoke = commands.add_parser(
        "smoke", help="Run fast offline transliteration and training checks."
    )
    smoke.add_argument("--config", type=Path)

    train_smoke = commands.add_parser(
        "train-smoke", help="Train and resume a tiny local mock model."
    )
    train_smoke.add_argument("--run-id", default="training-smoke")
    train_smoke.add_argument("--steps", type=int, default=40)
    train_smoke.add_argument("--resume", action="store_true")
    train_smoke.add_argument("--stop-after", type=int, help=argparse.SUPPRESS)

    baseline = commands.add_parser(
        "baseline",
        help=(
            "Reserved; TICO-19 final test references are unavailable for routine runs."
        ),
    )
    baseline.add_argument("--samples", type=int, default=20)
    baseline.add_argument("--seed", type=int, default=1729)

    evaluation = commands.add_parser(
        "evaluate",
        help="Score the prepared Google SMOL test split on offline Somali routes.",
    )
    evaluation.add_argument(
        "--dataset", choices=["google-smol-en-so"], default="google-smol-en-so"
    )
    evaluation.add_argument("--samples", type=int, default=20)
    evaluation.add_argument("--seed", type=int, default=1729)

    overnight = commands.add_parser(
        "overnight",
        help="Run preflight, scripts, offline baseline and safe training gate.",
    )
    overnight.add_argument("--config", type=Path)
    overnight.add_argument("--script-checks", type=int)
    overnight.add_argument("--translation-samples", type=int)
    overnight.add_argument("--recover-stale-lock", action="store_true")
    overnight.add_argument("--resume", action="store_true")

    resume = commands.add_parser(
        "resume", help="Resume the last compatible paused or interrupted run."
    )
    resume.add_argument("--config", type=Path)
    resume.add_argument("--recover-stale-lock", action="store_true")

    leaderboard = commands.add_parser(
        "leaderboard", help="List independently verified private dev evaluations."
    )
    leaderboard.add_argument("--verified-only", action="store_true")

    report = commands.add_parser(
        "report", help="Print the latest local report location and counts."
    )
    report.add_argument("--json", action="store_true")
    report.add_argument("--run-id")
    training = commands.add_parser(
        "train", help="Check training readiness or train a private LoRA candidate."
    )
    training.add_argument("--config", type=Path)
    training.add_argument("--execute", action="store_true")
    training.add_argument("--resume", action="store_true")
    training.add_argument("--experiment-id", default="m2m100-smol-lora-20261031")
    training.add_argument("--run-id")
    training.add_argument("--dataset-id", default="google-smol-en-so")
    training.add_argument("--model-dir", type=Path)
    training.add_argument("--max-gpu-fraction", type=float, default=0.65)
    training.add_argument("--max-vram-gb", type=float)
    training.add_argument("--gpu-max-temp-c", type=float)
    training.add_argument("--learning-rate", type=float, default=1e-4)
    training.add_argument("--num-train-epochs", type=int, default=1)
    training.add_argument("--lora-rank", type=int, default=8)
    training.add_argument("--max-steps", type=int)
    campaign = commands.add_parser(
        "train-campaign",
        help="Run bounded M2M100 LoRA pilots, one full candidate, and dev evaluation.",
    )
    campaign.add_argument("--campaign-id", required=True)
    campaign.add_argument("--pilot-steps", type=int, default=250)
    campaign.add_argument("--max-hours", type=float, default=8)
    campaign.add_argument("--resume", action="store_true")
    campaign.add_argument("--dry-run", action="store_true")
    campaign.add_argument("--max-vram-gb", type=float)
    campaign.add_argument("--gpu-max-temp-c", type=float)
    candidate_eval = commands.add_parser(
        "evaluate-candidate",
        help="Compare a private LoRA candidate with its base on untouched test data.",
    )
    candidate_eval.add_argument("--config", type=Path)
    candidate_eval.add_argument("--experiment-id", default="m2m100-smol-lora-20261031")
    candidate_eval.add_argument("--dataset-id", default="google-smol-en-so")
    candidate_eval.add_argument("--evaluation-dataset-id")
    candidate_eval.add_argument("--model-dir", type=Path)
    candidate_eval.add_argument("--max-vram-gb", type=float)
    candidate_eval.add_argument("--gpu-max-temp-c", type=float)
    multilingual_training = commands.add_parser(
        "train-multilingual-candidate",
        help=(
            "Train one private M2M100 LoRA across approved English/French/Somali pairs."
        ),
    )
    multilingual_training.add_argument("--config", type=Path)
    multilingual_training.add_argument("--execute", action="store_true", required=True)
    multilingual_training.add_argument("--resume", action="store_true")
    multilingual_training.add_argument(
        "--experiment-id", default="m2m100-en-fr-so-shared-lora-20261104"
    )
    multilingual_training.add_argument("--model-dir", type=Path)
    multilingual_training.add_argument("--max-gpu-fraction", type=float, default=0.60)
    multilingual_training.add_argument("--learning-rate", type=float, default=5e-5)
    multilingual_training.add_argument("--epochs", type=float, default=1.0)
    multilingual_training.add_argument(
        "--initial-adapter-experiment-id",
        help="Continue training from a completed private multilingual candidate.",
    )
    multilingual_eval = commands.add_parser(
        "evaluate-multilingual-candidate",
        help="Score a frozen shared adapter on pair-specific held-out test rows.",
    )
    multilingual_eval.add_argument("--config", type=Path)
    multilingual_eval.add_argument(
        "--experiment-id", default="m2m100-en-fr-so-shared-lora-20261104"
    )
    multilingual_eval.add_argument(
        "--run-id", default="m2m100-en-fr-so-heldout-20261104"
    )
    multilingual_eval.add_argument("--model-dir", type=Path)
    french_eval = commands.add_parser(
        "evaluate-tico19-french-dev",
        help="Score installed French/English routes on pinned TICO-19 dev data.",
    )
    french_eval.add_argument(
        "--archive",
        type=Path,
        default=default_workspace() / "cache/data/tico19/tico19-testset-2021-02-26.zip",
    )
    french_eval.add_argument("--run-id", default="tico19-french-dev")
    french_eval.add_argument("--resume", action="store_true")
    french_eval.add_argument("--limit", type=int)
    route_matrix = commands.add_parser(
        "evaluate-tico19-route-matrix-dev",
        help="Score all installed translation routes on matched TICO-19 dev data.",
    )
    route_matrix.add_argument(
        "--archive",
        type=Path,
        default=default_workspace() / "cache/data/tico19/tico19-testset-2021-02-26.zip",
    )
    route_matrix.add_argument("--run-id", default="tico19-somali-pivot-dev")
    route_matrix.add_argument("--resume", action="store_true")
    route_matrix.add_argument("--limit", type=int)
    flores_eval = commands.add_parser(
        "evaluate-flores-devtest",
        help="Score installed translation routes on pinned FLORES-200 devtest.",
    )
    flores_eval.add_argument(
        "--archive",
        type=Path,
        default=default_workspace()
        / "cache/data/flores200-official/flores200_dataset.tar.gz",
    )
    flores_eval.add_argument("--run-id", default="flores200-route-matrix-devtest")
    flores_eval.add_argument("--resume", action="store_true")
    m2m_flores_eval = commands.add_parser(
        "evaluate-m2m100-flores-devtest",
        help="Compare a private M2M100 adapter with its base on clean FLORES devtest.",
    )
    m2m_flores_eval.add_argument(
        "--archive",
        type=Path,
        default=default_workspace()
        / "cache/data/flores200-official/flores200_dataset.tar.gz",
    )
    m2m_flores_eval.add_argument(
        "--experiment-id",
        default="m2m100-learning-rate-campaign-20261101-full-2e-04",
    )
    m2m_flores_eval.add_argument("--run-id", default="m2m100-flores-devtest")
    m2m_flores_eval.add_argument("--resume", action="store_true")
    marian_flores_eval = commands.add_parser(
        "evaluate-marian-flores-devtest",
        help="Compare an existing Marian adapter with its base on FLORES devtest.",
    )
    marian_flores_eval.add_argument(
        "--archive",
        type=Path,
        default=default_workspace()
        / "cache/data/flores200-official/flores200_dataset.tar.gz",
    )
    marian_flores_eval.add_argument(
        "--experiment-id",
        default="marian-mixture-google-weighted-2epoch-lora-20261031",
    )
    marian_flores_eval.add_argument("--run-id", default="marian-flores-devtest")
    marian_flores_eval.add_argument("--resume", action="store_true")
    prepare = commands.add_parser(
        "prepare", help="Validate and split a pinned English–Somali corpus."
    )
    prepare.add_argument(
        "--source",
        choices=[
            "google-smol-en-so",
            "opus-paracrawl-en-so",
            "opus-infopankki-en-so",
        ],
        default="google-smol-en-so",
    )
    for command, help_text in (
        ("export", "Check for a verified candidate ready for staged export."),
        ("propose", "Create an owner-reviewable local promotion proposal."),
        ("promote", "Install a candidate locally only after explicit approval."),
        ("rollback", "Restore the prior local candidate only after explicit approval."),
    ):
        commands.add_parser(command, help=help_text)
    download = commands.add_parser(
        "download",
        help="Download only pinned, rights-cleared, owner-approved artifacts.",
    )
    download.add_argument("--approved", action="store_true", required=True)
    download.add_argument("--config", type=Path)
    download.add_argument("--max-download-gb", type=float)
    download.add_argument("--max-disk-gb", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = args.workspace
    if args.command == "doctor":
        config_path = args.config or _workspace_config(workspace)
        try:
            config = load_config(config_path)
        except (OSError, ValueError) as error:
            print(f"Config validation failed: {error}", file=sys.stderr)
            return 2
        _print_json(
            {
                "inventory": build_inventory(REPOSITORY),
                "config": str(config_path),
                "config_valid": True,
                "training_enabled": config.training_enabled,
                "approved_source_count": len(config.approved_source_ids),
                "automatic_promotion": config.automatic_promotion,
                "resource_limits": {
                    "max_runtime_hours": config.max_runtime_hours,
                    "max_disk_gib": config.max_disk_gib,
                    "max_download_gib": config.max_download_gib,
                    "max_vram_gib": config.max_vram_gib,
                    "gpu_max_temp_c": config.gpu_max_temp_c,
                    "min_free_vram_gib": config.min_free_vram_gib,
                },
                "rights": _source_gate_summary(workspace, config),
            }
        )
        return 0
    if args.command == "init":
        active = initialize_workspace(workspace, REPOSITORY, DEFAULT_CONFIG)
        _print_json(build_inventory(REPOSITORY), workspace / "inventory.json")
        print(f"Workspace initialized. Active config: {active}")
        return 0
    if args.command == "sources":
        return _sources(args.sources_command, workspace)
    if args.command == "download":
        return _download(args, workspace)
    if args.command == "test-scripts":
        try:
            result = evaluate_script_cases(args.count, args.seed)
        except (AssertionError, ValueError) as error:
            print(f"Script checks failed: {error}", file=sys.stderr)
            return 1
        result_path = workspace / "reports" / f"scripts-{_timestamp()}.json"
        _print_json(result, result_path)
        print(f"Script report: {result_path}")
        return 1 if result["failure_count"] else 0
    if args.command == "transliteration-check":
        from tools.translation_lab.independent_runner import run_transliteration_check

        run_id = args.run_id
        if args.restart:
            run_id = (run_id or f"script-{args.seed}") + f"-restart-{_timestamp()}"
        if args.dry_run:
            _print_json(
                {
                    "status": "DRY_RUN",
                    "target": args.target,
                    "seed": args.seed,
                    "workspace": str(workspace),
                    "will_start": False,
                }
            )
            return 0
        progress_state = {"last": 0.0}

        def show_progress(counts):
            now = __import__("time").monotonic()
            if (
                counts["completed"] == counts["target"]
                or now - progress_state["last"] >= 1
            ):
                progress_state["last"] = now
                print(
                    f"{counts['completed']:,}/{counts['target']:,} committed | "
                    f"pass={counts['passed']:,} fail={counts['failed']:,} "
                    f"unique-inputs={counts['unique_inputs']:,} "
                    f"{counts['cases_per_second']:,}/s",
                    flush=True,
                )

        try:
            result = run_transliteration_check(
                workspace,
                target=args.target,
                seed=args.seed,
                run_id=run_id,
                resume=args.resume,
                stop_after=args.stop_after,
                max_hours=args.max_hours,
                retry_failures=args.retry_failures,
                progress=show_progress,
            )
        except (OSError, RuntimeError, ValueError, AssertionError) as error:
            print(f"Transliteration run stopped safely: {error}", file=sys.stderr)
            return 2
        except KeyboardInterrupt:
            print("Interrupted at the last committed checkpoint; resume with --resume.")
            return 3
        _print_json(result)
        return 0 if result["status"] == "COMPLETED" and not result["failed"] else 3
    if args.command == "smoke":
        from tools.translation_lab.independent_runner import run_transliteration_check
        from tools.translation_lab.training_smoke import run_training_smoke

        try:
            load_config(args.config or _workspace_config(workspace))
        except (OSError, ValueError) as error:
            print(f"Config validation failed: {error}", file=sys.stderr)
            return 2
        stamp = _timestamp()
        script = run_transliteration_check(
            workspace, target=64, seed=101, run_id=f"smoke-script-{stamp}"
        )
        training = run_training_smoke(
            workspace, run_id=f"smoke-training-{stamp}", steps=8
        )
        _print_json(
            {
                "status": "PASS"
                if script["failed"] == 0 and training["parameters_changed"]
                else "FAIL",
                "transliteration": script,
                "training": training,
                "network": "not used",
                "large_model": "not loaded",
            }
        )
        return 0 if script["failed"] == 0 and training["parameters_changed"] else 2
    if args.command == "train-smoke":
        from tools.translation_lab.training_smoke import run_training_smoke

        try:
            result = run_training_smoke(
                workspace,
                run_id=args.run_id,
                steps=args.steps,
                resume=args.resume,
                stop_after=args.stop_after,
            )
        except (OSError, ValueError, FileExistsError) as error:
            print(f"Training smoke stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0 if result["status"] == "COMPLETED" else 3
    if args.command in {"baseline", "evaluate"}:
        if args.command == "baseline":
            print(
                "Blocked: TICO-19 final test references are reserved. Use the "
                "private dev-only candidate evaluator for development scoring.",
                file=sys.stderr,
            )
            return 2
        samples = args.samples
        result = evaluate_prepared_google_smol(workspace, samples, args.seed)
        result_path = workspace / "reports" / f"baseline-{_timestamp()}.json"
        _print_json(result, result_path)
        print(f"Baseline report: {result_path}")
        return 0 if result.get("status") in {"PASS", "SKIPPED"} else 2
    if args.command == "overnight":
        return _run(args, workspace, resume=args.resume)
    if args.command == "resume":
        return _run(args, workspace, resume=True)
    if args.command == "status":
        _print_json(current_status(workspace))
        return 0
    if args.command == "pause":
        if args.run_id:
            from tools.translation_lab.independent_runner import _validate_run_id
            from tools.translation_lab.state import read_json

            try:
                _validate_run_id(args.run_id)
            except ValueError as error:
                print(str(error), file=sys.stderr)
                return 2
            active = read_json(workspace / "locks" / "active_run.json") or {}
            if active.get("run_id") == args.run_id:
                from tools.translation_lab.state import request_pause

                request_pause(workspace)
            else:
                pause_file = workspace / "runs" / args.run_id / "pause.requested"
                pause_file.parent.mkdir(parents=True, exist_ok=True)
                pause_file.write_text(_timestamp() + "\n", encoding="utf-8")
        else:
            try:
                from tools.translation_lab.independent_runner import _latest_incomplete

                active_id = _latest_incomplete(workspace)
            except ValueError:
                from tools.translation_lab.state import request_pause

                request_pause(workspace)
            else:
                pause_file = workspace / "runs" / active_id / "pause.requested"
                pause_file.write_text(_timestamp() + "\n", encoding="utf-8")
        print("Pause requested. The runner will stop at its next committed checkpoint.")
        return 0
    if args.command == "leaderboard":
        _leaderboard(workspace, verified_only=args.verified_only)
        return 0
    if args.command == "report":
        if args.run_id:
            _run_report(workspace, args.run_id)
            return 0
        path = workspace / "reports" / "latest.json"
        if not path.is_file():
            print("No completed run report exists yet.", file=sys.stderr)
            return 2
        print(f"Markdown: {workspace / 'reports' / 'latest.md'}")
        print(f"JSON: {path}")
        if args.json:
            print(path.read_text(encoding="utf-8"))
        else:
            _print_json(json.loads(path.read_text(encoding="utf-8")))
        return 0
    if args.command == "train":
        config = load_config(args.config or _workspace_config(workspace))
        if args.execute:
            from tools.translation_lab.m2m100_training import MODEL_REVISION
            from tools.translation_lab.m2m100_training import train_m2m100_lora

            model_dir = args.model_dir or (
                workspace / "cache" / "models" / "facebook-m2m100-418M" / MODEL_REVISION
            )
            try:
                from tools.translation_lab.resources import gpu_preflight

                gpu = gpu_preflight(
                    max_vram_gib=(
                        args.max_vram_gb
                        if args.max_vram_gb is not None
                        else config.max_vram_gib
                    ),
                    max_temperature_c=(
                        args.gpu_max_temp_c
                        if args.gpu_max_temp_c is not None
                        else config.gpu_max_temp_c
                    ),
                    minimum_free_gib=config.min_free_vram_gib,
                )
                gpu_fraction = min(args.max_gpu_fraction, gpu["max_process_fraction"])
                if gpu_fraction < 0.25:
                    raise RuntimeError(
                        "Configured VRAM cap is below M2M100's minimum supported "
                        "GPU allocation fraction of 0.25."
                    )
                result = train_m2m100_lora(
                    workspace,
                    config,
                    model_dir=model_dir,
                    experiment_id=args.run_id or args.experiment_id,
                    resume=args.resume,
                    max_gpu_fraction=gpu_fraction,
                    dataset_id=args.dataset_id,
                    learning_rate=args.learning_rate,
                    num_train_epochs=args.num_train_epochs,
                    lora_rank=args.lora_rank,
                    max_steps=args.max_steps,
                    max_gpu_temperature_c=(
                        args.gpu_max_temp_c
                        if args.gpu_max_temp_c is not None
                        else config.gpu_max_temp_c
                    ),
                )
            except (
                FileNotFoundError,
                FileExistsError,
                ImportError,
                OSError,
                PermissionError,
                RuntimeError,
                ValueError,
            ) as error:
                print(f"Training stopped safely: {error}", file=sys.stderr)
                return 2
            _print_json(result)
            return 0
        from tools.translation_lab.runner import _training_gate

        result = _training_gate(REPOSITORY, config)
        _print_json(result)
        return 0 if result["status"] == "READY" else 2
    if args.command == "train-campaign":
        from tools.translation_lab.m2m100_campaign import run_campaign

        config = load_config(_workspace_config(workspace))
        try:
            result = run_campaign(
                workspace,
                config,
                campaign_id=args.campaign_id,
                model_dir=(
                    workspace
                    / "cache"
                    / "models"
                    / "facebook-m2m100-418M"
                    / "55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636"
                ),
                pilot_steps=args.pilot_steps,
                max_hours=min(args.max_hours, config.max_runtime_hours),
                resume=args.resume,
                dry_run=args.dry_run,
                max_vram_gib=(
                    args.max_vram_gb
                    if args.max_vram_gb is not None
                    else config.max_vram_gib
                ),
                max_temperature_c=(
                    args.gpu_max_temp_c
                    if args.gpu_max_temp_c is not None
                    else config.gpu_max_temp_c
                ),
            )
        except (
            FileNotFoundError,
            ImportError,
            OSError,
            PermissionError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"Training campaign stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        return (
            0 if result["status"] in {"DRY_RUN", "COMPLETED", "NO_IMPROVEMENT"} else 2
        )
    if args.command == "evaluate-candidate":
        from tools.translation_lab.m2m100_training import MODEL_REVISION
        from tools.translation_lab.m2m100_training import evaluate_m2m100_candidate

        model_dir = args.model_dir or (
            workspace / "cache" / "models" / "facebook-m2m100-418M" / MODEL_REVISION
        )
        try:
            from tools.translation_lab.resources import gpu_preflight

            config = load_config(args.config or _workspace_config(workspace))
            gpu = gpu_preflight(
                max_vram_gib=(
                    args.max_vram_gb
                    if args.max_vram_gb is not None
                    else config.max_vram_gib
                ),
                max_temperature_c=(
                    args.gpu_max_temp_c
                    if args.gpu_max_temp_c is not None
                    else config.gpu_max_temp_c
                ),
                minimum_free_gib=config.min_free_vram_gib,
            )
            if gpu["max_process_fraction"] + 0.001 < 0.65:
                raise RuntimeError(
                    "The candidate evaluator's fixed 0.65 VRAM fraction exceeds "
                    "--max-vram-gb; raise the cap or use a compatible evaluator."
                )
            result = evaluate_m2m100_candidate(
                workspace,
                config,
                model_dir=model_dir,
                experiment_id=args.experiment_id,
                dataset_id=args.dataset_id,
                evaluation_dataset_id=args.evaluation_dataset_id,
            )
        except (
            FileNotFoundError,
            ImportError,
            OSError,
            PermissionError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"Candidate evaluation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0
    if args.command == "train-multilingual-candidate":
        from tools.translation_lab.m2m100_multilingual import train_multilingual_lora
        from tools.translation_lab.m2m100_training import MODEL_REVISION

        config = load_config(args.config or _workspace_config(workspace))
        model_dir = args.model_dir or (
            workspace / "cache" / "models" / "facebook-m2m100-418M" / MODEL_REVISION
        )
        try:
            result = train_multilingual_lora(
                workspace,
                config,
                model_dir=model_dir,
                experiment_id=args.experiment_id,
                resume=args.resume,
                max_gpu_fraction=args.max_gpu_fraction,
                learning_rate=args.learning_rate,
                num_train_epochs=args.epochs,
                initial_adapter_experiment_id=args.initial_adapter_experiment_id,
            )
        except (
            FileExistsError,
            FileNotFoundError,
            ImportError,
            OSError,
            PermissionError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"Multilingual training stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0
    if args.command == "evaluate-multilingual-candidate":
        from tools.translation_lab.m2m100_multilingual import evaluate_multilingual_lora
        from tools.translation_lab.m2m100_training import MODEL_REVISION

        config = load_config(args.config or _workspace_config(workspace))
        model_dir = args.model_dir or (
            workspace / "cache" / "models" / "facebook-m2m100-418M" / MODEL_REVISION
        )
        try:
            result = evaluate_multilingual_lora(
                workspace,
                config,
                model_dir=model_dir,
                experiment_id=args.experiment_id,
                run_id=args.run_id,
            )
        except (
            FileExistsError,
            FileNotFoundError,
            ImportError,
            OSError,
            PermissionError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"Multilingual evaluation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0
    if args.command == "evaluate-tico19-french-dev":
        from tools.translation_lab.tico19_french_eval import evaluate_french_dev

        try:
            result = evaluate_french_dev(
                workspace,
                archive_path=args.archive,
                run_id=args.run_id,
                resume=args.resume,
                limit=args.limit,
            )
        except (FileExistsError, OSError, RuntimeError, ValueError) as error:
            print(f"French TICO-19 evaluation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        print(f"French TICO-19 report: {workspace / 'reports' / f'{args.run_id}.json'}")
        return 0
    if args.command == "evaluate-tico19-route-matrix-dev":
        from tools.translation_lab.tico19_french_eval import (
            evaluate_somali_and_pivot_dev,
        )

        try:
            result = evaluate_somali_and_pivot_dev(
                workspace,
                archive_path=args.archive,
                run_id=args.run_id,
                resume=args.resume,
                limit=args.limit,
            )
        except (FileExistsError, OSError, RuntimeError, ValueError) as error:
            print(f"Translation route matrix stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        print(f"Route matrix report: {workspace / 'reports' / f'{args.run_id}.json'}")
        return 0
    if args.command == "evaluate-flores-devtest":
        from tools.translation_lab.flores_eval import evaluate_flores_devtest

        try:
            result = evaluate_flores_devtest(
                workspace,
                archive_path=args.archive,
                run_id=args.run_id,
                resume=args.resume,
            )
        except (FileExistsError, OSError, RuntimeError, ValueError) as error:
            print(f"FLORES-200 evaluation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        print(f"FLORES-200 report: {workspace / 'reports' / f'{args.run_id}.json'}")
        return 0
    if args.command == "evaluate-m2m100-flores-devtest":
        from tools.translation_lab.m2m100_flores_eval import (
            evaluate_m2m100_flores_devtest,
        )

        try:
            result = evaluate_m2m100_flores_devtest(
                workspace,
                archive_path=args.archive,
                experiment_id=args.experiment_id,
                run_id=args.run_id,
                resume=args.resume,
            )
        except (
            FileExistsError,
            ImportError,
            OSError,
            PermissionError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"M2M100 FLORES evaluation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        print(f"M2M100 FLORES report: {workspace / 'reports' / f'{args.run_id}.json'}")
        return 0
    if args.command == "evaluate-marian-flores-devtest":
        from tools.translation_lab.marian_flores_eval import (
            evaluate_marian_flores_devtest,
        )

        try:
            result = evaluate_marian_flores_devtest(
                workspace,
                archive_path=args.archive,
                experiment_id=args.experiment_id,
                run_id=args.run_id,
                resume=args.resume,
            )
        except (
            FileExistsError,
            ImportError,
            OSError,
            PermissionError,
            RuntimeError,
            ValueError,
        ) as error:
            print(f"Marian FLORES evaluation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        print(f"Marian FLORES report: {workspace / 'reports' / f'{args.run_id}.json'}")
        return 0
    if args.command == "prepare":
        catalog = load_catalog(REPOSITORY / "research" / "sources.catalog.json")
        source = next(item for item in catalog if item["source_id"] == args.source)
        artifact = source["artifacts"][0]
        cached_file = workspace / "cache/downloads" / artifact["sha256"] / "artifact"
        if not cached_file.is_file():
            print(
                "Pinned corpus is not downloaded yet. Review the source record, "
                "approve it in the private workspace registry and run download.",
                file=sys.stderr,
            )
            return 2
        try:
            if args.source == "google-smol-en-so":
                result = prepare_google_smol(cached_file, workspace)
            else:
                from tools.translation_lab.prepare_paracrawl import (
                    prepare_parallel_parquet,
                )

                result = prepare_parallel_parquet(
                    cached_file,
                    workspace,
                    source_id=args.source,
                    tico_test=REPOSITORY
                    / "tests/data/somali_translation_tico19_test_150.jsonl",
                )
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            print(f"Corpus preparation stopped safely: {error}", file=sys.stderr)
            return 2
        _print_json(result)
        return 0
    if args.command in {
        "export",
        "propose",
        "promote",
        "rollback",
    }:
        print(
            f"{args.command} is safely gated: no owner-approved training source "
            "or promotion candidate is available. "
            "No data, model, or production files were changed.",
            file=sys.stderr,
        )
        return 2
    return 2


def _run(args, workspace: Path, *, resume: bool) -> int:
    config_path = args.config or _workspace_config(workspace)
    try:
        config = load_config(config_path)
        if resume:
            from tools.translation_lab.state import read_json

            saved = read_json(workspace / "locks" / "active_run.json")
            if not saved or not saved.get("effective_config"):
                raise ValueError("No saved run configuration is available to resume.")
            config = LabConfig(**saved["effective_config"]).validate()
        else:
            overrides = {}
            if args.script_checks is not None:
                overrides["script_checks"] = args.script_checks
            if args.translation_samples is not None:
                overrides["translation_samples"] = args.translation_samples
            config = replace(config, **overrides).validate()
        result = run_overnight(
            REPOSITORY,
            workspace,
            config_path,
            config,
            resume=resume,
            recover_stale_lock=args.recover_stale_lock,
        )
    except PauseRun as error:
        print(str(error))
        return 3
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Research run could not complete: {error}", file=sys.stderr)
        return 2
    _print_json(result)
    print(f"Latest report: {workspace / 'reports' / 'latest.md'}")
    return 0 if result["status"] in {"COMPLETED", "COMPLETED_WITH_BLOCKERS"} else 2


def _sources(action: str, workspace: Path) -> int:
    catalog = load_catalog(REPOSITORY / "research" / "sources.catalog.json")
    active_config = workspace / "config" / "active.toml"
    config = load_config(active_config if active_config.is_file() else DEFAULT_CONFIG)
    registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
    registry_by_id = {source["source_id"]: source for source in registry}
    approved_count = 0

    for source in catalog:
        print(
            f"{source['source_id']}: {source['title']} | {source['license']} | "
            f"{source['rights_status']} | split={source['split_role']}"
        )
        print(f"  {source['source_page']}")
        if action == "verify":
            from tools.translation_lab.sources import verify_approved_source

            approved_source = registry_by_id.get(source["source_id"])
            if approved_source is None:
                print("  BLOCKED: No matching private approval record.")
                continue
            try:
                verify_approved_source(
                    approved_source,
                    set(config.approved_source_ids),
                    allow_noncommercial=config.allow_noncommercial_training,
                )
            except PermissionError as error:
                print(f"  BLOCKED: {error}")
            else:
                approved_count += 1
                print("  APPROVED for configured training use.")

    if action != "verify":
        return 0
    if not approved_count:
        print("No private source record is approved for training.")
        return 2
    print(f"Verified {approved_count} approved private training source(s).")
    return 0


def _source_gate_summary(workspace: Path, config: LabConfig) -> dict:
    catalog = load_catalog(REPOSITORY / "research" / "sources.catalog.json")
    registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
    by_id = {source.get("source_id"): source for source in registry}
    approvals = set(config.approved_source_ids)
    approved = []
    blocked = []
    from tools.translation_lab.sources import verify_approved_source

    for source_id in sorted(approvals):
        entry = by_id.get(source_id)
        if entry is None:
            blocked.append(
                {"source_id": source_id, "reason": "missing private registry record"}
            )
            continue
        try:
            verify_approved_source(
                entry,
                approvals,
                purpose="train",
                allow_noncommercial=config.allow_noncommercial_training,
            )
        except PermissionError as error:
            blocked.append({"source_id": source_id, "reason": str(error)})
        else:
            approved.append(source_id)
    return {
        "approved_for_training": approved,
        "blocked_configured_sources": blocked,
        "catalog_source_count": len(catalog),
        "unknown_rights_are_blocked": True,
    }


def _download(args, workspace: Path) -> int:
    try:
        config_path = args.config or _workspace_config(workspace)
        config = load_config(config_path)
        max_download_gib = (
            args.max_download_gb
            if args.max_download_gb is not None
            else config.max_download_gib
        )
        max_disk_gib = (
            args.max_disk_gb if args.max_disk_gb is not None else config.max_disk_gib
        )
        config = replace(
            config,
            max_download_gib=max_download_gib,
            max_disk_gib=max_disk_gib,
            max_single_download_gib=min(
                config.max_single_download_gib, max_download_gib
            ),
        ).validate()
        initialize_workspace(workspace, REPOSITORY, config_path)
        registry = read_owner_registry(workspace / "registry" / "sources.jsonl")
        approved_ids = set(config.approved_source_ids)
        selected = [
            source
            for source in registry
            if source.get("source_id") in approved_ids
            and source.get("owner_approved") is True
        ]
        artifacts = [
            (source, artifact)
            for source in selected
            for artifact in source.get("artifacts", [])
        ]
        total_bytes = sum(
            artifact.get("expected_bytes", -1) for _, artifact in artifacts
        )
        if not artifacts:
            raise ValueError(
                "No pinned artifacts are both owner-approved in the local registry "
                "and listed in approved_source_ids. No network request was made."
            )
        if total_bytes <= 0 or total_bytes > config.max_download_gib * 1024**3:
            raise ValueError(
                "Selected downloads exceed the configured total byte budget."
            )
        from tools.translation_lab.resources import assert_workspace_disk_budget

        assert_workspace_disk_budget(
            workspace,
            additional_bytes=total_bytes,
            maximum_gib=config.max_disk_gib,
        )
        disk = shutil.disk_usage(workspace)
        minimum_free = config.keep_free_disk_gib * 1024**3
        if disk.free - total_bytes < minimum_free:
            raise ValueError(
                "Download would use the configured keep-free disk reserve."
            )

        downloaded = []
        for source, artifact in artifacts:
            filename = Path(str(artifact.get("filename", "artifact"))).name
            if not filename or filename in {".", ".."}:
                raise ValueError("Invalid artifact filename in owner registry.")
            spec = DownloadSpec(
                source=source,
                url=artifact["url"],
                sha256=artifact["sha256"],
                expected_bytes=artifact["expected_bytes"],
                purpose=artifact.get("purpose", "train"),
            )
            cached = download_approved(
                spec,
                workspace / "cache" / "downloads",
                set(config.allowed_download_hosts),
                approved_ids,
                max_bytes=int(config.max_single_download_gib * 1024**3),
                allow_noncommercial=config.allow_noncommercial_training,
            )
            downloaded.append(
                {
                    "source_id": source["source_id"],
                    "revision": source.get("revision"),
                    "purpose": spec.purpose,
                    "filename": filename,
                    "bytes": cached.stat().st_size,
                    "sha256": spec.sha256.lower(),
                    "cache_key": spec.sha256.lower(),
                }
            )
        receipt = workspace / "registry" / "downloads.jsonl"
        old_receipts = receipt.read_text(encoding="utf-8") if receipt.exists() else ""
        new_receipts = "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
            for item in downloaded
        )
        temporary = receipt.with_suffix(".jsonl.tmp")
        temporary.write_text(old_receipts + new_receipts, encoding="utf-8")
        temporary.replace(receipt)
    except (OSError, RuntimeError, ValueError, KeyError, PermissionError) as error:
        print(f"Download stopped safely: {error}", file=sys.stderr)
        return 2
    _print_json({"downloaded_artifacts": downloaded})
    return 0


def _leaderboard(workspace: Path, *, verified_only: bool) -> None:
    reports = list((workspace / "reports").glob("*.json"))
    reports.extend((workspace / "experiments").glob("*/*dev*.json"))
    entries = []
    for path in reports:
        if path.name.endswith("-predictions.json"):
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        overlap = item.get("exact_training_overlap", {})
        verified = (
            item.get("status") == "PRIVATE_DEV_EVALUATION_ONLY"
            and item.get("split") == "dev"
            and item.get("row_count", 0) > 0
            and overlap
            and all(value == 0 for value in overlap.values())
            and isinstance(item.get("metrics"), dict)
        )
        if verified_only and not verified:
            continue
        if verified:
            entries.append(
                {
                    "experiment_id": item.get("experiment_id"),
                    "model_id": item.get("model_id"),
                    "split": item.get("split"),
                    "rows": item.get("row_count"),
                    "metrics": item["metrics"],
                    "report": str(path),
                    "human_review": item.get("human_review"),
                    "status": item.get("status"),
                }
            )
    entries.sort(key=lambda entry: entry.get("experiment_id") or "")
    _print_json(
        {
            "verified_only": verified_only,
            "count": len(entries),
            "candidates": entries,
            "promotion": "never automatic; dev metrics are not final approval",
        }
    )


def _run_report(workspace: Path, run_id: str) -> None:
    from tools.translation_lab.independent_runner import _validate_run_id

    _validate_run_id(run_id)
    smoke = workspace / "runs" / run_id / "training-smoke.json"
    if smoke.is_file():
        _print_json(json.loads(smoke.read_text(encoding="utf-8")))
        return
    database = workspace / "runs" / run_id / "run_state.sqlite"
    if database.is_file():
        import sqlite3

        with sqlite3.connect(database) as db:
            run = db.execute(
                "SELECT run_id,seed,target,status,created FROM runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if run is None:
                raise ValueError(f"No run named {run_id}")
            count, passed, failed, unique_inputs = db.execute(
                "SELECT COUNT(*),SUM(status='PASS'),SUM(status='FAIL'),"
                "COUNT(DISTINCT input_hash) FROM cases WHERE run_id=?",
                (run_id,),
            ).fetchone()
        _print_json(
            {
                "run_id": run[0],
                "seed": run[1],
                "target": run[2],
                "status": run[3],
                "created_utc_epoch": run[4],
                "attempted": count,
                "completed": count,
                "passed": passed or 0,
                "failed": failed or 0,
                "unique_case_ids": count,
                "unique_inputs": unique_inputs or 0,
                "database": str(database),
            }
        )
        return
    raise ValueError(f"No local run report named {run_id}")


def _print_json(value: dict, path: Path | None = None) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered)
    if path is not None:
        from tools.translation_lab.state import atomic_json

        atomic_json(path, value)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _workspace_config(workspace: Path) -> Path:
    active = workspace / "config" / "active.toml"
    return active if active.is_file() else DEFAULT_CONFIG


if __name__ == "__main__":
    raise SystemExit(main())
