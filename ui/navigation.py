"""Navigation callbacks shared by the sidebar and guided demo."""

import streamlit as st

PAGE_SLUGS = {
    "Executive Dashboard": "dashboard",
    "Risk Register": "risks",
    "Asset Inventory": "assets",
    "Security Controls": "controls",
    "Control Evidence": "evidence",
    "Remediation Actions": "remediation",
    "Reports & Exports": "reports",
    "System Status": "status",
    "About the Project": "about",
}


def initialize_navigation() -> None:
    """Honor a shared URL when a browser session first opens the app."""
    if "main_navigation" not in st.session_state:
        slug = st.query_params.get("page", "dashboard")
        st.session_state["main_navigation"] = next(
            (page for page, value in PAGE_SLUGS.items() if value == slug), "Executive Dashboard")
        if st.session_state["main_navigation"] == "Risk Register":
            st.session_state["risk_detail"] = st.query_params.get("risk", "RSK-001")


def sync_navigation() -> None:
    """Keep the address bar usable as a share link for the selected route."""
    st.query_params["page"] = PAGE_SLUGS[st.session_state["main_navigation"]]
    st.query_params.pop("risk", None)


def navigate_to(page: str, risk_id: str | None = None) -> None:
    """Select a route before widgets render, optionally opening a risk."""
    st.session_state["main_navigation"] = page
    sync_navigation()
    if risk_id is not None:
        st.session_state["risk_detail"] = risk_id
        st.query_params["risk"] = risk_id
        for key in ("risk_search", "risk_status", "risk_inherent", "risk_residual",
                    "risk_treatment", "risk_nist"):
            st.session_state.pop(key, None)
