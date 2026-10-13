"""SP1 (README, Pre-registration: SP1): heavy favourites in the sports game-winner markets. Rules fixed in the README before any sports market was downloaded for this test.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/sports.sqlite`). Usage: python -m scalper.sp1 fetch   then   python -m scalper.sp1 run
"""
from __future__ import annotations

import random
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api, backfill
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS, fee

SPORTS_DB = DATA_DIR / "sports.sqlite"
SERIES = ("KXNFLGAME", "KXMLBGAME", "KXWNBAGAME", "KXATPMATCH", "KXUFCFIGHT", "KXNBAGAME", "KXWTAMATCH", "KXNCAAFGAME", "KXNHLGAME", "KXATPCHALLENGERMATCH", "KXVALORANTGAME",
          "KXWTACHALLENGERMATCH")
DAYS = 40
ENTRY_BEFORE_S = 12 * 3600
FETCH_FROM_S = 14 * 3600        # candles from 14 h ...
FETCH_TO_S = 10 * 3600          # ... to 10 h before the expected expiration
BAND = (0.88, 0.97)
CHUNK = 100
MAX_SPAN_S = 48 * 3600
MIN_ENTRIES = 300
MIN_DAYS = 10
Z_BAR = 2.1
PLACEBO_REPS = 200
MDE_FLAG = 0.010


