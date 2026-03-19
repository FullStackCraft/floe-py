"""floe — zero-dependency Python options analytics library."""

# Types & constants
from floe.types import (
    DAYS_PER_YEAR,
    MILLISECONDS_PER_DAY,
    MILLISECONDS_PER_YEAR,
    MINUTES_PER_DAY,
    MINUTES_PER_YEAR,
    BlackScholesParams,
    BrokerAdapter,
    CharmMetrics,
    ExposureCalculationOptions,
    ExposureModeBreakdown,
    ExposurePerExpiry,
    ExposureVariantsPerExpiry,
    ExposureVector,
    GEXMetrics,
    Greeks,
    IVSurface,
    NormalizedOption,
    NormalizedTicker,
    OptionChain,
    OptionType,
    RawOptionData,
    SmoothingModel,
    StrikeExposure,
    StrikeExposureVariants,
    VannaMetrics,
)

# Statistics
from floe.statistics import cumulative_normal_distribution, normal_pdf

# Black-Scholes
from floe.blackscholes import (
    black_scholes,
    calculate_greeks,
    calculate_implied_volatility,
    get_time_to_expiration_in_years,
)

# Volatility surfaces
from floe.volatility import (
    get_iv_for_strike,
    get_iv_surfaces,
    smooth_total_variance_smile,
)

# Exposure (GEX / VEX / CEX)
from floe.exposure import (
    SharesCoverResult,
    calculate_gamma_vanna_charm_exposures,
    calculate_shares_needed_to_cover,
)

# Hedge flow
from floe.hedgeflow import (
    CharmBucket,
    CharmIntegral,
    CharmIntegralConfig,
    DirectionalAsymmetry,
    HedgeContractEstimates,
    HedgeFlowAnalysis,
    HedgeImpulseConfig,
    HedgeImpulseCurve,
    HedgeImpulsePoint,
    ImpulseExtremum,
    PressureCloud,
    PressureCloudConfig,
    PressureLevel,
    PressureZone,
    RegimeEdge,
    RegimeParams,
    StrikeContribution,
    ZeroCrossing,
    analyze_hedge_flow,
    compute_charm_integral,
    compute_hedge_impulse_curve,
    compute_pressure_cloud,
    derive_regime_params,
    interpolate_iv_at_strike,
)

# Implied PDF
from floe.impliedpdf import (
    AdjustedPDFResult,
    AdjustmentLevel,
    CRISIS_CONFIG,
    DEFAULT_ADJUSTMENT_CONFIG,
    ExposureAdjustmentConfig,
    GammaConfig,
    ImpliedPDFResult,
    ImpliedProbabilityDistribution,
    LOW_VOL_CONFIG,
    OPEX_CONFIG,
    PDFComparison,
    TailComparison,
    VannaConfig,
    CharmAdjConfig,
    StrikeProbability,
    estimate_exposure_adjusted_pdf,
    estimate_implied_probability_distribution,
    estimate_implied_probability_distributions,
    get_edge_at_price,
    get_cumulative_probability,
    get_probability_in_range,
    get_quantile,
    get_significant_adjustment_levels,
)

# Model-free IV (variance swap / VIX methodology)
from floe.iv import (
    ImpliedVolatilityResult,
    VarianceSwapResult,
    compute_implied_volatility as compute_model_free_iv,
    compute_variance_swap_iv,
)

# Realized volatility
from floe.rv import (
    PriceObservation,
    RealizedVolatilityResult,
    compute_realized_volatility,
)

# Vol response
from floe.volresponse import (
    VolResponseConfig,
    VolResponseCoefficients,
    VolResponseObservation,
    VolResponseResult,
    build_vol_response_observation,
    compute_vol_response_z_score,
)

# OCC symbols
from floe.occ import (
    OCCSymbol,
    OCCSymbolParams,
    ParsedOCCSymbol,
    StrikeGenerationParams,
    build_occ_symbol,
    generate_occ_symbols_around_spot,
    generate_occ_symbols_for_strikes,
    generate_strikes_around_spot,
    parse_occ_symbol,
)

# Adapters
from floe.adapters import (
    BROKER_ADAPTERS,
    create_option_chain,
    generic_adapter,
    get_adapter,
    ibkr_adapter,
    schwab_adapter,
    tda_adapter,
)

# API client
from floe.apiclient import (
    APIError,
    AMTEventsRow,
    AMTRequest,
    AMTSessionStatsRow,
    ApiClient,
    DealerMinuteSurface,
    DealerMinuteSurfacesRequest,
    HindsightDataRequest,
    HindsightEvent,
    MinuteSurface,
    OptionsScreenerRequest,
    OptionsScreenerResponse,
    SurfacePoint,
)

