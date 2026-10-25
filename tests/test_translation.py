import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from saylacian.core import translation


class FakeTokenizer:
    def encode(self, text, out_type=str):
        return text.split()

    def decode(self, tokens):
        return "translated text"


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


if __name__ == "__main__":
    unittest.main()
