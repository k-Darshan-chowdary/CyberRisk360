"""Simple calculations for assessing cybersecurity risk."""


def _validate_integer_rating(value: object, name: str) -> int:
    """Validate that a likelihood or impact value is an integer from 1 to 5."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer from 1 through 5.")
    if not 1 <= value <= 5:
        raise ValueError(f"{name} must be between 1 and 5.")
    return value


def _validate_numeric_range(
    value: object, name: str, minimum: float, maximum: float
) -> int | float:
    """Validate that a value is a non-boolean number within an allowed range."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number.")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def calculate_inherent_score(likelihood: int, impact: int) -> int:
    """Calculate risk before controls by multiplying likelihood by impact.

    Both inputs must be whole numbers from 1 through 5. A ``TypeError`` is
    raised for other data types, including booleans, and a ``ValueError`` is
    raised when either number is outside the allowed range.
    """
    valid_likelihood = _validate_integer_rating(likelihood, "likelihood")
    valid_impact = _validate_integer_rating(impact, "impact")
    return valid_likelihood * valid_impact


def calculate_residual_score(
    inherent_score: int | float, control_effectiveness_pct: int | float
) -> float:
    """Calculate risk remaining after controls and round it to two decimals.

    ``inherent_score`` must be a number from 1 through 25, while
    ``control_effectiveness_pct`` must be a number from 0 through 100.
    Booleans are not accepted as numbers.
    """
    valid_score = _validate_numeric_range(
        inherent_score, "inherent_score", 1, 25
    )
    valid_effectiveness = _validate_numeric_range(
        control_effectiveness_pct, "control_effectiveness_pct", 0, 100
    )
    residual_score = valid_score * (1 - valid_effectiveness / 100)
    return round(residual_score, 2)


def get_risk_rating(score: int | float) -> str:
    """Return the risk rating for a numeric score from 0 through 25.

    Scores of 20 or more are Critical, scores of 15 or more are High,
    scores of 8 or more are Medium, and lower scores are Low. Invalid data
    types raise ``TypeError``; out-of-range numbers raise ``ValueError``.
    """
    valid_score = _validate_numeric_range(score, "score", 0, 25)

    if valid_score >= 20:
        return "Critical"
    if valid_score >= 15:
        return "High"
    if valid_score >= 8:
        return "Medium"
    return "Low"


def assess_risk(
    likelihood: int, impact: int, control_effectiveness_pct: int | float
) -> dict[str, int | float | str]:
    """Calculate and return a complete inherent and residual risk assessment.

    The returned dictionary includes the original inputs, both calculated
    scores, and the rating associated with each score. Input validation is
    performed by the individual calculation functions.
    """
    inherent_score = calculate_inherent_score(likelihood, impact)
    inherent_rating = get_risk_rating(inherent_score)
    residual_score = calculate_residual_score(
        inherent_score, control_effectiveness_pct
    )
    residual_rating = get_risk_rating(residual_score)

    return {
        "likelihood": likelihood,
        "impact": impact,
        "inherent_score": inherent_score,
        "inherent_rating": inherent_rating,
        "control_effectiveness_pct": control_effectiveness_pct,
        "residual_score": residual_score,
        "residual_rating": residual_rating,
    }
