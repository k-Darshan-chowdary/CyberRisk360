"""Read-only risk-register page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from risk_register import filter_risks, search_risks


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


def render_risk_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render searchable, filterable risk data without edit controls."""
    risks = data["risks"]
    st.header("Risk Register")
    st.write("Review identified cybersecurity risks, calculated scores, treatments, and ownership.")
    st.metric("Total Risks", len(risks))
    if not risks:
        st.info("No risk records are available.")
        return

    with st.expander("Search and filters", expanded=True):
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
    st.dataframe(frame, width="stretch", hide_index=True)
