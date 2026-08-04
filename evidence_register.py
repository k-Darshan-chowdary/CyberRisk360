"""CSV-backed control-evidence register operations for CyberRisk360."""

from __future__ import annotations

import csv
import re
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Mapping

from control_register import load_controls


FIELDNAMES = [
    "evidence_id", "control_id", "evidence_name", "evidence_type",
    "description", "evidence_owner", "collected_date", "review_date",
    "expiration_date", "status", "storage_reference", "reviewer", "notes",
]

EVIDENCE_TYPES = {
    "Policy", "Procedure", "Configuration", "Screenshot", "Report", "Log",
    "Ticket", "Attestation", "Test Result", "Contract",
}
STATUSES = {"Current", "Expiring Soon", "Expired", "Under Review", "Rejected"}
REQUIRED_TEXT_FIELDS = {
    "evidence_name", "description", "evidence_owner", "storage_reference", "reviewer",
}
SEARCH_FIELDS = (
    "evidence_id", "control_id", "evidence_name", "evidence_type", "description",
    "evidence_owner", "storage_reference", "reviewer", "notes",
)
_EVIDENCE_ID_PATTERN = re.compile(r"EVD-\d{3}", re.IGNORECASE)
_CONTROL_ID_PATTERN = re.compile(r"CTL-\d{3}", re.IGNORECASE)


def _require_text(value: object, field: str) -> str:
    """Return trimmed, non-empty text for a required field."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text.")
    result = value.strip()
    if not result:
        raise ValueError(f"{field} cannot be empty.")
    return result


def _validate_id(value: object, field: str, pattern: re.Pattern[str]) -> str:
    """Validate and normalize an evidence or control identifier."""
    result = _require_text(value, field).upper()
    if pattern.fullmatch(result) is None:
        prefix = "EVD" if field == "evidence_id" else "CTL"
        raise ValueError(f"{field} must use {prefix}- followed by exactly three digits.")
    return result


def _validate_choice(value: object, field: str, choices: set[str]) -> str:
    """Validate one value from a fixed, case-sensitive vocabulary."""
    result = _require_text(value, field)
    if result not in choices:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(choices))}.")
    return result


def _validate_date(value: object, field: str) -> str:
    """Validate a real date written in exact YYYY-MM-DD form."""
    result = _require_text(value, field)
    try:
        parsed = datetime.strptime(result, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must be a real date in YYYY-MM-DD format.") from exc
    if parsed.strftime("%Y-%m-%d") != result:
        raise ValueError(f"{field} must be a real date in YYYY-MM-DD format.")
    return result


def _parse_as_of_date(value: str | None) -> date:
    """Return today's local date or validate a supplied ISO date string."""
    if value is None:
        return date.today()
    return datetime.strptime(_validate_date(value, "as_of_date"), "%Y-%m-%d").date()


def _validate_evidence(data: Mapping[str, object]) -> dict[str, str]:
    """Validate a complete evidence record and return a normalized copy."""
    missing = [field for field in FIELDNAMES if field not in data]
    if missing:
        raise ValueError(f"Missing required evidence fields: {', '.join(missing)}.")
    result: dict[str, str] = {
        "evidence_id": _validate_id(data["evidence_id"], "evidence_id", _EVIDENCE_ID_PATTERN),
        "control_id": _validate_id(data["control_id"], "control_id", _CONTROL_ID_PATTERN),
    }
    for field in REQUIRED_TEXT_FIELDS:
        result[field] = _require_text(data[field], field)
    result["evidence_type"] = _validate_choice(
        data["evidence_type"], "evidence_type", EVIDENCE_TYPES
    )
    result["status"] = _validate_choice(data["status"], "status", STATUSES)
    for field in ("collected_date", "review_date", "expiration_date"):
        result[field] = _validate_date(data[field], field)
    collected = date.fromisoformat(result["collected_date"])
    if date.fromisoformat(result["review_date"]) < collected:
        raise ValueError("review_date cannot be before collected_date.")
    if date.fromisoformat(result["expiration_date"]) < collected:
        raise ValueError("expiration_date cannot be before collected_date.")
    notes = data["notes"]
    if not isinstance(notes, str):
        raise TypeError("notes must be text.")
    result["notes"] = notes
    return {field: result[field] for field in FIELDNAMES}


