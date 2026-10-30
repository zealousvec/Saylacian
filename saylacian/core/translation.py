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
MODEL_TOKEN_LIMIT = 400
MODEL_CHUNK_TOKEN_TARGET = 380
AFRISLM_CONTEXT_LENGTH = 2048
AFRISLM_MAX_INPUT_TOKENS = 1700
AFRISLM_LONG_INPUT_THRESHOLD = 1200
AFRISLM_MAX_OUTPUT_TOKENS = 512
AFRISLM_PROMPT_TOKEN_RESERVE = 160

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


def _model_token_segments(text, tokenizer):
    """Keep model inputs within context while splitting only at whitespace."""
    tokens = tokenizer.encode(text, out_type=str)
    if len(tokens) <= MODEL_TOKEN_LIMIT:
        return (tokens,), (), "", "", False

    words = list(re.finditer(r"\S+", text))
    if not words:
        return (tokens,), (), "", "", False

    prefix = text[: words[0].start()]
    suffix = text[words[-1].end() :]
    chunks = []
    separators = []
    current = words[0].group()
    previous = words[0]

    for word in words[1:]:
        separator = text[previous.end() : word.start()]
        candidate = current + separator + word.group()
        candidate_tokens = tokenizer.encode(candidate, out_type=str)
        if len(candidate_tokens) <= MODEL_CHUNK_TOKEN_TARGET:
            current = candidate
        else:
            current_tokens = tokenizer.encode(current, out_type=str)
            if len(current_tokens) > MODEL_TOKEN_LIMIT:
                raise ValueError(
                    "A single unbroken input segment exceeds this model's 400-token limit; split it manually."
                )
            chunks.append(current_tokens)
            separators.append(separator or " ")
            current = word.group()
        previous = word

    current_tokens = tokenizer.encode(current, out_type=str)
    if len(current_tokens) > MODEL_TOKEN_LIMIT:
        raise ValueError(
            "A single unbroken input segment exceeds this model's 400-token limit; split it manually."
        )
    chunks.append(current_tokens)
    return tuple(chunks), tuple(separators), prefix, suffix, True


def _join_model_segments(outputs, separators, prefix="", suffix=""):
    """Join translated chunks with the exact source whitespace at split points."""
    if not outputs:
        return prefix + suffix
    joined = [prefix, outputs[0]]
    for separator, output in zip(separators, outputs[1:], strict=True):
        joined.extend((separator, output))
    joined.append(suffix)
    return "".join(joined)


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


@lru_cache(maxsize=1)
def load_afrislm_model(model_path):
    try:
        from llama_cpp import Llama
    except ImportError as error:
        raise ValueError(
            "The optional Somali model runtime is not installed. Install llama-cpp-python 0.3.36."
        ) from error
    return Llama(
        model_path=str(model_path),
        n_ctx=AFRISLM_CONTEXT_LENGTH,
        n_threads=max(2, min(8, os.cpu_count() or 2)),
        n_gpu_layers=0,
        verbose=False,
    )


def _afrislm_model_path():
    return next(
        (
            root / "somali" / "afrislm" / "model.gguf"
            for root in _model_roots()
            if (root / "somali" / "afrislm" / "model.gguf").is_file()
        ),
        None,
    )


def _afrislm_2b_model_path():
    return next(
        (
            root / "somali" / "afrislm_2b" / "model.gguf"
            for root in _model_roots()
            if (root / "somali" / "afrislm_2b" / "model.gguf").is_file()
        ),
        None,
    )


def _afrislm_4b_model_path():
    return next(
        (
            root / "somali" / "afrislm_4b" / "model.gguf"
            for root in _model_roots()
            if (root / "somali" / "afrislm_4b" / "model.gguf").is_file()
        ),
        None,
    )


def _translate_afrislm(text, source, target, model_path):
    try:
        model = load_afrislm_model(str(model_path))
        token_count = len(model.tokenize(text.encode("utf-8"), add_bos=False))
        if token_count > AFRISLM_MAX_INPUT_TOKENS:
            return (
                None,
                "Long text used the standard offline model to stay within context.",
            )
        max_tokens = 160
        if token_count > AFRISLM_LONG_INPUT_THRESHOLD:
            max_tokens = min(
                AFRISLM_MAX_OUTPUT_TOKENS,
                AFRISLM_CONTEXT_LENGTH - token_count - AFRISLM_PROMPT_TOKEN_RESERVE,
            )
        result = model.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional {source} to {target} translator. "
                        f"Your goal is to accurately convey the meaning and nuances of "
                        f"the original {source} text while adhering to {target} grammar, "
                        "vocabulary, and cultural sensitivities. Produce only the "
                        f"{target} translation, without any additional explanations "
                        "or commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Please translate the following {source} text into "
                        f"{target}: {text}\n\nTranslation:"
                    ),
                },
            ],
            max_tokens=max_tokens,
            temperature=0,
            top_p=1,
        )
    except MemoryError:
        load_afrislm_model.cache_clear()
        return (
            None,
            "The optional Somali model ran out of memory; used the standard offline model.",
        )
    except (OSError, RuntimeError):
        load_afrislm_model.cache_clear()
        return (
            None,
            "The optional Somali model could not run; used the standard offline model.",
        )

    content = result["choices"][0]["message"].get("content")
    translated = content.strip() if isinstance(content, str) else ""
    if "</think>" in translated:
        translated = translated.rsplit("</think>", 1)[-1].strip()
    if not translated:
        return (
            None,
            "The optional Somali model returned no text; used the standard offline model.",
        )
    return Conversion(
        translated,
        ("Alpha testing: have a fluent Somali speaker check important translations.",),
    ), None


