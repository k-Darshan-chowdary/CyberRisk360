"""CSV-backed asset inventory operations for CyberRisk360."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable, Mapping

from risk_register import load_risks


FIELDNAMES = [
    "asset_id",
    "asset_name",
    "asset_type",
    "asset_owner",
    "department",
    "data_classification",
    "business_criticality",
    "location",
    "description",
]

TEXT_FIELDS = {
    "asset_name",
    "asset_type",
    "asset_owner",
    "department",
    "location",
    "description",
}
DATA_CLASSIFICATIONS = {"Public", "Internal", "Confidential", "Restricted"}
BUSINESS_CRITICALITIES = {"Low", "Medium", "High", "Critical"}
_ASSET_ID_PATTERN = re.compile(r"AST-\d{3}", re.IGNORECASE)


def _require_text(value: object, field: str) -> str:
    """Return trimmed non-empty text for a required field."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} cannot be empty.")
    return normalized


def _validate_choice(value: object, field: str, choices: set[str]) -> str:
    """Return a trimmed value when it belongs to an allowed vocabulary."""
    normalized = _require_text(value, field)
    if normalized not in choices:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(choices))}.")
    return normalized


def _validate_asset_id(value: object) -> str:
    """Validate and normalize an asset identifier."""
    normalized = _require_text(value, "asset_id").upper()
    if _ASSET_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError("asset_id must use AST- followed by exactly three digits.")
    return normalized


def _validate_asset(data: Mapping[str, object]) -> dict[str, str]:
    """Validate a complete asset and return a normalized independent record."""
    missing = [field for field in FIELDNAMES if field not in data]
    if missing:
        raise ValueError(f"Missing required asset fields: {', '.join(missing)}.")

    normalized = {"asset_id": _validate_asset_id(data["asset_id"])}
    for field in TEXT_FIELDS:
        normalized[field] = _require_text(data[field], field)
    normalized["data_classification"] = _validate_choice(
        data["data_classification"], "data_classification", DATA_CLASSIFICATIONS
    )
    normalized["business_criticality"] = _validate_choice(
        data["business_criticality"], "business_criticality", BUSINESS_CRITICALITIES
    )
    return {field: normalized[field] for field in FIELDNAMES}


