"""Tests for the Phase 5 control-evidence register."""

import csv
from copy import deepcopy
from pathlib import Path
from shutil import copy2

import pytest

from control_register import load_controls
from evidence_register import (
    FIELDNAMES,
    add_evidence,
    delete_evidence,
    filter_evidence,
    get_evidence_by_id,
    get_evidence_for_control,
    get_expired_evidence,
    get_expiring_evidence,
    is_evidence_expired,
    load_evidence,
    save_evidence,
    search_evidence,
    update_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_evidence.csv"
CONTROLS = ROOT / "data" / "sample_controls.csv"


@pytest.fixture
def evidence():
    return load_evidence(SAMPLE)


@pytest.fixture
def writable_files(tmp_path):
    evidence_path = tmp_path / "evidence.csv"
    controls_path = tmp_path / "controls.csv"
    copy2(SAMPLE, evidence_path)
    copy2(CONTROLS, controls_path)
    return evidence_path, controls_path


def new_evidence(evidence_id="EVD-013"):
    return {
        "evidence_id": evidence_id,
        "control_id": "CTL-001",
        "evidence_name": "Access configuration review",
        "evidence_type": "Configuration",
        "description": "Fictional configuration evidence for testing.",
        "evidence_owner": "Test Evidence Owner",
        "collected_date": "2026-08-01",
        "review_date": "2026-08-02",
        "expiration_date": "2027-08-01",
        "status": "Current",
        "storage_reference": "grc://test/evidence-013",
        "reviewer": "Test Reviewer",
        "notes": "Temporary test record.",
    }


def test_sample_has_expected_ids_and_valid_controls(evidence):
    assert [item["evidence_id"] for item in evidence] == [f"EVD-{i:03d}" for i in range(1, 13)]
    controls = {item["control_id"] for item in load_controls(CONTROLS)}
    assert len(evidence) == 12
    assert all(item["control_id"] in controls for item in evidence)


def test_sample_dates_have_valid_relationships(evidence):
    assert all(item["review_date"] >= item["collected_date"] for item in evidence)
    assert all(item["expiration_date"] >= item["collected_date"] for item in evidence)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_evidence(ROOT / "data" / "missing.csv")


def test_missing_column_and_malformed_row_raise(tmp_path):
    missing = tmp_path / "missing.csv"
    missing.write_text("evidence_id,control_id\nEVD-001,CTL-001\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_evidence(missing)
    malformed = tmp_path / "malformed.csv"
    malformed.write_text(",".join(FIELDNAMES) + "\n" + ",".join(["x"] * 14) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_evidence(malformed)


def test_save_round_trip_header_and_input_unchanged(tmp_path, evidence):
    before = deepcopy(evidence)
    output = tmp_path / "roundtrip.csv"
    save_evidence(output, evidence)
    assert evidence == before
    assert load_evidence(output) == evidence
    with output.open(encoding="utf-8", newline="") as handle:
        assert next(csv.reader(handle)) == FIELDNAMES


def test_lookup_is_case_insensitive_and_returns_copy(evidence):
    found = get_evidence_by_id(evidence, "evd-001")
    assert found == evidence[0]
    found["notes"] = "changed"
    assert evidence[0]["notes"] != "changed"
    assert get_evidence_by_id(evidence, "EVD-999") is None


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("MFA configuration", "EVD-001"),
        ("showing multifactor", "EVD-001"),
        ("endpoint services", "EVD-003"),
        ("security operations", "EVD-002"),
        ("grc://evidence/cloud", "EVD-004"),
        ("replacement review", "EVD-006"),
    ],
)
def test_searches_requested_fields(evidence, query, expected):
    assert expected in [item["evidence_id"] for item in search_evidence(evidence, query)]


def test_empty_search_preserves_order_and_returns_copies(evidence):
    result = search_evidence(evidence, "  ")
    assert result == evidence
    result[0]["notes"] = "changed"
    assert evidence[0]["notes"] != "changed"


def test_filters_and_combines_criteria(evidence):
    assert [item["evidence_id"] for item in filter_evidence(evidence, control_id="ctl-001")] == ["EVD-001"]
    assert len(filter_evidence(evidence, evidence_type="report")) == 4
    assert len(filter_evidence(evidence, status="current")) == 6
    assert [item["evidence_id"] for item in filter_evidence(evidence, evidence_owner="identity and access manager")] == ["EVD-001", "EVD-006"]
    assert len(filter_evidence(evidence, reviewer="security operations manager")) == 2
    assert [item["evidence_id"] for item in filter_evidence(evidence, evidence_type="report", status="expiring soon")] == ["EVD-002", "EVD-011"]


def test_no_filters_and_control_retrieval_return_ordered_copies(evidence):
    all_records = filter_evidence(evidence)
    assert all_records == evidence
    assert get_evidence_for_control(evidence, "ctl-006")[0]["evidence_id"] == "EVD-006"
    all_records[0]["status"] = "Expired"
    assert evidence[0]["status"] == "Current"


def test_expiration_boundaries_and_collection(evidence):
    record = {"expiration_date": "2026-08-04"}
    assert not is_evidence_expired(record, "2026-08-04")
    assert is_evidence_expired(record, "2026-08-05")
    assert [item["evidence_id"] for item in get_expired_evidence(evidence, "2026-08-04")] == ["EVD-006", "EVD-009"]


def test_expiring_window_boundaries(evidence):
    result = get_expiring_evidence(evidence, days=21, as_of_date="2026-08-04")
    assert [item["evidence_id"] for item in result] == ["EVD-011"]
    assert get_expiring_evidence(evidence, days=0, as_of_date="2026-08-25") == [evidence[10]]
    assert get_expiring_evidence(evidence, days=20, as_of_date="2026-08-05") == [evidence[10]]


@pytest.mark.parametrize("days", [-1, 1.5, True, "30"])
def test_invalid_expiring_days_raise(evidence, days):
    with pytest.raises((TypeError, ValueError)):
        get_expiring_evidence(evidence, days=days, as_of_date="2026-08-04")


@pytest.mark.parametrize("as_of", ["2026-02-30", "08/04/2026", 20260804])
def test_invalid_comparison_dates_raise(as_of):
    with pytest.raises((TypeError, ValueError)):
        is_evidence_expired({"expiration_date": "2026-08-04"}, as_of)


def test_add_valid_record_and_preserve_caller(writable_files):
    evidence_path, controls_path = writable_files
    candidate = new_evidence()
    before = deepcopy(candidate)
    created = add_evidence(evidence_path, controls_path, candidate)
    assert candidate == before
    assert created == before
    assert load_evidence(evidence_path)[-1] == created


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("control_id", "CTL-999"),
        ("evidence_type", "Memo"),
        ("status", "Pending"),
        ("collected_date", "2026-02-30"),
        ("review_date", "2026-07-31"),
        ("expiration_date", "2026-07-31"),
    ],
)
def test_invalid_add_leaves_file_unchanged(writable_files, field, value):
    evidence_path, controls_path = writable_files
    original = evidence_path.read_bytes()
    candidate = new_evidence()
    candidate[field] = value
    with pytest.raises(ValueError):
        add_evidence(evidence_path, controls_path, candidate)
    assert evidence_path.read_bytes() == original


