"""Central, cached data-loading functions for the Streamlit interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from asset_register import load_assets
from control_register import load_controls
from evidence_register import load_evidence
from remediation_register import load_remediation_actions
from risk_register import load_risks


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_PATH = DATA_DIR / "sample_assets.csv"
RISKS_PATH = DATA_DIR / "sample_risks.csv"
CONTROLS_PATH = DATA_DIR / "sample_controls.csv"
EVIDENCE_PATH = DATA_DIR / "sample_evidence.csv"
REMEDIATION_PATH = DATA_DIR / "sample_remediation.csv"


@st.cache_data(show_spinner=False)
def _load_assets(path: str) -> list[dict[str, str]]:
    return load_assets(Path(path))


@st.cache_data(show_spinner=False)
def _load_risks(path: str) -> list[dict[str, Any]]:
    return load_risks(Path(path))


@st.cache_data(show_spinner=False)
def _load_controls(path: str) -> list[dict[str, Any]]:
    return load_controls(Path(path))


@st.cache_data(show_spinner=False)
def _load_evidence(path: str) -> list[dict[str, str]]:
    return load_evidence(Path(path))


@st.cache_data(show_spinner=False)
def _load_remediation(path: str) -> list[dict[str, Any]]:
    return load_remediation_actions(Path(path))


def load_all_assets() -> list[dict[str, str]]:
    """Load and validate all asset records without changing the CSV."""
    return _load_assets(str(ASSETS_PATH))


def load_all_risks() -> list[dict[str, Any]]:
    """Load and validate all risk records without changing the CSV."""
    return _load_risks(str(RISKS_PATH))


def load_all_controls() -> list[dict[str, Any]]:
    """Load and validate all security-control records."""
    return _load_controls(str(CONTROLS_PATH))


def load_all_evidence() -> list[dict[str, str]]:
    """Load and validate all control-evidence records."""
    return _load_evidence(str(EVIDENCE_PATH))


def load_all_remediation_actions() -> list[dict[str, Any]]:
    """Load and validate all remediation-action records."""
    return _load_remediation(str(REMEDIATION_PATH))


def load_all_project_data() -> dict[str, list[dict[str, Any]]]:
    """Return all five project datasets under stable, beginner-friendly keys."""
    return {
        "assets": load_all_assets(),
        "risks": load_all_risks(),
        "controls": load_all_controls(),
        "evidence": load_all_evidence(),
        "remediation": load_all_remediation_actions(),
    }


def clear_project_data_cache() -> None:
    """Clear only the cached UI loaders; project data files are never changed."""
    _load_assets.clear()
    _load_risks.clear()
    _load_controls.clear()
    _load_evidence.clear()
    _load_remediation.clear()
