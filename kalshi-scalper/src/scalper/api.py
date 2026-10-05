"""Minimal Kalshi REST client. Public market data only for now.

No order placement lives here on purpose. Orders go through the risk gate
(risk.py) and are added only after paper results clear the pre-registered bar.
Quotes are dollar strings ("0.0950"), not cents.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def _wait_for(i: int, err: Exception) -> float:
    """Seconds to wait before attempt i+1. Kalshi's 429 (rate limited) is not a
    failure of the request, it is a request to slow down: honour Retry-After and
    otherwise back off hard, so a long job waits out a limit instead of dying."""
    wait = 1.5 * (i + 1)
    if isinstance(err, urllib.error.HTTPError) and err.code == 429:
        try:
            wait = max(wait, float(err.headers.get("Retry-After", 0)))
        except (TypeError, ValueError):
            pass
        wait = max(wait, 5.0 * (i + 1))
    return min(wait, 60.0)


def _get(path: str, params: dict | None = None, retries: int = 8) -> dict:
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.load(r)
        except Exception as e:  # network blips and 429s: back off and retry
            last = e
            time.sleep(_wait_for(i, e))
    raise RuntimeError(f"GET {path} failed: {last}")


def markets(series_ticker: str, status: str = "open", limit: int = 20) -> list[dict]:
    return _get("/markets", {"series_ticker": series_ticker, "status": status,
                             "limit": limit}).get("markets", [])


def orderbook(ticker: str) -> dict:
    return _get(f"/markets/{ticker}/orderbook")["orderbook_fp"]


def f(x) -> float | None:
    """Dollar string to float, tolerating missing or empty values."""
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


def settled_markets(series: str, min_close_ts: int, max_close_ts: int):
    """Every settled market of a series that closed in [min, max], following the
    cursor until the listing is exhausted."""
    cursor = None
    while True:
        params = {"series_ticker": series, "status": "settled", "min_close_ts": min_close_ts,
                  "max_close_ts": max_close_ts, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        d = _get("/markets", params)
        yield from d.get("markets", [])
        cursor = d.get("cursor")
        if not cursor:
            return


def candlesticks(series: str, ticker: str, start_ts: int, end_ts: int) -> list[dict]:
    """One minute candles for a market, each with yes_bid and yes_ask OHLC."""
    d = _get(f"/series/{series}/markets/{ticker}/candlesticks",
             {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1})
    return d.get("candlesticks", [])