def test_duplicate_add_rejected_without_change(writable_files):
    evidence_path, controls_path = writable_files
    original = evidence_path.read_bytes()
    with pytest.raises(ValueError):
        add_evidence(evidence_path, controls_path, new_evidence("evd-001"))
    assert evidence_path.read_bytes() == original


def test_update_preserves_fields_position_and_caller(writable_files):
    evidence_path, controls_path = writable_files
    updates = {"status": "Under Review", "control_id": "CTL-002"}
    before = deepcopy(updates)
    updated = update_evidence(evidence_path, controls_path, "evd-003", updates)
    records = load_evidence(evidence_path)
    assert updates == before
    assert records[2] == updated
    assert updated["evidence_name"] == "EDR coverage report"


@pytest.mark.parametrize("updates", [{"evidence_id": "EVD-099"}, {"control_id": "CTL-999"}, {"status": "Pending"}])
def test_invalid_update_leaves_file_unchanged(writable_files, updates):
    evidence_path, controls_path = writable_files
    original = evidence_path.read_bytes()
    with pytest.raises(ValueError):
        update_evidence(evidence_path, controls_path, "EVD-003", updates)
    assert evidence_path.read_bytes() == original


def test_delete_preserves_order(writable_files):
    evidence_path, _ = writable_files
    deleted = delete_evidence(evidence_path, "evd-002")
    assert deleted["evidence_id"] == "EVD-002"
    assert [item["evidence_id"] for item in load_evidence(evidence_path)][:3] == ["EVD-001", "EVD-003", "EVD-004"]


def test_missing_update_and_delete_leave_file_unchanged(writable_files):
    evidence_path, controls_path = writable_files
    original = evidence_path.read_bytes()
    with pytest.raises(ValueError):
        update_evidence(evidence_path, controls_path, "EVD-999", {"status": "Current"})
    with pytest.raises(ValueError):
        delete_evidence(evidence_path, "EVD-999")
    assert evidence_path.read_bytes() == original
