# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise private research workspaces, gates, download integrity and recovery."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.local_translation_lab import build_parser
from tools.local_translation_lab import main
from tools.translation_lab.config import LabConfig
from tools.translation_lab.config import load_config
from tools.translation_lab.downloader import DownloadSpec
from tools.translation_lab.downloader import download_approved
from tools.translation_lab.m2m100_training import bidirectional_examples
from tools.translation_lab.marian_candidate import _matches_pin
from tools.translation_lab.marian_candidate import (
    _tokenize_rows as tokenize_marian_rows,
)
from tools.translation_lab.marian_candidate import build_parser as build_marian_parser
from tools.translation_lab.marian_candidate import verify_model_bundle
from tools.translation_lab.mixture_data import _revision_for
from tools.translation_lab.mixture_data import _weight_training_rows
from tools.translation_lab.mixture_data import _write_split
from tools.translation_lab.mixture_data import prepare_marian_mixture
from tools.translation_lab.prepare_data import _assign_splits
from tools.translation_lab.prepare_data import _duplicate_components
from tools.translation_lab.prepare_paracrawl import _usable_pair
from tools.translation_lab.runner import run_overnight
from tools.translation_lab.somali_reverse_screen import (
    MODEL_FILES as REVERSE_MODEL_FILES,
)
from tools.translation_lab.somali_reverse_screen import (
    _matches_pin as reverse_model_matches_pin,
)
from tools.translation_lab.somali_reverse_screen import _reverse_rows
from tools.translation_lab.somali_reverse_screen import (
    build_parser as build_reverse_parser,
)
from tools.translation_lab.sources import load_catalog
from tools.translation_lab.sources import verify_approved_source
from tools.translation_lab.state import RunLock
from tools.translation_lab.state import checkpoint
from tools.translation_lab.state import new_run
from tools.translation_lab.state import pause_requested
from tools.translation_lab.state import read_json
from tools.translation_lab.state import request_pause
from tools.translation_lab.transliteration_eval import evaluate_script_cases
from tools.translation_lab.transliteration_eval import verify_static_evidence
from tools.translation_lab.workspace import ensure_outside_repository
from tools.translation_lab.workspace import initialize_workspace

REPOSITORY = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, body, status=200, headers=None, url="https://example.org/file"):
        self.stream = io.BytesIO(body)
        self.status = status
        self.headers = headers or {}
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def read(self, size=-1):
        return self.stream.read(size)

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status


