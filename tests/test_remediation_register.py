"""Tests for the Phase 5 remediation-action register."""

import csv
from copy import deepcopy
from pathlib import Path
from shutil import copy2

import pytest

from control_register import load_controls
from remediation_register import (
    FIELDNAMES,
    add_remediation_action,
    delete_remediation_action,
    filter_actions,
    get_action_by_id,
    get_actions_for_control,
    get_actions_for_risk,
    get_overdue_actions,
    is_action_overdue,
    load_remediation_actions,
    save_remediation_actions,
    search_actions,
    update_remediation_action,
)
from risk_register import load_risks


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_remediation.csv"
RISKS = ROOT / "data" / "sample_risks.csv"
CONTROLS = ROOT / "data" / "sample_controls.csv"


@pytest.fixture
def actions():
    return load_remediation_actions(SAMPLE)


@pytest.fixture
def writable_files(tmp_path):
    action_path = tmp_path / "actions.csv"
    risk_path = tmp_path / "risks.csv"
    control_path = tmp_path / "controls.csv"
    copy2(SAMPLE, action_path)
    copy2(RISKS, risk_path)
    copy2(CONTROLS, control_path)
    return action_path, risk_path, control_path


def new_action(action_id="ACT-011"):
    return {
        "action_id": action_id,
        "action_title": "Review access exception",
        "description": "Review and resolve a fictional access exception.",
        "related_risk_id": "RSK-006",
        "related_control_id": "CTL-006",
        "action_owner": "Test Action Owner",
        "priority": "Medium",
        "status": "Open",
        "created_date": "2026-08-01",
        "due_date": "2026-09-01",
        "completion_pct": 10,
        "closure_date": "",
        "verification_notes": "Temporary test record.",
    }


def test_sample_ids_types_relationships_and_rules(actions):
    risks = {str(item["risk_id"]) for item in load_risks(RISKS)}
    controls = {str(item["control_id"]) for item in load_controls(CONTROLS)}
    assert [item["action_id"] for item in actions] == [f"ACT-{i:03d}" for i in range(1, 11)]
    assert all(isinstance(item["completion_pct"], int) for item in actions)
    assert all(not item["related_risk_id"] or item["related_risk_id"] in risks for item in actions)
    assert all(not item["related_control_id"] or item["related_control_id"] in controls for item in actions)
    assert all(item["related_risk_id"] or item["related_control_id"] for item in actions)
    assert all(item["status"] not in {"Completed", "Closed"} or item["completion_pct"] == 100 for item in actions)
    assert all(item["status"] != "Closed" or item["closure_date"] for item in actions)


def test_missing_file_and_missing_columns_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_remediation_actions(tmp_path / "missing.csv")
    bad = tmp_path / "bad.csv"
    bad.write_text("action_id,status\nACT-001,Open\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_remediation_actions(bad)


def test_save_round_trip_header_and_input_unchanged(tmp_path, actions):
    before = deepcopy(actions)
    output = tmp_path / "roundtrip.csv"
    save_remediation_actions(output, actions)
    assert actions == before
    assert load_remediation_actions(output) == actions
    with output.open(encoding="utf-8", newline="") as handle:
        assert next(csv.reader(handle)) == FIELDNAMES


def test_lookup_case_insensitive_missing_and_copy(actions):
    found = get_action_by_id(actions, "act-001")
    assert found == actions[0]
    found["status"] = "Closed"
    assert actions[0]["status"] == "In Progress"
    assert get_action_by_id(actions, "ACT-999") is None


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("ACT-001", "ACT-001"),
        ("phishing simulations", "ACT-001"),
        ("sensor", "ACT-002"),
        ("RSK-004", "ACT-003"),
        ("ctl-005", "ACT-006"),
        ("network services", "ACT-008"),
        ("Rescan results", "ACT-009"),
    ],
)
def test_searches_requested_fields(actions, query, expected):
    assert expected in [item["action_id"] for item in search_actions(actions, query)]


def test_empty_search_preserves_order_and_returns_copies(actions):
    result = search_actions(actions, " ")
    assert result == actions
    result[0]["description"] = "changed"
    assert actions[0]["description"] != "changed"


def test_filters_and_combines_criteria(actions):
    assert len(filter_actions(actions, priority="critical")) == 3
    assert [item["action_id"] for item in filter_actions(actions, status="closed")] == ["ACT-005"]
    assert [item["action_id"] for item in filter_actions(actions, action_owner="cloud services manager")] == ["ACT-003"]
    assert [item["action_id"] for item in filter_actions(actions, related_risk_id="rsk-001")] == ["ACT-001"]
    assert [item["action_id"] for item in filter_actions(actions, related_control_id="ctl-009")] == ["ACT-008"]
    assert [item["action_id"] for item in filter_actions(actions, priority="high", status="open")] == ["ACT-008"]


def test_no_filters_and_relationship_retrieval_return_copies(actions):
    result = filter_actions(actions)
    assert result == actions
    assert get_actions_for_risk(actions, "rsk-006")[0]["action_id"] == "ACT-010"
    assert get_actions_for_control(actions, "ctl-003")[0]["action_id"] == "ACT-002"
    result[0]["priority"] = "Low"
    assert actions[0]["priority"] == "High"


