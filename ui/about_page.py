"""About page for the CyberRisk360 portfolio project."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_about_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Explain the project, architecture, methods, phases, and limitations."""
    del data  # The route signature stays consistent; this page does not need record data.
    st.header("About the Project")
    st.write("CyberRisk360 is a beginner-friendly governance, risk, and compliance portfolio project.")
    st.info(
        "EagleShield Community Bank is fictional. All project data is fictional, and no "
        "real banking, customer, employee, or personal data is used."
    )

    st.subheader("Purpose and Framework")
    st.write(
        "The project demonstrates how an organization can inventory assets, assess cyber risk, "
        "map controls, retain evidence, and track remediation. Its organization follows the six "
        "functions of NIST Cybersecurity Framework (CSF) 2.0: Govern, Identify, Protect, Detect, "
        "Respond, and Recover."
    )

    st.subheader("Major Modules")
    st.markdown(
        "- **Risk engine:** calculates inherent and residual risk.\n"
        "- **Risk register:** validates and manages assessed risks.\n"
        "- **Asset register:** inventories the systems and services in scope.\n"
        "- **Control register:** maps safeguards to assets and risks.\n"
        "- **Evidence register:** tracks proof of control operation and expiration.\n"
        "- **Remediation register:** tracks corrective actions, ownership, and due dates.\n"
        "- **Reporting engine:** creates executive summaries, coverage measures, and priority insights.\n"
        "- **Export manager:** generates Markdown, CSV, and ZIP reports entirely in memory.\n"
        "- **Reports & Exports page:** previews management reporting and provides downloads.\n"
        "- **Streamlit UI:** provides read-only navigation, metrics, charts, filters, and details."
    )

    st.subheader("Risk-Scoring Methodology")
    st.write(
        "Inherent risk is likelihood multiplied by impact. Residual risk reduces that score by "
        "the stated control-effectiveness percentage. The risk engine then assigns consistent "
        "rating bands to the calculated scores."
    )

    st.subheader("Completed Phases")
    st.write(
        "Phases 0 through 7 cover project foundation, risk scoring, the risk register, asset and "
        "control relationships, evidence, remediation, the read-only Streamlit interface, and "
        "management reporting with downloadable Markdown, CSV, and ZIP formats."
    )

    st.subheader("Project Architecture")
    st.code(
        "Sample CSV Data\n"
        "       |\n"
        "       v\n"
        "Backend Register Modules\n"
        "       |\n"
        "       v\n"
        "Validation and Business Logic\n"
        "       |\n"
        "       v\n"
        "Central UI Data Loader\n"
        "       |\n"
        "       v\n"
        "Streamlit Pages\n"
        "       |\n"
        "       v\n"
        "Dashboard, Tables, Filters and Details",
        language="text",
    )

    st.subheader("Technologies Used")
    st.write("Python · Streamlit · Pandas · Plotly · Pytest · Git and GitHub · CSV data storage")

    st.subheader("Current Limitations")
    st.write(
        "Phase 7 is intentionally read-only. PDF reporting remains a future feature after Phase 8. "
        "The project does not include add, edit, or delete forms; "
        "authentication; database storage; file uploads; email alerts; or production deployment. "
        "CSV storage and the fixed demonstration date are appropriate for a portfolio exercise, "
        "but not for a production banking system."
    )
