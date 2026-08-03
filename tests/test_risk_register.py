"""Tests for the Phase 3 CSV-backed risk register."""

import csv
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from risk_register import (
    FIELDNAMES,
    add_risk,
    delete_risk,
    filter_risks,
    get_risk_by_id,
    load_risks,
    save_risks,
    search_risks,
    update_risk,
)


PROJECT_ROOT = Path(__file__).parents[1]
SAMPLE_RISKS = PROJECT_ROOT / "data" / "sample_risks.csv"
SAMPLE_ASSETS = PROJECT_ROOT / "data" / "sample_assets.csv"


@pytest.fixture
def temporary_csv_files(tmp_path):
    """Copy both samples so write tests cannot change project data."""
    risks_path = tmp_path / "risks.csv"
    assets_path = tmp_path / "assets.csv"
    shutil.copyfile(SAMPLE_RISKS, risks_path)
    shutil.copyfile(SAMPLE_ASSETS, assets_path)
    return risks_path, assets_path


@pytest.fixture
def valid_risk_data():
    return {
        "risk_id": "RSK-011",
        "risk_title": "Unsupported software remains in service",
        "threat": "External attacker",
        "vulnerability": "Security fixes are no longer available",
        "affected_asset_id": "AST-006",
        "likelihood": 4,
        "impact": 3,
        "existing_controls": "Network segmentation and monitoring",
        "control_effectiveness_pct": 25,
        "risk_owner": "Network Services Manager",
        "treatment": "Mitigate",
        "status": "Open",
        "target_date": "2027-02-28",
        "nist_csf_function": "Identify",
    }


def test_loads_ten_typed_risks_in_original_order():
    risks = load_risks(SAMPLE_RISKS)
    assert len(risks) == 10
    assert [risk["risk_id"] for risk in risks] == [f"RSK-{number:03d}" for number in range(1, 11)]
    assert isinstance(risks[0]["likelihood"], int)
    assert isinstance(risks[0]["impact"], int)
    assert isinstance(risks[0]["inherent_score"], int)
    assert isinstance(risks[0]["control_effectiveness_pct"], float)
    assert isinstance(risks[0]["residual_score"], float)


def test_load_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_risks(tmp_path / "missing.csv")


def test_load_missing_required_column_raises_value_error(tmp_path):
    path = tmp_path / "incomplete.csv"
    path.write_text("risk_id,risk_title\nRSK-001,Example\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_risks(path)


def test_get_existing_risk_is_case_insensitive_and_returns_copy():
    risks = load_risks(SAMPLE_RISKS)
    found = get_risk_by_id(risks, "rsk-003")
    assert found["risk_title"] == "Customer data breach"
    assert found is not risks[2]


def test_get_missing_risk_returns_none():
    assert get_risk_by_id(load_risks(SAMPLE_RISKS), "RSK-999") is None


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("customer data breach", "RSK-003"),
        ("credential thief", "RSK-006"),
        ("digital banking manager", "RSK-009"),
    ],
)
def test_searches_requested_text_fields(query, expected_id):
    matches = search_risks(load_risks(SAMPLE_RISKS), query.upper())
    assert expected_id in [risk["risk_id"] for risk in matches]


def test_empty_search_returns_copies_of_all_risks_in_order():
    risks = load_risks(SAMPLE_RISKS)
    matches = search_risks(risks, "   ")
    assert [risk["risk_id"] for risk in matches] == [risk["risk_id"] for risk in risks]
    assert all(match is not original for match, original in zip(matches, risks))


def test_search_results_preserve_original_order():
    matches = search_risks(load_risks(SAMPLE_RISKS), "manager")
    ids = [risk["risk_id"] for risk in matches]
    assert ids == sorted(ids)


@pytest.mark.parametrize(
    ("filter_name", "value"),
    [
        ("status", "open"),
        ("inherent_rating", "high"),
        ("residual_rating", "medium"),
        ("treatment", "transfer"),
        ("nist_csf_function", "protect"),
    ],
)
def test_filters_are_case_insensitive(filter_name, value):
    matches = filter_risks(load_risks(SAMPLE_RISKS), **{filter_name: value})
    assert matches
    assert all(risk[filter_name].casefold() == value for risk in matches)


def test_multiple_filters_must_all_match():
    matches = filter_risks(
        load_risks(SAMPLE_RISKS), status="monitoring", treatment="transfer"
    )
    assert [risk["risk_id"] for risk in matches] == ["RSK-005", "RSK-009"]


def test_no_filters_return_copies_of_all_risks():
    risks = load_risks(SAMPLE_RISKS)
    matches = filter_risks(risks)
    assert matches == risks
    assert matches[0] is not risks[0]


def test_add_valid_risk_appends_and_calculates_fields(
    temporary_csv_files, valid_risk_data
):
    risks_path, assets_path = temporary_csv_files
    created = add_risk(risks_path, assets_path, valid_risk_data)
    saved = load_risks(risks_path)
    assert len(saved) == 11
    assert saved[-1] == created
    assert created["inherent_score"] == 12
    assert created["inherent_rating"] == "Medium"
    assert created["residual_score"] == 9.0
    assert created["residual_rating"] == "Medium"


def test_add_does_not_modify_caller_dictionary(temporary_csv_files, valid_risk_data):
    risks_path, assets_path = temporary_csv_files
    original = deepcopy(valid_risk_data)
    add_risk(risks_path, assets_path, valid_risk_data)
    assert valid_risk_data == original