def _prepare_assets(assets: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    """Validate asset records before any output file is opened."""
    prepared: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, asset in enumerate(assets, start=1):
        if not isinstance(asset, Mapping):
            raise TypeError(f"Asset record {index} must be a dictionary-like mapping.")
        normalized = _validate_asset(asset)
        folded_id = normalized["asset_id"].casefold()
        if folded_id in seen_ids:
            raise ValueError(f"Duplicate asset ID {normalized['asset_id']}.")
        seen_ids.add(folded_id)
        prepared.append(normalized)
    return prepared


def load_assets(assets_path: str | Path) -> list[dict[str, str]]:
    """Load and validate asset records from a CSV file in their original order."""
    path = Path(assets_path)
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        present_fields = set(reader.fieldnames or [])
        missing = [field for field in FIELDNAMES if field not in present_fields]
        if missing:
            raise ValueError(f"Asset CSV is missing required columns: {', '.join(missing)}.")

        assets: list[dict[str, str]] = []
        seen_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(row.get(field) is None for field in FIELDNAMES):
                    raise ValueError("row has the wrong number of columns")
                asset = _validate_asset(row)
                folded_id = asset["asset_id"].casefold()
                if folded_id in seen_ids:
                    raise ValueError(f"duplicate asset ID {asset['asset_id']}")
                seen_ids.add(folded_id)
                assets.append(asset)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid asset data on CSV row {row_number}: {exc}") from exc
    return assets


def save_assets(
    assets_path: str | Path, assets: Iterable[Mapping[str, object]]
) -> None:
    """Write validated assets in the exact inventory column order."""
    prepared = _prepare_assets(assets)
    path = Path(assets_path)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(prepared)


def get_asset_by_id(
    assets: Iterable[Mapping[str, str]], asset_id: str
) -> dict[str, str] | None:
    """Return a copy of one case-insensitive asset ID match, or None."""
    if not isinstance(asset_id, str):
        raise TypeError("asset_id must be text.")
    wanted = asset_id.casefold()
    for asset in assets:
        if str(asset.get("asset_id", "")).casefold() == wanted:
            return dict(asset)
    return None


def search_assets(
    assets: Iterable[Mapping[str, str]], query: str
) -> list[dict[str, str]]:
    """Search common asset text fields while preserving inventory order."""
    if not isinstance(query, str):
        raise TypeError("query must be text.")
    search_fields = (
        "asset_id",
        "asset_name",
        "asset_type",
        "asset_owner",
        "department",
        "location",
        "description",
    )
    needle = query.strip().casefold()
    return [
        dict(asset)
        for asset in assets
        if not needle
        or any(needle in str(asset.get(field, "")).casefold() for field in search_fields)
    ]


def filter_assets(
    assets: Iterable[Mapping[str, str]],
    asset_type: str | None = None,
    department: str | None = None,
    data_classification: str | None = None,
    business_criticality: str | None = None,
    location: str | None = None,
) -> list[dict[str, str]]:
    """Return copies of assets matching every supplied case-insensitive filter."""
    criteria = {
        "asset_type": asset_type,
        "department": department,
        "data_classification": data_classification,
        "business_criticality": business_criticality,
        "location": location,
    }
    for field, value in criteria.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{field} filter must be text or None.")
    return [
        dict(asset)
        for asset in assets
        if all(
            value is None
            or str(asset.get(field, "")).casefold() == value.casefold()
            for field, value in criteria.items()
        )
    ]


def add_asset(assets_path: str | Path, asset_data: dict[str, object]) -> dict[str, str]:
    """Validate and append one new asset, returning an independent copy."""
    if not isinstance(asset_data, dict):
        raise TypeError("asset_data must be a dictionary.")
    created = _validate_asset(dict(asset_data))
    assets = load_assets(assets_path)
    if get_asset_by_id(assets, created["asset_id"]) is not None:
        raise ValueError(f"Asset ID {created['asset_id']} already exists.")
    save_assets(assets_path, [*assets, created])
    return dict(created)


def update_asset(
    assets_path: str | Path, asset_id: str, updates: dict[str, object]
) -> dict[str, str]:
    """Validate and update an asset without moving it in the inventory."""
    if not isinstance(asset_id, str):
        raise TypeError("asset_id must be text.")
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dictionary.")
    if "asset_id" in updates:
        raise ValueError("The asset_id of an existing asset cannot be changed.")
    unknown = set(updates) - set(FIELDNAMES)
    if unknown:
        raise ValueError(f"Unknown asset fields: {', '.join(sorted(unknown))}.")

    assets = load_assets(assets_path)
    match_index = next(
        (index for index, asset in enumerate(assets) if asset["asset_id"].casefold() == asset_id.casefold()),
        None,
    )
    if match_index is None:
        raise ValueError(f"Asset ID {asset_id!r} does not exist.")
    updated = _validate_asset({**assets[match_index], **dict(updates)})
    assets[match_index] = updated
    save_assets(assets_path, assets)
    return dict(updated)


def delete_asset(
    assets_path: str | Path, risks_path: str | Path, asset_id: str
) -> dict[str, str]:
    """Delete an unreferenced asset and return a copy of the removed record."""
    if not isinstance(asset_id, str):
        raise TypeError("asset_id must be text.")
    assets = load_assets(assets_path)
    match_index = next(
        (index for index, asset in enumerate(assets) if asset["asset_id"].casefold() == asset_id.casefold()),
        None,
    )
    if match_index is None:
        raise ValueError(f"Asset ID {asset_id!r} does not exist.")

    matched_id = assets[match_index]["asset_id"]
    risk_ids = [
        str(risk["risk_id"])
        for risk in load_risks(risks_path)
        if str(risk["affected_asset_id"]).casefold() == matched_id.casefold()
    ]
    if risk_ids:
        raise ValueError(
            f"Asset ID {matched_id} is referenced by risks: {', '.join(risk_ids)}."
        )
    deleted = assets.pop(match_index)
    save_assets(assets_path, assets)
    return dict(deleted)
