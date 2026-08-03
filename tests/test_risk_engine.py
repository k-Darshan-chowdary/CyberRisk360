"""Unit tests for the risk-scoring engine."""

import pytest

from risk_engine import (
    assess_risk,
    calculate_inherent_score,
    calculate_residual_score,
    get_risk_rating,
)


@pytest.mark.parametrize(
    ("likelihood", "impact", "expected"),
    [(1, 1, 1), (2, 4, 8), (3, 5, 15), (4, 4, 16), (5, 5, 25)],
)
def test_calculate_inherent_score(likelihood, impact, expected):
    assert calculate_inherent_score(likelihood, impact) == expected


@pytest.mark.parametrize(
    ("inherent_score", "effectiveness", "expected"),
    [(16, 60, 6.4), (20, 45, 11.0), (15, 50, 7.5), (12, 25, 9.0)],
)
def test_calculate_residual_score(inherent_score, effectiveness, expected):
    assert calculate_residual_score(inherent_score, effectiveness) == expected


def test_residual_score_rounds_to_two_decimal_places():
    assert calculate_residual_score(25, 33.33) == 16.67


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "Low"),
        (7.99, "Low"),
        (8, "Medium"),
        (14.99, "Medium"),
        (15, "High"),
        (19.99, "High"),
        (20, "Critical"),
        (25, "Critical"),
    ],
)
def test_exact_risk_rating_boundaries(score, expected):
    assert get_risk_rating(score) == expected


@pytest.mark.parametrize(
    ("score", "expected"),
    [(3, "Low"), (10, "Medium"), (17, "High"), (23, "Critical")],
)
def test_risk_rating_categories(score, expected):
    assert get_risk_rating(score) == expected


def test_zero_percent_control_effectiveness_leaves_score_unchanged():
    assert calculate_residual_score(20, 0) == 20.0


def test_full_control_effectiveness_reduces_score_to_zero():
    assert calculate_residual_score(20, 100) == 0.0


def test_assess_risk_returns_complete_result():
    assert assess_risk(4, 4, 60) == {
        "likelihood": 4,
        "impact": 4,
        "inherent_score": 16,
        "inherent_rating": "High",
        "control_effectiveness_pct": 60,
        "residual_score": 6.4,
        "residual_rating": "Low",
    }


@pytest.mark.parametrize("likelihood", [0, 6, -1])
def test_invalid_likelihood_range_raises_value_error(likelihood):
    with pytest.raises(ValueError):
        calculate_inherent_score(likelihood, 3)


@pytest.mark.parametrize("impact", [0, 6, -1])
def test_invalid_impact_range_raises_value_error(impact):
    with pytest.raises(ValueError):
        calculate_inherent_score(3, impact)


@pytest.mark.parametrize("effectiveness", [-0.01, 100.01, -1, 101])
def test_invalid_control_effectiveness_range_raises_value_error(effectiveness):
    with pytest.raises(ValueError):
        calculate_residual_score(10, effectiveness)


@pytest.mark.parametrize("inherent_score", [0, 25.01, -1, 26])
def test_invalid_inherent_score_range_raises_value_error(inherent_score):
    with pytest.raises(ValueError):
        calculate_residual_score(inherent_score, 50)


@pytest.mark.parametrize("score", [-0.01, 25.01, -1, 26])
def test_invalid_rating_score_range_raises_value_error(score):
    with pytest.raises(ValueError):
        get_risk_rating(score)


@pytest.mark.parametrize("bad_value", ["3", None, True, False, 3.0])
def test_invalid_likelihood_types_raise_type_error(bad_value):
    with pytest.raises(TypeError):
        calculate_inherent_score(bad_value, 3)


@pytest.mark.parametrize("bad_value", ["3", None, True, False, 3.0])
def test_invalid_impact_types_raise_type_error(bad_value):
    with pytest.raises(TypeError):
        calculate_inherent_score(3, bad_value)


@pytest.mark.parametrize("bad_value", ["50", None, True, False])
def test_invalid_control_effectiveness_types_raise_type_error(bad_value):
    with pytest.raises(TypeError):
        calculate_residual_score(10, bad_value)


@pytest.mark.parametrize("bad_value", ["10", None, True, False])
def test_invalid_inherent_score_types_raise_type_error(bad_value):
    with pytest.raises(TypeError):
        calculate_residual_score(bad_value, 50)


@pytest.mark.parametrize("bad_value", ["10", None, True, False])
def test_invalid_rating_score_types_raise_type_error(bad_value):
    with pytest.raises(TypeError):
        get_risk_rating(bad_value)
