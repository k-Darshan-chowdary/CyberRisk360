"""Read-only asset-inventory page with relationship details."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from asset_register import filter_assets, search_assets
from control_register import get_controls_for_asset


DISPLAY_COLUMNS = [
    "asset_id", "asset_name", "asset_type", "asset_owner", "department",
    "data_classification", "business_criticality", "location", "description",
]


def _options(records: list[dict[str, Any]], field: str) -> list[str]:
    return ["All", *sorted({str(item[field]) for item in records})]


def _selected(value: str) -> str | None:
    return None if value == "All" else value


def _reset_filters() -> None:
    for key in ("asset_search", "asset_type", "asset_department", "asset_classification", "asset_criticality", "asset_location"):
        st.session_state.pop(key, None)


def _display_records(records: list[dict[str, Any]], columns: list[str]) -> None:
    if not records:
        st.info("No related records are available.")
        return
    available = [column for column in columns if column in records[0]]
    frame = pd.DataFrame([dict(item) for item in records])[available]
    frame.columns = [column.replace("_", " ").title() for column in available]
    st.dataframe(frame, width="stretch", hide_index=True)


def render_asset_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Render the asset inventory and cross-module asset details."""
    assets = data["assets"]
    st.header("Asset Inventory")
    st.write("Explore the fictional bank's technology assets and their mapped risks and controls.")
    st.metric("Total Assets", len(assets))
    if not assets:
        st.info("No asset records are available.")
        return

    with st.expander("Search and filters", expanded=True):
        query = st.text_input("Search assets", placeholder="Search by ID, name, owner, type, or description", key="asset_search")
        columns = st.columns(5)
        asset_type = columns[0].selectbox("Asset type", _options(assets, "asset_type"), key="asset_type")
        department = columns[1].selectbox("Department", _options(assets, "department"), key="asset_department")
        classification = columns[2].selectbox("Data classification", _options(assets, "data_classification"), key="asset_classification")
        criticality = columns[3].selectbox("Business criticality", _options(assets, "business_criticality"), key="asset_criticality")
        location = columns[4].selectbox("Location", _options(assets, "location"), key="asset_location")
        st.button("Reset Filters", on_click=_reset_filters, key="reset_asset_filters")

    matches = filter_assets(
        search_assets(assets, query),
        asset_type=_selected(asset_type), department=_selected(department),
        data_classification=_selected(classification), business_criticality=_selected(criticality),
        location=_selected(location),
    )
    st.caption(f"Showing {len(matches)} of {len(assets)} assets")
    if not matches:
        st.info("No assets match the current search and filters.")
        return
    _display_records(matches, DISPLAY_COLUMNS)

    st.subheader("Asset Details")
    selected_id = st.selectbox("Select an asset", [item["asset_id"] for item in matches], key="asset_detail")
    asset = next(item for item in matches if item["asset_id"] == selected_id)
    detail_frame = pd.DataFrame(
        {"Field": [key.replace("_", " ").title() for key in asset], "Value": list(asset.values())}
    )
    st.dataframe(detail_frame, width="stretch", hide_index=True)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Risks Affecting This Asset")
        related_risks = [item for item in data["risks"] if item["affected_asset_id"] == selected_id]
        _display_records(related_risks, ["risk_id", "risk_title", "residual_rating", "status", "risk_owner"])
    with right:
        st.markdown("#### Controls Mapped to This Asset")
        related_controls = get_controls_for_asset(data["controls"], selected_id)
        _display_records(related_controls, ["control_id", "control_name", "implementation_status", "effectiveness_pct", "control_owner"])
