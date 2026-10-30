# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify a Saylacian package read back from the real Windows clipboard."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from saylacian.core.interchange import decode_saylacian_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reader-evidence", required=True)
    parser.add_argument("--expected-latin", required=True)
    parser.add_argument("--script", required=True)
    args = parser.parse_args()
    evidence = json.loads(Path(args.reader_evidence).read_text(encoding="utf-8-sig"))
    package = decode_saylacian_text(evidence["unicode_fallback"])
    if package.script != args.script or package.latin != args.expected_latin:
        raise SystemExit(
            "External clipboard package did not decode to the expected "
            "script and Latin reading."
        )
    print(
        f"Clipboard round-trip: {package.script}, {len(package.text)} glyphs, "
        f"{package.latin}"
    )


if __name__ == "__main__":
    main()
