#!/usr/bin/env python3
"""Create and verify a Windows Store MSIX from Saylacian's onedir build."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_RE = re.compile(r"[A-Za-z0-9.]{3,50}\Z")
VERSION_RE = re.compile(r"(?:0|[1-9][0-9]{0,4})(?:\.(?:0|[1-9][0-9]{0,4})){3}\Z")
FORBIDDEN_WEIGHT_SUFFIXES = {".gguf", ".safetensors", ".onnx_data"}
FORBIDDEN_MODEL_NAMES = {
    "model.bin",
    "pytorch_model.bin",
    "model.safetensors",
    "model_quantized.onnx",
}
TEXT_SUFFIXES = {".cfg", ".ini", ".json", ".kv", ".md", ".py", ".txt", ".xml"}


def manifest_xml(
    identity: str,
    publisher: str,
    publisher_display_name: str,
    version: str,
) -> str:
    """Create the minimal full-trust desktop manifest used for the Store package."""
    if not IDENTITY_RE.fullmatch(identity):
        raise ValueError("Package identity must be 3–50 letters, digits, or periods.")
    if not publisher.startswith("CN=") or not publisher.strip():
        raise ValueError(
            "Publisher must exactly match the Partner Center publisher DN."
        )
    if len(publisher) > 255 or len(publisher_display_name) > 50:
        raise ValueError("Publisher values exceed Windows package manifest limits.")
    if not VERSION_RE.fullmatch(version):
        raise ValueError("Version must have four numeric components, such as 0.1.0.0.")

    identity_xml = escape(identity, {'"': "&quot;"})
    publisher_xml = escape(publisher, {'"': "&quot;"})
    publisher_display_xml = escape(publisher_display_name)
    version_xml = escape(version, {'"': "&quot;"})
    return rf'''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         IgnorableNamespaces="uap rescap">
  <Identity Name="{identity_xml}" Publisher="{publisher_xml}" Version="{version_xml}" ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>Saylacian</DisplayName>
    <PublisherDisplayName>{publisher_display_xml}</PublisherDisplayName>
    <Description>Somali translation, writing-system conversion, and offline English–French translation.</Description>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19041.0" MaxVersionTested="10.0.28000.0" />
  </Dependencies>
  <Resources>
    <Resource Language="en-us" />
  </Resources>
  <Applications>
    <Application Id="Saylacian" Executable="Saylacian.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="Saylacian" Description="Somali translation and script conversion"
                          Square150x150Logo="Assets\Square150x150Logo.png"
                          Square44x44Logo="Assets\Square44x44Logo.png"
                          BackgroundColor="black" />
    </Application>
  </Applications>
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
</Package>
'''


def _create_store_assets(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    font_candidates = (
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
    )
    font_path = next((path for path in font_candidates if path.is_file()), None)
    for size, filename, inset in (
        (50, "StoreLogo.png", 11),
        (44, "Square44x44Logo.png", 10),
        (150, "Square150x150Logo.png", 32),
    ):
        image = Image.new("RGB", (size, size), "#000000")
        draw = ImageDraw.Draw(image)
        font = (
            ImageFont.truetype(str(font_path), size - inset * 2)
            if font_path
            else ImageFont.load_default()
        )
        box = draw.textbbox((0, 0), "S", font=font)
        x = (size - (box[2] - box[0])) / 2 - box[0]
        y = (size - (box[3] - box[1])) / 2 - box[1]
        draw.text((x, y), "S", fill="#FFFFFF", font=font)
        image.save(destination / filename, format="PNG", optimize=True)


def _private_path_markers() -> tuple[bytes, ...]:
    candidates = {str(Path.home()), str(ROOT)}
    markers = set()
    for value in candidates:
        if value:
            markers.add(value.encode("utf-8").lower())
            markers.add(value.replace("\\", "/").encode("utf-8").lower())
    return tuple(markers)


def inspect_payload(dist_dir: Path) -> list[str]:
    errors: list[str] = []
    executable = dist_dir / "Saylacian.exe"
    required = (
        executable,
        dist_dir / "_internal" / "app" / "main.kv",
        dist_dir / "_internal" / "assets" / "NotoSansOsmanya.ttf",
        dist_dir / "_internal" / "saylacian" / "core" / "data" / "model_manifest.json",
        dist_dir / "_internal" / "LICENSE",
        dist_dir / "_internal" / "THIRD_PARTY_NOTICES.md",
    )
    for path in required:
        if not path.is_file():
            errors.append(
                f"Required packaged file is missing: {path.relative_to(dist_dir)}"
            )
    if errors:
        return errors

    private_markers = _private_path_markers()
    for path in dist_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if (
            path.suffix.lower() in FORBIDDEN_WEIGHT_SUFFIXES
            or name in FORBIDDEN_MODEL_NAMES
        ):
            errors.append(
                f"Model weights are not allowed in the installer: {path.relative_to(dist_dir)}"
            )
        if path.suffix.lower() == ".onnx" and path.stat().st_size > 1_000_000:
            errors.append(
                f"Downloaded model data is not allowed in the installer: {path.relative_to(dist_dir)}"
            )
        if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 2_000_000:
            lowered = path.read_bytes().lower()
            if any(marker in lowered for marker in private_markers):
                errors.append(
                    f"A local user path appears in: {path.relative_to(dist_dir)}"
                )
    return errors


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_msix(args: argparse.Namespace) -> dict[str, object]:
    dist_dir = args.dist_dir.resolve()
    makeappx = args.makeappx.resolve()
    output = args.output.resolve()
    errors = inspect_payload(dist_dir)
    if errors:
        raise ValueError("Packaged app failed checks:\n- " + "\n- ".join(errors))
    if not makeappx.is_file() or makeappx.name.lower() != "makeappx.exe":
        raise ValueError("Pass the Windows SDK's MakeAppx.exe using --makeappx.")

    manifest = manifest_xml(
        args.identity, args.publisher, args.publisher_display_name, args.version
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="saylacian-msix-stage-") as temporary:
        stage = Path(temporary)
        shutil.copytree(dist_dir, stage, dirs_exist_ok=True)
        assets = stage / "Assets"
        _create_store_assets(assets)
        (stage / "AppxManifest.xml").write_text(manifest, encoding="utf-8")
        errors = inspect_payload(stage)
        if errors:
            raise ValueError("Staged package failed checks:\n- " + "\n- ".join(errors))
        command = [str(makeappx), "pack", "/d", str(stage), "/p", str(output)]
        result = subprocess.run(
            command, check=False, cwd=ROOT, capture_output=True, text=True
        )
        if result.returncode:
            log = result.stdout + result.stderr
            raise subprocess.CalledProcessError(
                result.returncode, command, output=log[-4000:]
            )

    verify_msix(output, args.identity, args.publisher, args.version)

    summary = {
        "format": "MSIX",
        "version": args.version,
        "architecture": "x64",
        "bytes": output.stat().st_size,
        "sha256": _sha256(output),
        "signed": False,
        "store_identity": args.identity,
        "model_weights_included": False,
    }
    summary_path = output.with_suffix(output.suffix + ".sha256.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def verify_msix(
    package_path: Path, identity: str, publisher: str, version: str
) -> None:
    """Check the package archive and its identity after MakeAppx creates it."""
    if not package_path.is_file():
        raise ValueError("MakeAppx did not create the requested package.")
    with zipfile.ZipFile(package_path) as package:
        names = set(package.namelist())
        required = {
            "AppxManifest.xml",
            "Assets/StoreLogo.png",
            "Assets/Square44x44Logo.png",
            "Assets/Square150x150Logo.png",
            "Saylacian.exe",
            "_internal/LICENSE",
            "_internal/THIRD_PARTY_NOTICES.md",
        }
        missing = sorted(required - names)
        if missing:
            raise ValueError("MSIX is missing required files: " + ", ".join(missing))
        if any(
            Path(name).suffix.lower() in FORBIDDEN_WEIGHT_SUFFIXES for name in names
        ):
            raise ValueError("MSIX contains a forbidden model-weight file.")
        root = ElementTree.fromstring(package.read("AppxManifest.xml"))
        namespace = {
            "appx": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
        }
        package_identity = root.find("appx:Identity", namespace)
        expected = (identity, publisher, version)
        actual = (
            (
                package_identity.get("Name"),
                package_identity.get("Publisher"),
                package_identity.get("Version"),
            )
            if package_identity is not None
            else None
        )
        if actual != expected:
            raise ValueError(
                f"MSIX identity mismatch: expected {expected!r}, got {actual!r}."
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify", help="Check the onedir payload.")
    verify.add_argument("--dist-dir", type=Path, required=True)
    package = subparsers.add_parser("package", help="Create an unsigned Store MSIX.")
    package.add_argument("--dist-dir", type=Path, required=True)
    package.add_argument("--makeappx", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--identity", required=True)
    package.add_argument("--publisher", required=True)
    package.add_argument("--publisher-display-name", required=True)
    package.add_argument("--version", default="0.1.0.0")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            errors = inspect_payload(args.dist_dir.resolve())
            if errors:
                raise ValueError("\n- " + "\n- ".join(errors))
            print(
                "Packaged app payload passed. No downloadable model weights or local paths found."
            )
            return 0
        result = package_msix(args)
        print(json.dumps(result, indent=2))
        print(
            "The unsigned MSIX is for Store submission only; it is not ready for local installation."
        )
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.output:
            print(error.output, file=sys.stderr)
        print(f"Windows package error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
