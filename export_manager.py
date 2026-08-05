"""In-memory CSV, Markdown, and ZIP exports for CyberRisk360."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Any, Callable
from zipfile import ZIP_DEFLATED, ZipFile

from asset_register import FIELDNAMES as ASSET_FIELDS
from control_register import FIELDNAMES as CONTROL_FIELDS
from evidence_register import FIELDNAMES as EVIDENCE_FIELDS
from remediation_register import FIELDNAMES as REMEDIATION_FIELDS
from risk_register import FIELDNAMES as RISK_FIELDS
from reporting_engine import (
    ORGANIZATION,
    REFERENCE_DATE,
    _validate_date,
    _validate_records,
    build_management_insights,
)


REQUIRED_PROJECT_KEYS = ("assets", "risks", "controls", "evidence", "remediation")
PACKAGE_FILES = (
    "CyberRisk360_Executive_Report.md",
    "CyberRisk360_Assets.csv",
    "CyberRisk360_Risks.csv",
    "CyberRisk360_Controls.csv",
    "CyberRisk360_Evidence.csv",
    "CyberRisk360_Remediation.csv",
    "CyberRisk360_Report_Manifest.txt",
)


def _project_collections(project_data: object) -> dict[str, list[dict[str, Any]]]:
    """Validate and return the five required project collections."""
    if not isinstance(project_data, dict):
        raise TypeError("project_data must be a dictionary.")
    missing = [key for key in REQUIRED_PROJECT_KEYS if key not in project_data]
    if missing:
        raise ValueError(f"project_data is missing required keys: {', '.join(missing)}.")
    return {key: _validate_records(project_data[key], key) for key in REQUIRED_PROJECT_KEYS}


def _csv_bytes(
    records: object,
    name: str,
    fieldnames: list[str],
    transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> bytes:
    """Create UTF-8 CSV bytes after validating fields without changing records."""
    rows = _validate_records(records, name)
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for index, record in enumerate(rows, start=1):
        missing = [field for field in fieldnames if field not in record]
        # Export-only calculated fields are added by a transform.
        if transform:
            missing = [field for field in missing if field not in {"calculated_condition", "overdue"}]
        if missing:
            raise ValueError(f"{name} record {index} is missing fields: {', '.join(missing)}.")
        row = dict(record)
        writer.writerow(transform(row) if transform else row)
    return output.getvalue().encode("utf-8")


def assets_to_csv_bytes(assets: list[dict[str, Any]]) -> bytes:
    """Return the asset inventory as UTF-8 CSV bytes in register field order."""
    return _csv_bytes(assets, "assets", ASSET_FIELDS)


def risks_to_csv_bytes(risks: list[dict[str, Any]]) -> bytes:
    """Return the risk register as UTF-8 CSV bytes in register field order."""
    return _csv_bytes(risks, "risks", RISK_FIELDS)


def controls_to_csv_bytes(controls: list[dict[str, Any]]) -> bytes:
    """Return controls as CSV, flattening mapping lists only in copied rows."""
    def transform(row: dict[str, Any]) -> dict[str, Any]:
        for field in ("mapped_asset_ids", "mapped_risk_ids"):
            if not isinstance(row.get(field), list):
                raise TypeError(f"control {field} must be a list.")
            row[field] = ";".join(str(item) for item in row[field])
        value = row.get("effectiveness_pct")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("control effectiveness_pct must be numeric.")
        row["effectiveness_pct"] = f"{value:.2f}"
        return row

    return _csv_bytes(controls, "controls", CONTROL_FIELDS, transform)


def evidence_to_csv_bytes(
    evidence_records: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE
) -> bytes:
    """Return evidence CSV bytes with a display-only calculated condition."""
    selected_date = _validate_date(as_of_date)
    from evidence_register import get_expired_evidence, get_expiring_evidence

    records = _validate_records(evidence_records, "evidence_records")
    expired = {str(item.get("evidence_id", "")).casefold()
               for item in get_expired_evidence(records, selected_date)}
    expiring = {str(item.get("evidence_id", "")).casefold()
                for item in get_expiring_evidence(records, 30, selected_date)}

    def transform(row: dict[str, Any]) -> dict[str, Any]:
        evidence_id = str(row.get("evidence_id", "")).casefold()
        row["calculated_condition"] = (
            "Expired" if evidence_id in expired else
            "Expiring Within 30 Days" if evidence_id in expiring else "Active"
        )
        return row

    return _csv_bytes(records, "evidence_records", [*EVIDENCE_FIELDS, "calculated_condition"], transform)


def remediation_to_csv_bytes(
    actions: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE
) -> bytes:
    """Return remediation CSV bytes with a display-only overdue column."""
    selected_date = _validate_date(as_of_date)
    from remediation_register import get_overdue_actions

    records = _validate_records(actions, "actions")
    overdue_ids = {str(item.get("action_id", "")).casefold()
                   for item in get_overdue_actions(records, selected_date)}

    def transform(row: dict[str, Any]) -> dict[str, Any]:
        row["overdue"] = "Yes" if str(row.get("action_id", "")).casefold() in overdue_ids else "No"
        return row

    return _csv_bytes(records, "actions", [*REMEDIATION_FIELDS, "overdue"], transform)


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Build a small Markdown table without exposing Python representations."""
    def clean(value: Any) -> str:
        return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _priority_or_empty(headers: list[str], rows: list[list[Any]], empty: str) -> str:
    return _markdown_table(headers, rows) if rows else f"_{empty}_"


