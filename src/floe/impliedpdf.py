"""Risk-neutral probability distribution estimation and exposure-adjusted PDFs."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

from floe.types import ExposurePerExpiry, NormalizedOption


@dataclass
class StrikeProbability:
    strike: float = 0.0
    probability: float = 0.0


@dataclass
class ImpliedProbabilityDistribution:
    symbol: str = ""
    expiry_date: int = 0
    calculation_timestamp: int = 0
    underlying_price: float = 0.0
    strike_probabilities: list[StrikeProbability] = field(default_factory=list)
    most_likely_price: float = 0.0
    median_price: float = 0.0
    expected_value: float = 0.0
    expected_move: float = 0.0
    tail_skew: float = 0.0
    cumulative_probability_above_spot: float = 0.0
    cumulative_probability_below_spot: float = 0.0


@dataclass
class ImpliedPDFResult:
    success: bool = False
    error: str = ""
    distribution: ImpliedProbabilityDistribution | None = None


@dataclass
class GammaConfig:
    enabled: bool = True
    attractor_strength: float = 0.3
    repellent_strength: float = 0.3
    threshold: float = 1_000_000.0
    decay_rate: float = 2.0


@dataclass
class VannaConfig:
    enabled: bool = True
    spot_vol_beta: float = -3.0
    max_tail_multiplier: float = 2.5
    feedback_iterations: int = 3


@dataclass
class CharmAdjConfig:
    enabled: bool = True
    time_horizon: str = "daily"  # intraday, daily, weekly
    shift_scale: float = 1.0


@dataclass
class ExposureAdjustmentConfig:
    gamma: GammaConfig = field(default_factory=GammaConfig)
    vanna: VannaConfig = field(default_factory=VannaConfig)
    charm: CharmAdjConfig = field(default_factory=CharmAdjConfig)


@dataclass
class TailComparison:
    baseline: float = 0.0
    adjusted: float = 0.0
    ratio: float = 0.0


@dataclass
class PDFComparison:
    mean_shift: float = 0.0
    mean_shift_percent: float = 0.0
    std_dev_change: float = 0.0
    tail_skew_change: float = 0.0
    left_tail: TailComparison = field(default_factory=TailComparison)
    right_tail: TailComparison = field(default_factory=TailComparison)
    dominant_factor: str = "none"  # gamma, vanna, charm, none


@dataclass
class AdjustedPDFResult:
    baseline: ImpliedProbabilityDistribution = field(default_factory=ImpliedProbabilityDistribution)
    adjusted: ImpliedProbabilityDistribution = field(default_factory=ImpliedProbabilityDistribution)
    gamma_modifiers: list[float] = field(default_factory=list)
    vanna_modifiers: list[float] = field(default_factory=list)
    charm_shift: float = 0.0
    comparison: PDFComparison = field(default_factory=PDFComparison)


@dataclass
class AdjustmentLevel:
    strike: float = 0.0
    baseline_prob: float = 0.0
    adjusted_prob: float = 0.0
    edge: float = 0.0


DEFAULT_ADJUSTMENT_CONFIG = ExposureAdjustmentConfig(
    gamma=GammaConfig(enabled=True, attractor_strength=0.3, repellent_strength=0.3, threshold=1_000_000.0, decay_rate=2.0),
    vanna=VannaConfig(enabled=True, spot_vol_beta=-3.0, max_tail_multiplier=2.5, feedback_iterations=3),
    charm=CharmAdjConfig(enabled=True, time_horizon="daily", shift_scale=1.0),
)

LOW_VOL_CONFIG = ExposureAdjustmentConfig(
    gamma=GammaConfig(enabled=True, attractor_strength=0.4, repellent_strength=0.2, threshold=500_000.0, decay_rate=1.5),
    vanna=VannaConfig(enabled=True, spot_vol_beta=-2.0, max_tail_multiplier=1.5, feedback_iterations=2),
    charm=CharmAdjConfig(enabled=True, time_horizon="daily", shift_scale=1.5),
)

CRISIS_CONFIG = ExposureAdjustmentConfig(
    gamma=GammaConfig(enabled=True, attractor_strength=0.1, repellent_strength=0.5, threshold=2_000_000.0, decay_rate=3.0),
    vanna=VannaConfig(enabled=True, spot_vol_beta=-5.0, max_tail_multiplier=3.0, feedback_iterations=5),
    charm=CharmAdjConfig(enabled=True, time_horizon="intraday", shift_scale=0.5),
)

OPEX_CONFIG = ExposureAdjustmentConfig(
    gamma=GammaConfig(enabled=True, attractor_strength=0.5, repellent_strength=0.4, threshold=1_000_000.0, decay_rate=2.5),
    vanna=VannaConfig(enabled=True, spot_vol_beta=-3.0, max_tail_multiplier=2.0, feedback_iterations=3),
    charm=CharmAdjConfig(enabled=True, time_horizon="intraday", shift_scale=2.0),
)


def estimate_implied_probability_distribution(
    symbol: str,
    underlying_price: float,
    call_options: list[NormalizedOption],
    calculation_timestamp: int,
) -> ImpliedPDFResult:
    """Compute the implied PDF for a single expiry using Breeden-Litzenberger."""
    sorted_opts = sorted(call_options, key=lambda o: o.strike)
    n = len(sorted_opts)

    if n < 3:
        return ImpliedPDFResult(success=False, error="Not enough data points (need at least 3 call options)")

    expiry_date = sorted_opts[0].expiration_timestamp

    probs = [StrikeProbability(strike=sorted_opts[0].strike, probability=0.0)]
    for i in range(1, n - 1):
        k_prev = sorted_opts[i - 1].strike
        k_next = sorted_opts[i + 1].strike

        mid_prev = (sorted_opts[i - 1].bid + sorted_opts[i - 1].ask) / 2.0
        mid_curr = (sorted_opts[i].bid + sorted_opts[i].ask) / 2.0
        mid_next = (sorted_opts[i + 1].bid + sorted_opts[i + 1].ask) / 2.0

        strike_diff = k_next - k_prev
        if abs(strike_diff) < 1e-9:
            probs.append(StrikeProbability(strike=sorted_opts[i].strike, probability=0.0))
            continue

        d2 = (mid_next - 2.0 * mid_curr + mid_prev) / (strike_diff * strike_diff)
        probs.append(StrikeProbability(strike=sorted_opts[i].strike, probability=max(d2, 0.0)))

    probs.append(StrikeProbability(strike=sorted_opts[n - 1].strike, probability=0.0))

    total = sum(sp.probability for sp in probs)
    if total < 1e-9:
        return ImpliedPDFResult(success=False, error="Insufficient probability mass to normalize")
    for sp in probs:
        sp.probability /= total

    most_likely = max(probs, key=lambda sp: sp.probability).strike

    cum = 0.0
    median = probs[n // 2].strike
    for sp in probs:
        cum += sp.probability
        if cum >= 0.5:
            median = sp.strike
            break

    mean = sum(sp.strike * sp.probability for sp in probs)
    variance = sum((sp.strike - mean) ** 2 * sp.probability for sp in probs)
    expected_move = math.sqrt(variance)

    left_tail = sum(sp.probability for sp in probs if sp.strike < mean)
    right_tail = sum(sp.probability for sp in probs if sp.strike >= mean)
    tail_skew = right_tail / max(left_tail, 1e-9)

    below = sum(sp.probability for sp in probs if sp.strike < underlying_price)
    above = sum(sp.probability for sp in probs if sp.strike > underlying_price)

    return ImpliedPDFResult(
        success=True,
        distribution=ImpliedProbabilityDistribution(
            symbol=symbol,
            expiry_date=expiry_date,
            calculation_timestamp=calculation_timestamp,
            underlying_price=underlying_price,
            strike_probabilities=probs,
            most_likely_price=most_likely,
            median_price=median,
            expected_value=mean,
            expected_move=expected_move,
            tail_skew=tail_skew,
            cumulative_probability_above_spot=above,
            cumulative_probability_below_spot=below,
        ),
    )


def estimate_implied_probability_distributions(
    symbol: str,
    underlying_price: float,
    options: list[NormalizedOption],
    calculation_timestamp: int,
) -> list[ImpliedProbabilityDistribution]:
    """Compute implied PDFs for all expirations."""
    expirations = sorted({opt.expiration_timestamp for opt in options})

    dists: list[ImpliedProbabilityDistribution] = []
    for exp in expirations:
        calls = [
            o
            for o in options
            if o.expiration_timestamp == exp and o.option_type == "call" and o.bid > 0 and o.ask > 0
        ]
        result = estimate_implied_probability_distribution(symbol, underlying_price, calls, calculation_timestamp)
        if result.success and result.distribution is not None:
            dists.append(result.distribution)
    return dists


def get_probability_in_range(
    dist: ImpliedProbabilityDistribution,
    lower: float,
    upper: float,
) -> float:
    """Return probability of finishing between two prices."""
    return sum(sp.probability for sp in dist.strike_probabilities if lower <= sp.strike <= upper)


def get_cumulative_probability(
    dist: ImpliedProbabilityDistribution,
    price: float,
) -> float:
    """Return P(S <= price)."""
    return sum(sp.probability for sp in dist.strike_probabilities if sp.strike <= price)


def get_quantile(
    dist: ImpliedProbabilityDistribution,
    probability: float,
) -> float:
    """Return the strike at the given probability quantile."""
    if not dist.strike_probabilities:
        return 0.0
    if probability <= 0:
        return dist.strike_probabilities[0].strike
    if probability >= 1:
        return dist.strike_probabilities[-1].strike

    cum = 0.0
    for sp in dist.strike_probabilities:
        cum += sp.probability
        if cum >= probability:
            return sp.strike
    return dist.strike_probabilities[-1].strike


def estimate_exposure_adjusted_pdf(
    symbol: str,
    underlying_price: float,
    call_options: list[NormalizedOption],
    exposures: ExposurePerExpiry,
    config: ExposureAdjustmentConfig | None,
    calculation_timestamp: int,
) -> AdjustedPDFResult:
    """Estimate exposure-adjusted implied PDF from baseline + GEX/VEX/CEX modifiers."""
    cfg = copy.deepcopy(config if config is not None else DEFAULT_ADJUSTMENT_CONFIG)

    baseline_result = estimate_implied_probability_distribution(
        symbol, underlying_price, call_options, calculation_timestamp
    )
    if not baseline_result.success or baseline_result.distribution is None:
        raise ValueError(baseline_result.error or "failed to estimate baseline implied PDF")

    baseline = baseline_result.distribution

    if cfg.gamma.enabled:
        gamma_modifiers = _calculate_gamma_modifiers(
            baseline.strike_probabilities,
            exposures,
            underlying_price,
            cfg.gamma,
        )
    else:
        gamma_modifiers = _ones(len(baseline.strike_probabilities))

    if cfg.vanna.enabled:
        vanna_modifiers = _calculate_vanna_modifiers(
            baseline.strike_probabilities,
            exposures,
            underlying_price,
            cfg.vanna,
        )
    else:
        vanna_modifiers = _ones(len(baseline.strike_probabilities))

    charm_shift = 0.0
    if cfg.charm.enabled:
        charm_shift = _calculate_charm_shift(exposures, underlying_price, cfg.charm)

    adjusted = _apply_modifiers(
        baseline.strike_probabilities,
        gamma_modifiers,
        vanna_modifiers,
        charm_shift,
    )
    normalized = _normalize_probabilities(adjusted)
    adjusted_dist = _recalculate_stats(baseline, normalized, underlying_price, calculation_timestamp)

    comparison = _calculate_comparison(
        baseline,
        adjusted_dist,
        gamma_modifiers,
        vanna_modifiers,
        charm_shift,
    )

    return AdjustedPDFResult(
        baseline=baseline,
        adjusted=adjusted_dist,
        gamma_modifiers=gamma_modifiers,
        vanna_modifiers=vanna_modifiers,
        charm_shift=charm_shift,
        comparison=comparison,
    )


def get_edge_at_price(result: AdjustedPDFResult, price: float) -> float:
    """Return adjusted minus baseline cumulative probability at a price."""
    return get_cumulative_probability(result.adjusted, price) - get_cumulative_probability(result.baseline, price)


def get_significant_adjustment_levels(
    result: AdjustedPDFResult,
    threshold: float,
) -> list[AdjustmentLevel]:
    """Return strikes with absolute probability adjustment above threshold."""
    if threshold == 0:
        threshold = 0.01

    levels: list[AdjustmentLevel] = []
    for i, baseline_sp in enumerate(result.baseline.strike_probabilities):
        adjusted_prob = (
            result.adjusted.strike_probabilities[i].probability
            if i < len(result.adjusted.strike_probabilities)
            else 0.0
        )
        edge = adjusted_prob - baseline_sp.probability
        if abs(edge) >= threshold:
            levels.append(
                AdjustmentLevel(
                    strike=baseline_sp.strike,
                    baseline_prob=baseline_sp.probability,
                    adjusted_prob=adjusted_prob,
                    edge=edge,
                )
            )

    levels.sort(key=lambda l: abs(l.edge), reverse=True)
    return levels


def _calculate_gamma_modifiers(
    probs: list[StrikeProbability],
    exposures: ExposurePerExpiry,
    spot: float,
    cfg: GammaConfig,
) -> list[float]:
    max_gex = 1.0
    for e in exposures.strike_exposures:
        max_gex = max(max_gex, abs(e.gamma_exposure))

    mods: list[float] = []
    for p in probs:
        mod = 1.0
        for e in exposures.strike_exposures:
            if abs(e.gamma_exposure) < cfg.threshold:
                continue
            dist = abs(p.strike - e.strike_price) / max(spot, 1e-12)
            influence = 1.0 / (1.0 + cfg.decay_rate * dist * dist)
            norm_gex = e.gamma_exposure / max_gex

            if e.gamma_exposure > 0:
                mod *= 1.0 + cfg.attractor_strength * norm_gex * influence
            else:
                mod *= 1.0 - cfg.repellent_strength * abs(norm_gex) * influence

        mods.append(max(0.1, min(3.0, mod)))
    return mods


def _calculate_vanna_modifiers(
    probs: list[StrikeProbability],
    exposures: ExposurePerExpiry,
    spot: float,
    cfg: VannaConfig,
) -> list[float]:
    vanna_below = 0.0
    vanna_above = 0.0
    for e in exposures.strike_exposures:
        if e.strike_price < spot:
            vanna_below += e.vanna_exposure
        else:
            vanna_above += e.vanna_exposure

    mods: list[float] = []
    for p in probs:
        mod = 1.0
        move_percent = (p.strike - spot) / max(spot, 1e-12)

        if move_percent < 0:
            iv_spike = -move_percent * abs(cfg.spot_vol_beta)
            vanna_flow = vanna_below * iv_spike
            if vanna_flow < 0:
                cum_effect = 0.0
                flow = abs(vanna_flow)
                for _ in range(cfg.feedback_iterations):
                    cum_effect += flow
                    flow *= 0.5
                effect_scale = cum_effect / (spot * 1_000_000.0)
                mod = 1.0 + min(cfg.max_tail_multiplier - 1.0, effect_scale)

        elif move_percent > 0:
            iv_compress = move_percent * abs(cfg.spot_vol_beta) * 0.5
            vanna_flow = vanna_above * (-iv_compress)
            if vanna_flow > 0:
                effect_scale = vanna_flow / (spot * 1_000_000.0)
                mod = max(0.5, 1.0 - effect_scale * 0.5)

        mods.append(mod)
    return mods


def _calculate_charm_shift(
    exposures: ExposurePerExpiry,
    spot: float,
    cfg: CharmAdjConfig,
) -> float:
    time_mult = 1.0
    if cfg.time_horizon == "intraday":
        time_mult = 0.25
    elif cfg.time_horizon == "daily":
        time_mult = 1.0
    elif cfg.time_horizon == "weekly":
        time_mult = 5.0

    flow_impact = 0.001 * spot
    price_shift = (exposures.total_charm_exposure / 1_000_000_000.0) * flow_impact * time_mult
    return price_shift * cfg.shift_scale


def _apply_modifiers(
    probs: list[StrikeProbability],
    gamma: list[float],
    vanna: list[float],
    charm_shift: float,
) -> list[StrikeProbability]:
    out: list[StrikeProbability] = []
    for i, sp in enumerate(probs):
        out.append(
            StrikeProbability(
                strike=sp.strike + charm_shift,
                probability=sp.probability * gamma[i] * vanna[i],
            )
        )
    return out


def _normalize_probabilities(probs: list[StrikeProbability]) -> list[StrikeProbability]:
    total = sum(sp.probability for sp in probs)
    if total < 1e-9:
        uniform = 1.0 / max(len(probs), 1)
        return [StrikeProbability(strike=sp.strike, probability=uniform) for sp in probs]

    return [StrikeProbability(strike=sp.strike, probability=sp.probability / total) for sp in probs]


def _recalculate_stats(
    baseline: ImpliedProbabilityDistribution,
    probs: list[StrikeProbability],
    underlying_price: float,
    calculation_timestamp: int,
) -> ImpliedProbabilityDistribution:
    mode = probs[0].strike if probs else 0.0
    max_prob = -1.0
    for sp in probs:
        if sp.probability > max_prob:
            max_prob = sp.probability
            mode = sp.strike

    cum = 0.0
    median = probs[len(probs) // 2].strike if probs else 0.0
    for sp in probs:
        cum += sp.probability
        if cum >= 0.5:
            median = sp.strike
            break

    mean = sum(sp.strike * sp.probability for sp in probs)
    variance = sum((sp.strike - mean) ** 2 * sp.probability for sp in probs)

    left_tail = sum(sp.probability for sp in probs if sp.strike < mean)
    right_tail = sum(sp.probability for sp in probs if sp.strike >= mean)

    below = sum(sp.probability for sp in probs if sp.strike < underlying_price)
    above = sum(sp.probability for sp in probs if sp.strike > underlying_price)

    return ImpliedProbabilityDistribution(
        symbol=baseline.symbol,
        expiry_date=baseline.expiry_date,
        calculation_timestamp=calculation_timestamp,
        underlying_price=underlying_price,
        strike_probabilities=probs,
        most_likely_price=mode,
        median_price=median,
        expected_value=mean,
        expected_move=math.sqrt(variance),
        tail_skew=right_tail / max(left_tail, 1e-9),
        cumulative_probability_above_spot=above,
        cumulative_probability_below_spot=below,
    )


def _calculate_comparison(
    baseline: ImpliedProbabilityDistribution,
    adjusted: ImpliedProbabilityDistribution,
    gamma: list[float],
    vanna: list[float],
    charm_shift: float,
) -> PDFComparison:
    b5 = get_quantile(baseline, 0.05)
    b95 = get_quantile(baseline, 0.95)
    a5 = get_quantile(adjusted, 0.05)
    a95 = get_quantile(adjusted, 0.95)

    gamma_effect = _max_float(gamma) - _min_float(gamma)
    vanna_effect = _max_float(vanna) - _min_float(vanna)
    charm_effect = abs(charm_shift) / max(baseline.underlying_price, 1e-12)

    dominant = "none"
    max_effect = max(gamma_effect, vanna_effect, charm_effect)
    if max_effect > 0.01:
        if gamma_effect == max_effect:
            dominant = "gamma"
        elif vanna_effect == max_effect:
            dominant = "vanna"
        else:
            dominant = "charm"

    return PDFComparison(
        mean_shift=adjusted.expected_value - baseline.expected_value,
        mean_shift_percent=((adjusted.expected_value - baseline.expected_value) / max(baseline.underlying_price, 1e-12)) * 100.0,
        std_dev_change=adjusted.expected_move - baseline.expected_move,
        tail_skew_change=adjusted.tail_skew - baseline.tail_skew,
        left_tail=TailComparison(baseline=b5, adjusted=a5, ratio=_safe_div(a5, b5)),
        right_tail=TailComparison(baseline=b95, adjusted=a95, ratio=_safe_div(a95, b95)),
        dominant_factor=dominant,
    )


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def _ones(n: int) -> list[float]:
    return [1.0] * n


def _max_float(values: list[float]) -> float:
    return max(values) if values else 0.0


def _min_float(values: list[float]) -> float:
    return min(values) if values else 0.0
