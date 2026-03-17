---
title: Dataset API Clients
description: Query hindsight, dealer, and AMT datasets with ApiClient.
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
```
