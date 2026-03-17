"""Tests for floe.rv."""

import math

from floe.rv import PriceObservation, compute_realized_volatility


def test_compute_realized_volatility_basic_series():
    obs = [
        PriceObservation(price=100, timestamp=0),
        PriceObservation(price=101, timestamp=60_000),
        PriceObservation(price=100.5, timestamp=120_000),
        PriceObservation(price=102, timestamp=180_000),
        PriceObservation(price=101, timestamp=240_000),
    ]

    result = compute_realized_volatility(obs)
    assert result.num_observations == 5
    assert result.num_returns == 4
    assert result.realized_volatility > 0


def test_compute_realized_volatility_single_obs_returns_zero():
    result = compute_realized_volatility([PriceObservation(price=100, timestamp=0)])
    assert result.realized_volatility == 0


def test_compute_realized_volatility_filters_invalid_prices():
    obs = [
        PriceObservation(price=100, timestamp=0),
        PriceObservation(price=-1, timestamp=60_000),
        PriceObservation(price=math.nan, timestamp=120_000),
        PriceObservation(price=math.inf, timestamp=180_000),
        PriceObservation(price=101, timestamp=240_000),
    ]

    result = compute_realized_volatility(obs)
    assert result.num_observations == 2
