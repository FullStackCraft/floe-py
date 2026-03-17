"""Tests for floe.blackscholes."""

import math

from floe.blackscholes import (
    black_scholes,
    calculate_greeks,
    calculate_implied_volatility,
)
from floe.types import BlackScholesParams


def _params(**overrides) -> BlackScholesParams:
    defaults = dict(
        spot=100, strike=100, time_to_expiry=1.0,
        volatility=0.20, risk_free_rate=0.05, dividend_yield=0.0,
        option_type="call",
    )
    defaults.update(overrides)
    return BlackScholesParams(**defaults)


# --- Pricing ----------------------------------------------------------------

def test_call_price_atm():
    price = black_scholes(_params())
    assert 10 < price < 11


def test_put_price_atm():
    price = black_scholes(_params(option_type="put"))
    assert 5 < price < 6


def test_zero_time_returns_zero():
    price = black_scholes(_params(spot=110, time_to_expiry=0))
    assert price == 0.0


def test_deep_itm_call():
    price = black_scholes(_params(spot=150, strike=100, time_to_expiry=0.25))
    assert 49 < price < 52


def test_deep_otm_put():
    price = black_scholes(_params(spot=150, strike=100, time_to_expiry=0.25, option_type="put"))
    assert price < 0.01


def test_put_call_parity():
    p = _params(spot=100, strike=105, time_to_expiry=0.25, volatility=0.20,
                risk_free_rate=0.05, dividend_yield=0.02)
    call = black_scholes(p)
    put = black_scholes(BlackScholesParams(**{**vars(p), "option_type": "put"}))
    S = p.spot * math.exp(-p.dividend_yield * p.time_to_expiry)
    K = p.strike * math.exp(-p.risk_free_rate * p.time_to_expiry)
    assert abs((call - put) - (S - K)) < 0.01


# --- Greeks -----------------------------------------------------------------

def test_call_delta_range():
    g = calculate_greeks(_params())
    assert 0.5 < g.delta < 0.65


def test_put_delta_range():
    g = calculate_greeks(_params(option_type="put"))
    assert -0.5 < g.delta < 0


def test_call_put_gamma_equal():
    gc = calculate_greeks(_params())
    gp = calculate_greeks(_params(option_type="put"))
    assert abs(gc.gamma - gp.gamma) < 1e-5


def test_call_put_vega_equal():
    gc = calculate_greeks(_params())
    gp = calculate_greeks(_params(option_type="put"))
    assert abs(gc.vega - gp.vega) < 1e-5


def test_negative_theta():
    g = calculate_greeks(_params())
    assert g.theta < 0


def test_positive_vega():
    g = calculate_greeks(_params())
    assert g.vega > 0


def test_call_positive_rho():
    g = calculate_greeks(_params())
    assert g.rho > 0


def test_put_negative_rho():
    g = calculate_greeks(_params(option_type="put"))
    assert g.rho < 0


def test_invalid_params_return_zero():
    g = calculate_greeks(_params(volatility=0))
    assert g.price == 0 and g.delta == 0


def test_second_order_greeks_exist():
    g = calculate_greeks(_params())
    assert g.vanna != 0
    assert g.charm != 0


# --- Implied volatility -----------------------------------------------------

def test_iv_recovery_call():
    p = _params(spot=100, strike=105, time_to_expiry=0.25, volatility=0.25,
                risk_free_rate=0.05, dividend_yield=0.02)
    price = black_scholes(p)
    iv = calculate_implied_volatility(price, 100, 105, 0.05, 0.02, 0.25, "call")
    assert abs(iv - 25.0) < 0.5


def test_iv_recovery_put():
    p = _params(spot=100, strike=95, time_to_expiry=0.5, volatility=0.30,
                risk_free_rate=0.05, dividend_yield=0.01, option_type="put")
    price = black_scholes(p)
    iv = calculate_implied_volatility(price, 100, 95, 0.05, 0.01, 0.5, "put")
    assert abs(iv - 30.0) < 0.5


def test_iv_zero_price():
    iv = calculate_implied_volatility(0, 100, 100, 0.05, 0, 1.0, "call")
    assert iv == 0.0


def test_iv_below_intrinsic():
    iv = calculate_implied_volatility(0.50, 110, 100, 0.05, 0, 1.0, "call")
    assert iv == 1.0  # IV floor


def test_iv_high_vol():
    p = _params(spot=100, strike=100, time_to_expiry=1.0, volatility=0.80,
                risk_free_rate=0.05, dividend_yield=0)
    price = black_scholes(p)
    iv = calculate_implied_volatility(price, 100, 100, 0.05, 0, 1.0, "call")
    assert abs(iv - 80.0) < 1.0
