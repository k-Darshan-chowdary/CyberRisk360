"""Read-only security-controls page with evidence and action details."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd
import streamlit as st

from control_register import filter_controls, search_controls
from evidence_register import get_evidence_for_control
from remediation_register import get_actions_for_control


DISPLAY_COLUMNS = [
    "control_id", "control_name", "control_type", "nist_csf_function",
    "implementation_status", "control_owner", "effectiveness_pct",
    "mapped_asset_ids", "mapped_risk_ids", "review_date",
]


def _options(records: list[dict[str, Any]], field: str) -> list[str]:
    return ["All", *sorted({str(item[field]) for item in records})]


def _selected(value: str) -> str | None:
    return None if value == "All" else value


def _reset_filters() -> None:
    for key in ("control_search", "control_type", "control_nist", "control_status", "control_owner"):
        st.session_state.pop(key, None)


def _display_frame(records: list[dict[str, Any]], columns: list[str]) -> None:
    """Display copies of control-related records with readable list fields."""
    if not records:
        st.info("No related records are available.")
        return
    copies = deepcopy(records)
    for item in copies:
        for field, value in item.items():
            if isinstance(value, list):
                item[field] = ", ".join(str(entry) for entry in value)
    available = [column for column in columns if column in copies[0]]
    frame = pd.DataFrame(copies)[available]
    frame.columns = [column.replace("_", " ").title() for column in available]
    st.dataframe(frame, width="stretch", hide_index=True)


def render_control_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render searchable controls and their evidence/remediation relationships."""
    controls = data["controls"]
    st.header("Security Controls")
    st.write("Review security safeguards, implementation progress, effectiveness, and relationships.")
    st.metric("Total Controls", len(controls))
    if not controls:
        st.info("No security-control records are available.")
        return

    with st.expander("Search and filters", expanded=True):
        query = st.text_input("Search controls", placeholder="Search by ID, name, owner, mapping, or notes", key="control_search")
        columns = st.columns(4)
        control_type = columns[0].selectbox("Control type", _options(controls, "control_type"), key="control_type")
        nist = columns[1].selectbox("NIST CSF function", _options(controls, "nist_csf_function"), key="control_nist")
        status = columns[2].selectbox("Implementation status", _options(controls, "implementation_status"), key="control_status")
        owner = columns[3].selectbox("Control owner", _options(controls, "control_owner"), key="control_owner")
        st.button("Reset Filters", on_click=_reset_filters, key="reset_control_filters")

    matches = filter_controls(
        search_controls(controls, query), control_type=_selected(control_type),
        nist_csf_function=_selected(nist), implementation_status=_selected(status),
        control_owner=_selected(owner),
    )
    st.caption(f"Showing {len(matches)} of {len(controls)} controls")
    if not matches:
        st.info("No controls match the current search and filters.")
        return
    _display_frame(matches, DISPLAY_COLUMNS)

    st.subheader("Control Details")
    selected_id = st.selectbox("Select a control", [item["control_id"] for item in matches], key="control_detail")
    selected = next(item for item in matches if item["control_id"] == selected_id)
    detail = deepcopy(selected)
    for field, value in detail.items():
        if isinstance(value, list):
            detail[field] = ", ".join(str(entry) for entry in value)
    detail_frame = pd.DataFrame(
        {
            "Field": [key.replace("_", " ").title() for key in detail],
            "Value": [str(value) for value in detail.values()],
        }
    )
    st.dataframe(detail_frame, width="stretch", hide_index=True)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Linked Evidence")
        _display_frame(
            get_evidence_for_control(data["evidence"], selected_id),
            ["evidence_id", "evidence_name", "evidence_type", "status", "expiration_date", "evidence_owner"],
        )
    with right:
        st.markdown("#### Linked Remediation Actions")
        _display_frame(
            get_actions_for_control(data["remediation"], selected_id),
            ["action_id", "action_title", "priority", "status", "due_date", "action_owner"],
        )