@pytest.mark.parametrize(
    ("field", "bad_value", "message"),
    [
        ("risk_id", "RSK-001", "already exists"),
        ("affected_asset_id", "AST-999", "does not exist"),
        ("target_date", "2027-02-30", "real date"),
        ("treatment", "Reduce", "treatment"),
        ("status", "Pending", "status"),
        ("nist_csf_function", "Plan", "nist_csf_function"),
    ],
)
def test_failed_additions_leave_file_unchanged(
    temporary_csv_files, valid_risk_data, field, bad_value, message
):
    risks_path, assets_path = temporary_csv_files
    before = risks_path.read_bytes()
    valid_risk_data[field] = bad_value
    with pytest.raises(ValueError, match=message):
        add_risk(risks_path, assets_path, valid_risk_data)
    assert risks_path.read_bytes() == before


def test_add_rejects_boolean_numeric_fields(temporary_csv_files, valid_risk_data):
    risks_path, assets_path = temporary_csv_files
    valid_risk_data["likelihood"] = True
    with pytest.raises(TypeError, match="likelihood"):
        add_risk(risks_path, assets_path, valid_risk_data)


def test_update_recalculates_and_preserves_fields_and_position(temporary_csv_files):
    risks_path, assets_path = temporary_csv_files
    before = load_risks(risks_path)
    updated = update_risk(
        risks_path,
        assets_path,
        "rsk-003",
        {"likelihood": 4, "impact": 4, "control_effectiveness_pct": 25},
    )
    after = load_risks(risks_path)
    assert updated["inherent_score"] == 16
    assert updated["inherent_rating"] == "High"
    assert updated["residual_score"] == 12.0
    assert updated["residual_rating"] == "Medium"
    assert updated["risk_title"] == before[2]["risk_title"]
    assert after[2] == updated
    assert [risk["risk_id"] for risk in after] == [risk["risk_id"] for risk in before]


@pytest.mark.parametrize(
    ("updates", "expected_inherent", "expected_residual"),
    [
        ({"likelihood": 5}, 25, 12.5),
        ({"impact": 4}, 12, 6.0),
        ({"control_effectiveness_pct": 20}, 15, 12.0),
    ],
)
def test_update_recalculates_relevant_derived_values(
    temporary_csv_files, updates, expected_inherent, expected_residual
):
    risks_path, assets_path = temporary_csv_files
    updated = update_risk(risks_path, assets_path, "RSK-003", updates)
    assert updated["inherent_score"] == expected_inherent
    assert updated["residual_score"] == expected_residual


def test_update_does_not_modify_caller_dictionary(temporary_csv_files):
    risks_path, assets_path = temporary_csv_files
    updates = {"status": "Monitoring"}
    original = deepcopy(updates)
    update_risk(risks_path, assets_path, "RSK-003", updates)
    assert updates == original


@pytest.mark.parametrize(
    ("risk_id", "updates", "message"),
    [
        ("RSK-999", {"status": "Closed"}, "does not exist"),
        ("RSK-003", {"risk_id": "RSK-099"}, "cannot be changed"),
        ("RSK-003", {"target_date": "not-a-date"}, "real date"),
        ("RSK-003", {"affected_asset_id": "AST-999"}, "does not exist"),
    ],
)
def test_failed_updates_leave_file_unchanged(
    temporary_csv_files, risk_id, updates, message
):
    risks_path, assets_path = temporary_csv_files
    before = risks_path.read_bytes()
    with pytest.raises(ValueError, match=message):
        update_risk(risks_path, assets_path, risk_id, updates)
    assert risks_path.read_bytes() == before


def test_delete_returns_risk_and_preserves_remaining_order(temporary_csv_files):
    risks_path, _ = temporary_csv_files
    before = load_risks(risks_path)
    deleted = delete_risk(risks_path, "rsk-004")
    after = load_risks(risks_path)
    assert deleted == before[3]
    assert len(after) == 9
    assert [risk["risk_id"] for risk in after] == [
        risk["risk_id"] for risk in before if risk["risk_id"] != "RSK-004"
    ]


def test_failed_delete_leaves_file_unchanged(temporary_csv_files):
    risks_path, _ = temporary_csv_files
    before = risks_path.read_bytes()
    with pytest.raises(ValueError, match="does not exist"):
        delete_risk(risks_path, "RSK-999")
    assert risks_path.read_bytes() == before


def test_save_reload_round_trip_and_does_not_modify_input(tmp_path):
    risks = load_risks(SAMPLE_RISKS)
    original = deepcopy(risks)
    path = tmp_path / "round-trip.csv"
    save_risks(path, risks)
    assert load_risks(path) == risks
    assert risks == original


def test_save_uses_exact_header_and_two_decimal_residual_scores(tmp_path):
    risks = load_risks(SAMPLE_RISKS)
    path = tmp_path / "saved.csv"
    save_risks(path, risks)
    with path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.reader(csv_file))
    assert rows[0] == FIELDNAMES
    residual_index = FIELDNAMES.index("residual_score")
    assert all(row[residual_index].partition(".")[2].__len__() == 2 for row in rows[1:])


def test_write_tests_did_not_change_original_sample_files(temporary_csv_files):
    risks_before = SAMPLE_RISKS.read_bytes()
    assets_before = SAMPLE_ASSETS.read_bytes()
    risks_path, assets_path = temporary_csv_files
    delete_risk(risks_path, "RSK-010")
    assert SAMPLE_RISKS.read_bytes() == risks_before
    assert SAMPLE_ASSETS.read_bytes() == assets_before
