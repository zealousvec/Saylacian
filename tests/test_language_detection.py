import unittest
from unittest.mock import patch

from saylacian.core import language_detection
from saylacian.core.model_packs import get_pack_specs


class FakeIdentifier:
    def __init__(self, code, confidence):
        self.code = code
        self.confidence = confidence

    def classify(self, _text):
        return self.code, self.confidence


class LanguageDetectionTests(unittest.TestCase):
    def test_high_confidence_english_keeps_precedence(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("en", 0.99),
            ),
            patch.object(language_detection, "_openlid_somali_confidence") as candidate,
        ):
            self.assertEqual(
                language_detection.detect_language(
                    "This is a long English sentence for a detection check."
                ),
                ("English", 0.99, ""),
            )
        candidate.assert_not_called()

    def test_confident_openlid_somali_recovers_unknown_baseline(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.1),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=0.94
            ),
        ):
            self.assertEqual(
                language_detection.detect_language(
                    "Waxaan rabaa inaan barto af Soomaali maanta."
                ),
                ("Somali Latin", 0.94, ""),
            )

    def test_candidate_below_threshold_does_not_force_somali(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.2),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=0.899
            ),
        ):
            language, confidence, message = language_detection.detect_language(
                "Waxaan rabaa inaan barto af Soomaali maanta."
            )
        self.assertIsNone(language)
        self.assertEqual(confidence, 0.2)
        self.assertIn("uncertain", message)

    def test_missing_optional_model_preserves_baseline_abstention(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.2),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=None
            ),
        ):
            language, confidence, message = language_detection.detect_language(
                "Waxaan rabaa inaan barto af Soomaali maanta."
            )
        self.assertIsNone(language)
        self.assertEqual(confidence, 0.2)
        self.assertIn("uncertain", message)

    def test_short_input_abstains_without_loading_optional_model(self):
        with patch.object(
            language_detection, "_openlid_somali_confidence"
        ) as candidate:
            result = language_detection.detect_language("hi you")
        self.assertIsNone(result[0])
        candidate.assert_not_called()

    def test_somali_pack_files_are_pinned(self):
        pack = get_pack_specs()["somali_detection_openlid"]
        self.assertEqual(pack["license"], "MIT (model); GPL-3.0 (training dataset)")
        self.assertEqual(pack["download_bytes"], 25_833_402)
        self.assertEqual(pack["runtimes"]["onnxruntime"], "1.31.0")
        self.assertEqual(
            next(
                asset
                for asset in pack["assets"]
                if asset["destination"].endswith("model_quantized.onnx")
            )["sha256"],
            "ee8599c721d24f678ef10cee403f4deda3a40e7e237e9983b3df11bf3f34ec2e",
        )

    def test_synthetic_somali_pack_is_optional_and_separately_licensed(self):
        pack = get_pack_specs()["somali_synthetic_en_so"]
        self.assertEqual(pack["license"], "CC-BY-4.0")
        self.assertEqual(
            pack["model_repositories"],
            ["WindyWord/translate-synthetic-en-so"],
        )
        self.assertEqual(pack["download_bytes"], 64_704_828)
        assets = {asset["destination"]: asset for asset in pack["assets"]}
        model = assets["somali/en_so_synthetic/model.bin"]
        self.assertEqual(
            model["sha256"],
            "4c010d7a7aad603503294994bd59a0f30517fa1e64295debfe9aae44f1fe2228",
        )
        self.assertIn("11427877b7864afad1b5e93e10d1e89661d8b0c0", model["url"])
        self.assertIn("somali/en_so_synthetic/NOTICE.md", assets)


if __name__ == "__main__":
    unittest.main()
