# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools import benchmark_somali_en_candidate as candidate_tool
from tools.benchmark_output import (
    ROOT,
    checkpoint_for,
    new_benchmark_output,
    require_external_output,
)
from tools.benchmark_somali_quality import (
    en_to_so_route_audit,
    load_checkpoint,
    save_checkpoint,
    save_result,
)


class SomaliBenchmarkOutputTests(unittest.TestCase):
    def test_default_predictions_and_checkpoints_are_unique_and_external(self):
        first = new_benchmark_output("somali-test")
        second = new_benchmark_output("somali-test")

        self.assertNotEqual(first, second)
        for output in (first, second):
            self.assertEqual(require_external_output(output), output.resolve())
            self.assertEqual(
                require_external_output(checkpoint_for(output)),
                checkpoint_for(output).resolve(),
            )

    def test_repository_output_paths_are_rejected_before_writing(self):
        output = ROOT / "docs" / "must-not-contain-predictions.json"
        with self.assertRaisesRegex(ValueError, "outside the source repository"):
            require_external_output(output)
        with self.assertRaisesRegex(ValueError, "outside the source repository"):
            save_result(output, {"prediction": "must not be written"})
        self.assertFalse(output.exists())

    def test_selected_external_checkpoint_resumes_only_matching_run(self):
        outputs = {"en_so": [{"text": "test output"}], "so_en": []}
        with tempfile.TemporaryDirectory() as temporary_directory:
            checkpoint = Path(temporary_directory) / "checkpoint.json"
            save_checkpoint(
                "baseline",
                "data-hash",
                None,
                outputs,
                1.5,
                1,
                150,
                checkpoint_path=checkpoint,
            )
            restored = load_checkpoint(
                "baseline", "data-hash", checkpoint_path=checkpoint
            )
            self.assertEqual(restored["samples"], outputs)
            self.assertEqual(restored["completed_pairs"], 1)
            rejected = load_checkpoint(
                "baseline", "different-data", checkpoint_path=checkpoint
            )
            self.assertEqual(rejected["samples"], {"en_so": [], "so_en": []})

    def test_candidate_merge_preserves_baseline_metadata_and_route_audit(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            model = root / "model"
            model.mkdir()
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (model / filename).write_text("fixture", encoding="utf-8")
            data = root / "samples.jsonl"
            data.write_text(
                "\n".join(
                    json.dumps(
                        {
                            "id": str(index),
                            "source_en": "sample",
                            "reference_so": "reference",
                        }
                    )
                    for index in range(150)
                ),
                encoding="utf-8",
            )
            baseline = {
                "model": "preserve baseline provenance",
                "en_to_so_route_audit": {"synthetic_candidate_selected_samples": 97},
                "samples": {"en_so": [{"text": "baseline"} for _ in range(150)]},
            }
            results = root / "results.json"
            results.write_text(json.dumps({"systems": {"baseline": baseline}}))
            tokenizer = Mock()
            tokenizer.encode.return_value = ["sample"]
            tokenizer.decode.return_value = "candidate"
            engine = Mock()
            engine.translate_batch.return_value = [
                types.SimpleNamespace(hypotheses=[["candidate"]])
            ]
            with (
                patch.dict(
                    sys.modules,
                    {
                        "ctranslate2": types.SimpleNamespace(
                            Translator=Mock(return_value=engine)
                        ),
                        "sentencepiece": types.SimpleNamespace(
                            SentencePieceProcessor=Mock(return_value=tokenizer)
                        ),
                    },
                ),
                patch.object(candidate_tool, "DATA", data),
                patch.object(
                    candidate_tool.importlib.metadata, "version", return_value="test"
                ),
                patch(
                    "tools.benchmark_somali_quality.score",
                    return_value={"bleu": 0, "chrf_plus_plus": 0},
                ),
                patch.object(
                    sys,
                    "argv",
                    ["candidate", "--model-dir", str(model), "--results", str(results)],
                ),
            ):
                self.assertEqual(candidate_tool.main(), 0)
            saved = json.loads(results.read_text(encoding="utf-8"))
            self.assertEqual(saved["systems"]["baseline"], baseline)
            self.assertEqual(saved["systems"]["maanka2_en_to_so"]["sample_count"], 150)

    def test_route_audit_counts_current_fallback_warnings(self):
        samples = [
            {
                "warnings": [
                    "The first result contained an unreadable symbol; an alternative was used."
                ]
            },
            {
                "warnings": [
                    "The first result was unusually long; an alternative was used.",
                    "An extra symbol was removed from the output.",
                ]
            },
            {
                "warnings": [
                    "The first result repeated or copied the input; an alternative was used."
                ]
            },
            {
                "warnings": [
                    "Somali translation may be inaccurate; check important details."
                ]
            },
        ]

        self.assertEqual(
            en_to_so_route_audit(samples, candidate_available=True),
            {
                "synthetic_candidate_available": True,
                "synthetic_candidate_selected_samples": 1,
                "candidate_fallback_samples": 3,
                "unreadable_marker_fallback_samples": 1,
                "output_length_fallback_samples": 1,
                "repeat_or_copy_fallback_samples": 1,
                "extra_symbol_removed_samples": 1,
            },
        )
        self.assertEqual(
            en_to_so_route_audit(samples, candidate_available=False)[
                "synthetic_candidate_selected_samples"
            ],
            0,
        )

    def test_result_writes_atomically_to_selected_path(self):
        result = {"systems": {"baseline": {"sample_count": 3}}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "nested" / "result.json"
            save_result(output, result)

            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)
            self.assertEqual(list(output.parent.iterdir()), [output])

    def test_failed_write_preserves_existing_results_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "result.json"
            original = '{"kept": true}'
            output.write_text(original, encoding="utf-8")

            with self.assertRaises(TypeError):
                save_result(output, {"unsupported": object()})

            self.assertEqual(output.read_text(encoding="utf-8"), original)
            self.assertEqual(list(output.parent.iterdir()), [output])


if __name__ == "__main__":
    unittest.main()
