"""Tests for the Phase 6 central Streamlit data loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from asset_register import load_assets
from control_register import load_controls
from evidence_register import load_evidence
from remediation_register import load_remediation_actions
from risk_register import load_risks
from ui import data_loader


SAMPLE_PATHS = [
    data_loader.ASSETS_PATH,
    data_loader.RISKS_PATH,
    data_loader.CONTROLS_PATH,
    data_loader.EVIDENCE_PATH,
    data_loader.REMEDIATION_PATH,
]


@pytest.fixture(autouse=True)
def clear_ui_cache():
    """Keep cache state independent between tests."""
    data_loader.clear_project_data_cache()
    yield
    data_loader.clear_project_data_cache()


def test_asset_loader_returns_eight_records():
    assert len(data_loader.load_all_assets()) == 8


def test_risk_loader_returns_ten_records():
    assert len(data_loader.load_all_risks()) == 10


def test_control_loader_returns_twelve_records():
    assert len(data_loader.load_all_controls()) == 12


def test_evidence_loader_returns_twelve_records():
    assert len(data_loader.load_all_evidence()) == 12


def test_remediation_loader_returns_ten_records():
    assert len(data_loader.load_all_remediation_actions()) == 10


def test_project_loader_returns_five_exact_keys():
    assert set(data_loader.load_all_project_data()) == {
        "assets", "risks", "controls", "evidence", "remediation"
    }


@pytest.mark.parametrize(
    "loader",
    [
        data_loader.load_all_assets,
        data_loader.load_all_risks,
        data_loader.load_all_controls,
        data_loader.load_all_evidence,
        data_loader.load_all_remediation_actions,
    ],
)
def test_individual_loaders_return_lists_of_dictionaries(loader):
    records = loader()
    assert isinstance(records, list)
    assert records
    assert all(isinstance(record, dict) for record in records)


def test_missing_file_error_is_surfaced(monkeypatch, tmp_path):
    monkeypatch.setattr(data_loader, "ASSETS_PATH", tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError):
        data_loader.load_all_assets()


def test_malformed_data_error_is_surfaced(monkeypatch, tmp_path):
    malformed = tmp_path / "malformed_assets.csv"
    malformed.write_text("asset_id,asset_name\nAST-001,Incomplete\n", encoding="utf-8")
    monkeypatch.setattr(data_loader, "ASSETS_PATH", malformed)
    with pytest.raises(ValueError, match="missing required columns"):
        data_loader.load_all_assets()


def test_calling_all_loaders_does_not_modify_sample_files():
    before = {path: path.read_bytes() for path in SAMPLE_PATHS}
    data_loader.load_all_project_data()
    assert {path: path.read_bytes() for path in SAMPLE_PATHS} == before


def test_clearing_cache_does_not_modify_data():
    before = data_loader.load_all_project_data()
    data_loader.clear_project_data_cache()
    assert data_loader.load_all_project_data() == before


@pytest.mark.parametrize(
    ("ui_loader", "backend_loader", "path"),
    [
        (data_loader.load_all_assets, load_assets, data_loader.ASSETS_PATH),
        (data_loader.load_all_risks, load_risks, data_loader.RISKS_PATH),
        (data_loader.load_all_controls, load_controls, data_loader.CONTROLS_PATH),
        (data_loader.load_all_evidence, load_evidence, data_loader.EVIDENCE_PATH),
        (
            data_loader.load_all_remediation_actions,
            load_remediation_actions,
            data_loader.REMEDIATION_PATH,
        ),
    ],
)
def test_ui_loaders_preserve_backend_data(ui_loader, backend_loader, path: Path):
    assert ui_loader() == backend_loader(path)
