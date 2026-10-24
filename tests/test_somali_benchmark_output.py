# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import tempfile
import unittest
from pathlib import Path

from tools.benchmark_somali_quality import save_result


class SomaliBenchmarkOutputTests(unittest.TestCase):
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
