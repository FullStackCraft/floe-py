"""Broker data adapters for normalizing option chain data."""

from __future__ import annotations

import datetime as dt
import math
import time

from floe.occ import OCCSymbolParams, build_occ_symbol
from floe.types import (
    BrokerAdapter,
    NormalizedOption,
    OptionChain,
    OptionType,
    RawOptionData,
)


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if not math.isfinite(result):
        return default
    return result


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _as_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    try:
        s = str(value)
    except Exception:
        return default
    return s


def _as_option_type(value: object, default: OptionType = "call") -> OptionType:
    s = _as_str(value).strip().lower()
    if s in {"call", "c"}:
        return "call"
    if s in {"put", "p"}:
        return "put"
    return default


def _optional_float(value: object) -> float | None:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _expiration_to_ms(expiration: str) -> int:
    exp = expiration.strip()
    if not exp:
        return 0

    # Common compact IBKR expiry format (YYYYMMDD).
    if len(exp) == 8 and exp.isdigit():
        try:
            d = dt.date(int(exp[0:4]), int(exp[4:6]), int(exp[6:8]))
            return int(dt.datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=dt.timezone.utc).timestamp() * 1000)
        except ValueError:
            return 0

    # ISO date / datetime.
    normalized = exp.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        try:
            d = dt.date.fromisoformat(exp)
        except ValueError:
            return 0
        parsed = dt.datetime(d.year, d.month, d.day, 12, 0, 0)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return int(parsed.timestamp() * 1000)


def _to_iso_expiration(expiration: object) -> str:
    raw = _as_str(expiration).strip()
    if not raw:
        return ""

    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"

    if "T" in raw:
        return raw.split("T", 1)[0]

    return raw


def _iso_to_occ_yy_mm_dd(expiration_iso: str) -> str:
    exp = expiration_iso.strip()
    if not exp:
        return ""
    try:
        d = dt.date.fromisoformat(exp)
    except ValueError:
        return ""
    return d.strftime("%y%m%d")


def _build_occ_from_raw(underlying: str, expiration: str, option_type: OptionType, strike: float) -> str:
    occ_exp = _iso_to_occ_yy_mm_dd(expiration)
    if not underlying or not occ_exp or strike <= 0:
        return ""
    try:
        return build_occ_symbol(
            OCCSymbolParams(
                symbol=underlying,
                expiration=occ_exp,
                option_type=option_type,
                strike=strike,
                padded=False,
            )
        )
    except Exception:
        return ""


def generic_adapter(data: RawOptionData) -> NormalizedOption:
    """Generic adapter mapping common field names."""
    underlying = _as_str(
        data.get("underlying")
        or data.get("symbol")
        or data.get("underlyingSymbol")
        or ""
    )
    expiration = _to_iso_expiration(data.get("expiration") or data.get("expirationDate") or "")
    option_type = _as_option_type(data.get("optionType") or data.get("putCall") or "")
    strike = _as_float(data.get("strike") or data.get("strikePrice") or 0)

    bid = _as_float(data.get("bid"))
    ask = _as_float(data.get("ask"))
    mark = _as_float(data.get("mark"), default=(bid + ask) / 2 if (bid > 0 and ask > 0) else 0.0)

    return NormalizedOption(
        occ_symbol=_as_str(data.get("occSymbol") or data.get("symbol") or "") or _build_occ_from_raw(underlying, expiration, option_type, strike),
        underlying=underlying,
        strike=strike,
        expiration=expiration,
        expiration_timestamp=_as_int(data.get("expirationTimestamp"), default=_expiration_to_ms(expiration)),
        option_type=option_type,
        bid=bid,
        bid_size=_as_float(data.get("bidSize") or data.get("bidQty") or 0),
        ask=ask,
        ask_size=_as_float(data.get("askSize") or data.get("askQty") or 0),
        mark=mark,
        last=_as_float(data.get("last") or data.get("lastPrice") or 0),
        volume=_as_float(data.get("volume") or 0),
        open_interest=_as_float(data.get("openInterest") or 0),
        live_open_interest=_optional_float(data.get("liveOpenInterest")),
        implied_volatility=_as_float(data.get("impliedVolatility") or data.get("iv") or 0),
        timestamp=_as_int(data.get("timestamp"), default=int(time.time() * 1000)),
    )