class TrainingExampleTests(unittest.TestCase):
    def test_training_and_candidate_evaluation_arguments_parse(self):
        train = build_parser().parse_args(
            [
                "train",
                "--execute",
                "--resume",
                "--experiment-id",
                "resume-check",
            ]
        )
        evaluate = build_parser().parse_args(
            [
                "evaluate-candidate",
                "--experiment-id",
                "resume-check",
                "--dataset-id",
                "opus-paracrawl-en-so",
                "--evaluation-dataset-id",
                "google-smol-en-so",
            ]
        )
        prepare = build_parser().parse_args(
            ["prepare", "--source", "opus-infopankki-en-so"]
        )

        self.assertTrue(train.execute)
        self.assertTrue(train.resume)
        self.assertEqual(train.experiment_id, "resume-check")
        self.assertEqual(evaluate.experiment_id, "resume-check")
        self.assertEqual(evaluate.dataset_id, "opus-paracrawl-en-so")
        self.assertEqual(evaluate.evaluation_dataset_id, "google-smol-en-so")
        self.assertEqual(prepare.source, "opus-infopankki-en-so")

    def test_marian_file_pin_checks_size_and_git_blob_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model-file"
            content = b"pinned test payload"
            path.write_bytes(content)
            digest = hashlib.sha1(
                f"blob {len(content)}\0".encode() + content
            ).hexdigest()

            self.assertTrue(_matches_pin(path, (len(content), "git", digest)))
            self.assertFalse(_matches_pin(path, (len(content) + 1, "git", digest)))
            self.assertFalse(_matches_pin(path, (len(content), "git", "0" * 40)))

    def test_marian_learning_rate_is_explicit_and_defaults_to_baseline(self):
        default = build_marian_parser().parse_args(["--experiment-id", "baseline"])
        reduced = build_marian_parser().parse_args(
            ["--experiment-id", "reduced-lr", "--learning-rate", "5e-5"]
        )
        training_only = build_marian_parser().parse_args(
            ["--experiment-id", "training-only", "--skip-evaluation"]
        )
        targeted_evaluation = build_marian_parser().parse_args(
            [
                "--experiment-id",
                "targeted-evaluation",
                "--evaluate-only",
                "--evaluation-dataset",
                "combined-corpus-heldout",
            ]
        )

        self.assertEqual(default.learning_rate, 1e-4)
        self.assertEqual(reduced.learning_rate, 5e-5)
        self.assertTrue(training_only.skip_evaluation)
        self.assertEqual(
            targeted_evaluation.evaluation_dataset,
            ["combined-corpus-heldout"],
        )

    def test_marian_tokenization_uses_forward_pairs_only(self):
        class FakeTokenizer:
            def __call__(self, source, *, text_target, **kwargs):
                return {
                    "input": source,
                    "target": text_target,
                    "max_length": kwargs["max_length"],
                }

        examples = tokenize_marian_rows(
            [
                {
                    "source_text": "Good morning.",
                    "target_text": "Subax wanaagsan.",
                }
            ],
            FakeTokenizer(),
        )

        self.assertEqual(
            examples,
            [
                {
                    "input": "Good morning.",
                    "target": "Subax wanaagsan.",
                    "max_length": 256,
                }
            ],
        )

    def test_marian_bundle_rejects_an_incomplete_download(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaisesRegex(ValueError, r"\.gitattributes"),
        ):
            verify_model_bundle(Path(temporary))

    def test_mixture_requires_each_source_approval_before_reading_data(self):
        config = LabConfig(
            training_enabled=True,
            approved_source_ids=("opus-infopankki-en-so",),
        )

        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaisesRegex(PermissionError, "explicit private approval"),
        ):
            prepare_marian_mixture(Path(temporary), config)

    def test_expands_approved_pair_in_both_directions(self):
        examples = bidirectional_examples(
            [{"source_text": "Good morning", "target_text": "Subax wanaagsan"}]
        )

        self.assertEqual(
            examples,
            [
                {
                    "source_text": "Good morning",
                    "target_text": "Subax wanaagsan",
                    "source_language": "en",
                    "target_language": "so",
                },
                {
                    "source_text": "Subax wanaagsan",
                    "target_text": "Good morning",
                    "source_language": "so",
                    "target_language": "en",
                },
            ],
        )

    def test_rejects_empty_or_malformed_pairs(self):
        with self.assertRaises(ValueError):
            bidirectional_examples([{"source_text": " ", "target_text": "Salaan"}])
        with self.assertRaises(TypeError):
            bidirectional_examples([{"source_text": "Hello", "target_text": None}])

    def test_paracrawl_filter_rejects_markup_and_unbalanced_pairs(self):
        self.assertIsNone(
            _usable_pair(
                {"translation": {"en": "Visit https://example.org", "so": "Booqo"}}
            )
        )
        self.assertIsNone(
            _usable_pair(
                {
                    "translation": {
                        "en": "A significantly longer English phrase",
                        "so": "Haa",
                    }
                }
            )
        )
        self.assertEqual(
            _usable_pair(
                {
                    "translation": {
                        "en": "A clear sentence for the reader.",
                        "so": "Weedh cad oo akhristaha loogu talagalay.",
                    }
                }
            ),
            (
                "A clear sentence for the reader.",
                "Weedh cad oo akhristaha loogu talagalay.",
            ),
        )

    def test_parquet_filter_drops_long_non_english_text_and_keeps_somali(self):
        somali = (
            "Waxbarashada carruurta waxay ka dhacdaa dugsiyada, waalidkuna "
            "waxay la xiriiraan macallimiinta si joogto ah."
        )
        self.assertIsNone(
            _usable_pair(
                {
                    "translation": {
                        "en": "Bonjour, ceci est une longue phrase française qui "
                        "décrit la vie quotidienne dans la ville.",
                        "so": somali,
                    }
                }
            )
        )
        self.assertEqual(
            _usable_pair(
                {
                    "translation": {
                        "en": "Children's education takes place in schools, and "
                        "parents communicate regularly with their teachers.",
                        "so": somali,
                    }
                }
            )[1],
            somali,
        )

    def test_parquet_filter_drops_merged_navigation_labels(self):
        somali = "Waxbarashada carruurta waxay ka dhacdaa dugsiyada."
        self.assertIsNone(
            _usable_pair(
                {
                    "translation": {
                        "en": "Activities for young peopleFinnish _ Swedish _ English",
                        "so": "Waxqabadka dhalinyarada Finnish _ Swedish _ English",
                    }
                }
            )
        )

        self.assertIsNotNone(
            _usable_pair(
                {
                    "translation": {
                        "en": "Finnish schools offer support to families.",
                        "so": somali,
                    }
                }
            )
        )

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status


