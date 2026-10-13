"""FLB1 (README, Pre-registration: FLB1): favourites in long-dated, non-sports, non-price markets. Rules fixed in the README before any such market was downloaded.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

History goes into its OWN database (`data/flb1.sqlite`). Usage: python -m scalper.flb1 fetch   then   python -m scalper.flb1 run
"""
from __future__ import annotations

import random
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict

from . import api, backfill
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DATA_DIR
from .scalps import STRESS, fee

FLB_DB = DATA_DIR / "flb1.sqlite"
EXCLUDED_CATEGORIES = ("Sports", "Financials", "Crypto")
LEADS_H = (24, 72, 168)
DAYS = 60
MIN_LIFETIME_S = 3 * 86400
BAND = (0.88, 0.97)
CHUNK = 100
MAX_SPAN_S = 48 * 3600
MIN_ENTRIES = 300
MIN_EVENTS = 60
Z_BAR = 2.1
PLACEBO_REPS = 200
AUDIT_MEAN = 0.02
MDE_FLAG = 0.01


def entry_end(close_ts: int, lead_h: int) -> int:
    """The latest hour boundary at or before `lead_h` hours before the close."""
    return ((close_ts - lead_h * 3600) // 3600) * 3600


def eligible(category: str | None, open_ts: int | None, close_ts: int | None, result: str | None) -> bool:
    """Selected on category, lifetime and having a result only: never on price."""
    if category in EXCLUDED_CATEGORIES or result not in ("yes", "no") or open_ts is None or close_ts is None:
        return False
    return close_ts - open_ts >= MIN_LIFETIME_S


def chunk_markets(markets: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    cur: list[dict] = []
    for m in sorted(markets, key=lambda x: x["close_ts"]):
        if cur and (len(cur) >= CHUNK or m["close_ts"] - cur[0]["close_ts"] > MAX_SPAN_S):
            out.append(cur)
            cur = []
        cur.append(m)
    if cur:
        out.append(cur)
    return out


def take_entry(bid: float | None, ask: float | None, result: str):
    """(side, price, mid_of_side, net, stress) if one side's ask is in BAND on a valid quote, else None. YES at its ask, NO at 1 minus the YES bid."""
    if not valid_quote(bid, ask):
        return None
    if BAND[0] - 1e-9 <= ask <= BAND[1] + 1e-9:
        side, price, mid = "yes", ask, (bid + ask) / 2.0
    else:
        no = round(1.0 - bid, 4)
        if not (BAND[0] - 1e-9 <= no <= BAND[1] + 1e-9):
            return None
        side, price, mid = "no", no, 1.0 - (bid + ask) / 2.0
    won = 1.0 if (result == "yes") == (side == "yes") else 0.0
    return side, price, mid, won - price - fee(price), won - price - fee(price, STRESS)


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db = sqlite3.connect(FLB_DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, event TEXT, category TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, lead_h INTEGER, end_ts INTEGER, bid_c REAL, ask_c REAL, volume REAL, PRIMARY KEY(ticker, lead_h));
CREATE TABLE IF NOT EXISTS done(ticker TEXT, lead_h INTEGER, PRIMARY KEY(ticker, lead_h));""")
    now = int(time.time())
    cur, pages, kept = None, 0, 0
    while True:
        params = {"status": "settled", "with_nested_markets": "true", "limit": 200, "min_close_ts": now - DAYS * 86400}
        if cur:
            params["cursor"] = cur
        d = api._get("/events", params)
        for e in d.get("events", []):
            for m in e.get("markets", []):
                o, c = backfill.iso_ts(m.get("open_time")), backfill.iso_ts(m.get("close_time"))
                if c is not None and c < now - DAYS * 86400:
                    continue
                if eligible(e.get("category"), o, c, m.get("result")):
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?)", (m["ticker"], e["event_ticker"], e.get("category"), o, c, m["result"]))
                    kept += 1
        db.commit()
        pages += 1
        if pages % 10 == 0:
            print(f"  {pages} event pages, {kept} eligible markets", flush=True)
        cur = d.get("cursor")
        if not cur:
            break
    print(f"{pages} event pages, {kept} eligible markets listed", flush=True)
    markets = [{"ticker": t, "close_ts": c} for t, c in db.execute("SELECT ticker, close_ts FROM market")]
    for lead in LEADS_H:
        done = {r[0] for r in db.execute("SELECT ticker FROM done WHERE lead_h=?", (lead,))}
        todo = [m for m in markets if m["ticker"] not in done]
        stored = 0
        for chunk in chunk_markets(todo):
            ends = {m["ticker"]: entry_end(m["close_ts"], lead) for m in chunk}
            got = api._get("/markets/candlesticks", {"market_tickers": ",".join(ends), "start_ts": min(ends.values()) - 3600, "end_ts": max(ends.values()), "period_interval": 60})
            by_t = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
            for t, end in ends.items():
                for r in (backfill.parse_candle(c, t, "FLB") for c in by_t.get(t, [])):
                    if r and r[2] == end:
                        db.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?)", (t, lead, end, r[6], r[10], r[12]))
                        stored += 1
                db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (t, lead))
            db.commit()
            time.sleep(0.3)
        print(f"lead {lead} h: {stored} entry candles stored", flush=True)
    print("done", flush=True)


def simulate(markets: list[dict], candles: dict, lead_h: int) -> list[dict]:
    """One entry per market. `candles` is {(ticker, lead_h): (end_ts, bid, ask, volume)}."""
    out = []
    for m in markets:
        c = candles.get((m["ticker"], lead_h))
        if c is None or c[0] != entry_end(m["close_ts"], lead_h):
            continue
        te = take_entry(c[1], c[2], m["result"])
        if te is None:
            continue
        side, price, mid, net, stress = te
        out.append({"ticker": m["ticker"], "event": m["event"], "category": m["category"], "close_ts": m["close_ts"], "side": side, "price": price, "mid": mid, "net": net, "stress": stress,
                    "won": 1.0 if net + price + fee(price) > 0.5 else 0.0, "volume": c[3]})
    return sorted(out, key=lambda e: e["close_ts"])


def placebo_means(entries: list[dict], reps: int = PLACEBO_REPS, seed: int = 29) -> list[float]:
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
    events = {e["event"] for e in entries}
    if n < MIN_ENTRIES or len(events) < MIN_EVENTS:
        return "NOT_ENOUGH_DATA", {"n": n, "events": len(events)}
    es = sorted(entries, key=lambda e: e["close_ts"])
    mean, se, z = cluster_mean_z([(e["event"], e["net"]) for e in es])
    half = es[n // 2]["close_ts"]
    h1 = [e["net"] for e in es if e["close_ts"] < half]
    h2 = [e["net"] for e in es if e["close_ts"] >= half]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    stress = sum(e["stress"] for e in es) / n
    p95 = sorted(placebo)[int(0.95 * (len(placebo) - 1))] if placebo else float("inf")
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0 and mean > p95
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "events": len(events), "mean": mean, "z": z, "h1": m1, "h2": m2, "stress": stress, "p95": p95, "mde": Z_BAR * se,
                                                           "audit": mean > AUDIT_MEAN}


def run() -> None:
    db = sqlite3.connect(FLB_DB)
    markets = [{"ticker": t, "event": e, "category": c, "close_ts": cl, "result": r} for t, e, c, cl, r in db.execute("SELECT ticker, event, category, close_ts, result FROM market")]
    candles = {(t, lead): (end, bc, ac, v) for t, lead, end, bc, ac, v in db.execute("SELECT ticker, lead_h, end_ts, bid_c, ask_c, volume FROM candle")}
    print(f"{len(markets)} eligible markets in {len({m['event'] for m in markets})} events. Signal counts first.\n")
    f = lambda x: f"{x * 100:+.2f}c"
    for lead in LEADS_H:
        es = simulate(markets, candles, lead)
        print(f"lead {lead} h: {len(es)} entries in {len({e['event'] for e in es})} events")
        v, s = verdict(es, placebo_means(es) if es else [])
        if "mean" in s:
            loss = sum(1 for e in es if e["won"] == 0.0) / len(es)
            paid = st.mean(e["price"] for e in es)
            note = "  (FALSIFIED here means NOT SHOWN at this sample size: the minimum detectable edge is above 1c)" if v == "FALSIFIED" and s["mde"] > MDE_FLAG else ""
            print(f"    mean price paid {paid:.3f}, loss rate {loss:.1%}, net {f(s['mean'])} per contract, z (by event) {s['z']:+.2f}, halves {f(s['h1'])} / {f(s['h2'])}, fees x{STRESS} {f(s['stress'])}, "
                  f"placebo 95th percentile {f(s['p95'])}, minimum detectable edge {f(s['mde'])}{note}" + ("  AUDIT TRIGGER: mean above +2c" if s["audit"] else ""))
        print(f"    -> {v}")
        if es:
            by = defaultdict(list)
            for e in es:
                by[e["category"]].append(e["net"])
            print("    per category (information): " + ", ".join(f"{k} n={len(v)} {f(st.mean(v))}" for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))))
            print(f"    median entry-candle volume {st.median(e['volume'] or 0.0 for e in es):,.0f}")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
