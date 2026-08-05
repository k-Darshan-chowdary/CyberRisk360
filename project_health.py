"""Read-only quality and deployment-readiness checks for CyberRisk360."""

from __future__ import annotations

import copy
from io import BytesIO
from pathlib import Path
import re
import sys
import tomllib
from typing import Any, Callable
from zipfile import BadZipFile, ZipFile

from asset_register import load_assets
from control_register import load_controls
from evidence_register import load_evidence
from export_manager import PACKAGE_FILES, build_report_package, generate_management_report_markdown
from integrity_guard import verify_sample_data_integrity
from remediation_register import load_remediation_actions
from reporting_engine import build_management_insights
from risk_register import load_risks


PROJECT_ROOT = Path(__file__).resolve().parent
REFERENCE_DATE = "2026-08-05"
ORGANIZATION = "EagleShield Community Bank"
CHECK_KEYS = {"check_id", "category", "name", "status", "details"}
REQUIRED_FILES = (
    "app.py", "requirements.txt", "data/sample_assets.csv", "data/sample_risks.csv",
    "data/sample_controls.csv", "data/sample_evidence.csv", "data/sample_remediation.csv",
    "risk_engine.py", "risk_register.py", "asset_register.py", "control_register.py",
    "evidence_register.py", "remediation_register.py", "reporting_engine.py",
    "export_manager.py", "data/integrity_manifest.json", ".streamlit/config.toml",
)


def _result(check_id: str, category: str, name: str, passed: bool, details: str) -> dict[str, str]:
    return {"check_id": check_id, "category": category, "name": name,
            "status": "Pass" if passed else "Fail", "details": details}


