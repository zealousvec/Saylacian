# SPDX-License-Identifier: AGPL-3.0-or-later
"""Scan candidate source files for common credential formats without printing values."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {
    ".py",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".md",
    ".txt",
    ".kv",
    ".spec",
    ".ps1",
    ".bat",
    ".env",
}
SKIP_DIRS = {
    ".git",
    ".venv",
    ".kivy",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "wheelhouse",
}
PATTERNS = {
    "GitHub token": re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{50,})\b"
    ),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key block": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "API secret format": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "Bearer credential": re.compile(
        r"(?i)\bAuthorization\s*[:=]\s*Bearer\s+[A-Za-z0-9._~-]{20,}"
    ),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "GitLab token": re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    "Windows user profile path": re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s\"']+"),
}


def scan() -> list[tuple[str, str]]:
    findings = []
    git = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if git.returncode == 0:
        paths = [
            ROOT / item.decode("utf-8", "replace")
            for item in git.stdout.split(b"\0")
            if item
        ]
    else:
        paths = ROOT.rglob("*")
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.append((path.relative_to(ROOT).as_posix(), label))
    return findings


if __name__ == "__main__":
    matches = scan()
    if matches:
        print(
            f"Release safety scan found {len(matches)} possible credential pattern(s):"
        )
        for filename, label in matches:
            print(f"- {filename}: {label} (value redacted)")
        sys.exit(1)
    print("Release safety scan passed: no recognized credential patterns found.")
