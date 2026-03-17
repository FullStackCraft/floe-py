"""Tests for floe.occ."""

import datetime as dt

from floe.occ import (
    OCCSymbolParams,
    StrikeGenerationParams,
    build_occ_symbol,
    generate_occ_symbols_around_spot,
    generate_occ_symbols_for_strikes,
    generate_strikes_around_spot,
    parse_occ_symbol,
)


def test_build_occ_symbol_format():
    symbol = build_occ_symbol(
        OCCSymbolParams(
            symbol="AAPL",
            expiration=dt.date(2024, 1, 19),
            option_type="call",
            strike=150,
        )
    )
    assert symbol == "AAPL240119C00150000"


def test_parse_occ_symbol_round_trip():
    original = build_occ_symbol(
        OCCSymbolParams(symbol="QQQ", expiration="2024-03-15", option_type="put", strike=425.5, padded=True)
    )
    parsed = parse_occ_symbol(original)

    assert parsed.symbol == "QQQ"
    assert parsed.expiration == dt.date(2024, 3, 15)
    assert parsed.option_type == "put"
    assert abs(parsed.strike - 425.5) < 1e-9


def test_generate_strikes_around_spot_count_and_ordering():
    strikes = generate_strikes_around_spot(
        StrikeGenerationParams(spot=450.25, strikes_above=10, strikes_below=10, strike_increment_in_dollars=5)
    )
    assert len(strikes) == 21
    assert strikes == sorted(strikes)


def test_generate_occ_symbols_for_strikes_both_types():
    strikes = [495, 500, 505]
    symbols = generate_occ_symbols_for_strikes("QQQ", "2024-01-19", strikes, ["call", "put"])
    assert len(symbols) == 6


def test_generate_occ_symbols_around_spot_convenience():
    symbols = generate_occ_symbols_around_spot("QQQ", "2024-01-19", 502.5, strikes_above=2, strikes_below=2, strike_increment_in_dollars=5)
    assert len(symbols) == 10
