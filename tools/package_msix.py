# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build and structurally verify an unsigned MSIX from the existing Saylacian bundle.

This does not sign or install the package. The identity placeholders are not
Store-ready; use the exact reserved identity and publisher from Partner Center.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "tools" / "msix" / "AppxManifest.xml"
NS = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
ET.register_namespace("", NS)
ET.register_namespace("uap", "http://schemas.microsoft.com/appx/manifest/uap/windows10")
ET.register_namespace(
    "rescap",
    "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_candidate(candidate: Path, manifest_path: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("runtime_verified") is not False:
        raise ValueError(
            "Candidate manifest must explicitly show runtime_verified=false."
        )
    count = 0
    for entry in manifest["files"]:
        path = candidate / Path(entry["path"])
        if not path.is_file() or path.stat().st_size != entry["bytes"]:
            raise ValueError(
                f"Candidate file missing or size mismatch: {entry['path']}"
            )
        if sha256(path).lower() != entry["sha256"].lower():
            raise ValueError(f"Candidate SHA-256 mismatch: {entry['path']}")
        count += 1
    extra = {
        p.relative_to(candidate).as_posix()
        for p in candidate.rglob("*")
        if p.is_file() and p.name != "SHA256SUMS.txt"
    }
    listed = {entry["path"].replace("\\", "/") for entry in manifest["files"]}
    if extra != listed:
        raise ValueError(
            f"Candidate file set differs from manifest: {len(extra ^ listed)} entries"
        )
    checksum_file = candidate / "SHA256SUMS.txt"
    if checksum_file.is_file():
        expected_sums = {
            f"{item['sha256'].lower()}  {item['path'].replace(chr(92), '/')}"
            for item in manifest["files"]
        }
        actual_sums = set(checksum_file.read_text(encoding="utf-8").splitlines())
        if actual_sums != expected_sums:
            raise ValueError("Candidate SHA256SUMS.txt differs from the JSON manifest")
    return count


def create_assets(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    font_path = Path(r"C:\Windows\Fonts\segoeuib.ttf")
    if not font_path.is_file():
        font_path = Path(r"C:\Windows\Fonts\arialbd.ttf")
    for size in (44, 50, 150):
        image = Image.new("RGBA", (size, size), (17, 17, 17, 255))
        draw = ImageDraw.Draw(image)
        inset = max(2, round(size * 0.09))
        draw.rounded_rectangle(
            (inset, inset, size - inset - 1, size - inset - 1),
            radius=max(2, round(size * 0.13)),
            outline=(238, 238, 238, 255),
            width=max(1, round(size * 0.025)),
        )
        font = (
            ImageFont.truetype(str(font_path), max(12, round(size * 0.62)))
            if font_path.is_file()
            else ImageFont.load_default()
        )
        box = draw.textbbox((0, 0), "S", font=font)
        xy = (
            (size - (box[2] - box[0])) / 2 - box[0],
            (size - (box[3] - box[1])) / 2 - box[1],
        )
        draw.text(xy, "S", font=font, fill=(255, 255, 255, 255))
        image.save(
            folder
            / {
                44: "Square44x44Logo.png",
                50: "StoreLogo.png",
                150: "Square150x150Logo.png",
            }[size]
        )


def write_package_checksums(layout: Path) -> int:
    checksum_path = layout / "SHA256SUMS.txt"
    entries = []
    for path in sorted(
        p for p in layout.rglob("*") if p.is_file() and p != checksum_path
    ):
        entries.append(f"{sha256(path)}  {path.relative_to(layout).as_posix()}")
    checksum_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return len(entries)


def verify_package_checksums(root: Path) -> int:
    checksum_path = root / "SHA256SUMS.txt"
    rows = [
        line.split("  ", 1)
        for line in checksum_path.read_text(encoding="utf-8").splitlines()
    ]
    if any(len(row) != 2 for row in rows):
        raise ValueError("Malformed package SHA256SUMS.txt")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "AppxBlockMap.xml"}
    }
    listed = {name for _, name in rows}
    if len(rows) != len(listed) or actual != listed:
        raise ValueError(
            "Package SHA256SUMS.txt does not cover the unpacked file set exactly"
        )
    for digest, name in rows:
        if sha256(root / name).lower() != digest.lower():
            raise ValueError(f"Package SHA-256 index mismatch: {name}")
    return len(rows)


