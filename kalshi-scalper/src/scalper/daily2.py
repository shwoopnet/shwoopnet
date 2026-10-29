"""DAILY2 (kalshi-scalper/workers/DAILY2_REGISTRATION.md): Kalshi's WTI, EUR/USD and USD/JPY daily markets against a fair value
from the outside price (Yahoo 5 minute bars, amendment 1) and its own realised volatility. Research only: nothing here places an order.

Usage (from kalshi-scalper/, PYTHONPATH=src; data go to $DAILY2_DIR, the session scratchpad, never into git):
  python -m scalper.daily2 yahoo     Yahoo 5 minute bars (60 days)
  python -m scalper.daily2 fetch     Kalshi settled markets and their 1 minute candles (resumable)
  python -m scalper.daily2 run       windows A and B only
  python -m scalper.daily2 holdout   window C, once, after the A and B verdicts are written
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from . import api, backfill
from .calibration import cluster_mean_z
from .fees import taker_fee

DIR = Path(os.environ.get("DAILY2_DIR", "data/daily2"))
DB = DIR / "daily2.sqlite"
START_TS = 1788134400          # 2026-08-31 00:00 UTC
END_TS = 1793232000            # 2026-10-29 00:00 UTC
SERIES = ("KXWTI", "KXEURUSD", "KXUSDJPY")
YSYM = {"CL=F": "CL%3DF", "CLZ26.NYM": "CLZ26.NYM", "EURUSD=X": "EURUSD%3DX", "JPY=X": "JPY%3DX"}
VARIANTS = {"KXWTI": (60, 30, 10), "KXEURUSD": (60, 30, 10), "KXUSDJPY": (60, 30)}
EDGE = 0.05
PER_EVENT = 2
UNIV_LEAD, UNIV_STALE = 75 * 60, 15 * 60
LAG, REF_STALE = 60, 15 * 60
BAR = 300                       # 5 minute bars (amendment 1)
NBARS, MIN_RET, GAP = 121, 60, 12 * 60
CANDLE_LO, CANDLE_HI = 92 * 60, 8 * 60
STRESS = 1.2
# CME last trading days (crude: 3 business days before the 25th of the prior month, 4 if the 25th is not a business day)
LTD_OCT26 = 1790035200 + 86399   # 2026-09-22 end of day UTC
LTD_NOV26 = 1792454400 + 86399   # 2026-10-20 end of day UTC
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september",
                                       "october", "november", "december"], 1)}


# ---------------------------------------------------------------- data
def yahoo() -> None:
    """Yahoo 5 minute bars, one range=60d request per symbol (amendment 1: 2 minute chunks reach back only to mid September)."""
    DIR.mkdir(parents=True, exist_ok=True)
    for sym, q in YSYM.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{q}?interval=5m&range=60d"
        raw = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", url], capture_output=True, check=True).stdout
        r = json.loads(raw)["chart"]["result"][0]
        bars = {str(int(t)): float(c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c is not None}
        json.dump(bars, open(DIR / f"y_{sym}.json", "w"))
        ts = sorted(int(t) for t in bars)
        print(sym, len(ts), time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts[0])), flush=True)
        time.sleep(1.0)


def contract_month(rules: str) -> tuple[int, int] | None:
    m = re.search(r"\((\w+) (\d{4}) contract\)", rules or "")
    if not m or m.group(1).lower() not in MONTHS:
        return None
    return MONTHS[m.group(1).lower()], int(m.group(2))


def fetch() -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    db.execute("CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, series TEXT, close_ts INTEGER, result TEXT, stype TEXT, "
               "floor REAL, cap REAL, cmonth TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS done(close_key TEXT PRIMARY KEY)")
    done = {r[0] for r in db.execute("SELECT close_key FROM done")}
    for s in SERIES:
        ms = list(api.settled_markets(s, START_TS, END_TS))
        by = defaultdict(list)
        for m in ms:
            c = backfill.iso_ts(m.get("close_time"))
            if c and START_TS <= c < END_TS and m.get("result") in ("yes", "no"):
                by[c].append(m)
        print(s, len(ms), "markets,", len(by), "closes", flush=True)
        for c in sorted(by):
            key = f"{s}:{c}"
            if key in done:
                continue
            group = by[c]
            for i in range(0, len(group), 100):
                chunk = group[i:i + 100]
                got = api.batch_candlesticks([m["ticker"] for m in chunk], c - CANDLE_LO, c - CANDLE_HI)
                for m in chunk:
                    t = m["ticker"]
                    rows = [r for r in (backfill.parse_candle(x, t, s) for x in got.get(t, [])) if r]
                    db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                    cm = contract_month(m.get("rules_primary", "")) if s == "KXWTI" else None
                    db.execute("INSERT OR REPLACE INTO mk VALUES(?,?,?,?,?,?,?,?)",
                               (t, s, c, m["result"], m.get("strike_type"), api.f(m.get("floor_strike")), api.f(m.get("cap_strike")),
                                f"{cm[1]}-{cm[0]:02d}" if cm else None))
                time.sleep(0.6)
            db.execute("INSERT OR REPLACE INTO done VALUES(?)", (key,))
            db.commit()
        print(s, "done", flush=True)


# ---------------------------------------------------------------- model
def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def day_of(c: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(c))


def load_bars(sym: str) -> tuple[list[int], list[float]]:
    b = json.load(open(DIR / f"y_{sym}.json"))
    ts = sorted(int(t) for t in b)
    return ts, [b[str(t)] for t in ts]


def ref_symbol(series: str, cmonth: str | None, close: int) -> str | None:
    if series == "KXEURUSD":
        return "EURUSD=X"
    if series == "KXUSDJPY":
        return "JPY=X"
    if cmonth == "2026-12":
        return "CLZ26.NYM"
    if cmonth == "2026-10" and close <= LTD_OCT26:
        return "CL=F"
    if cmonth == "2026-11" and LTD_OCT26 < close <= LTD_NOV26:
        return "CL=F"
    return None


def ref_at(ts: list[int], px: list[float], D: int):
    """(S, s_per_sqrt_bar, bar_end) from the latest bar that ENDED at or before D - LAG, at most REF_STALE before D."""
    import bisect
    i = bisect.bisect_right(ts, D - LAG - BAR) - 1      # bar start + BAR <= D - LAG
    if i < 0 or ts[i] + BAR < D - REF_STALE:
        return None
    lo = max(0, i - NBARS + 1)
    rets = [math.log(px[j] / px[j - 1]) for j in range(lo + 1, i + 1) if ts[j] - ts[j - 1] <= GAP and px[j] > 0 and px[j - 1] > 0]
    if len(rets) < MIN_RET:
        return None
    return px[i], statistics.pstdev(rets), ts[i] + BAR


def model_p(stype: str, S: float, lo: float | None, hi: float | None, s: float) -> float | None:
    if s <= 0:
        return None
    if stype == "greater" and lo:
        return phi(math.log(S / lo) / s)
    if stype == "less" and hi:
        return 1 - phi(math.log(S / hi) / s)
    if stype == "between" and lo and hi:
        return phi(math.log(S / lo) / s) - phi(math.log(S / hi) / s)
    return None


def two_sided(q) -> bool:
    return bool(q) and q[0] is not None and q[1] is not None and q[0] > 0 and q[1] < 1


def trades():
    db = sqlite3.connect(DB)
    mk = defaultdict(list)
    for t, s, c, r, st, lo, hi, cm in db.execute("SELECT ticker, series, close_ts, result, stype, floor, cap, cmonth FROM mk"):
        mk[(s, c)].append((t, r, st, lo, hi, cm))
    cd = defaultdict(dict)
    for t, e, b, a, v in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle"):
        cd[t][e] = (b, a, v or 0.0)
    bars = {sym: load_bars(sym) for sym in YSYM}
    out, stats = [], defaultdict(int)
    for (s, c), ms in sorted(mk.items()):
        cms = {m[5] for m in ms}
        sym = ref_symbol(s, next(iter(cms)) if len(cms) == 1 else None, c)
        stats[(s, "closes")] += 1
        if sym is None:
            stats[(s, "no reference (roll)")] += 1
            continue
        uni = []
        for t, r, st, lo, hi, _ in ms:
            q = None
            for e in sorted((e for e in cd[t] if c - UNIV_LEAD - UNIV_STALE <= e <= c - UNIV_LEAD), reverse=True):
                if two_sided(cd[t][e]):
                    q = (cd[t][e][0] + cd[t][e][1]) / 2
                    break
            if q is not None and 0.05 <= q <= 0.95:
                uni.append((t, r, st, lo, hi))
        stats[(s, "universe strikes")] += len(uni)
        for L in VARIANTS[s]:
            D = c - L * 60
            ref = ref_at(*bars[sym], D)
            if ref is None:
                stats[(s, L, "no ref bar")] += 1
                continue
            S, sig, bend = ref
            sd = sig * math.sqrt((c - bend) / BAR)
            cands = []
            for t, r, st, lo, hi in uni:
                q = cd[t].get(D)
                if not two_sided(q):
                    continue
                p = model_p(st, S, lo, hi, sd)
                if p is None:
                    continue
                b, a, _ = q
                if p - a >= EDGE:
                    cands.append((p - a, t, "yes", r == "yes", p))
                elif b - p >= EDGE:
                    cands.append((b - p, t, "no", r == "no", p))
            stats[(s, L, "signals")] += len(cands)
            for edge, t, side, won, p in sorted(cands, reverse=True)[:PER_EVENT]:
                for tag, end in (("main", D + 60), ("info", D)):
                    q = cd[t].get(end)
                    if not two_sided(q):
                        stats[(s, L, tag, "fill candle missing")] += 1
                        continue
                    price = q[1] if side == "yes" else round(1 - q[0], 4)
                    out.append(dict(var=f"{s}-{L}", tag=tag, day=day_of(c), ticker=t, side=side, price=price, won=won,
                                    zv=q[2] == 0, edge=edge, p=p))
    return out, stats


def pnl(tr, C: int, mult: float = 1.0) -> float:
    fee = taker_fee(tr["price"], C, mult)
    return (C * (1 - tr["price"]) if tr["won"] else -C * tr["price"]) - fee


def score(rows, C=1, mult=1.0):
    nets = [pnl(r, C, mult) for r in rows]
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    pf = (w / l) if l > 0 else (float("inf") if w > 0 else float("nan"))
    return dict(n=len(rows), days=len({r["day"] for r in rows}), mk=len({r["ticker"] for r in rows}), net=sum(nets), pf=pf,
                loss=(sum(1 for r in rows if not r["won"]) / len(rows)) if rows else float("nan"))


def windows():
    db = sqlite3.connect(DB)
    days = sorted({day_of(c) for (c,) in db.execute("SELECT DISTINCT close_ts FROM mk")})
    n = len(days)
    a, b = days[n // 3 - 1], days[2 * n // 3 - 1]
    return days, a, b, (lambda d: "A" if d <= a else ("B" if d <= b else "C"))


def report(which: set[str]) -> None:
    rows, stats = trades()
    days, a, b, win = windows()
    nd = defaultdict(int)
    for d in days:
        nd[win(d)] += 1
    print(f"days {len(days)}: {days[0]} to {days[-1]}; A <= {a} ({nd['A']} days), B <= {b} ({nd['B']}), C ({nd['C']})")
    for k, v in sorted(stats.items(), key=str):
        print("  stat", k, v)
    for var in [f"{s}-{L}" for s in SERIES for L in VARIANTS[s]]:
        for tag in ("main", "info"):
            rs = [r for r in rows if r["var"] == var and r["tag"] == tag]
            line = []
            for w in ("A", "B", "C"):
                if w not in which:
                    continue
                ws = [r for r in rs if win(r["day"]) == w]
                s1, s10, sx = score(ws, 1), score(ws, 10), score(ws, 1, STRESS)
                nz = score([r for r in ws if not r["zv"]], 1)
                line.append(f"{w}: n {s1['n']} days {s1['days']} mk {s1['mk']} PF1 {s1['pf']:.2f} PF10 {s10['pf']:.2f} "
                            f"net1 {s1['net']:+.2f} net10 {s10['net']:+.2f} loss {s1['loss']:.1%} PFx1.2 {sx['pf']:.2f} "
                            f"zv {sum(r['zv'] for r in ws)} PF1noZV {nz['pf']:.2f}")
            print(f"{var} [{tag}]  " + " | ".join(line))
            if tag == "main":
                ab = [r for r in rs if win(r["day"]) in ("A", "B")]
                sab = score(ab, 1)
                m, se, z = cluster_mean_z([(r["day"], pnl(r, 1)) for r in ab])
                print(f"   A+B pooled: n {sab['n']} days {sab['days']} PF1 {sab['pf']:.2f} net1 {sab['net']:+.2f} "
                      f"mean {m*100:+.2f}c z {z:+.2f}")
                if which == {"A", "B", "C"}:
                    m, se, z = cluster_mean_z([(r["day"], pnl(r, 1)) for r in rs])
                    print(f"   A+B+C pooled: mean {m*100:+.2f}c day-clustered z {z:+.2f} (bar 5.17)")
    sides = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["tag"] == "main" and win(r["day"]) in which:
            k = (r["var"].split("-")[0], r["side"], "price>=0.5" if r["price"] >= 0.5 else "price<0.5")
            sides[k][0] += 1
            sides[k][1] += 0 if r["won"] else 1
    for k in sorted(sides):
        print("  orders, losses", k, sides[k])


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
