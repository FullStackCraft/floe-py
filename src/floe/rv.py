"""Realized volatility from tick-level price observations via quadratic variation."""

from __future__ import annotations

import math
from dataclasses import dataclass

_MILLISECONDS_PER_YEAR = 31_536_000_000.0


@dataclass
class PriceObservation:
    price: float = 0.0
    timestamp: float = 0.0  # milliseconds


@dataclass
class RealizedVolatilityResult:
    realized_volatility: float = 0.0
    annualized_variance: float = 0.0
    quadratic_variation: float = 0.0
    num_observations: int = 0
    num_returns: int = 0
    elapsed_minutes: float = 0.0
    elapsed_years: float = 0.0
    first_observation: float = 0.0
    last_observation: float = 0.0


def compute_realized_volatility(
    observations: list[PriceObservation],
) -> RealizedVolatilityResult:
    """Compute annualized realized volatility from price ticks.

    QV = sum(ln(Pi/Pi-1)^2)
    sigma = sqrt(QV / elapsed_years)
    """
    valid = [o for o in observations if o.price > 0 and math.isfinite(o.price)]

    if len(valid) < 2:
        return RealizedVolatilityResult(num_observations=len(valid))

    valid.sort(key=lambda o: o.timestamp)

    qv = 0.0
    for i in range(1, len(valid)):
        log_return = math.log(valid[i].price / valid[i - 1].price)
        qv += log_return * log_return

    first = valid[0].timestamp
    last = valid[-1].timestamp
    elapsed_ms = last - first
    elapsed_years = elapsed_ms / _MILLISECONDS_PER_YEAR

    if elapsed_years <= 0:
        return RealizedVolatilityResult(
            num_observations=len(valid),
            num_returns=len(valid) - 1,
            first_observation=first,
            last_observation=last,
        )

    annualized_variance = qv / elapsed_years
    rv = math.sqrt(annualized_variance)

    return RealizedVolatilityResult(
        realized_volatility=rv,
        annualized_variance=annualized_variance,
        quadratic_variation=qv,
        num_observations=len(valid),
        num_returns=len(valid) - 1,
        elapsed_minutes=elapsed_ms / 60000.0,
        elapsed_years=elapsed_years,
        first_observation=first,
        last_observation=last,
    )
