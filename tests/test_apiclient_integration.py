"""Integration tests for AMT JOY API endpoints.

Run with:
    FLOE_DATA_API_KEY=amtjoy_live_xxx pytest tests/test_apiclient_integration.py -v

Tests will skip gracefully if the API key is not provided.
"""

import os

import pytest

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; key can still come from env

from floe.apiclient import AMTEventCategory, AMTRequest, ApiClient

API_KEY = os.getenv("FLOE_DATA_API_KEY", "")
skip_no_key = pytest.mark.skipif(not API_KEY, reason="FLOE_DATA_API_KEY not set")


@skip_no_key
def test_get_amt_session_stats_futures():
    client = ApiClient(API_KEY)
    rows = client.get_amt_session_stats(AMTRequest(symbol="NQ", session_id="2025-03-10"))

    assert len(rows) > 0
    assert rows[0].symbol == "NQ"
    assert rows[0].session_id == "2025-03-10"
    assert isinstance(rows[0].session_data, dict)
    assert len(rows[0].session_data) > 0


@skip_no_key
def test_get_amt_session_stats_stock():
    client = ApiClient(API_KEY)
    rows = client.get_amt_session_stats(AMTRequest(symbol="SPY", session_id="2025-03-10"))

    assert len(rows) > 0
    assert rows[0].symbol == "SPY"
    assert isinstance(rows[0].session_data, dict)


@skip_no_key
def test_get_amt_events_futures():
    client = ApiClient(API_KEY)
    rows = client.get_amt_events(AMTRequest(symbol="NQ", session_id="2025-03-10"))

    assert len(rows) > 0
    assert rows[0].symbol == "NQ"
    assert isinstance(rows[0].events, list)
    assert len(rows[0].events) > 0

    # Verify event structure
    event = rows[0].events[0]
    assert "event_code" in event
    assert "event_category" in event


@skip_no_key
def test_get_amt_events_stock():
    client = ApiClient(API_KEY)
    rows = client.get_amt_events(AMTRequest(symbol="SPY", session_id="2025-03-10"))

    assert len(rows) > 0
    assert isinstance(rows[0].events, list)

    # Stocks should not have overnight events
    overnight_events = [
        e for e in rows[0].events if e.get("event_category") == AMTEventCategory.OVERNIGHT
    ]
    assert len(overnight_events) == 0


@skip_no_key
def test_get_amt_session_stats_invalid_symbol():
    client = ApiClient(API_KEY)
    rows = client.get_amt_session_stats(AMTRequest(symbol="ZZZZZ", session_id="2025-03-10"))

    assert len(rows) == 0


@skip_no_key
def test_get_amt_events_invalid_session_id():
    client = ApiClient(API_KEY)
    with pytest.raises(ValueError):
        client.get_amt_events(AMTRequest(symbol="NQ", session_id="not-a-date"))