def test_overdue_status_and_date_boundaries(actions):
    assert is_action_overdue(actions[0], "2026-08-04")
    assert not is_action_overdue(actions[4], "2026-08-04")
    assert not is_action_overdue(actions[6], "2026-08-04")
    assert not is_action_overdue(actions[0], "2026-07-31")
    assert [item["action_id"] for item in get_overdue_actions(actions, "2026-08-04")] == ["ACT-001", "ACT-003", "ACT-004", "ACT-009"]


@pytest.mark.parametrize("as_of", ["2026-02-30", "08/04/2026", 20260804])
def test_invalid_overdue_date_raises(actions, as_of):
    with pytest.raises((TypeError, ValueError)):
        is_action_overdue(actions[0], as_of)


def test_add_valid_action_and_preserve_caller(writable_files):
    action_path, risk_path, control_path = writable_files
    candidate = new_action()
    before = deepcopy(candidate)
    created = add_remediation_action(action_path, risk_path, control_path, candidate)
    assert candidate == before
    assert created == before
    assert load_remediation_actions(action_path)[-1] == created


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("related_risk_id", "RSK-999"),
        ("related_control_id", "CTL-999"),
        ("due_date", "2026-07-31"),
        ("created_date", "2026-02-30"),
        ("priority", "Urgent"),
        ("status", "Pending"),
        ("completion_pct", 101),
        ("completion_pct", True),
    ],
)
def test_invalid_add_leaves_file_unchanged(writable_files, field, value):
    action_path, risk_path, control_path = writable_files
    original = action_path.read_bytes()
    candidate = new_action()
    candidate[field] = value
    with pytest.raises((TypeError, ValueError)):
        add_remediation_action(action_path, risk_path, control_path, candidate)
    assert action_path.read_bytes() == original


def test_add_requires_relationship_and_unique_id(writable_files):
    action_path, risk_path, control_path = writable_files
    original = action_path.read_bytes()
    no_link = new_action()
    no_link["related_risk_id"] = no_link["related_control_id"] = ""
    with pytest.raises(ValueError):
        add_remediation_action(action_path, risk_path, control_path, no_link)
    with pytest.raises(ValueError):
        add_remediation_action(action_path, risk_path, control_path, new_action("act-001"))
    assert action_path.read_bytes() == original


@pytest.mark.parametrize(
    "updates",
    [
        {"status": "Completed", "completion_pct": 90},
        {"status": "Open", "completion_pct": 100},
        {"status": "Closed", "completion_pct": 100, "closure_date": ""},
    ],
)
def test_status_completion_violations_are_rejected(writable_files, updates):
    action_path, risk_path, control_path = writable_files
    original = action_path.read_bytes()
    with pytest.raises(ValueError):
        update_remediation_action(action_path, risk_path, control_path, "ACT-002", updates)
    assert action_path.read_bytes() == original


def test_update_preserves_position_fields_and_caller(writable_files):
    action_path, risk_path, control_path = writable_files
    updates = {"related_risk_id": "", "related_control_id": "CTL-001", "priority": "Low"}
    before = deepcopy(updates)
    updated = update_remediation_action(action_path, risk_path, control_path, "act-003", updates)
    actions = load_remediation_actions(action_path)
    assert updates == before
    assert actions[2] == updated
    assert updated["action_title"] == "Correct cloud misconfigurations"


def test_valid_close_requires_and_records_completion(writable_files):
    action_path, risk_path, control_path = writable_files
    updated = update_remediation_action(
        action_path, risk_path, control_path, "ACT-002",
        {"status": "Closed", "completion_pct": 100, "closure_date": "2026-08-03"},
    )
    assert updated["status"] == "Closed"
    assert updated["closure_date"] == "2026-08-03"


@pytest.mark.parametrize("updates", [{"action_id": "ACT-099"}, {"related_control_id": "CTL-999"}])
def test_invalid_update_leaves_file_unchanged(writable_files, updates):
    action_path, risk_path, control_path = writable_files
    original = action_path.read_bytes()
    with pytest.raises(ValueError):
        update_remediation_action(action_path, risk_path, control_path, "ACT-003", updates)
    assert action_path.read_bytes() == original


def test_delete_preserves_order(writable_files):
    action_path, _, _ = writable_files
    deleted = delete_remediation_action(action_path, "act-002")
    assert deleted["action_id"] == "ACT-002"
    assert [item["action_id"] for item in load_remediation_actions(action_path)][:3] == ["ACT-001", "ACT-003", "ACT-004"]


def test_missing_update_and_delete_leave_file_unchanged(writable_files):
    action_path, risk_path, control_path = writable_files
    original = action_path.read_bytes()
    with pytest.raises(ValueError):
        update_remediation_action(action_path, risk_path, control_path, "ACT-999", {"priority": "Low"})
    with pytest.raises(ValueError):
        delete_remediation_action(action_path, "ACT-999")
    assert action_path.read_bytes() == original
