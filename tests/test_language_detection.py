import hashlib
import json
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from saylacian.core import language_detection
from saylacian.core.model_packs import ModelPackManager, get_pack_specs


class FakeIdentifier:
    def __init__(self, code, confidence):
        self.code = code
        self.confidence = confidence

    def classify(self, _text):
        return self.code, self.confidence


class SequencedIdentifier:
    def __init__(self, predictions):
        self.predictions = iter(predictions)
        self.inputs = []

    def classify(self, text):
        self.inputs.append(text)
        return next(self.predictions)


class LanguageDetectionTests(unittest.TestCase):
    def test_optional_detector_thread_profile_scales_down_on_small_cpus(self):
        from saylacian.core import language_detection

        self.assertEqual(language_detection._inference_threads(2), 1)
        self.assertEqual(language_detection._inference_threads(4), 1)
        self.assertEqual(language_detection._inference_threads(8), 2)

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
                language_detection, "_openlid_somali_confidence", return_value=0.99
            ),
        ):
            self.assertEqual(
                language_detection.detect_language(
                    "Waxaan rabaa barto Soomaali maanta."
                ),
                ("Somali Latin", 0.99, ""),
            )

    def test_candidate_below_threshold_does_not_force_somali(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.2),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=0.979
            ),
        ):
            language, confidence, message = language_detection.detect_language(
                "Waxaan rabaa barto Soomaali maanta."
            )
        self.assertIsNone(language)
        self.assertEqual(confidence, 0.2)
        self.assertIn("uncertain", message)

    def test_openlid_confidence_at_threshold_is_accepted(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.1),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=0.98
            ),
        ):
            self.assertEqual(
                language_detection.detect_language(
                    "Waxaan rabaa barto Soomaali maanta."
                ),
                ("Somali Latin", 0.98, ""),
            )

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
        with (
            patch.object(language_detection, "_identifier") as identifier,
            patch.object(language_detection, "_openlid_somali_confidence") as candidate,
        ):
            result = language_detection.detect_language("a b c d")
        self.assertIsNone(result[0])
        identifier.assert_not_called()
        candidate.assert_not_called()

    def test_eight_character_three_word_input_reaches_optional_detector(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.1),
            ),
            patch.object(
                language_detection,
                "_openlid_somali_confidence",
                return_value=0.98,
            ) as candidate,
        ):
            result = language_detection.detect_language("waa la i")

        self.assertEqual(result, ("Somali Latin", 0.98, ""))
        candidate.assert_called_once_with("waa la i")

    def test_short_confidence_at_threshold_is_accepted(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("so", 0.70),
            ),
            patch.object(language_detection, "_openlid_somali_confidence") as candidate,
        ):
            result = language_detection.detect_language("waa la i")

        self.assertEqual(result, ("Somali Latin", 0.70, ""))
        candidate.assert_not_called()

    def test_short_confidence_below_threshold_still_abstains(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("so", 0.69),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=None
            ),
        ):
            result = language_detection.detect_language("waa la i")

        self.assertIsNone(result[0])
        self.assertEqual(result[1], 0.69)
        self.assertIn("uncertain", result[2])

    def test_confidently_different_text_ends_abstain_as_mixed(self):
        identifier = SequencedIdentifier([("en", 0.91), ("so", 0.89), ("en", 0.98)])

        with (
            patch.object(language_detection, "_identifier", return_value=identifier),
            patch.object(language_detection, "_openlid_somali_confidence") as openlid,
        ):
            result = language_detection.detect_language(
                "Good morning friend waxaan rabaa cunto maanta"
            )

        self.assertIsNone(result[0])
        self.assertEqual(result[1], 0.89)
        self.assertIn("more than one language", result[2])
        self.assertEqual(
            identifier.inputs,
            [
                "Good morning friend",
                "rabaa cunto maanta",
            ],
        )
        openlid.assert_not_called()

    def test_confidently_different_middle_chunk_abstains_as_mixed(self):
        identifier = SequencedIdentifier([("en", 0.92), ("en", 0.91), ("so", 0.88)])

        with (
            patch.object(language_detection, "_identifier", return_value=identifier),
            patch.object(language_detection, "_openlid_somali_confidence") as openlid,
        ):
            result = language_detection.detect_language(
                "Good morning friend waxaan rabaa cunto this is good"
            )

        self.assertIsNone(result[0])
        self.assertEqual(result[1], 0.88)
        self.assertIn("more than one language", result[2])
        self.assertEqual(
            identifier.inputs,
            [
                "Good morning friend",
                "this is good",
                "waxaan rabaa cunto",
            ],
        )
        openlid.assert_not_called()

    def test_mixed_guard_checks_short_edges_before_openlid_fallback(self):
        identifier = SequencedIdentifier([("en", 0.84), ("so", 0.82)])

        with (
            patch.object(language_detection, "_identifier", return_value=identifier),
            patch.object(language_detection, "_openlid_somali_confidence") as openlid,
        ):
            result = language_detection.detect_language("go it now waan ku fiican")

        self.assertIsNone(result[0])
        self.assertEqual(result[1], 0.82)
        self.assertIn("more than one language", result[2])
        self.assertEqual(identifier.inputs, ["go it now", "waan ku fiican"])
        openlid.assert_not_called()

    def test_mixed_guard_accepts_edge_confidence_at_its_threshold(self):
        identifier = SequencedIdentifier([("en", 0.50), ("so", 0.50)])

        with patch.object(language_detection, "_identifier", return_value=identifier):
            result = language_detection.detect_language("go it now waan ku fiican")

        self.assertIsNone(result[0])
        self.assertEqual(result[1], 0.50)
        self.assertIn("more than one language", result[2])

    def test_mixed_guard_rejects_edge_confidence_below_its_threshold(self):
        identifier = SequencedIdentifier([("en", 0.49), ("so", 0.70)])

        with patch.object(language_detection, "_identifier", return_value=identifier):
            result = language_detection.detect_language("go it now waan ku fiican")

        self.assertEqual(result, ("Somali Latin", 0.70, ""))

    def test_openlid_does_not_override_long_ambiguous_text(self):
        with (
            patch.object(
                language_detection,
                "_identifier",
                return_value=FakeIdentifier("xx", 0.1),
            ),
            patch.object(
                language_detection, "_openlid_somali_confidence", return_value=0.99
            ) as candidate,
        ):
            result = language_detection.detect_language(
                "English words with Somali words mixed together"
            )

        self.assertIsNone(result[0])
        self.assertIn("uncertain", result[2])
        candidate.assert_not_called()

    def test_same_confident_edge_languages_continue_to_whole_text(self):
        identifier = SequencedIdentifier(
            [("en", 0.93), ("en", 0.91), ("en", 0.92), ("en", 0.98)]
        )

        with patch.object(language_detection, "_identifier", return_value=identifier):
            result = language_detection.detect_language(
                "Good morning friend this is a longer English message"
            )

        self.assertEqual(result, ("English", 0.98, ""))
        self.assertEqual(
            identifier.inputs,
            [
                "Good morning friend",
                "longer English message",
                "this is a",
                "Good morning friend this is a longer English message",
            ],
        )

    def test_uncertain_middle_chunk_does_not_force_mixed_warning(self):
        identifier = SequencedIdentifier(
            [("en", 0.93), ("en", 0.91), ("so", 0.49), ("en", 0.98)]
        )

        with patch.object(language_detection, "_identifier", return_value=identifier):
            result = language_detection.detect_language(
                "Good morning friend waxaan rabaa cunto this is good"
            )

        self.assertEqual(result, ("English", 0.98, ""))

    def test_middle_chunk_confidence_at_threshold_warns_as_mixed(self):
        identifier = SequencedIdentifier([("en", 0.93), ("en", 0.91), ("so", 0.50)])

        with patch.object(language_detection, "_identifier", return_value=identifier):
            result = language_detection.detect_language(
                "Good morning friend waxaan rabaa cunto this is good"
            )

        self.assertIsNone(result[0])
        self.assertEqual(result[1], 0.50)
        self.assertIn("more than one language", result[2])

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
        self.assertEqual(pack["requires"], ["somali"])
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

    def test_afrislm_pack_is_pinned_and_requires_the_standard_fallback(self):
        pack = get_pack_specs()["somali_afrislm"]
        model = pack["assets"][0]

        self.assertEqual(pack["license"], "Apache-2.0")
        self.assertIn("CC BY-NC-4.0", pack["license_note"])
        self.assertIn("llama-cpp-python", pack["runtime_note"])
        self.assertEqual(pack["requires"], ["somali"])
        self.assertEqual(pack["download_bytes"], 672_329_792)
        self.assertEqual(pack["runtimes"]["llama-cpp-python"], "0.3.36")
        self.assertEqual(
            model["sha256"],
            "4af8ee1df3ec9008f763ebe95e6f21df3acd8d42c541feeb13314ca22e560afc",
        )
        self.assertIn("14d6fd1e24c9f94a5e40c2e91c066241aede0dce", model["url"])
        self.assertEqual(model["destination"], "somali/en_so_afrislm/model.gguf")

    def test_afrislm_2b_pack_is_pinned_and_keeps_upstream_attributions(self):
        pack = get_pack_specs()["somali_afrislm_2b"]
        assets = {asset["destination"]: asset for asset in pack["assets"]}
        model = assets["somali/en_so_afrislm_2b/model.gguf"]
        attributions = assets["somali/en_so_afrislm_2b/ATTRIBUTIONS.md"]

        self.assertEqual(pack["license"], "Apache-2.0")
        self.assertIn("CC BY-NC-4.0", pack["license_note"])
        self.assertIn("2.3 GB", pack["runtime_note"])
        self.assertEqual(pack["requires"], ["somali"])
        self.assertEqual(pack["download_bytes"], 1_560_528_531)
        self.assertEqual(pack["runtimes"]["llama-cpp-python"], "0.3.36")
        self.assertEqual(model["bytes"], 1_560_461_376)
        self.assertEqual(
            model["sha256"],
            "fc2a80532e58e0655efd9e68c5b7cb2c4373222e736bcc88de648502a4e30361",
        )
        self.assertIn("9bcceadebbcc5d36bba9f7f02141300a95ae8d04", model["url"])
        self.assertEqual(attributions["bytes"], 67_155)
        self.assertEqual(
            attributions["sha256"],
            "9754d9e4d3dbe4001f30e46a14a93293caaf9af9bb40773ffefb5e47c31f5f96",
        )

    def test_afrislm_2b_download_requires_its_optional_runtime(self):
        manager = ModelPackManager(specs=get_pack_specs())
        with (
            patch(
                "saylacian.core.model_packs.importlib.util.find_spec",
                return_value=None,
            ),
            self.assertRaisesRegex(ValueError, "requirements-afrislm.txt"),
        ):
            manager.install("somali_afrislm_2b")

    def test_afrislm_download_requires_its_optional_runtime(self):
        manager = ModelPackManager(specs=get_pack_specs())
        with (
            patch(
                "saylacian.core.model_packs.importlib.util.find_spec",
                return_value=None,
            ),
            self.assertRaisesRegex(ValueError, "requirements-afrislm.txt"),
        ):
            manager.install("somali_afrislm")

    def test_pack_manager_enforces_required_packs_for_install_and_removal(self):
        content = {"ready": True}
        payload = json.dumps(content, ensure_ascii=False).encode("utf-8")
        asset = {
            "kind": "generated-json",
            "content": content,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "destination": "model.json",
        }
        base_spec = {
            "title": "Somali / English",
            "license": "MIT",
            "runtimes": {},
            "assets": [asset],
            "version": "1-base",
            "download_bytes": 0,
        }
        addon_spec = {
            **base_spec,
            "title": "Optional Somali translation model",
            "requires": ["base"],
            "version": "1-addon",
        }

        with TemporaryDirectory() as temporary:
            manager = ModelPackManager(
                temporary,
                specs={"base": base_spec, "addon": addon_spec},
            )
            with self.assertRaisesRegex(
                ValueError, "Install Somali / English before this pack"
            ):
                manager.install("addon")

            manager.install("base")
            manager.install("addon")
            with self.assertRaisesRegex(ValueError, "Remove that pack first"):
                manager.remove("base")
            self.assertTrue(manager.list_packs()[0]["installed"])

            manager.remove("addon")
            manager.remove("base")
            self.assertFalse(any(pack["installed"] for pack in manager.list_packs()))


if __name__ == "__main__":
    unittest.main()
