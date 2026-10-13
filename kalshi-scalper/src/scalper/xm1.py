"""XM1 (README, Pre-registration: XM1): does the hourly ladder price the 15 minute market better than the 15 minute market does. Rules fixed in the README before any ladder strike was
downloaded for this test. Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/xm1.sqlite`). Usage: python -m scalper.xm1 fetch   then   python -m scalper.xm1 run
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time
from datetime import datetime, timezone

from . import api, backfill
from .analyze import valid_quote
from .paths import DATA_DIR, DB
from .scalps import STRESS, fee
from . import wx1

XM_DB = DATA_DIR / "xm1.sqlite"
PAIRS = {"KXBTC15M": "KXBTCD", "KXETH15M": "KXETHD"}          # 15 minute series -> its hourly ladder: the registered two
ENTRY_LEFT_S = 360
NEAR = 0.015                  # keep ladder strikes within 1.5% of the 15 minute strike
EDGE = 0.02
BAND = (0.03, 0.97)
MDE_FLAG = 0.02


def near_strikes(strikes: list[float], k15: float, frac: float = NEAR) -> list[float]:
    """The ladder strikes within `frac` of the 15 minute strike: chosen from the strike alone, never from an outcome."""
    return [s for s in strikes if abs(s - k15) <= frac * k15]


def interpolate(quotes: dict[float, tuple[float, float]], k: float) -> float | None:
    """Mid of the ladder's YES (above) quote at strike k, linear between the two strikes that bracket it. Both must have a valid quote; no bracket gives None."""
    below = [s for s in quotes if s <= k]
    above = [s for s in quotes if s >= k]
    if not below or not above:
        return None
    s1, s2 = max(below), min(above)
    for s in (s1, s2):
        bid, ask = quotes[s]
        if not valid_quote(bid, ask):
            return None
    p1 = sum(quotes[s1]) / 2.0
    p2 = sum(quotes[s2]) / 2.0
    if s2 == s1:
        return p1
    return p1 + (p2 - p1) * (k - s1) / (s2 - s1)


def xm_trade(p: float, bid: float, ask: float):
    """The side with the larger edge after the fee if it is at least EDGE and inside BAND, else None. Returns (side, price, edge)."""
    no_ask = round(1.0 - bid, 4)
    e_yes = p - ask - fee(ask)
    e_no = (1.0 - p) - no_ask - fee(no_ask)
    side, price, e = ("yes", ask, e_yes) if e_yes >= e_no else ("no", no_ask, e_no)
    if e >= EDGE - 1e-12 and BAND[0] - 1e-9 <= price <= BAND[1] + 1e-9:
        return side, price, e
    return None


def hourly_windows() -> list[dict]:
    """The hourly-aligned 15 minute markets of the registered series that have a result, a strike and a usable quote at the entry candle."""
    db = sqlite3.connect(DB)
    ms = {t: {"series": s, "close_ts": c, "result": r, "k": k} for t, s, c, r, k in db.execute(
        "SELECT ticker, series, close_ts, result, strike FROM market WHERE series IN ('KXBTC15M','KXETH15M') AND result IN ('yes','no') AND strike IS NOT NULL")}
    out = []
    for t, m in ms.items():
        if m["close_ts"] % 3600:
            continue
        row = db.execute("SELECT bid_c, ask_c FROM candle WHERE ticker=? AND end_ts=?", (t, m["close_ts"] - ENTRY_LEFT_S)).fetchone()
        if row and valid_quote(row[0], row[1]):
            out.append(dict(m, ticker=t, bid=row[0], ask=row[1]))
    return sorted(out, key=lambda m: m["close_ts"])


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    x = sqlite3.connect(XM_DB)
    x.executescript("""CREATE TABLE IF NOT EXISTS window(ticker TEXT PRIMARY KEY, close_ts INTEGER, n INTEGER);
CREATE TABLE IF NOT EXISTS ladder(window TEXT, ticker TEXT, strike REAL, bid REAL, ask REAL, PRIMARY KEY(window, ticker));""")
    done = {r[0] for r in x.execute("SELECT ticker FROM window")}
    wins = [w for w in hourly_windows() if w["ticker"] not in done]
    print(f"{len(wins)} hourly-aligned 15 minute windows to fetch", flush=True)
    for i, w in enumerate(wins):
        lad = PAIRS[w["series"]]
        c = w["close_ts"]
        listed = [m for m in api.settled_markets(lad, c - 60, c + 60) if m.get("floor_strike") is not None and m.get("strike_type") == "greater"]
        keep = set(near_strikes([m["floor_strike"] for m in listed], w["k"]))
        pick = [m for m in listed if m["floor_strike"] in keep]
        n = 0
        if pick:
            t = c - ENTRY_LEFT_S
            got = api.batch_candlesticks([m["ticker"] for m in pick], t - 120, t + 60)
            for m in pick:
                cs = [r for r in (backfill.parse_candle(k, m["ticker"], lad) for k in got.get(m["ticker"], [])) if r and r[2] == t]
                if cs:
                    x.execute("INSERT OR REPLACE INTO ladder VALUES(?,?,?,?,?)", (w["ticker"], m["ticker"], m["floor_strike"], cs[0][6], cs[0][10]))
                    n += 1
        x.execute("INSERT OR REPLACE INTO window VALUES(?,?,?)", (w["ticker"], c, n))
        x.commit()
        time.sleep(0.4)
        if i % 100 == 99:
            print(f"  {i + 1} windows", flush=True)
    print("done", flush=True)