def generate_management_report_markdown(
    project_data: dict[str, list[dict[str, Any]]], as_of_date: str = REFERENCE_DATE
) -> str:
    """Return a management report as a readable Markdown string."""
    data = _project_collections(project_data)
    selected_date = _validate_date(as_of_date)
    insights = build_management_insights(
        data["assets"], data["risks"], data["controls"], data["evidence"],
        data["remediation"], selected_date,
    )
    risk = insights["risk_summary"]
    control = insights["control_summary"]
    evidence = insights["evidence_summary"]
    remediation = insights["remediation_summary"]
    coverage = insights["relationship_coverage"]
    priorities = insights["priority_remediation"]
    priority_actions: list[dict[str, Any]] = []
    seen_actions: set[str] = set()
    for group in (priorities["overdue"], priorities["critical_open"], priorities["blocked"]):
        for action in group:
            key = str(action.get("action_id", "")).casefold()
            if key not in seen_actions:
                seen_actions.add(key)
                priority_actions.append(action)
    priority_evidence: list[dict[str, Any]] = []
    seen_evidence: set[str] = set()
    for group in (insights["priority_evidence"]["expired"], insights["priority_evidence"]["expiring_within_30_days"]):
        for item in group:
            key = str(item.get("evidence_id", "")).casefold()
            if key not in seen_evidence:
                seen_evidence.add(key)
                priority_evidence.append(item)

    return f"""# CyberRisk360 Management Report

**Organization:** {ORGANIZATION}  
**Reporting reference date:** {selected_date}

## 1. Executive Summary

The portfolio contains {risk['total_risks']} risks, {control['total_controls']} controls, {evidence['total_evidence']} evidence records, and {remediation['total_actions']} remediation actions. There are {risk['critical_risks'] + risk['high_risks']} Critical or High residual risks and {remediation['overdue_actions']} overdue actions. These indicators identify areas for management attention; they do not establish security or compliance.

## 2. Risk Overview

{_markdown_table(['Measure', 'Value'], [
    ['Total risks', risk['total_risks']], ['Open risks', risk['open_risks']],
    ['Critical', risk['critical_risks']], ['High', risk['high_risks']],
    ['Medium', risk['medium_risks']], ['Low', risk['low_risks']],
    ['Average inherent score', risk['average_inherent_score']],
    ['Average residual score', risk['average_residual_score']],
    ['Average risk reduction', f"{risk['average_risk_reduction_pct']:.2f}%"],
])}

Residual-risk concentration should guide review and treatment prioritization.

## 3. Control Overview

{_markdown_table(['Measure', 'Value'], [
    ['Total controls', control['total_controls']], ['Implemented', control['implemented_controls']],
    ['Partially implemented', control['partially_implemented_controls']], ['Planned', control['planned_controls']],
    ['Not implemented', control['not_implemented_controls']], ['Not applicable', control['not_applicable_controls']],
    ['Average effectiveness', f"{control['average_effectiveness_pct']:.2f}%"],
])}

Incomplete and lower-effectiveness controls warrant validation against their mapped risks.

## 4. Evidence Health

{_markdown_table(['Measure', 'Value'], [
    ['Total evidence', evidence['total_evidence']], ['Current stored status', evidence['current_evidence']],
    ['Calculated expired', evidence['expired_evidence']], ['Calculated expiring within 30 days', evidence['expiring_within_30_days']],
    ['Under review', evidence['under_review_evidence']], ['Rejected', evidence['rejected_evidence']],
])}

Stored workflow status remains separate from the date-based expiration condition.

## 5. Remediation Performance

{_markdown_table(['Measure', 'Value'], [
    ['Total actions', remediation['total_actions']], ['Open', remediation['open_actions']],
    ['In progress', remediation['in_progress_actions']], ['Blocked', remediation['blocked_actions']],
    ['Completed', remediation['completed_actions']], ['Closed', remediation['closed_actions']],
    ['Cancelled', remediation['cancelled_actions']], ['Overdue', remediation['overdue_actions']],
    ['Average completion', f"{remediation['average_completion_pct']:.2f}%"],
])}

Overdue and blocked actions may require owner follow-up or obstacle removal.

## 6. Relationship Coverage

{_markdown_table(['Relationship', 'Covered records', 'Coverage'], [
    ['Assets to risks', coverage['assets_with_risks'], f"{coverage['asset_risk_coverage_pct']:.2f}%"],
    ['Assets to controls', coverage['assets_with_controls'], f"{coverage['asset_control_coverage_pct']:.2f}%"],
    ['Risks to controls', coverage['risks_with_controls'], f"{coverage['risk_control_coverage_pct']:.2f}%"],
    ['Controls to evidence', coverage['controls_with_evidence'], f"{coverage['control_evidence_coverage_pct']:.2f}%"],
    ['Risks to remediation', coverage['risks_with_remediation'], f"{coverage['risk_remediation_coverage_pct']:.2f}%"],
    ['Controls to remediation', coverage['controls_with_remediation'], f"{coverage['control_remediation_coverage_pct']:.2f}%"],
])}

Coverage measures relationship presence, not control adequacy or compliance.

## 7. Priority Residual Risks

{_priority_or_empty(['Risk ID', 'Title', 'Inherent', 'Residual', 'Rating'], [
    [item.get('risk_id'), item.get('risk_title'), item.get('inherent_score'), item.get('residual_score'), item.get('residual_rating')]
    for item in insights['top_residual_risks']
], 'No residual risks are available for prioritization.')}

## 8. Weak or Incomplete Controls

{_priority_or_empty(['Control ID', 'Control', 'Status', 'Effectiveness'], [
    [item.get('control_id'), item.get('control_name'), item.get('implementation_status'), f"{float(item.get('effectiveness_pct', 0)):.2f}%"]
    for item in insights['weak_controls']
], 'No weak or incomplete controls were identified by the reporting criteria.')}

## 9. Expired and Expiring Evidence

{_priority_or_empty(['Evidence ID', 'Evidence', 'Control', 'Expiration date', 'Stored status'], [
    [item.get('evidence_id'), item.get('evidence_name'), item.get('control_id'), item.get('expiration_date'), item.get('status')]
    for item in priority_evidence
], 'No evidence is expired or expiring within 30 days.')}

## 10. Overdue, Critical, and Blocked Actions

{_priority_or_empty(['Action ID', 'Action', 'Priority', 'Status', 'Due date', 'Completion'], [
    [item.get('action_id'), item.get('action_title'), item.get('priority'), item.get('status'), item.get('due_date'), f"{item.get('completion_pct', 0)}%"]
    for item in priority_actions
], 'No overdue, critical-open, or blocked actions were identified.')}

## 11. Scope and Data Notice

All CyberRisk360 data is fictional and created for education and portfolio demonstration. This report is educational and is not an actual assessment of a bank, security posture, regulatory compliance, or operational readiness. Results use the fixed reporting reference date shown above and reflect only the supplied in-memory registers.
"""


