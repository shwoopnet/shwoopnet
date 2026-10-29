"""GOLDFV1: gold's 15 minute market against the COMEX gold future (registered in README.md before any scoring).
Usage: python -m scalper.goldfv1 run | holdout (holdout once, after the run verdicts are written)     (reads data/gc1m.json, data/book.sqlite, data/five.sqlite; public data only)
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

from .fees import taker_fee

START = 1790812800  # 2026-10-01 00:00 UTC
DBS = ("data/book.sqlite", "data/five.sqlite")
LOOKS = (10, 6)
EDGE = 0.05


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def load_bars() -> dict[int, float]:
    d = json.load(open("data/gc1m.json"))["bars"]
    return {int(t): v[3] for t, v in d.items()}


def load_markets(last_bar: int):
    mk, cd = {}, defaultdict(dict)
    for f in DBS:
        if not Path(f).exists():
            continue
        db = sqlite3.connect(f)
        for t, o, c, r in db.execute("select ticker, open_ts, close_ts, result from market where series='KXGOLD15M' and close_ts>=?", (START,)):
            if c <= last_bar and r in ("yes", "no"):
                mk[t] = (o, c, r)
        for t, e, ba, aa, v in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle where series='KXGOLD15M' and end_ts>=?", (START - 3600,)):
            if t in mk:
                cd[t][e] = (ba, aa, v)
    return mk, cd


def bar_at_or_before(bars, t, maxgap=120):
    """Close of the last bar whose START is at or before t, if it started within maxgap seconds."""
    for k in range(0, maxgap + 1, 60):
        s = (t - k) // 60 * 60
        if s in bars:
            return bars[s]
    return None


def model(bars, o, c, D):
    last = D - 60
    now_px = bar_at_or_before(bars, last)
    open_px = bar_at_or_before(bars, o - 60)
    if now_px is None or open_px is None:
        return None, "missing bar"
    seq = [bars.get(s) for s in range((last // 60) * 60 - 60 * 60, (last // 60) * 60 + 1, 60)]
    ch = [b / a - 1 for a, b in zip(seq, seq[1:]) if a is not None and b is not None]
    win = [bars.get(s) for s in range((o - 60) // 60 * 60, (last // 60) * 60 + 1, 60)]
    wch = [b / a - 1 for a, b in zip(win, win[1:]) if a is not None and b is not None]
    if len(ch) < 45:
        return None, "sigma bars"
    if any(abs(x) > 0.005 for x in ch + wch):
        return None, "jump"
    dif = [b - a for a, b in zip(seq, seq[1:]) if a is not None and b is not None]
    sig = st.pstdev(dif)
    tau = (c - D) / 60
    if sig <= 0:
        return None, "flat"
    return phi((now_px - open_px) / (sig * math.sqrt(tau))), None


def trades(bars, mk, cd, look, mode, nextfill=False):
    out, skips = [], defaultdict(int)
    for t, (o, c, r) in mk.items():
        D = c - look * 60
        q = cd[t].get(D + (60 if nextfill else 0))
        if q is None:
            skips["no candle"] += 1
            continue
        pm, why = model(bars, o, c, D)
        if pm is None:
            skips[why] += 1
            continue
        bid, ask, vol = q
        sides = [("yes", ask, pm), ("no", 1 - bid if bid and bid > 0 else None, 1 - pm)]
        for side, a, p in sides:
            if a is None or not (0 < a < 0.99):
                continue
            if mode == "S" and 0.10 <= a <= 0.95 and p - a >= EDGE:
                out.append((c, t, side, a, side == r, vol, p))
            if mode in ("FK", "FR") and 0.88 <= a <= 0.97:
                keep = p >= a
                if (mode == "FK") == keep:
                    out.append((c, t, side, a, side == r, vol, p))
    return out, skips


def stats(tr, n=1, fm=1.0, drop0=False):
    if drop0:
        tr = [x for x in tr if x[5] and x[5] > 0]
    pnl = [((1 - x[3]) if x[4] else -x[3]) * n - fm * taker_fee(x[3], n) for x in tr]
    w, l = sum(p for p in pnl if p > 0), -sum(p for p in pnl if p < 0)
    pf = w / l if l > 0 else float("inf") if w > 0 else float("nan")
    days = defaultdict(float)
    for x, p in zip(tr, pnl):
        days[x[0] // 86400] += p
    dv = list(days.values())
    z = (st.mean(dv) / (st.pstdev(dv) / math.sqrt(len(dv)))) if len(dv) > 1 and st.pstdev(dv) > 0 else float("nan")
    return dict(n=len(tr), days=len(dv), pf=round(pf, 3), cents_per=round(100 * sum(pnl) / n / max(1, len(tr)), 2), z=round(z, 2))


def main() -> None:
    if sys.argv[1:] not in (["run"], ["holdout"]):
        print(__doc__)
        return
    hold = sys.argv[1] == "holdout"
    bars = load_bars()
    mk, cd = load_markets(max(bars))
    closes = sorted(c for _, c, _ in mk.values())
    cut1, cut2 = closes[len(closes) // 3], closes[2 * len(closes) // 3]
    print(f"markets {len(mk)}; windows split at {cut1} and {cut2}")
    W = {"discovery": lambda c: c < cut1, "validation": lambda c: cut1 <= c < cut2, "holdout": lambda c: c >= cut2}
    for look in LOOKS:
        for mode, name in (("S", f"S{look}"), ("FK", f"F{look} kept"), ("FR", f"F{look} removed"), ("L1", f"L1 gold {look} parent")):
            if mode == "L1":
                tr = trades(bars, mk, cd, look, "FK")[0] + trades(bars, mk, cd, look, "FR")[0]
                sk = {}
            else:
                tr, sk = trades(bars, mk, cd, look, mode)
            nx = trades(bars, mk, cd, look, mode if mode != "L1" else "FK", nextfill=True)[0]
            print(f"\n{name}: skips {dict(sk)}")
            for wn, f in W.items():
                if (wn == "holdout") != hold:
                    continue
                sub = [x for x in tr if f(x[0])]
                print(f"  {wn:10s} 1c {stats(sub)}  10c {stats(sub, 10)}  fees1.2 {stats(sub, 10, 1.2)['pf']}  drop0vol {stats(sub, 1, 1, True)['pf']}")
            print(f"  next-candle fill, these windows: {stats([x for x in nx if (x[0] >= cut2) == hold])}")


if __name__ == "__main__":
    main()
