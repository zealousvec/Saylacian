# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run bundled CTranslate2 models without downloads or external services."""

import os
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

from .afrislm import clear_model_cache as clear_afrislm_cache
from .afrislm import should_use_2b_model as should_use_2b_afrislm
from .afrislm import should_use_large_model as should_use_large_afrislm
from .afrislm import translate as translate_afrislm
from .capabilities import get_capability
from .online_translation import (
    SERVICE_URL_ENV,
    selected_provider,
    translate_cloudflare,
    translate_self_hosted,
)
from .transliteration import Conversion

LANGUAGE_CODES = {"English": "en", "French": "fr", "Somali Latin": "so"}
LINE_SEPARATORS = re.compile(r"(\r\n|[\r\n\u2028\u2029])")
MODEL_ROOT = Path(__file__).resolve().parents[2] / "models"
MULTILINGUAL_PAIRS = {"en_so", "so_en"}
EN_TO_SO_NO_REPEAT_NGRAM_SIZE = 3
SO_TO_EN_NO_REPEAT_NGRAM_SIZE = 2
SYNTHETIC_SOMALI_NO_REPEAT_NGRAM_SIZE = 2
SYNTHETIC_SOMALI_REPLACE_UNKNOWNS = True
MULTILINE_BATCH_SIZE = 16
MULTILINE_WARNING = "Line breaks were preserved; each line was translated separately, so context may change."


def _inference_profile(cpu_count=None):
    """Return a small CPU and model-cache profile for low-resource devices."""
    cpu_count = cpu_count or os.cpu_count() or 1
    if cpu_count <= 4:
        return 1, 2, 2
    return 2, 4, 3


INFERENCE_THREADS, INFERENCE_BEAM_SIZE, MODEL_CACHE_SIZE = _inference_profile()

PIVOT_ROUTES = {
    ("Somali Latin", "French"): "English",
    ("French", "Somali Latin"): "English",
}
_MODEL_LEADING_MARKERS = re.compile(r"^(?:[←▪❏▸○]\s*)+")
_SENTENCE_SPLIT = re.compile(r"[.!?…]+")
_SENTENCEPIECE_UNKNOWN_SURFACE = "\u2047"
_LONG_INPUT_BOUNDARY = re.compile(r"(?<=[.!?…。！？])\s+|\n+")
MAX_MODEL_INPUT_TOKENS = 400


def _synthetic_candidate_rejection_reason(source, output):
    """Identify why candidate output should fall back to the standard model."""
    if _SENTENCEPIECE_UNKNOWN_SURFACE in output:
        return "unknown_symbol"
    if output.rstrip().endswith(("...", "…")) and not source.rstrip().endswith(
        ("...", "…")
    ):
        return "trailing_ellipsis"

    def normalize(value):
        return " ".join(
            "".join(
                char
                for char in unicodedata.normalize("NFKC", value).casefold()
                if char.isalnum() or char.isspace()
            ).split()
        )

    if normalize(source) == normalize(output):
        return "copied_input"
    words = re.findall(r"[^\W_]+", output.casefold(), flags=re.UNICODE)
    source_word_count = len(re.findall(r"[^\W_]+", source.casefold(), flags=re.UNICODE))
    output_word_count = len(words)

    if output_word_count > source_word_count * 2 + 10:
        return "overlong"
    if _has_repeated_content_word(words):
        return "repeated_content_word"
    segments = [normalize(part) for part in _SENTENCE_SPLIT.split(output)]
    segments = [part for part in segments if part]
    if len(segments) != len(set(segments)):
        return "duplicate_sentence"
    words = normalize(output).split()
    if (
        len(words) > 1
        and len(words[0]) >= 3
        and words[0] in words[1]
        and words[0] != words[1]
    ):
        return "repeated_fragment"
    return None


def _synthetic_candidate_is_degenerate(source, output):
    """Reject incomplete, copied, repeated, unreadable or expanded candidate text."""
    return _synthetic_candidate_rejection_reason(source, output) is not None


def _has_repeated_content_word(words):
    return any(len(word) >= 4 and count >= 3 for word, count in Counter(words).items())


def _clean_model_markers(text):
    return _MODEL_LEADING_MARKERS.sub("", text)


