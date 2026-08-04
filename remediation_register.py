"""CSV-backed remediation-action register operations for CyberRisk360."""

from __future__ import annotations

import csv
import re
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Mapping

from control_register import load_controls
from risk_register import load_risks


FIELDNAMES = [
    "action_id", "action_title", "description", "related_risk_id",
    "related_control_id", "action_owner", "priority", "status", "created_date",
    "due_date", "completion_pct", "closure_date", "verification_notes",
]
PRIORITIES = {"Low", "Medium", "High", "Critical"}
STATUSES = {"Open", "In Progress", "Blocked", "Completed", "Closed", "Cancelled"}
SEARCH_FIELDS = (
    "action_id", "action_title", "description", "related_risk_id",
    "related_control_id", "action_owner", "verification_notes",
)
_ACTION_ID_PATTERN = re.compile(r"ACT-\d{3}", re.IGNORECASE)
_RISK_ID_PATTERN = re.compile(r"RSK-\d{3}", re.IGNORECASE)
_CONTROL_ID_PATTERN = re.compile(r"CTL-\d{3}", re.IGNORECASE)


def _require_text(value: object, field: str) -> str:
    """Return trimmed, non-empty text for a required field."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text.")
    result = value.strip()
    if not result:
        raise ValueError(f"{field} cannot be empty.")
    return result


def _optional_text(value: object, field: str) -> str:
    """Return trimmed optional text while rejecting non-string values."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text.")
    return value.strip()


def _validate_id(value: object, field: str, pattern: re.Pattern[str]) -> str:
    """Validate and normalize a Phase 5 relationship identifier."""
    result = _require_text(value, field).upper()
    if pattern.fullmatch(result) is None:
        prefix = {"action_id": "ACT", "related_risk_id": "RSK"}.get(field, "CTL")
        raise ValueError(f"{field} must use {prefix}- followed by exactly three digits.")
    return result


def _validate_choice(value: object, field: str, choices: set[str]) -> str:
    """Validate a required fixed-vocabulary value."""
    result = _require_text(value, field)
    if result not in choices:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(choices))}.")
    return result


def _validate_date(value: object, field: str, optional: bool = False) -> str:
    """Validate an exact ISO calendar date, optionally allowing empty text."""
    if optional:
        result = _optional_text(value, field)
        if not result:
            return ""
    else:
        result = _require_text(value, field)
    try:
        parsed = datetime.strptime(result, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must be a real date in YYYY-MM-DD format.") from exc
    if parsed.strftime("%Y-%m-%d") != result:
        raise ValueError(f"{field} must be a real date in YYYY-MM-DD format.")
    return result


def _parse_as_of_date(value: str | None) -> date:
    """Return today's local date or validate a requested comparison date."""
    if value is None:
        return date.today()
    return date.fromisoformat(_validate_date(value, "as_of_date"))


def _validate_completion(value: object) -> int:
    """Validate a non-boolean integer percentage from zero through one hundred."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("completion_pct must be an integer from 0 through 100.")
    if not 0 <= value <= 100:
        raise ValueError("completion_pct must be between 0 and 100.")
    return value


def _validate_action(data: Mapping[str, object]) -> dict[str, object]:
    """Validate a complete remediation action and return a normalized copy."""
    missing = [field for field in FIELDNAMES if field not in data]
    if missing:
        raise ValueError(f"Missing required remediation fields: {', '.join(missing)}.")
    result: dict[str, object] = {
        "action_id": _validate_id(data["action_id"], "action_id", _ACTION_ID_PATTERN),
    }
    for field in ("action_title", "description", "action_owner"):
        result[field] = _require_text(data[field], field)
    risk_id = _optional_text(data["related_risk_id"], "related_risk_id")
    control_id = _optional_text(data["related_control_id"], "related_control_id")
    result["related_risk_id"] = (
        _validate_id(risk_id, "related_risk_id", _RISK_ID_PATTERN) if risk_id else ""
    )
    result["related_control_id"] = (
        _validate_id(control_id, "related_control_id", _CONTROL_ID_PATTERN) if control_id else ""
    )
    if not risk_id and not control_id:
        raise ValueError("At least one related risk or control must be provided.")
    result["priority"] = _validate_choice(data["priority"], "priority", PRIORITIES)
    result["status"] = _validate_choice(data["status"], "status", STATUSES)
    result["created_date"] = _validate_date(data["created_date"], "created_date")
    result["due_date"] = _validate_date(data["due_date"], "due_date")
    result["closure_date"] = _validate_date(data["closure_date"], "closure_date", optional=True)
    result["completion_pct"] = _validate_completion(data["completion_pct"])
    notes = data["verification_notes"]
    if not isinstance(notes, str):
        raise TypeError("verification_notes must be text.")
    result["verification_notes"] = notes

    created = date.fromisoformat(str(result["created_date"]))
    if date.fromisoformat(str(result["due_date"])) < created:
        raise ValueError("due_date cannot be before created_date.")
    if result["closure_date"] and date.fromisoformat(str(result["closure_date"])) < created:
        raise ValueError("closure_date cannot be before created_date.")
    if result["status"] in {"Completed", "Closed"} and result["completion_pct"] != 100:
        raise ValueError("Completed or Closed actions must have completion_pct equal to 100.")
    if result["status"] == "Open" and result["completion_pct"] == 100:
        raise ValueError("Open actions cannot have completion_pct equal to 100.")
    if result["status"] == "Closed" and not result["closure_date"]:
        raise ValueError("Closed actions require a closure_date.")
    return {field: deepcopy(result[field]) for field in FIELDNAMES}


def _prepare_actions(actions: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Validate every action and duplicate ID before writing a file."""
    prepared: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, Mapping):
            raise TypeError(f"Remediation action {index} must be a dictionary-like mapping.")
        item = _validate_action(action)
        folded = str(item["action_id"]).casefold()
        if folded in seen:
            raise ValueError(f"Duplicate action ID {item['action_id']}.")
        seen.add(folded)
        prepared.append(item)
    return prepared


