"""Vol response z-score model using OLS regression with ridge regularization."""

from __future__ import annotations

import math
from dataclasses import dataclass

_NUM_FEATURES = 5
_RIDGE_LAMBDA = 1e-8


@dataclass
class VolResponseObservation:
    timestamp: int = 0
    delta_iv: float = 0.0
    spot_return: float = 0.0
    abs_spot_return: float = 0.0
    rv_level: float = 0.0
    iv_level: float = 0.0


@dataclass
class VolResponseCoefficients:
    intercept: float = 0.0
    beta_return: float = 0.0
    beta_abs_return: float = 0.0
    beta_rv: float = 0.0
    beta_iv_level: float = 0.0


@dataclass
class VolResponseConfig:
    min_observations: int = 30
    vol_bid_threshold: float = 1.5
    vol_offered_threshold: float = -1.5


@dataclass
class VolResponseResult:
    is_valid: bool = False
    min_observations: int = 0
    num_observations: int = 0
    coefficients: VolResponseCoefficients | None = None
    r_squared: float = 0.0
    residual_std_dev: float = 0.0
    expected_delta_iv: float = 0.0
    observed_delta_iv: float = 0.0
    residual: float = 0.0
    z_score: float = 0.0
    signal: str = "insufficient_data"
    timestamp: int = 0


def build_vol_response_observation(
    current_iv: float,
    current_rv: float,
    current_spot: float,
    current_timestamp: int,
    previous_iv: float,
    previous_spot: float,
) -> VolResponseObservation:
    """Create an observation from consecutive readings."""
    delta_iv = current_iv - previous_iv
    spot_return = math.log(current_spot / previous_spot)
    return VolResponseObservation(
        timestamp=current_timestamp,
        delta_iv=delta_iv,
        spot_return=spot_return,
        abs_spot_return=abs(spot_return),
        rv_level=current_rv,
        iv_level=current_iv,
    )


def compute_vol_response_z_score(
    observations: list[VolResponseObservation],
    config: VolResponseConfig | None = None,
) -> VolResponseResult:
    """Fit OLS regression and compute z-score of most recent IV residual.

    deltaIV(t) ~ a + b1*return + b2*|return| + b3*RV + b4*IV_level
    """
    if config is None:
        config = VolResponseConfig()

    min_obs = config.min_observations or 30
    bid_thresh = config.vol_bid_threshold or 1.5
    off_thresh = config.vol_offered_threshold or -1.5

    empty = VolResponseCoefficients()
    n = len(observations)

    if n < min_obs:
        ts = observations[-1].timestamp if n > 0 else 0
        obs_iv = observations[-1].delta_iv if n > 0 else 0.0
        return VolResponseResult(
            is_valid=False, min_observations=min_obs, num_observations=n,
            coefficients=empty, observed_delta_iv=obs_iv,
            signal="insufficient_data", timestamp=ts,
        )

    X = [[1.0, o.spot_return, o.abs_spot_return, o.rv_level, o.iv_level] for o in observations]
    y = [o.delta_iv for o in observations]

    ols = _solve_ols(X, y)
    if ols is None:
        return VolResponseResult(
            is_valid=False, min_observations=min_obs, num_observations=n,
            coefficients=empty, observed_delta_iv=observations[-1].delta_iv,
            signal="insufficient_data", timestamp=observations[-1].timestamp,
        )

    last_obs = observations[-1]
    last_x = X[-1]

    expected = sum(ols["beta"][j] * last_x[j] for j in range(_NUM_FEATURES))
    residual = last_obs.delta_iv - expected
    z_score = residual / ols["residual_std_dev"] if ols["residual_std_dev"] > 0 else 0.0

    signal = "neutral"
    if z_score > bid_thresh:
        signal = "vol_bid"
    elif z_score < off_thresh:
        signal = "vol_offered"

    return VolResponseResult(
        is_valid=True,
        min_observations=min_obs,
        num_observations=n,
        coefficients=VolResponseCoefficients(
            intercept=ols["beta"][0],
            beta_return=ols["beta"][1],
            beta_abs_return=ols["beta"][2],
            beta_rv=ols["beta"][3],
            beta_iv_level=ols["beta"][4],
        ),
        r_squared=ols["r_squared"],
        residual_std_dev=ols["residual_std_dev"],
        expected_delta_iv=expected,
        observed_delta_iv=last_obs.delta_iv,
        residual=residual,
        z_score=z_score,
        signal=signal,
        timestamp=last_obs.timestamp,
    )


# ---------------------------------------------------------------------------
# OLS solver via normal equations with ridge regularization
# ---------------------------------------------------------------------------


def _solve_ols(
    X: list[list[float]],
    y: list[float],
) -> dict | None:
    n = len(X)
    p = _NUM_FEATURES

    # X'X
    xtx = [[0.0] * p for _ in range(p)]
    for i in range(p):
        for j in range(p):
            s = 0.0
            for k in range(n):
                s += X[k][i] * X[k][j]
            xtx[i][j] = s

    # Ridge penalty (skip intercept).
    for i in range(1, p):
        xtx[i][i] += _RIDGE_LAMBDA

    # X'y
    xty = [0.0] * p
    for i in range(p):
        s = 0.0
        for k in range(n):
            s += X[k][i] * y[k]
        xty[i] = s

    # Augmented matrix [XtX | Xty]
    aug = [row[:] + [xty[i]] for i, row in enumerate(xtx)]

    # Gauss-Jordan elimination with partial pivoting.
    for col in range(p):
        max_val = abs(aug[col][col])
        max_row = col
        for row in range(col + 1, p):
            v = abs(aug[row][col])
            if v > max_val:
                max_val = v
                max_row = row
        if max_val < 1e-14:
            return None
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot = aug[col][col]
        for j in range(col, p + 1):
            aug[col][j] /= pivot
        for row in range(p):
            if row == col:
                continue
            factor = aug[row][col]
            for j in range(col, p + 1):
                aug[row][j] -= factor * aug[col][j]

    beta = [aug[i][p] for i in range(p)]
    for b in beta:
        if not math.isfinite(b):
            return None

    # Residuals and stats.
    y_mean = sum(y) / n
    ss_res = 0.0
    ss_tot = 0.0
    for i in range(n):
        predicted = sum(beta[j] * X[i][j] for j in range(p))
        res = y[i] - predicted
        ss_res += res * res
        ss_tot += (y[i] - y_mean) ** 2

    r_squared = max(0.0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    dof = max(n - p, 1)
    residual_std_dev = math.sqrt(ss_res / dof)

    return {"beta": beta, "r_squared": r_squared, "residual_std_dev": residual_std_dev}
