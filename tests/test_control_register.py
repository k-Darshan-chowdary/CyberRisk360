"""Tests for the Phase 4 CSV-backed security-control register."""

import csv
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from asset_register import load_assets
from control_register import (
    FIELDNAMES,
    add_control,
    delete_control,
    filter_controls,
    get_control_by_id,
    get_controls_for_asset,
    get_controls_for_risk,
    load_controls,
    save_controls,
    search_controls,
    update_control,
)
from risk_register import load_risks


PROJECT_ROOT = Path(__file__).parents[1]
SAMPLE_CONTROLS = PROJECT_ROOT / "data" / "sample_controls.csv"
SAMPLE_ASSETS = PROJECT_ROOT / "data" / "sample_assets.csv"
SAMPLE_RISKS = PROJECT_ROOT / "data" / "sample_risks.csv"


@pytest.fixture
def temporary_registers(tmp_path):
    paths = tuple(tmp_path / name for name in ("controls.csv", "assets.csv", "risks.csv"))
    for source, destination in zip((SAMPLE_CONTROLS, SAMPLE_ASSETS, SAMPLE_RISKS), paths):
        shutil.copyfile(source, destination)
    return paths


@pytest.fixture
def valid_control():
    return {
        "control_id": "CTL-013",
        "control_name": "Removable media restrictions",
        "control_description": "Limits unapproved removable media on managed endpoints.",
        "control_type": "Preventive",
        "nist_csf_function": "Protect",
        "implementation_status": "Planned",
        "control_owner": "Endpoint Services Manager",
        "effectiveness_pct": 35,
        "mapped_asset_ids": ["AST-004"],
        "mapped_risk_ids": ["RSK-002"],
        "review_date": "2027-02-28",
        "evidence_reference": "Implementation plan 2027",
        "notes": "Fictional planning record.",
    }


def test_sample_has_twelve_typed_controls_and_all_functions():
    controls = load_controls(SAMPLE_CONTROLS)
    assert [item["control_id"] for item in controls] == [f"CTL-{number:03d}" for number in range(1, 13)]
    assert all(isinstance(item["effectiveness_pct"], float) for item in controls)
    assert all(isinstance(item["mapped_asset_ids"], list) and isinstance(item["mapped_risk_ids"], list) for item in controls)
    assert {item["nist_csf_function"] for item in controls} == {"Govern", "Identify", "Protect", "Detect", "Respond", "Recover"}


def test_every_sample_mapping_exists():
    asset_ids = {item["asset_id"] for item in load_assets(SAMPLE_ASSETS)}
    risk_ids = {item["risk_id"] for item in load_risks(SAMPLE_RISKS)}
    for control in load_controls(SAMPLE_CONTROLS):
        assert set(control["mapped_asset_ids"]) <= asset_ids
        assert set(control["mapped_risk_ids"]) <= risk_ids


def test_load_missing_file_and_columns_raise_expected_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_controls(tmp_path / "missing.csv")
    path = tmp_path / "incomplete.csv"
    path.write_text("control_id,control_name\nCTL-001,Example\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_controls(path)


def test_save_round_trip_format_and_deep_input_immutability(tmp_path):
    controls = load_controls(SAMPLE_CONTROLS)
    original = deepcopy(controls)
    path = tmp_path / "saved.csv"
    save_controls(path, controls)
    assert load_controls(path) == controls
    assert controls == original
    with path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.reader(csv_file))
    assert rows[0] == FIELDNAMES
    assert all(len(row[FIELDNAMES.index("effectiveness_pct")].partition(".")[2]) == 2 for row in rows[1:])
    assert ";" in rows[1][FIELDNAMES.index("mapped_asset_ids")]


def test_lookup_is_case_insensitive_deep_and_handles_missing():
    controls = load_controls(SAMPLE_CONTROLS)
    found = get_control_by_id(controls, "ctl-001")
    assert found == controls[0] and found is not controls[0]
    found["mapped_asset_ids"].append("AST-999")
    assert "AST-999" not in controls[0]["mapped_asset_ids"]
    assert get_control_by_id(controls, "CTL-999") is None


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("multifactor", "CTL-001"),
        ("cloud services manager", "CTL-004"),
        ("rapid investigation", "CTL-003"),
        ("steering minutes", "CTL-012"),
        ("legacy rule", "CTL-009"),
        ("ast-007", "CTL-005"),
        ("rsk-009", "CTL-007"),
    ],
)
def test_searches_all_requested_control_fields(query, expected):
    assert expected in [item["control_id"] for item in search_controls(load_controls(SAMPLE_CONTROLS), query.upper())]


def test_empty_search_and_no_filters_return_ordered_deep_copies():
    controls = load_controls(SAMPLE_CONTROLS)
    for results in (search_controls(controls, " "), filter_controls(controls)):
        assert results == controls
        results[0]["mapped_asset_ids"].append("AST-999")
        assert "AST-999" not in controls[0]["mapped_asset_ids"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("control_type", "recovery"),
        ("nist_csf_function", "detect"),
        ("implementation_status", "planned"),
        ("control_owner", "network services manager"),
    ],
)
def test_each_control_filter_is_case_insensitive(field, value):
    results = filter_controls(load_controls(SAMPLE_CONTROLS), **{field: value})
    assert results and all(item[field].casefold() == value for item in results)


