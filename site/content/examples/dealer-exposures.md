---
title: Dealer Exposures
description: Compute canonical, state-weighted, and flow-delta exposure vectors.
order: 3
---

## Build Chain, Surfaces, and Exposure Variants

```python
import time

from floe import (
    ExposureCalculationOptions,
    NormalizedOption,
    OptionChain,
    calculate_gamma_vanna_charm_exposures,
    get_iv_surfaces,
)

now = int(time.time() * 1000)
expiry = now + 14 * 24 * 60 * 60 * 1000

options = [
    NormalizedOption(strike=440, expiration_timestamp=expiry, option_type="call", bid=13.0, ask=13.4, mark=13.2, open_interest=21000, implied_volatility=0.19),
    NormalizedOption(strike=440, expiration_timestamp=expiry, option_type="put", bid=2.7, ask=3.1, mark=2.9, open_interest=19000, implied_volatility=0.20),
    NormalizedOption(strike=445, expiration_timestamp=expiry, option_type="call", bid=9.0, ask=9.2, mark=9.1, open_interest=26000, implied_volatility=0.18),
    NormalizedOption(strike=445, expiration_timestamp=expiry, option_type="put", bid=5.0, ask=5.2, mark=5.1, open_interest=24000, implied_volatility=0.19),
    NormalizedOption(strike=450, expiration_timestamp=expiry, option_type="call", bid=5.8, ask=6.0, mark=5.9, open_interest=33000, implied_volatility=0.17),
    NormalizedOption(strike=450, expiration_timestamp=expiry, option_type="put", bid=8.2, ask=8.4, mark=8.3, open_interest=30000, implied_volatility=0.18),
]

chain = OptionChain(symbol="SPY", spot=447.5, risk_free_rate=0.05, dividend_yield=0.01, options=options)
surfaces = get_iv_surfaces("totalvariance", chain, now)
variants = calculate_gamma_vanna_charm_exposures(chain, surfaces, ExposureCalculationOptions(as_of_timestamp=now))

for exp in variants:
    print(exp.expiration)
    print(exp.canonical.total_net_exposure)
    print(exp.state_weighted.total_net_exposure)
    print(exp.flow_delta.total_net_exposure)
```

## Estimate Shares Needed to Rebalance

```python
from floe import calculate_shares_needed_to_cover

cover = calculate_shares_needed_to_cover(900_000_000, -4_000_000, 447.5)
print(cover.action_to_cover)
print(cover.shares_to_cover)
print(cover.implied_move_to_cover)
```
