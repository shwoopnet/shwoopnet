"""XLADDER1 (workers/XLADDER1_REGISTRATION.md): S&P 500 and Nasdaq 100 daily range brackets (KXINX, KXNASDAQ100) against the 4 pm
"above K" ladder (KXINXU, KXNASDAQ100U) at the same close. Research only; nothing here places an order.

Usage: python3 -I -m scalper.xladder1 fetch     (bracket candles into data/xladder1.sqlite; resumable, 1 thread)
       python3 -I -m scalper.xladder1 run       (discovery and validation only)
"""
from __future__ import annotations

import math
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

from . import api, backfill
from .calibration import cluster_mean_z

DATA = Path("data")
DB = DATA / "xladder1.sqlite"
INX1 = DATA / "inx1.sqlite"
PAIRS = {"KXINX": "KXINXU", "KXNASDAQ100": "KXNASDAQ100U"}
START_TS, END_TS = 1787529600, 1793232000
LOOKS = (3600, 1800, 600)
STALE = 300
FILL_WAIT = 180
C = 10
LOCK_MIN = 0.01
GAP = 0.04
MAX_LADDER_SPREAD = 0.06
TOL = 0.011
CANDLE_LO, CANDLE_HI = 90 * 60, 8 * 60
PER_EVENT = 10
N_DISC, N_VAL = 15, 14


def fee(p: float, c: int = C, mult: float = 1.0) -> float:
    """Total dollar fee of one order of c contracts at price p, rounded up to the cent."""
    if not 0.0 < p < 1.0:
        return 0.0
    return math.ceil(round(0.07 * mult * c * p * (1 - p) * 100, 9)) / 100.0


# ------------------------------------------------------------------ data
def fetch() -> None:
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    db.execute("CREATE TABLE IF NOT EXISTS bracket(ticker TEXT PRIMARY KEY, series TEXT, close_ts INTEGER, kind TEXT, lo REAL, cap REAL)")
    have = {r[0] for r in db.execute("SELECT ticker FROM bracket")}
    for series in PAIRS:
        by = defaultdict(list)
        for m in api.settled_markets(series, START_TS, END_TS):
            c = backfill.iso_ts(m.get("close_time"))
            if c and m.get("result") in ("yes", "no") and "H1600" in m["ticker"]:
                by[c].append(m)
        print(series, len(by), "events", flush=True)
        for c in sorted(by):
            ms = [m for m in by[c] if m["ticker"] not in have]
            for i in range(0, len(ms), 100):
                chunk = ms[i:i + 100]
                for attempt in range(12):
                    try:
                        got = api.batch_candlesticks([m["ticker"] for m in chunk], c - CANDLE_LO, c - CANDLE_HI)
                        break
                    except RuntimeError as err:
                        print("  retry", attempt, str(err)[:60], flush=True)
                        time.sleep(30 + 20 * attempt)
                else:
                    raise RuntimeError("giving up")
                for m in chunk:
                    t = m["ticker"]
                    rows = [r for r in (backfill.parse_candle(x, t, series) for x in got.get(t, [])) if r]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)",
                               (t, series, backfill.iso_ts(m.get("open_time")), c, m["result"], m.get("floor_strike") or m.get("cap_strike") or 0.0, len(rows)))
                    db.execute("INSERT OR REPLACE INTO bracket VALUES(?,?,?,?,?,?)",
                               (t, series, c, m.get("strike_type"), m.get("floor_strike"), m.get("cap_strike")))
                db.commit()
                time.sleep(2.0)
    print("fetch done", flush=True)


def quote_at(candles: list[tuple], t: int):
    """(bid, ask, volume) of the latest candle ending in (t - STALE, t] with both sides valid, else None."""
    best = None
    for end, b, a, v in candles:
        if t - STALE < end <= t and b is not None and a is not None and 0 <= b < a <= 1:
            if best is None or end > best[0]:
                best = (end, b, a, v or 0.0)
    return None if best is None else best[1:]


