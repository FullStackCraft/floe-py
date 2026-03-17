"""Statistical utility functions for options analytics."""

import math


def cumulative_normal_distribution(x: float) -> float:
    """CDF of the standard normal distribution (Abramowitz & Stegun approximation)."""
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989423 * math.exp(-x * x / 2.0)
    probability = d * t * (
        0.3193815
        + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))
    )
    if x > 0:
        return 1.0 - probability
    return probability


def normal_pdf(x: float) -> float:
    """PDF of the standard normal distribution."""
    return math.exp(-x * x / 2.0) / math.sqrt(2.0 * math.pi)
