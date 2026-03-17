---
title: Recipes
description: Practical Python workflows combining floe modules.
order: 3
---

## Build IV Surfaces and Dealer Exposures

```python
import time

from floe import (
    ExposureCalculationOptions,
    OptionChain,
    calculate_gamma_vanna_charm_exposures,
    get_iv_surfaces,
)

now = int(time.time() * 1000)

chain = OptionChain(
    symbol="SPY",
    spot=450.5,
    risk_free_rate=0.05,
    dividend_yield=0.01,
    options=load_options(),
)

surfaces = get_iv_surfaces("totalvariance", chain, now)
variants = calculate_gamma_vanna_charm_exposures(
    chain,
    surfaces,
    ExposureCalculationOptions(as_of_timestamp=now),
)

for exp in variants:
    print(exp.expiration, exp.canonical.total_net_exposure, exp.canonical.strike_of_max_gamma)


def load_options():
    return []
```

## Use Market Price -> IV -> Greeks

```python
import time

from floe import (
    BlackScholesParams,
    calculate_greeks,
    calculate_implied_volatility,
    get_time_to_expiration_in_years,
)

now = int(time.time() * 1000)
expiry = now + 30 * 24 * 60 * 60 * 1000

tte = get_time_to_expiration_in_years(expiry, now)

iv_percent = calculate_implied_volatility(
    2.50,  # market option price
    100.0,
    105.0,
    0.05,
    0.01,
    tte,
    "call",
)

greeks = calculate_greeks(
    BlackScholesParams(
        spot=100,
        strike=105,
        time_to_expiry=tte,
        risk_free_rate=0.05,
        dividend_yield=0.01,
        volatility=iv_percent / 100.0,
        option_type="call",
    )
)

print(iv_percent)
print(greeks.price, greeks.delta, greeks.vega)
```

## Run Combined Hedge Flow Analysis

```python
from floe import CharmIntegralConfig, HedgeImpulseConfig, analyze_hedge_flow

analysis = analyze_hedge_flow(
    canonical_exposure,
    call_surface,
    HedgeImpulseConfig(),
    CharmIntegralConfig(),
    now_ms,
)

print(analysis.impulse_curve.regime)
print(analysis.charm_integral.direction)
print(analysis.regime_params.regime)
```
