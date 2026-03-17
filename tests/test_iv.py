"""Tests for floe.iv."""

from floe.iv import compute_implied_volatility, compute_variance_swap_iv
from floe.types import NormalizedOption


def _option(strike: float, option_type: str, bid: float, ask: float, expiration: int) -> NormalizedOption:
    return NormalizedOption(
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        mark=(bid + ask) / 2,
        expiration_timestamp=expiration,
    )


def test_compute_variance_swap_iv_empty_chain_returns_zero():
    result = compute_variance_swap_iv([], 500, 0.05, 1_000_000)
    assert result.implied_volatility == 0


def test_compute_variance_swap_iv_basic_chain_positive():
    exp = 1_000_000 + 30 * 86_400_000
    as_of = 1_000_000

    options = [
        _option(490, "put", 1.0, 1.2, exp),
        _option(495, "put", 2.0, 2.4, exp),
        _option(500, "call", 5.0, 5.5, exp),
        _option(500, "put", 4.8, 5.3, exp),
        _option(505, "call", 2.0, 2.4, exp),
        _option(510, "call", 1.0, 1.2, exp),
    ]

    result = compute_variance_swap_iv(options, 500, 0.05, as_of)
    assert result.implied_volatility > 0
    assert result.forward > 0
    assert result.num_strikes > 0


def test_compute_implied_volatility_two_term_interpolates():
    as_of = 1_000_000
    exp1 = 1_000_000 + 20 * 86_400_000
    exp2 = 1_000_000 + 50 * 86_400_000

    near = [
        _option(490, "put", 1.0, 1.2, exp1),
        _option(500, "call", 4.0, 4.5, exp1),
        _option(500, "put", 3.8, 4.3, exp1),
        _option(510, "call", 0.8, 1.0, exp1),
    ]
    far = [
        _option(490, "put", 2.0, 2.4, exp2),
        _option(500, "call", 7.0, 7.5, exp2),
        _option(500, "put", 6.8, 7.3, exp2),
        _option(510, "call", 2.0, 2.4, exp2),
    ]

    result = compute_implied_volatility(near, 500, 0.05, as_of, far, 30)
    assert result.is_interpolated is True
    assert result.far_term is not None
    assert result.implied_volatility > 0
