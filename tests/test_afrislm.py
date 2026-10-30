import unittest
from pathlib import Path
from unittest.mock import patch

from saylacian.core import afrislm


class FakeModel:
    def __init__(self, output="</think>\n\nSubax wanaagsan"):
        self.output = output
        self.messages = None
        self.token_count = 0

    def tokenize(self, text):
        return [b"token"] * self.token_count

    def create_chat_completion(self, **arguments):
        self.messages = arguments["messages"]
        return {
            "choices": [{"message": {"content": self.output}}],
        }


class AfriSLMTests(unittest.TestCase):
    def test_thread_profile_scales_down_on_small_cpus(self):
        self.assertEqual(afrislm._inference_threads(2), 1)
        self.assertEqual(afrislm._inference_threads(4), 1)
        self.assertEqual(afrislm._inference_threads(8), 4)

    def test_large_model_is_not_selected_on_low_core_devices(self):
        self.assertFalse(afrislm.should_use_large_model(2))
        self.assertFalse(afrislm.should_use_large_model(4))
        self.assertTrue(afrislm.should_use_large_model(8))

    def test_two_billion_model_requires_cpu_and_memory_headroom(self):
        memory = 4 * 1024**3

        self.assertFalse(afrislm.should_use_2b_model(4, memory))
        self.assertFalse(afrislm.should_use_2b_model(8, memory - 1))
        self.assertTrue(afrislm.should_use_2b_model(8, memory))

    def test_two_billion_model_reads_current_available_memory(self):
        with patch.object(
            afrislm,
            "_available_physical_memory_bytes",
            return_value=4 * 1024**3,
        ):
            self.assertTrue(afrislm.should_use_2b_model(8))

        with patch.object(
            afrislm, "_available_physical_memory_bytes", return_value=None
        ):
            self.assertFalse(afrislm.should_use_2b_model(8))

    def test_translation_uses_explicit_languages_and_hides_thinking_marker(self):
        model = FakeModel()
        with patch.object(afrislm, "_load_model", return_value=model):
            result = afrislm.translate(
                "Good morning", "English", "Somali Latin", Path("model")
            )

        self.assertEqual(result, "Subax wanaagsan")
        self.assertIn("English to Somali", model.messages[0]["content"])
        self.assertIn("cultural sensitivities", model.messages[0]["content"])
        self.assertIn("Good morning", model.messages[1]["content"])
        self.assertIn("Good morning.\n\nTranslation:", model.messages[1]["content"])
        self.assertTrue(model.messages[0]["content"].endswith("commentary. "))

    def test_translation_rejects_source_that_exceeds_model_context_budget(self):
        model = FakeModel()
        model.token_count = afrislm.MAX_SOURCE_TOKENS + 1
        with (
            patch.object(afrislm, "_load_model", return_value=model),
            self.assertRaisesRegex(ValueError, "too long"),
        ):
            afrislm.translate("Long source", "English", "Somali Latin", Path("model"))
        self.assertIsNone(model.messages)

    def test_translation_rejects_empty_generated_text(self):
        model = FakeModel("</think>")
        with (
            patch.object(afrislm, "_load_model", return_value=model),
            self.assertRaisesRegex(ValueError, "no translation"),
        ):
            afrislm.translate("Hello", "English", "Somali Latin", Path("model"))

    def test_translation_rejects_unclosed_thinking_block(self):
        model = FakeModel("<think>unfinished internal reasoning")
        with (
            patch.object(afrislm, "_load_model", return_value=model),
            self.assertRaisesRegex(ValueError, "incomplete thinking block"),
        ):
            afrislm.translate("Hello", "English", "Somali Latin", Path("model"))

    def test_translation_rejects_non_text_model_output(self):
        model = FakeModel(None)
        with (
            patch.object(afrislm, "_load_model", return_value=model),
            self.assertRaisesRegex(TypeError, "no text"),
        ):
            afrislm.translate("Hello", "English", "Somali Latin", Path("model"))
