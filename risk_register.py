"""CSV-backed risk register operations for CyberRisk360."""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from risk_engine import assess_risk


FIELDNAMES = [
    "risk_id",
    "risk_title",
    "threat",
    "vulnerability",
    "affected_asset_id",
    "likelihood",
    "impact",
    "inherent_score",
    "inherent_rating",
    "existing_controls",
    "control_effectiveness_pct",
    "residual_score",
    "residual_rating",
    "risk_owner",
    "treatment",
    "status",
    "target_date",
    "nist_csf_function",
]

USER_FIELDS = [
    "risk_id",
    "risk_title",
    "threat",
    "vulnerability",
    "affected_asset_id",
    "likelihood",
    "impact",
    "existing_controls",
    "control_effectiveness_pct",
    "risk_owner",
    "treatment",
    "status",
    "target_date",
    "nist_csf_function",
]

DERIVED_FIELDS = {
    "inherent_score",
    "inherent_rating",
    "residual_score",
    "residual_rating",
}
TEXT_FIELDS = {
    "risk_title",
    "threat",
    "vulnerability",
    "existing_controls",
    "risk_owner",
}
TREATMENTS = {"Mitigate", "Avoid", "Transfer", "Accept"}
STATUSES = {"Open", "In Progress", "Monitoring", "Accepted", "Closed"}
NIST_CSF_FUNCTIONS = {
    "Govern",
    "Identify",
    "Protect",
    "Detect",
    "Respond",
    "Recover",
}

_RISK_ID_PATTERN = re.compile(r"RSK-\d{3}", re.IGNORECASE)
_ASSET_ID_PATTERN = re.compile(r"AST-\d{3}", re.IGNORECASE)


def _require_text(value: object, field: str) -> str:
    """Return trimmed required text or raise a helpful validation error."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} cannot be empty.")
    return normalized


def _validate_choice(value: object, field: str, choices: set[str]) -> str:
    """Validate a required string against a case-sensitive stored vocabulary."""
    normalized = _require_text(value, field)
    if normalized not in choices:
        options = ", ".join(sorted(choices))
        raise ValueError(f"{field} must be one of: {options}.")
    return normalized


def _validate_integer(value: object, field: str) -> int:
    """Validate a non-boolean integer from one through five."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer from 1 through 5.")
    if not 1 <= value <= 5:
        raise ValueError(f"{field} must be between 1 and 5.")
    return value


def _validate_effectiveness(value: object) -> int | float:
    """Validate a non-boolean control effectiveness percentage."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("control_effectiveness_pct must be a number from 0 through 100.")
    if not 0 <= value <= 100:
        raise ValueError("control_effectiveness_pct must be between 0 and 100.")
    return value


def _validate_date(value: object) -> str:
    """Validate and return a date in ISO YYYY-MM-DD format."""
    normalized = _require_text(value, "target_date")
    try:
        parsed = datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("target_date must be a real date in YYYY-MM-DD format.") from exc
    if parsed.strftime("%Y-%m-%d") != normalized:
        raise ValueError("target_date must be a real date in YYYY-MM-DD format.")
    return normalized


def _validate_id(value: object, field: str, pattern: re.Pattern[str]) -> str:
    """Validate and normalize a risk or asset identifier."""
    normalized = _require_text(value, field).upper()
    if pattern.fullmatch(normalized) is None:
        prefix = "RSK" if field == "risk_id" else "AST"
        raise ValueError(f"{field} must use the format {prefix}- followed by three digits.")
    return normalized


def _validate_user_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate user-maintained fields and return a normalized copy."""
    missing = [field for field in USER_FIELDS if field not in data]
    if missing:
        raise ValueError(f"Missing required risk fields: {', '.join(missing)}.")

    normalized: dict[str, Any] = {}
    normalized["risk_id"] = _validate_id(data["risk_id"], "risk_id", _RISK_ID_PATTERN)
    for field in TEXT_FIELDS:
        normalized[field] = _require_text(data[field], field)
    normalized["affected_asset_id"] = _validate_id(
        data["affected_asset_id"], "affected_asset_id", _ASSET_ID_PATTERN
    )
    normalized["likelihood"] = _validate_integer(data["likelihood"], "likelihood")
    normalized["impact"] = _validate_integer(data["impact"], "impact")
    normalized["control_effectiveness_pct"] = _validate_effectiveness(
        data["control_effectiveness_pct"]
    )
    normalized["treatment"] = _validate_choice(
        data["treatment"], "treatment", TREATMENTS
    )
    normalized["status"] = _validate_choice(data["status"], "status", STATUSES)
    normalized["target_date"] = _validate_date(data["target_date"])
    normalized["nist_csf_function"] = _validate_choice(
        data["nist_csf_function"], "nist_csf_function", NIST_CSF_FUNCTIONS
    )
    return normalized


