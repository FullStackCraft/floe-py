---
title: Dataset API Clients
description: Query hindsight, dealer, AMT, and options screener datasets with ApiClient.
order: 7
---

## Create the Client

```python
from floe import AMTRequest, DealerMinuteSurfacesRequest, HindsightDataRequest, ApiClient

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

session_rows = client.get_amt_session_stats(
    AMTRequest(symbol="NQ", session_id="2026-03-10")
)
print(len(session_rows))

event_rows = client.get_amt_events(
    AMTRequest(symbol="NQ", session_id="2026-03-10")
)
print(len(event_rows))

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
