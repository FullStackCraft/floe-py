---
title: Implied Probability Distribution
description: Estimate risk-neutral strike distributions from call option prices.
order: 4
---

## Estimate a Single-Expiry Distribution

```python
import time

from floe import NormalizedOption, estimate_implied_probability_distribution

expiry = int(time.time() * 1000) + 7 * 24 * 60 * 60 * 1000

calls = [
    NormalizedOption(strike=490, expiration_timestamp=expiry, option_type="call", bid=15.2, ask=15.5),
    NormalizedOption(strike=495, expiration_timestamp=expiry, option_type="call", bid=11.4, ask=11.7),
    NormalizedOption(strike=500, expiration_timestamp=expiry, option_type="call", bid=8.1, ask=8.4),
    NormalizedOption(strike=505, expiration_timestamp=expiry, option_type="call", bid=5.3, ask=5.6),
    NormalizedOption(strike=510, expiration_timestamp=expiry, option_type="call", bid=3.1, ask=3.4),
]

result = estimate_implied_probability_distribution("QQQ", 502.5, calls, int(time.time() * 1000))
if not result.success:
    raise RuntimeError(result.error)

dist = result.distribution
assert dist is not None

print(dist.most_likely_price)
print(dist.median_price)
print(dist.expected_move)
print(dist.tail_skew)
```

## Query Range and Quantiles

```python
from floe import get_cumulative_probability, get_probability_in_range, get_quantile

p_range = get_probability_in_range(dist, 495, 510)
p_below = get_cumulative_probability(dist, 495)
p90 = get_quantile(dist, 0.90)

print(p_range, p_below, p90)
```