__all__ = [
    # Types & constants
    "DAYS_PER_YEAR",
    "MILLISECONDS_PER_DAY",
    "MILLISECONDS_PER_YEAR",
    "MINUTES_PER_DAY",
    "MINUTES_PER_YEAR",
    "BlackScholesParams",
    "BrokerAdapter",
    "CharmMetrics",
    "ExposureCalculationOptions",
    "ExposureModeBreakdown",
    "ExposurePerExpiry",
    "ExposureVariantsPerExpiry",
    "ExposureVector",
    "GEXMetrics",
    "Greeks",
    "IVSurface",
    "NormalizedOption",
    "NormalizedTicker",
    "OptionChain",
    "OptionType",
    "RawOptionData",
    "SmoothingModel",
    "StrikeExposure",
    "StrikeExposureVariants",
    "VannaMetrics",
    # Statistics
    "cumulative_normal_distribution",
    "normal_pdf",
    # Black-Scholes
    "black_scholes",
    "calculate_greeks",
    "calculate_implied_volatility",
    "get_time_to_expiration_in_years",
    # Volatility
    "get_iv_for_strike",
    "get_iv_surfaces",
    "smooth_total_variance_smile",
    # Exposure
    "SharesCoverResult",
    "calculate_gamma_vanna_charm_exposures",
    "calculate_shares_needed_to_cover",
    # Hedge flow
    "CharmBucket",
    "CharmIntegral",
    "CharmIntegralConfig",
    "DirectionalAsymmetry",
    "HedgeContractEstimates",
    "HedgeFlowAnalysis",
    "HedgeImpulseConfig",
    "HedgeImpulseCurve",
    "HedgeImpulsePoint",
    "ImpulseExtremum",
    "PressureCloud",
    "PressureCloudConfig",
    "PressureLevel",
    "PressureZone",
    "RegimeEdge",
    "RegimeParams",
    "StrikeContribution",
    "ZeroCrossing",
    "analyze_hedge_flow",
    "compute_charm_integral",
    "compute_hedge_impulse_curve",
    "compute_pressure_cloud",
    "derive_regime_params",
    "interpolate_iv_at_strike",
    # Implied PDF
    "AdjustedPDFResult",
    "AdjustmentLevel",
    "CRISIS_CONFIG",
    "DEFAULT_ADJUSTMENT_CONFIG",
    "ExposureAdjustmentConfig",
    "GammaConfig",
    "ImpliedPDFResult",
    "ImpliedProbabilityDistribution",
    "LOW_VOL_CONFIG",
    "OPEX_CONFIG",
    "PDFComparison",
    "TailComparison",
    "VannaConfig",
    "CharmAdjConfig",
    "StrikeProbability",
    "estimate_exposure_adjusted_pdf",
    "estimate_implied_probability_distribution",
    "estimate_implied_probability_distributions",
    "get_edge_at_price",
    "get_cumulative_probability",
    "get_probability_in_range",
    "get_quantile",
    "get_significant_adjustment_levels",
    # Model-free IV
    "ImpliedVolatilityResult",
    "VarianceSwapResult",
    "compute_model_free_iv",
    "compute_variance_swap_iv",
    # Realized volatility
    "PriceObservation",
    "RealizedVolatilityResult",
    "compute_realized_volatility",
    # Vol response
    "VolResponseConfig",
    "VolResponseCoefficients",
    "VolResponseObservation",
    "VolResponseResult",
    "build_vol_response_observation",
    "compute_vol_response_z_score",
    # OCC
    "OCCSymbol",
    "OCCSymbolParams",
    "ParsedOCCSymbol",
    "StrikeGenerationParams",
    "build_occ_symbol",
    "generate_occ_symbols_around_spot",
    "generate_occ_symbols_for_strikes",
    "generate_strikes_around_spot",
    "parse_occ_symbol",
    # Adapters
    "BROKER_ADAPTERS",
    "create_option_chain",
    "generic_adapter",
    "get_adapter",
    "ibkr_adapter",
    "schwab_adapter",
    "tda_adapter",
    # API client
    "APIError",
    "AMTEventsRow",
    "AMTRequest",
    "AMTSessionStatsRow",
    "ApiClient",
    "DealerMinuteSurface",
    "DealerMinuteSurfacesRequest",
    "HindsightDataRequest",
    "HindsightEvent",
    "MinuteSurface",
    "OptionsScreenerRequest",
    "OptionsScreenerResponse",
    "SurfacePoint",
]
