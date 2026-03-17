---
title: Black-Scholes Pricing
description: Price calls and puts in Python with Black-Scholes-Merton.
order: 1
---

## Basic Pricing

```python
from floe import BlackScholesParams, black_scholes

common = BlackScholesParams(
    spot=100,
    strike=105,
    time_to_expiry=0.25,
    risk_free_rate=0.05,
    volatility=0.20,
    option_type="call",
)

call = black_scholes(common)
put = black_scholes(
    BlackScholesParams(
        spot=common.spot,
        strike=common.strike,
        time_to_expiry=common.time_to_expiry,
        risk_free_rate=common.risk_free_rate,
        volatility=common.volatility,
        option_type="put",
    )
)

print(call, put)
```

## With Dividend Yield

```python
price = black_scholes(
    BlackScholesParams(
        spot=100,
        strike=100,
        time_to_expiry=0.50,
        risk_free_rate=0.05,
        volatility=0.25,
        dividend_yield=0.02,
        option_type="call",
    )
)
```
