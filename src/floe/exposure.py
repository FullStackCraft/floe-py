"""Dealer gamma, vanna, and charm exposure calculations (GEX / VEX / CEX)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from floe.blackscholes import calculate_greeks
from floe.types import (
    DAYS_PER_YEAR,
    MILLISECONDS_PER_YEAR,
    BlackScholesParams,
    ExposureModeBreakdown,
    ExposureVariantsPerExpiry,
    ExposureVector,
    OptionChain,
    StrikeExposure,
    StrikeExposureVariants,
    IVSurface,
    ExposureCalculationOptions,
)
from floe.volatility import get_iv_for_strike


@dataclass
class SharesCoverResult:
    """Result of computing shares needed to cover exposure."""

    action_to_cover: str = ""
    shares_to_cover: float = 0.0
    implied_move_to_cover: float = 0.0
    resulting_spot_to_cover: float = 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_gamma_vanna_charm_exposures(
    chain: OptionChain,
    iv_surfaces: list[IVSurface],
    opts: ExposureCalculationOptions,
) -> list[ExposureVariantsPerExpiry]:
    """Compute canonical, state-weighted, and flow-delta exposure variants."""
    spot = chain.spot
    as_of = opts.as_of_timestamp
    if as_of == 0:
        return []

    expiration_set: set[int] = set()
    for opt in chain.options:
        expiration_set.add(opt.expiration_timestamp)
    expirations = sorted(expiration_set)

    puts_by_key: dict[str, object] = {}
    for opt in chain.options:
        if opt.option_type == "put":
            puts_by_key[f"{opt.expiration_timestamp}:{opt.strike:.4f}"] = opt

    results: list[ExposureVariantsPerExpiry] = []

    for exp in expirations:
        if exp < as_of:
            continue

        tte = float(exp - as_of) / MILLISECONDS_PER_YEAR
        if tte <= 0:
            continue

        dte_in_days = max(tte * DAYS_PER_YEAR, 0.0)
        strike_variants: list[StrikeExposureVariants] = []

        for call_opt in chain.options:
            if call_opt.expiration_timestamp != exp or call_opt.option_type != "call":
                continue

            key = f"{exp}:{call_opt.strike:.4f}"
            put_opt = puts_by_key.get(key)
            if put_opt is None:
                continue

            call_iv = _resolve_iv_percent(
                get_iv_for_strike(iv_surfaces, exp, "call", call_opt.strike),
                call_opt.implied_volatility,
            )
            put_iv = _resolve_iv_percent(
                get_iv_for_strike(iv_surfaces, exp, "put", put_opt.strike),
                put_opt.implied_volatility,
            )

            call_greeks = calculate_greeks(BlackScholesParams(
                spot=spot, strike=call_opt.strike, time_to_expiry=tte,
                volatility=call_iv / 100.0, risk_free_rate=chain.risk_free_rate,
                dividend_yield=chain.dividend_yield, option_type="call",
            ))
            put_greeks = calculate_greeks(BlackScholesParams(
                spot=spot, strike=put_opt.strike, time_to_expiry=tte,
                volatility=put_iv / 100.0, risk_free_rate=chain.risk_free_rate,
                dividend_yield=chain.dividend_yield, option_type="put",
            ))

            call_oi = _sanitize(call_opt.open_interest)
            put_oi = _sanitize(put_opt.open_interest)

            canonical = _canonical_vector(
                spot, call_oi, put_oi,
                call_greeks.gamma, put_greeks.gamma,
                call_greeks.vanna, put_greeks.vanna,
                call_greeks.charm, put_greeks.charm,
            )

            state_weighted = _state_weighted_vector(
                spot, call_oi, put_oi,
                call_greeks.vanna, put_greeks.vanna,
                call_greeks.charm, put_greeks.charm,
                call_iv, put_iv, dte_in_days, canonical.gamma_exposure,
            )

            call_flow = _resolve_flow_delta_oi(call_opt.open_interest, call_opt.live_open_interest)
            put_flow = _resolve_flow_delta_oi(put_opt.open_interest, put_opt.live_open_interest)
            flow_delta = _canonical_vector(
                spot, call_flow, put_flow,
                call_greeks.gamma, put_greeks.gamma,
                call_greeks.vanna, put_greeks.vanna,
                call_greeks.charm, put_greeks.charm,
            )

            strike_variants.append(StrikeExposureVariants(
                strike_price=call_opt.strike,
                canonical=canonical,
                state_weighted=state_weighted,
                flow_delta=flow_delta,
            ))

        if not strike_variants:
            continue

        results.append(ExposureVariantsPerExpiry(
            spot_price=spot,
            expiration=exp,
            canonical=_build_mode_breakdown(strike_variants, "canonical"),
            state_weighted=_build_mode_breakdown(strike_variants, "state_weighted"),
            flow_delta=_build_mode_breakdown(strike_variants, "flow_delta"),
            strike_exposure_variants=strike_variants,
        ))

    return results


def calculate_shares_needed_to_cover(
    shares_outstanding: float,
    total_net_exposure: float,
    underlying_mark: float,
) -> SharesCoverResult:
    """Compute shares dealers need to trade to neutralize net exposure."""
    action = "SELL" if total_net_exposure > 0 else "BUY"

    if shares_outstanding == 0 or not math.isfinite(shares_outstanding):
        return SharesCoverResult(resulting_spot_to_cover=underlying_mark)
    if underlying_mark == 0 or not math.isfinite(underlying_mark):
        return SharesCoverResult(resulting_spot_to_cover=underlying_mark)

    shares_needed = -total_net_exposure / underlying_mark
    implied_change = (shares_needed / shares_outstanding) * 100.0
    resulting_price = underlying_mark * (1 + implied_change / 100.0)

    return SharesCoverResult(
        action_to_cover=action,
        shares_to_cover=abs(shares_needed),
        implied_move_to_cover=implied_change,
        resulting_spot_to_cover=resulting_price,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sanitize(v: float) -> float:
    if not math.isfinite(v):
        return 0.0
    return v


def _sanitize_vector(v: ExposureVector) -> ExposureVector:
    return ExposureVector(
        gamma_exposure=_sanitize(v.gamma_exposure),
        vanna_exposure=_sanitize(v.vanna_exposure),
        charm_exposure=_sanitize(v.charm_exposure),
        net_exposure=_sanitize(v.net_exposure),
    )


def _canonical_vector(
    spot: float, call_oi: float, put_oi: float,
    call_gamma: float, put_gamma: float,
    call_vanna: float, put_vanna: float,
    call_charm: float, put_charm: float,
) -> ExposureVector:
    gex = -call_oi * call_gamma * (spot * 100.0) * spot * 0.01 + \
        put_oi * put_gamma * (spot * 100.0) * spot * 0.01

    vex = -call_oi * call_vanna * (spot * 100.0) * 0.01 + \
        put_oi * put_vanna * (spot * 100.0) * 0.01

    cex = -call_oi * call_charm * (spot * 100.0) + \
        put_oi * put_charm * (spot * 100.0)

    return _sanitize_vector(ExposureVector(
        gamma_exposure=gex,
        vanna_exposure=vex,
        charm_exposure=cex,
        net_exposure=gex + vex + cex,
    ))


def _state_weighted_vector(
    spot: float, call_oi: float, put_oi: float,
    call_vanna: float, put_vanna: float,
    call_charm: float, put_charm: float,
    call_iv_pct: float, put_iv_pct: float,
    dte_in_days: float, canonical_gex: float,
) -> ExposureVector:
    call_iv_level = max(call_iv_pct * 0.01, 0.0)
    put_iv_level = max(put_iv_pct * 0.01, 0.0)

    gex = canonical_gex

    vex = -call_oi * call_vanna * (spot * 100.0) * 0.01 * call_iv_level + \
        put_oi * put_vanna * (spot * 100.0) * 0.01 * put_iv_level

    canonical_charm = -call_oi * call_charm * (spot * 100.0) + \
        put_oi * put_charm * (spot * 100.0)
    cex = canonical_charm * max(dte_in_days, 0.0)

    return _sanitize_vector(ExposureVector(
        gamma_exposure=gex,
        vanna_exposure=vex,
        charm_exposure=cex,
        net_exposure=gex + vex + cex,
    ))


def _resolve_flow_delta_oi(open_interest: float, live_oi: float | None) -> float:
    if live_oi is None or not math.isfinite(live_oi):
        return 0.0
    return _sanitize(live_oi - open_interest)


def _resolve_iv_percent(iv_from_surface: float, option_iv_decimal: float) -> float:
    if math.isfinite(iv_from_surface) and iv_from_surface > 0:
        return iv_from_surface
    fallback = option_iv_decimal * 100.0
    if math.isfinite(fallback) and fallback > 0:
        return fallback
    return 0.0


def _build_mode_breakdown(
    variants: list[StrikeExposureVariants],
    mode: str,
) -> ExposureModeBreakdown:
    if not variants:
        return ExposureModeBreakdown()

    exposures: list[StrikeExposure] = []
    for v in variants:
        vec = getattr(v, mode)
        exposures.append(StrikeExposure(
            strike_price=v.strike_price,
            gamma_exposure=vec.gamma_exposure,
            vanna_exposure=vec.vanna_exposure,
            charm_exposure=vec.charm_exposure,
            net_exposure=vec.net_exposure,
        ))

    total_gex = sum(e.gamma_exposure for e in exposures)
    total_vex = sum(e.vanna_exposure for e in exposures)
    total_cex = sum(e.charm_exposure for e in exposures)
    total_net = total_gex + total_vex + total_cex

    by_gamma = sorted(exposures, key=lambda e: e.gamma_exposure, reverse=True)
    by_vanna = sorted(exposures, key=lambda e: e.vanna_exposure, reverse=True)
    by_charm = sorted(exposures, key=lambda e: e.charm_exposure, reverse=True)
    by_net = sorted(exposures, key=lambda e: e.net_exposure, reverse=True)

    return ExposureModeBreakdown(
        total_gamma_exposure=_sanitize(total_gex),
        total_vanna_exposure=_sanitize(total_vex),
        total_charm_exposure=_sanitize(total_cex),
        total_net_exposure=_sanitize(total_net),
        strike_of_max_gamma=by_gamma[0].strike_price,
        strike_of_min_gamma=by_gamma[-1].strike_price,
        strike_of_max_vanna=by_vanna[0].strike_price,
        strike_of_min_vanna=by_vanna[-1].strike_price,
        strike_of_max_charm=by_charm[0].strike_price,
        strike_of_min_charm=by_charm[-1].strike_price,
        strike_of_max_net=by_net[0].strike_price,
        strike_of_min_net=by_net[-1].strike_price,
        strike_exposures=by_net,
    )
