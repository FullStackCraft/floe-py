"""Model-free implied volatility using the CBOE variance swap methodology."""

from __future__ import annotations

import math
from dataclasses import dataclass

from floe.types import MILLISECONDS_PER_YEAR, NormalizedOption


@dataclass
class VarianceSwapResult:
    implied_volatility: float = 0.0
    annualized_variance: float = 0.0
    forward: float = 0.0
    k0: float = 0.0
    time_to_expiry: float = 0.0
    expiration: int = 0
    num_strikes: int = 0
    put_contribution: float = 0.0
    call_contribution: float = 0.0


@dataclass
class ImpliedVolatilityResult:
    implied_volatility: float = 0.0
    near_term: VarianceSwapResult | None = None
    far_term: VarianceSwapResult | None = None
    target_days: int | None = None
    is_interpolated: bool = False


def compute_variance_swap_iv(
    options: list[NormalizedOption],
    spot: float,
    risk_free_rate: float,
    as_of_timestamp: int,
) -> VarianceSwapResult:
    """Compute model-free implied variance for a single expiration (CBOE methodology)."""
    if not options or spot <= 0:
        return VarianceSwapResult()

    expiration = options[0].expiration_timestamp
    T = float(expiration - as_of_timestamp) / MILLISECONDS_PER_YEAR
    if T <= 0:
        return VarianceSwapResult(expiration=expiration)

    calls_by_strike: dict[float, float] = {}
    puts_by_strike: dict[float, float] = {}
    strike_set: set[float] = set()

    for opt in options:
        mid = _mid_price(opt)
        if mid <= 0:
            continue
        strike_set.add(opt.strike)
        if opt.option_type == "call":
            calls_by_strike[opt.strike] = mid
        else:
            puts_by_strike[opt.strike] = mid

    strikes = sorted(strike_set)
    if len(strikes) < 2:
        return VarianceSwapResult(expiration=expiration, time_to_expiry=T)

    # Find K0.
    k0 = strikes[0]
    min_diff = float("inf")
    for k in strikes:
        if k in calls_by_strike and k in puts_by_strike:
            diff = abs(calls_by_strike[k] - puts_by_strike[k])
            if diff < min_diff:
                min_diff = diff
                k0 = k

    # Forward price.
    ert = math.exp(risk_free_rate * T)
    call_k0 = calls_by_strike.get(k0, 0.0)
    put_k0 = puts_by_strike.get(k0, 0.0)
    F = k0 + ert * (call_k0 - put_k0)

    put_contrib = 0.0
    call_contrib = 0.0
    num_strikes = 0

    # Walk puts downward from K0.
    zero_count = 0
    for i in range(len(strikes) - 1, -1, -1):
        k = strikes[i]
        if k > k0:
            continue
        p = puts_by_strike.get(k, 0.0)
        if p <= 0:
            zero_count += 1
            if zero_count >= 2:
                break
            continue
        zero_count = 0

        delta_k = _compute_delta_k(strikes, i)
        q = p
        if k == k0 and k in calls_by_strike:
            q = (calls_by_strike[k] + p) / 2
        put_contrib += (delta_k / (k * k)) * ert * q
        num_strikes += 1

    # Walk calls upward from K0.
    zero_count = 0
    for i in range(len(strikes)):
        k = strikes[i]
        if k < k0:
            continue
        c = calls_by_strike.get(k, 0.0)
        if c <= 0:
            zero_count += 1
            if zero_count >= 2:
                break
            continue
        zero_count = 0

        delta_k = _compute_delta_k(strikes, i)
        q = c
        if k == k0 and k in puts_by_strike:
            q = (c + puts_by_strike[k]) / 2
        call_contrib += (delta_k / (k * k)) * ert * q
        num_strikes += 1

    variance = (2.0 / T) * (put_contrib + call_contrib) - (1.0 / T) * ((F / k0 - 1) ** 2)
    variance = max(variance, 0.0)

    return VarianceSwapResult(
        implied_volatility=math.sqrt(variance),
        annualized_variance=variance,
        forward=F,
        k0=k0,
        time_to_expiry=T,
        expiration=expiration,
        num_strikes=num_strikes,
        put_contribution=put_contrib,
        call_contribution=call_contrib,
    )


def compute_implied_volatility(
    near_term_options: list[NormalizedOption],
    spot: float,
    risk_free_rate: float,
    as_of_timestamp: int,
    far_term_options: list[NormalizedOption] | None = None,
    target_days: int | None = None,
) -> ImpliedVolatilityResult:
    """Compute model-free IV, optionally interpolating between two terms."""
    near = compute_variance_swap_iv(near_term_options, spot, risk_free_rate, as_of_timestamp)

    if not far_term_options or target_days is None:
        return ImpliedVolatilityResult(
            implied_volatility=near.implied_volatility,
            near_term=near,
            is_interpolated=False,
        )

    far = compute_variance_swap_iv(far_term_options, spot, risk_free_rate, as_of_timestamp)

    T1 = near.time_to_expiry
    T2 = far.time_to_expiry
    N1 = T1 * 365.0 * 1440.0
    N2 = T2 * 365.0 * 1440.0
    N_target = float(target_days) * 1440.0
    N_365 = 365.0 * 1440.0

    denom = N2 - N1
    if denom <= 0:
        return ImpliedVolatilityResult(
            implied_volatility=near.implied_volatility,
            near_term=near,
            far_term=far,
            target_days=target_days,
            is_interpolated=False,
        )

    w1 = (N2 - N_target) / denom
    w2 = (N_target - N1) / denom

    interp_var = (T1 * near.annualized_variance * w1 + T2 * far.annualized_variance * w2) * N_365 / N_target
    interp_var = max(interp_var, 0.0)

    return ImpliedVolatilityResult(
        implied_volatility=math.sqrt(interp_var),
        near_term=near,
        far_term=far,
        target_days=target_days,
        is_interpolated=True,
    )


def _mid_price(opt: NormalizedOption) -> float:
    if opt.bid > 0 and opt.ask > 0:
        return (opt.bid + opt.ask) / 2
    if opt.mark > 0:
        return opt.mark
    return 0.0


def _compute_delta_k(strikes: list[float], i: int) -> float:
    n = len(strikes)
    if n == 1:
        return 1.0
    if i == 0:
        return strikes[1] - strikes[0]
    if i == n - 1:
        return strikes[n - 1] - strikes[n - 2]
    return (strikes[i + 1] - strikes[i - 1]) / 2
