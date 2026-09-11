"""About page for the CyberRisk360 GRC reference application."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_about_page(data: dict[str, list[dict[str, Any]]]) -> None:
    """Explain the project, architecture, methods, phases, and limitations."""
    del data  # The route signature stays consistent; this page does not need record data.
    st.header("About the Project")
    st.write(
        "CyberRisk360 connects asset inventory, cyber risk assessment, control mapping, "
        "evidence metadata, remediation, and executive reporting in a read-only GRC application."
    )
    st.info(
        "EagleShield Community Bank is fictional. All project data is fictional, and no "
        "real banking, customer, employee, or personal data is used."
    )

    st.subheader("Purpose and Framework")
    st.write(
        "The project demonstrates how an organization can inventory assets, assess cyber risk, "
        "map controls, review evidence metadata, and track remediation. Risks and controls use "
        "primary function labels from NIST Cybersecurity Framework (CSF) 2.0: Govern, Identify, "
        "Protect, Detect, Respond, and Recover. These labels do not constitute a complete "
        "framework mapping or compliance assessment."
    )

    st.subheader("Major Modules")
    st.markdown(
        "- **Risk engine:** calculates inherent and residual risk.\n"
        "- **Risk register:** validates and manages assessed risks.\n"
        "- **Asset register:** inventories the systems and services in scope.\n"
        "- **Control register:** maps safeguards to assets and risks.\n"
        "- **Evidence register:** tracks evidence metadata, storage references, and expiration.\n"
        "- **Remediation register:** tracks corrective actions, ownership, and due dates.\n"
        "- **Reporting engine:** creates executive summaries, coverage measures, and priority insights.\n"
        "- **Export manager:** generates Markdown, CSV, and ZIP reports entirely in memory.\n"
        "- **Reports & Exports page:** previews management reporting and provides downloads.\n"
        "- **Integrity guard:** detects sample-data changes against a versioned SHA-256 manifest.\n"
        "- **Project health:** checks files, data, relationships, exports, configuration, and dependencies.\n"
        "- **System Status page:** presents read-only health and deployment-readiness results.\n"
        "- **Streamlit UI:** provides read-only navigation, metrics, charts, filters, and details."
    )

    st.subheader("Risk-Scoring Methodology")
    st.write(
        "Inherent risk is likelihood multiplied by impact. Residual risk reduces that score by "
        "the stated control-effectiveness percentage. The risk engine then assigns consistent "
        "rating bands to the calculated scores. Effectiveness is a risk-level assessment input; "
        "it is not automatically calculated from linked controls or evidence."
    )

    st.subheader("Completed Phases")
    st.write(
        "Phases 0 through 8 cover project foundation, risk scoring, the risk register, asset and "
        "control relationships, evidence, remediation, the read-only Streamlit interface, and "
        "management reporting with downloadable Markdown, CSV, and ZIP formats. Phase 8 adds "
        "integrity verification, project health checks, the System Status page, safe Streamlit "
        "configuration, pinned dependencies, GitHub Actions continuous integration, and "
        "deployment-readiness documentation."
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
        "Phase 8 remains intentionally read-only. The project has no authentication, authorization "
        "system, production database, audit-log storage, encryption-at-rest implementation, "
        "penetration test, or formal compliance certification. It uses no real banking data, and "
        "public deployment is not performed automatically. CSV storage and the fixed demonstration "
        "date of 2026-08-05 supports reproducible demonstrations. Evidence attachments are not "
        "stored or collected, and the application is not suitable for a production banking system."
    )
