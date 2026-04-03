---
title: Dataset API Clients
description: Query hindsight, dealer, AMT, and options screener datasets with ApiClient.
order: 7
---

## Create the Client

```python
from floe import AMTEventCategory, AMTEventCode, AMTRequest, DealerMinuteSurfacesRequest, HindsightDataRequest, ApiClient

client = ApiClient("YOUR_API_KEY")

hindsight_events = client.get_hindsight_data(
    HindsightDataRequest(
        start_date="2026-03-01",
        end_date="2026-03-16",
        country="US",
        min_volatility=2,
        event="CPI",
    )
)
print(len(hindsight_events))

sample = client.get_hindsight_sample()
print(len(sample))

minute_rows = client.get_dealer_minute_surfaces(
    DealerMinuteSurfacesRequest(symbol="SPY", trade_date="2026-03-10")
)
print(len(minute_rows))

# AMT Session Stats — supports futures (ES, NQ, YM, RTY, GC, SI, CL, NG, BTC, ZN
# and micros MES, MNQ, MYM, M2K, MGC, MCL, MBT, SIL) and stocks (SPY, QQQ, IWM,
# DIA, AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA, AVGO, AMD, NFLX, JPM).
session_rows = client.get_amt_session_stats(
    AMTRequest(symbol="NQ", session_id="2025-03-10")
)
print(len(session_rows))

# Stock example
spy_rows = client.get_amt_session_stats(
    AMTRequest(symbol="SPY", session_id="2025-03-10")
)
print(len(spy_rows))

# AMT Events — 66 typed events across 5 categories (TPO, Price, Volume, Session, Overnight)
from floe import AMTEventCategory, AMTEventCode

event_rows = client.get_amt_events(
    AMTRequest(symbol="NQ", session_id="2025-03-10")
)
print(len(event_rows))

# Filter events by category
tpo_events = [
    e for e in event_rows[0].events
    if e.get("event_category") == AMTEventCategory.TPO
]
print(f"TPO events: {len(tpo_events)}")

# Check for specific event codes
poor_highs = [
    e for e in event_rows[0].events
    if e.get("event_code") == AMTEventCode.TPO_POOR_HIGH
]
print(f"Poor highs: {len(poor_highs)}")

# Wheel Screener
from floe import OptionsScreenerRequest

wheel_data = client.get_wheel_screener_data(
    OptionsScreenerRequest(
        strategy="CC",
        page_size=10,
        order_by="score",
        order_direction="desc",
        extra_params={"min_score": "70", "sector": "Technology"},
    )
)
print(f"wheel rows: {len(wheel_data.data)}, total: {wheel_data.total}")

# LEAPS Screener
leaps_data = client.get_leaps_screener_data(
    OptionsScreenerRequest(
        strategy="LC",
        extra_params={"min_dte": "180", "max_delta": "0.7"},
    )
)
print(f"leaps rows: {len(leaps_data.data)}, total: {leaps_data.total}")

# Option Screener
option_data = client.get_option_screener_data(
    OptionsScreenerRequest(
        strategy="CDS",
        search="AAPL",
        page_size=25,
    )
)
print(f"option screener rows: {len(option_data.data)}, total: {option_data.total}")
```
