# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests deterministic selection and pinned parsing for the Somali dev benchmark."""

import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from tools.benchmark_somali_dev import (
    TICO_DEV_ARCHIVE_SHA256,
    TICO_DEV_MEMBER,
    load_dev_pairs,
    select_stratified_sample,
)


class SomaliDevBenchmarkTests(unittest.TestCase):
    def test_dev_archive_parser_requires_pinned_hash_and_reads_parallel_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "dev.zip"
            output = io.StringIO()
            writer = csv.writer(output, delimiter="\t", lineterminator="\n")
            writer.writerow(
                (
                    "sourceLang",
                    "targetLang",
                    "sourceString",
                    "targetString",
                    "stringID",
                )
            )
            for index in range(971):
                writer.writerow(
                    (
                        "en",
                        "so",
                        f"Source {index}",
                        f"Tarjumid {index}",
                        f"id-{index:04}",
                    )
                )
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(TICO_DEV_MEMBER, output.getvalue())

            with patch(
                "tools.benchmark_somali_dev.model_file_sha256",
                return_value=TICO_DEV_ARCHIVE_SHA256,
            ):
                pairs, archive_hash = load_dev_pairs(archive_path)

        self.assertEqual(len(pairs), 971)
        self.assertEqual(archive_hash, TICO_DEV_ARCHIVE_SHA256)
        self.assertEqual(
            pairs[0],
            {
                "id": "id-0000",
                "source_en": "Source 0",
                "reference_so": "Tarjumid 0",
            },
        )

    def test_selection_is_repeatable_and_balanced_across_length_bands(self):
        rows = []
        for band, count in (("short", 4), ("medium", 12), ("long", 23)):
            for index in range(6):
                rows.append(
                    {
                        "id": f"{band}-{index}",
                        "source_en": "word " * count,
                        "reference_so": "Somali translation",
                    }
                )

        selected = select_stratified_sample(rows, 9)
        self.assertEqual(selected, select_stratified_sample(rows, 9))
        self.assertEqual(len(selected), 9)
        self.assertEqual(
            {
                band: sum(row["id"].startswith(band) for row in selected)
                for band in ("short", "medium", "long")
            },
            {"short": 3, "medium": 3, "long": 3},
        )

    def test_selection_rejects_unbalanced_or_oversized_limits(self):
        rows = [
            {"id": str(index), "source_en": "one two", "reference_so": "laba"}
            for index in range(3)
        ]
        with self.assertRaisesRegex(ValueError, "divisible by 3"):
            select_stratified_sample(rows, 4)
        with self.assertRaisesRegex(ValueError, "Not enough rows"):
            select_stratified_sample(rows, 3)


if __name__ == "__main__":
    unittest.main()