def fill_at(candles: list[tuple], t: int):
    """First valid candle ending in (t, t + FILL_WAIT]."""
    for end, b, a, v in sorted(candles):
        if t < end <= t + FILL_WAIT and b is not None and a is not None and 0 <= b < a <= 1:
            return b, a, v or 0.0
    return None


def pnl_legs(legs: list[tuple[float, bool]], payoff: float, c: int = C, mult: float = 1.0) -> float:
    """legs = (price paid per contract, True) ... ; returns dollars of payoff minus cost minus fees for c contracts."""
    cost = sum(p * c for p, _ in legs)
    return payoff * c - cost - sum(fee(p, c, mult) for p, _ in legs)


def lock_plus(bB, aB, bLo, aLo, bCap, aCap, c=C):
    """(+) YES B, YES above(cap), NO above(lo): pays 1 per contract. Returns per contract net at the quoted prices."""
    legs = [(aB, True), (aCap, True), (1 - bLo, True)]
    return pnl_legs(legs, 1.0, c) / c


def lock_minus(bB, aB, bLo, aLo, bCap, aCap, c=C):
    """(-) NO B, YES above(lo), NO above(cap): pays 2 per contract."""
    legs = [(1 - bB, True), (aLo, True), (1 - bCap, True)]
    return pnl_legs(legs, 2.0, c) / c


def load():
    """events[(series, close)] -> dict with brackets (lo,cap,kind,ticker,result), ladder strike -> (ticker,result), candle dict."""
    d = sqlite3.connect(DB)
    u = sqlite3.connect(INX1)
    cand = defaultdict(list)
    for tk, end, b, a, v in d.execute("SELECT ticker,end_ts,bid_c,ask_c,volume FROM candle"):
        cand[tk].append((end, b, a, v))
    for tk, end, b, a, v in u.execute("SELECT ticker,end_ts,bid_c,ask_c,volume FROM candle"):
        cand[tk].append((end, b, a, v))
    res = {}
    ev = defaultdict(lambda: {"br": [], "lad": {}})
    for tk, ser, c, kind, lo, cap in d.execute("SELECT ticker,series,close_ts,kind,lo,cap FROM bracket"):
        r = d.execute("SELECT result FROM market WHERE ticker=?", (tk,)).fetchone()[0]
        ev[(ser, c)]["br"].append((lo, cap, kind, tk, r))
    for ser, up in PAIRS.items():
        for tk, c, r, k in u.execute("SELECT ticker,close_ts,result,strike FROM market WHERE series=?", (up,)):
            if (ser, c) in ev:
                ev[(ser, c)]["lad"][k] = (tk, r)
    return ev, cand


def ladder_near(lad: dict, x: float):
    for k, v in lad.items():
        if abs(k - x) <= TOL:
            return v
    return None


def split_of(series_events: list[int], c: int) -> str:
    s = sorted(series_events)
    i = s.index(c)
    return "disc" if i < N_DISC else ("val" if i < N_DISC + N_VAL else "hold")


