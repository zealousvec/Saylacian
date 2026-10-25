# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline language identification with conservative abstention."""

from functools import lru_cache

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
    if confidence < threshold:
        message = (
            "Short text is uncertain; add more text or choose the language manually."
            if len(text) < MIN_CHARACTERS
            else "Language is uncertain; choose it manually."
        )
        return None, confidence, message
    language = SUPPORTED.get(code)
    if language is None:
        return (
            None,
            confidence,
            "Detected language is not supported for local translation. Choose manually.",
        )
    return language, confidence, ""
