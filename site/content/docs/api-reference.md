---
title: API Reference
description: Core Python APIs and dataclasses in floe.
order: 2
---

## Pricing (`blackscholes`)

### `black_scholes`

```python
from floe import BlackScholesParams, black_scholes

price = black_scholes(
    BlackScholesParams(
        spot=100,
        strike=105,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type="call",
    )
)
```

### `calculate_greeks`

```python
from floe import calculate_greeks

g = calculate_greeks(params)
print(g.price, g.delta, g.gamma, g.theta, g.vega, g.rho)
print(g.vanna, g.charm, g.volga, g.speed, g.zomma, g.color, g.ultima)
```

### `calculate_implied_volatility`

```python
from floe import calculate_implied_volatility

iv_percent = calculate_implied_volatility(
    3.50,   # option price
    100.0,  # spot
    105.0,  # strike
    0.05,   # risk-free rate
    0.01,   # dividend yield
    0.25,   # time to expiry (years)
    "call",
)
```

### `get_time_to_expiration_in_years`

```python
from floe import get_time_to_expiration_in_years

tte = get_time_to_expiration_in_years(expiration_ms, now_ms)
```

## Statistics (`statistics`)

```python
from floe import cumulative_normal_distribution, normal_pdf

cdf = cumulative_normal_distribution(1.96)
pdf = normal_pdf(0)
```

## Volatility Surfaces (`volatility`)

### `get_iv_surfaces`

```python
from floe import get_iv_surfaces

surfaces = get_iv_surfaces("totalvariance", chain, now_ms)
```

### `get_iv_for_strike`

```python
from floe import get_iv_for_strike

iv_at_k = get_iv_for_strike(surfaces, expiry_ms, "call", 450)
```

### `smooth_total_variance_smile`

```python
from floe import smooth_total_variance_smile

smoothed = smooth_total_variance_smile(
    [440, 445, 450, 455, 460],
    [23, 21, 19, 20, 22],
    0.08,
)
```

## Dealer Exposure (`exposure`)

### `calculate_gamma_vanna_charm_exposures`

```python
from floe import ExposureCalculationOptions, calculate_gamma_vanna_charm_exposures

variants = calculate_gamma_vanna_charm_exposures(
    chain,
    surfaces,
    ExposureCalculationOptions(as_of_timestamp=now_ms),
)

for v in variants:
    print(v.expiration, v.canonical.total_net_exposure)
```

### `calculate_shares_needed_to_cover`

```python
from floe import calculate_shares_needed_to_cover

cover = calculate_shares_needed_to_cover(900_000_000, total_net_exposure, spot)
print(cover.action_to_cover, cover.shares_to_cover, cover.implied_move_to_cover)
```

## Hedge Flow (`hedgeflow`)

### `compute_hedge_impulse_curve`

```python
from floe import HedgeImpulseConfig, compute_hedge_impulse_curve

curve = compute_hedge_impulse_curve(
    canonical_exposure,
    call_surface,
    HedgeImpulseConfig(range_percent=3, step_percent=0.05, kernel_width_strikes=2),
    now_ms,
)
```

### `compute_charm_integral`

```python
from floe import CharmIntegralConfig, compute_charm_integral

charm = compute_charm_integral(
    canonical_exposure,
    CharmIntegralConfig(time_step_minutes=15),
    now_ms,
)
```

### `analyze_hedge_flow`

```python
from floe import analyze_hedge_flow, HedgeImpulseConfig, CharmIntegralConfig

analysis = analyze_hedge_flow(
    canonical_exposure,
    call_surface,
    HedgeImpulseConfig(),
    CharmIntegralConfig(),
    now_ms,
)
```

## Implied Probability (`impliedpdf`)

### `estimate_implied_probability_distribution`

```python
from floe import estimate_implied_probability_distribution

result = estimate_implied_probability_distribution(
    "QQQ",
    502.5,
    call_options,
    now_ms,
)
```

### `estimate_implied_probability_distributions`

```python
from floe import estimate_implied_probability_distributions

dists = estimate_implied_probability_distributions(
    "QQQ",
    502.5,
    all_options,
    now_ms,
)
```

### Query helpers

```python
from floe import get_probability_in_range, get_cumulative_probability, get_quantile

prob = get_probability_in_range(dist, 495, 510)
cum = get_cumulative_probability(dist, 500)
q90 = get_quantile(dist, 0.90)
```

### Exposure-adjusted PDF

```python
from floe import DEFAULT_ADJUSTMENT_CONFIG, estimate_exposure_adjusted_pdf

adjusted = estimate_exposure_adjusted_pdf(
    "QQQ",
    502.5,
    call_options,
    exposure_snapshot,
    DEFAULT_ADJUSTMENT_CONFIG,
    now_ms,
)
```

## IV vs RV (`iv`, `rv`, `volresponse`)

### Model-free IV

```python
from floe import compute_model_free_iv

near = compute_model_free_iv(near_term_options, spot, 0.05, now_ms)
interp = compute_model_free_iv(near_term_options, spot, 0.05, now_ms, far_term_options, 30)
```

### Realized volatility

```python
from floe import compute_realized_volatility

rv_result = compute_realized_volatility(observations)
```

### Vol response z-score

```python
from floe import build_vol_response_observation, compute_vol_response_z_score

obs = build_vol_response_observation(current_iv, current_rv, current_spot, now_ms, prev_iv, prev_spot)
result = compute_vol_response_z_score(series)
```

## OCC / Adapters / API Client

```python
from floe import build_occ_symbol, parse_occ_symbol, create_option_chain, ApiClient
```
