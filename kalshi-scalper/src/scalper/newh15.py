"""NEWH15 scorer (registered in workers/NEWH15_REGISTRATION.md before any race outcome was read).

Three tries on the Coin Race (KXCRYPTOLEAD15M) conditioned on the KXBTC15M quote at 10 minutes left.
Usage: PYTHONPATH=src python -m scalper.newh15 info|score [--holdout]
Candles come from data/newh15/candles.sqlite (newh15_fetch.py).
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

DB = "data/newh15/candles.sqlite"
D0 = int(datetime(2026, 8, 24, tzinfo=timezone.utc).timestamp())
D1 = int(datetime(2026, 9, 28, tzinfo=timezone.utc).timestamp())
V1 = int(datetime(2026, 10, 18, tzinfo=timezone.utc).timestamp())
UP, DOWN = 0.70, 0.30
BAND = (0.15, 0.85)
RULES = {  # name: (state, coin, side)
    "H1 RACE-UP-HYPE": ("UP", "HYPE", "yes"),
    "H2 RACE-DOWN-BTC": ("DOWN", "BTC", "yes"),
    "H3 RACE-UP-BTCNO": ("UP", "BTC", "no"),
}
Z_BAR = 5.27


def stage(c):
    return "disc" if c < D1 else ("val" if c < V1 else "hold")


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def fee(p, c=10, m=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * m * 100, 9)) / 100


def net(t, c=10, m=1.0):
    return c * ((1.0 if t["won"] else 0.0) - t["fill"]) - fee(t["fill"], c, m)


def pf(v):
    g = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    return float("inf") if l == 0 else g / l


def dayz(tr):
    d = defaultdict(float)
    for t in tr:
        d[day(t["close"])] += net(t)
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def load():
    c = sqlite3.connect(DB)
    ev = defaultdict(dict)  # close -> coin -> (ticker, result)
    for tk, close, res in c.execute("select ticker,close_ts,result from market where series='KXCRYPTOLEAD15M'"):
        ev[close][tk.rsplit("-", 1)[1]] = (tk, res)
    btc = {close: tk for tk, close in c.execute("select ticker,close_ts from market where series='KXBTC15M'")}
    q = {}
    for tk, end, b, a, v in c.execute("select ticker,end_ts,bid_c,ask_c,volume from candle where series in ('KXCRYPTOLEAD15M','KXBTC15M')"):
        q[(tk, end)] = (b, a, v or 0)
    return ev, btc, q


def state(q, tk, close):
    x = q.get((tk, close - 600))
    if not x or x[0] is None or x[1] is None or not (0 < x[0] < x[1] < 1) or x[1] - x[0] > 0.05:
        return None, None
    m = (x[0] + x[1]) / 2
    return ("UP" if m >= UP else "DOWN" if m <= DOWN else "MID"), m


def trades(ev, btc, q):
    out = {k: [] for k in RULES}
    fun = {k: Counter() for k in RULES}
    for close, mk in sorted(ev.items()):
        if len(mk) != 5 or sum(1 for v in mk.values() if v[1] == "yes") != 1 or close not in btc:
            continue
        st, m = state(q, btc[close], close)
        for name, (want, coin, side) in RULES.items():
            f = fun[name]
            if st is None:
                f["no state"] += 1
                continue
            if st != want:
                f["state differs"] += 1
                continue
            tk, res = mk[coin]
            fq = q.get((tk, close - 540))
            if not fq or fq[0] is None or fq[1] is None:
                f["no fill quote"] += 1
                continue
            a = fq[1] if side == "yes" else round(1 - fq[0], 6)
            if not (0 < a < 1) or not (BAND[0] - 1e-9 <= a <= BAND[1] + 1e-9):
                f["band"] += 1
                continue
            out[name].append({"close": close, "fill": a, "won": res == side, "zv": fq[2] <= 0, "stage": stage(close)})
            f["trade"] += 1
    return out, fun


def summ(tr):
    if not tr:
        return "n 0"
    n10 = [net(t) for t in tr]
    nz = [net(t) for t in tr if not t["zv"]]
    return (f"n {len(tr)} ({len({day(t['close']) for t in tr})} d) PF10 {pf(n10):.2f} PF1 {pf([net(t, 1) for t in tr]):.2f} "
            f"PFx1.2 {pf([net(t, 10, 1.2) for t in tr]):.2f} net10 ${sum(n10):.2f} netx1.2 ${sum(net(t, 10, 1.2) for t in tr):.2f} "
            f"win {sum(t['won'] for t in tr) / len(tr):.1%} fill {statistics.mean(t['fill'] for t in tr):.3f} z {dayz(tr):.2f} | "
            f"zero-vol {sum(t['zv'] for t in tr)}, PF10 without {pf(nz) if nz else float('nan'):.2f} (n {len(nz)})")


def info(ev, btc, q):
    """Discovery window only: who led, by state. No rule, no fee."""
    lead = defaultdict(Counter)
    spr = []
    for close, mk in sorted(ev.items()):
        if stage(close) != "disc" or len(mk) != 5 or close not in btc:
            continue
        if sum(1 for v in mk.values() if v[1] == "yes") != 1:
            continue
        st, m = state(q, btc[close], close)
        if st is None:
            continue
        w = [c for c, v in mk.items() if v[1] == "yes"][0]
        lead[st][w] += 1
        for c, v in mk.items():
            x = q.get((v[0], close - 540))
            if x and x[0] is not None and x[1] is not None:
                spr.append(x[1] - x[0])
    for st, cnt in lead.items():
        n = sum(cnt.values())
        print(st, n, {c: f"{v / n:.1%}" for c, v in sorted(cnt.items())})
    if spr:
        spr.sort()
        print("race spread at fill candle: median", spr[len(spr) // 2], "n", len(spr))


if __name__ == "__main__":
    ev, btc, q = load()
    if sys.argv[1] == "info":
        info(ev, btc, q)
    else:
        hold = "--holdout" in sys.argv
        out, fun = trades(ev, btc, q)
        for name, tr in out.items():
            print("==", name, dict(fun[name]))
            for s in ("disc", "val") + (("hold",) if hold else ()):
                print("  ", s, summ([t for t in tr if t["stage"] == s]))