def _model_roots(root=None):
    if root is not None:
        return [Path(root)]
    from .model_packs import ModelPackManager

    return [*ModelPackManager().active_model_roots(), MODEL_ROOT]


def _sentence_chunks(text, tokenizers, token_overheads=()):
    """Group complete sentences or paragraphs within each model's input limit."""
    fragments = []
    separators = []
    start = 0
    for match in _LONG_INPUT_BOUNDARY.finditer(text):
        fragments.append(text[start : match.start()])
        separators.append(match.group())
        start = match.end()
    fragments.append(text[start:])
    overheads = (*token_overheads, *(0 for _ in tokenizers))[: len(tokenizers)]

    def fits(value):
        return all(
            len(tokenizer.encode(value, out_type=str)) + overhead
            <= MAX_MODEL_INPUT_TOKENS
            for tokenizer, overhead in zip(tokenizers, overheads, strict=True)
        )

    if any(not fits(fragment) for fragment in fragments):
        raise ValueError(
            "A single sentence exceeds 400 model tokens; split it into shorter sentences."
        )

    chunks = []
    boundaries = []
    current = fragments[0]
    for separator, fragment in zip(separators, fragments[1:], strict=True):
        combined = current + separator + fragment
        if fits(combined):
            current = combined
        else:
            chunks.append(current)
            boundaries.append(separator)
            current = fragment
    chunks.append(current)
    return chunks, boundaries


def _translate_long_input(
    text, source, target, model_root, tokenizers, token_overheads=()
):
    chunks, boundaries = _sentence_chunks(text, tokenizers, token_overheads)
    if len(chunks) == 1:
        raise ValueError(
            "Input exceeds this model's 400-token limit; split it into shorter sentences."
        )
    results = [
        translate_meaning(
            chunk,
            source,
            target,
            model_root,
            provider_override="offline",
        )
        for chunk in chunks
    ]
    translated = []
    warnings = []
    for index, result in enumerate(results):
        translated.append(result.text)
        warnings.extend(result.warnings)
        if index < len(boundaries):
            translated.append(boundaries[index])
    warnings.append(
        "Long text was split at sentence or paragraph boundaries; context between sections may change."
    )
    return Conversion("".join(translated), tuple(dict.fromkeys(warnings)))


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
            str(folder),
            device="cpu",
            compute_type="int8",
            intra_threads=INFERENCE_THREADS,
        )
        return (source_tokenizer, target_tokenizer), engine
    tokenizer = sentencepiece.SentencePieceProcessor(
        model_file=str(folder / "sentencepiece.model")
    )
    engine = ctranslate2.Translator(
        str(folder / "model"),
        device="cpu",
        compute_type="int8",
        intra_threads=INFERENCE_THREADS,
    )
    return tokenizer, engine


def clear_model_cache():
    """Release cached model engines after pack removal or memory recovery."""
    load_model.cache_clear()
    clear_afrislm_cache()


def _translate_offline_multiline(text, source, target, model_root):
    """Batch independent French/English lines without changing their order."""
    parts = LINE_SEPARATORS.split(text)
    records = []
    for index in range(0, len(parts), 2):
        line = parts[index]
        if not line.strip():
            continue
        leading = line[: len(line) - len(line.lstrip(" \t"))]
        trailing = line[len(line.rstrip(" \t")) :]
        content_end = len(line) - len(trailing) if trailing else len(line)
        records.append((index, leading, trailing, line[len(leading) : content_end]))

    if not records:
        return Conversion(text, (MULTILINE_WARNING,))

    folder = model_directory(source, target, model_root)
    tokenizer, engine = load_model(str(folder))
    encoded_lines = [
        tokenizer.encode(content, out_type=str)
        for _index, _leading, _trailing, content in records
    ]
    if any(len(tokens) > MAX_MODEL_INPUT_TOKENS for tokens in encoded_lines):
        return None

    translated_lines = []
    for start in range(0, len(encoded_lines), MULTILINE_BATCH_SIZE):
        token_batch = encoded_lines[start : start + MULTILINE_BATCH_SIZE]
        try:
            results = engine.translate_batch(
                token_batch,
                max_input_length=0,
                max_decoding_length=512,
            )
        except (MemoryError, RuntimeError):
            return None
        if len(results) != len(token_batch):
            return None
        translated_lines.extend(
            tokenizer.decode(result.hypotheses[0]) for result in results
        )

    translated_by_index = {
        index: leading + translated + trailing
        for (index, leading, trailing, _content), translated in zip(
            records, translated_lines, strict=True
        )
    }
    output = []
    for index, part in enumerate(parts):
        output.append(translated_by_index.get(index, part))

    return Conversion(
        "".join(output),
        ("Machine translation; check important details.", MULTILINE_WARNING),
    )


