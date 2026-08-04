"""CSV-backed security-control register operations for CyberRisk360."""

from __future__ import annotations

import csv
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from asset_register import load_assets
from risk_register import load_risks


FIELDNAMES = [
    "control_id",
    "control_name",
    "control_description",
    "control_type",
    "nist_csf_function",
    "implementation_status",
    "control_owner",
    "effectiveness_pct",
    "mapped_asset_ids",
    "mapped_risk_ids",
    "review_date",
    "evidence_reference",
    "notes",
]

TEXT_FIELDS = {"control_name", "control_description", "control_owner"}
CONTROL_TYPES = {"Preventive", "Detective", "Corrective", "Recovery", "Governance"}
NIST_CSF_FUNCTIONS = {"Govern", "Identify", "Protect", "Detect", "Respond", "Recover"}
IMPLEMENTATION_STATUSES = {
    "Implemented",
    "Partially Implemented",
    "Planned",
    "Not Implemented",
    "Not Applicable",
}
_CONTROL_ID_PATTERN = re.compile(r"CTL-\d{3}", re.IGNORECASE)
_ASSET_ID_PATTERN = re.compile(r"AST-\d{3}", re.IGNORECASE)
_RISK_ID_PATTERN = re.compile(r"RSK-\d{3}", re.IGNORECASE)


def _require_text(value: object, field: str) -> str:
    """Return trimmed non-empty text for a required field."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} cannot be empty.")
    return normalized


def _validate_choice(value: object, field: str, choices: set[str]) -> str:
    """Validate a required text value against an allowed vocabulary."""
    normalized = _require_text(value, field)
    if normalized not in choices:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(choices))}.")
    return normalized


def _validate_control_id(value: object) -> str:
    """Validate and normalize a security-control identifier."""
    normalized = _require_text(value, "control_id").upper()
    if _CONTROL_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError("control_id must use CTL- followed by exactly three digits.")
    return normalized


def _validate_effectiveness(value: object) -> float:
    """Validate a non-boolean percentage from zero through one hundred."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("effectiveness_pct must be a number from 0 through 100.")
    result = float(value)
    if not 0 <= result <= 100:
        raise ValueError("effectiveness_pct must be between 0 and 100.")
    return result


def _validate_mapping(value: object, field: str, pattern: re.Pattern[str]) -> list[str]:
    """Validate, trim, normalize, and de-duplicate one mapping list."""
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list of strings.")
    normalized: list[str] = []
    seen: set[str] = set()
    prefix = "AST" if field == "mapped_asset_ids" else "RSK"
    for mapping_id in value:
        if not isinstance(mapping_id, str):
            raise TypeError(f"Every value in {field} must be text.")
        clean_id = mapping_id.strip().upper()
        if pattern.fullmatch(clean_id) is None:
            raise ValueError(f"{field} values must use {prefix}- followed by three digits.")
        folded_id = clean_id.casefold()
        if folded_id in seen:
            raise ValueError(f"{field} contains duplicate ID {clean_id}.")
        seen.add(folded_id)
        normalized.append(clean_id)
    return normalized


def _validate_date(value: object) -> str:
    """Validate and return a real date in ISO YYYY-MM-DD format."""
    normalized = _require_text(value, "review_date")
    try:
        parsed = datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("review_date must be a real date in YYYY-MM-DD format.") from exc
    if parsed.strftime("%Y-%m-%d") != normalized:
        raise ValueError("review_date must be a real date in YYYY-MM-DD format.")
    return normalized


def _validate_control(data: Mapping[str, object]) -> dict[str, object]:
    """Validate a complete control and return a normalized deep copy."""
    missing = [field for field in FIELDNAMES if field not in data]
    if missing:
        raise ValueError(f"Missing required control fields: {', '.join(missing)}.")
    normalized: dict[str, object] = {"control_id": _validate_control_id(data["control_id"])}
    for field in TEXT_FIELDS:
        normalized[field] = _require_text(data[field], field)
    normalized["control_type"] = _validate_choice(data["control_type"], "control_type", CONTROL_TYPES)
    normalized["nist_csf_function"] = _validate_choice(
        data["nist_csf_function"], "nist_csf_function", NIST_CSF_FUNCTIONS
    )
    normalized["implementation_status"] = _validate_choice(
        data["implementation_status"], "implementation_status", IMPLEMENTATION_STATUSES
    )
    normalized["effectiveness_pct"] = _validate_effectiveness(data["effectiveness_pct"])
    normalized["mapped_asset_ids"] = _validate_mapping(
        data["mapped_asset_ids"], "mapped_asset_ids", _ASSET_ID_PATTERN
    )
    normalized["mapped_risk_ids"] = _validate_mapping(
        data["mapped_risk_ids"], "mapped_risk_ids", _RISK_ID_PATTERN
    )
    if not normalized["mapped_asset_ids"] and not normalized["mapped_risk_ids"]:
        raise ValueError("A control must map to at least one asset or risk.")
    normalized["review_date"] = _validate_date(data["review_date"])
    for field in ("evidence_reference", "notes"):
        value = data[field]
        if not isinstance(value, str):
            raise TypeError(f"{field} must be text.")
        normalized[field] = value
    return {field: deepcopy(normalized[field]) for field in FIELDNAMES}


