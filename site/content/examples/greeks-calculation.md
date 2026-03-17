---
title: Greeks Calculation
description: Calculate full Greeks output for risk and sensitivity analysis.
order: 2
---

## Full Greeks Profile

```python
from floe import BlackScholesParams, calculate_greeks

g = calculate_greeks(
    BlackScholesParams(
        spot=100,
        strike=100,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.01,
        option_type="call",
    )
)

print(g.price)
print(g.delta, g.gamma, g.theta)
print(g.vega, g.rho)
print(g.vanna, g.charm, g.volga)
print(g.speed, g.zomma, g.color, g.ultima)
```
