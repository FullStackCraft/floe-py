"""Tests for floe.volresponse."""

import math

from floe.volresponse import (
    VolResponseConfig,
    VolResponseObservation,
    build_vol_response_observation,
    compute_vol_response_z_score,
)


def _observations(n: int) -> list[VolResponseObservation]:
    out: list[VolResponseObservation] = []
    for i in range(n):
        t = float(i)
        out.append(
            VolResponseObservation(
                timestamp=i * 60_000,
                delta_iv=0.001 * math.sin(t * 0.1),
                spot_return=0.002 * math.cos(t * 0.1),
                abs_spot_return=abs(0.002 * math.cos(t * 0.1)),
                rv_level=0.15 + 0.01 * math.sin(t * 0.05),
                iv_level=0.20 + 0.01 * math.cos(t * 0.05),
            )
        )
    return out


def test_build_vol_response_observation():
    obs = build_vol_response_observation(0.21, 0.15, 501.0, 120_000, 0.20, 500.0)
    assert abs(obs.delta_iv - 0.01) < 1e-10
    assert obs.timestamp == 120_000


def test_compute_vol_response_z_score_insufficient_data():
    result = compute_vol_response_z_score(_observations(10), VolResponseConfig())
    assert result.is_valid is False
    assert result.signal == "insufficient_data"


def test_compute_vol_response_z_score_valid_result():
    result = compute_vol_response_z_score(_observations(50), VolResponseConfig())
    assert result.is_valid is True
    assert 0 <= result.r_squared <= 1
    assert result.signal in {"vol_bid", "vol_offered", "neutral"}


def test_compute_vol_response_z_score_custom_thresholds():
    result = compute_vol_response_z_score(
        _observations(50),
        VolResponseConfig(min_observations=20, vol_bid_threshold=0.5, vol_offered_threshold=-0.5),
    )
    assert result.is_valid is True
    assert result.min_observations == 20