def translate_meaning(text, source, target, model_root=None, *, provider_override=None):
    if get_capability(source, target, "translation") is None:
        raise ValueError("Choose English, French or Somali.")
    if not text.strip():
        return Conversion("")
    if len(text) > 4000:
        raise ValueError("Maximum 4,000 characters.")
    provider = provider_override or selected_provider()
    if LINE_SEPARATORS.search(text):
        if provider == "offline" and (source, target) in {
            ("English", "French"),
            ("French", "English"),
        }:
            batched = _translate_offline_multiline(text, source, target, model_root)
            if batched is not None:
                return batched

        parts = LINE_SEPARATORS.split(text)
        translated_parts = []
        warnings = []
        for index in range(0, len(parts), 2):
            line = parts[index]
            if line.strip():
                leading = line[: len(line) - len(line.lstrip(" \t"))]
                trailing = line[len(line.rstrip(" \t")) :]
                content_end = len(line) - len(trailing) if trailing else len(line)
                content = line[len(leading) : content_end]
                result = translate_meaning(
                    content,
                    source,
                    target,
                    model_root,
                    provider_override=provider,
                )
                translated_parts.extend((leading, result.text, trailing))
                warnings.extend(result.warnings)
            else:
                translated_parts.append(line)
            if index + 1 < len(parts):
                translated_parts.append(parts[index + 1])
        warnings.append(MULTILINE_WARNING)
        return Conversion("".join(translated_parts), tuple(dict.fromkeys(warnings)))
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
    afrislm_2b_folder = next(
        (
            root / "somali" / "en_so_afrislm_2b"
            for root in _model_roots(model_root)
            if (root / "somali" / "en_so_afrislm_2b" / "model.gguf").is_file()
        ),
        None,
    )
    afrislm_folder = next(
        (
            root / "somali" / "en_so_afrislm"
            for root in _model_roots(model_root)
            if (root / "somali" / "en_so_afrislm" / "model.gguf").is_file()
        ),
        None,
    )
    afrislm_selection_warning = None
    if afrislm_2b_folder is not None:
        if should_use_2b_afrislm():
            afrislm_folder = afrislm_2b_folder
        elif afrislm_folder is not None and should_use_large_afrislm():
            afrislm_selection_warning = (
                "AfriSLM 2B was skipped because this device does not meet its "
                "resource check; the smaller AfriSLM pack was used."
            )
        else:
            afrislm_folder = None
            afrislm_selection_warning = (
                "AfriSLM 2B was skipped because this device does not meet its "
                "resource check; another installed Somali model was used."
            )
    elif afrislm_folder is not None and not should_use_large_afrislm():
        afrislm_folder = None
        afrislm_selection_warning = "AfriSLM was skipped on this low-core device; a smaller Somali model was used."
    if afrislm_selection_warning and afrislm_folder is None:
        candidate_fallback = True
        candidate_fallback_reason = afrislm_selection_warning
    if afrislm_folder is not None and (source, target) in {
        ("English", "Somali Latin"),
        ("Somali Latin", "English"),
    }:
        if not candidate_fallback:
            try:
                candidate_text = translate_afrislm(text, source, target, afrislm_folder)
            except (OSError, RuntimeError, TypeError, ValueError):
                candidate_fallback = True
                candidate_fallback_reason = "AfriSLM could not handle this request; another installed Somali model was used."
            else:
                rejection_reason = _synthetic_candidate_rejection_reason(
                    text, candidate_text
                )
                if rejection_reason is None:
                    return Conversion(
                        candidate_text,
                        tuple(
                            warning
                            for warning in (
                                "Somali translation may be inaccurate; check important details.",
                                afrislm_selection_warning,
                            )
                            if warning
                        ),
                    )
                candidate_fallback = True
                candidate_fallback_reason = (
                    "AfriSLM output was flagged as incomplete or repetitive; "
                    "another installed Somali model was used."
                )
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
            try:
                candidate_tokenizer, candidate_engine = load_model(str(candidate))
                candidate_source, candidate_target = candidate_tokenizer
                candidate_tokens = candidate_source.encode(text, out_type=str)
                if len(candidate_tokens) <= MAX_MODEL_INPUT_TOKENS:
                    candidate_result = candidate_engine.translate_batch(
                        [candidate_tokens],
                        beam_size=INFERENCE_BEAM_SIZE,
                        no_repeat_ngram_size=SYNTHETIC_SOMALI_NO_REPEAT_NGRAM_SIZE,
                        replace_unknowns=SYNTHETIC_SOMALI_REPLACE_UNKNOWNS,
                        max_input_length=0,
                        max_decoding_length=512,
                    )[0]
                    candidate_text = candidate_target.decode(
                        candidate_result.hypotheses[0]
                    )
            except (IndexError, OSError, RuntimeError, TypeError, ValueError):
                candidate_fallback = True
                candidate_fallback_reason = (
                    "Optional Somali model could not run; the standard model was used."
                )
            else:
                if len(candidate_tokens) > MAX_MODEL_INPUT_TOKENS:
                    baseline_tokenizers, _baseline_engine = load_model(str(folder))
                    baseline_source = (
                        baseline_tokenizers[0]
                        if isinstance(baseline_tokenizers, tuple)
                        else baseline_tokenizers
                    )
                    return _translate_long_input(
                        text,
                        source,
                        target,
                        model_root,
                        (candidate_source, baseline_source),
                        token_overheads=(0, 2),
                    )
                rejection_reason = _synthetic_candidate_rejection_reason(
                    text, candidate_text
                )
                if rejection_reason is not None:
                    candidate_fallback = True
                    candidate_fallback_reason = {
                        "unknown_symbol": (
                            "The first result contained an unreadable symbol; "
                            "an alternative was used."
                        ),
                        "trailing_ellipsis": (
                            "The first result appeared unfinished; an alternative was used."
                        ),
                        "copied_input": (
                            "The first result repeated or copied the input; "
                            "an alternative was used."
                        ),
                        "overlong": (
                            "The first result was unusually long; an alternative was used."
                        ),
                        "repeated_content_word": (
                            "The first result repeated a word several times; "
                            "an alternative was used."
                        ),
                        "duplicate_sentence": (
                            "The first result repeated a sentence; an alternative was used."
                        ),
                        "repeated_fragment": (
                            "The first result repeated an incomplete word; "
                            "an alternative was used."
                        ),
                    }[rejection_reason]
                else:
                    return Conversion(
                        candidate_text,
                        tuple(
                            warning
                            for warning in (
                                candidate_fallback_reason,
                                "Somali translation may be inaccurate; check important details.",
                            )
                            if warning
                        ),
                    )
    tokenizer, engine = load_model(str(folder))
    if folder.name in MULTILINGUAL_PAIRS:
        source_tokenizer, target_tokenizer = tokenizer
        language_prefix = (">>som<<",) if folder.name == "en_so" else ()
        tokens = [
            *language_prefix,
            *source_tokenizer.encode(text, out_type=str),
            "</s>",
        ]
        if len(tokens) > MAX_MODEL_INPUT_TOKENS:
            return _translate_long_input(
                text,
                source,
                target,
                model_root,
                (source_tokenizer,),
                token_overheads=(len(language_prefix) + 1,),
            )
        result = engine.translate_batch(
            [tokens],
            beam_size=INFERENCE_BEAM_SIZE,
            no_repeat_ngram_size=(
                EN_TO_SO_NO_REPEAT_NGRAM_SIZE
                if target == "Somali Latin"
                else SO_TO_EN_NO_REPEAT_NGRAM_SIZE
            ),
            max_input_length=0,
            max_decoding_length=512,
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

    if len(tokens) > MAX_MODEL_INPUT_TOKENS:
        return _translate_long_input(text, source, target, model_root, (tokenizer,))
    result = engine.translate_batch(
        [tokens], max_input_length=0, max_decoding_length=512
    )[0]
    return Conversion(
        tokenizer.decode(result.hypotheses[0]),
        ("Machine translation; check important details.",),
    )
