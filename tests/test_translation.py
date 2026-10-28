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
    def test_multiline_translation_preserves_lines_and_blank_lines(self):
        engine = FakeEngine()
        tokenizer = FakeTokenizer()
        with (
            patch.object(translation, "model_directory", return_value=Path("en_fr")),
            patch.object(translation, "_model_roots", return_value=[]),
            patch.object(translation, "load_model", return_value=(tokenizer, engine)),
        ):
            result = translation.translate_meaning(
                "  First line.\r\n\r\nSecond line.  ",
                "English",
                "French",
                provider_override="offline",
            )

        self.assertEqual(result.text, "  translated text\r\n\r\ntranslated text  ")
        self.assertEqual(len(engine.calls), 1)
        self.assertEqual(engine.calls[0], [["First", "line."], ["Second", "line."]])
        self.assertTrue(
            any(
                "each line was translated separately" in item
                for item in result.warnings
            )
        )

    def test_multiline_online_translation_sends_each_line_and_keeps_separators(self):
        calls = []

        def translate_line(text, source, target):
            calls.append((text, source, target))
            return text.upper(), ()

        with patch.object(
            translation, "translate_cloudflare", side_effect=translate_line
        ):
            result = translation.translate_meaning(
                "first\nsecond",
                "English",
                "French",
                provider_override="cloudflare",
            )

        self.assertEqual(
            calls,
            [("first", "English", "French"), ("second", "English", "French")],
        )
        self.assertEqual(result.text, "FIRST\nSECOND")
        self.assertTrue(
            any(
                "each line was translated separately" in item
                for item in result.warnings
            )
        )

    def test_multiline_translation_preserves_unicode_line_separators(self):
        for separator in ("\r", "\u2028", "\u2029"):
            with self.subTest(separator=separator):
                engine = FakeEngine()
                tokenizer = FakeTokenizer()
                with (
                    patch.object(
                        translation, "model_directory", return_value=Path("en_fr")
                    ),
                    patch.object(translation, "_model_roots", return_value=[]),
                    patch.object(
                        translation,
                        "load_model",
                        return_value=(tokenizer, engine),
                    ),
                ):
                    result = translation.translate_meaning(
                        f"First line.{separator}Second line.",
                        "English",
                        "French",
                        provider_override="offline",
                    )

                self.assertEqual(
                    result.text,
                    f"translated text{separator}translated text",
                )
                self.assertEqual(len(engine.calls), 1)
                self.assertEqual(len(engine.calls[0]), 2)

    def test_multiline_offline_batch_is_bounded(self):
        engine = FakeEngine()
        tokenizer = FakeTokenizer()
        text = "\n".join(f"Line {index}." for index in range(35))
        with (
            patch.object(translation, "model_directory", return_value=Path("en_fr")),
            patch.object(translation, "load_model", return_value=(tokenizer, engine)),
        ):
            result = translation.translate_meaning(
                text,
                "English",
                "French",
                provider_override="offline",
            )

        self.assertEqual(result.text.splitlines(), ["translated text"] * 35)
        self.assertEqual([len(batch) for batch in engine.calls], [16, 16, 3])
        self.assertTrue(
            all(
                len(batch) <= translation.MULTILINE_BATCH_SIZE for batch in engine.calls
            )
        )

    def test_multiline_batch_runtime_failure_falls_back_to_individual_lines(self):
        class BatchLimitedEngine(FakeEngine):
            def translate_batch(self, tokens, **options):
                if len(tokens) > 1:
                    raise RuntimeError("batch exceeds available memory")
                return super().translate_batch(tokens, **options)

        engine = BatchLimitedEngine()
        tokenizer = FakeTokenizer()
        with (
            patch.object(translation, "model_directory", return_value=Path("en_fr")),
            patch.object(translation, "load_model", return_value=(tokenizer, engine)),
        ):
            result = translation.translate_meaning(
                "First line.\nSecond line.",
                "English",
                "French",
                provider_override="offline",
            )

        self.assertEqual(result.text, "translated text\ntranslated text")
        self.assertEqual(len(engine.calls), 2)

    def test_multiline_batch_preserves_existing_single_line_token_limit(self):
        engine = FakeEngine()
        tokenizer = FakeTokenizer()
        long_line = " ".join(["word"] * 401)
        with (
            patch.object(translation, "model_directory", return_value=Path("en_fr")),
            patch.object(translation, "load_model", return_value=(tokenizer, engine)),
            self.assertRaisesRegex(
                ValueError, "single sentence exceeds 400 model tokens"
            ),
        ):
            translation.translate_meaning(
                long_line + "\nA short line.",
                "English",
                "French",
                provider_override="offline",
            )

    def test_inference_profile_scales_down_on_small_cpus(self):
        self.assertEqual(translation._inference_profile(2), (1, 2, 2))
        self.assertEqual(translation._inference_profile(4), (1, 2, 2))
        self.assertEqual(translation._inference_profile(8), (2, 4, 3))

    def test_loaded_model_uses_profile_thread_limit_and_int8(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "source.spm").touch()
            (folder / "target.spm").touch()
            translator_args = []

            class FakeSentencePiece:
                def __init__(self, model_file):
                    self.model_file = model_file

            class FakeTranslator:
                def __init__(self, *args, **kwargs):
                    translator_args.append((args, kwargs))

            fake_ctranslate2 = SimpleNamespace(Translator=FakeTranslator)
            fake_sentencepiece = SimpleNamespace(
                SentencePieceProcessor=FakeSentencePiece
            )
            translation.load_model.cache_clear()
            with (
                patch.dict(
                    "sys.modules",
                    {
                        "ctranslate2": fake_ctranslate2,
                        "sentencepiece": fake_sentencepiece,
                    },
                ),
                patch.object(translation, "INFERENCE_THREADS", 1),
            ):
                tokenizers, _engine = translation.load_model(str(folder))
            translation.load_model.cache_clear()

        self.assertEqual(len(tokenizers), 2)
        self.assertEqual(translator_args[0][1]["compute_type"], "int8")
        self.assertEqual(translator_args[0][1]["intra_threads"], 1)

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
                self.assertEqual(
                    engine.options["beam_size"],
                    translation.INFERENCE_BEAM_SIZE,
                )

    def run_with_candidate_output(self, candidate_output, candidate_error=None):
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
                    if candidate_error is not None:
                        raise candidate_error
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

    def run_with_afrislm_output(
        self, candidate_output, source="English", allow_large_model=True
    ):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline_folder = root / "somali" / "en_so"
            afrislm_folder = root / "somali" / "en_so_afrislm"
            baseline_folder.mkdir(parents=True)
            afrislm_folder.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (baseline_folder / filename).touch()
            (afrislm_folder / "model.gguf").touch()
            baseline_engine = FakeEngine()

            with (
                patch.object(translation, "_model_roots", return_value=[root]),
                patch.object(
                    translation,
                    "load_model",
                    return_value=(
                        (FakeTokenizer(), FakeTokenizer("baseline result")),
                        baseline_engine,
                    ),
                ),
                patch.object(
                    translation,
                    "should_use_large_afrislm",
                    return_value=allow_large_model,
                ),
                patch.object(
                    translation, "translate_afrislm", return_value=candidate_output
                ) as afrislm,
            ):
                result = translation.translate_meaning(
                    "A useful sentence.",
                    source,
                    "Somali Latin" if source == "English" else "English",
                    provider_override="offline",
                )
            return result, baseline_engine, afrislm

    def test_optional_synthetic_model_is_used_before_the_baseline(self):
        result, candidate_engine, baseline_engine = self.run_with_candidate_output(
            "candidate Somali result"
        )

        self.assertEqual(result.text, "candidate Somali result")
        self.assertIn("no_repeat_ngram_size", candidate_engine.options)
        self.assertIsNone(baseline_engine.options)

    def test_synthetic_model_runtime_error_falls_back_to_the_baseline(self):
        result, _candidate_engine, baseline_engine = self.run_with_candidate_output(
            None,
            candidate_error=RuntimeError("optional runtime failure"),
        )

        self.assertEqual(result.text, "baseline Somali result")
        self.assertIsNotNone(baseline_engine.options)
        self.assertTrue(
            any(
                "Optional Somali model could not run" in warning
                for warning in result.warnings
            )
        )

    def test_installed_afrislm_model_is_tried_before_the_standard_pack(self):
        result, baseline_engine, afrislm = self.run_with_afrislm_output(
            "Subax wanaagsan"
        )

        self.assertEqual(result.text, "Subax wanaagsan")
        self.assertIn("Somali translation may be inaccurate", result.warnings[0])
        self.assertIsNone(baseline_engine.options)
        afrislm.assert_called_once()

    def test_installed_afrislm_is_skipped_on_low_core_devices(self):
        result, baseline_engine, afrislm = self.run_with_afrislm_output(
            "candidate Somali result",
            allow_large_model=False,
        )

        self.assertEqual(result.text, "baseline result")
        self.assertIsNotNone(baseline_engine.options)
        self.assertTrue(
            any("skipped on this low-core device" in w for w in result.warnings)
        )
        afrislm.assert_not_called()

    def test_afrislm_degenerate_output_falls_back_to_the_standard_pack(self):
        result, baseline_engine, _afrislm = self.run_with_afrislm_output(
            "A useful sentence."
        )

        self.assertEqual(result.text, "baseline result")
        self.assertIsNotNone(baseline_engine.options)
        self.assertTrue(any("AfriSLM output was flagged" in w for w in result.warnings))

    def test_afrislm_missing_runtime_uses_the_standard_pack(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "somali" / "en_so_afrislm"
            folder.mkdir(parents=True)
            (folder / "model.gguf").touch()
            baseline_folder = root / "somali" / "en_so"
            baseline_folder.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (baseline_folder / filename).touch()
            baseline_engine = FakeEngine()
            with (
                patch.object(translation, "_model_roots", return_value=[root]),
                patch.object(
                    translation,
                    "load_model",
                    return_value=(
                        (FakeTokenizer(), FakeTokenizer("baseline result")),
                        baseline_engine,
                    ),
                ),
                patch.object(
                    translation, "should_use_large_afrislm", return_value=True
                ),
                patch.object(
                    translation,
                    "translate_afrislm",
                    side_effect=RuntimeError("optional runtime missing"),
                ),
            ):
                result = translation.translate_meaning(
                    "A useful sentence.",
                    "English",
                    "Somali Latin",
                    provider_override="offline",
                )

        self.assertEqual(result.text, "baseline result")
        self.assertTrue(any("AfriSLM could not handle" in w for w in result.warnings))

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