class TranslationLabTests(unittest.TestCase):
    def test_one_command_campaign_runs_marian_mixture_and_script_checks(self):
        command = (REPOSITORY / "tools" / "run_somali_marian_experiment.cmd").read_text(
            encoding="utf-8"
        )

        self.assertIn("--count 1000000", command)
        self.assertIn("--dataset-id marian-mixture", command)
        self.assertIn("SAYLACIAN_EXPERIMENT_ID=marian-mixture-%%i", command)

    def test_full_translation_campaign_runs_both_directions(self):
        command = (
            REPOSITORY / "tools" / "run_full_somali_translation_campaign.cmd"
        ).read_text(encoding="utf-8")

        self.assertIn("run_somali_marian_experiment.cmd", command)
        self.assertIn("somali_reverse_screen --train-mixture", command)

    def test_explicit_google_weighting_only_repeats_assigned_training_rows(self):
        rows = [
            {"source_id": "google-smol-en-so", "source_text": "one"},
            {"source_id": "opus-infopankki-en-so", "source_text": "two"},
        ]

        with patch(
            "tools.translation_lab.mixture_data.TRAIN_SAMPLE_MULTIPLIERS",
            {"google-smol-en-so": 2},
        ):
            weighted = _weight_training_rows(rows)

        self.assertEqual(len(weighted), 3)
        self.assertEqual(
            sum(row["source_id"] == "google-smol-en-so" for row in weighted), 2
        )
        self.assertEqual(
            sum(row["source_id"] == "opus-infopankki-en-so" for row in weighted), 1
        )

    def test_default_mixture_keeps_training_rows_unweighted(self):
        rows = [
            {"source_id": "google-smol-en-so", "source_text": "one"},
            {"source_id": "opus-infopankki-en-so", "source_text": "two"},
        ]

        self.assertEqual(_weight_training_rows(rows), rows)

    def test_dataset_revision_changes_with_builder_identity(self):
        base = {"sources": {"small-set": "abc"}, "builder_sha256": "first"}
        changed = {**base, "builder_sha256": "second"}

        self.assertNotEqual(_revision_for(base), _revision_for(changed))

    def test_prepared_split_cannot_be_overwritten_with_different_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "train.jsonl"
            path.write_text('{"old": true}\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "immutable dataset split"):
                _write_split(path, [{"new": True}])

            self.assertEqual(path.read_text(encoding="utf-8"), '{"old": true}\n')

    def test_reverse_candidate_defaults_to_a_private_one_epoch_run(self):
        args = build_reverse_parser().parse_args(["--train-mixture"])
        self.assertTrue(args.train_mixture)
        self.assertEqual(args.epochs, 1)
        self.assertIsNone(args.experiment_id)

    def test_reverse_model_accepts_a_matching_git_blob_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model-file"
            payload = b"pinned test payload"
            path.write_bytes(payload)
            digest = hashlib.sha1(
                f"blob {len(payload)}\0".encode() + payload
            ).hexdigest()
            self.assertTrue(
                reverse_model_matches_pin(path, (len(payload), "git", digest))
            )

    def test_reverse_model_rejects_modified_pinned_bundle_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "model-file"
            path.write_bytes(b"not the model")
            self.assertFalse(
                reverse_model_matches_pin(path, REVERSE_MODEL_FILES["config.json"])
            )

    def test_reverse_route_flips_only_the_translation_direction(self):
        rows = [{"source_text": "Maalin wanaagsan", "target_text": "Good day"}]
        self.assertEqual(
            _reverse_rows(rows),
            [{"source_text": "Good day", "target_text": "Maalin wanaagsan"}],
        )

    def test_default_transliteration_budget_is_one_million(self):
        self.assertEqual(LabConfig().validate().script_checks, 1_000_000)
        arguments = build_parser().parse_args(["test-scripts"])
        self.assertEqual(arguments.count, 1_000_000)

    def test_source_verification_reads_private_config_and_registry(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            config_dir = workspace / "config"
            registry_dir = workspace / "registry"
            config_dir.mkdir()
            registry_dir.mkdir()
            (config_dir / "active.toml").write_text(
                'approved_source_ids = ["google-smol-en-so"]\n'
                "training_enabled = true\n",
                encoding="utf-8",
            )
            source = {
                "source_id": "google-smol-en-so",
                "owner_approved": True,
                "gated": False,
                "rights_status": "verified",
                "split_role": "train",
                "license": "CC-BY-4.0",
                "rights": {"download": "allowed", "train": "allowed"},
            }
            (registry_dir / "sources.jsonl").write_text(
                json.dumps(source) + "\n", encoding="utf-8"
            )
            output = StringIO()
            with redirect_stdout(output):
                result = main(["--workspace", str(workspace), "sources", "verify"])

        self.assertEqual(result, 0)
        self.assertIn("APPROVED for configured training use", output.getvalue())

    def test_config_rejects_unknown_keys_and_unsafe_training(self):
        with tempfile.TemporaryDirectory() as temporary:
            config_file = Path(temporary) / "bad.toml"
            config_file.write_text(
                "version=1\nallow_everything=true\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "Unknown configuration keys"):
                load_config(config_file)
        with self.assertRaisesRegex(ValueError, "approved source IDs"):
            LabConfig(training_enabled=True).validate()
        with self.assertRaisesRegex(ValueError, "Automatic promotion"):
            LabConfig(automatic_promotion=True).validate()

    def test_workspace_is_outside_repo_and_init_does_not_overwrite_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "project"
            workspace = root / "private-lab"
            repo.mkdir()
            template = repo / "template.toml"
            template.write_text("version=1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside the repository"):
                ensure_outside_repository(repo / "research" / "private", repo)
            config_path = initialize_workspace(workspace, repo, template)
            config_path.write_text("owner setting\n", encoding="utf-8")
            initialize_workspace(workspace, repo, template)
            self.assertEqual(config_path.read_text(encoding="utf-8"), "owner setting\n")
            self.assertTrue((workspace / "data/test").is_dir())

    def test_catalog_only_allows_verified_owner_approved_training_sources(self):
        catalog = load_catalog(REPOSITORY / "research" / "sources.catalog.json")
        sources = {item["source_id"]: item for item in catalog}
        self.assertIn("google-smol-en-so", sources)
        self.assertEqual(sources["opus-infopankki-en-so"]["license"], "CC-BY-4.0")
        self.assertFalse(sources["opus-infopankki-en-so"]["owner_approved"])
        self.assertIn("tufaax-en-so-parallel-clean-8k", sources)
        self.assertEqual(
            sources["tufaax-en-so-parallel-clean-8k"]["rights_status"],
            "provenance_unresolved",
        )
        mt560 = sources["opus-mt560-en-so-hf-mirror"]
        self.assertEqual(mt560["revision"], "833f5c69d63c15eaf6b8d8d86620b74fd08e6d00")
        self.assertFalse(mt560["owner_approved"])
        self.assertTrue(
            all(value == "approval_required" for value in mt560["rights"].values())
        )
        with self.assertRaises(PermissionError):
            verify_approved_source(sources["google-smol-en-so"], {"google-smol-en-so"})
        with self.assertRaises(PermissionError):
            verify_approved_source(
                sources["tufaax-en-so-parallel-clean-8k"],
                {"tufaax-en-so-parallel-clean-8k"},
            )
        with self.assertRaises(PermissionError):
            verify_approved_source(mt560, {"opus-mt560-en-so-hf-mirror"})

    def test_downloader_verifies_bytes_and_hash_before_activation(self):
        payload = b"approved test fixture\n"
        digest = hashlib.sha256(payload).hexdigest()
        source = {
            "source_id": "fixture",
            "owner_approved": True,
            "gated": False,
            "rights_status": "verified",
            "split_role": "train",
            "rights": {"download": "allowed", "train": "allowed"},
        }
        spec = DownloadSpec(source, "https://example.org/file", digest, len(payload))
        with tempfile.TemporaryDirectory() as temporary:
            result = download_approved(
                spec,
                Path(temporary),
                {"example.org"},
                {"fixture"},
                1000,
                retries=0,
                opener=lambda *args, **kwargs: FakeResponse(
                    payload,
                    headers={"Content-Length": str(len(payload)), "ETag": '"v1"'},
                ),
            )
            self.assertEqual(result.read_bytes(), payload)
            self.assertEqual(result.name, "artifact")

    def test_downloader_rejects_wrong_hash_redirect_and_unknown_rights(self):
        payload = b"bad fixture"
        source = {
            "source_id": "fixture",
            "owner_approved": True,
            "gated": False,
            "rights_status": "verified",
            "split_role": "train",
            "rights": {"download": "allowed", "train": "allowed"},
        }
        spec = DownloadSpec(source, "https://example.org/file", "0" * 64, len(payload))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                download_approved(
                    spec,
                    Path(temporary),
                    {"example.org"},
                    {"fixture"},
                    1000,
                    retries=0,
                    opener=lambda *args, **kwargs: FakeResponse(payload),
                )
            self.assertFalse(list(Path(temporary).rglob("artifact")))
            with self.assertRaisesRegex(ValueError, "allowlist"):
                download_approved(
                    DownloadSpec(
                        source, "https://other.example/file", "0" * 64, len(payload)
                    ),
                    Path(temporary),
                    {"example.org"},
                    {"fixture"},
                    1000,
                    retries=0,
                )
            with self.assertRaisesRegex(ValueError, "allowlist"):
                download_approved(
                    DownloadSpec(source, spec.url, hashlib.sha256(b"x").hexdigest(), 1),
                    Path(temporary),
                    {"example.org"},
                    {"fixture"},
                    1000,
                    retries=0,
                    opener=lambda *args, **kwargs: FakeResponse(
                        b"x", url="https://127.0.0.1/private"
                    ),
                )
            unapproved = {**source, "rights_status": "pending_review"}
            with self.assertRaises(PermissionError):
                download_approved(
                    DownloadSpec(
                        unapproved, spec.url, spec.sha256, spec.expected_bytes
                    ),
                    Path(temporary),
                    {"example.org"},
                    {"fixture"},
                    1000,
                    retries=0,
                )

    def test_downloader_resumes_only_matching_etag_and_range(self):
        payload = b"complete fixture"
        prefix = payload[:8]
        suffix = payload[8:]
        digest = hashlib.sha256(payload).hexdigest()
        source = {
            "source_id": "fixture",
            "owner_approved": True,
            "gated": False,
            "rights_status": "verified",
            "split_role": "train",
            "rights": {"download": "allowed", "train": "allowed"},
        }
        spec = DownloadSpec(source, "https://example.org/file", digest, len(payload))
        with tempfile.TemporaryDirectory() as temporary:
            partial_dir = Path(temporary) / digest
            partial_dir.mkdir()
            (partial_dir / "artifact.part").write_bytes(prefix)
            (partial_dir / "artifact.part.json").write_text(
                json.dumps({"url": spec.url, "sha256": digest, "etag": '"same"'}),
                encoding="utf-8",
            )

            def opener(request, timeout):
                self.assertEqual(request.get_header("Range"), f"bytes={len(prefix)}-")
                return FakeResponse(
                    suffix,
                    status=206,
                    headers={
                        "ETag": '"same"',
                        "Content-Range": (
                            f"bytes {len(prefix)}-{len(payload) - 1}/{len(payload)}"
                        ),
                        "Content-Length": str(len(suffix)),
                    },
                )

            result = download_approved(
                spec,
                Path(temporary),
                {"example.org"},
                {"fixture"},
                1000,
                retries=0,
                opener=opener,
            )
            self.assertEqual(result.read_bytes(), payload)

    def test_atomic_checkpoint_and_pause_flag(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            state_path = workspace / "locks" / "active_run.json"
            state = new_run("config-hash", "source-hash", {})
            checkpoint(state_path, state, stage="PREFLIGHT")
            self.assertEqual(read_json(state_path)["revision"], 1)
            request_pause(workspace)
            self.assertTrue(pause_requested(workspace))
            self.assertFalse(list((workspace / "locks").glob("*.tmp")))

    def test_lock_prevents_parallel_runner_and_preserves_stale_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            with (
                RunLock(workspace),
                self.assertRaisesRegex(RuntimeError, "already holds the lock"),
            ):
                RunLock(workspace).__enter__()
            lock = workspace / "locks" / "active.lock"
            lock.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "stale run lock"):
                RunLock(workspace).__enter__()
            with RunLock(workspace, recover_stale=True):
                self.assertTrue(list((workspace / "locks").glob("active.stale-*.lock")))

    def test_script_suite_checks_real_maps_and_reports_honest_counts(self):
        evidence = verify_static_evidence()
        self.assertEqual(evidence["old_nubian_entries_verified"], 29)
        result = evaluate_script_cases(1000, seed=42)
        self.assertEqual(result["generated_checks"], 1000)
        self.assertEqual(result["executed_checks"], 1000)
        self.assertEqual(result["reference_scored_translations"], 0)
        self.assertGreaterEqual(result["unique_case_ids"], 900)
        self.assertEqual(result["failure_count"], 0)

    def test_parallel_data_split_keeps_repeated_sentences_in_one_group(self):
        rows = [
            {"record_id": 1, "source_text": "Hello.", "target_text": "Salaan."},
            {"record_id": 2, "source_text": "hello.", "target_text": "Nabad."},
            {
                "record_id": 3,
                "source_text": "Good day.",
                "target_text": "Maalin wanaagsan.",
            },
            {
                "record_id": 4,
                "source_text": "Good evening.",
                "target_text": "Fiid wanaagsan.",
            },
            {
                "record_id": 5,
                "source_text": "Good night.",
                "target_text": "Habeen wanaagsan.",
            },
            {"record_id": 6, "source_text": "Welcome.", "target_text": "Soo dhowow."},
            {"record_id": 7, "source_text": "Farewell.", "target_text": "Nabad gelyo."},
        ]
        groups = _duplicate_components(rows)
        self.assertEqual(len(groups), 6)
        self.assertEqual(len(groups[0]), 2)
        splits = _assign_splits(groups)
        locations = {
            row["record_id"]: split
            for split, split_rows in splits.items()
            for row in split_rows
        }
        self.assertEqual(locations[1], locations[2])
        self.assertEqual(set(locations), set(range(1, 8)))

    def test_noncommercial_training_requires_explicit_config_permission(self):
        source = {
            "source_id": "nc-corpus",
            "owner_approved": True,
            "gated": False,
            "rights_status": "verified",
            "split_role": "train",
            "license": "CC-BY-NC-4.0",
            "rights": {"download": "allowed", "train": "allowed"},
        }
        with self.assertRaisesRegex(PermissionError, "Noncommercial"):
            verify_approved_source(source, {"nc-corpus"})
        verify_approved_source(
            source,
            {"nc-corpus"},
            allow_noncommercial=True,
        )

    def test_overnight_checkpoint_recovery_skips_completed_stage(self):
        config_path = REPOSITORY / "research" / "translation_lab.example.toml"
        config = LabConfig(script_checks=20, translation_samples=0)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "lab"
            with patch(
                "tools.translation_lab.runner.build_inventory",
                return_value={"ready": True},
            ):
                with self.assertRaisesRegex(RuntimeError, "Injected recovery"):
                    run_overnight(
                        REPOSITORY,
                        workspace,
                        config_path,
                        config,
                        fault_after="script-evaluation",
                    )
                before = read_json(workspace / "locks" / "active_run.json")
                script_timestamp = before["completed_steps"]["script-evaluation"][
                    "completed_utc"
                ]
                result = run_overnight(
                    REPOSITORY,
                    workspace,
                    config_path,
                    config,
                    resume=True,
                )
            after = read_json(workspace / "locks" / "active_run.json")
            self.assertEqual(result["status"], "COMPLETED_WITH_BLOCKERS")
            self.assertEqual(
                after["completed_steps"]["script-evaluation"]["completed_utc"],
                script_timestamp,
            )
            self.assertTrue((workspace / "reports" / "latest.md").is_file())


if __name__ == "__main__":
    unittest.main()
