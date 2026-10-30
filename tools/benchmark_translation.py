# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run reproducible, local-only sentence samples for every bundled route."""

import argparse
import ctypes
import socket
import sys
import time
from ctypes import wintypes
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saylacian.core.translation import translate_meaning
from tools.benchmark_output import new_benchmark_output
from tools.benchmark_output import require_external_output
from tools.benchmark_output import save_json_atomic

EN = [
    "Hello.",
    "Good morning.",
    "How are you?",
    "Thank you.",
    "Please help me.",
    "The child is reading a book.",
    "I live in the city.",
    "We are going home.",
    "This water is cold.",
    "The door is open.",
]
FR = [
    "Bonjour.",
    "Bon matin.",
    "Comment allez-vous ?",
    "Merci.",
    "Aidez-moi, s’il vous plaît.",
    "L’enfant lit un livre.",
    "J’habite en ville.",
    "Nous rentrons à la maison.",
    "Cette eau est froide.",
    "La porte est ouverte.",
]
SO = [
    "Salaan.",
    "Subax wanaagsan.",
    "Sidee tahay?",
    "Mahadsanid.",
    "Fadlan i caawi.",
    "Ilmuhu buug buu akhrinayaa.",
    "Waxaan ku noolahay magaalada.",
    "Waxaan aadeynaa guriga.",
    "Biyahani waa qabow.",
    "Albaabku wuu furan yahay.",
]


def deny_network(*args, **kwargs):
    raise AssertionError("Offline benchmark attempted a network connection")


def peak_working_set_bytes():
    """Return this Windows process' peak resident working set."""

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize",
                "WorkingSetSize",
                "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage",
                "PagefileUsage",
                "PeakPagefileUsage",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    get_info = psapi.GetProcessMemoryInfo
    get_info.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
    get_info.restype = wintypes.BOOL
    ok = get_info(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    if not ok:
        return None
    return int(counters.PeakWorkingSetSize)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=new_benchmark_output("translation-routes"),
        help="result JSON path (default: unique file under local app data)",
    )
    args = parser.parse_args()
    try:
        output_path = require_external_output(args.output)
    except ValueError as error:
        parser.error(str(error))
    routes = [
        ("English", "French", EN),
        ("French", "English", FR),
        ("English", "Somali Latin", EN),
        ("Somali Latin", "English", SO),
        ("Somali Latin", "French", SO),
        ("French", "Somali Latin", FR),
    ]
    rows = []
    initial_rss = peak_working_set_bytes()
    with patch.object(socket.socket, "connect", deny_network):
        for source, target, sentences in routes:
            for text in sentences:
                start = time.perf_counter()
                result = translate_meaning(text, source, target)
                rows.append(
                    {
                        "source": source,
                        "target": target,
                        "input": text,
                        "output": result.text,
                        "warnings": list(result.warnings),
                        "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
                    }
                )
    peak_rss = peak_working_set_bytes()
    save_json_atomic(
        output_path,
        {
            "network": "socket.socket.connect patched to raise for entire run",
            "human_review": "not performed; outputs are raw model results",
            "route_sample_count": 10,
            "peak_process_working_set_bytes": peak_rss,
            "peak_process_working_set_note": (
                "Windows GetProcessMemoryInfo; includes Python runtime and "
                "loaded models, measured in this run."
            ),
            "samples": rows,
        },
    )
    print(f"Wrote {len(rows)} offline samples to {output_path}")
    print(f"Peak process working set: {peak_rss} bytes (initial: {initial_rss})")
    for source, target_name, _ in routes:
        selected = [
            row
            for row in rows
            if row["source"] == source and row["target"] == target_name
        ]
        mean_latency = sum(row["elapsed_ms"] for row in selected) / len(selected)
        print(
            f"{source} -> {target_name}: {len(selected)} cases; "
            f"mean {mean_latency:.1f} ms"
        )


if __name__ == "__main__":
    main()
