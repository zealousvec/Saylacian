# SPDX-License-Identifier: AGPL-3.0-or-later
"""Download a pinned model pack and smoke-test local inference."""

from __future__ import annotations

import argparse
import json
import socket
import sys
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saylacian.core.model_packs import ModelPackManager
from saylacian.core.translation import translate_meaning

SAMPLES = {
    "french": (
        ("English", "French", "Hello, how are you?"),
        ("French", "English", "Bonjour, comment allez-vous?"),
    ),
    "somali": (
        ("English", "Somali Latin", "Thank you."),
        ("Somali Latin", "English", "Waad ku mahadsan tahay."),
    ),
}


def verify_pack(
    pack_id: str,
    manager: ModelPackManager | None = None,
    translator: Callable = translate_meaning,
    progress: Callable | None = None,
) -> list[tuple[str, str, int]]:
    """Install one selected pack, validate its active receipt, and run offline routes."""
    if pack_id not in SAMPLES:
        raise ValueError(f"Unsupported pack: {pack_id}")
    manager = manager or ModelPackManager()
    installed = manager.install(pack_id, progress=progress)
    installed = Path(installed).resolve()
    active_roots = {Path(root).resolve() for root in manager.active_model_roots()}
    if installed not in active_roots:
        raise RuntimeError("Installed pack is not the active model version.")
    receipt = json.loads((installed / "installed.json").read_text(encoding="utf-8"))
    if receipt.get("pack_id") != pack_id:
        raise RuntimeError("Installed model receipt has the wrong pack id.")
    if receipt.get("version") != manager.specs[pack_id]["version"]:
        raise RuntimeError("Installed model receipt has the wrong version.")

    results = []
    for source, target, sample in SAMPLES[pack_id]:
        with patch.object(
            socket.socket,
            "connect",
            side_effect=AssertionError(
                "Network access attempted during offline smoke."
            ),
        ):
            result = translator(sample, source, target, provider_override="offline")
        if not result.text.strip():
            raise RuntimeError(
                f"Offline smoke returned empty output for {source} → {target}."
            )
        results.append((source, target, len(result.text)))
    return results


def _progress_reporter(pack_id: str):
    last_reported = -10

    def report(current: int, total: int, message: str) -> None:
        nonlocal last_reported
        percentage = 100 if total == 0 else current * 100 // total
        if percentage >= last_reported + 10 or percentage == 100:
            print(f"{pack_id}: {percentage}% · {message}")
            last_reported = percentage

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=("french", "somali", "both"), required=True)
    args = parser.parse_args()
    pack_ids = tuple(SAMPLES) if args.pack == "both" else (args.pack,)
    manager = ModelPackManager()
    for pack_id in pack_ids:
        routes = verify_pack(pack_id, manager, progress=_progress_reporter(pack_id))
        summary = ", ".join(f"{source} -> {target}" for source, target, _ in routes)
        print(f"{pack_id}: pinned install and offline inference passed ({summary}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
