"""Core data structures for floe options analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

OptionType = Literal["call", "put"]
SmoothingModel = Literal["totalvariance", "none"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MILLISECONDS_PER_YEAR: float = 31_536_000_000.0
MILLISECONDS_PER_DAY: float = 86_400_000.0
MINUTES_PER_YEAR: float = 525_600.0
MINUTES_PER_DAY: float = 1_440.0
DAYS_PER_YEAR: float = 365.0

# ---------------------------------------------------------------------------
# Pricing & Greeks
# ---------------------------------------------------------------------------


@dataclass
class BlackScholesParams:
    """Inputs for Black-Scholes pricing."""

    spot: float
    strike: float
    time_to_expiry: float
    volatility: float
    risk_free_rate: float
    option_type: OptionType
    dividend_yield: float = 0.0


@dataclass
class Greeks:
    """Complete set of option Greeks."""

    price: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    charm: float = 0.0
    vanna: float = 0.0
    volga: float = 0.0
    speed: float = 0.0
    zomma: float = 0.0
    color: float = 0.0
    ultima: float = 0.0


# ---------------------------------------------------------------------------
# Normalized market data
# ---------------------------------------------------------------------------


@dataclass
class NormalizedTicker:
    """Broker-agnostic ticker quote."""

    symbol: str = ""
    spot: float = 0.0
    bid: float = 0.0
    bid_size: float = 0.0
    ask: float = 0.0
    ask_size: float = 0.0
    last: float = 0.0
    volume: float = 0.0
    timestamp: int = 0


@dataclass
class NormalizedOption:
    """Broker-agnostic option quote."""

    occ_symbol: str = ""
    underlying: str = ""
    strike: float = 0.0
    expiration: str = ""
    expiration_timestamp: int = 0
    option_type: OptionType = "call"
    bid: float = 0.0
    bid_size: float = 0.0
    ask: float = 0.0
    ask_size: float = 0.0
    mark: float = 0.0
    last: float = 0.0
    volume: float = 0.0
    open_interest: float = 0.0
    live_open_interest: float | None = None
    implied_volatility: float = 0.0
    timestamp: int = 0
    greeks: Greeks | None = None


@dataclass
class OptionChain:
    """Complete options chain with market context."""

    symbol: str = ""
    spot: float = 0.0
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    options: list[NormalizedOption] = field(default_factory=list)


# ---------------------------------------------------------------------------
# IV Surfaces
# ---------------------------------------------------------------------------


@dataclass
class IVSurface:
    """IV surface for one expiration and option type."""

    expiration_date: int = 0
    put_call: OptionType = "call"
    strikes: list[float] = field(default_factory=list)
    raw_ivs: list[float] = field(default_factory=list)
    smoothed_ivs: list[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Exposure structures
# ---------------------------------------------------------------------------


@dataclass
class StrikeExposure:
    """Exposure metrics at a single strike."""

    strike_price: float = 0.0
    gamma_exposure: float = 0.0
    vanna_exposure: float = 0.0
    charm_exposure: float = 0.0
    net_exposure: float = 0.0


@dataclass
class ExposureVector:
    """Single mode's exposure values."""

    gamma_exposure: float = 0.0
    vanna_exposure: float = 0.0
    charm_exposure: float = 0.0
    net_exposure: float = 0.0


@dataclass
class StrikeExposureVariants:
    """Per-strike exposure in all three variants."""

    strike_price: float = 0.0
    canonical: ExposureVector = field(default_factory=ExposureVector)
    state_weighted: ExposureVector = field(default_factory=ExposureVector)
    flow_delta: ExposureVector = field(default_factory=ExposureVector)


@dataclass
class ExposureModeBreakdown:
    """Full breakdown for one exposure mode."""

    total_gamma_exposure: float = 0.0
    total_vanna_exposure: float = 0.0
    total_charm_exposure: float = 0.0
    total_net_exposure: float = 0.0
    strike_of_max_gamma: float = 0.0
    strike_of_min_gamma: float = 0.0
    strike_of_max_vanna: float = 0.0
    strike_of_min_vanna: float = 0.0
    strike_of_max_charm: float = 0.0
    strike_of_min_charm: float = 0.0
    strike_of_max_net: float = 0.0
    strike_of_min_net: float = 0.0
    strike_exposures: list[StrikeExposure] = field(default_factory=list)


@dataclass
class ExposureVariantsPerExpiry:
    """All three exposure variants for one expiration."""

    spot_price: float = 0.0
    expiration: int = 0
    canonical: ExposureModeBreakdown = field(default_factory=ExposureModeBreakdown)
    state_weighted: ExposureModeBreakdown = field(default_factory=ExposureModeBreakdown)
    flow_delta: ExposureModeBreakdown = field(default_factory=ExposureModeBreakdown)
    strike_exposure_variants: list[StrikeExposureVariants] = field(default_factory=list)


@dataclass
class ExposurePerExpiry:
    """Flattened exposure view used by hedge flow calculations."""

    spot_price: float = 0.0
    expiration: int = 0
    total_gamma_exposure: float = 0.0
    total_vanna_exposure: float = 0.0
    total_charm_exposure: float = 0.0
    total_net_exposure: float = 0.0
    strike_of_max_gamma: float = 0.0
    strike_of_min_gamma: float = 0.0
    strike_of_max_vanna: float = 0.0
    strike_of_min_vanna: float = 0.0
    strike_of_max_charm: float = 0.0
    strike_of_min_charm: float = 0.0
    strike_of_max_net: float = 0.0
    strike_of_min_net: float = 0.0
    strike_exposures: list[StrikeExposure] = field(default_factory=list)


@dataclass
class ExposureCalculationOptions:
    """Configuration for exposure calculations."""

    as_of_timestamp: int = 0


# ---------------------------------------------------------------------------
# TS-only metric structures
# ---------------------------------------------------------------------------


@dataclass
class GEXMetrics:
    """Dealer Gamma Exposure (GEX) metrics."""

    by_strike: dict[float, float] = field(default_factory=dict)
    net_gamma: float = 0.0
    max_positive_strike: float = 0.0
    max_negative_strike: float = 0.0
    zero_gamma_level: float | None = None


@dataclass
class VannaMetrics:
    """Dealer Vanna Exposure (VEX) metrics."""

    by_strike: dict[float, float] = field(default_factory=dict)
    net_vanna: float = 0.0


@dataclass
class CharmMetrics:
    """Dealer Charm Exposure (CEX) metrics."""

    by_strike: dict[float, float] = field(default_factory=dict)
    net_charm: float = 0.0


# ---------------------------------------------------------------------------
# Adapter type
# ---------------------------------------------------------------------------

RawOptionData = dict[str, Any]
BrokerAdapter = Callable[[RawOptionData], NormalizedOption]