def _validate_date(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("The reference date must be a string.")
    from datetime import date
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError("The reference date must use YYYY-MM-DD format.") from error


def load_all_project_data(project_root: str | Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load all registers through their existing read-only backend loaders."""
    root = Path(project_root) if project_root is not None else PROJECT_ROOT
    data = root / "data"
    return {
        "assets": load_assets(data / "sample_assets.csv"),
        "risks": load_risks(data / "sample_risks.csv"),
        "controls": load_controls(data / "sample_controls.csv"),
        "evidence": load_evidence(data / "sample_evidence.csv"),
        "remediation": load_remediation_actions(data / "sample_remediation.csv"),
    }


def check_required_files(project_root: str | Path | None = None) -> dict[str, str]:
    root = Path(project_root) if project_root is not None else PROJECT_ROOT
    missing = [name for name in REQUIRED_FILES if not (root / Path(name)).is_file()]
    details = "All required project files are present." if not missing else "Missing: " + ", ".join(missing)
    return _result("required_files", "Project", "Required Files", not missing, details)


def check_data_loading() -> dict[str, str]:
    try:
        data = load_all_project_data()
        missing = [name for name in ("assets", "risks", "controls", "evidence", "remediation")
                   if not isinstance(data.get(name), list)]
        if missing:
            return _result("data_loading", "Data", "Data Loading", False,
                           "Invalid loaded collections: " + ", ".join(missing))
        return _result("data_loading", "Data", "Data Loading", True,
                       "All five sample datasets loaded successfully.")
    except Exception as error:
        return _result("data_loading", "Data", "Data Loading", False,
                       f"Data loading failed: {type(error).__name__}: {error}")


def check_expected_sample_counts() -> dict[str, str]:
    expected = {"assets": 8, "risks": 10, "controls": 12, "evidence": 12, "remediation": 10}
    try:
        data = load_all_project_data()
        actual = {name: len(data[name]) for name in expected}
        mismatches = [f"{name} expected {expected[name]}, found {actual[name]}"
                      for name in expected if actual[name] != expected[name]]
        details = "Expected counts confirmed: 8 assets, 10 risks, 12 controls, 12 evidence records, and 10 remediation actions."
        if mismatches:
            details = "Count mismatches: " + "; ".join(mismatches)
        return _result("sample_counts", "Data", "Sample Counts", not mismatches, details)
    except Exception as error:
        return _result("sample_counts", "Data", "Sample Counts", False,
                       f"Count check failed: {type(error).__name__}: {error}")


def check_relationship_integrity() -> dict[str, str]:
    try:
        data = load_all_project_data()
        assets = {str(item["asset_id"]).casefold() for item in data["assets"]}
        risks = {str(item["risk_id"]).casefold() for item in data["risks"]}
        controls = {str(item["control_id"]).casefold() for item in data["controls"]}
        invalid = 0
        invalid += sum(str(item.get("affected_asset_id", "")).casefold() not in assets for item in data["risks"])
        for item in data["controls"]:
            invalid += sum(str(value).casefold() not in assets for value in item.get("mapped_asset_ids", []))
            invalid += sum(str(value).casefold() not in risks for value in item.get("mapped_risk_ids", []))
        invalid += sum(str(item.get("control_id", "")).casefold() not in controls for item in data["evidence"])
        for item in data["remediation"]:
            risk = str(item.get("related_risk_id", "")).strip().casefold()
            control = str(item.get("related_control_id", "")).strip().casefold()
            invalid += int(bool(risk) and risk not in risks)
            invalid += int(bool(control) and control not in controls)
        return _result("relationship_integrity", "Data", "Relationship Integrity", invalid == 0,
                       f"Invalid relationships found: {invalid}.")
    except Exception as error:
        return _result("relationship_integrity", "Data", "Relationship Integrity", False,
                       f"Relationship check failed: {type(error).__name__}: {error}")


def check_sample_integrity() -> dict[str, str]:
    try:
        report = verify_sample_data_integrity()
        return _result("sample_integrity", "Integrity", "Sample Data Integrity",
                       report["status"] == "Pass",
                       f"Verified {report['verified_files']} of {report['total_files']} protected files; {report['failed_files']} failed.")
    except Exception as error:
        return _result("sample_integrity", "Integrity", "Sample Data Integrity", False,
                       f"Integrity check failed: {type(error).__name__}: {error}")


def check_reporting_and_exports(reference_date: str = REFERENCE_DATE) -> dict[str, str]:
    selected_date = _validate_date(reference_date)
    try:
        data = load_all_project_data()
        build_management_insights(data["assets"], data["risks"], data["controls"],
                                  data["evidence"], data["remediation"], selected_date)
        markdown = generate_management_report_markdown(data, selected_date)
        package = build_report_package(data, selected_date)
        with ZipFile(BytesIO(package)) as archive:
            members = archive.namelist()
            archive.testzip()
        valid = bool(markdown.strip()) and members == list(PACKAGE_FILES)
        details = "Markdown and seven-member ZIP reports generated successfully in memory."
        if not valid:
            details = f"Export validation failed: Markdown non-empty={bool(markdown.strip())}; ZIP members={len(members)}."
        return _result("reporting_exports", "Reporting", "Reporting and Exports", valid, details)
    except (BadZipFile, Exception) as error:
        return _result("reporting_exports", "Reporting", "Reporting and Exports", False,
                       f"Report generation failed: {type(error).__name__}: {error}")


def check_streamlit_configuration(config_path: str | Path | None = None) -> dict[str, str]:
    path = Path(config_path) if config_path is not None else PROJECT_ROOT / ".streamlit" / "config.toml"
    try:
        with path.open("rb") as source:
            config = tomllib.load(source)
        expected = (("server", "headless", True), ("server", "enableXsrfProtection", True),
                    ("server", "enableCORS", True), ("client", "showErrorDetails", "none"),
                    ("browser", "gatherUsageStats", False))
        invalid = [f"{section}.{key}" for section, key, value in expected
                   if config.get(section, {}).get(key) != value]
        details = "Required Streamlit production settings are enabled." if not invalid else "Incorrect settings: " + ", ".join(invalid)
        return _result("streamlit_config", "Configuration", "Streamlit Configuration", not invalid, details)
    except (OSError, tomllib.TOMLDecodeError, TypeError) as error:
        return _result("streamlit_config", "Configuration", "Streamlit Configuration", False,
                       f"Configuration check failed: {type(error).__name__}: {error}")


def check_dependency_pinning(requirements_path: str | Path | None = None) -> dict[str, str]:
    path = Path(requirements_path) if requirements_path is not None else PROJECT_ROOT / "requirements.txt"
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        pattern = re.compile(r"^([a-z0-9][a-z0-9._-]*)==([^=\s]+)$", re.IGNORECASE)
        names: list[str] = []
        invalid: list[str] = []
        for line in lines:
            match = pattern.fullmatch(line)
            if not match:
                invalid.append(line)
            else:
                names.append(re.sub(r"[-_.]+", "-", match.group(1).lower()))
        duplicates = sorted({name for name in names if names.count(name) > 1})
        missing = sorted({"streamlit", "pandas", "plotly", "pytest"} - set(names))
        passed = bool(lines) and not invalid and not duplicates and not missing
        problems = []
        if invalid: problems.append("unpinned or invalid lines: " + ", ".join(invalid))
        if duplicates: problems.append("duplicates: " + ", ".join(duplicates))
        if missing: problems.append("missing: " + ", ".join(missing))
        details = "All direct dependencies use exact version pins." if passed else "; ".join(problems) or "No dependencies found."
        return _result("dependency_pinning", "Dependencies", "Dependency Pinning", passed, details)
    except (OSError, UnicodeError) as error:
        return _result("dependency_pinning", "Dependencies", "Dependency Pinning", False,
                       f"Requirements check failed: {type(error).__name__}: {error}")


def run_project_health_check(reference_date: str = REFERENCE_DATE) -> dict[str, object]:
    selected_date = _validate_date(reference_date)
    checks = [check_required_files(), check_data_loading(), check_expected_sample_counts(),
              check_relationship_integrity(), check_sample_integrity(),
              check_reporting_and_exports(selected_date), check_streamlit_configuration(),
              check_dependency_pinning()]
    passed = sum(check["status"] == "Pass" for check in checks)
    return {"organization": ORGANIZATION, "reference_date": selected_date,
            "overall_status": "Healthy" if passed == len(checks) else "Needs Attention",
            "total_checks": len(checks), "passed_checks": passed,
            "failed_checks": len(checks) - passed, "checks": copy.deepcopy(checks)}


def get_failed_health_checks(health_report: object) -> list[dict[str, str]]:
    if not isinstance(health_report, dict):
        raise TypeError("The health report must be a dictionary.")
    checks = health_report.get("checks")
    if not isinstance(checks, list):
        raise ValueError("The health report must contain a checks list.")
    for check in checks:
        if not isinstance(check, dict):
            raise TypeError("Each health check must be a dictionary.")
        if set(check) != CHECK_KEYS or check["status"] not in {"Pass", "Fail"}:
            raise ValueError("A health check has an invalid structure.")
    return [copy.deepcopy(check) for check in checks if check["status"] == "Fail"]


def format_health_report_markdown(health_report: object) -> str:
    if not isinstance(health_report, dict):
        raise TypeError("The health report must be a dictionary.")
    checks = health_report.get("checks")
    if not isinstance(checks, list):
        raise ValueError("The health report must contain checks.")
    rows = "\n".join(f"| {item['category']} | {item['name']} | {item['status']} | {item['details']} |"
                     for item in checks)
    return f"""# CyberRisk360 Project Health Report

**Project:** CyberRisk360  
**Organization:** {health_report.get('organization')}  
**Reference date:** {health_report.get('reference_date')}  
**Overall status:** {health_report.get('overall_status')}  
**Passed checks:** {health_report.get('passed_checks')}  
**Failed checks:** {health_report.get('failed_checks')}

| Category | Check | Status | Details |
|---|---|---|---|
{rows}

All data is fictional and provided for education. These health checks are not a security certification.
"""


def _main() -> int:
    try:
        report = run_project_health_check()
        print("Project: CyberRisk360")
        print(f"Reference date: {report['reference_date']}")
        print(f"Overall status: {report['overall_status']}")
        for check in report["checks"]:
            print(f"- {check['name']}: {check['status']} - {check['details']}")
        return 0 if report["overall_status"] == "Healthy" else 1
    except (TypeError, ValueError, OSError) as error:
        print(f"CyberRisk360 project health: Needs Attention\n- {error}")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
