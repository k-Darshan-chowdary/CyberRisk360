"""Reliable in-process Streamlit smoke coverage for all nine routes."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from integrity_guard import calculate_file_sha256, load_integrity_manifest, PROJECT_ROOT


ROUTES = ("Executive Dashboard", "Risk Register", "Asset Inventory", "Security Controls",
          "Control Evidence", "Remediation Actions", "Reports & Exports", "System Status",
          "About the Project")


def _start():
    return AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=20).run()


def test_app_starts_without_uncaught_exceptions():
    app = _start()
    assert not app.exception


@pytest.mark.parametrize("route", ROUTES)
def test_every_navigation_route_renders_without_writes(route):
    manifest = load_integrity_manifest()
    before = {name: calculate_file_sha256(PROJECT_ROOT / name) for name in manifest["files"]}
    app = _start()
    app.radio(key="main_navigation").set_value(route).run()
    assert not app.exception
    after = {name: calculate_file_sha256(PROJECT_ROOT / name) for name in manifest["files"]}
    assert before == after


def test_system_status_title_and_about_phase_information():
    app = _start()
    app.radio(key="main_navigation").set_value("System Status").run()
    assert any("System Status & Readiness" in item.value for item in app.header)
    app.radio(key="main_navigation").set_value("About the Project").run()
    assert "Phase 8" in " ".join(item.value for item in app.markdown)


def test_reports_page_keeps_download_controls():
    app = _start()
    app.radio(key="main_navigation").set_value("Reports & Exports").run()
    assert len(app.get("download_button")) == 7
