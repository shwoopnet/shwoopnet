"""Footprint (order-flow) data for a Kalshi market from the public trade tape. Research tool: nothing here places an order.
Each trade has a YES price, a size and the side the TAKER bought. In YES-price terms a taker buying YES lifts the ask (a buy) and a taker buying NO hits the bid (a sell)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from . import api


def trades(ticker: str, min_ts: int, max_ts: int) -> list[dict]:
    out, cur = [], None
    while True:
        p = {"ticker": ticker, "limit": 1000, "min_ts": min_ts, "max_ts": max_ts}
        if cur:
            p["cursor"] = cur
        d = api._get("/markets/trades", p)
        out += d.get("trades", [])
        cur = d.get("cursor")
        if not cur or not d.get("trades"):
            break
    return out


def parse(t: dict):
    """(epoch seconds, yes price in cents, size, +1 buy / -1 sell)."""
    ts = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
    price = round(float(t["yes_price_dollars"]) * 100)
    size = float(t["count_fp"])
    return ts, price, size, (1 if t["taker_outcome_side"] == "yes" else -1)


def footprint(parsed: list[tuple], bar_s: int = 60) -> dict[int, dict[int, list[float]]]:
    """bar start (epoch) -> {price cents: [sell volume, buy volume]}."""
    bars: dict[int, dict[int, list[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    for ts, price, size, side in parsed:
        bars[int(ts // bar_s) * bar_s][price][1 if side > 0 else 0] += size
    return bars


def bar_stats(levels: dict[int, list[float]]) -> dict:
    """Delta, total, open-to-close proxy (first and last level by price), point of control, and the stacked-imbalance count (3:1 at 3 or more adjacent levels)."""
    ps = sorted(levels)
    sell = sum(v[0] for v in levels.values())
    buy = sum(v[1] for v in levels.values())
    poc = max(ps, key=lambda p: levels[p][0] + levels[p][1])
    streak = best = 0
    for p in ps:
        s, b = levels[p]
        if (b >= 3 * max(s, 1.0) and b >= 50) or (s >= 3 * max(b, 1.0) and s >= 50):
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    return {"buy": buy, "sell": sell, "delta": buy - sell, "total": buy + sell, "low": ps[0], "high": ps[-1], "poc": poc, "stacked": best}