def entry_candle_end(expected_ts: int) -> int:
    """The latest hourly candle end at or before 12 hours before the expected expiration."""
    return ((expected_ts - ENTRY_BEFORE_S) // 3600) * 3600


def chunk_markets(markets: list[dict]) -> list[list[dict]]:
    """Consecutive markets by expected expiration, at most CHUNK of them and a span of at most MAX_SPAN_S, so one candles request stays inside the endpoint's limit."""
    out: list[list[dict]] = []
    cur: list[dict] = []
    for m in sorted(markets, key=lambda x: x["exp_ts"]):
        if cur and (len(cur) >= CHUNK or m["exp_ts"] - cur[0]["exp_ts"] > MAX_SPAN_S):
            out.append(cur)
            cur = []
        cur.append(m)
    if cur:
        out.append(cur)
    return out


def take_entry(bid: float | None, ask: float | None, result: str):
    """(price, net, stress) if the YES ask is in BAND with a valid quote, else None."""
    if bid is None or ask is None or bid < 0.01 or ask > 0.99 or ask < bid:
        return None
    if not (BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9):
        return None
    won = 1.0 if result == "yes" else 0.0
    return ask, won - ask - fee(ask), won - ask - fee(ask, STRESS)


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(SPORTS_DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, exp_ts INTEGER, close_ts INTEGER, result TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid_c REAL, ask_c REAL, volume REAL, PRIMARY KEY(ticker, end_ts));""")
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    now = int(time.time())
    for series in SERIES:
        listed = []
        for m in api.settled_markets(series, now - DAYS * 86400, now):
            exp = backfill.iso_ts(m.get("expected_expiration_time"))
            if m.get("result") in ("yes", "no") and exp is not None and m["ticker"] not in have:
                listed.append({"ticker": m["ticker"], "exp_ts": exp, "close_ts": backfill.iso_ts(m.get("close_time")) or exp, "result": m["result"]})
        stored = 0
        for chunk in chunk_markets(listed):
            lo = min(m["exp_ts"] for m in chunk) - FETCH_FROM_S
            hi = max(m["exp_ts"] for m in chunk) - FETCH_TO_S
            got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": lo, "end_ts": hi, "period_interval": 60})
            by_t = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
            for m in chunk:
                rows = [r for r in (backfill.parse_candle(c, m["ticker"], series) for c in by_t.get(m["ticker"], [])) if r]
                rows = [r for r in rows if m["exp_ts"] - FETCH_FROM_S <= r[2] <= m["exp_ts"] - FETCH_TO_S]
                db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?)", [(r[0], r[2], r[6], r[10], r[12]) for r in rows])
                db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?)", (m["ticker"], series, m["exp_ts"], m["close_ts"], m["result"]))
                stored += 1
            db.commit()
            time.sleep(0.4)
        print(f"{series}: {stored} markets stored", flush=True)
    print("done", flush=True)


def simulate(markets: list[dict], candles: dict) -> list[dict]:
    """One entry per qualifying market. `candles` is {ticker: {end_ts: (bid, ask, volume)}}."""
    out = []
    for m in markets:
        c = candles.get(m["ticker"], {}).get(entry_candle_end(m["exp_ts"]))
        if c is None:
            continue
        te = take_entry(c[0], c[1], m["result"])
        if te is None:
            continue
        price, net, stress = te
        out.append({"ticker": m["ticker"], "series": m["series"], "close_ts": m["close_ts"], "day": datetime.fromtimestamp(m["close_ts"], timezone.utc).strftime("%Y-%m-%d"),
                    "price": price, "net": net, "stress": stress, "mid": (c[0] + c[1]) / 2.0, "won": 1.0 if m["result"] == "yes" else 0.0})
    return sorted(out, key=lambda e: e["close_ts"])


def placebo_means(entries: list[dict], reps: int = PLACEBO_REPS, seed: int = 17) -> list[float]:
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        tot = 0.0
        for e in entries:
            tot += (1.0 if rng.random() < e["mid"] else 0.0) - e["price"] - fee(e["price"])
        out.append(tot / len(entries))
    return out


def verdict(entries: list[dict], placebo: list[float]) -> tuple[str, dict]:
    n = len(entries)
    days = sorted({e["day"] for e in entries})
    if n < MIN_ENTRIES or len(days) < MIN_DAYS:
        return "NOT_ENOUGH_DATA", {"n": n, "days": len(days)}
    mean, se, z = cluster_mean_z([(e["day"], e["net"]) for e in entries])
    half = days[len(days) // 2]
    h1 = [e["net"] for e in entries if e["day"] < half]
    h2 = [e["net"] for e in entries if e["day"] >= half]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in entries) / n
    p95 = sorted(placebo)[int(0.95 * (len(placebo) - 1))] if placebo else float("inf")
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0 and mean > p95
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "days": len(days), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress, "p95": p95, "mde": Z_BAR * se}


def run() -> None:
    db = sqlite3.connect(SPORTS_DB)
    markets = [{"ticker": t, "series": s, "exp_ts": e, "close_ts": c, "result": r} for t, s, e, c, r in db.execute("SELECT ticker, series, exp_ts, close_ts, result FROM market")]
    candles: dict = defaultdict(dict)
    for t, end, bc, ac, v in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle"):
        candles[t][end] = (bc, ac, v)
    entries = simulate(markets, candles)
    print(f"{len(markets)} markets loaded; {len(entries)} entries on {len({e['day'] for e in entries})} days. Signal counts first.\n")
    pl = placebo_means(entries) if entries else []
    v, s = verdict(entries, pl)
    f = lambda x: f"{x * 100:+.2f}c"
    if "mean" in s:
        loss = sum(1 for e in entries if e["won"] == 0.0) / len(entries)
        paid = st.mean(e["price"] for e in entries)
        print(f"SP1: n={s['n']} on {s['days']} days, mean price paid {paid:.3f}, loss rate {loss:.2%}, net {f(s['mean'])} per contract, z {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, "
              f"fees x{STRESS} {f(s['stress'])}, placebo 95th percentile {f(s['p95'])} -> {v}")
        note = "  (FALSIFIED here means NOT SHOWN at this sample size: the minimum detectable edge is above 1c)" if v == "FALSIFIED" and s["mde"] > MDE_FLAG else ""
        print(f"    minimum detectable edge {f(s['mde'])}{note}")
    else:
        print(f"SP1: n={s['n']} on {s['days']} days -> {v}")
    print("\nPer series (information):")
    for series in SERIES:
        mine = [e for e in entries if e["series"] == series]
        if not mine:
            print(f"  {series:<24} no entries")
            continue
        paid = st.mean(e["price"] for e in mine)
        loss = sum(1 for e in mine if e["won"] == 0.0) / len(mine)
        print(f"  {series:<24} n={len(mine):>4} price {paid:.3f} loss rate {loss:5.1%} net {f(st.mean(e['net'] for e in mine))}")
    print("\nBy price decile within the band (information):")
    if entries:
        ps = sorted(e["price"] for e in entries)
        cuts = [ps[int(i * (len(ps) - 1) / 5)] for i in range(6)]
        for i in range(5):
            grp = [e for e in entries if cuts[i] <= e["price"] <= cuts[i + 1]]
            if grp:
                print(f"  price {cuts[i]:.3f} to {cuts[i + 1]:.3f}: n={len(grp):>4} net {f(st.mean(e['net'] for e in grp))} loss rate {sum(1 for e in grp if e['won'] == 0.0) / len(grp):.1%}")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
