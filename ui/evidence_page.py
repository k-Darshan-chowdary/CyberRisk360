"""Read-only control-evidence page."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd
import streamlit as st

from evidence_register import (
    filter_evidence,
    get_expired_evidence,
    get_expiring_evidence,
    search_evidence,
)


REFERENCE_DATE = "2026-08-05"
DISPLAY_COLUMNS = [
    "evidence_id", "control_id", "evidence_name", "evidence_type", "evidence_owner",
    "collected_date", "review_date", "expiration_date", "evidence_condition",
    "status", "reviewer", "storage_reference",
]


def _options(records: list[dict[str, Any]], field: str) -> list[str]:
    return ["All", *sorted({str(item[field]) for item in records})]


def _selected(value: str) -> str | None:
    return None if value == "All" else value


def _reset_filters() -> None:
    for key in ("evidence_search", "evidence_control", "evidence_type", "evidence_status", "evidence_owner", "evidence_reviewer"):
        st.session_state.pop(key, None)


def _with_condition(
    records: list[dict[str, Any]], expired_ids: set[str], expiring_ids: set[str]
) -> list[dict[str, Any]]:
    """Add a display-only condition to independent record copies."""
    copies = deepcopy(records)
    for item in copies:
        evidence_id = str(item["evidence_id"])
        if evidence_id in expired_ids:
            item["evidence_condition"] = "Expired"
        elif evidence_id in expiring_ids:
            item["evidence_condition"] = "Expiring Within 30 Days"
        else:
            item["evidence_condition"] = "Active"
    return copies


def render_evidence_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render evidence metrics, deterministic conditions, search, and filters."""
    evidence = data["evidence"]
    st.header("Control Evidence")
    st.write("Review the records used to demonstrate that security controls are operating.")
    st.caption(f"Expiration calculations use the fixed reference date {REFERENCE_DATE}.")
    expired = get_expired_evidence(evidence, REFERENCE_DATE)
    expiring = get_expiring_evidence(evidence, days=30, as_of_date=REFERENCE_DATE)
    expired_ids = {item["evidence_id"] for item in expired}
    expiring_ids = {item["evidence_id"] for item in expiring}
    metric_columns = st.columns(4)
    metric_columns[0].metric("Total Evidence", len(evidence))
    metric_columns[1].metric("Current Evidence", sum(item["status"] == "Current" for item in evidence))
    metric_columns[2].metric("Expired Evidence", len(expired))
    metric_columns[3].metric("Expiring Soon", len(expiring))
    if not evidence:
        st.info("No evidence records are available.")
        return

    with st.expander("Search and filters", expanded=True):
        query = st.text_input("Search evidence", placeholder="Search by ID, control, name, owner, or reference", key="evidence_search")
        columns = st.columns(5)
        control_id = columns[0].selectbox("Control ID", _options(evidence, "control_id"), key="evidence_control")
        evidence_type = columns[1].selectbox("Evidence type", _options(evidence, "evidence_type"), key="evidence_type")
        status = columns[2].selectbox("Stored status", _options(evidence, "status"), key="evidence_status")
        owner = columns[3].selectbox("Evidence owner", _options(evidence, "evidence_owner"), key="evidence_owner")
        reviewer = columns[4].selectbox("Reviewer", _options(evidence, "reviewer"), key="evidence_reviewer")
        st.button("Reset Filters", on_click=_reset_filters, key="reset_evidence_filters")

    matches = filter_evidence(
        search_evidence(evidence, query), control_id=_selected(control_id),
        evidence_type=_selected(evidence_type), status=_selected(status),
        evidence_owner=_selected(owner), reviewer=_selected(reviewer),
    )
    st.caption(f"Showing {len(matches)} of {len(evidence)} evidence records")
    if not matches:
        st.info("No evidence records match the current search and filters.")
        return
    display_records = _with_condition(matches, expired_ids, expiring_ids)
    frame = pd.DataFrame(display_records)[DISPLAY_COLUMNS]
    frame.columns = [column.replace("_", " ").title() for column in DISPLAY_COLUMNS]
    st.dataframe(frame, width="stretch", hide_index=True)