def run(command: list[str]) -> None:
    print("+", subprocess.list2cmdline(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        print((result.stdout + "\n" + result.stderr)[-12000:], file=sys.stderr)
        result.check_returncode()
    summary = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if "succeeded" in line.lower() or "successfully" in line.lower()
    ]
    print("; ".join(summary[-3:]) or "completed", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate", type=Path, required=True, help="Existing clean onedir candidate"
    )
    parser.add_argument(
        "--manifest", type=Path, required=True, help="Candidate JSON manifest"
    )
    parser.add_argument(
        "--makeappx",
        type=Path,
        required=True,
        help="Microsoft Windows SDK MakeAppx.exe",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="New output .msix path"
    )
    parser.add_argument("--identity-name", default="Saylacian.IdentityPending")
    parser.add_argument("--publisher", default="CN=Saylacian-Publisher-PENDING")
    parser.add_argument("--version", default="1.0.0.0")
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="verify an existing output without replacing the MSIX; refresh its manifest only after all checks pass",
    )
    args = parser.parse_args()

    candidate, manifest_path = args.candidate.resolve(), args.manifest.resolve()
    makeappx, output = args.makeappx.resolve(), args.output.resolve()
    if not makeappx.is_file() or not candidate.is_dir() or not manifest_path.is_file():
        parser.error("candidate, manifest, and MakeAppx paths must exist")
    result_manifest = output.with_suffix(output.suffix + ".manifest.json")
    if result_manifest.exists() and not args.verify_existing:
        parser.error(
            f"output manifest already exists; choose a new path: {result_manifest}"
        )
    if output.exists() and not args.verify_existing:
        parser.error(
            f"output already exists; use --verify-existing or choose a new path: {output}"
        )
    if args.verify_existing and not output.is_file():
        parser.error("--verify-existing requires an existing output file")
    count = verify_candidate(candidate, manifest_path)
    print(
        f"Verified clean candidate: {count} files; source manifest marks runtime unverified.",
        flush=True,
    )

    with tempfile.TemporaryDirectory(prefix="saylacian-msix-") as temp:
        work = Path(temp)
        layout = work / "layout"
        shutil.copytree(candidate, layout)
        shutil.copytree(
            ROOT / "notices", layout / "_internal" / "notices", dirs_exist_ok=True
        )
        create_assets(layout / "Assets")
        tree = ET.parse(TEMPLATE)
        identity = tree.getroot().find(f"{{{NS}}}Identity")
        identity.set("Name", args.identity_name)
        identity.set("Publisher", args.publisher)
        identity.set("Version", args.version)
        tree.write(layout / "AppxManifest.xml", encoding="utf-8", xml_declaration=True)
        package_checksum_count = write_package_checksums(layout)

        output.parent.mkdir(parents=True, exist_ok=True)
        packed = output if args.verify_existing else work / "Saylacian-unsigned.msix"
        if not args.verify_existing:
            run([str(makeappx), "pack", "/d", str(layout), "/p", str(packed), "/o"])
        unpacked = work / "unpacked"
        run([str(makeappx), "unpack", "/p", str(packed), "/d", str(unpacked)])
        if not (unpacked / "AppxManifest.xml").is_file():
            raise RuntimeError("MSIX unpack check did not recover the package manifest")
        packaged = {
            p.relative_to(unpacked).as_posix()
            for p in unpacked.rglob("*")
            if p.is_file() and p.name != "AppxBlockMap.xml"
        }
        expected = {
            p.relative_to(layout).as_posix() for p in layout.rglob("*") if p.is_file()
        }
        if packaged != expected:
            raise RuntimeError(
                f"Unpacked package file-set mismatch: {len(packaged ^ expected)} entries"
            )
        for relative in expected:
            if sha256(layout / relative) != sha256(unpacked / relative):
                raise RuntimeError(f"Unpacked package content mismatch: {relative}")
        package_checksum_count = verify_package_checksums(unpacked)
        output.parent.mkdir(parents=True, exist_ok=True)
        if not args.verify_existing:
            shutil.copy2(packed, output)
        result = {
            "output": str(output),
            "bytes": output.stat().st_size,
            "sha256": sha256(output),
            "candidate_file_count": count,
            "package_payload_file_count": len(expected),
            "package_checksum_entries": package_checksum_count,
            "candidate_manifest_sha256": sha256(manifest_path),
            "makeappx_sha256": sha256(makeappx),
            "release_notice_file_count": sum(
                1 for p in (ROOT / "notices").rglob("*") if p.is_file()
            ),
            "release_notice_files": {
                p.relative_to(ROOT / "notices").as_posix(): sha256(p)
                for p in sorted((ROOT / "notices").rglob("*"))
                if p.is_file()
            },
            "identity_name": args.identity_name,
            "publisher": args.publisher,
            "identity_pending": "PENDING"
            in (args.identity_name + args.publisher).upper(),
            "signature": "unsigned; Store identity placeholder unless explicitly overridden",
            "runtime_verified": False,
        }
        result_manifest.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        KeyError,
        ET.ParseError,
        subprocess.CalledProcessError,
        RuntimeError,
    ) as exc:
        print(f"MSIX build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