def load_remediation_actions(actions_path: str | Path) -> list[dict[str, object]]:
    """Load actions, converting completion percentages to integers."""
    path = Path(actions_path)
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fields = set(reader.fieldnames or [])
        missing = [field for field in FIELDNAMES if field not in fields]
        if missing:
            raise ValueError(f"Remediation CSV is missing required columns: {', '.join(missing)}.")
        actions: list[dict[str, object]] = []
        seen: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(row.get(field) is None for field in FIELDNAMES):
                    raise ValueError("row has the wrong number of columns")
                converted: dict[str, object] = {field: row[field] for field in FIELDNAMES}
                converted["completion_pct"] = int(row["completion_pct"])
                item = _validate_action(converted)
                folded = str(item["action_id"]).casefold()
                if folded in seen:
                    raise ValueError(f"duplicate action ID {item['action_id']}")
                seen.add(folded)
                actions.append(item)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Invalid remediation data on CSV row {row_number}: {exc}") from exc
    return actions


def save_remediation_actions(
    actions_path: str | Path, actions: Iterable[Mapping[str, object]]
) -> None:
    """Write validated actions in the exact Phase 5 CSV field order."""
    prepared = _prepare_actions(actions)
    with Path(actions_path).open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(prepared)


def get_action_by_id(
    actions: Iterable[Mapping[str, object]], action_id: str
) -> dict[str, object] | None:
    """Return a copy of a case-insensitive action ID match, or None."""
    if not isinstance(action_id, str):
        raise TypeError("action_id must be text.")
    wanted = action_id.casefold()
    for action in actions:
        if str(action.get("action_id", "")).casefold() == wanted:
            return deepcopy(dict(action))
    return None


def search_actions(
    actions: Iterable[Mapping[str, object]], query: str
) -> list[dict[str, object]]:
    """Search action text fields and return copies in original order."""
    if not isinstance(query, str):
        raise TypeError("query must be text.")
    needle = query.strip().casefold()
    return [deepcopy(dict(action)) for action in actions
            if not needle or any(needle in str(action.get(field, "")).casefold()
                                 for field in SEARCH_FIELDS)]


def filter_actions(
    actions: Iterable[Mapping[str, object]], priority: str | None = None,
    status: str | None = None, action_owner: str | None = None,
    related_risk_id: str | None = None, related_control_id: str | None = None,
) -> list[dict[str, object]]:
    """Return copies of actions matching all supplied case-insensitive filters."""
    criteria = {
        "priority": priority, "status": status, "action_owner": action_owner,
        "related_risk_id": related_risk_id, "related_control_id": related_control_id,
    }
    for field, value in criteria.items():
        if value is not None and not isinstance(value, str):
            raise TypeError(f"{field} filter must be text or None.")
    return [deepcopy(dict(action)) for action in actions
            if all(value is None or str(action.get(field, "")).casefold() == value.casefold()
                   for field, value in criteria.items())]


