"""NFLFTD1: NFL first touchdown scorer, cheap side only (ask 3c-30c), research only.
Census command reads listings only (ticker, event, close time, volume); never result, price or candle."""
from __future__ import annotations
import hashlib, json, math, re, sys, time
from collections import Counter, defaultdict

CUT = "2026-10-03T16:00:00Z"
MIN_TREATED = 150
LIMIT = 0.30
RATIO = 3.0


def fee(p: float, c: int = 10) -> float:
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def net(win: bool, ask: float, mult: float = 1.0) -> float:
    return (1.0 if win else 0.0) - ask - fee(ask) * mult


def split_thirds(games: list[str]) -> tuple[list[str], list[str]]:
    """games sorted by start time; first two thirds fit, last third test."""
    k = (2 * len(games)) // 3
    return games[:k], games[k:]


def pick_two(rows: list[dict], treated: bool) -> list[dict]:
    """rows have ticker, ratio, ask. At most 2 per game: highest ratio (treated) else sha1(ticker)."""
    if treated:
        rows = [r for r in rows if r["ratio"] >= RATIO and r["ask"] <= LIMIT]
        key = lambda r: (-r["ratio"], hashlib.sha1(r["ticker"].encode()).hexdigest())
    else:
        key = lambda r: hashlib.sha1(r["ticker"].encode()).hexdigest()
    return sorted(rows, key=key)[:2]


def overround(asks: list[float]) -> float:
    return sum(asks)


def census(out: str) -> None:
    from . import api
    ev = defaultdict(lambda: dict(n=0, close=None, vol=[]))
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None
        while True:
            q = dict(series_ticker="KXNFLFIRSTTD", limit=1000, **extra)
            if cursor:
                q["cursor"] = cursor
            d = None
            for a in range(6):
                try:
                    d = api._get(path, q)
                    break
                except Exception:
                    time.sleep(2 ** a)
            time.sleep(0.8)
            if not d:
                break
            for m in d.get("markets", []):
                ct = m.get("close_time") or ""
                ex = m.get("expected_expiration_time") or ct
                if ct >= CUT or ex >= CUT:
                    continue
                e = ev[m["event_ticker"]]
                e["n"] += 1
                e["close"] = ct
                e.setdefault("tk", set()).add(m["ticker"])
                e["vol"].append(float(m.get("volume") or m.get("volume_fp") or 0))
            cursor = d.get("cursor")
            if not cursor:
                break
    res = {k: dict(n=len(v["tk"]), close=v["close"], vol=sum(v["vol"])) for k, v in ev.items()}
    json.dump(res, open(out, "w"), indent=1, sort_keys=True)
    games = sorted(res, key=lambda k: res[k]["close"])
    fit, test = split_thirds(games)
    print("events", len(res), "markets", sum(v["n"] for v in res.values()), "test games", len(test))


if __name__ == "__main__":
    if sys.argv[1] == "census":
        census(sys.argv[2])
