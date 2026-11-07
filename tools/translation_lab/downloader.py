# SPDX-License-Identifier: AGPL-3.0-or-later
"""Pinned HTTPS downloads with license gates, redirect checks and SHA-256."""

from __future__ import annotations

import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

from .sources import verify_approved_source

_SHA256 = re.compile(r"[a-fA-F0-9]{64}\Z")


def _validate_url(url: str, allowed_hosts: set[str]) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError(
            "Only credential-free HTTPS URLs on the default port are accepted."
        )
    if host not in {
        item.rstrip(".").encode("idna").decode("ascii").lower()
        for item in allowed_hosts
    }:
        raise ValueError("Download host is not on the exact allowlist.")
    if parsed.fragment:
        raise ValueError("Download URLs cannot contain fragments.")
    return host


class AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, request, response, code, message, headers, newurl):
        _validate_url(newurl, self.allowed_hosts)
        return super().redirect_request(
            request, response, code, message, headers, newurl
        )


@dataclass(frozen=True)
class DownloadSpec:
    source: dict
    url: str
    sha256: str
    expected_bytes: int
    purpose: str = "train"


def download_approved(
    spec: DownloadSpec,
    cache: Path,
    allowed_hosts: set[str],
    approved_source_ids: set[str],
    max_bytes: int,
    *,
    timeout: int = 45,
    retries: int = 3,
    allow_noncommercial: bool = False,
    opener=None,
) -> Path:
    verify_approved_source(
        spec.source,
        approved_source_ids,
        purpose=spec.purpose,
        allow_noncommercial=allow_noncommercial,
    )
    _validate_url(spec.url, allowed_hosts)
    if not _SHA256.fullmatch(spec.sha256):
        raise ValueError("A valid pinned SHA-256 is required.")
    if type(spec.expected_bytes) is not int or not 0 < spec.expected_bytes <= max_bytes:
        raise ValueError("Artifact size is missing or exceeds the configured limit.")
    if not 1 <= timeout <= 300 or not 0 <= retries <= 10:
        raise ValueError("Timeout or retry count is outside the safe configured range.")

    digest = spec.sha256.lower()
    directory = cache / digest
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "artifact"
    if destination.is_file() and _matches(destination, digest, spec.expected_bytes):
        return destination

    part = directory / "artifact.part"
    metadata_path = directory / "artifact.part.json"
    metadata = _read_metadata(metadata_path)
    if (
        not metadata
        or metadata.get("url") != spec.url
        or metadata.get("sha256") != digest
    ):
        suffix = uuid.uuid4().hex[:8]
        part = directory / f"artifact-{suffix}.part"
        metadata_path = directory / f"artifact-{suffix}.part.json"
        metadata = {}

    transport = (
        opener
        or urllib.request.build_opener(AllowlistedRedirectHandler(allowed_hosts)).open
    )
    last_error = None
    for attempt in range(retries + 1):
        offset = part.stat().st_size if part.exists() else 0
        etag = metadata.get("etag")
        resume = offset > 0 and bool(etag)
        headers = {"User-Agent": "Saylacian-Research-Lab/0.1"}
        if resume:
            headers.update({"Range": f"bytes={offset}-", "If-Range": etag})
        request = urllib.request.Request(spec.url, headers=headers)
        try:
            with transport(request, timeout=timeout) as response:
                final_url = response.geturl()
                _validate_url(final_url, allowed_hosts)
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                response_etag = response.headers.get("ETag")
                if resume and status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    if (
                        not content_range.startswith(f"bytes {offset}-")
                        or response_etag != etag
                    ):
                        raise ValueError(
                            "Server returned a mismatched partial response."
                        )
                    mode = "ab"
                else:
                    if status == 206:
                        raise ValueError(
                            "Server returned a partial response without "
                            "a verified resume."
                        )
                    offset = 0
                    mode = "wb"
                if status not in {200, 206}:
                    raise ValueError(f"Unexpected HTTP status {status}.")
                content_length = response.headers.get("Content-Length")
                if (
                    content_length
                    and int(content_length) + offset > spec.expected_bytes
                ):
                    raise ValueError(
                        "Server response exceeds the pinned artifact size."
                    )
                metadata = {"url": spec.url, "sha256": digest, "etag": response_etag}
                _write_metadata(metadata_path, metadata)
                received = offset
                with part.open(mode) as output:
                    while chunk := response.read(1024 * 1024):
                        received += len(chunk)
                        if received > spec.expected_bytes or received > max_bytes:
                            raise ValueError("Downloaded data exceeded its size limit.")
                        output.write(chunk)
                    output.flush()
                    import os

                    os.fsync(output.fileno())
            if part.stat().st_size != spec.expected_bytes:
                raise ValueError(
                    "Downloaded byte count does not match the pinned size."
                )
            if not _matches(part, digest, spec.expected_bytes):
                raise ValueError("Downloaded artifact SHA-256 does not match the pin.")
            part.replace(destination)
            metadata_path.unlink(missing_ok=True)
            return destination
        except ValueError as error:
            if "allowlist" in str(error):
                raise
            last_error = error
            if any(
                marker in str(error)
                for marker in (
                    "byte count",
                    "SHA-256",
                    "partial response",
                    "exceeds its size limit",
                )
            ):
                suffix = uuid.uuid4().hex[:8]
                part = directory / f"artifact-{suffix}.part"
                metadata_path = directory / f"artifact-{suffix}.part.json"
                metadata = {}
            if attempt < retries:
                time.sleep(min(4.0, 0.25 * 2**attempt) * random.uniform(0.8, 1.2))
        except (OSError, urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(min(4.0, 0.25 * 2**attempt) * random.uniform(0.8, 1.2))
    raise RuntimeError(
        f"Pinned download failed after {retries + 1} attempts: {last_error}"
    ) from last_error


def _matches(path: Path, digest: str, expected_bytes: int) -> bool:
    if not path.is_file() or path.stat().st_size != expected_bytes:
        return False
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest() == digest


def _read_metadata(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_metadata(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    temporary.replace(path)
