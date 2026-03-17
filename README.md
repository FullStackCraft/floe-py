# `floe-py`

![PyPI](https://img.shields.io/pypi/v/floe-py?style=flat-square) ![License](https://img.shields.io/pypi/l/floe-py?style=flat-square) ![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)

Zero-dependency Python library for options flow analytics: Black-Scholes, Greeks, IV surfaces, dealer exposures, implied PDFs, hedge flow, and more, with a clean, fully-typed API. Broker agnostic. Built for use in trading platforms, analytics pipelines, and fintech applications.

The same library that is used in [Full Stack Craft's](https://fullstackcraft.com) various fintech products including [The Wheel Screener](https://wheelscreener.com), [LEAPS Screener](https://leapsscreener.com), [Option Screener](https://option-screener.com), [AMT JOY](https://amtjoy.com), and [VannaCharm](https://vannacharm.com).

## Quick Start / Documentation / Examples

[fullstackcraft.github.io/floe-py](https://fullstackcraft.github.io/floe-py)

## Dual License

**This project is dual-licensed:**

- **MIT License** - Free for individuals, personal projects, and non-commercial use
- **Commercial License** - Required for businesses and commercial applications

[Read full licensing details](LICENSE.md) | [Get Commercial License](mailto:hi@fullstackcraft.com)

---

## Features

- **Black-Scholes Pricing** - Fast, accurate options pricing
- **Greeks Calculations** - Delta, gamma, theta, vega, rho, charm, vanna, volga, speed, zomma, color, ultima
- **Dealer Exposure Metrics** - GEX, VEX, and CEX exposures in three modes
- **Implied Volatility & Surfaces** - Calculate IV from market prices and build volatility surfaces
- **Implied PDF** - Risk-neutral probability density functions with exposure adjustment
- **Hedge Flow Analysis** - Impulse curves, charm integrals, pressure clouds, regime classification
- **Model-Free IV** - CBOE variance swap methodology
- **Realized Volatility** - Quadratic variation from tick data
- **Vol Response Model** - IV regression with z-score signal classification
- **Broker-Agnostic** - Normalize data from any broker
- **Fully Typed** - Complete type annotations with dataclasses
- **Zero Dependencies** - Pure Python, no external packages required

## Installation

```bash
pip install floe-py
```

## Quick Start

```python
from floe import calculate_greeks, BlackScholesParams

greeks = calculate_greeks(BlackScholesParams(
    spot=100.0,
    strike=105.0,
    time_to_expiry=0.25,
    volatility=0.20,
    risk_free_rate=0.05,
    option_type="call",
))

print(f"Price: {greeks.price}")
print(f"Delta: {greeks.delta}")
print(f"Gamma: {greeks.gamma}")
print(f"Theta: {greeks.theta}")
print(f"Vega:  {greeks.vega}")
```

## License

**Free for Individuals** - Use the MIT License for personal, educational, and non-commercial projects.

**Commercial License Required** - Businesses and commercial applications must obtain a commercial license.

See [LICENSE.md](LICENSE.md) for full details.

**Need a Commercial License?** Contact us at [hi@fullstackcraft.com](mailto:hi@fullstackcraft.com)

## Also Available In

- **TypeScript**: [@fullstackcraftllc/floe](https://www.npmjs.com/package/@fullstackcraftllc/floe) ([Docs](https://fullstackcraft.github.io/floe))
- **Go**: [github.com/FullStackCraft/floe-go](https://pkg.go.dev/github.com/FullStackCraft/floe-go) ([Docs](https://fullstackcraft.github.io/floe-go))

## Contributing

Contributions are welcome! Please open an issue or PR.

By contributing, you agree that your contributions will be licensed under the same dual-license terms.

## Credits

Copyright 2025 Built by [Full Stack Craft LLC](https://fullstackcraft.com)
