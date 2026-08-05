"""Read-only management insights and exports page for CyberRisk360."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from export_manager import (
    assets_to_csv_bytes, build_report_package, controls_to_csv_bytes,
    evidence_to_csv_bytes, generate_management_report_markdown,
    remediation_to_csv_bytes, risks_to_csv_bytes,
)
from reporting_engine import REFERENCE_DATE, build_management_insights


def _metrics(items: list[tuple[str, Any]], count: int) -> None:
    """Display metric items in a compact repeated column layout."""
    columns = st.columns(count)
    for index, (label, value) in enumerate(items):
        columns[index % count].metric(label, value)


def _table(records: list[dict[str, Any]], columns: list[str], empty: str) -> None:
    """Display selected copied fields or a neutral empty state."""
    if not records:
        st.info(empty)
        return
    available = [name for name in columns if name in records[0]]
    frame = pd.DataFrame([dict(record) for record in records])[available]
    frame.columns = [name.replace("_", " ").title() for name in available]
    st.dataframe(frame, width="stretch", hide_index=True)


def _risk_chart(risks: list[dict[str, Any]]):
    frame = pd.DataFrame([dict(item) for item in risks])
    if frame.empty:
        return None
    frame["Risk"] = frame["risk_id"] + " · " + frame["risk_title"].str.slice(0, 38)
    figure = go.Figure()
    figure.add_bar(name="Inherent score", x=frame["Risk"], y=frame["inherent_score"])
    figure.add_bar(name="Residual score", x=frame["Risk"], y=frame["residual_score"])
    figure.update_layout(barmode="group", title="Inherent Versus Residual Risk",
                         xaxis_title="Risk", yaxis_title="Score")
    return figure


def _coverage_chart(coverage: dict[str, int | float]):
    frame = pd.DataFrame({
        "Relationship": ["Asset to Risk", "Asset to Control", "Risk to Control",
                         "Control to Evidence", "Risk to Remediation", "Control to Remediation"],
        "Coverage (%)": [coverage[name] for name in (
            "asset_risk_coverage_pct", "asset_control_coverage_pct", "risk_control_coverage_pct",
            "control_evidence_coverage_pct", "risk_remediation_coverage_pct",
            "control_remediation_coverage_pct")],
    })
    figure = px.bar(frame, x="Relationship", y="Coverage (%)", text_auto=".2f",
                    title="Register Relationship Coverage", range_y=[0, 100])
    figure.update_traces(texttemplate="%{y:.2f}%", textposition="outside")
    return figure


def _remediation_chart(summary: dict[str, int | float]):
    frame = pd.DataFrame({
        "Status": ["Open", "In Progress", "Blocked", "Completed", "Closed", "Cancelled"],
        "Actions": [summary[name] for name in (
            "open_actions", "in_progress_actions", "blocked_actions",
            "completed_actions", "closed_actions", "cancelled_actions")],
    })
    return px.bar(frame, x="Status", y="Actions", text_auto=True,
                  title="Remediation Actions by Status")


def render_reports_page(project_data: dict[str, list[dict[str, Any]]]) -> None:
    """Render management summaries, priority tables, charts, and downloads."""
    st.header("Reports & Exports")
    st.write("Management insights and downloadable reporting packages for EagleShield Community Bank.")
    st.caption(f"Reporting reference date: {REFERENCE_DATE}")
    insights = build_management_insights(
        project_data["assets"], project_data["risks"], project_data["controls"],
        project_data["evidence"], project_data["remediation"], REFERENCE_DATE)
    risk, control = insights["risk_summary"], insights["control_summary"]
    evidence, remediation = insights["evidence_summary"], insights["remediation_summary"]
    coverage = insights["relationship_coverage"]

    st.subheader("Reporting Overview")
    _metrics([
        ("Total Risks", risk["total_risks"]),
        ("Critical and High Risks", risk["critical_risks"] + risk["high_risks"]),
        ("Average Risk Reduction", f"{risk['average_risk_reduction_pct']:.2f}%"),
        ("Implemented Controls", control["implemented_controls"]),
        ("Control Evidence Coverage", f"{coverage['control_evidence_coverage_pct']:.2f}%"),
        ("Overdue Actions", remediation["overdue_actions"]),
    ], 3)

    st.subheader("Management Insights")
    observations = [
        f"{risk['critical_risks'] + risk['high_risks']} Critical or High residual risks are recorded for management review.",
        f"{coverage['control_evidence_coverage_pct']:.2f}% of controls have linked evidence.",
        f"{len(insights['weak_controls'])} controls meet the weak or incomplete reporting criteria.",
        f"{evidence['expired_evidence']} evidence records are expired as of the reference date.",
        f"{remediation['overdue_actions']} remediation actions are overdue.",
        f"Average remediation completion is {remediation['average_completion_pct']:.2f}%.",
    ]
    st.markdown("\n".join(f"- {item}" for item in observations))
    st.caption("These observations support prioritization and do not represent a compliance or security conclusion.")

    st.subheader("Risk Management")
    _metrics([("Open Risks", risk["open_risks"]), ("Critical", risk["critical_risks"]),
              ("High", risk["high_risks"]),
              ("Average Residual Score", risk["average_residual_score"])], 4)
    st.markdown("#### Top Residual Risks")
    _table(insights["top_residual_risks"],
           ["risk_id", "risk_title", "inherent_score", "residual_score", "residual_rating", "risk_owner"],
           "No residual risks are available.")
    risk_figure = _risk_chart(project_data["risks"])
    if risk_figure is not None:
        st.plotly_chart(risk_figure, width="stretch")

    st.subheader("Control and Relationship Coverage")
    _metrics([
        ("Average Control Effectiveness", f"{control['average_effectiveness_pct']:.2f}%"),
        ("Implemented Controls", control["implemented_controls"]),
        ("Weak Controls", len(insights["weak_controls"])),
        ("Asset-Control Coverage", f"{coverage['asset_control_coverage_pct']:.2f}%"),
        ("Risk-Control Coverage", f"{coverage['risk_control_coverage_pct']:.2f}%"),
        ("Control-Evidence Coverage", f"{coverage['control_evidence_coverage_pct']:.2f}%"),
    ], 3)
    st.plotly_chart(_coverage_chart(coverage), width="stretch")

    st.subheader("Evidence Health")
    _metrics([("Total Evidence", evidence["total_evidence"]),
              ("Expired", evidence["expired_evidence"]),
              ("Expiring Within 30 Days", evidence["expiring_within_30_days"]),
              ("Under Review", evidence["under_review_evidence"]),
              ("Rejected", evidence["rejected_evidence"])], 5)
    groups = insights["priority_evidence"]
    attention = groups["expired"] + [item for item in groups["expiring_within_30_days"]
                                      if item not in groups["expired"]]
    _table(attention, ["evidence_id", "evidence_name", "control_id", "expiration_date", "status"],
           "No evidence is expired or expiring within 30 days.")

    st.subheader("Remediation Performance")
    action_groups = insights["priority_remediation"]
    _metrics([("Total Actions", remediation["total_actions"]),
              ("Overdue", remediation["overdue_actions"]),
              ("Critical Open", len(action_groups["critical_open"])),
              ("Blocked", len(action_groups["blocked"])),
              ("Average Completion", f"{remediation['average_completion_pct']:.2f}%")], 5)
    st.plotly_chart(_remediation_chart(remediation), width="stretch")

    report = generate_management_report_markdown(project_data, REFERENCE_DATE)
    st.subheader("Management Report Preview")
    with st.expander("Preview Executive Report"):
        st.text_area("Markdown report", report, height=500, disabled=True,
                     key="management_report_preview")

    st.subheader("Download Center")
    exports = [
        ("Download Executive Report", report, "CyberRisk360_Executive_Report.md", "text/markdown", "download_report"),
        ("Download Asset Inventory", assets_to_csv_bytes(project_data["assets"]), "CyberRisk360_Assets.csv", "text/csv", "download_assets"),
        ("Download Risk Register", risks_to_csv_bytes(project_data["risks"]), "CyberRisk360_Risks.csv", "text/csv", "download_risks"),
        ("Download Security Controls", controls_to_csv_bytes(project_data["controls"]), "CyberRisk360_Controls.csv", "text/csv", "download_controls"),
        ("Download Control Evidence", evidence_to_csv_bytes(project_data["evidence"], REFERENCE_DATE), "CyberRisk360_Evidence.csv", "text/csv", "download_evidence"),
        ("Download Remediation Actions", remediation_to_csv_bytes(project_data["remediation"], REFERENCE_DATE), "CyberRisk360_Remediation.csv", "text/csv", "download_remediation"),
        ("Download Complete Report Package", build_report_package(project_data, REFERENCE_DATE), "CyberRisk360_Report_Package.zip", "application/zip", "download_package"),
    ]
    for start in range(0, len(exports), 3):
        containers = st.columns(3)
        for container, args in zip(containers, exports[start:start + 3]):
            label, payload, filename, mime, key = args
            container.download_button(label, payload, file_name=filename, mime=mime,
                                      key=key, width="stretch")
    st.info("PDF generation will be added after Phase 8. All reports use fictional educational data.")
