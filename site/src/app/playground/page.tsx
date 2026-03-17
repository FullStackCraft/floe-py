"use client";

import Link from "next/link";
import { useState } from "react";

const EXAMPLES = {
  "black-scholes": {
    title: "Black-Scholes Pricing",
    description: "Price calls and puts with floe's Black-Scholes implementation.",
    code: `from floe import BlackScholesParams, black_scholes

common = BlackScholesParams(
    spot=100.0,
    strike=105.0,
    time_to_expiry=0.25,
    risk_free_rate=0.05,
    volatility=0.20,
    option_type="call",
)

call_price = black_scholes(common)
put_price = black_scholes(
    BlackScholesParams(
        spot=common.spot,
        strike=common.strike,
        time_to_expiry=common.time_to_expiry,
        risk_free_rate=common.risk_free_rate,
        volatility=common.volatility,
        option_type="put",
    )
)

print(f"Call: {call_price:.2f}")
print(f"Put:  {put_price:.2f}")`,
  },
  greeks: {
    title: "Greeks",
    description: "Compute first, second, and third order Greeks.",
    code: `from floe import BlackScholesParams, calculate_greeks

g = calculate_greeks(
    BlackScholesParams(
        spot=100.0,
        strike=105.0,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.01,
        option_type="call",
    )
)

print(g.price, g.delta, g.gamma, g.theta, g.vega, g.rho)
print(g.vanna, g.charm, g.volga, g.speed, g.zomma, g.color, g.ultima)`,
  },
  "iv-surfaces": {
    title: "IV Surfaces",
    description: "Build smoothed IV surfaces for calls and puts.",
    code: `import time

from floe import NormalizedOption, OptionChain, get_iv_surfaces

now = int(time.time() * 1000)
expiry = now + 30 * 24 * 60 * 60 * 1000

options = [
    NormalizedOption(strike=95, expiration_timestamp=expiry, option_type="call", bid=7.1, ask=7.3, mark=7.2, implied_volatility=0.22),
    NormalizedOption(strike=100, expiration_timestamp=expiry, option_type="call", bid=4.8, ask=5.0, mark=4.9, implied_volatility=0.20),
    NormalizedOption(strike=105, expiration_timestamp=expiry, option_type="call", bid=3.0, ask=3.2, mark=3.1, implied_volatility=0.19),
    NormalizedOption(strike=95, expiration_timestamp=expiry, option_type="put", bid=1.0, ask=1.2, mark=1.1, implied_volatility=0.24),
    NormalizedOption(strike=100, expiration_timestamp=expiry, option_type="put", bid=2.7, ask=2.9, mark=2.8, implied_volatility=0.21),
    NormalizedOption(strike=105, expiration_timestamp=expiry, option_type="put", bid=5.6, ask=5.8, mark=5.7, implied_volatility=0.20),
]

chain = OptionChain(
    symbol="SPY",
    spot=100.0,
    risk_free_rate=0.05,
    dividend_yield=0.01,
    options=options,
)

surfaces = get_iv_surfaces("totalvariance", chain, now)
print(f"Built {len(surfaces)} surfaces")`,
  },
  "dealer-exposures": {
    title: "Dealer Exposures",
    description: "Calculate canonical, state-weighted, and flow-delta exposures.",
    code: `import time

from floe import (
    ExposureCalculationOptions,
    NormalizedOption,
    OptionChain,
    calculate_gamma_vanna_charm_exposures,
    get_iv_surfaces,
)

now = int(time.time() * 1000)
expiry = now + 7 * 24 * 60 * 60 * 1000

options = [
    NormalizedOption(strike=440, expiration_timestamp=expiry, option_type="call", bid=13.1, ask=13.3, mark=13.2, open_interest=21000, implied_volatility=0.19),
    NormalizedOption(strike=440, expiration_timestamp=expiry, option_type="put", bid=2.8, ask=3.0, mark=2.9, open_interest=18000, implied_volatility=0.20),
    NormalizedOption(strike=445, expiration_timestamp=expiry, option_type="call", bid=9.0, ask=9.2, mark=9.1, open_interest=28000, implied_volatility=0.18),
    NormalizedOption(strike=445, expiration_timestamp=expiry, option_type="put", bid=4.9, ask=5.1, mark=5.0, open_interest=25000, implied_volatility=0.19),
    NormalizedOption(strike=450, expiration_timestamp=expiry, option_type="call", bid=5.7, ask=5.9, mark=5.8, open_interest=36000, implied_volatility=0.17),
    NormalizedOption(strike=450, expiration_timestamp=expiry, option_type="put", bid=8.3, ask=8.5, mark=8.4, open_interest=34000, implied_volatility=0.18),
]

chain = OptionChain(symbol="SPY", spot=447.5, risk_free_rate=0.05, dividend_yield=0.01, options=options)
surfaces = get_iv_surfaces("totalvariance", chain, now)
variants = calculate_gamma_vanna_charm_exposures(chain, surfaces, ExposureCalculationOptions(as_of_timestamp=now))

for exp in variants:
    print(exp.expiration, exp.canonical.total_net_exposure, exp.state_weighted.total_net_exposure)`,
  },
  "implied-pdf": {
    title: "Implied PDF",
    description: "Estimate risk-neutral distribution and range probabilities.",
    code: `import time

from floe import (
    NormalizedOption,
    estimate_implied_probability_distribution,
    get_probability_in_range,
    get_quantile,
)

expiry = int(time.time() * 1000) + 14 * 24 * 60 * 60 * 1000
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

range_prob = get_probability_in_range(dist, 495, 510)
p90 = get_quantile(dist, 0.90)

print(dist.most_likely_price)
print(dist.expected_move)
print(range_prob)
print(p90)`,
  },
  "iv-vs-rv": {
    title: "IV vs RV",
    description: "Compare model-free implied vol with realized vol and vol-response z-score.",
    code: `import time

from floe import (
    NormalizedOption,
    PriceObservation,
    build_vol_response_observation,
    compute_model_free_iv,
    compute_realized_volatility,
    compute_vol_response_z_score,
)

now = int(time.time() * 1000)
expiry = now + 6 * 60 * 60 * 1000

options = [
    NormalizedOption(strike=595, expiration_timestamp=expiry, option_type="call", bid=5.2, ask=5.4),
    NormalizedOption(strike=595, expiration_timestamp=expiry, option_type="put", bid=0.5, ask=0.7),
    NormalizedOption(strike=600, expiration_timestamp=expiry, option_type="call", bid=2.1, ask=2.3),
    NormalizedOption(strike=600, expiration_timestamp=expiry, option_type="put", bid=2.0, ask=2.2),
    NormalizedOption(strike=605, expiration_timestamp=expiry, option_type="call", bid=0.7, ask=0.9),
    NormalizedOption(strike=605, expiration_timestamp=expiry, option_type="put", bid=5.3, ask=5.5),
]

iv_result = compute_model_free_iv(options, 600, 0.05, now)

ticks = [
    PriceObservation(price=600.0, timestamp=float(now - 300000)),
    PriceObservation(price=600.6, timestamp=float(now - 240000)),
    PriceObservation(price=599.8, timestamp=float(now - 180000)),
    PriceObservation(price=600.9, timestamp=float(now - 120000)),
    PriceObservation(price=601.2, timestamp=float(now - 60000)),
    PriceObservation(price=600.7, timestamp=float(now)),
]
rv_result = compute_realized_volatility(ticks)

obs = [
    build_vol_response_observation(0.22, 0.19, 600.8, now - 2000, 0.20, 600.1),
    build_vol_response_observation(0.23, 0.20, 601.1, now - 1000, 0.22, 600.8),
    build_vol_response_observation(0.24, 0.21, 601.4, now, 0.23, 601.1),
]
z = compute_vol_response_z_score(obs, None)

print(iv_result.implied_volatility, rv_result.realized_volatility)
print(z.signal, z.z_score)`,
  },
} as const;

