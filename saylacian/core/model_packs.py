# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pinned, versioned offline model packs with atomic installation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import threading
import urllib.parse
import urllib.request
import uuid
import zipfile
from functools import lru_cache
from pathlib import Path, PurePosixPath, PureWindowsPath

DATA_ROOT = Path(__file__).resolve().parent / "data"
_SAFE_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def default_store_root() -> Path:
    configured = os.environ.get("SAYLACIAN_PACKS_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "Saylacian" / "model-packs"


def _safe_relative(value: str) -> Path:
    if not isinstance(value, str) or "\\" in value or PureWindowsPath(value).drive:
        raise ValueError("Invalid model pack path in manifest.")
    parsed = PurePosixPath(value)
    if (
        parsed.is_absolute()
        or not parsed.parts
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise ValueError("Invalid model pack path in manifest.")
    return Path(*parsed.parts)


def _safe_component(value: str, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_COMPONENT.fullmatch(value):
        raise ValueError(f"Invalid model pack {label}.")
    return value


def _pack_home(store_root: Path, pack_id: str) -> tuple[Path, Path]:
    store = store_root.resolve()
    requested_home = store / _safe_component(pack_id, "id")
    home = requested_home.resolve()
    if home != requested_home or home.parent != store:
        raise ValueError("Language pack path escaped the configured storage directory.")
    return store, home


def _version_folder(home: Path, version: str) -> Path:
    requested_folder = home.resolve() / _safe_component(version, "version")
    folder = requested_folder.resolve()
    if folder != requested_folder or folder.parent != home.resolve():
        raise ValueError("Model pack version escaped its storage directory.")
    return folder


def _installed_file(folder: Path, relative_path: str) -> Path:
    candidate = folder / _safe_relative(relative_path)
    resolved = candidate.resolve()
    if folder.resolve() not in resolved.parents:
        raise ValueError("Installed model file escaped its version directory.")
    return resolved


def _huggingface_url(repository: str, revision: str, filename: str) -> str:
    safe_file = urllib.parse.quote(filename, safe="")
    return f"https://huggingface.co/{repository}/resolve/{revision}/{safe_file}?download=true"


def get_pack_specs() -> dict[str, dict]:
    """Build downloadable packs from the same pinned manifests used by the app."""
    argos = json.loads((DATA_ROOT / "model_manifest.json").read_text(encoding="utf-8"))
    somali = json.loads(
        (DATA_ROOT / "somali_model_manifest.json").read_text(encoding="utf-8")
    )
    detection = json.loads(
        (DATA_ROOT / "somali_detection_manifest.json").read_text(encoding="utf-8")
    )

    somali_assets = []
    for item in somali:
        for filename, metadata in item["files"].items():
            if "generated_json" in metadata:
                somali_assets.append(
                    {
                        "kind": "generated-json",
                        "content": metadata["generated_json"],
                        "bytes": metadata["bytes"],
                        "sha256": metadata["sha256"],
                        "destination": f"somali/{item['pair']}/{filename}",
                        "license": item["license"],
                        "repository": item["repository"],
                        "revision": item["revision"],
                        "runtimes": item["runtimes"],
                    }
                )
                continue
            somali_assets.append(
                {
                    "kind": "file",
                    "url": _huggingface_url(
                        item["repository"], item["revision"], filename
                    ),
                    "bytes": metadata["bytes"],
                    "sha256": metadata["sha256"],
                    "destination": f"somali/{item['pair']}/{filename}",
                    "license": item["license"],
                    "repository": item["repository"],
                    "revision": item["revision"],
                    "runtimes": item["runtimes"],
                }
            )
    french_assets = []
    for item in argos:
        if item.get("pair") not in {"en_fr", "fr_en"} or "url" not in item:
            continue
        french_assets.append(
            {
                "kind": "argos-archive",
                "url": item["url"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "pair": item["pair"],
                "license": item["license"],
                "repository": item["repository"],
                "revision": item["revision"],
                "runtimes": item["runtimes"],
            }
        )

    detection_assets = []
    for item in detection["files"]:
        filename = item["file"]
        detection_assets.append(
            {
                "kind": "file",
                "url": _huggingface_url(
                    detection["repository"], detection["revision"], filename
                ),
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "destination": f"openlid/{Path(filename).name}",
                "license": detection["license"],
                "repository": detection["repository"],
                "revision": detection["revision"],
                "runtimes": detection["runtimes"],
            }
        )

    somali_manifest_item = somali[0]
    french_manifest_items = [
        item for item in argos if item.get("pair") in {"en_fr", "fr_en"}
    ]
    specs = {
        "somali": {
            "title": "Somali / English",
            "license": somali_manifest_item["license"],
            "model_repositories": sorted({item["repository"] for item in somali}),
            "runtimes": somali_manifest_item["runtimes"],
            "assets": somali_assets,
        },
        "french": {
            "title": "French / English",
            "license": french_manifest_items[0]["license"],
            "model_repositories": sorted(
                {item["repository"] for item in french_manifest_items}
            ),
            "runtimes": french_manifest_items[0]["runtimes"],
            "assets": french_assets,
        },
        "somali_detection_openlid": {
            "title": "Somali detection (experimental)",
            "license": detection["license"],
            "model_repositories": [detection["repository"]],
            "runtimes": detection["runtimes"],
            "assets": detection_assets,
        },
    }
    for pack_id, spec in specs.items():
        version_input = json.dumps(
            {
                key: spec[key]
                for key in ("license", "model_repositories", "runtimes", "assets")
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(version_input.encode()).hexdigest()[:12]
        spec["id"] = pack_id
        spec["version"] = f"1-{digest}"
        spec["download_bytes"] = sum(
            asset["bytes"]
            for asset in spec["assets"]
            if asset["kind"] != "generated-json"
        )
    return specs


def _hash(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


@lru_cache(maxsize=64)
def _cached_file_hash(
    path: str, size: int, modified_ns: int, changed_ns: int, device: int, inode: int
) -> tuple[int, str]:
    return _hash(Path(path))


def _matches_installed_file(path: Path, record: dict) -> bool:
    if not isinstance(record, dict):
        return False
    expected_size = record.get("bytes")
    expected_hash = record.get("sha256")
    if (
        not isinstance(expected_size, int)
        or expected_size < 0
        or not isinstance(expected_hash, str)
        or len(expected_hash) != 64
    ):
        return False
    if not path.is_file():
        return False
    details = path.stat()
    if details.st_size != expected_size:
        return False
    actual_size, actual_hash = _cached_file_hash(
        str(path.resolve()),
        details.st_size,
        details.st_mtime_ns,
        details.st_ctime_ns,
        details.st_dev,
        details.st_ino,
    )
    return actual_size == expected_size and actual_hash.lower() == expected_hash.lower()


def _installed_files_match(folder: Path, manifest: dict) -> bool:
    if not isinstance(manifest, dict):
        return False
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return False
    return all(
        isinstance(item, dict)
        and _matches_installed_file(_installed_file(folder, item.get("path")), item)
        for item in files
    )


def _lock_for(pack_id: str) -> threading.Lock:
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(pack_id, threading.Lock())


class ModelPackManager:
    def __init__(self, store_root: Path | str | None = None, specs: dict | None = None):
        self.store_root = (
            Path(store_root) if store_root is not None else default_store_root()
        )
        self.specs = specs if specs is not None else get_pack_specs()

    def list_packs(self) -> list[dict]:
        packs = []
        for pack_id, spec in self.specs.items():
            try:
                _, pack_home = _pack_home(self.store_root, pack_id)
            except ValueError:
                continue
            current_version = None
            installed_bytes = 0
            damaged = False
            try:
                pointer = _installed_file(pack_home, "current.json")
                if pointer.is_file():
                    current_version = _safe_component(
                        json.loads(pointer.read_text(encoding="utf-8"))["version"],
                        "version",
                    )
                    folder = _version_folder(pack_home, current_version)
                    manifest_path = _installed_file(folder, "installed.json")
                    if manifest_path.is_file():
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        if manifest.get("version") == current_version:
                            if _installed_files_match(folder, manifest):
                                installed_bytes = sum(
                                    item["bytes"] for item in manifest["files"]
                                )
                            else:
                                damaged = current_version == spec["version"]
                        else:
                            current_version = None
            except (
                OSError,
                KeyError,
                TypeError,
                ValueError,
                AttributeError,
                json.JSONDecodeError,
            ):
                damaged = current_version == spec["version"]
                if not damaged:
                    current_version = None
            packs.append(
                {
                    "id": pack_id,
                    "title": spec["title"],
                    "version": spec["version"],
                    "installed": current_version == spec["version"]
                    and installed_bytes > 0
                    and not damaged,
                    "damaged": damaged,
                    "installed_version": current_version,
                    "download_bytes": spec["download_bytes"],
                    "license": spec.get("license", "See upstream model metadata"),
                    "runtimes": dict(spec.get("runtimes", {})),
                    "installed_bytes": installed_bytes,
                    "storage_bytes": self._directory_size(pack_home),
                }
            )
        return packs

    @staticmethod
    def _directory_size(folder: Path) -> int:
        if not folder.exists():
            return 0
        return sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())

    def active_model_roots(self, pack_ids: set[str] | None = None) -> list[Path]:
        roots = []
        selected_pack_ids = (
            self.specs
            if pack_ids is None
            else (pack_id for pack_id in self.specs if pack_id in pack_ids)
        )
        for pack_id in selected_pack_ids:
            try:
                _, home = _pack_home(self.store_root, pack_id)
            except ValueError:
                continue
            try:
                pointer = _installed_file(home, "current.json")
                version = _safe_component(
                    json.loads(pointer.read_text(encoding="utf-8"))["version"],
                    "version",
                )
                folder = _version_folder(home, version)
                manifest = json.loads(
                    _installed_file(folder, "installed.json").read_text(
                        encoding="utf-8"
                    )
                )
                if manifest.get("version") != version:
                    continue
                if _installed_files_match(folder, manifest):
                    roots.append(folder.resolve())
            except (
                OSError,
                KeyError,
                TypeError,
                ValueError,
                AttributeError,
                json.JSONDecodeError,
            ):
                continue
        return roots

    def install(self, pack_id: str, progress=None, cancel_event=None) -> Path:
        if pack_id not in self.specs:
            raise ValueError("Unknown language pack.")
        with _lock_for(pack_id):
            spec = self.specs[pack_id]
            _, home = _pack_home(self.store_root, pack_id)
            version = _safe_component(spec["version"], "version")
            home.mkdir(parents=True, exist_ok=True)
            version_dir = _version_folder(home, version)
            if version_dir.exists():
                self._verify_installed(version_dir, version)
                self._write_pointer(home, version)
                return version_dir

            staging = home / (".staging-" + uuid.uuid4().hex)
            staging.mkdir()
            total = spec["download_bytes"]
            transferred = 0
            verified_files = []
            try:
                for index, asset in enumerate(spec["assets"]):
                    self._check_cancel(cancel_event)
                    if asset["kind"] == "file":
                        parsed = urllib.parse.urlparse(asset["url"])
                        if parsed.scheme != "https" or parsed.hostname not in {
                            "huggingface.co",
                            "raw.githubusercontent.com",
                        }:
                            raise ValueError(
                                "Model pack manifest contains an untrusted download host."
                            )
                        destination = staging / _safe_relative(asset["destination"])
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        self._download(
                            asset,
                            destination,
                            transferred,
                            total,
                            progress,
                            cancel_event,
                        )
                        transferred += asset["bytes"]
                        size, checksum = _hash(destination)
                        if (
                            size != asset["bytes"]
                            or checksum.lower() != asset["sha256"].lower()
                        ):
                            raise ValueError(
                                f"Model file failed size/SHA-256 verification: {asset['destination']}"
                            )
                        verified_files.append(
                            {
                                "path": asset["destination"],
                                "bytes": size,
                                "sha256": checksum,
                                "license": asset.get("license"),
                                "repository": asset.get("repository"),
                                "revision": asset.get("revision"),
                                "runtimes": asset.get("runtimes", {}),
                            }
                        )
                    elif asset["kind"] == "generated-json":
                        destination = staging / _safe_relative(asset["destination"])
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        data = json.dumps(asset["content"], ensure_ascii=False).encode(
                            "utf-8"
                        )
                        if (
                            len(data) != asset["bytes"]
                            or hashlib.sha256(data).hexdigest() != asset["sha256"]
                        ):
                            raise ValueError(
                                f"Generated model config failed its pinned checksum: {asset['destination']}"
                            )
                        destination.write_bytes(data)
                        verified_files.append(
                            {
                                "path": asset["destination"],
                                "bytes": len(data),
                                "sha256": asset["sha256"],
                                "license": asset.get("license"),
                                "repository": asset.get("repository"),
                                "revision": asset.get("revision"),
                                "runtimes": asset.get("runtimes", {}),
                            }
                        )
                    elif asset["kind"] == "argos-archive":
                        parsed = urllib.parse.urlparse(asset["url"])
                        if parsed.scheme != "https" or parsed.hostname not in {
                            "huggingface.co",
                            "raw.githubusercontent.com",
                        }:
                            raise ValueError(
                                "Model pack manifest contains an untrusted download host."
                            )
                        archive = staging / (asset["pair"] + ".argosmodel")
                        self._download(
                            asset, archive, transferred, total, progress, cancel_event
                        )
                        transferred += asset["bytes"]
                        size, checksum = _hash(archive)
                        if (
                            size != asset["bytes"]
                            or checksum.lower() != asset["sha256"].lower()
                        ):
                            raise ValueError(
                                f"Argos archive failed size/SHA-256 verification: {asset['pair']}"
                            )
                        for installed_file in self._extract_argos(
                            archive, staging, asset["pair"]
                        ):
                            installed_file.update(
                                {
                                    key: asset[key]
                                    for key in (
                                        "license",
                                        "repository",
                                        "revision",
                                        "runtimes",
                                    )
                                }
                            )
                            verified_files.append(installed_file)
                        archive.unlink()
                    else:
                        raise ValueError("Unsupported model-pack asset type.")
                    if progress:
                        progress(
                            transferred,
                            total,
                            f"Verified {index + 1}/{len(spec['assets'])} assets",
                        )

                manifest = {
                    "pack_id": pack_id,
                    "version": spec["version"],
                    "title": spec["title"],
                    "license": spec.get("license", "See upstream model metadata"),
                    "model_repositories": list(spec.get("model_repositories", [])),
                    "runtimes": dict(spec.get("runtimes", {})),
                    "source_manifest_version": 2,
                    "files": verified_files,
                }
                (staging / "installed.json").write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                self._check_cancel(cancel_event)
                staging.replace(version_dir)
                self._write_pointer(home, version)
                if progress:
                    progress(total, total, "Installed and verified")
                return version_dir
            except BaseException:
                shutil.rmtree(staging, ignore_errors=True)
                raise

    @staticmethod
    def _check_cancel(cancel_event):
        if cancel_event is not None and cancel_event.is_set():
            raise InterruptedError("Language pack download cancelled.")

    @staticmethod
    def _download(asset, target, transferred, total, progress, cancel_event):
        request = urllib.request.Request(
            asset["url"], headers={"User-Agent": "Saylacian-Model-Packs/1.0"}
        )
        downloaded = 0
        temporary = target.with_suffix(target.suffix + ".part")
        try:
            with (
                urllib.request.urlopen(request, timeout=60) as response,
                temporary.open("wb") as output,
            ):
                while block := response.read(256 * 1024):
                    ModelPackManager._check_cancel(cancel_event)
                    output.write(block)
                    downloaded += len(block)
                    if downloaded > asset["bytes"]:
                        raise ValueError(
                            f"Download exceeds its pinned size: {target.name}"
                        )
                    if progress:
                        progress(
                            transferred + downloaded,
                            total,
                            f"Downloading {target.name}",
                        )
            if downloaded != asset["bytes"]:
                raise ValueError(f"Download has an unexpected size: {target.name}")
            temporary.replace(target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def _extract_argos(archive: Path, staging: Path, pair: str) -> list[dict]:
        extracted = []
        members = (
            f"{pair}/model/model.bin",
            f"{pair}/model/shared_vocabulary.txt",
            f"{pair}/sentencepiece.model",
        )
        with zipfile.ZipFile(archive) as package:
            names = set(package.namelist())
            missing = set(members) - names
            if missing:
                raise ValueError(
                    f"Pinned Argos archive lacks required files for {pair}."
                )
            for member in members:
                info = package.getinfo(member)
                if info.file_size > 500_000_000:
                    raise ValueError("Unexpectedly large model archive member.")
                target = staging / _safe_relative(member)
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                size, checksum = _hash(target)
                if size != info.file_size:
                    raise ValueError(f"Extracted model size check failed: {member}")
                extracted.append({"path": member, "bytes": size, "sha256": checksum})
        return extracted

    @staticmethod
    def _verify_installed(folder: Path, version: str):
        manifest_path = _installed_file(folder, "installed.json")
        if not manifest_path.is_file():
            raise ValueError(
                "Existing model pack version is incomplete; it was left untouched."
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("version") != version:
            raise ValueError("Existing model pack version does not match its manifest.")
        if not _installed_files_match(folder, manifest):
            raise ValueError(
                "Existing model pack failed integrity check; it was left untouched."
            )

    @staticmethod
    def _write_pointer(home: Path, version: str):
        version = _safe_component(version, "version")
        pointer = home / "current.json"
        temporary = home / (".current-" + uuid.uuid4().hex + ".tmp")
        try:
            with temporary.open("x", encoding="utf-8") as output:
                output.write(json.dumps({"version": version}))
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(pointer)
        finally:
            temporary.unlink(missing_ok=True)

    def remove(self, pack_id: str) -> None:
        if pack_id not in self.specs:
            raise ValueError("Unknown language pack.")
        with _lock_for(pack_id):
            _, home = _pack_home(self.store_root, pack_id)
            if home.exists():
                shutil.rmtree(home)
