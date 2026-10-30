# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build a checksummed, portable Windows ZIP from the pinned PyInstaller spec."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from saylacian import __version__

DOCS_TO_COPY = {
    ROOT / "LICENSE": "LICENSE.txt",
    ROOT / "docs" / "THIRD_PARTY_NOTICES.md": "THIRD_PARTY_NOTICES.txt",
    ROOT / "docs" / "USER_GUIDE.md": "USER_GUIDE.txt",
    ROOT / "docs" / "OFFLINE_PACKS.md": "OFFLINE_PACKS.txt",
    ROOT / "docs" / "SUPPORT_MATRIX.md": "SUPPORT_MATRIX.txt",
}
INSTALL_NOTES = f"""Saylacian for Windows — alpha testing
Version: {__version__}

Extract the complete Saylacian folder, then run Saylacian.exe. Keep the folder
contents together. No model weights are included in this ZIP.

Open Offline language packs in the app to download the models you want. The app
checks each download before using it. Once installed, supported packs run locally.
The 4B Somali-to-English pack needs substantial memory (about 5 GB in one test).

Somali translation needs fluent-speaker review. Borama and Kaddare cover selected
chart entries and use Saylacian private-use glyphs. Old Nubian provides a limited
29-character reading table; it is not meaning translation. Modern Nubian varieties
are not supported. See SUPPORT_MATRIX.txt and USER_GUIDE.txt for details.

This ZIP is unsigned and its runtime has not been verified on a clean Windows PC.
Windows may block an unsigned candidate. Do not bypass Windows security settings.
See THIRD_PARTY_NOTICES.txt and LICENSE.txt for source and asset terms.
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_metadata() -> dict[str, str | bool]:
    """Fingerprint the checked-in and non-ignored files used for this build."""
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    tree_digest = hashlib.sha256()
    tree_digest.update(status)
    for raw_path in sorted(filter(None, tracked.split(b"\0"))):
        relative = Path(os.fsdecode(raw_path))
        path = ROOT / relative
        tree_digest.update(relative.as_posix().encode("utf-8"))
        tree_digest.update(b"\0")
        if path.is_file():
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    tree_digest.update(chunk)
        else:
            tree_digest.update(b"<missing>")
        tree_digest.update(b"\0")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "source_commit": commit,
        "source_tree_dirty": bool(status),
        "source_tree_sha256": tree_digest.hexdigest(),
    }


def build_environment(config_root: Path | None = None) -> dict[str, str]:
    """Isolate builder caches and drop unrelated inherited native-library paths."""
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        entry
        for entry in environment.get("PATH", "").split(os.pathsep)
        if "codex-runtimes" not in entry.casefold()
        and "poppler" not in entry.casefold()
    )
    if config_root is not None:
        pyinstaller_config = config_root / "pyinstaller"
        kivy_config = config_root / "kivy"
        pyinstaller_config.mkdir(parents=True, exist_ok=True)
        kivy_config.mkdir(parents=True, exist_ok=True)
        environment["PYINSTALLER_CONFIG_DIR"] = str(pyinstaller_config)
        environment["KIVY_HOME"] = str(kivy_config)
    return environment


def payload_manifest(folder: Path) -> dict:
    paths = sorted(folder.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("The candidate contains a symbolic link; packaging stopped.")
    entries = [
        {
            "path": path.relative_to(folder).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in paths
        if path.is_file() and path.name != "SHA256SUMS.txt"
    ]
    return {
        "app_version": __version__,
        "runtime_verified": False,
        "build_recipe": "Saylacian.spec; PyInstaller 6.22.3",
        **source_metadata(),
        "files": entries,
    }


def write_checksums(folder: Path, manifest: dict) -> None:
    lines = [f"{item['sha256']}  {item['path']}" for item in manifest["files"]]
    (folder / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")


def restore_legacy_font_path(payload: Path) -> Path:
    """Place the bundled Osmanya font where the recovered KV screen expects it."""
    assets = payload / "_internal" / "assets"
    source = assets / "NotoSansOsmanya.ttf"
    if not source.is_file():
        raise FileNotFoundError(f"PyInstaller did not bundle {source}")
    destination = assets / "original" / "Fonts" / "Noto Sans Osmanya.ttf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def verify_zip(archive: Path, manifest: dict) -> None:
    expected = {item["path"]: item["sha256"] for item in manifest["files"]}
    with zipfile.ZipFile(archive) as bundle:
        actual_names = {
            name.removeprefix("Saylacian/")
            for name in bundle.namelist()
            if not name.endswith("/")
        }
        if actual_names != set(expected) | {"SHA256SUMS.txt"}:
            raise ValueError("Portable ZIP contents differ from its manifest")
        for name, expected_hash in expected.items():
            if (
                hashlib.sha256(bundle.read(f"Saylacian/{name}")).hexdigest()
                != expected_hash
            ):
                raise ValueError(f"Portable ZIP hash mismatch: {name}")


def build(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    output_root = args.distpath.resolve()
    work_root = args.workpath.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=True, exist_ok=True)
    payload = output_root / "Saylacian"
    archive = args.archive.resolve()
    manifest_path = output_root / "Saylacian-Portable.manifest.json"
    digest_path = archive.with_suffix(archive.suffix + ".sha256")
    if any(path.exists() for path in (payload, archive, manifest_path, digest_path)):
        raise FileExistsError(
            "Build output already exists. Choose a new distpath and archive name; "
            "existing candidate files are preserved."
        )
    if any(work_root.iterdir()):
        raise FileExistsError(
            "Build work directory is not empty. Choose a new workpath to preserve its files."
        )
    version = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if version != "6.22.3":
        raise RuntimeError(f"PyInstaller 6.22.3 is required; found {version}.")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--log-level",
        "WARN",
        "--distpath",
        str(output_root),
        "--workpath",
        str(work_root),
        str(ROOT / "Saylacian.spec"),
    ]
    build_log = work_root / "pyinstaller.log"
    try:
        with build_log.open("w", encoding="utf-8") as log_stream:
            subprocess.run(
                command,
                cwd=ROOT,
                env=build_environment(work_root / "config"),
                stdout=log_stream,
                stderr=subprocess.STDOUT,
                check=True,
            )
    except subprocess.CalledProcessError as error:
        log_lines = build_log.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = "\n".join(log_lines[-80:])
        raise RuntimeError(
            f"PyInstaller failed; last log lines from {build_log}:\n{tail}"
        ) from error
    executable = payload / "Saylacian.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"PyInstaller did not produce {executable}")
    for source, destination in DOCS_TO_COPY.items():
        shutil.copy2(source, payload / destination)
    restore_legacy_font_path(payload)
    (payload / "INSTALL.txt").write_text(INSTALL_NOTES, encoding="utf-8")
    manifest = payload_manifest(payload)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_checksums(payload, manifest)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as bundle:
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(
                    f"Saylacian/{path.relative_to(payload).as_posix()}",
                    date_time=(2020, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(
                    info,
                    path.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=6,
                )
    verify_zip(archive, manifest)
    digest_path.write_text(f"{sha256(archive)}  {archive.name}\n", encoding="ascii")
    return archive, manifest_path, digest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distpath", type=Path, default=ROOT / "dist" / "portable")
    parser.add_argument("--workpath", type=Path, default=ROOT / "build" / "portable")
    parser.add_argument(
        "--archive", type=Path, default=ROOT / "dist" / "Saylacian-Portable.zip"
    )
    args = parser.parse_args()
    archive, manifest, digest = build(args)
    print(f"ZIP: {archive} ({archive.stat().st_size:,} bytes)")
    print(f"Manifest: {manifest}")
    print(f"SHA-256: {digest.read_text(encoding='ascii').strip()}")
    print(
        "runtime_verified=false; use an authorized isolated Windows host for launch checks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
