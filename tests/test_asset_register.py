"""Tests for the Phase 4 CSV-backed asset inventory."""

import csv
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from asset_register import (
    FIELDNAMES,
    add_asset,
    delete_asset,
    filter_assets,
    get_asset_by_id,
    load_assets,
    save_assets,
    search_assets,
    update_asset,
)


PROJECT_ROOT = Path(__file__).parents[1]
SAMPLE_ASSETS = PROJECT_ROOT / "data" / "sample_assets.csv"
SAMPLE_RISKS = PROJECT_ROOT / "data" / "sample_risks.csv"


@pytest.fixture
def temporary_registers(tmp_path):
    """Copy protected samples before any write operation."""
    assets_path = tmp_path / "assets.csv"
    risks_path = tmp_path / "risks.csv"
    shutil.copyfile(SAMPLE_ASSETS, assets_path)
    shutil.copyfile(SAMPLE_RISKS, risks_path)
    return assets_path, risks_path


@pytest.fixture
def valid_asset():
    return {
        "asset_id": "AST-009",
        "asset_name": "Security Training Platform",
        "asset_type": "Software as a Service",
        "asset_owner": "Awareness Program Manager",
        "department": "Information Security",
        "data_classification": "Internal",
        "business_criticality": "Medium",
        "location": "Fictional hosted service",
        "description": "Delivers fictional workforce security training.",
    }


def test_loads_eight_string_assets_in_order():
    assets = load_assets(SAMPLE_ASSETS)
    assert [asset["asset_id"] for asset in assets] == [f"AST-{number:03d}" for number in range(1, 9)]
    assert all(isinstance(value, str) for asset in assets for value in asset.values())


def test_load_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_assets(tmp_path / "missing.csv")


def test_load_missing_column_and_malformed_row_raise_value_error(tmp_path):
    missing = tmp_path / "missing-column.csv"
    missing.write_text("asset_id,asset_name\nAST-001,Example\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        load_assets(missing)
    malformed = tmp_path / "malformed.csv"
    malformed.write_text(",".join(FIELDNAMES) + "\nAST-001,Too,Few\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid asset data"):
        load_assets(malformed)


def test_save_round_trip_header_and_input_immutability(tmp_path):
    assets = load_assets(SAMPLE_ASSETS)
    original = deepcopy(assets)
    path = tmp_path / "round-trip.csv"
    save_assets(path, assets)
    assert load_assets(path) == assets
    assert assets == original
    with path.open(encoding="utf-8", newline="") as csv_file:
        assert next(csv.reader(csv_file)) == FIELDNAMES


def test_lookup_is_case_insensitive_returns_copy_and_handles_missing():
    assets = load_assets(SAMPLE_ASSETS)
    found = get_asset_by_id(assets, "ast-003")
    assert found == assets[2] and found is not assets[2]
    assert get_asset_by_id(assets, "AST-999") is None


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("customer records", "AST-001"),
        ("identity and access manager", "AST-008"),
        ("digital banking", "AST-002"),
        ("recoverable copies", "AST-007"),
    ],
)
def test_searches_requested_asset_fields(query, expected):
    assert expected in [asset["asset_id"] for asset in search_assets(load_assets(SAMPLE_ASSETS), query.upper())]


def test_empty_search_and_no_filters_return_ordered_copies():
    assets = load_assets(SAMPLE_ASSETS)
    for results in (search_assets(assets, "  "), filter_assets(assets)):
        assert results == assets
        assert all(result is not original for result, original in zip(results, assets))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("asset_type", "cloud application"),
        ("department", "information security"),
        ("data_classification", "confidential"),
        ("business_criticality", "high"),
        ("location", "microsoft 365 cloud"),
    ],
)
def test_each_asset_filter_is_case_insensitive(field, value):
    results = filter_assets(load_assets(SAMPLE_ASSETS), **{field: value})
    assert results and all(asset[field].casefold() == value for asset in results)


