#!/usr/bin/env python3
"""Candle volume extension for the Desk C loader (Nov 16, 2026). A SEPARATE file so deskc_kp_load.py (audited, c76c7f7d) stays byte for byte.
candles(root, jobs, cut) -> ticker -> {end_ts: (yes_bid, yes_ask, volume)} for candles ending at or before cut[ticker].
volume_fp is the traded volume of THAT candle, not a running total (format check on the landed SIBHIT candles, counts only: 1,636 of 3,933
candle series with 3 or more candles were non-monotone, which a cumulative field cannot be). A minute with no candle is zero volume."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deskc_kp_load as KL


def candles(root, jobs, cut):
    q = {}

    def add(t, cs):
        if t not in cut:
            return
        for c in cs or []:
            ts = c.get("end_period_ts")
            if isinstance(ts, int) and ts <= cut[t]:
                q.setdefault(t, {}).setdefault(ts, (KL._px(c.get("yes_bid")), KL._px(c.get("yes_ask")), KL.num(c.get("volume_fp")) or 0.0))

    for job in jobs:
        for row, b in KL.bodies(root, job):
            if isinstance(b.get("markets"), list) and b["markets"] and "candlesticks" in (b["markets"][0] or {}):
                for m in b["markets"]:
                    add(m.get("market_ticker") or m.get("ticker"), m.get("candlesticks"))
            elif "candlesticks" in b:
                parts = (row.get("path") or "").split("/")
                add(b.get("ticker") or (parts[-2] if len(parts) >= 2 else ""), b.get("candlesticks"))
    return q
