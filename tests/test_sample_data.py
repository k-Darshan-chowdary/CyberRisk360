"""Integration tests for the Phase 1 sample risk data."""

import csv
from pathlib import Path

import pytest

from risk_engine import (
    calculate_inherent_score,
    calculate_residual_score,
    get_risk_rating,
)


SAMPLE_RISKS_PATH = Path(__file__).parents[1] / "data" / "sample_risks.csv"


def load_sample_risks():
    """Load the sample risks as a list of dictionaries."""
    with SAMPLE_RISKS_PATH.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def test_sample_data_contains_exactly_ten_risks():
    assert len(load_sample_risks()) == 10


@pytest.mark.parametrize(
    "risk", load_sample_risks(), ids=lambda risk: risk["risk_id"]
)
def test_sample_risk_calculations_and_ranges(risk):
    risk_id = risk["risk_id"]
    likelihood = int(risk["likelihood"])
    impact = int(risk["impact"])
    control_effectiveness = float(risk["control_effectiveness_pct"])

    assert 1 <= likelihood <= 5, f"{risk_id}: likelihood must be between 1 and 5"
    assert 1 <= impact <= 5, f"{risk_id}: impact must be between 1 and 5"
    assert 0 <= control_effectiveness <= 100, (
        f"{risk_id}: control effectiveness must be between 0 and 100"
    )

    inherent_score = calculate_inherent_score(likelihood, impact)
    residual_score = calculate_residual_score(
        inherent_score, control_effectiveness
    )

    assert inherent_score == int(risk["inherent_score"]), (
        f"{risk_id}: stored inherent score does not match the calculated score"
    )
    assert residual_score == float(risk["residual_score"]), (
        f"{risk_id}: stored residual score does not match the calculated score"
    )
    assert get_risk_rating(inherent_score) == risk["inherent_rating"], (
        f"{risk_id}: stored inherent rating does not match the calculated rating"
    )
    assert get_risk_rating(residual_score) == risk["residual_rating"], (
        f"{risk_id}: stored residual rating does not match the calculated rating"
    )