def get_actions_for_risk(
    actions: Iterable[Mapping[str, object]], risk_id: str
) -> list[dict[str, object]]:
    """Return copies of actions related to one risk."""
    if not isinstance(risk_id, str):
        raise TypeError("risk_id must be text.")
    return filter_actions(actions, related_risk_id=risk_id)


def get_actions_for_control(
    actions: Iterable[Mapping[str, object]], control_id: str
) -> list[dict[str, object]]:
    """Return copies of actions related to one security control."""
    if not isinstance(control_id, str):
        raise TypeError("control_id must be text.")
    return filter_actions(actions, related_control_id=control_id)


def is_action_overdue(action: Mapping[str, object], as_of_date: str | None = None) -> bool:
    """Return whether an active action's due date is before the selected date."""
    if not isinstance(action, Mapping):
        raise TypeError("action must be a dictionary-like mapping.")
    status = action.get("status")
    if not isinstance(status, str):
        raise TypeError("status must be text.")
    due = date.fromisoformat(_validate_date(action.get("due_date"), "due_date"))
    return status.casefold() not in {"closed", "cancelled"} and due < _parse_as_of_date(as_of_date)


def get_overdue_actions(
    actions: Iterable[Mapping[str, object]], as_of_date: str | None = None
) -> list[dict[str, object]]:
    """Return copies of overdue actions in original register order."""
    selected = _parse_as_of_date(as_of_date).isoformat()
    return [deepcopy(dict(action)) for action in actions if is_action_overdue(action, selected)]


def _validate_references(
    action: Mapping[str, object], risks_path: str | Path, controls_path: str | Path
) -> None:
    """Ensure all non-empty risk and control relationships exist."""
    if action["related_risk_id"]:
        valid_risks = {str(risk["risk_id"]).casefold() for risk in load_risks(risks_path)}
        if str(action["related_risk_id"]).casefold() not in valid_risks:
            raise ValueError(f"related_risk_id {action['related_risk_id']!r} does not exist.")
    if action["related_control_id"]:
        valid_controls = {str(control["control_id"]).casefold()
                          for control in load_controls(controls_path)}
        if str(action["related_control_id"]).casefold() not in valid_controls:
            raise ValueError(f"related_control_id {action['related_control_id']!r} does not exist.")


def add_remediation_action(
    actions_path: str | Path, risks_path: str | Path, controls_path: str | Path,
    action_data: dict[str, object],
) -> dict[str, object]:
    """Validate references and append one remediation action."""
    if not isinstance(action_data, dict):
        raise TypeError("action_data must be a dictionary.")
    created = _validate_action(deepcopy(action_data))
    actions = load_remediation_actions(actions_path)
    if get_action_by_id(actions, str(created["action_id"])) is not None:
        raise ValueError(f"Action ID {created['action_id']} already exists.")
    _validate_references(created, risks_path, controls_path)
    save_remediation_actions(actions_path, [*actions, created])
    return deepcopy(created)


def update_remediation_action(
    actions_path: str | Path, risks_path: str | Path, controls_path: str | Path,
    action_id: str, updates: dict[str, object],
) -> dict[str, object]:
    """Validate and update an action without changing its register position."""
    if not isinstance(action_id, str):
        raise TypeError("action_id must be text.")
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dictionary.")
    if "action_id" in updates:
        raise ValueError("The action_id of an existing action cannot be changed.")
    unknown = set(updates) - set(FIELDNAMES)
    if unknown:
        raise ValueError(f"Unknown remediation fields: {', '.join(sorted(unknown))}.")
    actions = load_remediation_actions(actions_path)
    index = next((i for i, item in enumerate(actions)
                  if str(item["action_id"]).casefold() == action_id.casefold()), None)
    if index is None:
        raise ValueError(f"Action ID {action_id!r} does not exist.")
    updated = _validate_action({**actions[index], **deepcopy(updates)})
    _validate_references(updated, risks_path, controls_path)
    actions[index] = updated
    save_remediation_actions(actions_path, actions)
    return deepcopy(updated)


def delete_remediation_action(
    actions_path: str | Path, action_id: str
) -> dict[str, object]:
    """Delete an action by ID and return a copy of the removed record."""
    if not isinstance(action_id, str):
        raise TypeError("action_id must be text.")
    actions = load_remediation_actions(actions_path)
    for index, action in enumerate(actions):
        if str(action["action_id"]).casefold() == action_id.casefold():
            deleted = actions.pop(index)
            save_remediation_actions(actions_path, actions)
            return deepcopy(deleted)
    raise ValueError(f"Action ID {action_id!r} does not exist.")
