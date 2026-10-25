# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import tempfile
import unittest
from pathlib import Path

from tools.benchmark_somali_quality import en_to_so_route_audit, save_result


class SomaliBenchmarkOutputTests(unittest.TestCase):
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
