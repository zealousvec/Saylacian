# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch/verify the pinned offline models needed by a source checkout.

Downloads are opt-in, hash checked, and never overwrite an existing file.
Once prepared, Saylacian uses these files offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "models"
DATA_ROOT = ROOT / "saylacian" / "core" / "data"


def digest(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            h.update(block)
    return size, h.hexdigest()


def check_file(path: Path, item: dict) -> bool:
    if not path.is_file():
        return False
    size, checksum = digest(path)
    if size != item["bytes"] or checksum.lower() != item["sha256"].lower():
        raise ValueError(
            f"Existing model file has wrong size/hash; left untouched: {path}"
        )
    return True


def fetch(url: str, target: Path, item: dict, download: bool) -> None:
    if check_file(target, item):
        return
    if not download:
        raise FileNotFoundError(f"Missing pinned model file: {target}; use --download")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ValueError(f"Refusing to replace existing file: {target}")
    with tempfile.NamedTemporaryFile(
        prefix="saylacian-model-", dir=target.parent, delete=False
    ) as tmp:
        temp = Path(tmp.name)
        request = urllib.request.Request(
            url, headers={"User-Agent": "Saylacian-model-bootstrap/1.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                shutil.copyfileobj(response, tmp, length=1024 * 1024)
        except Exception:
            temp.unlink(missing_ok=True)
            raise
    try:
        size, checksum = digest(temp)
        if size != item["bytes"] or checksum.lower() != item["sha256"].lower():
            raise ValueError(
                f"Downloaded model failed pinned SHA-256/size check: {url}"
            )
        temp.rename(target)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    print(f"Verified download: {target.relative_to(ROOT)} ({item['bytes']:,} bytes)")


def extract_argos(pair: str, archive: Path, download: bool) -> int:
    files = {
        f"{pair}/model/model.bin": Path("model/model.bin"),
        f"{pair}/model/shared_vocabulary.txt": Path("model/shared_vocabulary.txt"),
        f"{pair}/sentencepiece.model": Path("sentencepiece.model"),
    }
    count = 0
    with zipfile.ZipFile(archive) as package:
        names = set(package.namelist())
        missing = set(files) - names
        if missing:
            raise ValueError(
                f"Pinned Argos archive lacks required members for {pair}: {sorted(missing)}"
            )
        for member, relative in files.items():
            target = MODEL_ROOT / pair / relative
            info = package.getinfo(member)
            item = {"bytes": info.file_size}
            with package.open(member) as src:
                h = hashlib.sha256()
                size = 0
                with tempfile.NamedTemporaryFile(
                    prefix="saylacian-model-", dir=archive.parent, delete=False
                ) as tmp:
                    temp = Path(tmp.name)
                    while block := src.read(1024 * 1024):
                        tmp.write(block)
                        h.update(block)
                        size += len(block)
            checksum = h.hexdigest()
            if target.is_file():
                existing_size, existing_hash = digest(target)
                if (existing_size, existing_hash) != (size, checksum):
                    temp.unlink(missing_ok=True)
                    raise ValueError(
                        f"Existing extracted model differs; left untouched: {target}"
                    )
                temp.unlink(missing_ok=True)
            elif not download:
                temp.unlink(missing_ok=True)
                raise FileNotFoundError(
                    f"Missing extracted model file: {target}; use --download"
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                temp.rename(target)
                print(
                    f"Extracted verified member: {target.relative_to(ROOT)} ({size:,} bytes)"
                )
            count += size
    return count


def generate_json_config(target: Path, item: dict, download: bool) -> int:
    """Recreate a tiny, documented CTranslate2 compatibility config."""
    data = json.dumps(item["generated_json"], ensure_ascii=False).encode("utf-8")
    if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError(
            f"Generated model config failed pinned size/SHA-256 check: {target}"
        )
    if target.is_file():
        if not check_file(target, item):
            raise ValueError(f"Could not verify generated config: {target}")
        return len(data)
    if not download:
        raise FileNotFoundError(
            f"Missing generated model config: {target}; use --download"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(
        f"Generated verified config: {target.relative_to(ROOT)} ({len(data):,} bytes)"
    )
    return len(data)


def hug_url(repo: str, revision: str, filename: str) -> str:
    safe_file = urllib.parse.quote(filename, safe="")
    return f"https://huggingface.co/{repo}/resolve/{revision}/{safe_file}?download=true"


def run(download: bool) -> int:
    argos_manifest = json.loads(
        (DATA_ROOT / "model_manifest.json").read_text(encoding="utf-8")
    )
    somali_manifest = json.loads(
        (DATA_ROOT / "somali_model_manifest.json").read_text(encoding="utf-8")
    )
    total = 0
    for item in argos_manifest:
        if "url" not in item:
            continue
        pair = item["pair"]
        archive = MODEL_ROOT / f"{pair}.argosmodel"
        fetch(item["url"], archive, item, download)
        total += item["bytes"]
        total += extract_argos(pair, archive, download)

    for item in somali_manifest:
        for name, metadata in item["files"].items():
            if "generated_json" in metadata:
                total += generate_json_config(
                    MODEL_ROOT / "somali" / item["pair"] / name, metadata, download
                )
                continue
            url = hug_url(item["repository"], item["revision"], name)
            fetch(url, MODEL_ROOT / "somali" / item["pair"] / name, metadata, download)
            total += metadata["bytes"]

    mode = "downloaded/prepared" if download else "verified"
    print(
        f"All pinned, downloadable offline model-pack assets {mode}: {total:,} bytes."
    )
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--download",
        action="store_true",
        help="download missing models and extract the required files",
    )
    mode.add_argument(
        "--verify-only",
        action="store_true",
        help="verify archives and every extracted model without network access",
    )
    args = parser.parse_args()
    run(download=args.download)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Model preparation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
