"""HTTP clients for Hindsight, dealer minute-surface, and AMT datasets."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_DEFAULT_HINDSIGHT_BASE_URL = "https://hindsightapi.com/api"
_DEFAULT_DEALER_BASE_URL = "https://vannacharm.com/api"
_DEFAULT_AMT_BASE_URL = "https://amtjoy.com/api"
_DEFAULT_WHEELSCREENER_BASE_URL = "https://wheelscreener.com/api"
_DEFAULT_LEAPSSCREENER_BASE_URL = "https://leapsscreener.com/api"
_DEFAULT_OPTIONSCREENER_BASE_URL = "https://option-screener.com/api"
_DEFAULT_TIMEOUT = 30
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class HindsightDataRequest:
    start_date: str = ""
    end_date: str = ""
    country: str = ""
    min_volatility: int = 0
    event: str = ""


@dataclass
class DealerMinuteSurfacesRequest:
    symbol: str = ""
    trade_date: str = ""


@dataclass
class AMTRequest:
    symbol: str = ""
    session_id: str = ""


@dataclass
class HindsightEvent:
    id: int = 0
    event_id: str = ""
    date: str = ""
    time: str = ""
    timezone: str = ""
    country: str = ""
    country_code: str = ""
    event_name: str = ""
    volatility: int = 0
    actual: str | None = None
    forecast: str | None = None
    previous: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class SurfacePoint:
    strike: float = 0.0
    value: float = 0.0
    x: float = 0.0
    y: float = 0.0


@dataclass
class MinuteSurface:
    gamma: list[SurfacePoint] = field(default_factory=list)
    vanna: list[SurfacePoint] = field(default_factory=list)
    charm: list[SurfacePoint] = field(default_factory=list)
    iv: list[SurfacePoint] = field(default_factory=list)


@dataclass
class DealerMinuteSurface:
    id: str = ""
    run_at: str | None = None
    symbol: str = ""
    trade_date: str = ""
    minute_ts: str | None = None
    session_minute: int = 0
    spot: float = 0.0
    vix: float = 0.0
    surfaces: MinuteSurface = field(default_factory=MinuteSurface)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AMTSessionStatsRow:
    symbol: str = ""
    session_id: str = ""
    session_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AMTEventsRow:
    symbol: str = ""
    session_id: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)


# --- AMT Event Categories & Codes ---


class AMTEventCategory:
    """Event categories for filtering AMT minute events."""

    TPO = "TPO"
    PRICE = "Price"
    VOLUME = "Volume"
    SESSION = "Session"
    OVERNIGHT = "Overnight"


class AMTEventCode:
    """Typed event codes emitted by the AMT pipeline (66 codes across 5 categories)."""

    # --- TPO Events ---
    TPO_NEW_PRINT = "TPO_NEW_PRINT"
    TPO_PERIOD_FIRST_PRINT = "TPO_PERIOD_FIRST_PRINT"
    TPO_FIRST_3WIDE = "TPO_FIRST_3WIDE"
    TPO_FIRST_4WIDE = "TPO_FIRST_4WIDE"
    TPO_FIRST_5WIDE = "TPO_FIRST_5WIDE"
    TPO_SINGLE_PRINT_CREATED = "TPO_SINGLE_PRINT_CREATED"
    TPO_SINGLE_PRINT_FILLED = "TPO_SINGLE_PRINT_FILLED"
    TPO_POOR_HIGH = "TPO_POOR_HIGH"
    TPO_POOR_LOW = "TPO_POOR_LOW"
    TPO_EXCESS_HIGH = "TPO_EXCESS_HIGH"
    TPO_EXCESS_LOW = "TPO_EXCESS_LOW"

    # --- Price Cross Events ---
    PRICE_NHOD = "PRICE_NHOD"
    PRICE_NLOD = "PRICE_NLOD"
    PRICE_CROSS_HB_UP = "PRICE_CROSS_HB_UP"
    PRICE_CROSS_HB_DOWN = "PRICE_CROSS_HB_DOWN"
    PRICE_CROSS_TPOC_UP = "PRICE_CROSS_TPOC_UP"
    PRICE_CROSS_TPOC_DOWN = "PRICE_CROSS_TPOC_DOWN"
    PRICE_CROSS_VPOC_UP = "PRICE_CROSS_VPOC_UP"
    PRICE_CROSS_VPOC_DOWN = "PRICE_CROSS_VPOC_DOWN"
    PRICE_CROSS_VAH_UP = "PRICE_CROSS_VAH_UP"
    PRICE_CROSS_VAH_DOWN = "PRICE_CROSS_VAH_DOWN"
    PRICE_CROSS_VAL_UP = "PRICE_CROSS_VAL_UP"
    PRICE_CROSS_VAL_DOWN = "PRICE_CROSS_VAL_DOWN"
    PRICE_CROSS_OR_HIGH_UP = "PRICE_CROSS_OR_HIGH_UP"
    PRICE_CROSS_OR_HIGH_DOWN = "PRICE_CROSS_OR_HIGH_DOWN"
    PRICE_CROSS_OR_LOW_UP = "PRICE_CROSS_OR_LOW_UP"
    PRICE_CROSS_OR_LOW_DOWN = "PRICE_CROSS_OR_LOW_DOWN"
    PRICE_CROSS_IB_HIGH_UP = "PRICE_CROSS_IB_HIGH_UP"
    PRICE_CROSS_IB_HIGH_DOWN = "PRICE_CROSS_IB_HIGH_DOWN"
    PRICE_CROSS_IB_LOW_UP = "PRICE_CROSS_IB_LOW_UP"
    PRICE_CROSS_IB_LOW_DOWN = "PRICE_CROSS_IB_LOW_DOWN"
    PRICE_CROSS_PHOD_UP = "PRICE_CROSS_PHOD_UP"
    PRICE_CROSS_PHOD_DOWN = "PRICE_CROSS_PHOD_DOWN"
    PRICE_CROSS_PLOD_UP = "PRICE_CROSS_PLOD_UP"
    PRICE_CROSS_PLOD_DOWN = "PRICE_CROSS_PLOD_DOWN"
    PRICE_CROSS_PREV_CLOSE_UP = "PRICE_CROSS_PREV_CLOSE_UP"
    PRICE_CROSS_PREV_CLOSE_DOWN = "PRICE_CROSS_PREV_CLOSE_DOWN"
    PRICE_CROSS_PREV_OPEN_UP = "PRICE_CROSS_PREV_OPEN_UP"
    PRICE_CROSS_PREV_OPEN_DOWN = "PRICE_CROSS_PREV_OPEN_DOWN"
    PRICE_CROSS_ONH_UP = "PRICE_CROSS_ONH_UP"
    PRICE_CROSS_ONH_DOWN = "PRICE_CROSS_ONH_DOWN"
    PRICE_CROSS_ONL_UP = "PRICE_CROSS_ONL_UP"
    PRICE_CROSS_ONL_DOWN = "PRICE_CROSS_ONL_DOWN"
    PRICE_CROSS_VWAP_UP = "PRICE_CROSS_VWAP_UP"
    PRICE_CROSS_VWAP_DOWN = "PRICE_CROSS_VWAP_DOWN"
    PRICE_CROSS_VWAP_SD1_UP = "PRICE_CROSS_VWAP_SD1_UP"
    PRICE_CROSS_VWAP_SD1_DOWN = "PRICE_CROSS_VWAP_SD1_DOWN"
    PRICE_CROSS_VWAP_SD2_UP = "PRICE_CROSS_VWAP_SD2_UP"
    PRICE_CROSS_VWAP_SD2_DOWN = "PRICE_CROSS_VWAP_SD2_DOWN"

    # --- Volume Profile Events ---
    VOL_VPOC_SHIFT_UP = "VOL_VPOC_SHIFT_UP"
    VOL_VPOC_SHIFT_DOWN = "VOL_VPOC_SHIFT_DOWN"
    VOL_VA_MIGRATION_UP = "VOL_VA_MIGRATION_UP"
    VOL_VA_MIGRATION_DOWN = "VOL_VA_MIGRATION_DOWN"
    VOL_VA_EXPANDING = "VOL_VA_EXPANDING"
    VOL_VA_CONTRACTING = "VOL_VA_CONTRACTING"

    # --- Session Structure Events ---
    SESSION_PERIOD_TRANSITION = "SESSION_PERIOD_TRANSITION"
    SESSION_OR_ESTABLISHED = "SESSION_OR_ESTABLISHED"
    SESSION_IB_ESTABLISHED = "SESSION_IB_ESTABLISHED"
    SESSION_IB_EXTENSION_UP = "SESSION_IB_EXTENSION_UP"
    SESSION_IB_EXTENSION_DOWN = "SESSION_IB_EXTENSION_DOWN"
    SESSION_OR_EXTENSION_UP = "SESSION_OR_EXTENSION_UP"
    SESSION_OR_EXTENSION_DOWN = "SESSION_OR_EXTENSION_DOWN"
    SESSION_GAP_FILL = "SESSION_GAP_FILL"
    SESSION_GLOBEX_GAP_FILL = "SESSION_GLOBEX_GAP_FILL"
    SESSION_HALFBACK_REACHED = "SESSION_HALFBACK_REACHED"

    # --- Overnight Events (futures only) ---
    ON_ASIA_OPEN = "ON_ASIA_OPEN"
    ON_ASIA_CLOSE = "ON_ASIA_CLOSE"
    ON_EU_OPEN = "ON_EU_OPEN"
    ON_EU_CLOSE = "ON_EU_CLOSE"
    ON_NEW_HIGH = "ON_NEW_HIGH"
    ON_NEW_LOW = "ON_NEW_LOW"


@dataclass
class OptionsScreenerRequest:
    """Request for options strategy data from Wheel Screener, LEAPS Screener, or Option Screener."""

    strategy: str = ""
    search: str = ""
    page: int = 0
    page_size: int = 0
    order_by: str = ""
    order_direction: str = ""
    extra_params: dict[str, str] = field(default_factory=dict)


@dataclass
class OptionsScreenerResponse:
    """Paginated response of options strategy rows."""

    data: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    page: int = 0
    page_size: int = 0


class APIError(Exception):
    """Raised when an API request fails."""

    def __init__(
        self,
        status_code: int = 0,
        message: str = "",
        subscription_end: str = "",
        raw_body: str = "",
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.subscription_end = subscription_end
        self.raw_body = raw_body
        super().__init__(str(self))

    def __str__(self) -> str:
        parts: list[str] = []
        if self.status_code > 0:
            parts.append(f"{self.status_code}")
        if self.message:
            parts.append(self.message)
        detail = ": ".join(parts) if parts else "unknown"
        return f"api error: {detail}"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class ApiClient:
    """Zero-dependency HTTP client for Hindsight, VannaCharm, and AMT APIs."""

    def __init__(
        self,
        api_key: str,
        timeout: int = _DEFAULT_TIMEOUT,
        hindsight_base_url: str = _DEFAULT_HINDSIGHT_BASE_URL,
        dealer_base_url: str = _DEFAULT_DEALER_BASE_URL,
        amt_base_url: str = _DEFAULT_AMT_BASE_URL,
        wheel_screener_base_url: str = _DEFAULT_WHEELSCREENER_BASE_URL,
        leaps_screener_base_url: str = _DEFAULT_LEAPSSCREENER_BASE_URL,
        option_screener_base_url: str = _DEFAULT_OPTIONSCREENER_BASE_URL,
    ) -> None:
        self._api_key = api_key.strip()
        self._timeout = timeout
        self._hindsight_base_url = hindsight_base_url
        self._dealer_base_url = dealer_base_url
        self._amt_base_url = amt_base_url
        self._wheel_screener_base_url = wheel_screener_base_url
        self._leaps_screener_base_url = leaps_screener_base_url
        self._option_screener_base_url = option_screener_base_url

    # -- public API --------------------------------------------------------

    def get_hindsight_data(self, req: HindsightDataRequest) -> list[HindsightEvent]:
        _validate_hindsight_data_request(req)

        params: dict[str, str] = {
            "start_date": req.start_date.strip(),
            "end_date": req.end_date.strip(),
        }
        if req.country.strip():
            params["country"] = req.country.strip()
        if req.min_volatility > 0:
            params["min_volatility"] = str(req.min_volatility)
        if req.event.strip():
            params["event"] = req.event.strip()

        body = self._get_raw(self._hindsight_base_url, "/getData", params)
        return _decode_list(body, _parse_hindsight_event, "hindsight")

    def get_hindsight_sample(self) -> list[HindsightEvent]:
        body = self._get_raw(self._hindsight_base_url, "/getSample", {})
        return _decode_list(body, _parse_hindsight_event, "hindsight")

    def get_dealer_minute_surfaces(self, req: DealerMinuteSurfacesRequest) -> list[DealerMinuteSurface]:
        _validate_dealer_minute_surfaces_request(req)
        params = {
            "symbol": req.symbol.strip(),
            "trade_date": req.trade_date.strip(),
        }
        body = self._get_raw(self._dealer_base_url, "/getMinuteSurfaces", params)
        return _decode_list(body, _parse_dealer_minute_surface, "dealer minute surfaces")

    def get_amt_session_stats(self, req: AMTRequest) -> list[AMTSessionStatsRow]:
        _validate_amt_request(req)
        params = {
            "symbol": req.symbol.strip().upper(),
            "session_id": req.session_id.strip(),
        }
        body = self._get_raw(self._amt_base_url, "/getSessionStats", params)
        return _decode_list(body, _parse_amt_session_stats, "amt session stats")

    def get_amt_events(self, req: AMTRequest) -> list[AMTEventsRow]:
        _validate_amt_request(req)
        params = {
            "symbol": req.symbol.strip().upper(),
            "session_id": req.session_id.strip(),
        }
        body = self._get_raw(self._amt_base_url, "/getAMTEvents", params)
        return _decode_list(body, _parse_amt_events, "amt events")

    def get_wheel_screener_data(self, req: OptionsScreenerRequest) -> OptionsScreenerResponse:
        """Retrieve options strategy data from the Wheel Screener API."""
        return self._get_options_screener_data(self._wheel_screener_base_url, "/get-options", req)

    def get_leaps_screener_data(self, req: OptionsScreenerRequest) -> OptionsScreenerResponse:
        """Retrieve options strategy data from the LEAPS Screener API."""
        return self._get_options_screener_data(self._leaps_screener_base_url, "/get-options", req)

    def get_option_screener_data(self, req: OptionsScreenerRequest) -> OptionsScreenerResponse:
        """Retrieve options strategy data from the Option Screener API."""
        return self._get_options_screener_data(self._option_screener_base_url, "/getOptionsData", req)

    # -- internals ---------------------------------------------------------

    def _get_options_screener_data(
        self, base_url: str, path: str, req: OptionsScreenerRequest
    ) -> OptionsScreenerResponse:
        _validate_options_screener_request(req)

        params: dict[str, str] = {"strategy": req.strategy.strip().upper()}
        if req.search.strip():
            params["search"] = req.search.strip()
        if req.page > 0:
            params["page"] = str(req.page)
        if req.page_size > 0:
            params["page_size"] = str(req.page_size)
        if req.order_by.strip():
            params["order_by"] = req.order_by.strip()
        if req.order_direction.strip():
            params["order_direction"] = req.order_direction.strip()

        for k, v in req.extra_params.items():
            if v.strip():
                params[k] = v.strip()

        body = self._get_raw(base_url, path, params)
        return _decode_options_screener_response(body)

    def _get_raw(self, base_url: str, path: str, params: dict[str, str]) -> bytes:
        if not self._api_key:
            raise ValueError("api key is required")

        url = base_url.rstrip("/") + path
        if params:
            url += "?" + urlencode(params)

        req = Request(url, method="GET")
        req.add_header("Accept", "application/json")
        req.add_header("X-API-Key", self._api_key)

        try:
            with urlopen(req, timeout=self._timeout) as resp:
                body: bytes = resp.read()
        except HTTPError as exc:
            raw = exc.read()
            raise _decode_api_error(exc.code, raw) from None
        except URLError as exc:
            raise APIError(message=f"request failed: {exc.reason}") from exc

        if not body or not body.strip():
            raise APIError(message="empty response body")

        return body


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_hindsight_data_request(req: HindsightDataRequest) -> None:
    start = req.start_date.strip()
    end = req.end_date.strip()
    if not start:
        raise ValueError("start_date is required")
    if not end:
        raise ValueError("end_date is required")
    if not _DATE_RE.match(start):
        raise ValueError("start_date must be in YYYY-MM-DD format")
    if not _DATE_RE.match(end):
        raise ValueError("end_date must be in YYYY-MM-DD format")
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    if req.min_volatility != 0 and not (1 <= req.min_volatility <= 3):
        raise ValueError("min_volatility must be between 1 and 3 when provided")


def _validate_dealer_minute_surfaces_request(req: DealerMinuteSurfacesRequest) -> None:
    if not req.symbol.strip():
        raise ValueError("symbol is required")
    if not req.trade_date.strip():
        raise ValueError("trade_date is required")
    if not _DATE_RE.match(req.trade_date.strip()):
        raise ValueError("trade_date must be in YYYY-MM-DD format")


def _validate_amt_request(req: AMTRequest) -> None:
    if not req.symbol.strip():
        raise ValueError("symbol is required")
    if not req.session_id.strip():
        raise ValueError("session_id is required")
    if not _DATE_RE.match(req.session_id.strip()):
        raise ValueError("session_id must be in YYYY-MM-DD format")


# ---------------------------------------------------------------------------
# Decode helpers
# ---------------------------------------------------------------------------


def _first_non_empty(*values: str) -> str:
    for v in values:
        if v and v.strip():
            return v.strip()
    return ""


def _decode_api_error(status_code: int, body: bytes) -> APIError:
    trimmed = body.decode("utf-8", errors="replace").strip() if body else ""
    if not trimmed:
        return APIError(status_code=status_code, message=f"HTTP {status_code}")

    message = ""
    subscription_end = ""
    try:
        payload = json.loads(trimmed)
        message = _first_non_empty(
            payload.get("error", ""),
            payload.get("message", ""),
        )
        subscription_end = _first_non_empty(
            payload.get("subscriptionEnd", ""),
            payload.get("subscription_end", ""),
        )
    except (json.JSONDecodeError, AttributeError):
        pass

    if not message:
        message = trimmed[:300] + ("..." if len(trimmed) > 300 else "")
    if not message:
        message = f"HTTP {status_code}"

    return APIError(
        status_code=status_code,
        message=message,
        subscription_end=subscription_end,
        raw_body=trimmed,
    )


def _decode_list(body: bytes, parser: Any, label: str) -> list:
    text = body.decode("utf-8", errors="replace")
    data = json.loads(text)

    # Try envelope format: {"success": true, "data": [...]}
    if isinstance(data, dict):
        is_envelope = any(
            k in data for k in ("success", "data", "error", "message", "subscriptionEnd", "subscription_end")
        )
        if is_envelope:
            if not data.get("success", False):
                raise APIError(
                    status_code=200,
                    message=_first_non_empty(
                        data.get("error", ""),
                        data.get("message", ""),
                        "request failed",
                    ),
                    subscription_end=_first_non_empty(
                        data.get("subscriptionEnd", ""),
                        data.get("subscription_end", ""),
                    ),
                    raw_body=text,
                )
            raw_list = data.get("data", [])
            if isinstance(raw_list, list):
                return [parser(item) for item in raw_list]

    # Try raw array format
    if isinstance(data, list):
        return [parser(item) for item in data]

    raise APIError(message=f"failed to decode {label} response")


def _parse_hindsight_event(d: dict) -> HindsightEvent:
    return HindsightEvent(
        id=d.get("id", 0),
        event_id=d.get("event_id", ""),
        date=d.get("date", ""),
        time=d.get("time", ""),
        timezone=d.get("timezone", ""),
        country=d.get("country", ""),
        country_code=d.get("country_code", ""),
        event_name=d.get("event_name", ""),
        volatility=d.get("volatility", 0),
        actual=d.get("actual"),
        forecast=d.get("forecast"),
        previous=d.get("previous"),
        created_at=d.get("created_at"),
        updated_at=d.get("updated_at"),
    )


def _parse_surface_point(d: dict) -> SurfacePoint:
    return SurfacePoint(
        strike=d.get("strike", 0.0),
        value=d.get("value", 0.0),
        x=d.get("x", 0.0),
        y=d.get("y", 0.0),
    )


def _parse_minute_surface(d: dict) -> MinuteSurface:
    return MinuteSurface(
        gamma=[_parse_surface_point(p) for p in d.get("gamma", [])],
        vanna=[_parse_surface_point(p) for p in d.get("vanna", [])],
        charm=[_parse_surface_point(p) for p in d.get("charm", [])],
        iv=[_parse_surface_point(p) for p in d.get("iv", [])],
    )


def _parse_dealer_minute_surface(d: dict) -> DealerMinuteSurface:
    return DealerMinuteSurface(
        id=d.get("id", ""),
        run_at=d.get("run_at"),
        symbol=d.get("symbol", ""),
        trade_date=d.get("trade_date", ""),
        minute_ts=d.get("minute_ts"),
        session_minute=d.get("session_minute", 0),
        spot=d.get("spot", 0.0),
        vix=d.get("vix", 0.0),
        surfaces=_parse_minute_surface(d.get("surfaces", {})),
        metadata=d.get("metadata", {}),
    )


def _parse_amt_session_stats(d: dict) -> AMTSessionStatsRow:
    return AMTSessionStatsRow(
        symbol=d.get("symbol", ""),
        session_id=d.get("session_id", ""),
        session_data=d.get("session_data", {}),
    )


def _parse_amt_events(d: dict) -> AMTEventsRow:
    return AMTEventsRow(
        symbol=d.get("symbol", ""),
        session_id=d.get("session_id", ""),
        events=d.get("events", []),
    )


def _validate_options_screener_request(req: OptionsScreenerRequest) -> None:
    if not req.strategy.strip():
        raise ValueError("strategy is required")


def _decode_options_screener_response(body: bytes) -> OptionsScreenerResponse:
    text = body.decode("utf-8", errors="replace")
    data = json.loads(text)

    # Try envelope format: {"success": true, "data": [...], "total": N, ...}
    if isinstance(data, dict):
        is_envelope = any(
            k in data for k in ("success", "data", "error", "message", "subscriptionEnd", "subscription_end")
        )
        if is_envelope:
            if not data.get("success", False):
                raise APIError(
                    status_code=200,
                    message=_first_non_empty(
                        data.get("error", ""),
                        data.get("message", ""),
                        "request failed",
                    ),
                    subscription_end=_first_non_empty(
                        data.get("subscriptionEnd", ""),
                        data.get("subscription_end", ""),
                    ),
                    raw_body=text,
                )
            raw_list = data.get("data", [])
            rows = raw_list if isinstance(raw_list, list) else []
            return OptionsScreenerResponse(
                data=rows,
                total=data.get("total", len(rows)),
                page=data.get("page", 1),
                page_size=data.get("page_size", len(rows)),
            )

    # Try raw array format
    if isinstance(data, list):
        return OptionsScreenerResponse(
            data=data,
            total=len(data),
            page=1,
            page_size=len(data),
        )

    raise APIError(message="failed to decode options screener response")
