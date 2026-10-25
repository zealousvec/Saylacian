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
        self.calls = []

    def translate_batch(self, tokens, **options):
        self.options = options
        self.calls.append(tokens)
        return [SimpleNamespace(hypotheses=[["translated"]]) for _ in tokens]


class TranslationTests(unittest.TestCase):
    def test_somali_language_prefix_is_only_added_for_english_to_somali(self):
        for source, target, folder_name, expected_tokens in (
            (
                "English",
                "Somali Latin",
                "en_so",
                [">>som<<", "a", "short", "sentence", "for", "translation", "</s>"],
            ),
            (
                "Somali Latin",
                "English",
                "so_en",
                ["a", "short", "sentence", "for", "translation", "</s>"],
            ),
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
                    translation.translate_meaning(
                        "a short sentence for translation",
                        source,
                        target,
                        provider_override="offline",
                    )

                self.assertEqual(engine.calls, [[expected_tokens]])

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

    def test_synthetic_result_with_unprompted_trailing_ellipsis_falls_back(self):
        result, candidate_engine, baseline_engine = self.run_with_candidate_output(
            "A useful Somali result..."
        )

        self.assertEqual(result.text, "baseline Somali result")
        self.assertIsNotNone(candidate_engine.options)
        self.assertIsNotNone(baseline_engine.options)
        self.assertTrue(
            any("appeared unfinished" in warning for warning in result.warnings)
        )

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

    def test_synthetic_guard_reports_each_rejection_reason(self):
        cases = (
            ("hi", "hi \u2047", "unknown_symbol"),
            (
                "A useful English sentence.",
                "A useful English sentence.",
                "copied_input",
            ),
            (
                "A complete English sentence.",
                "Turjumaad dhammeystiran...",
                "trailing_ellipsis",
            ),
            (
                "An unfinished source thought...",
                "Fikir aan dhammeystirnayn...",
                None,
            ),
            ("hi", "a b c d e f g h i j k l m", "overlong"),
            ("a short sentence", "waxaan waxaan waxaan", "repeated_content_word"),
            (
                "a short sentence",
                "Waxaan hayaa. Waxaan hayaa.",
                "duplicate_sentence",
            ),
            ("hi", "Alpha alphabet", "repeated_fragment"),
        )
        for source, output, expected_reason in cases:
            with self.subTest(reason=expected_reason):
                self.assertEqual(
                    translation._synthetic_candidate_rejection_reason(source, output),
                    expected_reason,
                )

    def test_long_offline_input_splits_at_sentence_boundary(self):
        engine = FakeEngine()
        tokenizers = (FakeTokenizer(), FakeTokenizer("translated text"))
        long_input = " ".join(["first"] * 201) + ". " + " ".join(["second"] * 201) + "."
        with (
            patch.object(translation, "model_directory", return_value=Path("en_so")),
            patch.object(translation, "_model_roots", return_value=[]),
            patch.object(translation, "load_model", return_value=(tokenizers, engine)),
        ):
            result = translation.translate_meaning(
                long_input,
                "English",
                "Somali Latin",
                provider_override="offline",
            )

        self.assertEqual(result.text, "translated text translated text")
        self.assertEqual(len(engine.calls), 2)
        self.assertTrue(
            any(
                "context between sections may change" in item
                for item in result.warnings
            )
        )

    def test_single_overlong_sentence_keeps_actionable_limit(self):
        engine = FakeEngine()
        tokenizers = (FakeTokenizer(), FakeTokenizer())
        with (
            patch.object(translation, "model_directory", return_value=Path("en_so")),
            patch.object(translation, "_model_roots", return_value=[]),
            patch.object(translation, "load_model", return_value=(tokenizers, engine)),
            self.assertRaisesRegex(
                ValueError, "single sentence exceeds 400 model tokens"
            ),
        ):
            translation.translate_meaning(
                " ".join(["word"] * 401),
                "English",
                "Somali Latin",
                provider_override="offline",
            )

    def test_sentence_chunker_accounts_for_fallback_language_tokens(self):
        sentence_one = " ".join(["first"] * 200) + "."
        sentence_two = " ".join(["second"] * 199) + "."
        chunks, boundaries = translation._sentence_chunks(
            sentence_one + " " + sentence_two,
            (FakeTokenizer(), FakeTokenizer()),
            token_overheads=(0, 2),
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(boundaries, [" "])


if __name__ == "__main__":
    unittest.main()
