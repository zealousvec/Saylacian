# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run bundled CTranslate2 models without downloads or external services."""

import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from .capabilities import get_capability
from .online_translation import (
    SERVICE_URL_ENV,
    selected_provider,
    translate_cloudflare,
    translate_self_hosted,
)
from .transliteration import Conversion

LANGUAGE_CODES = {"English": "en", "French": "fr", "Somali Latin": "so"}
MODEL_ROOT = Path(__file__).resolve().parents[2] / "models"
MULTILINGUAL_PAIRS = {"en_so", "so_en"}
MODEL_CACHE_SIZE = 3

PIVOT_ROUTES = {
    ("Somali Latin", "French"): "English",
    ("French", "Somali Latin"): "English",
}
_MODEL_LEADING_MARKERS = re.compile(r"^(?:[←▪❏▸○]\s*)+")
_SENTENCE_SPLIT = re.compile(r"[.!?…]+")
_SENTENCEPIECE_UNKNOWN_SURFACE = "\u2047"


def _synthetic_candidate_is_degenerate(source, output):
    """Conservatively reject identity and obvious repeated output from candidate."""
    if _SENTENCEPIECE_UNKNOWN_SURFACE in output:
        return True

    normalize = lambda value: " ".join(
        "".join(
            char
            for char in unicodedata.normalize("NFKC", value).casefold()
            if char.isalnum() or char.isspace()
        ).split()
    )
    if normalize(source) == normalize(output):
        return True
    word_count = lambda value: len(
        re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)
    )

    if word_count(output) > word_count(source) * 2 + 10:
        return True
    segments = [normalize(part) for part in _SENTENCE_SPLIT.split(output)]
    segments = [part for part in segments if part]
    if len(segments) != len(set(segments)):
        return True
    words = normalize(output).split()
    return bool(
        len(words) > 1
        and len(words[0]) >= 3
        and words[0] in words[1]
        and words[0] != words[1]
    )


def _clean_model_markers(text):
    return _MODEL_LEADING_MARKERS.sub("", text)


def _model_roots(root=None):
    if root is not None:
        return [Path(root)]
    from .model_packs import ModelPackManager

    return [*ModelPackManager().active_model_roots(), MODEL_ROOT]


def model_directory(source, target, root=None):
    if source not in LANGUAGE_CODES or target not in LANGUAGE_CODES:
        raise ValueError(
            "Meaning translation unavailable for this language or script. Choose English, French or Somali Latin."
        )
    pair = LANGUAGE_CODES[source] + "_" + LANGUAGE_CODES[target]
    if (source, target) in PIVOT_ROUTES:
        intermediate = PIVOT_ROUTES[(source, target)]
        return (
            model_directory(source, intermediate, root),
            model_directory(intermediate, target, root),
        )
    for model_root in _model_roots(root):
        folder = model_root / ("somali" if pair in MULTILINGUAL_PAIRS else "") / pair
        if pair in MULTILINGUAL_PAIRS:
            available = all(
                (folder / filename).is_file()
                for filename in (
                    "model.bin",
                    "config.json",
                    "shared_vocabulary.json",
                    "source.spm",
                    "target.spm",
                )
            )
        else:
            available = (folder / "model/model.bin").is_file() and (
                folder / "sentencepiece.model"
            ).is_file()
        if available:
            return folder
    raise ValueError(
        "No local model installed for this pair. Download its offline language pack first."
    )


@lru_cache(maxsize=MODEL_CACHE_SIZE)
def load_model(folder):
    try:
        import ctranslate2
        import sentencepiece
    except ImportError as error:
        raise ValueError("Local translation runtime is not installed.") from error
    folder = Path(folder)
    if (folder / "source.spm").is_file():
        source_tokenizer = sentencepiece.SentencePieceProcessor(
            model_file=str(folder / "source.spm")
        )
        target_tokenizer = sentencepiece.SentencePieceProcessor(
            model_file=str(folder / "target.spm")
        )
        engine = ctranslate2.Translator(
            str(folder), device="cpu", compute_type="int8", intra_threads=2
        )
        return (source_tokenizer, target_tokenizer), engine
    tokenizer = sentencepiece.SentencePieceProcessor(
        model_file=str(folder / "sentencepiece.model")
    )
    engine = ctranslate2.Translator(
        str(folder / "model"), device="cpu", compute_type="int8", intra_threads=2
    )
    return tokenizer, engine


def clear_model_cache():
    """Release cached model engines after pack removal or memory recovery."""
    load_model.cache_clear()