def test_multiple_filters_and_mapping_helpers_preserve_order_and_deep_copy():
    controls = load_controls(SAMPLE_CONTROLS)
    assert [item["control_id"] for item in filter_controls(controls, control_type="detective", nist_csf_function="identify")] == ["CTL-004", "CTL-011"]
    asset_matches = get_controls_for_asset(controls, "ast-002")
    risk_matches = get_controls_for_risk(controls, "rsk-003")
    assert [item["control_id"] for item in asset_matches] == ["CTL-001", "CTL-004", "CTL-007", "CTL-011"]
    assert [item["control_id"] for item in risk_matches] == ["CTL-004", "CTL-005", "CTL-009", "CTL-011"]
    asset_matches[0]["mapped_asset_ids"].clear()
    assert controls[0]["mapped_asset_ids"]


def test_add_valid_control_appends_and_does_not_mutate_caller(temporary_registers, valid_control):
    controls_path, assets_path, risks_path = temporary_registers
    original = deepcopy(valid_control)
    created = add_control(controls_path, assets_path, risks_path, valid_control)
    assert load_controls(controls_path)[-1] == created
    assert valid_control == original


@pytest.mark.parametrize(
    ("field", "bad_value", "error"),
    [
        ("control_id", "CTL-001", "already exists"),
        ("control_id", "CONTROL-13", "exactly three digits"),
        ("control_type", "Administrative", "control_type"),
        ("nist_csf_function", "Prevent", "nist_csf_function"),
        ("implementation_status", "Pending", "implementation_status"),
        ("effectiveness_pct", 101, "between 0 and 100"),
        ("review_date", "2027-02-30", "real date"),
        ("mapped_asset_ids", ["AST-999"], "Unknown mapped asset"),
        ("mapped_risk_ids", ["RSK-999"], "Unknown mapped risk"),
        ("mapped_asset_ids", ["AST-004", "ast-004"], "duplicate ID"),
    ],
)
def test_failed_additions_leave_file_unchanged(temporary_registers, valid_control, field, bad_value, error):
    controls_path, assets_path, risks_path = temporary_registers
    before = controls_path.read_bytes()
    valid_control[field] = bad_value
    with pytest.raises(ValueError, match=error):
        add_control(controls_path, assets_path, risks_path, valid_control)
    assert controls_path.read_bytes() == before


def test_add_rejects_boolean_effectiveness_and_no_mappings(temporary_registers, valid_control):
    controls_path, assets_path, risks_path = temporary_registers
    valid_control["effectiveness_pct"] = True
    with pytest.raises(TypeError, match="effectiveness_pct"):
        add_control(controls_path, assets_path, risks_path, valid_control)
    valid_control["effectiveness_pct"] = 50
    valid_control["mapped_asset_ids"] = []
    valid_control["mapped_risk_ids"] = []
    with pytest.raises(ValueError, match="at least one"):
        add_control(controls_path, assets_path, risks_path, valid_control)


def test_update_preserves_fields_position_and_nested_caller_data(temporary_registers):
    controls_path, assets_path, risks_path = temporary_registers
    before = load_controls(controls_path)
    updates = {"effectiveness_pct": 88.5, "mapped_asset_ids": [" AST-003 ", "AST-008"]}
    original = deepcopy(updates)
    updated = update_control(controls_path, assets_path, risks_path, "ctl-002", updates)
    after = load_controls(controls_path)
    assert updated["control_name"] == before[1]["control_name"]
    assert updated["mapped_asset_ids"] == ["AST-003", "AST-008"]
    assert after[1] == updated
    assert [item["control_id"] for item in after] == [item["control_id"] for item in before]
    assert updates == original


@pytest.mark.parametrize(
    ("control_id", "updates", "message"),
    [
        ("CTL-999", {"notes": "Missing"}, "does not exist"),
        ("CTL-002", {"control_id": "CTL-099"}, "cannot be changed"),
        ("CTL-002", {"mapped_risk_ids": ["RSK-999"]}, "Unknown mapped risk"),
    ],
)
def test_failed_updates_leave_file_unchanged(temporary_registers, control_id, updates, message):
    controls_path, assets_path, risks_path = temporary_registers
    before = controls_path.read_bytes()
    original = deepcopy(updates)
    with pytest.raises(ValueError, match=message):
        update_control(controls_path, assets_path, risks_path, control_id, updates)
    assert controls_path.read_bytes() == before
    assert updates == original


def test_delete_returns_deep_copy_and_preserves_remaining_order(temporary_registers):
    controls_path, _, _ = temporary_registers
    before = load_controls(controls_path)
    deleted = delete_control(controls_path, "ctl-006")
    after = load_controls(controls_path)
    assert deleted == before[5]
    assert [item["control_id"] for item in after] == [item["control_id"] for item in before if item["control_id"] != "CTL-006"]


def test_failed_delete_does_not_write(temporary_registers):
    controls_path, _, _ = temporary_registers
    before = controls_path.read_bytes()
    with pytest.raises(ValueError, match="does not exist"):
        delete_control(controls_path, "CTL-999")
    assert controls_path.read_bytes() == before


def test_original_samples_remain_unchanged_after_temporary_writes(temporary_registers, valid_control):
    originals = [path.read_bytes() for path in (SAMPLE_CONTROLS, SAMPLE_ASSETS, SAMPLE_RISKS)]
    controls_path, assets_path, risks_path = temporary_registers
    add_control(controls_path, assets_path, risks_path, valid_control)
    assert [path.read_bytes() for path in (SAMPLE_CONTROLS, SAMPLE_ASSETS, SAMPLE_RISKS)] == originals
