# SPDX-License-Identifier: AGPL-3.0-or-later
"""Optional local runner for the Somali-capable AfriSLM GGUF model."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

MODEL_FILENAME = "model.gguf"
MODEL_CONTEXT = 2048
MAX_SOURCE_TOKENS = 1200
_THINK_BLOCK = re.compile(r"(?s)<think>.*?</think>\s*")
_UNCLOSED_THINK_MARKER = re.compile(r"<think\b", re.IGNORECASE)
_MODEL_LANGUAGE_NAMES = {"Somali Latin": "Somali"}


def _inference_threads(cpu_count: int | None = None) -> int:
    """Keep optional large-model CPU use bounded on small devices."""
    cpu_count = cpu_count or os.cpu_count() or 1
    if cpu_count <= 4:
        return 1
    return min(4, cpu_count)


def should_use_large_model(cpu_count: int | None = None) -> bool:
    """Avoid starting the 0.8B model automatically on low-core devices."""
    cpu_count = cpu_count or os.cpu_count() or 1
    return cpu_count > 4


def _available_physical_memory_bytes() -> int | None:
    if os.name == "nt":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.available_physical)
        return None

    try:
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return None
    return int(available_pages * page_size)


def should_use_2b_model(
    cpu_count: int | None = None, available_memory_bytes: int | None = None
) -> bool:
    if cpu_count is None:
        cpu_count = os.cpu_count() or 1
    if cpu_count <= 4:
        return False
    if available_memory_bytes is None:
        available_memory_bytes = _available_physical_memory_bytes()
    return available_memory_bytes is not None and available_memory_bytes >= 4 * 1024**3


@lru_cache(maxsize=1)
def _load_model(model_path: str):
    try:
        from llama_cpp import Llama
    except ImportError as error:
        raise RuntimeError(
            "The optional Somali translation runtime is missing. Install it with "
            "the AfriSLM setup instructions, then retry."
        ) from error

    return Llama(
        model_path=model_path,
        n_ctx=MODEL_CONTEXT,
        n_threads=_inference_threads(),
        n_gpu_layers=0,
        verbose=False,
    )


def translate(text: str, source: str, target: str, model_folder: Path) -> str:
    """Translate one short passage with the downloaded local model."""
    model_path = Path(model_folder) / MODEL_FILENAME
    model = _load_model(str(model_path.resolve()))
    source_name = _MODEL_LANGUAGE_NAMES.get(source, source)
    target_name = _MODEL_LANGUAGE_NAMES.get(target, target)

    if len(model.tokenize(text.encode("utf-8"))) > MAX_SOURCE_TOKENS:
        raise ValueError("This passage is too long for the optional Somali model.")

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a professional {source_name} to {target_name} translator. "
                f"Your goal is to accurately convey the meaning and nuances of the "
                f"original {source_name} text while adhering to {target_name} grammar, "
                f"vocabulary, and cultural sensitivities. Produce only the "
                f"{target_name} translation, without any additional explanations "
                "or commentary. "
            ),
        },
        {
            "role": "user",
            "content": (
                f"Please translate the following {source_name} text into "
                f"{target_name}: {text}.\n\nTranslation:"
            ),
        },
    ]
    result = model.create_chat_completion(
        messages=messages,
        max_tokens=256,
        temperature=0.0,
    )
    output = result["choices"][0]["message"]["content"]
    if not isinstance(output, str):
        raise TypeError("The Somali model returned no text.")
    output = _THINK_BLOCK.sub("", output)
    if _UNCLOSED_THINK_MARKER.search(output):
        raise ValueError("The Somali model returned an incomplete thinking block.")
    output = re.sub(r"</think>", "", output, flags=re.IGNORECASE).strip()
    if not output:
        raise ValueError("The Somali model returned no translation.")
    return output


def clear_model_cache() -> None:
    """Release the optional model after its language pack is removed."""
    _load_model.cache_clear()