def test_multiple_asset_filters_preserve_order():
    results = filter_assets(
        load_assets(SAMPLE_ASSETS), department="information technology", business_criticality="critical"
    )
    assert [asset["asset_id"] for asset in results] == ["AST-001", "AST-006", "AST-007"]


def test_add_valid_asset_appends_without_mutating_caller(temporary_registers, valid_asset):
    assets_path, _ = temporary_registers
    original = deepcopy(valid_asset)
    created = add_asset(assets_path, valid_asset)
    assert load_assets(assets_path)[-1] == created
    assert valid_asset == original


@pytest.mark.parametrize(
    ("field", "bad_value", "error"),
    [
        ("asset_id", "AST-001", "already exists"),
        ("asset_id", "A-009", "exactly three digits"),
        ("asset_name", "  ", "cannot be empty"),
        ("data_classification", "Secret", "data_classification"),
        ("business_criticality", "Urgent", "business_criticality"),
    ],
)
def test_failed_additions_leave_file_unchanged(temporary_registers, valid_asset, field, bad_value, error):
    assets_path, _ = temporary_registers
    before = assets_path.read_bytes()
    valid_asset[field] = bad_value
    with pytest.raises(ValueError, match=error):
        add_asset(assets_path, valid_asset)
    assert assets_path.read_bytes() == before


def test_add_requires_dictionary(temporary_registers):
    assets_path, _ = temporary_registers
    with pytest.raises(TypeError):
        add_asset(assets_path, [])


def test_update_preserves_fields_position_and_caller(temporary_registers):
    assets_path, _ = temporary_registers
    before = load_assets(assets_path)
    updates = {"description": "  Updated fictional description.  ", "business_criticality": "High"}
    original = deepcopy(updates)
    updated = update_asset(assets_path, "ast-006", updates)
    after = load_assets(assets_path)
    assert updated["description"] == "Updated fictional description."
    assert updated["asset_name"] == before[5]["asset_name"]
    assert after[5] == updated
    assert [item["asset_id"] for item in after] == [item["asset_id"] for item in before]
    assert updates == original


@pytest.mark.parametrize(
    ("asset_id", "updates", "message"),
    [
        ("AST-999", {"department": "Operations"}, "does not exist"),
        ("AST-006", {"asset_id": "AST-099"}, "cannot be changed"),
        ("AST-006", {"location": " "}, "cannot be empty"),
    ],
)
def test_failed_updates_leave_file_unchanged(temporary_registers, asset_id, updates, message):
    assets_path, _ = temporary_registers
    before = assets_path.read_bytes()
    with pytest.raises(ValueError, match=message):
        update_asset(assets_path, asset_id, updates)
    assert assets_path.read_bytes() == before


def test_delete_unreferenced_asset_returns_copy_and_preserves_order(temporary_registers, valid_asset):
    assets_path, risks_path = temporary_registers
    add_asset(assets_path, valid_asset)
    deleted = delete_asset(assets_path, risks_path, "ast-009")
    assert deleted["asset_id"] == "AST-009"
    assert [item["asset_id"] for item in load_assets(assets_path)] == [f"AST-{number:03d}" for number in range(1, 9)]


def test_referenced_and_missing_asset_deletions_do_not_write(temporary_registers):
    assets_path, risks_path = temporary_registers
    for asset_id, message in (("AST-004", "RSK-002"), ("AST-999", "does not exist")):
        before = assets_path.read_bytes()
        with pytest.raises(ValueError, match=message):
            delete_asset(assets_path, risks_path, asset_id)
        assert assets_path.read_bytes() == before


def test_original_samples_remain_unchanged_after_temporary_writes(temporary_registers, valid_asset):
    original_assets = SAMPLE_ASSETS.read_bytes()
    original_risks = SAMPLE_RISKS.read_bytes()
    assets_path, _ = temporary_registers
    add_asset(assets_path, valid_asset)
    assert SAMPLE_ASSETS.read_bytes() == original_assets
    assert SAMPLE_RISKS.read_bytes() == original_risks