def _build_risk(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a risk and calculate its score and rating fields."""
    normalized = _validate_user_data(data)
    assessment = assess_risk(
        normalized["likelihood"],
        normalized["impact"],
        normalized["control_effectiveness_pct"],
    )
    normalized.update(
        {field: assessment[field] for field in DERIVED_FIELDS}
    )
    return {field: normalized[field] for field in FIELDNAMES}


def _load_asset_ids(assets_path: str | Path) -> set[str]:
    """Load valid asset IDs from an asset CSV file."""
    path = Path(assets_path)
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None or "asset_id" not in reader.fieldnames:
            raise ValueError("Asset CSV is missing the required asset_id column.")
        asset_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                asset_id = _validate_id(row.get("asset_id"), "asset_id", _ASSET_ID_PATTERN)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid asset data on CSV row {row_number}: {exc}") from exc
            asset_ids.add(asset_id.casefold())
    return asset_ids


def _validate_asset(asset_id: str, assets_path: str | Path) -> None:
    """Raise ValueError when an asset reference is not in the asset CSV."""
    if asset_id.casefold() not in _load_asset_ids(assets_path):
        raise ValueError(f"affected_asset_id {asset_id!r} does not exist in the asset CSV.")


def load_risks(risks_path: str | Path) -> list[dict[str, Any]]:
    """Load, validate, and type-convert risk records from a CSV file."""
    path = Path(risks_path)
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        present_fields = set(reader.fieldnames or [])
        missing = [field for field in FIELDNAMES if field not in present_fields]
        if missing:
            raise ValueError(f"Risk CSV is missing required columns: {', '.join(missing)}.")

        risks: list[dict[str, Any]] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                converted: dict[str, Any] = {field: row.get(field) for field in FIELDNAMES}
                for field in ("likelihood", "impact", "inherent_score"):
                    converted[field] = int(converted[field])
                for field in ("control_effectiveness_pct", "residual_score"):
                    converted[field] = float(converted[field])
                calculated = _build_risk(converted)
                if any(converted[field] != calculated[field] for field in DERIVED_FIELDS):
                    raise ValueError("calculated scores or ratings do not match the risk inputs")
                risks.append(converted)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Invalid risk data on CSV row {row_number}: {exc}") from exc
    return risks


def save_risks(risks_path: str | Path, risks: Iterable[Mapping[str, Any]]) -> None:
    """Write risks in the Phase 1 column order without changing caller data."""
    prepared: list[dict[str, Any]] = []
    for index, risk in enumerate(risks, start=1):
        if not isinstance(risk, Mapping):
            raise TypeError(f"Risk record {index} must be a dictionary-like mapping.")
        missing = [field for field in FIELDNAMES if field not in risk]
        if missing:
            raise ValueError(f"Risk record {index} is missing fields: {', '.join(missing)}.")
        row = {field: risk[field] for field in FIELDNAMES}
        try:
            row["residual_score"] = f"{float(row['residual_score']):.2f}"
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Risk record {index} has an invalid residual_score.") from exc
        prepared.append(row)

    path = Path(risks_path)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(prepared)


def get_risk_by_id(risks: Iterable[Mapping[str, Any]], risk_id: str) -> dict[str, Any] | None:
    """Return a copy of the case-insensitive ID match, or None."""
    if not isinstance(risk_id, str):
        raise TypeError("risk_id must be text.")
    wanted = risk_id.casefold()
    for risk in risks:
        if str(risk.get("risk_id", "")).casefold() == wanted:
            return dict(risk)
    return None


def search_risks(risks: Iterable[Mapping[str, Any]], query: str) -> list[dict[str, Any]]:
    """Search common risk text fields while preserving record order."""
    if not isinstance(query, str):
        raise TypeError("query must be text.")
    search_fields = (
        "risk_id",
        "risk_title",
        "threat",
        "vulnerability",
        "affected_asset_id",
        "existing_controls",
        "risk_owner",
    )
    needle = query.strip().casefold()
    return [
        dict(risk)
        for risk in risks
        if not needle
        or any(needle in str(risk.get(field, "")).casefold() for field in search_fields)
    ]


def filter_risks(
    risks: Iterable[Mapping[str, Any]],
    status: str | None = None,
    inherent_rating: str | None = None,
    residual_rating: str | None = None,
    treatment: str | None = None,
    nist_csf_function: str | None = None,
) -> list[dict[str, Any]]:
    """Return copies of risks matching every supplied case-insensitive filter."""
    criteria = {
        "status": status,
        "inherent_rating": inherent_rating,
        "residual_rating": residual_rating,
        "treatment": treatment,
        "nist_csf_function": nist_csf_function,
    }
    for field, value in criteria.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{field} filter must be text or None.")
    return [
        dict(risk)
        for risk in risks
        if all(
            value is None
            or str(risk.get(field, "")).casefold() == value.casefold()
            for field, value in criteria.items()
        )
    ]


def add_risk(
    risks_path: str | Path, assets_path: str | Path, risk_data: dict[str, Any]
) -> dict[str, Any]:
    """Validate, score, append, and return a copy of one new risk."""
    if not isinstance(risk_data, dict):
        raise TypeError("risk_data must be a dictionary.")
    created = _build_risk(dict(risk_data))
    risks = load_risks(risks_path)
    if get_risk_by_id(risks, created["risk_id"]) is not None:
        raise ValueError(f"Risk ID {created['risk_id']} already exists.")
    _validate_asset(created["affected_asset_id"], assets_path)
    save_risks(risks_path, [*risks, created])
    return dict(created)


def update_risk(
    risks_path: str | Path,
    assets_path: str | Path,
    risk_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Validate, rescore, save, and return a copy of an existing risk."""
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dictionary.")
    if not isinstance(risk_id, str):
        raise TypeError("risk_id must be text.")
    if "risk_id" in updates:
        raise ValueError("The risk_id of an existing risk cannot be changed.")
    unknown = set(updates) - set(FIELDNAMES)
    if unknown:
        raise ValueError(f"Unknown risk fields: {', '.join(sorted(unknown))}.")

    risks = load_risks(risks_path)
    match_index = next(
        (
            index
            for index, risk in enumerate(risks)
            if risk["risk_id"].casefold() == risk_id.casefold()
        ),
        None,
    )
    if match_index is None:
        raise ValueError(f"Risk ID {risk_id!r} does not exist.")

    editable_updates = {key: value for key, value in updates.items() if key not in DERIVED_FIELDS}
    candidate = {**risks[match_index], **editable_updates}
    updated = _build_risk(candidate)
    if "affected_asset_id" in updates:
        _validate_asset(updated["affected_asset_id"], assets_path)
    risks[match_index] = updated
    save_risks(risks_path, risks)
    return dict(updated)


def delete_risk(risks_path: str | Path, risk_id: str) -> dict[str, Any]:
    """Delete one case-insensitive ID match and return a copy of it."""
    if not isinstance(risk_id, str):
        raise TypeError("risk_id must be text.")
    risks = load_risks(risks_path)
    for index, risk in enumerate(risks):
        if risk["risk_id"].casefold() == risk_id.casefold():
            deleted = risks.pop(index)
            save_risks(risks_path, risks)
            return dict(deleted)
    raise ValueError(f"Risk ID {risk_id!r} does not exist.")
