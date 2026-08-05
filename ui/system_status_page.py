"""Read-only Streamlit status and deployment-readiness page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from integrity_guard import verify_sample_data_integrity
from project_health import format_health_report_markdown, run_project_health_check

REFERENCE_DATE = "2026-08-05"


@st.cache_data(show_spinner=False)
def _load_status_reports() -> tuple[dict[str, object], dict[str, object]]:
    """Run and cache read-only checks for a responsive status page."""
    return run_project_health_check(REFERENCE_DATE), verify_sample_data_integrity()


def render_system_status_page() -> None:
    """Render technical health and integrity information without changing files."""
    st.header("System Status & Readiness")
    st.write("Read-only technical health, integrity, and deployment-readiness checks for CyberRisk360.")
    st.caption(f"Deterministic reference date: {REFERENCE_DATE}")
    health, integrity = _load_status_reports()

    st.subheader("Overall Status")
    columns = st.columns(5)
    values = (("Overall Status", health["overall_status"]),
              ("Passed Checks", health["passed_checks"]),
              ("Failed Checks", health["failed_checks"]),
              ("Protected Data Files", integrity["total_files"]),
              ("Verified Data Files", integrity["verified_files"]))
    for column, (label, value) in zip(columns, values):
        column.metric(label, value)

    st.subheader("Health-Check Results")
    frame = pd.DataFrame([{"Category": check["category"], "Check": check["name"],
                           "Status": check["status"], "Details": check["details"]}
                          for check in health["checks"]])
    st.dataframe(frame, hide_index=True, width="stretch")

    st.subheader("Sample-Data Integrity")
    integrity_frame = pd.DataFrame([{"Filename": result["file"], "Exists": result["exists"],
                                     "Integrity Result": "Pass" if result["matches"] else "Fail"}
                                    for result in integrity["results"]])
    st.dataframe(integrity_frame, hide_index=True, width="stretch")
    with st.expander("Developer hash details"):
        for result in integrity["results"]:
            st.code(f"{result['file']}\nExpected: {result['expected_sha256']}\nActual:   {result['actual_sha256'] or '(missing)'}")

    st.subheader("Deployment Readiness Checklist")
    statuses = {check["check_id"]: check["status"] for check in health["checks"]}
    checklist = (("Required files present", statuses.get("required_files")),
                 ("Sample data loads", statuses.get("data_loading")),
                 ("Relationships valid", statuses.get("relationship_integrity")),
                 ("Sample data integrity passes", statuses.get("sample_integrity")),
                 ("Reports generate in memory", statuses.get("reporting_exports")),
                 ("Streamlit configuration passes", statuses.get("streamlit_config")),
                 ("Dependencies are pinned", statuses.get("dependency_pinning")))
    st.markdown("**Automated checks**")
    st.markdown("\n".join(f"- {'[x]' if status == 'Pass' else '[ ]'} {label} — {status}"
                          for label, status in checklist))
    st.markdown("**Manual release action**")
    st.markdown("- [ ] Automated tests must pass before release (confirm in local or GitHub Actions results).")

    with st.expander("Health Report Preview"):
        st.text_area("Markdown health report", format_health_report_markdown(health), height=420,
                     disabled=True, key="phase8_health_report_preview")
    if st.button("Run Health Checks Again", key="phase8_refresh_health_checks", width="stretch"):
        _load_status_reports.clear()
        st.rerun()

    st.info("All data is fictional. This status page is an educational readiness check; it is not "
            "a penetration test, a compliance certification, or authorization to process real banking data.")
