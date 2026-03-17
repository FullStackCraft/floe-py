"""Black-Scholes-Merton option pricing, complete Greeks, and IV inversion."""

import math

from floe.statistics import cumulative_normal_distribution, normal_pdf
from floe.types import (
    DAYS_PER_YEAR,
    MILLISECONDS_PER_YEAR,
    BlackScholesParams,
    Greeks,
)


def _round(value: float, decimals: int) -> float:
    factor = 10**decimals
    return round(value * factor) / factor


def _zero_greeks() -> Greeks:
    return Greeks()


def black_scholes(params: BlackScholesParams) -> float:
    """Calculate the option price using the Black-Scholes model."""
    return calculate_greeks(params).price


def calculate_greeks(params: BlackScholesParams) -> Greeks:
    """Compute the complete set of option Greeks using Black-Scholes-Merton.

    Includes all first, second, and third-order Greeks:
    price, delta, gamma, theta, vega, rho, charm, vanna, volga,
    speed, zomma, color, ultima.
    """
    S = params.spot
    K = params.strike
    t = params.time_to_expiry
    vol = params.volatility
    r = params.risk_free_rate
    q = params.dividend_yield

    if t < 0:
        return _zero_greeks()
    if vol <= 0 or S <= 0 or t <= 0:
        return _zero_greeks()

    sqrt_t = math.sqrt(t)
    d1 = (math.log(S / K) + (r - q + vol * vol / 2) * t) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t

    nd1 = normal_pdf(d1)
    Nd1 = cumulative_normal_distribution(d1)
    Nd2 = cumulative_normal_distribution(d2)
    eqt = math.exp(-q * t)
    ert = math.exp(-r * t)

    if params.option_type == "call":
        return _calculate_call_greeks(S, K, r, q, t, vol, d1, d2, nd1, Nd1, Nd2, eqt, ert)
    return _calculate_put_greeks(S, K, r, q, t, vol, d1, d2, nd1, Nd1, Nd2, eqt, ert)


def _calculate_call_greeks(
    S: float, K: float, r: float, q: float, t: float, vol: float,
    d1: float, d2: float, nd1: float, Nd1: float, Nd2: float,
    eqt: float, ert: float,
) -> Greeks:
    sqrt_t = math.sqrt(t)

    price = S * eqt * Nd1 - K * ert * Nd2

    delta = eqt * Nd1
    gamma = (eqt * nd1) / (S * vol * sqrt_t)
    theta = -(S * vol * eqt * nd1) / (2 * sqrt_t) - r * K * ert * Nd2 + q * S * eqt * Nd1
    vega = S * eqt * sqrt_t * nd1
    rho = K * t * ert * Nd2

    vanna = -eqt * nd1 * (d2 / vol)
    charm = -q * eqt * Nd1 - (eqt * nd1 * (2 * (r - q) * t - d2 * vol * sqrt_t)) / (2 * t * vol * sqrt_t)
    volga = vega * ((d1 * d2) / (S * vol))
    speed = nd1 / (S * vol)
    zomma = (nd1 * d1) / (S * vol * vol)

    color = -(d1 * d2 * nd1) / (vol * vol)
    ultima = (d1 * d2 * d2 * nd1) / (vol * vol * vol)

    return Greeks(
        price=_round(price, 2),
        delta=_round(delta, 5),
        gamma=_round(gamma, 5),
        theta=_round(theta / DAYS_PER_YEAR, 5),
        vega=_round(vega * 0.01, 5),
        rho=_round(rho * 0.01, 5),
        charm=_round(charm / DAYS_PER_YEAR, 5),
        vanna=_round(vanna, 5),
        volga=_round(volga, 5),
        speed=_round(speed, 5),
        zomma=_round(zomma, 5),
        color=_round(color, 5),
        ultima=_round(ultima, 5),
    )


def _calculate_put_greeks(
    S: float, K: float, r: float, q: float, t: float, vol: float,
    d1: float, d2: float, nd1: float, Nd1: float, Nd2: float,
    eqt: float, ert: float,
) -> Greeks:
    sqrt_t = math.sqrt(t)

    NmD1 = cumulative_normal_distribution(-d1)
    NmD2 = cumulative_normal_distribution(-d2)

    price = K * ert * NmD2 - S * eqt * NmD1

    delta = -eqt * NmD1
    gamma = (eqt * nd1) / (S * vol * sqrt_t)
    theta = -(S * vol * eqt * nd1) / (2 * sqrt_t) + r * K * ert * NmD2 - q * S * eqt * NmD1
    vega = S * eqt * sqrt_t * nd1
    rho = -K * t * ert * NmD2

    vanna = -eqt * nd1 * (d2 / vol)
    charm = -q * eqt * NmD1 - (eqt * nd1 * (2 * (r - q) * t - d2 * vol * sqrt_t)) / (2 * t * vol * sqrt_t)
    volga = vega * ((d1 * d2) / (S * vol))
    speed = (nd1 * d1 * d1) / vol
    zomma = ((1 + d1 * d2) * nd1) / (vol * vol * sqrt_t)

    color = ((1 - d1 * d2) * nd1) / S
    ultima = (t * S * nd1 * d1 * d1) / vol

    return Greeks(
        price=_round(price, 2),
        delta=_round(delta, 5),
        gamma=_round(gamma, 5),
        theta=_round(theta / DAYS_PER_YEAR, 5),
        vega=_round(vega * 0.01, 5),
        rho=_round(rho * 0.01, 5),
        charm=_round(charm / DAYS_PER_YEAR, 5),
        vanna=_round(vanna, 5),
        volga=_round(volga, 5),
        speed=_round(speed, 5),
        zomma=_round(zomma, 5),
        color=_round(color, 5),
        ultima=_round(ultima, 5),
    )


def calculate_implied_volatility(
    price: float,
    spot: float,
    strike: float,
    risk_free_rate: float,
    dividend_yield: float,
    time_to_expiry: float,
    option_type: str,
) -> float:
    """Recover implied volatility from an observed option price using bisection.

    Returns IV as a percentage (e.g. 20.0 for 20%).
    """
    if price <= 0 or spot <= 0 or strike <= 0 or time_to_expiry <= 0:
        return 0.0

    eqt = math.exp(-dividend_yield * time_to_expiry)
    ert = math.exp(-risk_free_rate * time_to_expiry)

    if option_type == "call":
        intrinsic = max(0.0, spot * eqt - strike * ert)
    else:
        intrinsic = max(0.0, strike * ert - spot * eqt)

    extrinsic = price - intrinsic
    if extrinsic <= 0.01:
        return 1.0

    low = 0.0001
    high = 5.0
    mid = 0.0

    for _ in range(100):
        mid = 0.5 * (low + high)

        model_price = black_scholes(BlackScholesParams(
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            volatility=mid,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type,
        ))

        diff = model_price - price
        if abs(diff) < 1e-6:
            return mid * 100.0

        if diff > 0:
            high = mid
        else:
            low = mid

    return 0.5 * (low + high) * 100.0


def get_time_to_expiration_in_years(expiration_timestamp: int, now: int) -> float:
    """Convert an expiration timestamp (ms) to years from a reference time."""
    ms = float(expiration_timestamp - now)
    return ms / MILLISECONDS_PER_YEAR
