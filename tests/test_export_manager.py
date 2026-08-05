"""Tests for Phase 7 in-memory reporting exports."""

from __future__ import annotations

import csv
from copy import deepcopy
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from asset_register import FIELDNAMES as ASSET_FIELDS, load_assets
from control_register import FIELDNAMES as CONTROL_FIELDS, load_controls
from evidence_register import FIELDNAMES as EVIDENCE_FIELDS, load_evidence
from export_manager import (
    PACKAGE_FILES, assets_to_csv_bytes, build_report_package, controls_to_csv_bytes,
    evidence_to_csv_bytes, generate_management_report_markdown,
    remediation_to_csv_bytes, risks_to_csv_bytes,
)
from remediation_register import FIELDNAMES as REMEDIATION_FIELDS, load_remediation_actions
from risk_register import FIELDNAMES as RISK_FIELDS, load_risks


DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture()
def project_data():
    return {
        "assets": load_assets(DATA / "sample_assets.csv"),
        "risks": load_risks(DATA / "sample_risks.csv"),
        "controls": load_controls(DATA / "sample_controls.csv"),
        "evidence": load_evidence(DATA / "sample_evidence.csv"),
        "remediation": load_remediation_actions(DATA / "sample_remediation.csv"),
    }


def _rows(payload: bytes):
    return list(csv.DictReader(StringIO(payload.decode("utf-8"))))


def test_asset_csv_header_rows_order_decode_and_input_unchanged(project_data):
    records = project_data["assets"]
    before = deepcopy(records)
    payload = assets_to_csv_bytes(records)
    rows = _rows(payload)
    assert list(rows[0]) == ASSET_FIELDS
    assert len(rows) == 8
    assert [row["asset_id"] for row in rows] == [item["asset_id"] for item in records]
    assert records == before


def test_risk_csv_header_rows_numeric_values_and_input_unchanged(project_data):
    records = project_data["risks"]
    before = deepcopy(records)
    rows = _rows(risks_to_csv_bytes(records))
    assert list(rows[0]) == RISK_FIELDS and len(rows) == 10
    assert float(rows[0]["residual_score"]) == records[0]["residual_score"]
    assert int(rows[0]["inherent_score"]) == records[0]["inherent_score"]
    assert records == before


def test_control_csv_flattens_mappings_formats_effectiveness_and_preserves_nested_input(project_data):
    records = project_data["controls"]
    before = deepcopy(records)
    rows = _rows(controls_to_csv_bytes(records))
    assert list(rows[0]) == CONTROL_FIELDS and len(rows) == 12
    assert rows[0]["mapped_asset_ids"] == ";".join(records[0]["mapped_asset_ids"])
    assert rows[0]["mapped_risk_ids"] == ";".join(records[0]["mapped_risk_ids"])
    assert rows[0]["effectiveness_pct"] == f"{records[0]['effectiveness_pct']:.2f}"
    assert records == before


def test_evidence_csv_condition_status_and_immutability(project_data):
    records = project_data["evidence"]
    before = deepcopy(records)
    rows = _rows(evidence_to_csv_bytes(records))
    assert list(rows[0]) == [*EVIDENCE_FIELDS, "calculated_condition"]
    assert len(rows) == 12
    conditions = {row["calculated_condition"] for row in rows}
    assert {"Expired", "Expiring Within 30 Days", "Active"} <= conditions
    assert [row["status"] for row in rows] == [item["status"] for item in records]
    assert records == before


def test_remediation_csv_overdue_values_and_immutability(project_data):
    records = project_data["remediation"]
    before = deepcopy(records)
    rows = _rows(remediation_to_csv_bytes(records))
    assert list(rows[0]) == [*REMEDIATION_FIELDS, "overdue"] and len(rows) == 10
    assert {row["overdue"] for row in rows} == {"Yes", "No"}
    assert records == before


def test_management_markdown_sections_tables_notices_counts_and_immutability(project_data):
    before = deepcopy(project_data)
    report = generate_management_report_markdown(project_data)
    assert report.startswith("# CyberRisk360 Management Report")
    assert "EagleShield Community Bank" in report and "2026-08-05" in report
    for number, heading in enumerate([
        "Executive Summary", "Risk Overview", "Control Overview", "Evidence Health",
        "Remediation Performance", "Relationship Coverage", "Priority Residual Risks",
        "Weak or Incomplete Controls", "Expired and Expiring Evidence",
        "Overdue, Critical, and Blocked Actions", "Scope and Data Notice"], start=1):
        assert f"## {number}. {heading}" in report
    assert "| Measure | Value |" in report and "fictional" in report.lower()
    assert "10 risks" in report and "12 controls" in report
    assert project_data == before


def test_management_markdown_handles_empty_priorities():
    empty = {key: [] for key in ("assets", "risks", "controls", "evidence", "remediation")}
    report = generate_management_report_markdown(empty)
    assert "No residual risks are available" in report
    assert "No weak or incomplete controls" in report
    assert "No evidence is expired" in report
    assert "No overdue, critical-open, or blocked actions" in report


def test_zip_exact_readable_nonempty_members_parse_and_preserve_input(project_data):
    before = deepcopy(project_data)
    payload = build_report_package(project_data)
    assert isinstance(payload, bytes)
    with ZipFile(BytesIO(payload)) as package:
        assert tuple(package.namelist()) == PACKAGE_FILES
        for name in PACKAGE_FILES:
            assert package.read(name)
        assert "# CyberRisk360 Management Report" in package.read(PACKAGE_FILES[0]).decode()
        for name in PACKAGE_FILES[1:6]:
            assert list(csv.DictReader(StringIO(package.read(name).decode("utf-8"))))
        manifest = package.read(PACKAGE_FILES[6]).decode()
        for expected in ("Number of assets: 8", "Number of risks: 10",
                         "Number of controls: 12", "Number of evidence records: 12",
                         "Number of remediation actions: 10"):
            assert expected in manifest
        assert all(name in manifest for name in PACKAGE_FILES)
    assert project_data == before


@pytest.mark.parametrize("value", [None, [], "data"])
def test_project_exports_reject_invalid_project_data_type(value):
    with pytest.raises(TypeError, match="dictionary"):
        generate_management_report_markdown(value)


def test_project_exports_reject_missing_keys_and_invalid_dates(project_data):
    with pytest.raises(ValueError, match="missing required keys"):
        build_report_package({"assets": []})
    with pytest.raises(ValueError, match="real date"):
        generate_management_report_markdown(project_data, "2026-02-30")


def test_csv_exports_reject_invalid_collection_and_record_types():
    with pytest.raises(TypeError, match="must be a list"):
        assets_to_csv_bytes({})
    with pytest.raises(TypeError, match="dictionary"):
        risks_to_csv_bytes(["bad"])


def test_failed_export_does_not_mutate_input():
    records = [{"control_id": "CTL-001", "mapped_asset_ids": "bad", "mapped_risk_ids": []}]
    before = deepcopy(records)
    with pytest.raises((TypeError, ValueError)):
        controls_to_csv_bytes(records)
    assert records == before