def schwab_adapter(data: RawOptionData) -> NormalizedOption:
    """Schwab adapter."""
    underlying = _as_str(data.get("underlying") or data.get("underlyingSymbol") or "")
    expiration = _to_iso_expiration(data.get("expirationDate") or "")
    option_type = _as_option_type(data.get("putCall"), default="put")
    strike = _as_float(data.get("strikePrice") or 0)

    return NormalizedOption(
        occ_symbol=_as_str(data.get("symbol") or "") or _build_occ_from_raw(underlying, expiration, option_type, strike),
        underlying=underlying,
        strike=strike,
        expiration=expiration,
        expiration_timestamp=_expiration_to_ms(expiration),
        option_type=option_type,
        bid=_as_float(data.get("bid") or 0),
        bid_size=_as_float(data.get("bidSize") or 0),
        ask=_as_float(data.get("ask") or 0),
        ask_size=_as_float(data.get("askSize") or 0),
        mark=_as_float(data.get("mark") or 0),
        last=_as_float(data.get("last") or 0),
        volume=_as_float(data.get("totalVolume") or 0),
        open_interest=_as_float(data.get("openInterest") or 0),
        implied_volatility=_as_float(data.get("volatility") or 0),
        timestamp=_as_int(data.get("quoteTime"), default=int(time.time() * 1000)),
    )


def ibkr_adapter(data: RawOptionData) -> NormalizedOption:
    """Interactive Brokers adapter."""
    underlying = _as_str(data.get("underlying") or data.get("symbol") or "")
    expiration = _to_iso_expiration(data.get("lastTradeDateOrContractMonth") or "")
    option_type = _as_option_type(data.get("right"), default="put")
    strike = _as_float(data.get("strike") or 0)

    bid = _as_float(data.get("bid") or 0)
    ask = _as_float(data.get("ask") or 0)

    return NormalizedOption(
        occ_symbol=_as_str(data.get("localSymbol") or "") or _build_occ_from_raw(underlying, expiration, option_type, strike),
        underlying=underlying,
        strike=strike,
        expiration=expiration,
        expiration_timestamp=_expiration_to_ms(expiration),
        option_type=option_type,
        bid=bid,
        bid_size=_as_float(data.get("bidSize") or 0),
        ask=ask,
        ask_size=_as_float(data.get("askSize") or 0),
        mark=_as_float(data.get("mark"), default=(bid + ask) / 2 if (bid > 0 and ask > 0) else 0.0),
        last=_as_float(data.get("lastTradedPrice") or 0),
        volume=_as_float(data.get("volume") or 0),
        open_interest=_as_float(data.get("openInterest") or 0),
        implied_volatility=_as_float(data.get("impliedVolatility") or 0),
        timestamp=_as_int(data.get("time"), default=int(time.time() * 1000)),
    )


def tda_adapter(data: RawOptionData) -> NormalizedOption:
    """TD Ameritrade adapter."""
    underlying = _as_str(data.get("underlying") or data.get("underlyingSymbol") or "")
    expiration = _to_iso_expiration(data.get("expirationDate") or "")
    option_type = _as_option_type(data.get("putCall"), default="put")
    strike = _as_float(data.get("strikePrice") or 0)

    return NormalizedOption(
        occ_symbol=_as_str(data.get("symbol") or "") or _build_occ_from_raw(underlying, expiration, option_type, strike),
        underlying=underlying,
        strike=strike,
        expiration=expiration,
        expiration_timestamp=_expiration_to_ms(expiration) if expiration else 0,
        option_type=option_type,
        bid=_as_float(data.get("bid") or 0),
        bid_size=_as_float(data.get("bidSize") or 0),
        ask=_as_float(data.get("ask") or 0),
        ask_size=_as_float(data.get("askSize") or 0),
        mark=_as_float(data.get("mark") or 0),
        last=_as_float(data.get("last") or 0),
        volume=_as_float(data.get("totalVolume") or 0),
        open_interest=_as_float(data.get("openInterest") or 0),
        implied_volatility=_as_float(data.get("volatility") or 0),
        timestamp=_as_int(data.get("quoteTimeInLong"), default=int(time.time() * 1000)),
    )


BROKER_ADAPTERS: dict[str, BrokerAdapter] = {
    "generic": generic_adapter,
    "schwab": schwab_adapter,
    "ibkr": ibkr_adapter,
    "tda": tda_adapter,
}


def get_adapter(broker_name: str) -> BrokerAdapter:
    """Return adapter for broker, defaulting to the generic adapter."""
    return BROKER_ADAPTERS.get(_as_str(broker_name).lower(), generic_adapter)


def create_option_chain(
    symbol: str,
    spot: float,
    risk_free_rate: float,
    dividend_yield: float,
    raw_options: list[RawOptionData],
    broker: str = "generic",
) -> OptionChain:
    """Build an ``OptionChain`` from raw broker rows."""
    adapter = get_adapter(broker)
    return OptionChain(
        symbol=symbol,
        spot=spot,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        options=[adapter(raw) for raw in raw_options],
    )
