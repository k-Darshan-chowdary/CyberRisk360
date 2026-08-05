"""Read-only remediation-actions page."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd
import streamlit as st

from remediation_register import filter_actions, get_overdue_actions, search_actions


REFERENCE_DATE = "2026-08-05"
DISPLAY_COLUMNS = [
    "action_id", "action_title", "related_risk_id", "related_control_id",
    "action_owner", "priority", "status", "created_date", "due_date",
    "completion_pct", "overdue", "closure_date", "verification_notes",
]


def _options(records: list[dict[str, Any]], field: str) -> list[str]:
    return ["All", *sorted({str(item[field]) for item in records if str(item[field])})]


def _selected(value: str) -> str | None:
    return None if value == "All" else value


def _reset_filters() -> None:
    for key in ("action_search", "action_priority", "action_status", "action_owner", "action_risk", "action_control"):
        st.session_state.pop(key, None)


def render_remediation_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render remediation metrics and a deterministic overdue indicator."""
    actions = data["remediation"]
    st.header("Remediation Actions")
    st.write("Track the read-only action plan used to reduce risks and improve controls.")
    st.caption(f"Overdue calculations use the fixed reference date {REFERENCE_DATE}.")
    overdue_actions = get_overdue_actions(actions, REFERENCE_DATE)
    overdue_ids = {str(item["action_id"]) for item in overdue_actions}
    metric_columns = st.columns(5)
    metric_columns[0].metric("Total Actions", len(actions))
    metric_columns[1].metric("Open", sum(item["status"] == "Open" for item in actions))
    metric_columns[2].metric("In Progress", sum(item["status"] == "In Progress" for item in actions))
    metric_columns[3].metric("Completed or Closed", sum(item["status"] in {"Completed", "Closed"} for item in actions))
    metric_columns[4].metric("Overdue", len(overdue_actions))
    if not actions:
        st.info("No remediation actions are available.")
        return

    with st.expander("Search and filters", expanded=True):
        query = st.text_input("Search actions", placeholder="Search by ID, title, owner, risk, control, or notes", key="action_search")
        columns = st.columns(5)
        priority = columns[0].selectbox("Priority", _options(actions, "priority"), key="action_priority")
        status = columns[1].selectbox("Status", _options(actions, "status"), key="action_status")
        owner = columns[2].selectbox("Action owner", _options(actions, "action_owner"), key="action_owner")
        risk_id = columns[3].selectbox("Related risk ID", _options(actions, "related_risk_id"), key="action_risk")
        control_id = columns[4].selectbox("Related control ID", _options(actions, "related_control_id"), key="action_control")
        st.button("Reset Filters", on_click=_reset_filters, key="reset_action_filters")

    matches = filter_actions(
        search_actions(actions, query), priority=_selected(priority), status=_selected(status),
        action_owner=_selected(owner), related_risk_id=_selected(risk_id),
        related_control_id=_selected(control_id),
    )
    st.caption(f"Showing {len(matches)} of {len(actions)} remediation actions")
    if not matches:
        st.info("No remediation actions match the current search and filters.")
        return
    display_records = deepcopy(matches)
    for item in display_records:
        item["overdue"] = "Yes" if str(item["action_id"]) in overdue_ids else "No"
    frame = pd.DataFrame(display_records)[DISPLAY_COLUMNS]
    frame.columns = [column.replace("_", " ").title() for column in DISPLAY_COLUMNS]
    st.dataframe(frame, width="stretch", hide_index=True)