def translate_meaning(text, source, target, model_root=None, *, provider_override=None):
    if get_capability(source, target, "translation") is None:
        raise ValueError(
            "No verified offline meaning-translation route exists for this pair."
        )
    if not text.strip():
        return Conversion("")
    if len(text) > 4000:
        raise ValueError("Maximum 4,000 characters.")
    provider = provider_override or selected_provider()
    if provider in {"auto", "selfhosted", "cloudflare"}:
        failures = []
        candidates = []
        if provider == "selfhosted":
            candidates.append(("self-hosted", translate_self_hosted))
        elif provider == "cloudflare":
            candidates.append(("Cloudflare", translate_cloudflare))
        else:
            if os.environ.get(SERVICE_URL_ENV, "").strip():
                candidates.append(("self-hosted", translate_self_hosted))
            candidates.append(("Cloudflare", translate_cloudflare))
        for label, translate_online in candidates:
            try:
                translated, warnings = translate_online(text, source, target)
                return Conversion(translated, warnings)
            except ValueError as online_error:
                failures.append(f"{label}: {online_error}")
                if provider != "auto":
                    raise
        online_message = "; ".join(failures) or "No cloud provider configured."
        try:
            local = translate_meaning(
                text, source, target, model_root, provider_override="offline"
            )
        except ValueError as local_error:
            raise ValueError(
                f"{online_message} Downloaded-model fallback unavailable: {local_error}"
            ) from local_error
        return Conversion(
            local.text,
            (*local.warnings, "Cloud services unavailable; used downloaded model."),
        )
    if (source, target) in PIVOT_ROUTES:
        intermediate = PIVOT_ROUTES[(source, target)]
        first = translate_meaning(
            text, source, intermediate, model_root, provider_override=provider
        )
        second = translate_meaning(
            first.text, intermediate, target, model_root, provider_override=provider
        )
        warnings = tuple(
            dict.fromkeys(
                (
                    *first.warnings,
                    *second.warnings,
                    "Somali and French are translated through English, so some meaning may change.",
                )
            )
        )
        return Conversion(second.text, warnings)
    folder = model_directory(source, target, model_root)
    candidate_fallback = False
    candidate_fallback_reason = None
    if (source, target) == ("English", "Somali Latin"):
        candidate = next(
            (
                root / "somali" / "en_so_synthetic"
                for root in _model_roots(model_root)
                if (root / "somali" / "en_so_synthetic" / "model.bin").is_file()
            ),
            None,
        )
        if candidate is not None:
            candidate_tokenizer, candidate_engine = load_model(str(candidate))
            candidate_source, candidate_target = candidate_tokenizer
            candidate_tokens = candidate_source.encode(text, out_type=str)
            if len(candidate_tokens) > 400:
                raise ValueError(
                    "Input exceeds this model's 400-token limit; split it into shorter passages."
                )
            candidate_result = candidate_engine.translate_batch(
                [candidate_tokens],
                beam_size=4,
                max_input_length=0,
                max_decoding_length=512,
            )[0]
            candidate_text = candidate_target.decode(candidate_result.hypotheses[0])
            if _synthetic_candidate_is_degenerate(text, candidate_text):
                candidate_fallback = True
                word_count = lambda value: len(
                    re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)
                )
                source_words = word_count(text)
                output_words = word_count(candidate_text)
                if _SENTENCEPIECE_UNKNOWN_SURFACE in candidate_text:
                    candidate_fallback_reason = "The first result contained an unreadable symbol; an alternative was used."
                elif output_words > source_words * 2 + 10:
                    candidate_fallback_reason = (
                        "The first result was unusually long; an alternative was used."
                    )
                else:
                    candidate_fallback_reason = "The first result repeated or copied the input; an alternative was used."
            else:
                return Conversion(
                    candidate_text,
                    ("Somali translation may be inaccurate; check important details.",),
                )
    tokenizer, engine = load_model(str(folder))
    if folder.name in MULTILINGUAL_PAIRS:
        source_tokenizer, target_tokenizer = tokenizer
        tokens = source_tokenizer.encode(text, out_type=str)

        tokens = [">>som<<", *tokens, "</s>"]
        if len(tokens) > 400:
            raise ValueError(
                "Input exceeds this model's 400-token limit; split it into shorter passages."
            )
        result = engine.translate_batch(
            [tokens], beam_size=4, max_input_length=0, max_decoding_length=512
        )[0]
        decoded = target_tokenizer.decode(result.hypotheses[0])
        cleaned = _clean_model_markers(decoded)
        warnings = ["Somali translation may be inaccurate; check important details."]
        if candidate_fallback:
            warnings.append(candidate_fallback_reason)
        if cleaned != decoded:
            warnings.append("An extra symbol was removed from the output.")
        return Conversion(cleaned, tuple(warnings))
    tokens = tokenizer.encode(text, out_type=str)

    if len(tokens) > 400:
        raise ValueError(
            "Input exceeds this model's 400-token limit; split it into shorter passages."
        )
    result = engine.translate_batch(
        [tokens], max_input_length=0, max_decoding_length=512
    )[0]
    return Conversion(
        tokenizer.decode(result.hypotheses[0]),
        ("Machine translation; check important details.",),
    )