def _prepare_controls(controls: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Validate all controls before opening an output file."""
    prepared: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for index, control in enumerate(controls, start=1):
        if not isinstance(control, Mapping):
            raise TypeError(f"Control record {index} must be a dictionary-like mapping.")
        normalized = _validate_control(control)
        folded_id = str(normalized["control_id"]).casefold()
        if folded_id in seen_ids:
            raise ValueError(f"Duplicate control ID {normalized['control_id']}.")
        seen_ids.add(folded_id)
        prepared.append(normalized)
    return prepared


def _parse_mapping(raw_value: object, field: str) -> list[str]:
    """Convert a semicolon-separated CSV mapping into a Python list."""
    if not isinstance(raw_value, str):
        raise ValueError(f"{field} is missing")
    if not raw_value.strip():
        return []
    parts = raw_value.split(";")
    if any(not part.strip() for part in parts):
        raise ValueError(f"{field} contains an empty mapped ID")
    return parts


def load_controls(controls_path: str | Path) -> list[dict[str, object]]:
    """Load controls, converting percentages and mapping fields to Python types."""
    path = Path(controls_path)
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        present_fields = set(reader.fieldnames or [])
        missing = [field for field in FIELDNAMES if field not in present_fields]
        if missing:
            raise ValueError(f"Control CSV is missing required columns: {', '.join(missing)}.")

        controls: list[dict[str, object]] = []
        seen_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(row.get(field) is None for field in FIELDNAMES):
                    raise ValueError("row has the wrong number of columns")
                converted: dict[str, object] = {field: row[field] for field in FIELDNAMES}
                converted["effectiveness_pct"] = float(str(converted["effectiveness_pct"]))
                converted["mapped_asset_ids"] = _parse_mapping(row["mapped_asset_ids"], "mapped_asset_ids")
                converted["mapped_risk_ids"] = _parse_mapping(row["mapped_risk_ids"], "mapped_risk_ids")
                control = _validate_control(converted)
                folded_id = str(control["control_id"]).casefold()
                if folded_id in seen_ids:
                    raise ValueError(f"duplicate control ID {control['control_id']}")
                seen_ids.add(folded_id)
                controls.append(control)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Invalid control data on CSV row {row_number}: {exc}") from exc
    return controls


def save_controls(
    controls_path: str | Path, controls: Iterable[Mapping[str, object]]
) -> None:
    """Write controls in the exact Phase 4 CSV format without changing inputs."""
    prepared = _prepare_controls(controls)
    rows: list[dict[str, object]] = []
    for control in prepared:
        row = {field: deepcopy(control[field]) for field in FIELDNAMES}
        row["effectiveness_pct"] = f"{float(control['effectiveness_pct']):.2f}"
        row["mapped_asset_ids"] = ";".join(control["mapped_asset_ids"])
        row["mapped_risk_ids"] = ";".join(control["mapped_risk_ids"])
        rows.append(row)
    path = Path(controls_path)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def get_control_by_id(
    controls: Iterable[Mapping[str, object]], control_id: str
) -> dict[str, object] | None:
    """Return a deep copy of one case-insensitive control ID match, or None."""
    if not isinstance(control_id, str):
        raise TypeError("control_id must be text.")
    wanted = control_id.casefold()
    for control in controls:
        if str(control.get("control_id", "")).casefold() == wanted:
            return deepcopy(dict(control))
    return None


def search_controls(
    controls: Iterable[Mapping[str, object]], query: str
) -> list[dict[str, object]]:
    """Search control text and mappings while preserving register order."""
    if not isinstance(query, str):
        raise TypeError("query must be text.")
    text_fields = (
        "control_id", "control_name", "control_description", "control_owner",
        "evidence_reference", "notes",
    )
    needle = query.strip().casefold()
    matches: list[dict[str, object]] = []
    for control in controls:
        searchable = [str(control.get(field, "")) for field in text_fields]
        searchable.extend(str(item) for item in control.get("mapped_asset_ids", []))
        searchable.extend(str(item) for item in control.get("mapped_risk_ids", []))
        if not needle or any(needle in value.casefold() for value in searchable):
            matches.append(deepcopy(dict(control)))
    return matches


def filter_controls(
    controls: Iterable[Mapping[str, object]],
    control_type: str | None = None,
    nist_csf_function: str | None = None,
    implementation_status: str | None = None,
    control_owner: str | None = None,
) -> list[dict[str, object]]:
    """Return deep copies of controls matching all case-insensitive filters."""
    criteria = {
        "control_type": control_type,
        "nist_csf_function": nist_csf_function,
        "implementation_status": implementation_status,
        "control_owner": control_owner,
    }
    for field, value in criteria.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{field} filter must be text or None.")
    return [
        deepcopy(dict(control))
        for control in controls
        if all(
            value is None or str(control.get(field, "")).casefold() == value.casefold()
            for field, value in criteria.items()
        )
    ]


def get_controls_for_asset(
    controls: Iterable[Mapping[str, object]], asset_id: str
) -> list[dict[str, object]]:
    """Return deep copies of controls mapped to a case-insensitive asset ID."""
    if not isinstance(asset_id, str):
        raise TypeError("asset_id must be text.")
    wanted = asset_id.casefold()
    return [
        deepcopy(dict(control))
        for control in controls
        if any(str(item).casefold() == wanted for item in control.get("mapped_asset_ids", []))
    ]


def get_controls_for_risk(
    controls: Iterable[Mapping[str, object]], risk_id: str
) -> list[dict[str, object]]:
    """Return deep copies of controls mapped to a case-insensitive risk ID."""
    if not isinstance(risk_id, str):
        raise TypeError("risk_id must be text.")
    wanted = risk_id.casefold()
    return [
        deepcopy(dict(control))
        for control in controls
        if any(str(item).casefold() == wanted for item in control.get("mapped_risk_ids", []))
    ]


def _validate_references(
    control: Mapping[str, object], assets_path: str | Path, risks_path: str | Path
) -> None:
    """Ensure every control mapping points to an existing asset or risk."""
    asset_ids = {asset["asset_id"].casefold() for asset in load_assets(assets_path)}
    risk_ids = {str(risk["risk_id"]).casefold() for risk in load_risks(risks_path)}
    unknown_assets = [item for item in control["mapped_asset_ids"] if item.casefold() not in asset_ids]
    unknown_risks = [item for item in control["mapped_risk_ids"] if item.casefold() not in risk_ids]
    if unknown_assets:
        raise ValueError(f"Unknown mapped asset IDs: {', '.join(unknown_assets)}.")
    if unknown_risks:
        raise ValueError(f"Unknown mapped risk IDs: {', '.join(unknown_risks)}.")


def add_control(
    controls_path: str | Path,
    assets_path: str | Path,
    risks_path: str | Path,
    control_data: dict[str, object],
) -> dict[str, object]:
    """Validate references and append one control to the register."""
    if not isinstance(control_data, dict):
        raise TypeError("control_data must be a dictionary.")
    created = _validate_control(deepcopy(control_data))
    controls = load_controls(controls_path)
    if get_control_by_id(controls, str(created["control_id"])) is not None:
        raise ValueError(f"Control ID {created['control_id']} already exists.")
    _validate_references(created, assets_path, risks_path)
    save_controls(controls_path, [*controls, created])
    return deepcopy(created)


def update_control(
    controls_path: str | Path,
    assets_path: str | Path,
    risks_path: str | Path,
    control_id: str,
    updates: dict[str, object],
) -> dict[str, object]:
    """Validate and update a control without changing its register position."""
    if not isinstance(control_id, str):
        raise TypeError("control_id must be text.")
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dictionary.")
    if "control_id" in updates:
        raise ValueError("The control_id of an existing control cannot be changed.")
    unknown = set(updates) - set(FIELDNAMES)
    if unknown:
        raise ValueError(f"Unknown control fields: {', '.join(sorted(unknown))}.")
    controls = load_controls(controls_path)
    match_index = next(
        (
            index for index, control in enumerate(controls)
            if str(control["control_id"]).casefold() == control_id.casefold()
        ),
        None,
    )
    if match_index is None:
        raise ValueError(f"Control ID {control_id!r} does not exist.")
    updated = _validate_control({**controls[match_index], **deepcopy(updates)})
    _validate_references(updated, assets_path, risks_path)
    controls[match_index] = updated
    save_controls(controls_path, controls)
    return deepcopy(updated)


def delete_control(controls_path: str | Path, control_id: str) -> dict[str, object]:
    """Delete a control by ID and return a deep copy of the removed record."""
    if not isinstance(control_id, str):
        raise TypeError("control_id must be text.")
    controls = load_controls(controls_path)
    for index, control in enumerate(controls):
        if str(control["control_id"]).casefold() == control_id.casefold():
            deleted = controls.pop(index)
            save_controls(controls_path, controls)
            return deepcopy(deleted)
    raise ValueError(f"Control ID {control_id!r} does not exist.")
