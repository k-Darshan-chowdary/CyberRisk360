"""Read-only risk-register page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from risk_register import filter_risks, search_risks
from control_register import get_controls_for_risk
from evidence_register import get_expired_evidence, get_expiring_evidence
from remediation_register import get_overdue_actions
from reporting_engine import REFERENCE_DATE
from risk_engine import assess_risk
from ui.navigation import navigate_to


DISPLAY_COLUMNS = [
    "risk_id", "risk_title", "affected_asset_id", "likelihood", "impact",
    "inherent_score", "inherent_rating", "control_effectiveness_pct",
    "residual_score", "residual_rating", "treatment", "status", "risk_owner",
    "target_date", "nist_csf_function",
]


def _options(records: list[dict[str, Any]], field: str) -> list[str]:
    return ["All", *sorted({str(item[field]) for item in records})]


def _reset_filters() -> None:
    for key in ("risk_search", "risk_status", "risk_inherent", "risk_residual", "risk_treatment", "risk_nist"):
        st.session_state.pop(key, None)


def _selected(value: str) -> str | None:
    return None if value == "All" else value


def _table(records: list[dict[str, Any]], columns: list[str], empty: str) -> None:
    if not records:
        st.info(empty)
        return
    frame = pd.DataFrame(records)[columns]
    frame.columns = [column.replace("_", " ").title() for column in columns]
    st.dataframe(frame, width="stretch", hide_index=True)


def _reset_scenario(risk_id: str) -> None:
    for field in ("likelihood", "impact", "effectiveness"):
        st.session_state.pop(f"scenario_{risk_id}_{field}", None)


def _render_risk_details(data: dict[str, list[dict[str, Any]]], matches: list[dict[str, Any]]) -> None:
    st.subheader("Explore a risk")
    ids = [item["risk_id"] for item in matches]
    titles = {item["risk_id"]: item["risk_title"] for item in matches}
    if st.session_state.get("risk_detail") not in ids:
        st.session_state["risk_detail"] = ids[0]
    selected_id = st.selectbox("Select a risk", ids, key="risk_detail",
                               format_func=lambda value: f"{value} · {titles[value]}")
    st.query_params["page"] = "risks"
    st.query_params["risk"] = selected_id
    st.caption("Copy the browser URL to share this recorded risk. Scenario assumptions are not included in the link.")
    risk = next(item for item in matches if item["risk_id"] == selected_id)
    st.write(f"**{risk['risk_title']}**")
    st.write(f"**Threat:** {risk['threat']}  \n**Vulnerability:** {risk['vulnerability']}")
    st.caption(f"Owner: {risk['risk_owner']} · Treatment: {risk['treatment']} · Status: {risk['status']}")
    left, right = st.columns(2)
    left.metric("Recorded inherent risk", f"{risk['inherent_score']} · {risk['inherent_rating']}")
    right.metric("Recorded residual risk", f"{risk['residual_score']:.2f} · {risk['residual_rating']}")

    with st.expander("What if the assumptions change?", expanded=True):
        st.write("Adjust the assessment inputs to compare a hypothetical outcome with this recorded risk.")
        columns = st.columns(3)
        likelihood = columns[0].slider("Scenario likelihood", 1, 5, int(risk["likelihood"]),
                                       key=f"scenario_{selected_id}_likelihood")
        impact = columns[1].slider("Scenario impact", 1, 5, int(risk["impact"]),
                                   key=f"scenario_{selected_id}_impact")
        effectiveness = columns[2].slider(
            "Scenario control effectiveness (%)", 0.0, 100.0, float(risk["control_effectiveness_pct"]),
            step=1.0, key=f"scenario_{selected_id}_effectiveness")
        scenario = assess_risk(likelihood, impact, effectiveness)
        left, right = st.columns(2)
        left.metric("Scenario inherent risk", f"{scenario['inherent_score']} · {scenario['inherent_rating']}")
        right.metric("Scenario residual risk", f"{scenario['residual_score']:.2f} · {scenario['residual_rating']}",
                     delta=f"{scenario['residual_score'] - risk['residual_score']:+.2f} vs recorded", delta_color="inverse")
        st.caption(
            f"{likelihood} × {impact} × (1 − {effectiveness:g}/100) = {scenario['residual_score']:.2f}. "
            "Hypothetical only; registers and reports keep the recorded assessment. "
            "Effectiveness is an assessment estimate, not calculated from linked controls or evidence."
        )
        st.button("Reset scenario", on_click=_reset_scenario, args=(selected_id,), key="reset_scenario")

    st.markdown("#### 1. Affected asset")
    _table([item for item in data["assets"] if item["asset_id"] == risk["affected_asset_id"]],
           ["asset_id", "asset_name", "business_criticality", "asset_owner"], "No affected asset was found.")
    controls = get_controls_for_risk(data["controls"], selected_id)
    control_ids = {item["control_id"] for item in controls}
    st.markdown("#### 2. Controls mapped to this risk")
    _table(controls, ["control_id", "control_name", "implementation_status", "effectiveness_pct"],
           "No controls are mapped directly to this risk.")
    evidence = [item for item in data["evidence"] if item["control_id"] in control_ids]
    expired_ids = {item["evidence_id"] for item in get_expired_evidence(evidence, REFERENCE_DATE)}
    expiring_ids = {item["evidence_id"] for item in get_expiring_evidence(evidence, 30, REFERENCE_DATE)}
    evidence_rows = [dict(item, condition=("Expired" if item["evidence_id"] in expired_ids else
                                         "Expiring within 30 days" if item["evidence_id"] in expiring_ids else
                                         "Active")) for item in evidence]
    st.markdown("#### 3. Evidence supporting those controls")
    st.caption(f"Date conditions use {REFERENCE_DATE}. Stored review status is separate from expiration.")
    _table(evidence_rows, ["evidence_id", "control_id", "evidence_name", "status", "condition", "expiration_date"],
           "No evidence metadata is linked to these controls.")
    actions = [item for item in data["remediation"] if item["related_risk_id"] == selected_id or
               item["related_control_id"] in control_ids]
    overdue_ids = {item["action_id"] for item in get_overdue_actions(actions, REFERENCE_DATE)}
    action_rows = [dict(item, overdue="Yes" if item["action_id"] in overdue_ids else "No",
                        relationship="Risk" if item["related_risk_id"] == selected_id else "Mapped control")
                   for item in actions]
    st.markdown("#### 4. Remediation for this risk or its mapped controls")
    st.caption("Control-linked actions can address another risk. Completed actions remain overdue until Closed or Cancelled.")
    _table(action_rows, ["action_id", "action_title", "relationship", "priority", "status", "due_date", "overdue"],
           "No remediation actions are linked to this risk or its mapped controls.")
    st.button("Continue to executive reports", on_click=navigate_to,
              args=("Reports & Exports",), key="risk_to_reports")


def render_risk_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render searchable, filterable risk data without edit controls."""
    risks = data["risks"]
    st.header("Risk Register")
    st.write("Review identified cybersecurity risks, calculated scores, treatments, and ownership.")
    st.metric("Total Risks", len(risks))
    if not risks:
        st.info("No risk records are available.")
        return

    with st.expander("Search and filters", expanded=False):
        query = st.text_input("Search risks", placeholder="Search by ID, title, threat, owner, or asset", key="risk_search")
        columns = st.columns(5)
        status = columns[0].selectbox("Status", _options(risks, "status"), key="risk_status")
        inherent = columns[1].selectbox("Inherent rating", _options(risks, "inherent_rating"), key="risk_inherent")
        residual = columns[2].selectbox("Residual rating", _options(risks, "residual_rating"), key="risk_residual")
        treatment = columns[3].selectbox("Treatment", _options(risks, "treatment"), key="risk_treatment")
        nist = columns[4].selectbox("NIST CSF function", _options(risks, "nist_csf_function"), key="risk_nist")
        st.button("Reset Filters", on_click=_reset_filters, key="reset_risk_filters")

    matches = search_risks(risks, query)
    matches = filter_risks(
        matches,
        status=_selected(status),
        inherent_rating=_selected(inherent),
        residual_rating=_selected(residual),
        treatment=_selected(treatment),
        nist_csf_function=_selected(nist),
    )
    st.caption(f"Showing {len(matches)} of {len(risks)} risks")
    if not matches:
        st.info("No risks match the current search and filters.")
        return
    frame = pd.DataFrame([dict(item) for item in matches])[DISPLAY_COLUMNS]
    frame.columns = [column.replace("_", " ").title() for column in DISPLAY_COLUMNS]
    with st.expander("View filtered risk register", expanded=False):
        st.dataframe(frame, width="stretch", hide_index=True)
    _render_risk_details(data, matches)
