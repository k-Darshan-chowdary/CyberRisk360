"""Exercise the visitor journey and prevent hypothetical inputs from changing data."""

from copy import deepcopy

from streamlit.testing.v1 import AppTest

from integrity_guard import PROJECT_ROOT, calculate_file_sha256, load_integrity_manifest
from project_health import load_all_project_data


def _app(**query):
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=20)
    app.query_params.update(query)
    return app.run()


def test_guided_tour_opens_phishing_relationships_and_reports():
    app = _app()
    app.button(key="start_demo").click().run()
    assert not app.exception and not app.error
    assert app.radio(key="main_navigation").value == "Risk Register"
    assert app.selectbox(key="risk_detail").value == "RSK-001"
    assert app.query_params["risk"] == ["RSK-001"]
    # The full register plus asset, controls, evidence, and actions.
    frames = app.dataframe
    assert "AST-003" in frames[1].value["Asset Id"].tolist()
    assert "CTL-002" in frames[2].value["Control Id"].tolist()
    assert "EVD-002" in frames[3].value["Evidence Id"].tolist()
    action_ids = frames[4].value["Action Id"].tolist()
    assert "ACT-001" in action_ids
    assert len(action_ids) == len(set(action_ids))
    app.button(key="risk_to_reports").click().run()
    assert app.radio(key="main_navigation").value == "Reports & Exports"
    assert not app.exception and not app.error
    assert len(app.get("download_button")) == 7


def test_scenario_endpoints_reset_and_sample_files_are_unchanged():
    manifest = load_integrity_manifest()
    before = {name: calculate_file_sha256(PROJECT_ROOT / name) for name in manifest["files"]}
    recorded = deepcopy(load_all_project_data())
    app = _app(page="risks", risk="RSK-001")
    effectiveness = "scenario_RSK-001_effectiveness"
    app.slider(key=effectiveness).set_value(0.0).run()
    assert next(item.value for item in app.metric if item.label == "Scenario residual risk") == "16.00 · High"
    app.slider(key=effectiveness).set_value(100.0).run()
    assert next(item.value for item in app.metric if item.label == "Scenario residual risk") == "0.00 · Low"
    app.button(key="reset_scenario").click().run()
    assert app.slider(key=effectiveness).value == 60.0
    assert not app.exception and not app.error
    assert load_all_project_data() == recorded
    assert before == {name: calculate_file_sha256(PROJECT_ROOT / name) for name in manifest["files"]}


def test_shared_risk_url_filters_and_invalid_links_recover():
    app = _app(page="risks", risk="RSK-004")
    assert app.selectbox(key="risk_detail").value == "RSK-004"
    app.text_input(key="risk_search").set_value("RSK-002").run()
    assert app.selectbox(key="risk_detail").value == "RSK-002"
    assert not app.exception and not app.error
    app.text_input(key="risk_search").set_value("no matching risk").run()
    assert not app.exception and not app.error
    assert any("No risks match" in item.value for item in app.info)
    app = _app(page="risks", risk="RSK-999")
    assert app.selectbox(key="risk_detail").value == "RSK-001"
    assert not app.exception and not app.error
    app = _app(page="unknown")
    assert app.radio(key="main_navigation").value == "Executive Dashboard"
