"""INX1 (kalshi-scalper/workers/INX1_REGISTRATION.md): Kalshi's S&P 500 and Nasdaq 100 4 pm "above K" markets against a fair
value from the index level and its implied volatility. Research only: nothing here places an order.

Usage: python -m scalper.inx1 yahoo          (download Yahoo 5 minute bars into data/inx1_yahoo/)
       python -m scalper.inx1 fetch          (Kalshi settled 4 pm markets and their candles into data/inx1.sqlite; resumable)
       python -m scalper.inx1 run            (windows A and B only)
       python -m scalper.inx1 holdout        (window C, once, after the A and B verdicts are written)
"""
from __future__ import annotations

import json
import math
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from . import api, backfill
from .calibration import cluster_mean_z
from .fees import taker_fee

DATA = Path("data")
YDIR = DATA / "inx1_yahoo"
DB = DATA / "inx1.sqlite"
SERIES = {"KXINXU": ("%5EGSPC", "%5EVIX"), "KXNASDAQ100U": ("%5ENDX", "%5EVXN")}
START_TS = 1787529600          # 2026-08-24 00:00 UTC
END_TS = 1793232000            # 2026-10-29 00:00 UTC (events closing through Oct 28)
LOOKS = (60, 30, 10)
EDGE = 0.05
PER_EVENT = 2
SCREEN = 0.04
UNIV_LEAD = 75 * 60
UNIV_STALE = 15 * 60
BAR_STALE = 15 * 60
CANDLE_LO, CANDLE_HI = 90 * 60, 8 * 60
STRESS = 1.2


# ---------------------------------------------------------------- data
def yahoo() -> None:
    YDIR.mkdir(parents=True, exist_ok=True)
    for sym in {s for pair in SERIES.values() for s in pair}:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=5m&range=60d"
        out = YDIR / f"{sym.replace('%5E', '')}_5m.json"
        subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url, "-o", str(out)], check=True)
        print(sym, out.stat().st_size, flush=True)
        time.sleep(1)


def bars(sym: str) -> dict[int, float]:
    d = json.load(open(YDIR / f"{sym.replace('%5E', '')}_5m.json"))["chart"]["result"][0]
    closes = d["indicators"]["quote"][0]["close"]
    return {int(t): c for t, c in zip(d["timestamp"], closes) if c is not None}


def level_at(b: dict[int, float], D: int) -> float | None:
    """Close of the 5 minute bar starting at D - 300 (its close is the level at D); else the last bar that started within 15 minutes before."""
    for start in range(D - 300, D - 300 - BAR_STALE - 1, -60):
        if start in b:
            return b[start]
    return None


def four_pm_markets(series: str) -> list[dict]:
    """Settled markets of the series' 4 pm events in the date range, found through the event list (listing every hourly market is slow)."""
    evs, cursor = [], None
    while True:
        p = {"series_ticker": series, "status": "settled", "limit": 200}
        if cursor:
            p["cursor"] = cursor
        d = api._get("/events", p)
        evs += [e["event_ticker"] for e in d.get("events", []) if e["event_ticker"].endswith("H1600")]
        cursor = d.get("cursor")
        if not cursor or not d.get("events"):
            break
        time.sleep(0.6)
    out = []
    for e in sorted(set(evs)):
        d = api._get("/markets", {"event_ticker": e, "limit": 1000})
        out += [m for m in d.get("markets", []) if START_TS <= (backfill.iso_ts(m.get("close_time")) or 0) < END_TS]
        time.sleep(0.6)
    return out


def fetch() -> None:
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    have = {r[0] for r in db.execute("SELECT ticker FROM market")}
    for series, (isym, _) in SERIES.items():
        ib = bars(isym)
        listed = four_pm_markets(series)
        by = defaultdict(list)
        for m in listed:
            c = backfill.iso_ts(m.get("close_time"))
            if c and m.get("result") in ("yes", "no") and m.get("strike_type") == "greater_or_equal":
                by[c].append(m)
        print(series, len(listed), "4 pm markets,", len(by), "events", flush=True)
        for c in sorted(by):
            s0 = level_at(ib, c - UNIV_LEAD)
            if s0 is None:
                print("  no index level for", c, flush=True)
                continue
            ms = [m for m in by[c] if abs(float(m["floor_strike"]) / s0 - 1) <= SCREEN and m["ticker"] not in have]
            for i in range(0, len(ms), 100):
                chunk = ms[i:i + 100]
                got = api.batch_candlesticks([m["ticker"] for m in chunk], c - CANDLE_LO, c - CANDLE_HI)
                for m in chunk:
                    t = m["ticker"]
                    rows = [r for r in (backfill.parse_candle(x, t, series) for x in got.get(t, [])) if r]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)",
                               (t, series, backfill.iso_ts(m.get("open_time")), c, m["result"], float(m["floor_strike"]), len(rows)))
                    have.add(t)
                db.commit()
                time.sleep(0.6)
        print(series, "done", flush=True)


# ---------------------------------------------------------------- model
def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def day_of(c: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(c))


