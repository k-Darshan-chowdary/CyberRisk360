"""Executive dashboard for the CyberRisk360 Streamlit interface."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from evidence_register import get_expired_evidence, get_expiring_evidence
from remediation_register import get_overdue_actions


REFERENCE_DATE = "2026-08-05"


def _count_chart(records: list[dict[str, Any]], field: str, title: str):
    """Build a readable count chart for one categorical record field."""
    frame = pd.DataFrame([dict(item) for item in records])
    if frame.empty or field not in frame:
        return None
    counts = frame[field].fillna("Not specified").value_counts().rename_axis(field).reset_index(name="Count")
    figure = px.bar(counts, x=field, y="Count", title=title, text_auto=True)
    figure.update_layout(xaxis_title=field.replace("_", " ").title(), yaxis_title="Records")
    return figure


def _show_table(records: list[dict[str, Any]], columns: list[str], empty_message: str) -> None:
    """Display a compact priority table or a useful empty-state message."""
    if not records:
        st.success(empty_message)
        return
    available = [column for column in columns if column in records[0]]
    frame = pd.DataFrame([dict(item) for item in records])[available]
    frame.columns = [column.replace("_", " ").title() for column in available]
    st.dataframe(frame, width="stretch", hide_index=True)


def render_dashboard(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render summary metrics, charts, and priority-attention tables."""
    st.header("Executive Dashboard")
    st.write("A read-only overview of EagleShield Community Bank's cybersecurity risk posture.")

    assets, risks = data["assets"], data["risks"]
    controls, evidence, actions = data["controls"], data["evidence"], data["remediation"]
    expired = get_expired_evidence(evidence, REFERENCE_DATE)
    expiring = get_expiring_evidence(evidence, days=30, as_of_date=REFERENCE_DATE)
    overdue = get_overdue_actions(actions, REFERENCE_DATE)

    metric_values = [
        ("Total Assets", len(assets)),
        ("Total Risks", len(risks)),
        ("Critical Risks", sum(item["residual_rating"] == "Critical" for item in risks)),
        ("High Risks", sum(item["residual_rating"] == "High" for item in risks)),
        ("Total Controls", len(controls)),
        ("Implemented Controls", sum(item["implementation_status"] == "Implemented" for item in controls)),
        ("Evidence Records", len(evidence)),
        ("Open Remediation Actions", sum(item["status"] not in {"Completed", "Closed", "Cancelled"} for item in actions)),
        ("Overdue Remediation Actions", len(overdue)),
    ]
    for start in range(0, len(metric_values), 5):
        columns = st.columns(min(5, len(metric_values) - start))
        for column, (label, value) in zip(columns, metric_values[start : start + 5]):
            column.metric(label, value)

    st.subheader("Portfolio Distribution")
    chart_specs = [
        (risks, "residual_rating", "Risks by Residual Rating"),
        (risks, "nist_csf_function", "Risks by NIST CSF Function"),
        (controls, "implementation_status", "Controls by Implementation Status"),
        (actions, "status", "Remediation Actions by Status"),
    ]
    for start in range(0, 4, 2):
        left, right = st.columns(2)
        for container, spec in zip((left, right), chart_specs[start : start + 2]):
            figure = _count_chart(*spec)
            if figure is not None:
                container.plotly_chart(figure, width="stretch")

    st.subheader("Priority Attention")
    st.caption(f"Evidence expiration and remediation overdue calculations use {REFERENCE_DATE}.")
    high_risks = [item for item in risks if item["residual_rating"] in {"Critical", "High"}]
    st.markdown("#### Critical and High Residual Risks")
    _show_table(
        high_risks,
        ["risk_id", "risk_title", "residual_score", "residual_rating", "risk_owner", "target_date"],
        "No critical or high residual risks require attention.",
    )
    st.markdown("#### Expired or Expiring Evidence")
    attention_evidence = expired + [item for item in expiring if item not in expired]
    _show_table(
        attention_evidence,
        ["evidence_id", "evidence_name", "control_id", "expiration_date", "status", "evidence_owner"],
        "No evidence is expired or expiring within 30 days.",
    )
    st.markdown("#### Overdue Remediation Actions")
    _show_table(
        overdue,
        ["action_id", "action_title", "priority", "status", "action_owner", "due_date"],
        "No remediation actions are overdue.",
    )
