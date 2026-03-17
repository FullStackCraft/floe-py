"""Tests for floe.hedgeflow."""

from floe.hedgeflow import (
    CharmIntegralConfig,
    HedgeImpulseConfig,
    PressureCloudConfig,
    analyze_hedge_flow,
    compute_charm_integral,
    compute_hedge_impulse_curve,
    compute_pressure_cloud,
    derive_regime_params,
)
from floe.types import ExposurePerExpiry, IVSurface, StrikeExposure


def _surface() -> IVSurface:
    return IVSurface(
        expiration_date=1_000_000 + 30 * 86_400_000,
        put_call="call",
        strikes=[480, 490, 500, 510, 520],
        raw_ivs=[25, 22, 20, 22, 25],
        smoothed_ivs=[25, 22, 20, 22, 25],
    )


def _exposures() -> ExposurePerExpiry:
    return ExposurePerExpiry(
        spot_price=500,
        expiration=1_000_000 + 30 * 86_400_000,
        total_gamma_exposure=1_000_000,
        total_vanna_exposure=-500_000,
        total_charm_exposure=-200_000,
        strike_exposures=[
            StrikeExposure(strike_price=490, gamma_exposure=500_000, vanna_exposure=-300_000, charm_exposure=-100_000),
            StrikeExposure(strike_price=495, gamma_exposure=300_000, vanna_exposure=-200_000, charm_exposure=-50_000),
            StrikeExposure(strike_price=500, gamma_exposure=-200_000, vanna_exposure=100_000, charm_exposure=50_000),
            StrikeExposure(strike_price=505, gamma_exposure=100_000, vanna_exposure=-50_000, charm_exposure=-50_000),
            StrikeExposure(strike_price=510, gamma_exposure=300_000, vanna_exposure=-50_000, charm_exposure=-50_000),
        ],
    )


def test_derive_regime_params_returns_valid_regime():
    rp = derive_regime_params(_surface(), 500)
    assert rp.regime in {"calm", "normal", "stressed", "crisis"}
    assert rp.atm_iv > 0


def test_compute_hedge_impulse_curve_produces_points():
    curve = compute_hedge_impulse_curve(_exposures(), _surface(), HedgeImpulseConfig(), 1_000_000)
    assert len(curve.curve) > 0
    assert 2 <= curve.spot_vol_coupling <= 20


def test_compute_charm_integral_returns_buckets():
    charm = compute_charm_integral(_exposures(), CharmIntegralConfig(), 1_000_000)
    assert charm.minutes_remaining > 0
    assert len(charm.buckets) > 0


def test_compute_pressure_cloud_returns_price_levels():
    surface = _surface()
    exposures = _exposures()
    curve = compute_hedge_impulse_curve(exposures, surface, HedgeImpulseConfig(), 1_000_000)
    regime = derive_regime_params(surface, 500)
    cloud = compute_pressure_cloud(curve, regime, PressureCloudConfig(), 1_000_000)
    assert len(cloud.price_levels) > 0


def test_analyze_hedge_flow_composes_outputs():
    analysis = analyze_hedge_flow(_exposures(), _surface(), HedgeImpulseConfig(), CharmIntegralConfig(), 1_000_000)
    assert len(analysis.impulse_curve.curve) > 0
    assert analysis.regime_params.atm_iv > 0
