"""OCC option symbol utilities."""

from __future__ import annotations

import datetime as dt
import math
import re
from dataclasses import dataclass

from floe.types import OptionType

_OCC_TRAILER_RE = re.compile(r"([CP])(\d{8})$")


@dataclass
class OCCSymbolParams:
    symbol: str
    expiration: dt.date | dt.datetime | str
    option_type: OptionType
    strike: float
    padded: bool = False


@dataclass
class ParsedOCCSymbol:
    symbol: str
    expiration: dt.date
    option_type: OptionType
    strike: float


@dataclass
class StrikeGenerationParams:
    spot: float
    strikes_above: int = 10
    strikes_below: int = 10
    strike_increment_in_dollars: float = 1.0


# Backward-compatible alias for older imports.
OCCSymbol = ParsedOCCSymbol


def _to_expiration_date(expiration: dt.date | dt.datetime | str) -> dt.date:
    if isinstance(expiration, dt.datetime):
        return expiration.date()
    if isinstance(expiration, dt.date):
        return expiration

    value = str(expiration).strip()
    if not value:
        raise ValueError("expiration is required")

    # OCC compact date in YYMMDD.
    if len(value) == 6 and value.isdigit():
        year = 2000 + int(value[0:2])
        month = int(value[2:4])
        day = int(value[4:6])
        return dt.date(year, month, day)

    # Compact YYYYMMDD.
    if len(value) == 8 and value.isdigit():
        return dt.date(int(value[0:4]), int(value[4:6]), int(value[6:8]))

    # ISO date / datetime.
    if "T" in value:
        value = value.split("T", 1)[0]
    return dt.date.fromisoformat(value)


def build_occ_symbol(params: OCCSymbolParams) -> str:
    """Build an OCC-formatted option symbol."""
    exp = _to_expiration_date(params.expiration)
    root = params.symbol.upper().ljust(6) if params.padded else params.symbol.upper()
    date_str = exp.strftime("%y%m%d")
    type_char = "C" if params.option_type == "call" else "P"
    strike_str = str(int(round(params.strike * 1000))).zfill(8)
    return f"{root}{date_str}{type_char}{strike_str}"


def parse_occ_symbol(occ_symbol: str) -> ParsedOCCSymbol:
    """Parse an OCC symbol in padded or compact format."""
    m = _OCC_TRAILER_RE.search(occ_symbol)
    if m is None:
        raise ValueError(f"Invalid OCC symbol format: {occ_symbol}")

    type_char = m.group(1)
    strike_str = m.group(2)
    prefix = occ_symbol[: -9]

    if len(prefix) < 6:
        raise ValueError(f"Invalid OCC symbol format: {occ_symbol}")

    date_str = prefix[-6:]
    symbol = prefix[:-6].strip()
    if not symbol:
        raise ValueError(f"Invalid OCC symbol: no ticker found in {occ_symbol}")

    year = 2000 + int(date_str[0:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    expiration = dt.date(year, month, day)

    option_type: OptionType = "call" if type_char == "C" else "put"
    strike = int(strike_str) / 1000.0

    return ParsedOCCSymbol(
        symbol=symbol,
        expiration=expiration,
        option_type=option_type,
        strike=strike,
    )


def generate_strikes_around_spot(params: StrikeGenerationParams) -> list[float]:
    """Generate strikes around spot in ascending order."""
    inc = params.strike_increment_in_dollars
    if inc <= 0:
        return []

    base = math.floor(params.spot / inc) * inc
    strikes: list[float] = []

    for i in range(params.strikes_below, -1, -1):
        strikes.append(round(base - i * inc, 4))
    for i in range(1, params.strikes_above + 1):
        strikes.append(round(base + i * inc, 4))

    return strikes


def generate_occ_symbols_for_strikes(
    symbol: str,
    expiration: dt.date | dt.datetime | str,
    strikes: list[float],
    include_types: list[OptionType] | None = None,
) -> list[str]:
    """Generate OCC symbols for all strikes and requested option types."""
    types = include_types or ["call", "put"]
    out: list[str] = []
    for strike in strikes:
        for option_type in types:
            out.append(
                build_occ_symbol(
                    OCCSymbolParams(
                        symbol=symbol,
                        expiration=expiration,
                        option_type=option_type,
                        strike=strike,
                    )
                )
            )
    return out


def generate_occ_symbols_around_spot(
    symbol: str,
    expiration: dt.date | dt.datetime | str,
    spot: float,
    strikes_above: int = 10,
    strikes_below: int = 10,
    strike_increment_in_dollars: float = 1.0,
) -> list[str]:
    """Generate call and put OCC symbols around a spot price."""
    strikes = generate_strikes_around_spot(
        StrikeGenerationParams(
            spot=spot,
            strikes_above=strikes_above,
            strikes_below=strikes_below,
            strike_increment_in_dollars=strike_increment_in_dollars,
        )
    )
    return generate_occ_symbols_for_strikes(symbol, expiration, strikes)