def build_report_package(
    project_data: dict[str, list[dict[str, Any]]], as_of_date: str = REFERENCE_DATE
) -> bytes:
    """Return a compressed seven-file reporting package entirely in memory."""
    data = _project_collections(project_data)
    selected_date = _validate_date(as_of_date)
    report = generate_management_report_markdown(data, selected_date).encode("utf-8")
    members: dict[str, bytes] = {
        PACKAGE_FILES[0]: report,
        PACKAGE_FILES[1]: assets_to_csv_bytes(data["assets"]),
        PACKAGE_FILES[2]: risks_to_csv_bytes(data["risks"]),
        PACKAGE_FILES[3]: controls_to_csv_bytes(data["controls"]),
        PACKAGE_FILES[4]: evidence_to_csv_bytes(data["evidence"], selected_date),
        PACKAGE_FILES[5]: remediation_to_csv_bytes(data["remediation"], selected_date),
    }
    manifest = f"""Project name: CyberRisk360
Fictional organization: {ORGANIZATION}
Reporting reference date: {selected_date}
Number of assets: {len(data['assets'])}
Number of risks: {len(data['risks'])}
Number of controls: {len(data['controls'])}
Number of evidence records: {len(data['evidence'])}
Number of remediation actions: {len(data['remediation'])}

Files contained in this package:
{chr(10).join(f'- {name}' for name in PACKAGE_FILES)}

Fictional-data notice: All data is fictional and educational. This package is not an actual bank assessment.
""".encode("utf-8")
    members[PACKAGE_FILES[6]] = manifest
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as package:
        for filename in PACKAGE_FILES:
            package.writestr(filename, members[filename])
    return archive.getvalue()