def clear_model_cache():
    """Release cached model engines after pack removal or memory recovery."""
    load_model.cache_clear()
    load_afrislm_model.cache_clear()


def translate_meaning(text, source, target, model_root=None, *, provider_override=None):
    if get_capability(source, target, "translation") is None:
        raise ValueError("Choose English, French or Somali.")
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
    candidate_paths = []
    if (source, target) == ("English", "Somali Latin"):
        candidate_paths.append(_afrislm_model_path())
    elif (source, target) == ("Somali Latin", "English"):
        candidate_paths.extend(
            (
                _afrislm_4b_model_path(),
                _afrislm_2b_model_path(),
                _afrislm_model_path(),
            )
        )

    candidate_warning = None
    for candidate_path in filter(None, candidate_paths):
        try:
            candidate, fallback_warning = _translate_afrislm(
                text, source, target, candidate_path
            )
        except ValueError:
            candidate = None
            fallback_warning = (
                "Optional AfriSLM runtime unavailable; used the standard offline model."
            )
        if candidate is not None and _synthetic_candidate_is_degenerate(
            text, candidate.text
        ):
            candidate = None
            fallback_warning = (
                "The optional Somali model returned unreadable or repetitive text; "
                "used the standard offline model."
            )
        if candidate is not None:
            if candidate_warning:
                return Conversion(
                    candidate.text,
                    (
                        *candidate.warnings,
                        "The larger Somali model could not run; used the smaller model.",
                    ),
                    candidate.alternatives,
                )
            return candidate
        candidate_warning = fallback_warning

    try:
        folder = model_directory(source, target, model_root)
    except ValueError as error:
        if candidate_warning:
            raise ValueError(
                f"{candidate_warning} Download the Somali / English offline pack or install the optional runtime."
            ) from error
        raise
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
            candidate_tokens, candidate_separators, leading, trailing, chunked = (
                _model_token_segments(text, candidate_source)
            )
            candidate_results = candidate_engine.translate_batch(
                list(candidate_tokens),
                beam_size=4,
                max_input_length=0,
                max_decoding_length=512,
            )
            candidate_text = _join_model_segments(
                [
                    candidate_target.decode(result.hypotheses[0])
                    for result in candidate_results
                ],
                candidate_separators,
                leading,
                trailing,
            )
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
                warnings = [
                    "Somali translation may be inaccurate; check important details."
                ]
                if chunked:
                    warnings.append(
                        "Long text was split into independent segments; context may change at the joins."
                    )
                return Conversion(
                    candidate_text,
                    tuple(warnings),
                )
    tokenizer, engine = load_model(str(folder))
    if folder.name in MULTILINGUAL_PAIRS:
        source_tokenizer, target_tokenizer = tokenizer
        segments, separators, leading, trailing, chunked = _model_token_segments(
            text, source_tokenizer
        )
        token_batch = [[">>som<<", *segment, "</s>"] for segment in segments]
        if any(len(segment) > MODEL_TOKEN_LIMIT for segment in token_batch):
            raise ValueError(
                "A segmented input still exceeds this model's 400-token limit; split it manually."
            )
        results = engine.translate_batch(
            token_batch, beam_size=4, max_input_length=0, max_decoding_length=512
        )
        decoded = _join_model_segments(
            [target_tokenizer.decode(result.hypotheses[0]) for result in results],
            separators,
            leading,
            trailing,
        )
        cleaned = _clean_model_markers(decoded)
        warnings = ["Somali translation may be inaccurate; check important details."]
        if candidate_fallback:
            warnings.append(candidate_fallback_reason)
        if candidate_warning:
            warnings.append(candidate_warning)
        if cleaned != decoded:
            warnings.append("An extra symbol was removed from the output.")
        if chunked:
            warnings.append(
                "Long text was split into independent segments; context may change at the joins."
            )
        return Conversion(cleaned, tuple(warnings))
    segments, separators, leading, trailing, chunked = _model_token_segments(
        text, tokenizer
    )
    results = engine.translate_batch(
        list(segments), max_input_length=0, max_decoding_length=512
    )
    translated = _join_model_segments(
        [tokenizer.decode(result.hypotheses[0]) for result in results],
        separators,
        leading,
        trailing,
    )
    warnings = ["Machine translation; check important details."]
    if candidate_warning:
        warnings.append(candidate_warning)
    if chunked:
        warnings.append(
            "Long text was split into independent segments; context may change at the joins."
        )
    return Conversion(
        translated,
        tuple(warnings),
    )
