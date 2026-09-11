"""Streamlit entry point for the CyberRisk360 read-only interface."""

from __future__ import annotations

import streamlit as st

from ui.about_page import render_about_page
from ui.asset_page import render_asset_page
from ui.control_page import render_control_page
from ui.dashboard import render_dashboard
from ui.data_loader import load_all_project_data
from ui.evidence_page import render_evidence_page
from ui.remediation_page import render_remediation_page
from ui.reports_page import render_reports_page
from ui.risk_page import render_risk_page
from ui.system_status_page import render_system_status_page


st.set_page_config(
    page_title="CyberRisk360",
    page_icon="🛡️",
    layout="wide",
)


PAGES = {
    "Executive Dashboard": render_dashboard,
    "Risk Register": render_risk_page,
    "Asset Inventory": render_asset_page,
    "Security Controls": render_control_page,
    "Control Evidence": render_evidence_page,
    "Remediation Actions": render_remediation_page,
    "Reports & Exports": render_reports_page,
    "System Status": lambda _data: render_system_status_page(),
    "About the Project": render_about_page,
}


def main() -> None:
    """Load project data and route the selected sidebar page."""
    st.title("CyberRisk360")
    st.caption("GRC Risk Assessment and Compliance Dashboard")
    st.write("**EagleShield Community Bank**")

    st.sidebar.title("CyberRisk360")
    st.sidebar.caption("EagleShield Community Bank")
    selected_page = st.sidebar.radio("Navigation", list(PAGES), key="main_navigation")
    st.sidebar.divider()
    st.sidebar.caption("Read-only GRC demo · Synthetic data")

    try:
        project_data = load_all_project_data()
        if not any(project_data.values()):
            st.warning("No project data is available to display.")
            return
        PAGES[selected_page](project_data)
    except FileNotFoundError:
        st.error(
            "A required project data file could not be found. Please confirm that all "
            "sample CSV files are present in the data folder."
        )
    except ValueError:
        st.error(
            "A project data file could not be read because its contents are invalid. "
            "Please validate the sample CSV files and try again."
        )
    except Exception as error:  # Streamlit must show a friendly failure for unexpected issues.
        st.error("CyberRisk360 could not load the requested page. Please try again.")
        with st.expander("Developer details"):
            st.caption(f"Unexpected error type: {type(error).__name__}")


if __name__ == "__main__":
    main()
