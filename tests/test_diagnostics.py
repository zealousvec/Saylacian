# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests privacy-safe application diagnostics."""

import tempfile
import unittest
from pathlib import Path

from saylacian.core.diagnostics import PrivateDiagnostics


class PrivateDiagnosticsTests(unittest.TestCase):
    def test_log_records_code_location_but_not_exception_text(self):
        with tempfile.TemporaryDirectory() as directory:
            diagnostics = PrivateDiagnostics(Path(directory))
            log_path = diagnostics.start("test")
            try:
                raise RuntimeError("PRIVATE TRANSLATION INPUT")
            except RuntimeError as error:
                diagnostics.record_exception("translation-worker", error)
            diagnostics.close()

            contents = log_path.read_text(encoding="utf-8")
            self.assertIn("startup version=test", contents)
            self.assertIn("context=translation-worker type=RuntimeError", contents)
            self.assertIn("test_diagnostics.py", contents)
            self.assertNotIn("PRIVATE TRANSLATION INPUT", contents)
            self.assertNotIn(
                str(Path(__file__).resolve().parent).replace("\\", "/"),
                contents.replace("\\", "/"),
            )


if __name__ == "__main__":
    unittest.main()
