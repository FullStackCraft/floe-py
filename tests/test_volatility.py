"""Tests for floe.volatility."""

import math
import time

from floe.types import NormalizedOption, OptionChain
from floe.volatility import (
    _CubicSpline,
    _enforce_convexity,
    get_iv_for_strike,
    get_iv_surfaces,
    smooth_total_variance_smile,
)


def _sample_chain() -> tuple[OptionChain, int]:
    now = int(time.time() * 1000)
    exp = now + 30 * 24 * 60 * 60 * 1000

    options = [
        NormalizedOption(strike=90, expiration_timestamp=exp, option_type="call", bid=12.2, ask=12.6, mark=12.4, implied_volatility=0.24),
        NormalizedOption(strike=95, expiration_timestamp=exp, option_type="call", bid=8.9, ask=9.2, mark=9.05, implied_volatility=0.21),
        NormalizedOption(strike=100, expiration_timestamp=exp, option_type="call", bid=5.8, ask=6.1, mark=5.95, implied_volatility=0.19),
        NormalizedOption(strike=105, expiration_timestamp=exp, option_type="call", bid=3.3, ask=3.6, mark=3.45, implied_volatility=0.21),
        NormalizedOption(strike=110, expiration_timestamp=exp, option_type="call", bid=1.8, ask=2.1, mark=1.95, implied_volatility=0.24),
        NormalizedOption(strike=90, expiration_timestamp=exp, option_type="put", bid=1.4, ask=1.7, mark=1.55, implied_volatility=0.25),
        NormalizedOption(strike=95, expiration_timestamp=exp, option_type="put", bid=2.5, ask=2.8, mark=2.65, implied_volatility=0.22),
        NormalizedOption(strike=100, expiration_timestamp=exp, option_type="put", bid=4.9, ask=5.2, mark=5.05, implied_volatility=0.20),
        NormalizedOption(strike=105, expiration_timestamp=exp, option_type="put", bid=8.4, ask=8.7, mark=8.55, implied_volatility=0.21),
        NormalizedOption(strike=110, expiration_timestamp=exp, option_type="put", bid=12.6, ask=12.9, mark=12.75, implied_volatility=0.24),
    ]

    chain = OptionChain(
        symbol="SPY",
        spot=100.0,
        risk_free_rate=0.05,
        dividend_yield=0.01,
        options=options,
    )
    return chain, now


def test_get_iv_surfaces_builds_call_and_put_surfaces():
    chain, now = _sample_chain()
    surfaces = get_iv_surfaces("totalvariance", chain, now)

    assert len(surfaces) == 2
    assert {(s.expiration_date, s.put_call) for s in surfaces} == {
        (chain.options[0].expiration_timestamp, "call"),
        (chain.options[0].expiration_timestamp, "put"),
    }


def test_get_iv_for_strike_returns_value_for_existing_strike():
    chain, now = _sample_chain()
    surfaces = get_iv_surfaces("totalvariance", chain, now)

    exp = chain.options[0].expiration_timestamp
    iv = get_iv_for_strike(surfaces, exp, "call", 100)

    assert iv > 0


def test_smooth_total_variance_smile_returns_same_length_and_positive():
    strikes = [90, 95, 100, 105, 110]
    ivs = [24, 21, 18, 21, 24]
    smoothed = smooth_total_variance_smile(strikes, ivs, 0.25)

    assert len(smoothed) == len(ivs)
    assert all(v > 0 for v in smoothed)


def test_enforce_convexity_produces_finite_values():
    x = [1, 2, 3, 4, 5]
    w = [1.0, 0.5, 0.3, 0.5, 1.0]
    out = _enforce_convexity(x, w)

    assert len(out) == len(w)
    assert all(not math.isnan(v) for v in out)


def test_cubic_spline_interpolates_knots_exactly():
    x = [0, 1, 2, 3, 4]
    y = [0, 1, 4, 9, 16]
    spline = _CubicSpline(x, y)

    for i, xi in enumerate(x):
        assert abs(spline.eval(xi) - y[i]) < 1e-10

    mid = spline.eval(1.5)
    assert 1 <= mid <= 4
