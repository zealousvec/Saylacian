import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from saylacian.core import translation


class FakeTokenizer:
    def __init__(self, decoded="translated text"):
        self.decoded = decoded

    def encode(self, text, out_type=str):
        return text.split()

    def decode(self, tokens):
        return self.decoded


class FakeEngine:
    def __init__(self):
        self.options = None

    def translate_batch(self, _tokens, **options):
        self.options = options
        return [SimpleNamespace(hypotheses=[["translated"]])]


class TranslationTests(unittest.TestCase):
    def test_somali_model_routes_enable_bounded_ngram_repetition_guard(self):
        for source, target, folder_name in (
            ("English", "Somali Latin", "en_so"),
            ("Somali Latin", "English", "so_en"),
        ):
            with self.subTest(source=source, target=target):
                engine = FakeEngine()
                tokenizers = (FakeTokenizer(), FakeTokenizer())
                with (
                    patch.object(
                        translation,
                        "model_directory",
                        return_value=Path(folder_name),
                    ),
                    patch.object(
                        translation, "load_model", return_value=(tokenizers, engine)
                    ),
                ):
                    result = translation.translate_meaning(
                        "a short sentence for translation",
                        source,
                        target,
                        provider_override="offline",
                    )
                self.assertEqual(result.text, "translated text")
                self.assertEqual(
                    engine.options["no_repeat_ngram_size"],
                    3,
                )

    def run_with_candidate_output(self, candidate_output):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = root / "baseline"
            synthetic = root / "synthetic"
            baseline_folder = baseline / "somali" / "en_so"
            candidate_folder = synthetic / "somali" / "en_so_synthetic"
            baseline_folder.mkdir(parents=True)
            candidate_folder.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (baseline_folder / filename).touch()
            (candidate_folder / "model.bin").touch()

            candidate_engine = FakeEngine()
            baseline_engine = FakeEngine()

            def load(folder):
                if Path(folder) == candidate_folder:
                    return (
                        (FakeTokenizer(), FakeTokenizer(candidate_output)),
                        candidate_engine,
                    )
                return (
                    (FakeTokenizer(), FakeTokenizer("baseline Somali result")),
                    baseline_engine,
                )

            with (
                patch.object(
                    translation,
                    "_model_roots",
                    return_value=[baseline, synthetic],
                ),
                patch.object(translation, "load_model", side_effect=load),
            ):
                result = translation.translate_meaning(
                    "A useful English sentence.",
                    "English",
                    "Somali Latin",
                    provider_override="offline",
                )

            return result, candidate_engine, baseline_engine

    def test_optional_synthetic_model_is_used_before_the_baseline(self):
        result, candidate_engine, baseline_engine = self.run_with_candidate_output(
            "candidate Somali result"
        )

        self.assertEqual(result.text, "candidate Somali result")
        self.assertIn("no_repeat_ngram_size", candidate_engine.options)
        self.assertIsNone(baseline_engine.options)

    def test_degenerate_synthetic_result_falls_back_to_the_baseline(self):
        result, _candidate_engine, baseline_engine = self.run_with_candidate_output(
            "A useful English sentence."
        )

        self.assertEqual(result.text, "baseline Somali result")
        self.assertIsNotNone(baseline_engine.options)
        self.assertTrue(any("copied" in warning for warning in result.warnings))

    def test_synthetic_guard_rejects_repeated_content_and_long_outputs(self):
        examples = (
            (
                "people often repeat names in a long sentence many times",
                "qaraabadaadu waxay leeyihiin calaamado qaraabadaadu waxay leeyihiin calaamado qaraabadaadu",
            ),
            (
                "a short sentence",
                "waxaan waxaan waxaan",
            ),
            (
                "hi",
                "waxaan u baahanahay inaad iga caawiso inaan helo goobta ugu dhow ee aan ka heli karo meel kale oo aan aado",
            ),
        )
        for source, output in examples:
            with self.subTest(source=source):
                self.assertTrue(
                    translation._synthetic_candidate_is_degenerate(source, output)
                )


if __name__ == "__main__":
    unittest.main()