def trades():
    """Every order of every variant: dict(var, day, close, ticker, side, price, won, zero_vol, info_price, info_won)."""
    db = sqlite3.connect(DB)
    mk = defaultdict(list)
    for t, s, c, r, k in db.execute("SELECT ticker, series, close_ts, result, strike FROM market"):
        mk[(s, c)].append((t, r, k))
    cd = defaultdict(dict)
    for t, e, b, a, v in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle"):
        cd[t][e] = (b, a, v or 0.0)
    out, stats = [], defaultdict(int)
    for series, (isym, vsym) in SERIES.items():
        ib, vb = bars(isym), bars(vsym)
        for (s, c), ms in sorted(mk.items()):
            if s != series:
                continue
            # universe from quotes at or before close - 75 min
            uni = []
            for t, r, k in ms:
                q = None
                for e in sorted((e for e in cd[t] if c - UNIV_LEAD - UNIV_STALE <= e <= c - UNIV_LEAD), reverse=True):
                    b, a, _ = cd[t][e]
                    if b is not None and a is not None and b > 0 and a < 1:
                        q = (b + a) / 2
                        break
                if q is not None and 0.05 <= q <= 0.95:
                    uni.append((t, r, k))
            stats[(series, "universe")] += len(uni)
            stats[(series, "events")] += 1
            for L in LOOKS:
                D = c - L * 60
                S, V = level_at(ib, D), level_at(vb, D)
                if S is None or V is None or V <= 0:
                    stats[(series, L, "no bar")] += 1
                    continue
                sig = V / 100 * math.sqrt((L / 390) / 252)
                for fill_end, tag in ((D + 60, "main"), (D, "info")):
                    cands = []
                    for t, r, k in uni:
                        q = cd[t].get(fill_end)
                        if not q or q[0] is None or q[1] is None or not (q[0] > 0 and q[1] < 1):
                            continue
                        b, a, vol = q
                        p = phi(math.log(S / k) / sig)
                        if p - a >= EDGE:
                            cands.append((p - a, t, "yes", a, r == "yes", vol == 0))
                        elif b - p >= EDGE:
                            cands.append((b - p, t, "no", round(1 - b, 4), r == "no", vol == 0))
                    for edge, t, side, price, won, zv in sorted(cands, reverse=True)[:PER_EVENT]:
                        out.append(dict(var=f"{series}-{L}", tag=tag, day=day_of(c), close=c, ticker=t, side=side,
                                        price=price, won=won, zv=zv, edge=edge))
    return out, stats


def pnl(tr, C: int, mult: float = 1.0) -> float:
    fee = taker_fee(tr["price"], C, mult)
    return (C * (1 - tr["price"]) if tr["won"] else -C * tr["price"]) - fee


def score(rows, C=1, mult=1.0):
    nets = [pnl(r, C, mult) for r in rows]
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    pf = (w / l) if l > 0 else (float("inf") if w > 0 else 0.0)
    return dict(n=len(rows), days=len({r["day"] for r in rows}), mk=len({r["ticker"] for r in rows}), net=sum(nets), pf=pf,
                loss=sum(1 for r in rows if not r["won"]) / len(rows) if rows else 0.0)


def windows(all_rows):
    days = sorted({day_of(c) for c in json.load(open(DATA / "inx1_spx_days.json"))})
    n = len(days)
    a, b = days[n // 3 - 1] if n >= 3 else None, days[2 * n // 3 - 1] if n >= 3 else None
    return days, (lambda d: "A" if d <= a else ("B" if d <= b else "C"))


def report(which: set[str]) -> None:
    rows, stats = trades()
    db = sqlite3.connect(DB)
    spx_closes = sorted({c for (c,) in db.execute("SELECT DISTINCT close_ts FROM market WHERE series='KXINXU'")})
    json.dump(spx_closes, open(DATA / "inx1_spx_days.json", "w"))
    days, win = windows(rows)
    print(f"S&P 4 pm days {len(days)}: {days[0]} to {days[-1]}; window cut A <= {days[len(days)//3-1]}, B <= {days[2*len(days)//3-1]}")
    for k, v in sorted(stats.items(), key=str):
        print("  stat", k, v)
    zbar = 5.17
    for var in sorted({r["var"] for r in rows}):
        for tag in ("main", "info"):
            rs = [r for r in rows if r["var"] == var and r["tag"] == tag]
            line = []
            for w in ("A", "B", "C"):
                if w not in which:
                    continue
                ws = [r for r in rs if win(r["day"]) == w]
                s1, s10, sx = score(ws, 1), score(ws, 10), score(ws, 1, STRESS)
                nz = score([r for r in ws if not r["zv"]], 1)
                zv = sum(r["zv"] for r in ws)
                line.append(f"{w}: n {s1['n']} days {s1['days']} mk {s1['mk']} PF1 {s1['pf']:.2f} PF10 {s10['pf']:.2f} net1 {s1['net']:+.2f} "
                            f"loss {s1['loss']:.1%} PFx1.2 {sx['pf']:.2f} zerovol {zv} PF1(no zv) {nz['pf']:.2f}")
            print(f"{var} [{tag}]  " + " | ".join(line))
            if tag == "main" and which == {"A", "B", "C"}:
                m, se, z = cluster_mean_z([(r["day"], pnl(r, 1)) for r in rs])
                print(f"   pooled A+B+C: mean {m*100:+.2f}c per order, day-clustered z {z:+.2f} (bar {zbar})")
    sides = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["tag"] == "main" and win(r["day"]) in which:
            fav = r["price"] >= 0.5
            sides[(r["side"], "fav" if fav else "dog")][0] += 1
            sides[(r["side"], "fav" if fav else "dog")][1] += 0 if r["won"] else 1
    print("side x price>=0.5 (orders, losses):", dict(sides))


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "yahoo":
        yahoo()
    elif cmd == "fetch":
        fetch()
    elif cmd == "run":
        report({"A", "B"})
    elif cmd == "holdout":
        report({"A", "B", "C"})


if __name__ == "__main__":
    main()
