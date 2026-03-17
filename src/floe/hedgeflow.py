"""Hedge impulse curve, charm integral, regime derivation, and pressure cloud."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from floe.types import ExposurePerExpiry, IVSurface

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

MarketRegime = Literal["calm", "normal", "stressed", "crisis"]
ImpulseRegime = Literal["pinned", "expansion", "squeeze-up", "squeeze-down", "neutral"]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RegimeParams:
    atm_iv: float = 0.0
    implied_spot_vol_corr: float = 0.0
    implied_vol_of_vol: float = 0.0
    regime: MarketRegime = "normal"
    expected_daily_spot_move: float = 0.0
    expected_daily_vol_move: float = 0.0


@dataclass
class HedgeImpulseConfig:
    range_percent: float = 3.0
    step_percent: float = 0.05
    kernel_width_strikes: float = 2.0


@dataclass
class HedgeImpulsePoint:
    price: float = 0.0
    gamma: float = 0.0
    vanna: float = 0.0
    impulse: float = 0.0


@dataclass
class ZeroCrossing:
    price: float = 0.0
    direction: str = ""  # "rising" or "falling"


@dataclass
class ImpulseExtremum:
    price: float = 0.0
    impulse: float = 0.0
    type: str = ""  # "basin" or "peak"


@dataclass
class DirectionalAsymmetry:
    upside: float = 0.0
    downside: float = 0.0
    integration_range_percent: float = 0.0
    bias: str = "neutral"  # "up", "down", "neutral"
    asymmetry_ratio: float = 0.0


@dataclass
class HedgeImpulseCurve:
    spot: float = 0.0
    expiration: int = 0
    computed_at: int = 0
    spot_vol_coupling: float = 0.0
    kernel_width: float = 0.0
    strike_spacing: float = 0.0
    curve: list[HedgeImpulsePoint] = field(default_factory=list)
    impulse_at_spot: float = 0.0
    slope_at_spot: float = 0.0
    zero_crossings: list[ZeroCrossing] = field(default_factory=list)
    extrema: list[ImpulseExtremum] = field(default_factory=list)
    asymmetry: DirectionalAsymmetry = field(default_factory=DirectionalAsymmetry)
    regime: ImpulseRegime = "neutral"
    nearest_attractor_above: float | None = None
    nearest_attractor_below: float | None = None


@dataclass
class CharmIntegralConfig:
    time_step_minutes: float = 15.0


@dataclass
class CharmBucket:
    minutes_remaining: float = 0.0
    instantaneous_cex: float = 0.0
    cumulative_cex: float = 0.0


@dataclass
class StrikeContribution:
    strike: float = 0.0
    charm_exposure: float = 0.0
    fraction_of_total: float = 0.0


@dataclass
class CharmIntegral:
    spot: float = 0.0
    expiration: int = 0
    computed_at: int = 0
    minutes_remaining: float = 0.0
    total_charm_to_close: float = 0.0
    direction: str = "neutral"
    buckets: list[CharmBucket] = field(default_factory=list)
    strike_contributions: list[StrikeContribution] = field(default_factory=list)


@dataclass
class HedgeFlowAnalysis:
    impulse_curve: HedgeImpulseCurve = field(default_factory=HedgeImpulseCurve)
    charm_integral: CharmIntegral = field(default_factory=CharmIntegral)
    regime_params: RegimeParams = field(default_factory=RegimeParams)


# ---- Pressure Cloud types ----


@dataclass
class HedgeContractEstimates:
    nq: float = 0.0
    mnq: float = 0.0
    es: float = 0.0
    mes: float = 0.0


@dataclass
class PressureZone:
    center: float = 0.0
    lower: float = 0.0
    upper: float = 0.0
    strength: float = 0.0
    side: str = ""
    trade_type: str = ""
    hedge_type: str = ""


@dataclass
class RegimeEdge:
    price: float = 0.0
    transition_type: str = ""


@dataclass
class PressureLevel:
    price: float = 0.0
    stability_score: float = 0.0
    acceleration_score: float = 0.0
    expected_hedge_contracts: float = 0.0
    hedge_contracts: HedgeContractEstimates = field(default_factory=HedgeContractEstimates)
    hedge_type: str = "passive"


@dataclass
class PressureCloudConfig:
    contract_multiplier: float = 20.0
    reachability_multiple: float = 2.0
    zone_threshold: float = 0.15


@dataclass
class PressureCloud:
    spot: float = 0.0
    expiration: int = 0
    computed_at: int = 0
    stability_zones: list[PressureZone] = field(default_factory=list)
    acceleration_zones: list[PressureZone] = field(default_factory=list)
    regime_edges: list[RegimeEdge] = field(default_factory=list)
    price_levels: list[PressureLevel] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Product multipliers
# ---------------------------------------------------------------------------

_PRODUCT_MULTIPLIERS = {"NQ": 20.0, "MNQ": 2.0, "ES": 50.0, "MES": 5.0}

_SKEW_TO_CORR_SCALE = 0.15
_VOL_OF_VOL_SCALE = 2.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_hedge_flow(
    exposures: ExposurePerExpiry,
    iv_surface: IVSurface,
    impulse_config: HedgeImpulseConfig,
    charm_config: CharmIntegralConfig,
    computed_at: int,
) -> HedgeFlowAnalysis:
    """Compute complete hedge flow analysis for a single expiration."""
    rp = derive_regime_params(iv_surface, exposures.spot_price)
    ic = compute_hedge_impulse_curve(exposures, iv_surface, impulse_config, computed_at)
    ci = compute_charm_integral(exposures, charm_config, computed_at)
    return HedgeFlowAnalysis(impulse_curve=ic, charm_integral=ci, regime_params=rp)


def derive_regime_params(iv_surface: IVSurface, spot: float) -> RegimeParams:
    """Extract market regime parameters from an IV surface."""
    strikes = iv_surface.strikes
    ivs = iv_surface.smoothed_ivs

    atm_iv = interpolate_iv_at_strike(strikes, ivs, spot) / 100.0
    skew = _calculate_skew_at_spot(strikes, ivs, spot)
    implied_corr = _skew_to_correlation(skew)
    curvature = _calculate_curvature_at_spot(strikes, ivs, spot)
    vol_of_vol = _curvature_to_vol_of_vol(curvature, atm_iv)
    regime = _iv_to_regime(atm_iv)

    return RegimeParams(
        atm_iv=atm_iv,
        implied_spot_vol_corr=implied_corr,
        implied_vol_of_vol=vol_of_vol,
        regime=regime,
        expected_daily_spot_move=atm_iv / math.sqrt(252),
        expected_daily_vol_move=vol_of_vol / math.sqrt(252),
    )


def interpolate_iv_at_strike(
    strikes: list[float],
    ivs: list[float],
    target_strike: float,
) -> float:
    """Linearly interpolate IV at an arbitrary strike."""
    if not strikes or not ivs:
        return 20.0
    if len(strikes) == 1:
        return ivs[0]
    if target_strike <= strikes[0]:
        return ivs[0]
    if target_strike >= strikes[-1]:
        return ivs[-1]

    lower_idx, upper_idx = 0, len(strikes) - 1
    for i in range(len(strikes) - 1):
        if strikes[i] <= target_strike <= strikes[i + 1]:
            lower_idx, upper_idx = i, i + 1
            break

    dk = strikes[upper_idx] - strikes[lower_idx]
    if dk == 0:
        return ivs[lower_idx]
    t = (target_strike - strikes[lower_idx]) / dk
    return ivs[lower_idx] + t * (ivs[upper_idx] - ivs[lower_idx])


def compute_hedge_impulse_curve(
    exposures: ExposurePerExpiry,
    iv_surface: IVSurface,
    config: HedgeImpulseConfig,
    computed_at: int,
) -> HedgeImpulseCurve:
    """Compute the combined gamma-vanna hedge impulse curve."""
    cfg = HedgeImpulseConfig(
        range_percent=config.range_percent or 3.0,
        step_percent=config.step_percent or 0.05,
        kernel_width_strikes=config.kernel_width_strikes or 2.0,
    )

    spot = exposures.spot_price
    rp = derive_regime_params(iv_surface, spot)
    k = _derive_spot_vol_coupling(rp)

    strikes = [se.strike_price for se in exposures.strike_exposures]
    gex_values = [se.gamma_exposure for se in exposures.strike_exposures]
    vex_values = [se.vanna_exposure for se in exposures.strike_exposures]

    strike_spacing = _detect_strike_spacing(strikes)
    lam = cfg.kernel_width_strikes * strike_spacing

    grid_min = spot * (1 - cfg.range_percent / 100)
    grid_max = spot * (1 + cfg.range_percent / 100)
    grid_step = spot * (cfg.step_percent / 100)

    curve: list[HedgeImpulsePoint] = []
    price = grid_min
    while price <= grid_max:
        gamma = _kernel_smooth(strikes, gex_values, price, lam)
        vanna = _kernel_smooth(strikes, vex_values, price, lam)
        impulse = gamma - (k / price) * vanna
        curve.append(HedgeImpulsePoint(price=price, gamma=gamma, vanna=vanna, impulse=impulse))
        price += grid_step

    impulse_at_spot = _interpolate_impulse_at_price(curve, spot)
    slope_at_spot = _compute_slope_at_price(curve, spot)
    zero_crossings = _find_zero_crossings(curve)
    extrema = _find_extrema(curve)
    asymmetry = _compute_asymmetry(curve, spot, 0.5)
    regime = _classify_regime(impulse_at_spot, slope_at_spot, asymmetry, curve, spot)

    nearest_above: float | None = None
    nearest_below: float | None = None
    for e in extrema:
        if e.type == "basin" and e.price > spot:
            if nearest_above is None or e.price < nearest_above:
                nearest_above = e.price
        if e.type == "basin" and e.price < spot:
            if nearest_below is None or e.price > nearest_below:
                nearest_below = e.price

    return HedgeImpulseCurve(
        spot=spot,
        expiration=exposures.expiration,
        computed_at=computed_at,
        spot_vol_coupling=k,
        kernel_width=lam,
        strike_spacing=strike_spacing,
        curve=curve,
        impulse_at_spot=impulse_at_spot,
        slope_at_spot=slope_at_spot,
        zero_crossings=zero_crossings,
        extrema=extrema,
        asymmetry=asymmetry,
        regime=regime,
        nearest_attractor_above=nearest_above,
        nearest_attractor_below=nearest_below,
    )


def compute_charm_integral(
    exposures: ExposurePerExpiry,
    config: CharmIntegralConfig,
    computed_at: int,
) -> CharmIntegral:
    """Compute cumulative expected delta change from time decay."""
    step = config.time_step_minutes or 15.0
    spot = exposures.spot_price
    expiration = exposures.expiration
    ms_remaining = float(expiration - computed_at)
    minutes_remaining = max(0.0, ms_remaining / 60000.0)

    total_abs_charm = sum(abs(s.charm_exposure) for s in exposures.strike_exposures)

    contributions: list[StrikeContribution] = []
    for s in exposures.strike_exposures:
        if s.charm_exposure == 0:
            continue
        frac = abs(s.charm_exposure) / total_abs_charm if total_abs_charm > 0 else 0.0
        contributions.append(StrikeContribution(
            strike=s.strike_price,
            charm_exposure=s.charm_exposure,
            fraction_of_total=frac,
        ))
    contributions.sort(key=lambda c: abs(c.charm_exposure), reverse=True)

    if minutes_remaining <= 0:
        return CharmIntegral(
            spot=spot, expiration=expiration, computed_at=computed_at,
            minutes_remaining=0, total_charm_to_close=0, direction="neutral",
            buckets=[], strike_contributions=contributions,
        )

    total_cex = exposures.total_charm_exposure
    buckets: list[CharmBucket] = []
    cumulative_cex = 0.0

    t = minutes_remaining
    while t >= max(1.0, step):
        time_scaling = math.sqrt(minutes_remaining / t)
        instant_cex = total_cex * time_scaling
        bucket_fraction = step / 390.0
        bucket_contrib = instant_cex * bucket_fraction
        cumulative_cex += bucket_contrib
        buckets.append(CharmBucket(
            minutes_remaining=t,
            instantaneous_cex=instant_cex,
            cumulative_cex=cumulative_cex,
        ))
        t -= step

    direction = "neutral"
    if cumulative_cex > 0:
        direction = "buying"
    elif cumulative_cex < 0:
        direction = "selling"

    return CharmIntegral(
        spot=spot, expiration=expiration, computed_at=computed_at,
        minutes_remaining=minutes_remaining, total_charm_to_close=cumulative_cex,
        direction=direction, buckets=buckets, strike_contributions=contributions,
    )


def compute_pressure_cloud(
    impulse_curve: HedgeImpulseCurve,
    regime_params: RegimeParams,
    config: PressureCloudConfig,
    computed_at: int,
) -> PressureCloud:
    """Translate impulse curve into actionable trading zones."""
    cm = config.contract_multiplier or 20.0
    rm = config.reachability_multiple or 2.0
    zt = config.zone_threshold or 0.15

    spot = impulse_curve.spot
    expected_move = regime_params.expected_daily_spot_move * spot

    price_levels = _compute_price_levels(impulse_curve.curve, spot, expected_move, rm, cm)
    stability_zones = _extract_stability_zones(impulse_curve.extrema, impulse_curve.curve, spot, expected_move, rm, zt)
    acceleration_zones = _extract_acceleration_zones(impulse_curve.extrema, impulse_curve.curve, spot, expected_move, rm, zt)
    regime_edges = _convert_zero_crossings_to_edges(impulse_curve.zero_crossings, spot)

    return PressureCloud(
        spot=spot,
        expiration=impulse_curve.expiration,
        computed_at=computed_at,
        stability_zones=stability_zones,
        acceleration_zones=acceleration_zones,
        regime_edges=regime_edges,
        price_levels=price_levels,
    )


# ---------------------------------------------------------------------------
# Internal — regime
# ---------------------------------------------------------------------------


def _skew_to_correlation(skew: float) -> float:
    return max(-0.95, min(0.5, skew * _SKEW_TO_CORR_SCALE))


def _curvature_to_vol_of_vol(curvature: float, atm_iv: float) -> float:
    return math.sqrt(abs(curvature)) * _VOL_OF_VOL_SCALE * atm_iv


def _iv_to_regime(atm_iv: float) -> MarketRegime:
    if atm_iv < 0.15:
        return "calm"
    if atm_iv < 0.20:
        return "normal"
    if atm_iv < 0.35:
        return "stressed"
    return "crisis"


def _calculate_skew_at_spot(strikes: list[float], ivs: list[float], spot: float) -> float:
    if len(strikes) < 2:
        return 0.0

    lower_idx, upper_idx = 0, len(strikes) - 1
    for i in range(len(strikes) - 1):
        if strikes[i] <= spot <= strikes[i + 1]:
            lower_idx, upper_idx = i, i + 1
            break

    d_iv = ivs[upper_idx] - ivs[lower_idx]
    dk = strikes[upper_idx] - strikes[lower_idx]
    if dk <= 0:
        return 0.0
    return (d_iv / dk) * spot


def _calculate_curvature_at_spot(strikes: list[float], ivs: list[float], spot: float) -> float:
    if len(strikes) < 3:
        return 0.0

    center_idx = 0
    for i in range(len(strikes)):
        if abs(strikes[i] - spot) < abs(strikes[center_idx] - spot):
            center_idx = i

    if center_idx == 0 or center_idx == len(strikes) - 1:
        return 0.0

    h = (strikes[center_idx + 1] - strikes[center_idx - 1]) / 2
    if h <= 0:
        return 0.0

    iv_minus = ivs[center_idx - 1]
    iv_center = ivs[center_idx]
    iv_plus = ivs[center_idx + 1]

    return ((iv_plus - 2 * iv_center + iv_minus) / (h * h)) * spot * spot


# ---------------------------------------------------------------------------
# Internal — impulse curve
# ---------------------------------------------------------------------------


def _detect_strike_spacing(strikes: list[float]) -> float:
    if len(strikes) < 2:
        return 1.0

    gap_counts: dict[float, int] = {}
    for i in range(1, len(strikes)):
        gap = abs(strikes[i] - strikes[i - 1])
        if gap > 0:
            rounded = round(gap * 100) / 100
            gap_counts[rounded] = gap_counts.get(rounded, 0) + 1

    if not gap_counts:
        return 1.0

    return max(gap_counts, key=gap_counts.get)  # type: ignore[arg-type]


def _derive_spot_vol_coupling(rp: RegimeParams) -> float:
    k = -rp.implied_spot_vol_corr * rp.atm_iv * math.sqrt(252)
    return max(2.0, min(20.0, k))


def _kernel_smooth(strikes: list[float], values: list[float], eval_price: float, lam: float) -> float:
    weighted_sum = 0.0
    weight_sum = 0.0
    for i in range(len(strikes)):
        dist = (strikes[i] - eval_price) / lam
        w = math.exp(-(dist * dist))
        weighted_sum += values[i] * w
        weight_sum += w
    if weight_sum > 0:
        return weighted_sum / weight_sum
    return 0.0


def _interpolate_impulse_at_price(curve: list[HedgeImpulsePoint], price: float) -> float:
    if not curve:
        return 0.0
    if price <= curve[0].price:
        return curve[0].impulse
    if price >= curve[-1].price:
        return curve[-1].impulse

    for i in range(len(curve) - 1):
        if curve[i].price <= price <= curve[i + 1].price:
            t = (price - curve[i].price) / (curve[i + 1].price - curve[i].price)
            return curve[i].impulse + t * (curve[i + 1].impulse - curve[i].impulse)
    return 0.0


def _compute_slope_at_price(curve: list[HedgeImpulsePoint], price: float) -> float:
    if len(curve) < 3:
        return 0.0
    step = curve[1].price - curve[0].price
    above = _interpolate_impulse_at_price(curve, price + step)
    below = _interpolate_impulse_at_price(curve, price - step)
    return (above - below) / (2 * step)


def _find_zero_crossings(curve: list[HedgeImpulsePoint]) -> list[ZeroCrossing]:
    crossings: list[ZeroCrossing] = []
    for i in range(len(curve) - 1):
        a = curve[i].impulse
        b = curve[i + 1].impulse
        if a * b < 0:
            t = abs(a) / (abs(a) + abs(b))
            cross_price = curve[i].price + t * (curve[i + 1].price - curve[i].price)
            direction = "rising" if b > a else "falling"
            crossings.append(ZeroCrossing(price=cross_price, direction=direction))
    return crossings


def _find_extrema(curve: list[HedgeImpulsePoint]) -> list[ImpulseExtremum]:
    extrema: list[ImpulseExtremum] = []
    for i in range(1, len(curve) - 1):
        prev_val = curve[i - 1].impulse
        curr = curve[i].impulse
        next_val = curve[i + 1].impulse

        if curr > prev_val and curr > next_val and curr > 0:
            extrema.append(ImpulseExtremum(price=curve[i].price, impulse=curr, type="basin"))
        if curr < prev_val and curr < next_val and curr < 0:
            extrema.append(ImpulseExtremum(price=curve[i].price, impulse=curr, type="peak"))
    return extrema


def _compute_asymmetry(
    curve: list[HedgeImpulsePoint],
    spot: float,
    integration_range_percent: float,
) -> DirectionalAsymmetry:
    range_price = spot * (integration_range_percent / 100)
    step = curve[1].price - curve[0].price if len(curve) > 1 else 1.0

    upside_integral = 0.0
    downside_integral = 0.0
    for pt in curve:
        if spot < pt.price <= spot + range_price:
            upside_integral += pt.impulse * step
        if spot - range_price <= pt.price < spot:
            downside_integral += pt.impulse * step

    bias = "neutral"
    threshold = max(abs(upside_integral), abs(downside_integral)) * 0.1
    if upside_integral < downside_integral - threshold:
        bias = "up"
    elif downside_integral < upside_integral - threshold:
        bias = "down"

    denom = max(abs(downside_integral), 1e-10)
    return DirectionalAsymmetry(
        upside=upside_integral,
        downside=downside_integral,
        integration_range_percent=integration_range_percent,
        bias=bias,
        asymmetry_ratio=abs(upside_integral) / denom,
    )


def _classify_regime(
    impulse_at_spot: float,
    slope_at_spot: float,
    asymmetry: DirectionalAsymmetry,
    curve: list[HedgeImpulsePoint],
    spot: float,
) -> ImpulseRegime:
    sum_abs = sum(abs(pt.impulse) for pt in curve)
    mean_abs = sum_abs / len(curve) if curve else 0.0
    if mean_abs == 0:
        return "neutral"

    normalized = impulse_at_spot / mean_abs

    if normalized > 0.5:
        return "pinned"
    if normalized < -0.3:
        if asymmetry.bias == "up":
            return "squeeze-up"
        if asymmetry.bias == "down":
            return "squeeze-down"
        return "expansion"

    if asymmetry.bias == "up" and asymmetry.asymmetry_ratio > 1.5:
        return "squeeze-up"
    if asymmetry.bias == "down" and asymmetry.asymmetry_ratio > 1.5:
        return "squeeze-down"

    return "neutral"


# ---------------------------------------------------------------------------
# Internal — pressure cloud
# ---------------------------------------------------------------------------


def _sanitize(v: float) -> float:
    if not math.isfinite(v):
        return 0.0
    return v


def _impulse_to_contracts(impulse: float, multiplier: float, spot: float) -> float:
    denom = multiplier * spot * 0.01
    if denom > 0:
        return _sanitize(impulse / denom)
    return 0.0


def _compute_hedge_contract_estimates(impulse: float, spot: float) -> HedgeContractEstimates:
    return HedgeContractEstimates(
        nq=_impulse_to_contracts(impulse, _PRODUCT_MULTIPLIERS["NQ"], spot),
        mnq=_impulse_to_contracts(impulse, _PRODUCT_MULTIPLIERS["MNQ"], spot),
        es=_impulse_to_contracts(impulse, _PRODUCT_MULTIPLIERS["ES"], spot),
        mes=_impulse_to_contracts(impulse, _PRODUCT_MULTIPLIERS["MES"], spot),
    )


def _compute_price_levels(
    curve: list[HedgeImpulsePoint],
    spot: float,
    expected_move: float,
    reachability_multiple: float,
    contract_multiplier: float,
) -> list[PressureLevel]:
    reach_range = expected_move * reachability_multiple
    levels: list[PressureLevel] = []

    for pt in curve:
        distance = abs(pt.price - spot)
        proximity = math.exp(-(distance / reach_range) ** 2) if reach_range > 0 else 0.0

        stability_score = pt.impulse * proximity if pt.impulse > 0 else 0.0
        acceleration_score = abs(pt.impulse) * proximity if pt.impulse < 0 else 0.0

        contract_denom = contract_multiplier * spot * 0.01
        hedge_contracts = pt.impulse / contract_denom if contract_denom > 0 else 0.0

        levels.append(PressureLevel(
            price=pt.price,
            stability_score=stability_score,
            acceleration_score=acceleration_score,
            expected_hedge_contracts=_sanitize(hedge_contracts),
            hedge_contracts=_compute_hedge_contract_estimates(pt.impulse, spot),
            hedge_type="passive" if pt.impulse >= 0 else "aggressive",
        ))
    return levels


def _extract_stability_zones(
    extrema: list[ImpulseExtremum],
    curve: list[HedgeImpulsePoint],
    spot: float,
    expected_move: float,
    reachability_multiple: float,
    zone_threshold: float,
) -> list[PressureZone]:
    basins = [e for e in extrema if e.type == "basin"]
    if not basins:
        return []

    reach_range = expected_move * reachability_multiple
    max_impulse = max(abs(b.impulse) for b in basins) or 1e-10

    zones: list[PressureZone] = []
    for basin in basins:
        if abs(basin.impulse) / max_impulse < zone_threshold:
            continue

        proximity = math.exp(-((abs(basin.price - spot) / reach_range) ** 2)) if reach_range > 0 else 0.0
        raw_strength = (abs(basin.impulse) / max_impulse) * proximity

        half_peak = basin.impulse * 0.5
        lower, upper = _find_zone_bounds(curve, basin.price, half_peak)

        side = "above-spot" if basin.price >= spot else "below-spot"
        trade_type = "short" if side == "above-spot" else "long"

        zones.append(PressureZone(
            center=basin.price, lower=lower, upper=upper,
            strength=min(1.0, raw_strength), side=side,
            trade_type=trade_type, hedge_type="passive",
        ))

    zones.sort(key=lambda z: z.strength, reverse=True)
    return zones


def _extract_acceleration_zones(
    extrema: list[ImpulseExtremum],
    curve: list[HedgeImpulsePoint],
    spot: float,
    expected_move: float,
    reachability_multiple: float,
    zone_threshold: float,
) -> list[PressureZone]:
    peaks = [e for e in extrema if e.type == "peak"]
    if not peaks:
        return []

    reach_range = expected_move * reachability_multiple
    max_impulse = max(abs(p.impulse) for p in peaks) or 1e-10

    zones: list[PressureZone] = []
    for peak in peaks:
        if abs(peak.impulse) / max_impulse < zone_threshold:
            continue

        proximity = math.exp(-((abs(peak.price - spot) / reach_range) ** 2)) if reach_range > 0 else 0.0
        raw_strength = (abs(peak.impulse) / max_impulse) * proximity

        half_trough = peak.impulse * 0.5
        lower, upper = _find_zone_bounds(curve, peak.price, half_trough)

        side = "above-spot" if peak.price >= spot else "below-spot"
        trade_type = "long" if side == "above-spot" else "short"

        zones.append(PressureZone(
            center=peak.price, lower=lower, upper=upper,
            strength=min(1.0, raw_strength), side=side,
            trade_type=trade_type, hedge_type="aggressive",
        ))

    zones.sort(key=lambda z: z.strength, reverse=True)
    return zones


def _find_zone_bounds(
    curve: list[HedgeImpulsePoint],
    center_price: float,
    threshold_impulse: float,
) -> tuple[float, float]:
    center_idx = 0
    min_dist = float("inf")
    for i, pt in enumerate(curve):
        d = abs(pt.price - center_price)
        if d < min_dist:
            min_dist = d
            center_idx = i

    is_positive = threshold_impulse > 0

    lower_idx = center_idx
    for i in range(center_idx - 1, -1, -1):
        if is_positive:
            if curve[i].impulse < threshold_impulse:
                lower_idx = i
                break
        else:
            if curve[i].impulse > threshold_impulse:
                lower_idx = i
                break
        lower_idx = i

    upper_idx = center_idx
    for i in range(center_idx + 1, len(curve)):
        if is_positive:
            if curve[i].impulse < threshold_impulse:
                upper_idx = i
                break
        else:
            if curve[i].impulse > threshold_impulse:
                upper_idx = i
                break
        upper_idx = i

    return curve[lower_idx].price, curve[upper_idx].price


def _convert_zero_crossings_to_edges(
    crossings: list[ZeroCrossing],
    spot: float,
) -> list[RegimeEdge]:
    edges: list[RegimeEdge] = []
    for c in crossings:
        is_below = c.price < spot
        if c.direction == "falling":
            trans = "stable-to-unstable" if is_below else "unstable-to-stable"
        else:
            trans = "unstable-to-stable" if is_below else "stable-to-unstable"
        edges.append(RegimeEdge(price=c.price, transition_type=trans))
    return edges
