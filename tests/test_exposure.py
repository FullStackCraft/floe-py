"""Tests for floe.exposure."""

import time

from floe.exposure import calculate_gamma_vanna_charm_exposures, calculate_shares_needed_to_cover
from floe.types import ExposureCalculationOptions, NormalizedOption, OptionChain
from floe.volatility import get_iv_surfaces


def _make_chain() -> tuple[OptionChain, int]:
    now = int(time.time() * 1000)
    exp = now + 7 * 24 * 60 * 60 * 1000

    options = [
        NormalizedOption(strike=440, expiration_timestamp=exp, option_type="call", bid=13.1, ask=13.3, mark=13.2, open_interest=21000, implied_volatility=0.19),
        NormalizedOption(strike=440, expiration_timestamp=exp, option_type="put", bid=2.8, ask=3.0, mark=2.9, open_interest=18000, implied_volatility=0.20),
        NormalizedOption(strike=445, expiration_timestamp=exp, option_type="call", bid=9.0, ask=9.2, mark=9.1, open_interest=28000, implied_volatility=0.18),
        NormalizedOption(strike=445, expiration_timestamp=exp, option_type="put", bid=4.9, ask=5.1, mark=5.0, open_interest=25000, implied_volatility=0.19),
        NormalizedOption(strike=450, expiration_timestamp=exp, option_type="call", bid=5.7, ask=5.9, mark=5.8, open_interest=36000, implied_volatility=0.17),
        NormalizedOption(strike=450, expiration_timestamp=exp, option_type="put", bid=8.3, ask=8.5, mark=8.4, open_interest=34000, implied_volatility=0.18),
    ]

    chain = OptionChain(symbol="SPY", spot=447.5, risk_free_rate=0.05, dividend_yield=0.01, options=options)
    return chain, now


def test_calculate_gamma_vanna_charm_exposures_returns_expiry_results():
    chain, now = _make_chain()
    surfaces = get_iv_surfaces("totalvariance", chain, now)

    variants = calculate_gamma_vanna_charm_exposures(
        chain,
        surfaces,
        ExposureCalculationOptions(as_of_timestamp=now),
    )

    assert len(variants) == 1
    assert variants[0].canonical.total_gamma_exposure != 0


def test_calculate_shares_needed_to_cover_positive_exposure():
    result = calculate_shares_needed_to_cover(1_000_000_000, 5_000_000, 500)
    assert result.action_to_cover == "SELL"
    assert result.shares_to_cover > 0


def test_calculate_shares_needed_to_cover_negative_exposure():
    result = calculate_shares_needed_to_cover(1_000_000_000, -5_000_000, 500)
    assert result.action_to_cover == "BUY"
    assert result.shares_to_cover > 0