def run() -> None:
    ev, cand = load()
    evs = defaultdict(list)
    for (ser, c) in ev:
        evs[ser].append(c)
    stats = defaultdict(list)           # (rule, window) -> list of (day, pnl_per_contract, flags)
    gaps = defaultdict(list)
    counts = defaultdict(int)
    for (ser, c), e in sorted(ev.items()):
        win = split_of(evs[ser], c)
        if win == "hold":
            continue
        day = time.strftime("%Y-%m-%d", time.gmtime(c))
        done_lock, done_cheap = set(), []
        for L in LOOKS:
            t = c - L
            cheap_here = []
            for lo, cap, kind, tk, r in e["br"]:
                if kind == "between":
                    lo_l = ladder_near(e["lad"], lo)
                    cap_l = ladder_near(e["lad"], cap + 0.0001)
                    pairs = [(lo_l, cap_l)] if lo_l and cap_l else []
                elif kind == "greater":
                    pairs = []
                else:
                    pairs = []
                for lo_l, cap_l in pairs:
                    counts[(ser, win, "usable_look")] += 1
                    qB, qLo, qCap = quote_at(cand[tk], t), quote_at(cand[lo_l[0]], t), quote_at(cand[cap_l[0]], t)
                    if not (qB and qLo and qCap):
                        continue
                    counts[(ser, win, "quoted_look")] += 1
                    bB, aB, vB = qB
                    bLo, aLo, _ = qLo
                    bCap, aCap, _ = qCap
                    lp = lock_plus(bB, aB, bLo, aLo, bCap, aCap)
                    lm = lock_minus(bB, aB, bLo, aLo, bCap, aCap)
                    gaps[(ser, win, "lock")].append(max(lp, lm))
                    for name, val in (("+", lp), ("-", lm)):
                        if val >= LOCK_MIN and (tk, name) not in done_lock:
                            done_lock.add((tk, name))
                            fB, fLo, fCap = fill_at(cand[tk], t), fill_at(cand[lo_l[0]], t), fill_at(cand[cap_l[0]], t)
                            if not (fB and fLo and fCap):
                                counts[(ser, win, "lock_miss")] += 1
                                continue
                            fn = lock_plus if name == "+" else lock_minus
                            net = fn(fB[0], fB[1], fLo[0], fLo[1], fCap[0], fCap[1])
                            stats[("LOCK", win)].append((day, net, fB[2] > 0))
                    if (ser, c, tk) in done_cheap or any(x == tk for x in done_cheap):
                        continue
                    if (qLo[1] - qLo[0] > MAX_LADDER_SPREAD) or (qCap[1] - qCap[0] > MAX_LADDER_SPREAD):
                        continue
                    imp = (bLo + aLo) / 2 - (bCap + aCap) / 2
                    gy, gn = imp - aB, bB - imp
                    gaps[(ser, win, "cheap")].append(max(gy, gn))
                    if gy >= GAP and 0.05 <= aB <= 0.95:
                        cheap_here.append((gy, tk, "yes", r))
                    elif gn >= GAP and 0.05 <= 1 - bB <= 0.95:
                        cheap_here.append((gn, tk, "no", r))
            cheap_here.sort(reverse=True)
            for g, tk, side, r in cheap_here[:max(0, PER_EVENT - len(done_cheap))]:
                if tk in done_cheap:
                    continue
                done_cheap.append(tk)
                f = fill_at(cand[tk], t)
                if not f:
                    counts[(ser, win, "cheap_miss")] += 1
                    continue
                price = f[1] if side == "yes" else 1 - f[0]
                if not 0.05 <= price <= 0.95:
                    counts[(ser, win, "cheap_miss")] += 1
                    continue
                won = (r == "yes") == (side == "yes")
                net = (1.0 if won else 0.0) - price - fee(price, 1)
                net10 = ((1.0 if won else 0.0) * C - price * C - fee(price, C)) / C
                stats[("CHEAP", win)].append((day, net10, f[2] > 0, price, won, ser))
    report(stats, gaps, counts)


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf") if g > 0 else 0.0


def report(stats, gaps, counts):
    for k in sorted(counts):
        print("count", k, counts[k])
    for k in sorted(gaps):
        g = sorted(gaps[k])
        if g:
            print("gap", k, "n", len(g), "median %.4f p90 %.4f max %.4f" % (g[len(g) // 2], g[int(len(g) * .9)], g[-1]))
    for (rule, win), rows in sorted(stats.items()):
        xs = [r[1] for r in rows]
        m, se, z = cluster_mean_z([(r[0], r[1]) for r in rows])
        vol = [r[1] for r in rows if r[2]]
        print(rule, win, "n", len(rows), "mean %.4f PF %.2f z %.2f" % (m, pf(xs), z), "volpos n", len(vol), "mean %.4f" % (sum(vol) / len(vol) if vol else 0))
        if rule == "CHEAP" and rows:
            print("   win %.3f vs paid %.3f" % (sum(1 for r in rows if r[4]) / len(rows), sum(r[3] for r in rows) / len(rows)))


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
