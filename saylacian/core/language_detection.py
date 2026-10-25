# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline language identification with conservative abstention."""

import json
from functools import lru_cache
from pathlib import Path

SOMALI_DETECTION_PACK = "somali_detection_openlid"
OPENLID_SOMALI_THRESHOLD = 0.90

SUPPORTED = {"en": "English", "fr": "French", "so": "Somali Latin"}
MIN_CHARACTERS = 20
MIN_SHORT_CHARACTERS = 12
MIN_WORDS = 3
MIN_CONFIDENCE = 0.70
MIN_SHORT_CONFIDENCE = 0.75


@lru_cache(maxsize=1)
def _identifier():
    try:
        from py3langid.langid import MODEL_FILE, LanguageIdentifier
    except ImportError as error:
        raise ValueError("Offline language detection is not installed.") from error
    return LanguageIdentifier.from_model_file(MODEL_FILE, norm_probs=True)


class _OpenLIDDetector:
    def __init__(self, pack_root: Path):
        import numpy as np
        import onnxruntime
        from tokenizers import Tokenizer

        config = json.loads((pack_root / "config.json").read_text(encoding="utf-8"))
        labels = config.get("id2label", {})
        self.somali_index = next(
            (
                int(index)
                for index, label in labels.items()
                if str(label).split("_")[0].casefold() == "som"
            ),
            None,
        )
        if self.somali_index is None:
            raise ValueError("OpenLID model has no Somali output label.")

        self._numpy = np
        self._tokenizer = Tokenizer.from_file(str(pack_root / "tokenizer.json"))
        self._tokenizer.enable_truncation(max_length=96)
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self._session = onnxruntime.InferenceSession(
            str(pack_root / "model_quantized.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self._input_names = {item.name for item in self._session.get_inputs()}

    def somali_confidence(self, text: str) -> float:
        np = self._numpy
        encoding = self._tokenizer.encode(text)
        input_ids = np.asarray([encoding.ids], dtype=np.int64)
        attention_mask = np.asarray([encoding.attention_mask], dtype=np.int64)
        inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
        if "token_type_ids" in self._input_names:
            inputs["token_type_ids"] = np.zeros_like(input_ids)
        logits = self._session.run(
            None,
            {
                name: value
                for name, value in inputs.items()
                if name in self._input_names
            },
        )[0][0]
        logits = logits - np.max(logits)
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum()
        return float(probabilities[self.somali_index])


@lru_cache(maxsize=1)
def _load_openlid_detector(pack_root: str) -> _OpenLIDDetector:
    return _OpenLIDDetector(Path(pack_root))


def _openlid_somali_confidence(text: str) -> float | None:
    try:
        from .model_packs import ModelPackManager

        roots = ModelPackManager().active_model_roots({SOMALI_DETECTION_PACK})
        if not roots:
            _load_openlid_detector.cache_clear()
            return None
        return _load_openlid_detector(str(roots[0] / "openlid")).somali_confidence(text)
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
    ):
        return None


def detect_language(text):
    """Return (display name, confidence, message); abstain on short/uncertain text."""
    text = text.strip()
    if len(text) < MIN_SHORT_CHARACTERS or len(text.split()) < MIN_WORDS:
        return (
            None,
            0.0,
            "Add at least 12 characters and three words for language detection.",
        )

    code, confidence = _identifier().classify(text)
    threshold = MIN_SHORT_CONFIDENCE if len(text) < MIN_CHARACTERS else MIN_CONFIDENCE
    language = SUPPORTED.get(code)
    if language is not None and confidence >= threshold:
        return language, confidence, ""

    openlid_confidence = _openlid_somali_confidence(text)
    if (
        openlid_confidence is not None
        and openlid_confidence >= OPENLID_SOMALI_THRESHOLD
    ):
        return SUPPORTED["so"], openlid_confidence, ""

    if confidence < threshold:
        message = (
            "Short text is uncertain; add more text or choose the language manually."
            if len(text) < MIN_CHARACTERS
            else "Language is uncertain; choose it manually."
        )
        return None, confidence, message
    if language is None:
        return (
            None,
            confidence,
            "Detected language is not supported for local translation. Choose manually.",
        )
    return language, confidence, ""
