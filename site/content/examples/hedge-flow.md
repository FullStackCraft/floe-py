---
title: Hedge Flow Analysis
description: Combine impulse-curve and charm-integral analytics for one expiration.
order: 5
---

## Compute the Hedge Impulse Curve

```python
from floe import HedgeImpulseConfig, compute_hedge_impulse_curve

curve = compute_hedge_impulse_curve(
    canonical_exposure,
    call_surface,
    HedgeImpulseConfig(
        range_percent=3,
        step_percent=0.05,
        kernel_width_strikes=2,
    ),
    now_ms,
)

print(curve.regime)
print(curve.impulse_at_spot)
for zc in curve.zero_crossings:
    print(zc.price, zc.direction)
```

## Compute the Charm Integral

```python
from floe import CharmIntegralConfig, compute_charm_integral

charm = compute_charm_integral(
    canonical_exposure,
    CharmIntegralConfig(time_step_minutes=15),
    now_ms,
)

print(charm.minutes_remaining)
print(charm.total_charm_to_close)
print(charm.direction)
```

## Full Combined Analysis

```python
from floe import CharmIntegralConfig, HedgeImpulseConfig, analyze_hedge_flow

analysis = analyze_hedge_flow(
    canonical_exposure,
    call_surface,
    HedgeImpulseConfig(),
    CharmIntegralConfig(),
    now_ms,
)

print(analysis.regime_params.regime)
print(analysis.impulse_curve.regime)
print(analysis.charm_integral.direction)
```
