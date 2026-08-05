"""Phase 8 tests for structured, read-only project health checks."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

import project_health as health
from integrity_guard import calculate_file_sha256, load_integrity_manifest


CHECKS = (
    health.check_required_files, health.check_data_loading, health.check_expected_sample_counts,
    health.check_relationship_integrity, health.check_sample_integrity,
    health.check_reporting_and_exports, health.check_streamlit_configuration,
    health.check_dependency_pinning,
)


@pytest.mark.parametrize("check", CHECKS)
def test_each_check_has_exact_keys_and_allowed_status(check):
    result = check()
    assert set(result) == health.CHECK_KEYS
    assert result["status"] in {"Pass", "Fail"}


def test_required_files_pass_and_missing_file_fails(tmp_path):
    assert health.check_required_files()["status"] == "Pass"
    assert health.check_required_files(tmp_path)["status"] == "Fail"
    assert str(tmp_path) not in health.check_required_files(tmp_path)["details"]


def test_data_loading_passes_and_loader_exception_becomes_fail(monkeypatch):
    assert health.check_data_loading()["status"] == "Pass"
    monkeypatch.setattr(health, "load_all_project_data", lambda: (_ for _ in ()).throw(ValueError("bad")))
    assert health.check_data_loading()["status"] == "Fail"


def test_counts_pass_and_mismatch_fails(monkeypatch):
    assert health.check_expected_sample_counts()["status"] == "Pass"
    data = health.load_all_project_data()
    data["assets"] = data["assets"][:-1]
    monkeypatch.setattr(health, "load_all_project_data", lambda: data)
    assert health.check_expected_sample_counts()["status"] == "Fail"


def test_relationships_pass_and_invalid_reference_fails(monkeypatch):
    assert health.check_relationship_integrity()["status"] == "Pass"
    data = health.load_all_project_data()
    data["risks"][0]["affected_asset_id"] = "AST-999"
    monkeypatch.setattr(health, "load_all_project_data", lambda: data)
    result = health.check_relationship_integrity()
    assert result["status"] == "Fail" and "1" in result["details"]


def test_integrity_and_reporting_exports_pass():
    assert health.check_sample_integrity()["status"] == "Pass"
    assert health.check_reporting_and_exports()["status"] == "Pass"


def test_corrupt_export_becomes_fail(monkeypatch):
    monkeypatch.setattr(health, "build_report_package", lambda *_args: b"not a zip")
    assert health.check_reporting_and_exports()["status"] == "Fail"


def test_streamlit_config_passes_and_bad_configs_fail(tmp_path):
    assert health.check_streamlit_configuration()["status"] == "Pass"
    missing = health.check_streamlit_configuration(tmp_path / "missing.toml")
    assert missing["status"] == "Fail"
    malformed = tmp_path / "bad.toml"
    malformed.write_text("[broken", encoding="utf-8")
    assert health.check_streamlit_configuration(malformed)["status"] == "Fail"
    unsafe = tmp_path / "unsafe.toml"
    unsafe.write_text("[server]\nheadless=false\n", encoding="utf-8")
    assert health.check_streamlit_configuration(unsafe)["status"] == "Fail"


@pytest.mark.parametrize("content", [
    "streamlit\npandas==1\nplotly==1\npytest==1\n",
    "streamlit==1\nstreamlit==2\npandas==1\nplotly==1\npytest==1\n",
    "streamlit==1\npandas==1\nplotly==1\n",
])
def test_invalid_dependency_files_fail(tmp_path, content):
    path = tmp_path / "requirements.txt"
    path.write_text(content, encoding="utf-8")
    assert health.check_dependency_pinning(path)["status"] == "Fail"


def test_dependency_pinning_passes():
    assert health.check_dependency_pinning()["status"] == "Pass"


def test_full_health_report_is_healthy_and_ordered():
    report = health.run_project_health_check()
    assert set(report) == {"organization", "reference_date", "overall_status", "total_checks",
                           "passed_checks", "failed_checks", "checks"}
    assert report["overall_status"] == "Healthy"
    assert (report["total_checks"], report["passed_checks"], report["failed_checks"]) == (8, 8, 0)
    assert [item["name"] for item in report["checks"]] == [
        "Required Files", "Data Loading", "Sample Counts", "Relationship Integrity",
        "Sample Data Integrity", "Reporting and Exports", "Streamlit Configuration", "Dependency Pinning"]


@pytest.mark.parametrize("value", ["", "08/05/2026", "2026-02-30"])
def test_invalid_dates_raise(value):
    with pytest.raises(ValueError):
        health.run_project_health_check(value)


def test_failed_helper_returns_copies(monkeypatch):
    report = health.run_project_health_check()
    report["checks"][0]["status"] = "Fail"
    failed = health.get_failed_health_checks(report)
    failed[0]["details"] = "changed"
    assert report["checks"][0]["details"] != "changed"


def test_markdown_contains_required_notices():
    markdown = health.format_health_report_markdown(health.run_project_health_check())
    for phrase in ("CyberRisk360", health.ORGANIZATION, "2026-08-05", "Healthy",
                   "fictional", "not a security certification"):
        assert phrase in markdown


def test_health_does_not_change_samples_or_create_reports():
    manifest = load_integrity_manifest()
    before = {name: calculate_file_sha256(health.PROJECT_ROOT / name) for name in manifest["files"]}
    health.run_project_health_check()
    after = {name: calculate_file_sha256(health.PROJECT_ROOT / name) for name in manifest["files"]}
    assert before == after
    assert not (health.PROJECT_ROOT / "CyberRisk360_Report_Package.zip").exists()
