"""IV surface construction and total-variance cubic-spline smoothing."""

from __future__ import annotations

import math

from floe.blackscholes import calculate_implied_volatility, get_time_to_expiration_in_years
from floe.types import (
    MILLISECONDS_PER_YEAR,
    IVSurface,
    OptionChain,
    OptionType,
    SmoothingModel,
)

_IV_FLOOR = 1.5
_MIN_POINTS_FOR_SMOOTHING = 5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_iv_surfaces(
    smoothing_model: SmoothingModel,
    chain: OptionChain,
    as_of_timestamp: int,
) -> list[IVSurface]:
    """Build IV surfaces for every expiration in the option chain."""
    groups: dict[tuple[int, OptionType], list] = {}

    for opt in chain.options:
        key = (opt.expiration_timestamp, opt.option_type)
        groups.setdefault(key, []).append(opt)

    surfaces: list[IVSurface] = []

    for (exp, opt_type), opts in groups.items():
        opts.sort(key=lambda o: o.strike)

        strikes = [o.strike for o in opts]
        tte = get_time_to_expiration_in_years(exp, as_of_timestamp)

        raw_ivs = [
            calculate_implied_volatility(
                o.mark, chain.spot, o.strike,
                chain.risk_free_rate, chain.dividend_yield,
                tte, o.option_type,
            )
            for o in opts
        ]

        smoothed_ivs = list(raw_ivs)

        if smoothing_model == "totalvariance" and exp > as_of_timestamp:
            valid_strikes: list[float] = []
            valid_ivs: list[float] = []
            valid_indices: list[int] = []

            for i, iv in enumerate(raw_ivs):
                if iv > _IV_FLOOR:
                    valid_strikes.append(strikes[i])
                    valid_ivs.append(raw_ivs[i])
                    valid_indices.append(i)

            if len(valid_strikes) >= _MIN_POINTS_FOR_SMOOTHING:
                T = float(exp - as_of_timestamp) / MILLISECONDS_PER_YEAR
                smoothed = smooth_total_variance_smile(valid_strikes, valid_ivs, T)
                for j, idx in enumerate(valid_indices):
                    smoothed_ivs[idx] = smoothed[j]

        surfaces.append(IVSurface(
            expiration_date=exp,
            put_call=opt_type,
            strikes=strikes,
            raw_ivs=raw_ivs,
            smoothed_ivs=smoothed_ivs,
        ))

    surfaces.sort(key=lambda s: (s.expiration_date, s.put_call))
    return surfaces


def get_iv_for_strike(
    iv_surfaces: list[IVSurface],
    expiration: int,
    option_type: OptionType,
    strike: float,
) -> float:
    """Look up the smoothed IV for a specific strike. Returns 0 if not found."""
    for surface in iv_surfaces:
        if surface.expiration_date != expiration or surface.put_call != option_type:
            continue
        for i, s in enumerate(surface.strikes):
            if s == strike:
                return surface.smoothed_ivs[i]
        return 0.0
    return 0.0


# ---------------------------------------------------------------------------
# Total-variance smoothing
# ---------------------------------------------------------------------------


def smooth_total_variance_smile(
    strikes: list[float],
    ivs: list[float],
    T: float,
) -> list[float]:
    """Smooth an IV smile using cubic spline in total-variance space with convexity enforcement.

    strikes and ivs are parallel lists; ivs are in percent (e.g. 20.0 = 20%).
    T is time to expiration in years.
    """
    n = len(strikes)
    if n <= 2:
        return list(ivs)

    # Convert IV% to total variance.
    w = [(iv / 100.0) ** 2 * T for iv in ivs]

    # Fit cubic spline on w(K).
    spline = _CubicSpline(strikes, w)

    # Evaluate spline at each original strike.
    w_smooth = [spline.eval(k) for k in strikes]

    # Enforce convexity.
    w_convex = _enforce_convexity(strikes, w_smooth)

    # Convert back to IV%.
    result: list[float] = []
    for i in range(n):
        if w_convex[i] <= 0:
            result.append(ivs[i])
        else:
            result.append(math.sqrt(w_convex[i] / T) * 100.0)
    return result


# ---------------------------------------------------------------------------
# Natural cubic spline
# ---------------------------------------------------------------------------


class _CubicSpline:
    """Natural cubic spline interpolator."""

    __slots__ = ("x", "a", "b", "c", "d", "n")

    def __init__(self, x: list[float], y: list[float]) -> None:
        n = len(x) - 1  # number of intervals
        self.x = x
        self.n = n

        a = list(y)

        h = [x[i + 1] - x[i] for i in range(n)]

        alpha = [0.0] * (n + 1)
        for i in range(1, n):
            alpha[i] = (3.0 / h[i]) * (a[i + 1] - a[i]) - (3.0 / h[i - 1]) * (a[i] - a[i - 1])

        # Tridiagonal solve with natural boundary conditions.
        l = [0.0] * (n + 1)
        mu = [0.0] * (n + 1)
        z = [0.0] * (n + 1)
        l[0] = 1.0

        for i in range(1, n):
            l[i] = 2.0 * (x[i + 1] - x[i - 1]) - h[i - 1] * mu[i - 1]
            mu[i] = h[i] / l[i]
            z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / l[i]

        l[n] = 1.0
        z[n] = 0.0

        b = [0.0] * n
        c = [0.0] * (n + 1)
        d = [0.0] * n
        c[n] = 0.0

        for j in range(n - 1, -1, -1):
            c[j] = z[j] - mu[j] * c[j + 1]
            b[j] = (a[j + 1] - a[j]) / h[j] - h[j] * (c[j + 1] + 2.0 * c[j]) / 3.0
            d[j] = (c[j + 1] - c[j]) / (3.0 * h[j])

        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def eval(self, xv: float) -> float:
        """Evaluate the spline at *xv* using binary search."""
        if xv <= self.x[0]:
            return self.a[0]
        if xv >= self.x[self.n]:
            return self.a[self.n]

        lo, hi = 0, self.n - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if xv < self.x[mid]:
                hi = mid - 1
            elif xv >= self.x[mid + 1]:
                lo = mid + 1
            else:
                lo = mid
                break

        i = lo
        dx = xv - self.x[i]
        return self.a[i] + self.b[i] * dx + self.c[i] * dx * dx + self.d[i] * dx * dx * dx


# ---------------------------------------------------------------------------
# Convexity enforcement via lower convex hull
# ---------------------------------------------------------------------------


def _enforce_convexity(x: list[float], w: list[float]) -> list[float]:
    n = len(x)
    if n <= 2:
        return list(w)

    points = list(zip(x, w))

    hull: list[tuple[float, float]] = []
    for p in points:
        while len(hull) >= 2:
            h1 = hull[-2]
            h2 = hull[-1]
            cross = (h2[0] - h1[0]) * (p[1] - h1[1]) - (h2[1] - h1[1]) * (p[0] - h1[0])
            if cross >= 0:
                hull.pop()
            else:
                break
        hull.append(p)

    result = [0.0] * n
    hi_idx = 0
    for i in range(n):
        xi = x[i]

        while hi_idx < len(hull) - 2 and hull[hi_idx + 1][0] < xi:
            hi_idx += 1

        if hi_idx >= len(hull) - 1:
            result[i] = hull[-1][1]
        else:
            p0 = hull[hi_idx]
            p1 = hull[hi_idx + 1]
            dx = p1[0] - p0[0]
            if dx == 0:
                result[i] = p0[1]
            else:
                t = (xi - p0[0]) / dx
                result[i] = p0[1] + t * (p1[1] - p0[1])

    return result
