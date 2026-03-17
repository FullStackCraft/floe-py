---
title: Getting Started
description: Install floe and start running options analytics in Python.
order: 1
---

## Installation

Install from PyPI:

```bash
pip install floe-py
```

## Quick Start

```python
from floe import BlackScholesParams, black_scholes, calculate_greeks

params = BlackScholesParams(
    spot=100.0,
    strike=105.0,
    time_to_expiry=0.25,
    risk_free_rate=0.05,
    volatility=0.20,
    dividend_yield=0.01,
    option_type="call",
)

price = black_scholes(params)
greeks = calculate_greeks(params)

print(price)
print(greeks.delta, greeks.gamma, greeks.theta)
```

## Package Layout

`floe` is organized by focused Python modules:

1. `blackscholes` for pricing, Greeks, implied volatility, and time-to-expiry helpers.
2. `volatility` for IV surfaces and smile smoothing.
3. `exposure` for canonical/state-weighted/flow-delta dealer exposures.
4. `hedgeflow` for impulse curve, charm integral, and pressure cloud analysis.
5. `impliedpdf` for risk-neutral distribution estimation and adjusted PDFs.
6. `iv` and `rv` for model-free IV vs realized volatility workflows.
7. `volresponse` for IV response z-score classification.
8. `occ`, `adapters`, and `apiclient` for symbol utilities, broker normalization, and dataset APIs.

## Notes

- Time-sensitive APIs take explicit millisecond timestamps.
- `calculate_implied_volatility` returns IV in percent (`20` means `20%`).
- Most chain-based functions consume `OptionChain` and `NormalizedOption`.

## Next Steps

- Read the [API Reference](/documentation/api-reference)
- Explore [Recipes](/documentation/recipes)
- Run end-to-end patterns in [Examples](/examples)