type ExampleKey = keyof typeof EXAMPLES;

export default function PlaygroundPage() {
  const [activeExample, setActiveExample] = useState<ExampleKey>("black-scholes");
  const [copied, setCopied] = useState(false);

  const example = EXAMPLES[activeExample];

  const handleCopy = async () => {
    await navigator.clipboard.writeText(example.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="font-mono text-2xl font-bold text-[#0073b7]">
              floe
            </Link>
            <span className="text-gray-300">|</span>
            <h1 className="text-lg font-medium">Playground</h1>
          </div>
          <nav className="flex gap-4">
            <Link href="/documentation" className="text-gray-600 hover:text-black transition-colors">
              Docs
            </Link>
            <Link href="/examples" className="text-gray-600 hover:text-black transition-colors">
              Examples
            </Link>
          </nav>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {(Object.keys(EXAMPLES) as ExampleKey[]).map((key) => (
              <button
                key={key}
                onClick={() => setActiveExample(key)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeExample === key
                    ? "bg-[#0073b7] text-white"
                    : "bg-white border border-gray-200 text-gray-700 hover:border-gray-400"
                }`}
              >
                {EXAMPLES[key].title}
              </button>
            ))}
          </div>
          <p className="mt-3 text-gray-600">{example.description}</p>
        </div>

        <div className="rounded-lg overflow-hidden border border-gray-200 shadow-sm bg-[#0b1720]">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#1d3645] bg-[#122331]">
            <span className="font-mono text-xs text-[#9ecde0]">main.py</span>
            <button
              onClick={handleCopy}
              className="text-xs px-2 py-1 rounded bg-[#0073b7] text-white hover:bg-[#005a8f] transition-colors cursor-pointer"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <pre className="p-5 overflow-x-auto text-sm leading-6 text-[#d7e7ef]">
            <code>{example.code}</code>
          </pre>
        </div>

        <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="font-mono text-lg font-semibold mb-3">Tips</h2>
          <ul className="text-gray-600 space-y-2 text-sm">
            <li>• These snippets are designed for server-side Python workflows</li>
            <li>
              • Install with <code className="bg-gray-100 px-1 rounded">pip install floe-py</code> and import from
              <code className="bg-gray-100 px-1 rounded ml-1">floe</code>
            </li>
            <li>
              • Check the <Link href="/documentation" className="text-[#0073b7] hover:underline">documentation</Link>
              for API details and signatures
            </li>
            <li>• Pass explicit millisecond timestamps to time-sensitive APIs where required</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