def simulate(wins: list[dict], lad: dict[str, dict[float, tuple[float, float]]]) -> tuple[list[dict], list[dict]]:
    """(trades, gap rows). `lad` maps a 15 minute ticker to {strike: (bid, ask)} at the entry candle."""
    trades, gaps = [], []
    for w in wins:
        q = lad.get(w["ticker"])
        if not q:
            continue
        p = interpolate(q, w["k"])
        if p is None:
            continue
        mid = (w["bid"] + w["ask"]) / 2.0
        yes = w["result"] == "yes"
        gaps.append({"series": w["series"], "gap": p - mid, "ladder": (p - (1.0 if yes else 0.0)) ** 2, "market": (mid - (1.0 if yes else 0.0)) ** 2})
        pk = xm_trade(p, w["bid"], w["ask"])
        if pk is None:
            continue
        side, price, e = pk
        won = yes if side == "yes" else (not yes)
        trades.append({"series": w["series"], "close_ts": w["close_ts"], "day": datetime.fromtimestamp(w["close_ts"], timezone.utc).strftime("%Y-%m-%d"), "side": side, "price": price,
                       "net": (1.0 if won else 0.0) - price - fee(price), "stress": (1.0 if won else 0.0) - price - fee(price, STRESS), "mid": mid if side == "yes" else 1.0 - mid})
    return sorted(trades, key=lambda t: t["close_ts"]), gaps


def run() -> None:
    wins = hourly_windows()
    x = sqlite3.connect(XM_DB)
    lad: dict = {}
    for wt, strike, bid, ask in x.execute("SELECT window, strike, bid, ask FROM ladder"):
        lad.setdefault(wt, {})[strike] = (bid, ask)
    print(f"{len(wins)} hourly-aligned 15 minute windows, {len(lad)} with ladder quotes. Signal counts first.\n")
    f = lambda v: f"{v * 100:+.2f}c"
    for series in PAIRS:
        ws = [w for w in wins if w["series"] == series]
        trades, gaps = simulate(ws, lad)
        pl = wx1.placebo_means(trades) if trades else []
        v, s = wx1.verdict(trades, pl)
        print(f"{series}: {len(ws)} windows, {len(gaps)} with a bracket, {len(trades)} trades on {len({t['day'] for t in trades})} days")
        if "mean" in s:
            note = "  (FALSIFIED here means NOT SHOWN at this sample size: the minimum detectable edge is above 2c)" if v == "FALSIFIED" and s["mde"] > MDE_FLAG else ""
            print(f"    net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, placebo 95th percentile {f(s['p95'])}, minimum detectable edge {f(s['mde'])}{note}")
        print(f"    -> {v}")
        if gaps:
            g = sorted(x["gap"] for x in gaps)
            q = lambda a: g[min(len(g) - 1, int(a * (len(g) - 1)))]
            print(f"    gap (ladder p minus 15 minute mid): median {f(q(0.5))}, 5th {f(q(0.05))}, 95th {f(q(0.95))}, share above 2c in size {sum(1 for v_ in g if abs(v_) >= 0.02) / len(g):.1%}")
            print(f"    Brier: ladder {st.mean(x['ladder'] for x in gaps):.4f} vs 15 minute mid {st.mean(x['market'] for x in gaps):.4f} (lower is better)")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
