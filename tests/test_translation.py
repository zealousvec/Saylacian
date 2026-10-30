# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests local translation, route selection, and experimental Somali behavior."""

import os
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from saylacian.core.translation import (
    MODEL_ROOT,
    _afrislm_2b_model_path,
    _afrislm_4b_model_path,
    _afrislm_model_path,
    _clean_model_markers,
    _join_model_segments,
    _model_token_segments,
    _synthetic_candidate_is_degenerate,
    _translate_afrislm,
    clear_model_cache,
    load_model,
    translate_meaning,
)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.provider = patch.dict(
            os.environ, {"SAYLACIAN_TRANSLATION_PROVIDER": "offline"}
        )
        self.provider.start()
        self.addCleanup(self.provider.stop)

    def test_known_model_formatting_artifacts_are_removed_only_at_start(self):
        self.assertEqual(
            _clean_model_markers("○ A child will read a book."),
            "A child will read a book.",
        )
        self.assertEqual(_clean_model_markers("Text ○ remains."), "Text ○ remains.")

    def test_long_model_input_splits_at_words_and_keeps_source_whitespace(self):
        class WordTokenizer:
            @staticmethod
            def encode(text, out_type=str):
                return text.split()

        with (
            patch("saylacian.core.translation.MODEL_TOKEN_LIMIT", 2),
            patch("saylacian.core.translation.MODEL_CHUNK_TOKEN_TARGET", 2),
        ):
            segments, separators, leading, trailing, chunked = _model_token_segments(
                "  alpha  beta\tgamma\n  ", WordTokenizer()
            )

        self.assertEqual([len(segment) for segment in segments], [2, 1])
        self.assertEqual(separators, ("\t",))
        self.assertEqual(leading, "  ")
        self.assertEqual(trailing, "\n  ")
        self.assertTrue(chunked)
        translated = _join_model_segments(
            ["ALPHA  BETA", "GAMMA"], separators, leading, trailing
        )
        self.assertEqual(translated, "  ALPHA  BETA\tGAMMA\n  ")

    def test_installed_afrislm_model_handles_somali_without_base_pack(self):
        with TemporaryDirectory() as temporary:
            model_path = Path(temporary) / "somali" / "afrislm" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()
            model = Mock()
            model.tokenize.return_value = [1, 2]
            model.create_chat_completion.return_value = {
                "choices": [{"message": {"content": "<think>notes</think>I love you."}}]
            }

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[Path(temporary)],
                ),
                patch(
                    "saylacian.core.translation.load_afrislm_model",
                    return_value=model,
                ),
                patch(
                    "saylacian.core.translation.model_directory",
                    side_effect=AssertionError("base pack should not load"),
                ),
            ):
                result = translate_meaning(
                    "Waan ku jeclahay.", "Somali Latin", "English"
                )

        self.assertEqual(result.text, "I love you.")
        self.assertIn("Alpha testing", result.warnings[0])
        model.create_chat_completion.assert_called_once()
        self.assertEqual(
            model.create_chat_completion.call_args.kwargs["temperature"], 0
        )
        self.assertEqual(
            model.create_chat_completion.call_args.kwargs["max_tokens"], 160
        )

    def test_degenerate_afrislm_output_uses_standard_offline_model(self):
        with TemporaryDirectory() as temporary:
            model_root = Path(temporary)
            model_path = model_root / "somali" / "afrislm" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()
            model = Mock()
            model.tokenize.return_value = [1]
            model.create_chat_completion.return_value = {
                "choices": [{"message": {"content": "This is the source text."}}]
            }
            source_tokenizer = Mock()
            source_tokenizer.encode.return_value = ["source-token"]
            target_tokenizer = Mock()
            target_tokenizer.decode.return_value = "Tarjumid sax ah."
            engine = Mock()
            engine.translate_batch.return_value = [
                SimpleNamespace(hypotheses=[["translated-token"]])
            ]

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[model_root],
                ),
                patch(
                    "saylacian.core.translation.load_afrislm_model",
                    return_value=model,
                ),
                patch(
                    "saylacian.core.translation.model_directory",
                    return_value=model_root / "somali" / "en_so",
                ),
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=((source_tokenizer, target_tokenizer), engine),
                ),
            ):
                result = translate_meaning(
                    "This is the source text.", "English", "Somali Latin"
                )

        self.assertEqual(result.text, "Tarjumid sax ah.")
        self.assertTrue(
            any(
                "unreadable or repetitive text" in warning
                for warning in result.warnings
            )
        )
        engine.translate_batch.assert_called_once()

    def test_afrislm_reserves_context_for_longer_translations(self):
        with TemporaryDirectory() as temporary:
            model_path = Path(temporary) / "somali" / "afrislm" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()
            model = Mock()
            model.tokenize.return_value = [1] * 1600
            model.create_chat_completion.return_value = {
                "choices": [{"message": {"content": "Tarjumid."}}]
            }

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[Path(temporary)],
                ),
                patch(
                    "saylacian.core.translation.load_afrislm_model",
                    return_value=model,
                ),
            ):
                result = translate_meaning("word " * 300, "English", "Somali Latin")

        self.assertEqual(result.text, "Tarjumid.")
        self.assertEqual(
            model.create_chat_completion.call_args.kwargs["max_tokens"], 288
        )

    def test_afrislm_native_runtime_failure_returns_safe_fallback(self):
        model = Mock()
        model.tokenize.return_value = [1]
        model.create_chat_completion.side_effect = RuntimeError(
            "llama_decode returned -1"
        )

        with (
            patch(
                "saylacian.core.translation.load_afrislm_model",
                return_value=model,
            ),
            patch("saylacian.core.translation.load_afrislm_model.cache_clear") as clear,
        ):
            result, warning = _translate_afrislm(
                "Waan ku jeclahay.",
                "Somali Latin",
                "English",
                Path("model.gguf"),
            )

        self.assertIsNone(result)
        self.assertIn("used the standard offline model", warning)
        clear.assert_called_once()

    def test_afrislm_path_is_discovered_from_active_model_pack(self):
        with TemporaryDirectory() as temporary:
            model_path = Path(temporary) / "somali" / "afrislm" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()

            with patch(
                "saylacian.core.translation._model_roots",
                return_value=[Path(temporary)],
            ):
                self.assertEqual(_afrislm_model_path(), model_path)

    def test_afrislm_2b_path_is_discovered_from_active_model_pack(self):
        with TemporaryDirectory() as temporary:
            model_path = Path(temporary) / "somali" / "afrislm_2b" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()

            with patch(
                "saylacian.core.translation._model_roots",
                return_value=[Path(temporary)],
            ):
                self.assertEqual(_afrislm_2b_model_path(), model_path)

    def test_afrislm_4b_path_is_discovered_from_active_model_pack(self):
        with TemporaryDirectory() as temporary:
            model_path = Path(temporary) / "somali" / "afrislm_4b" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()

            with patch(
                "saylacian.core.translation._model_roots",
                return_value=[Path(temporary)],
            ):
                self.assertEqual(_afrislm_4b_model_path(), model_path)

    def test_directional_afrislm_routes_keep_best_model_per_direction(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            small = root / "somali" / "afrislm" / "model.gguf"
            large = root / "somali" / "afrislm_2b" / "model.gguf"
            largest = root / "somali" / "afrislm_4b" / "model.gguf"
            small.parent.mkdir(parents=True)
            large.parent.mkdir(parents=True)
            largest.parent.mkdir(parents=True)
            small.touch()
            large.touch()
            largest.touch()

            def convert(_text, _source, _target, path):
                label = (
                    "largest model"
                    if path == largest
                    else "larger model"
                    if path == large
                    else "smaller model"
                )
                return SimpleNamespace(text=label, warnings=("Experimental.",)), None

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[root],
                ),
                patch(
                    "saylacian.core.translation._translate_afrislm",
                    side_effect=convert,
                ) as route,
                patch(
                    "saylacian.core.translation.model_directory",
                    side_effect=AssertionError("installed candidate should handle it"),
                ),
            ):
                somali_to_english = translate_meaning(
                    "Waan ku jeclahay.", "Somali Latin", "English"
                )
                english_to_somali = translate_meaning(
                    "I love you.", "English", "Somali Latin"
                )

        self.assertEqual(somali_to_english.text, "largest model")
        self.assertEqual(english_to_somali.text, "smaller model")
        self.assertEqual(route.call_args_list[0].args[3], largest)
        self.assertEqual(route.call_args_list[1].args[3], small)

    def test_failed_afrislm_4b_falls_back_to_2b_then_smaller_model(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            small = root / "somali" / "afrislm" / "model.gguf"
            medium = root / "somali" / "afrislm_2b" / "model.gguf"
            largest = root / "somali" / "afrislm_4b" / "model.gguf"
            for path in (small, medium, largest):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            medium_result = SimpleNamespace(
                text="2B translation.", warnings=("Experimental.",), alternatives=()
            )

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[root],
                ),
                patch(
                    "saylacian.core.translation._translate_afrislm",
                    side_effect=[
                        (None, "4B model ran out of memory."),
                        (medium_result, None),
                    ],
                ) as route,
                patch(
                    "saylacian.core.translation.model_directory",
                    side_effect=AssertionError("smaller candidate should handle it"),
                ),
            ):
                result = translate_meaning(
                    "Waan ku jeclahay.", "Somali Latin", "English"
                )

        self.assertEqual(result.text, "2B translation.")
        self.assertIn("used the smaller model", result.warnings[-1])
        self.assertEqual(route.call_args_list[0].args[3], largest)
        self.assertEqual(route.call_args_list[1].args[3], medium)

    def test_failed_larger_model_falls_back_to_installed_smaller_model(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            small = root / "somali" / "afrislm" / "model.gguf"
            large = root / "somali" / "afrislm_2b" / "model.gguf"
            small.parent.mkdir(parents=True)
            large.parent.mkdir(parents=True)
            small.touch()
            large.touch()
            small_result = SimpleNamespace(
                text="I love you.", warnings=("Experimental.",), alternatives=()
            )

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[root],
                ),
                patch(
                    "saylacian.core.translation._translate_afrislm",
                    side_effect=[
                        (None, "Large model ran out of memory."),
                        (small_result, None),
                    ],
                ),
                patch(
                    "saylacian.core.translation.model_directory",
                    side_effect=AssertionError("smaller candidate should handle it"),
                ),
            ):
                result = translate_meaning(
                    "Waan ku jeclahay.", "Somali Latin", "English"
                )

        self.assertEqual(result.text, "I love you.")
        self.assertIn("used the smaller model", result.warnings[-1])

    def test_unavailable_afrislm_runtime_falls_back_with_warning(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            model_path = root / "somali" / "afrislm" / "model.gguf"
            model_path.parent.mkdir(parents=True)
            model_path.touch()
            tokenizer = Mock()
            tokenizer.encode.return_value = ["token"]
            tokenizer.decode.return_value = "I love you."
            engine = Mock()
            engine.translate_batch.return_value = [
                SimpleNamespace(hypotheses=[["token"]])
            ]

            with (
                patch(
                    "saylacian.core.translation._model_roots",
                    return_value=[root],
                ),
                patch(
                    "saylacian.core.translation.load_afrislm_model",
                    side_effect=ValueError("runtime unavailable"),
                ),
                patch(
                    "saylacian.core.translation.model_directory",
                    return_value=root / "somali" / "so_en",
                ),
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=((tokenizer, tokenizer), engine),
                ),
            ):
                result = translate_meaning(
                    "Waan ku jeclahay.", "Somali Latin", "English"
                )

        self.assertEqual(result.text, "I love you.")
        self.assertTrue(
            any("runtime unavailable" in warning for warning in result.warnings)
        )

    def test_synthetic_candidate_unknown_token_marker_is_degenerate(self):
        self.assertTrue(
            _synthetic_candidate_is_degenerate("rare term", "Tarjumid \u2047 calaamad")
        )

    def test_synthetic_unknown_token_marker_uses_multilingual_fallback(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            fallback = root / "somali" / "en_so"
            fallback.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (fallback / filename).touch()
            candidate = root / "somali" / "en_so_synthetic"
            candidate.mkdir()
            (candidate / "model.bin").touch()

            candidate_source = Mock()
            candidate_source.encode.return_value = ["candidate-token"]
            candidate_target = Mock()
            candidate_target.decode.return_value = "Tarjumid \u2047 calaamad"
            candidate_engine = Mock()
            candidate_engine.translate_batch.return_value = [
                Mock(hypotheses=[["candidate-output"]])
            ]

            fallback_source = Mock()
            fallback_source.encode.return_value = ["fallback-token"]
            fallback_target = Mock()
            fallback_target.decode.return_value = "Qoraal tijaabo"
            fallback_engine = Mock()
            fallback_engine.translate_batch.return_value = [
                Mock(hypotheses=[["fallback-output"]])
            ]

            with patch(
                "saylacian.core.translation.load_model",
                side_effect=(
                    ((candidate_source, candidate_target), candidate_engine),
                    ((fallback_source, fallback_target), fallback_engine),
                ),
            ):
                result = translate_meaning(
                    "rare terminology", "English", "Somali Latin", root
                )

        self.assertEqual(result.text, "Qoraal tijaabo")
        self.assertTrue(
            any("unreadable symbol" in warning for warning in result.warnings)
        )
        fallback_engine.translate_batch.assert_called_once()

    def test_synthetic_candidate_warning_hides_internal_model_details(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            base_model = root / "somali" / "en_so"
            base_model.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (base_model / filename).touch()
            (root / "somali" / "en_so_synthetic").mkdir()
            (root / "somali" / "en_so_synthetic" / "model.bin").touch()
            source_tokenizer = Mock()
            source_tokenizer.encode.return_value = ["token"]
            target_tokenizer = Mock()
            target_tokenizer.decode.return_value = "Waad ku mahadsan tahay."
            engine = Mock()
            engine.translate_batch.return_value = [Mock(hypotheses=[["output"]])]

            with patch(
                "saylacian.core.translation.load_model",
                return_value=((source_tokenizer, target_tokenizer), engine),
            ):
                result = translate_meaning(
                    "Thank you.", "English", "Somali Latin", root
                )

        self.assertEqual(
            result.warnings,
            ("Somali translation may be inaccurate; check important details.",),
        )
        self.assertFalse(
            any(
                internal in warning.lower()
                for warning in result.warnings
                for internal in ("candidate", "experimental", "human review pending")
            )
        )

    def test_offline_english_french_uses_plain_quality_note(self):
        with TemporaryDirectory() as temporary:
            model = Path(temporary) / "en_fr"
            (model / "model").mkdir(parents=True)
            (model / "model" / "model.bin").touch()
            (model / "sentencepiece.model").touch()
            tokenizer = Mock()
            tokenizer.encode.return_value = ["token"]
            tokenizer.decode.return_value = "Bonjour."
            engine = Mock()
            engine.translate_batch.return_value = [Mock(hypotheses=[["output"]])]

            with patch(
                "saylacian.core.translation.load_model",
                return_value=(tokenizer, engine),
            ):
                result = translate_meaning("Hello.", "English", "French", temporary)

        self.assertEqual(
            result.warnings, ("Machine translation; check important details.",)
        )
        self.assertFalse(
            any("experimental" in warning.lower() for warning in result.warnings)
        )
        self.assertFalse(
            any(
                "human review pending" in warning.lower() for warning in result.warnings
            )
        )

    def test_no_hidden_download(self):
        with (
            TemporaryDirectory() as folder,
            patch("socket.socket.connect", side_effect=AssertionError("Network")),
            self.assertRaisesRegex(ValueError, "No local model"),
        ):
            translate_meaning("hello", "English", "French", folder)

    def test_script_not_meaning_language(self):
        with self.assertRaises(ValueError):
            translate_meaning("b", "Osmanya", "French")

    def test_length_limit(self):
        with self.assertRaises(ValueError):
            translate_meaning("a" * 4001, "English", "French")

    def test_model_cache_evicts_least_recent_route_after_three_models(self):
        load_model.cache_clear()
        self.addCleanup(load_model.cache_clear)
        with TemporaryDirectory() as temporary:
            folders = []
            for index in range(4):
                folder = Path(temporary) / f"route-{index}"
                (folder / "model").mkdir(parents=True)
                (folder / "model" / "model.bin").touch()
                (folder / "sentencepiece.model").touch()
                folders.append(folder)

            fake_sentencepiece = types.ModuleType("sentencepiece")
            fake_sentencepiece.SentencePieceProcessor = Mock()
            fake_ctranslate2 = types.ModuleType("ctranslate2")
            fake_ctranslate2.Translator = Mock()

            with patch.dict(
                sys.modules,
                {
                    "sentencepiece": fake_sentencepiece,
                    "ctranslate2": fake_ctranslate2,
                },
            ):
                for folder in folders:
                    load_model(str(folder))

                self.assertEqual(load_model.cache_info().currsize, 3)
                load_model(str(folders[0]))

            self.assertEqual(fake_ctranslate2.Translator.call_count, 5)
            self.assertEqual(load_model.cache_info().currsize, 3)
            clear_model_cache()
            self.assertEqual(load_model.cache_info().currsize, 0)

    def test_token_limit_rejects_without_model_inference(self):
        with TemporaryDirectory() as temporary:
            model = Path(temporary) / "en_fr"
            (model / "model").mkdir(parents=True)
            (model / "model" / "model.bin").touch()
            (model / "sentencepiece.model").touch()
            tokenizer = Mock()
            tokenizer.encode.return_value = ["piece"] * 401
            engine = Mock()

            with (
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=(tokenizer, engine),
                ),
                self.assertRaisesRegex(ValueError, "400-token limit"),
            ):
                translate_meaning(
                    "small enough by characters", "English", "French", temporary
                )

            engine.translate_batch.assert_not_called()

    def test_somali_token_limit_includes_language_markers(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary) / "somali" / "so_en"
            folder.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (folder / filename).touch()
            source_tokenizer = Mock()
            source_tokenizer.encode.return_value = ["piece"] * 399
            target_tokenizer = Mock()
            engine = Mock()

            with (
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=((source_tokenizer, target_tokenizer), engine),
                ),
                self.assertRaisesRegex(ValueError, "400-token limit"),
            ):
                translate_meaning("short passage", "Somali Latin", "English", temporary)

            engine.translate_batch.assert_not_called()

    def test_synthetic_somali_token_limit_rejects_before_inference(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "somali" / "en_so"
            model.mkdir(parents=True)
            for filename in (
                "model.bin",
                "config.json",
                "shared_vocabulary.json",
                "source.spm",
                "target.spm",
            ):
                (model / filename).touch()
            synthetic = root / "somali" / "en_so_synthetic"
            synthetic.mkdir()
            (synthetic / "model.bin").touch()
            source_tokenizer = Mock()
            source_tokenizer.encode.return_value = ["piece"] * 401
            target_tokenizer = Mock()
            engine = Mock()

            with (
                patch(
                    "saylacian.core.translation.load_model",
                    return_value=((source_tokenizer, target_tokenizer), engine),
                ),
                self.assertRaisesRegex(ValueError, "400-token limit"),
            ):
                translate_meaning("short passage", "English", "Somali Latin", temporary)

            engine.translate_batch.assert_not_called()

    @unittest.skipUnless(
        (MODEL_ROOT / "en_fr/model/model.bin").exists(), "Local model not installed"
    )
    def test_english_french_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            self.assertEqual(
                translate_meaning("Hello, how are you?", "English", "French").text,
                "Bonjour, comment allez-vous ?",
            )

    @unittest.skipUnless(
        (MODEL_ROOT / "fr_en/model/model.bin").exists(), "Local model not installed"
    )
    def test_french_english_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            self.assertEqual(
                translate_meaning(
                    "Bonjour, comment allez-vous ?", "French", "English"
                ).text,
                "Hello, how are you?",
            )

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so/model.bin").exists(), "Somali model not installed"
    )
    def test_english_somali_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "The child is reading a book.", "English", "Somali Latin"
            )
        self.assertTrue(result.text)
        self.assertTrue(
            any(
                "Somali translation may be inaccurate" in warning
                for warning in result.warnings
            )
        )

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so_synthetic/model.bin").exists(),
        "Synthetic EN→SO candidate not installed",
    )
    def test_synthetic_candidate_improves_verified_examples_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            thank_you = translate_meaning("Thank you.", "English", "Somali Latin")
            morning = translate_meaning("Good morning.", "English", "Somali Latin")
        self.assertEqual(thank_you.text, "Waad ku mahadsan tahay.")
        self.assertEqual(morning.text, "Subax wanaagsan.")
        self.assertTrue(
            any(
                "Somali translation may be inaccurate" in warning
                for warning in thank_you.warnings
            )
        )

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so_synthetic/model.bin").exists(),
        "Synthetic EN→SO candidate not installed",
    )
    def test_synthetic_candidate_repetition_falls_back_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning("How are you?", "English", "Somali Latin")
        self.assertTrue(result.text)
        self.assertTrue(any("an alternative was used" in w for w in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/en_so_synthetic/model.bin").exists(),
        "Synthetic EN→SO candidate not installed",
    )
    def test_synthetic_runaway_output_uses_multilingual_rescue(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "and i have a cough too", "English", "Somali Latin"
            )
        self.assertTrue(result.text)
        self.assertTrue(any("an alternative was used" in w for w in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/so_en/model.bin").exists(), "Somali model not installed"
    )
    def test_somali_english_offline_smoke(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "Salaan, sidee tahay?", "Somali Latin", "English"
            )
        self.assertEqual(result.text, "How are you?")

    @unittest.skipUnless(
        (MODEL_ROOT / "somali/so_en/model.bin").exists()
        and (MODEL_ROOT / "en_fr/model/model.bin").exists(),
        "Somali-English or English-French model not installed",
    )
    def test_somali_french_pivot_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning("Salaan, sidee tahay?", "Somali Latin", "French")
        self.assertEqual(result.text, "Comment allez-vous ?")
        self.assertTrue(any("some meaning may change" in w for w in result.warnings))

    @unittest.skipUnless(
        (MODEL_ROOT / "fr_en/model/model.bin").exists()
        and (MODEL_ROOT / "somali/en_so/model.bin").exists(),
        "French-English or English-Somali model not installed",
    )
    def test_french_somali_pivot_offline(self):
        with patch("socket.socket.connect", side_effect=AssertionError("Network")):
            result = translate_meaning(
                "Bonjour, comment allez-vous ?", "French", "Somali Latin"
            )
        self.assertEqual(result.text, "Hello, sidee baad u tahay?")
        self.assertTrue(
            any("Somali translation may be inaccurate" in w for w in result.warnings)
        )
        self.assertTrue(any("some meaning may change" in w for w in result.warnings))
