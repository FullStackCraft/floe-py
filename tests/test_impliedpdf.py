"""Tests for floe.impliedpdf."""

from floe.impliedpdf import (
    DEFAULT_ADJUSTMENT_CONFIG,
    estimate_exposure_adjusted_pdf,
    estimate_implied_probability_distribution,
    get_edge_at_price,
    get_probability_in_range,
    get_quantile,
    get_significant_adjustment_levels,
)
from floe.types import ExposurePerExpiry, NormalizedOption, StrikeExposure


def _call_options() -> list[NormalizedOption]:
    exp = 1_000_000 + 30 * 86_400_000
    return [
        NormalizedOption(strike=490, option_type="call", bid=12.0, ask=12.5, mark=12.25, expiration_timestamp=exp),
        NormalizedOption(strike=495, option_type="call", bid=8.0, ask=8.5, mark=8.25, expiration_timestamp=exp),
        NormalizedOption(strike=500, option_type="call", bid=5.0, ask=5.5, mark=5.25, expiration_timestamp=exp),
        NormalizedOption(strike=505, option_type="call", bid=3.0, ask=3.5, mark=3.25, expiration_timestamp=exp),
        NormalizedOption(strike=510, option_type="call", bid=1.5, ask=2.0, mark=1.75, expiration_timestamp=exp),
    ]


def _exposures() -> ExposurePerExpiry:
    return ExposurePerExpiry(
        spot_price=500,
        expiration=1_000_000 + 30 * 86_400_000,
        total_charm_exposure=-200_000,
        strike_exposures=[
            StrikeExposure(strike_price=490, gamma_exposure=1_200_000, vanna_exposure=-300_000),
            StrikeExposure(strike_price=500, gamma_exposure=-900_000, vanna_exposure=250_000),
            StrikeExposure(strike_price=510, gamma_exposure=500_000, vanna_exposure=-100_000),
        ],
    )


def test_estimate_implied_pdf_requires_at_least_three_calls():
    result = estimate_implied_probability_distribution("QQQ", 500, _call_options()[:2], 1_000_000)
    assert result.success is False


def test_estimate_implied_pdf_probabilities_sum_to_one():
    result = estimate_implied_probability_distribution("QQQ", 500, _call_options(), 1_000_000)
    assert result.success is True

    assert result.distribution is not None
    total = sum(sp.probability for sp in result.distribution.strike_probabilities)
    assert abs(total - 1.0) < 0.01


def test_probability_and_quantile_helpers():
    result = estimate_implied_probability_distribution("QQQ", 500, _call_options(), 1_000_000)
    dist = result.distribution
    assert dist is not None

    p = get_probability_in_range(dist, 495, 510)
    assert 0 <= p <= 1

    q50 = get_quantile(dist, 0.5)
    assert dist.strike_probabilities[0].strike <= q50 <= dist.strike_probabilities[-1].strike


def test_exposure_adjusted_pdf_and_edges():
    adjusted = estimate_exposure_adjusted_pdf(
        "QQQ",
        500,
        _call_options(),
        _exposures(),
        DEFAULT_ADJUSTMENT_CONFIG,
        1_000_000,
    )

    edge = get_edge_at_price(adjusted, 500)
    levels = get_significant_adjustment_levels(adjusted, 0.001)

    assert isinstance(edge, float)
    assert isinstance(levels, list)
