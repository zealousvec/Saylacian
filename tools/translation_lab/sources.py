# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small, rights-aware source register; candidates are not download approvals."""

from __future__ import annotations

import json
from pathlib import Path


def load_catalog(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise TypeError("Source catalog must be a JSON array.")
    identifiers = set()
    for source in data:
        identifier = source.get("source_id")
        if not identifier or identifier in identifiers:
            raise ValueError("Source IDs must be present and unique.")
        identifiers.add(identifier)
        rights = source.get("rights", {})
        if any(
            value not in {"allowed", "prohibited", "unclear", "approval_required"}
            for value in rights.values()
        ):
            raise ValueError(f"Invalid rights value in source {identifier}.")
    return data


def read_owner_registry(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    identifiers = set()
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid source registry JSON on line {line_number}."
            ) from error
        if not isinstance(record, dict) or not record.get("source_id"):
            raise ValueError(f"Source registry line {line_number} has no source ID.")
        if record["source_id"] in identifiers:
            raise ValueError(f"Duplicate source ID on line {line_number}.")
        identifiers.add(record["source_id"])
        if not isinstance(record.get("artifacts", []), list):
            raise TypeError(f"Artifacts must be a list on line {line_number}.")
        records.append(record)
    return records


def verify_approved_source(
    source: dict,
    configured_approvals: set[str],
    *,
    purpose: str = "train",
    allow_noncommercial: bool = False,
) -> None:
    if (
        source.get("source_id") not in configured_approvals
        or source.get("owner_approved") is not True
    ):
        raise PermissionError("Source does not have explicit owner approval.")
    if source.get("gated"):
        raise PermissionError("Gated sources require the owner to handle access terms.")
    rights = source.get("rights", {})
    if rights.get("download") != "allowed":
        raise PermissionError("Download rights are not explicitly allowed.")
    if source.get("rights_status") != "verified":
        raise PermissionError("Source rights are not verified.")
    if purpose not in {"train", "evaluate"}:
        raise ValueError("Purpose must be train or evaluate.")
    if rights.get(purpose) != "allowed":
        raise PermissionError(f"Source does not explicitly allow {purpose} use.")
    if purpose == "train" and source.get("split_role") == "evaluation_only":
        raise PermissionError(
            "Evaluation-only sources cannot be used for training ingestion."
        )
    license_id = str(source.get("license", "")).lower()
    if purpose == "train" and "nc" in license_id and not allow_noncommercial:
        raise PermissionError(
            "Noncommercial training data is disabled by configuration."
        )
