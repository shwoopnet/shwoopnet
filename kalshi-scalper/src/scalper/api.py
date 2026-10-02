"""Minimal Kalshi REST client. Public market data only for now.

No order placement lives here on purpose. Orders go through the risk gate
(risk.py) and are added only after paper results clear the pre-registered bar.
Quotes are dollar strings ("0.0950"), not cents.
"""
from __future__ import annotations

import json
import time
import urllib.request

BASE = "https://api.elections.kalshi.com/trade-api/v2"


def _get(path: str, params: dict | None = None, retries: int = 3) -> dict:
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.load(r)
        except Exception as e:  # network blips and 429s: back off and retry
            last = e
            time.sleep(1.5 * (i + 1))
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
