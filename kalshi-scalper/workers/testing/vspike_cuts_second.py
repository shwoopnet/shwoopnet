#!/usr/bin/env python3
"""V3 vspike SEARCH tercile cuts, BUILD 2 (Testing Desk, Nov 17, 2026), from Desk A's rulings V1 to V8 (message of Nov 17, 00:39Z) and VSPIKE_CUTS_SECOND_HAND_CASE.md. Pure functions.
markets: [(ticker, close_ts, series)] already filtered by the loader; candles {ticker: {end_ts: (end_ts, yes_bid, yes_ask, last, volume, oi)}}."""
import math, time
BUCKETS = tuple(range(120, 841, 60))
LAST_SEARCH = {"BNB": "2026-09-03", "BTC": "2026-09-03", "COPPER": "2026-09-13", "DOGE": "2026-09-03", "ETH": "2026-09-03", "EURUSD": "2026-09-27", "GBPUSD": "2026-09-27", "GOLD": "2026-09-03", "HYPE": "2026-09-03", "NATGAS": "2026-09-14", "NEAR": "2026-09-03", "PALLADIUM": "2026-09-24", "PLATINUM": "2026-09-24", "SILVER": "2026-09-03", "SOL": "2026-09-07", "USDJPY": "2026-09-27", "WTI": "2026-09-04", "XRP": "2026-09-03", "ZEC": "2026-09-03"}


def short(series):
    s = series[2:] if series.startswith("KX") else series
    return s[:-3] if s.endswith("15M") else s


def is_search(series, close_ts): return time.strftime("%Y-%m-%d", time.gmtime(close_ts)) <= LAST_SEARCH[short(series)]


def vspike(cand, e):
    """x at candle end e of one market's candles, or None"""
    c = cand.get(e)
    if c is None or not (c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1): return None
    vols = []
    for k in range(0, 6):
        q = cand.get(e - 60 * k)
        if q is None or q[4] is None: return None
        vols.append(q[4])
    m = sum(vols[1:]) / 5
    if not m > 0: return None
    return vols[0] / m


def cuts(values):
    if not values: return None
    v = sorted(values); n = len(v)
    return v[math.ceil(n / 3) - 1], v[math.ceil(2 * n / 3) - 1]


def table(markets, candles):
    out = {}
    for series in sorted(set(s for _t, _c, s in markets if short(s) in LAST_SEARCH)):
        row = {}
        sm = [(t, c) for t, c, s in markets if s == series and is_search(s, c)]
        for b in BUCKETS:
            xs = [x for t, c in sm for x in [vspike(candles.get(t, {}), c - b)] if x is not None]
            cu = cuts(xs); row[str(b)] = {"c1": cu[0], "c2": cu[1]} if cu else {"c1": None, "c2": None}
        out[series] = row
    return out
