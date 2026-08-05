"""Tests for the read-only Phase 7 reporting calculations."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from asset_register import load_assets
from control_register import load_controls
from evidence_register import load_evidence
from remediation_register import load_remediation_actions
from reporting_engine import (
    build_management_insights, calculate_relationship_coverage,
    get_priority_evidence, get_priority_remediation, get_top_residual_risks,
    get_weak_controls, summarize_controls, summarize_evidence,
    summarize_remediation, summarize_risks,
)
from risk_register import load_risks


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


def test_risk_summary_exact_keys_counts_averages_and_immutability(project_data):
    risks = project_data["risks"]
    before = deepcopy(risks)
    result = summarize_risks(risks)
    assert list(result) == [
        "total_risks", "critical_risks", "high_risks", "medium_risks", "low_risks",
        "open_risks", "average_inherent_score", "average_residual_score",
        "average_risk_reduction_pct",
    ]
    assert result["total_risks"] == 10
    assert sum(result[name] for name in
               ("critical_risks", "high_risks", "medium_risks", "low_risks")) == 10
    assert result["open_risks"] == sum(
        risk["status"].casefold() not in {"closed", "accepted"} for risk in risks)
    assert result["average_inherent_score"] == round(
        sum(risk["inherent_score"] for risk in risks) / 10, 2)
    assert result["average_residual_score"] == round(
        sum(risk["residual_score"] for risk in risks) / 10, 2)
    expected_reduction = sum(
        ((risk["inherent_score"] - risk["residual_score"]) / risk["inherent_score"] * 100)
        if risk["inherent_score"] else 0 for risk in risks) / 10
    assert result["average_risk_reduction_pct"] == round(expected_reduction, 2)
    assert risks == before


def test_risk_summary_empty_and_zero_inherent():
    assert summarize_risks([]) == {name: 0 for name in (
        "total_risks", "critical_risks", "high_risks", "medium_risks", "low_risks",
        "open_risks", "average_inherent_score", "average_residual_score",
        "average_risk_reduction_pct")}
    risk = {"residual_rating": "low", "status": "closed", "inherent_score": 0,
            "residual_score": 0}
    assert summarize_risks([risk])["average_risk_reduction_pct"] == 0


def test_control_summary_exact_keys_statuses_average_and_deep_immutability(project_data):
    controls = project_data["controls"]
    before = deepcopy(controls)
    result = summarize_controls(controls)
    assert list(result) == [
        "total_controls", "implemented_controls", "partially_implemented_controls",
        "planned_controls", "not_implemented_controls", "not_applicable_controls",
        "average_effectiveness_pct",
    ]
    assert result["total_controls"] == 12
    assert sum(result[name] for name in list(result)[1:6]) == 12
    assert result["average_effectiveness_pct"] == round(
        sum(item["effectiveness_pct"] for item in controls) / 12, 2)
    assert controls == before
    assert summarize_controls([])["average_effectiveness_pct"] == 0


def test_evidence_summary_classification_date_validation_and_immutability(project_data):
    records = project_data["evidence"]
    before = deepcopy(records)
    result = summarize_evidence(records)
    assert list(result) == ["total_evidence", "current_evidence", "under_review_evidence",
                            "expired_evidence", "expiring_within_30_days", "rejected_evidence"]
    assert result["total_evidence"] == 12
    assert result["expired_evidence"] > 0
    assert result["expiring_within_30_days"] > 0
    assert result["under_review_evidence"] == sum(
        item["status"].casefold() == "under review" for item in records)
    assert result["rejected_evidence"] == sum(
        item["status"].casefold() == "rejected" for item in records)
    assert records == before
    with pytest.raises(ValueError, match="real date"):
        summarize_evidence(records, "2026-02-30")


def test_remediation_summary_exact_statuses_overdue_average_and_empty(project_data):
    actions = project_data["remediation"]
    before = deepcopy(actions)
    result = summarize_remediation(actions)
    assert list(result) == [
        "total_actions", "open_actions", "in_progress_actions", "blocked_actions",
        "completed_actions", "closed_actions", "cancelled_actions", "overdue_actions",
        "average_completion_pct",
    ]
    assert result["total_actions"] == 10
    assert sum(result[name] for name in list(result)[1:7]) == 10
    assert result["overdue_actions"] > 0
    assert result["average_completion_pct"] == round(
        sum(item["completion_pct"] for item in actions) / 10, 2)
    assert actions == before
    assert summarize_remediation([])["total_actions"] == 0


def test_relationship_coverage_exact_keys_unique_valid_case_insensitive_and_immutable():
    assets = [{"asset_id": "AST-001"}, {"asset_id": "AST-002"}]
    risks = [{"risk_id": "RSK-001", "affected_asset_id": "ast-001"}]
    controls = [{"control_id": "CTL-001", "mapped_asset_ids": ["ast-001", "AST-001", ""],
                 "mapped_risk_ids": ["rsk-001", "RSK-999"]}]
    evidence = [{"control_id": "ctl-001"}, {"control_id": "CTL-001"}]
    actions = [{"related_risk_id": "RSK-001", "related_control_id": "ctl-001"},
               {"related_risk_id": "", "related_control_id": ""}]
    inputs = [assets, risks, controls, evidence, actions]
    before = deepcopy(inputs)
    result = calculate_relationship_coverage(*inputs)
    assert list(result) == [
        "assets_with_risks", "asset_risk_coverage_pct", "assets_with_controls",
        "asset_control_coverage_pct", "risks_with_controls", "risk_control_coverage_pct",
        "controls_with_evidence", "control_evidence_coverage_pct", "risks_with_remediation",
        "risk_remediation_coverage_pct", "controls_with_remediation",
        "control_remediation_coverage_pct",
    ]
    assert result == {
        "assets_with_risks": 1, "asset_risk_coverage_pct": 50.0,
        "assets_with_controls": 1, "asset_control_coverage_pct": 50.0,
        "risks_with_controls": 1, "risk_control_coverage_pct": 100.0,
        "controls_with_evidence": 1, "control_evidence_coverage_pct": 100.0,
        "risks_with_remediation": 1, "risk_remediation_coverage_pct": 100.0,
        "controls_with_remediation": 1, "control_remediation_coverage_pct": 100.0,
    }
    assert inputs == before


def test_relationship_coverage_empty_parents_return_zero_percentages():
    result = calculate_relationship_coverage([], [], [], [], [])
    assert all(value == 0 for value in result.values())


def test_top_risks_sort_ties_limits_validation_and_copies():
    risks = [
        {"risk_id": "RSK-002", "residual_score": 10, "inherent_score": 15},
        {"risk_id": "RSK-001", "residual_score": 10, "inherent_score": 20},
        {"risk_id": "RSK-003", "residual_score": 10, "inherent_score": 20},
    ]
    before = deepcopy(risks)
    result = get_top_residual_risks(risks, 10)
    assert [item["risk_id"] for item in result] == ["RSK-001", "RSK-003", "RSK-002"]
    assert get_top_residual_risks(risks, 0) == []
    result[0]["risk_id"] = "changed"
    assert risks == before
    with pytest.raises(ValueError):
        get_top_residual_risks(risks, -1)
    for invalid in (1.5, "2", True):
        with pytest.raises(TypeError):
            get_top_residual_risks(risks, invalid)


def test_weak_controls_selection_sort_validation_and_deep_copy():
    controls = [
        {"control_id": "CTL-003", "effectiveness_pct": 90, "implementation_status": "Planned", "mapped_asset_ids": []},
        {"control_id": "CTL-002", "effectiveness_pct": 40, "implementation_status": "Implemented", "mapped_asset_ids": ["AST-001"]},
        {"control_id": "CTL-001", "effectiveness_pct": 80, "implementation_status": "Implemented", "mapped_asset_ids": []},
    ]
    result = get_weak_controls(controls, 50)
    assert [item["control_id"] for item in result] == ["CTL-002", "CTL-003"]
    result[0]["mapped_asset_ids"].append("changed")
    assert controls[1]["mapped_asset_ids"] == ["AST-001"]
    for invalid in (-1, 101):
        with pytest.raises(ValueError):
            get_weak_controls(controls, invalid)
    for invalid in (True, "50"):
        with pytest.raises(TypeError):
            get_weak_controls(controls, invalid)


def test_priority_groups_keys_order_copies_and_invalid_dates(project_data):
    evidence = project_data["evidence"]
    actions = project_data["remediation"]
    evidence_before, actions_before = deepcopy(evidence), deepcopy(actions)
    evidence_result = get_priority_evidence(evidence)
    action_result = get_priority_remediation(actions)
    assert list(evidence_result) == ["expired", "expiring_within_30_days", "under_review", "rejected"]
    assert list(action_result) == ["overdue", "critical_open", "blocked"]
    for group in evidence_result.values():
        positions = [next(i for i, source in enumerate(evidence)
                          if source["evidence_id"] == item["evidence_id"]) for item in group]
        assert positions == sorted(positions)
    evidence_result["expired"][0]["status"] = "changed"
    action_result["overdue"][0]["status"] = "changed"
    assert evidence == evidence_before and actions == actions_before
    with pytest.raises(ValueError):
        get_priority_evidence(evidence, "bad-date")
    with pytest.raises(ValueError):
        get_priority_remediation(actions, "bad-date")


def test_management_insights_exact_keys_reuse_results_and_preserve_inputs(project_data):
    before = deepcopy(project_data)
    result = build_management_insights(
        project_data["assets"], project_data["risks"], project_data["controls"],
        project_data["evidence"], project_data["remediation"])
    assert list(result) == [
        "organization", "reference_date", "risk_summary", "control_summary",
        "evidence_summary", "remediation_summary", "relationship_coverage",
        "top_residual_risks", "weak_controls", "priority_evidence", "priority_remediation",
    ]
    assert result["organization"] == "EagleShield Community Bank"
    assert result["reference_date"] == "2026-08-05"
    assert result["risk_summary"] == summarize_risks(project_data["risks"])
    assert result["control_summary"] == summarize_controls(project_data["controls"])
    assert project_data == before


@pytest.mark.parametrize("function,args", [
    (summarize_risks, ((),)), (summarize_controls, (None,)),
    (summarize_evidence, ({},)), (summarize_remediation, ("actions",)),
])
def test_public_summaries_require_lists(function, args):
    with pytest.raises(TypeError, match="must be a list"):
        function(*args)


def test_public_summaries_require_dictionary_records():
    with pytest.raises(TypeError, match="dictionary"):
        summarize_risks(["not a record"])