def _prepare_records(records: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    """Validate all records and duplicate IDs before opening an output file."""
    prepared: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            raise TypeError(f"Evidence record {index} must be a dictionary-like mapping.")
        item = _validate_evidence(record)
        folded = item["evidence_id"].casefold()
        if folded in seen:
            raise ValueError(f"Duplicate evidence ID {item['evidence_id']}.")
        seen.add(folded)
        prepared.append(item)
    return prepared


def load_evidence(evidence_path: str | Path) -> list[dict[str, str]]:
    """Load and validate evidence records while preserving CSV row order."""
    path = Path(evidence_path)
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fields = set(reader.fieldnames or [])
        missing = [field for field in FIELDNAMES if field not in fields]
        if missing:
            raise ValueError(f"Evidence CSV is missing required columns: {', '.join(missing)}.")
        records: list[dict[str, str]] = []
        seen: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(row.get(field) is None for field in FIELDNAMES):
                    raise ValueError("row has the wrong number of columns")
                item = _validate_evidence({field: row[field] for field in FIELDNAMES})
                folded = item["evidence_id"].casefold()
                if folded in seen:
                    raise ValueError(f"duplicate evidence ID {item['evidence_id']}")
                seen.add(folded)
                records.append(item)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid evidence data on CSV row {row_number}: {exc}") from exc
    return records


def save_evidence(
    evidence_path: str | Path, evidence_records: Iterable[Mapping[str, object]]
) -> None:
    """Write validated evidence in the exact Phase 5 field order."""
    prepared = _prepare_records(evidence_records)
    with Path(evidence_path).open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(prepared)


def get_evidence_by_id(
    evidence_records: Iterable[Mapping[str, str]], evidence_id: str
) -> dict[str, str] | None:
    """Return a copy of one case-insensitive evidence ID match, or None."""
    if not isinstance(evidence_id, str):
        raise TypeError("evidence_id must be text.")
    wanted = evidence_id.casefold()
    for record in evidence_records:
        if str(record.get("evidence_id", "")).casefold() == wanted:
            return deepcopy(dict(record))
    return None


def search_evidence(
    evidence_records: Iterable[Mapping[str, str]], query: str
) -> list[dict[str, str]]:
    """Search common evidence text fields and return copies in original order."""
    if not isinstance(query, str):
        raise TypeError("query must be text.")
    needle = query.strip().casefold()
    return [
        deepcopy(dict(record))
        for record in evidence_records
        if not needle
        or any(needle in str(record.get(field, "")).casefold() for field in SEARCH_FIELDS)
    ]


def filter_evidence(
    evidence_records: Iterable[Mapping[str, str]],
    control_id: str | None = None,
    evidence_type: str | None = None,
    status: str | None = None,
    evidence_owner: str | None = None,
    reviewer: str | None = None,
) -> list[dict[str, str]]:
    """Return copies of records matching every supplied case-insensitive filter."""
    criteria = {
        "control_id": control_id, "evidence_type": evidence_type, "status": status,
        "evidence_owner": evidence_owner, "reviewer": reviewer,
    }
    for field, value in criteria.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{field} filter must be text or None.")
    return [
        deepcopy(dict(record))
        for record in evidence_records
        if all(value is None or str(record.get(field, "")).casefold() == value.casefold()
               for field, value in criteria.items())
    ]


def get_evidence_for_control(
    evidence_records: Iterable[Mapping[str, str]], control_id: str
) -> list[dict[str, str]]:
    """Return copies of all evidence mapped to one control."""
    if not isinstance(control_id, str):
        raise TypeError("control_id must be text.")
    return filter_evidence(evidence_records, control_id=control_id)


def is_evidence_expired(
    evidence_record: Mapping[str, str], as_of_date: str | None = None
) -> bool:
    """Return whether evidence expired before the selected local calendar date."""
    if not isinstance(evidence_record, Mapping):
        raise TypeError("evidence_record must be a dictionary-like mapping.")
    expiration = date.fromisoformat(_validate_date(evidence_record.get("expiration_date"), "expiration_date"))
    return expiration < _parse_as_of_date(as_of_date)


def get_expired_evidence(
    evidence_records: Iterable[Mapping[str, str]], as_of_date: str | None = None
) -> list[dict[str, str]]:
    """Return copies of expired evidence in register order."""
    selected = _parse_as_of_date(as_of_date)
    selected_text = selected.isoformat()
    return [deepcopy(dict(record)) for record in evidence_records
            if is_evidence_expired(record, selected_text)]


def get_expiring_evidence(
    evidence_records: Iterable[Mapping[str, str]], days: int = 30,
    as_of_date: str | None = None,
) -> list[dict[str, str]]:
    """Return evidence expiring inclusively within a non-negative day window."""
    if isinstance(days, bool) or not isinstance(days, int):
        raise TypeError("days must be a non-negative integer.")
    if days < 0:
        raise ValueError("days must be a non-negative integer.")
    selected = _parse_as_of_date(as_of_date)
    final_day = selected + timedelta(days=days)
    matches: list[dict[str, str]] = []
    for record in evidence_records:
        expiration = date.fromisoformat(_validate_date(record.get("expiration_date"), "expiration_date"))
        if selected <= expiration <= final_day:
            matches.append(deepcopy(dict(record)))
    return matches


def _validate_control_reference(record: Mapping[str, str], controls_path: str | Path) -> None:
    """Ensure an evidence record refers to an existing control."""
    valid_ids = {str(control["control_id"]).casefold() for control in load_controls(controls_path)}
    if record["control_id"].casefold() not in valid_ids:
        raise ValueError(f"control_id {record['control_id']!r} does not exist in the control CSV.")


def add_evidence(
    evidence_path: str | Path, controls_path: str | Path, evidence_data: dict[str, object]
) -> dict[str, str]:
    """Validate and append one new control-evidence record."""
    if not isinstance(evidence_data, dict):
        raise TypeError("evidence_data must be a dictionary.")
    created = _validate_evidence(deepcopy(evidence_data))
    records = load_evidence(evidence_path)
    if get_evidence_by_id(records, created["evidence_id"]) is not None:
        raise ValueError(f"Evidence ID {created['evidence_id']} already exists.")
    _validate_control_reference(created, controls_path)
    save_evidence(evidence_path, [*records, created])
    return deepcopy(created)


def update_evidence(
    evidence_path: str | Path, controls_path: str | Path, evidence_id: str,
    updates: dict[str, object],
) -> dict[str, str]:
    """Validate and update evidence without changing its register position."""
    if not isinstance(evidence_id, str):
        raise TypeError("evidence_id must be text.")
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dictionary.")
    if "evidence_id" in updates:
        raise ValueError("The evidence_id of existing evidence cannot be changed.")
    unknown = set(updates) - set(FIELDNAMES)
    if unknown:
        raise ValueError(f"Unknown evidence fields: {', '.join(sorted(unknown))}.")
    records = load_evidence(evidence_path)
    index = next((i for i, item in enumerate(records)
                  if item["evidence_id"].casefold() == evidence_id.casefold()), None)
    if index is None:
        raise ValueError(f"Evidence ID {evidence_id!r} does not exist.")
    updated = _validate_evidence({**records[index], **deepcopy(updates)})
    if "control_id" in updates:
        _validate_control_reference(updated, controls_path)
    records[index] = updated
    save_evidence(evidence_path, records)
    return deepcopy(updated)


def delete_evidence(evidence_path: str | Path, evidence_id: str) -> dict[str, str]:
    """Delete evidence by ID and return a copy of the removed record."""
    if not isinstance(evidence_id, str):
        raise TypeError("evidence_id must be text.")
    records = load_evidence(evidence_path)
    for index, record in enumerate(records):
        if record["evidence_id"].casefold() == evidence_id.casefold():
            deleted = records.pop(index)
            save_evidence(evidence_path, records)
            return deepcopy(deleted)
    raise ValueError(f"Evidence ID {evidence_id!r} does not exist.")
