---
title: IV vs RV Analysis
description: Compare model-free implied volatility with realized volatility and vol-response z-scores.
order: 6
---

## 1. Compute Model-Free IV

```python
from floe import compute_variance_swap_iv

near = compute_variance_swap_iv(near_term_options, spot, 0.05, now_ms)
print(near.implied_volatility)
```

## 2. Interpolate to Constant Maturity (Optional)

```python
from floe import compute_model_free_iv

interpolated = compute_model_free_iv(
    near_term_options,
    spot,
    0.05,
    now_ms,
    far_term_options,
    1,
)

print(interpolated.implied_volatility)
```

## 3. Compute Realized Volatility from Ticks

```python
from floe import PriceObservation, compute_realized_volatility

obs = [
    PriceObservation(price=600.10, timestamp=float(now_ms - 300000)),
    PriceObservation(price=600.25, timestamp=float(now_ms - 240000)),
    PriceObservation(price=599.80, timestamp=float(now_ms - 180000)),
    PriceObservation(price=600.50, timestamp=float(now_ms - 120000)),
    PriceObservation(price=601.10, timestamp=float(now_ms - 60000)),
    PriceObservation(price=600.90, timestamp=float(now_ms)),
]

realized = compute_realized_volatility(obs)
print(realized.realized_volatility)
```

## 4. Track the IV-RV Spread

```python
spread = near.implied_volatility - realized.realized_volatility
print(spread)
```

## 5. Vol Response Z-Score

```python
from floe import (
    VolResponseConfig,
    build_vol_response_observation,
    compute_vol_response_z_score,
)

series = [
    build_vol_response_observation(0.21, 0.18, 600.4, now_ms - 2000, 0.20, 600.0),
    build_vol_response_observation(0.22, 0.19, 600.9, now_ms - 1000, 0.21, 600.4),
    build_vol_response_observation(0.23, 0.20, 601.2, now_ms, 0.22, 600.9),
]

result = compute_vol_response_z_score(series, VolResponseConfig(min_observations=3))
print(result.signal, result.z_score)
```
