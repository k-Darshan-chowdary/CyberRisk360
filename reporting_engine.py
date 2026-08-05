"""Read-only management reporting calculations for CyberRisk360."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from evidence_register import get_expired_evidence, get_expiring_evidence
from remediation_register import get_overdue_actions


ORGANIZATION = "EagleShield Community Bank"
REFERENCE_DATE = "2026-08-05"


def _validate_records(records: object, name: str) -> list[dict[str, Any]]:
    """Validate a public record collection and return the original list."""
    if not isinstance(records, list):
        raise TypeError(f"{name} must be a list.")
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise TypeError(f"{name} record {index} must be a dictionary.")
    return records


def _validate_date(value: object) -> str:
    """Return a validated real calendar date in exact ISO format."""
    if not isinstance(value, str):
        raise TypeError("as_of_date must be text in YYYY-MM-DD format.")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("as_of_date must be a real date in YYYY-MM-DD format.") from exc
    if parsed.strftime("%Y-%m-%d") != value:
        raise ValueError("as_of_date must be a real date in YYYY-MM-DD format.")
    return value


def _number(record: dict[str, Any], field: str, record_name: str) -> float:
    """Read a non-boolean numeric field with a clear public error."""
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{record_name} {field} must be numeric.")
    return float(value)


def _percentage(count: int, total: int) -> float:
    return round(count / total * 100, 2) if total else 0


def summarize_risks(risks: list[dict[str, Any]]) -> dict[str, int | float]:
    """Summarize residual risk ratings, open work, scores, and reduction."""
    records = _validate_records(risks, "risks")
    ratings = {name: 0 for name in ("critical", "high", "medium", "low")}
    inherent_scores: list[float] = []
    residual_scores: list[float] = []
    reductions: list[float] = []
    open_count = 0
    for risk in records:
        rating = str(risk.get("residual_rating", "")).casefold()
        if rating in ratings:
            ratings[rating] += 1
        if str(risk.get("status", "")).casefold() not in {"closed", "accepted"}:
            open_count += 1
        inherent = _number(risk, "inherent_score", "risk")
        residual = _number(risk, "residual_score", "risk")
        inherent_scores.append(inherent)
        residual_scores.append(residual)
        reductions.append(((inherent - residual) / inherent * 100) if inherent else 0.0)
    total = len(records)
    return {
        "total_risks": total,
        "critical_risks": ratings["critical"],
        "high_risks": ratings["high"],
        "medium_risks": ratings["medium"],
        "low_risks": ratings["low"],
        "open_risks": open_count,
        "average_inherent_score": round(sum(inherent_scores) / total, 2) if total else 0,
        "average_residual_score": round(sum(residual_scores) / total, 2) if total else 0,
        "average_risk_reduction_pct": round(sum(reductions) / total, 2) if total else 0,
    }


def summarize_controls(controls: list[dict[str, Any]]) -> dict[str, int | float]:
    """Summarize control implementation states and average effectiveness."""
    records = _validate_records(controls, "controls")
    statuses = {
        "implemented": 0, "partially implemented": 0, "planned": 0,
        "not implemented": 0, "not applicable": 0,
    }
    effectiveness: list[float] = []
    for control in records:
        status = str(control.get("implementation_status", "")).casefold()
        if status in statuses:
            statuses[status] += 1
        effectiveness.append(_number(control, "effectiveness_pct", "control"))
    total = len(records)
    return {
        "total_controls": total,
        "implemented_controls": statuses["implemented"],
        "partially_implemented_controls": statuses["partially implemented"],
        "planned_controls": statuses["planned"],
        "not_implemented_controls": statuses["not implemented"],
        "not_applicable_controls": statuses["not applicable"],
        "average_effectiveness_pct": round(sum(effectiveness) / total, 2) if total else 0,
    }


def summarize_evidence(
    evidence_records: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE
) -> dict[str, int]:
    """Summarize stored evidence statuses and calculated expiration health."""
    records = _validate_records(evidence_records, "evidence_records")
    selected_date = _validate_date(as_of_date)
    expired = get_expired_evidence(records, selected_date)
    expiring = get_expiring_evidence(records, days=30, as_of_date=selected_date)
    statuses = [str(item.get("status", "")).casefold() for item in records]
    return {
        "total_evidence": len(records),
        "current_evidence": statuses.count("current"),
        "under_review_evidence": statuses.count("under review"),
        "expired_evidence": len(expired),
        "expiring_within_30_days": len(expiring),
        "rejected_evidence": statuses.count("rejected"),
    }


def summarize_remediation(
    actions: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE
) -> dict[str, int | float]:
    """Summarize action status, overdue work, and average completion."""
    records = _validate_records(actions, "actions")
    selected_date = _validate_date(as_of_date)
    names = ("open", "in progress", "blocked", "completed", "closed", "cancelled")
    statuses = {name: 0 for name in names}
    completion: list[float] = []
    for action in records:
        status = str(action.get("status", "")).casefold()
        if status in statuses:
            statuses[status] += 1
        completion.append(_number(action, "completion_pct", "remediation action"))
    total = len(records)
    return {
        "total_actions": total,
        "open_actions": statuses["open"],
        "in_progress_actions": statuses["in progress"],
        "blocked_actions": statuses["blocked"],
        "completed_actions": statuses["completed"],
        "closed_actions": statuses["closed"],
        "cancelled_actions": statuses["cancelled"],
        "overdue_actions": len(get_overdue_actions(records, selected_date)),
        "average_completion_pct": round(sum(completion) / total, 2) if total else 0,
    }


def calculate_relationship_coverage(
    assets: list[dict[str, Any]], risks: list[dict[str, Any]],
    controls: list[dict[str, Any]], evidence_records: list[dict[str, Any]],
    remediation_actions: list[dict[str, Any]],
) -> dict[str, int | float]:
    """Calculate unique, valid relationship coverage across all registers."""
    assets = _validate_records(assets, "assets")
    risks = _validate_records(risks, "risks")
    controls = _validate_records(controls, "controls")
    evidence_records = _validate_records(evidence_records, "evidence_records")
    remediation_actions = _validate_records(remediation_actions, "remediation_actions")
    asset_ids = {str(item.get("asset_id", "")).casefold() for item in assets if item.get("asset_id")}
    risk_ids = {str(item.get("risk_id", "")).casefold() for item in risks if item.get("risk_id")}
    control_ids = {str(item.get("control_id", "")).casefold() for item in controls if item.get("control_id")}

    assets_with_risks = {
        str(item.get("affected_asset_id", "")).casefold() for item in risks
        if str(item.get("affected_asset_id", "")).casefold() in asset_ids
    }
    assets_with_controls: set[str] = set()
    risks_with_controls: set[str] = set()
    for control in controls:
        mapped_assets = control.get("mapped_asset_ids", [])
        mapped_risks = control.get("mapped_risk_ids", [])
        if not isinstance(mapped_assets, list) or not isinstance(mapped_risks, list):
            raise TypeError("control mapping fields must be lists.")
        assets_with_controls.update(str(value).casefold() for value in mapped_assets
                                    if str(value).casefold() in asset_ids)
        risks_with_controls.update(str(value).casefold() for value in mapped_risks
                                   if str(value).casefold() in risk_ids)
    controls_with_evidence = {
        str(item.get("control_id", "")).casefold() for item in evidence_records
        if str(item.get("control_id", "")).casefold() in control_ids
    }
    risks_with_remediation = {
        str(item.get("related_risk_id", "")).casefold() for item in remediation_actions
        if str(item.get("related_risk_id", "")).casefold() in risk_ids
    }
    controls_with_remediation = {
        str(item.get("related_control_id", "")).casefold() for item in remediation_actions
        if str(item.get("related_control_id", "")).casefold() in control_ids
    }
    counts = {
        "assets_with_risks": len(assets_with_risks),
        "assets_with_controls": len(assets_with_controls),
        "risks_with_controls": len(risks_with_controls),
        "controls_with_evidence": len(controls_with_evidence),
        "risks_with_remediation": len(risks_with_remediation),
        "controls_with_remediation": len(controls_with_remediation),
    }
    return {
        "assets_with_risks": counts["assets_with_risks"],
        "asset_risk_coverage_pct": _percentage(counts["assets_with_risks"], len(assets)),
        "assets_with_controls": counts["assets_with_controls"],
        "asset_control_coverage_pct": _percentage(counts["assets_with_controls"], len(assets)),
        "risks_with_controls": counts["risks_with_controls"],
        "risk_control_coverage_pct": _percentage(counts["risks_with_controls"], len(risks)),
        "controls_with_evidence": counts["controls_with_evidence"],
        "control_evidence_coverage_pct": _percentage(counts["controls_with_evidence"], len(controls)),
        "risks_with_remediation": counts["risks_with_remediation"],
        "risk_remediation_coverage_pct": _percentage(counts["risks_with_remediation"], len(risks)),
        "controls_with_remediation": counts["controls_with_remediation"],
        "control_remediation_coverage_pct": _percentage(counts["controls_with_remediation"], len(controls)),
    }


def get_top_residual_risks(
    risks: list[dict[str, Any]], limit: int = 5
) -> list[dict[str, Any]]:
    """Return independent copies of the highest residual risks."""
    records = _validate_records(risks, "risks")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit must be a non-negative integer.")
    if limit < 0:
        raise ValueError("limit must be a non-negative integer.")
    ordered = sorted(
        records,
        key=lambda item: (
            -_number(item, "residual_score", "risk"),
            -_number(item, "inherent_score", "risk"),
            str(item.get("risk_id", "")).casefold(),
        ),
    )
    return deepcopy(ordered[:limit])


def get_weak_controls(
    controls: list[dict[str, Any]], effectiveness_threshold: int | float = 50
) -> list[dict[str, Any]]:
    """Return deep copies of controls with weak effectiveness or incomplete status."""
    records = _validate_records(controls, "controls")
    if isinstance(effectiveness_threshold, bool) or not isinstance(effectiveness_threshold, (int, float)):
        raise TypeError("effectiveness_threshold must be a number from 0 through 100.")
    if not 0 <= effectiveness_threshold <= 100:
        raise ValueError("effectiveness_threshold must be between 0 and 100.")
    incomplete = {"planned", "not implemented", "partially implemented"}
    selected = [item for item in records if
                _number(item, "effectiveness_pct", "control") < effectiveness_threshold
                or str(item.get("implementation_status", "")).casefold() in incomplete]
    selected.sort(key=lambda item: (
        _number(item, "effectiveness_pct", "control"),
        str(item.get("control_id", "")).casefold(),
    ))
    return deepcopy(selected)


def get_priority_evidence(
    evidence_records: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE
) -> dict[str, list[dict[str, Any]]]:
    """Return independent priority evidence groups in source order."""
    records = _validate_records(evidence_records, "evidence_records")
    selected_date = _validate_date(as_of_date)
    expired = get_expired_evidence(records, selected_date)
    expiring = get_expiring_evidence(records, days=30, as_of_date=selected_date)
    return {
        "expired": deepcopy(expired),
        "expiring_within_30_days": deepcopy(expiring),
        "under_review": deepcopy([item for item in records if str(item.get("status", "")).casefold() == "under review"]),
        "rejected": deepcopy([item for item in records if str(item.get("status", "")).casefold() == "rejected"]),
    }


def get_priority_remediation(
    actions: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE
) -> dict[str, list[dict[str, Any]]]:
    """Return independent overdue, critical-open, and blocked action groups."""
    records = _validate_records(actions, "actions")
    selected_date = _validate_date(as_of_date)
    inactive = {"completed", "closed", "cancelled"}
    return {
        "overdue": deepcopy(get_overdue_actions(records, selected_date)),
        "critical_open": deepcopy([item for item in records
            if str(item.get("priority", "")).casefold() == "critical"
            and str(item.get("status", "")).casefold() not in inactive]),
        "blocked": deepcopy([item for item in records
            if str(item.get("status", "")).casefold() == "blocked"]),
    }


def build_management_insights(
    assets: list[dict[str, Any]], risks: list[dict[str, Any]],
    controls: list[dict[str, Any]], evidence_records: list[dict[str, Any]],
    remediation_actions: list[dict[str, Any]], as_of_date: str = REFERENCE_DATE,
) -> dict[str, Any]:
    """Build one independent management-insight model from all project registers."""
    selected_date = _validate_date(as_of_date)
    return {
        "organization": ORGANIZATION,
        "reference_date": selected_date,
        "risk_summary": summarize_risks(risks),
        "control_summary": summarize_controls(controls),
        "evidence_summary": summarize_evidence(evidence_records, selected_date),
        "remediation_summary": summarize_remediation(remediation_actions, selected_date),
        "relationship_coverage": calculate_relationship_coverage(
            assets, risks, controls, evidence_records, remediation_actions
        ),
        "top_residual_risks": get_top_residual_risks(risks),
        "weak_controls": get_weak_controls(controls),
        "priority_evidence": get_priority_evidence(evidence_records, selected_date),
        "priority_remediation": get_priority_remediation(remediation_actions, selected_date),
    }
