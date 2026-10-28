"""PAIRS1 (README, Strategy card PAIRS1): market-neutral ETH against BTC on the Binance perpetuals. Research only.
Usage: python -m scalper.pairs1 run   (once; a second run is refused). Data: data/binance_carry (daily perpetual closes and funding).
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

from .carry1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "pairs1_result.txt"
LOOK, ENTER, EXIT, STOP, MAXD = 30, 2.0, 0.5, 4.0, 30
COST_SIDE = 2 * (0.0005 + 0.0002)  # two legs, per side, of one leg's notional


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    db, fb, sb, Fb = load("BTCUSDT"); de, fe, se, Fe = load("ETHUSDT")
    days = sorted(set(db) & set(de))
    lr = np.array([np.log(Fe[d] / Fb[d]) for d in days])
    cap = 1.0; eq = [1.0]; pos = 0; N = 0.0; entry_i = 0; trades = []; pnl_days = []; ent_cap = 0.0
    for i in range(1, len(days)):
        d = days[i]; pnl = 0.0
        if pos != 0:
            rE = Fe[d] / Fe[days[i - 1]] - 1; rB = Fb[d] / Fb[days[i - 1]] - 1
            pnl = N * pos * (rE - rB) - pos * N * (fe[d] - fb[d])
            cap += pnl
        if i >= LOOK:
            w = lr[i - LOOK + 1:i + 1]; z = (lr[i] - w.mean()) / (w.std() or 1e-9)
            if pos != 0 and (abs(z) <= EXIT or abs(z) >= STOP or i - entry_i >= MAXD):
                c = N * COST_SIDE; cap -= c; pnl -= c; pos = 0
                trades.append(cap - ent_cap)
            elif pos == 0 and abs(z) >= ENTER and abs(z) < STOP:
                pos = -1 if z > 0 else 1  # z high: ETH rich, short ETH long BTC (pos = -1 means short the ratio ETH/BTC)
                N = 0.5 * cap; c = N * COST_SIDE; cap -= c; pnl -= c; entry_i = i; ent_cap = cap + c
        eq.append(cap); pnl_days.append((d, pnl))
    eq = np.array(eq); yrs = (len(days) - 1) / 365
    peak = np.maximum.accumulate(eq); dd = float(((peak - eq) / peak).max())
    ann = eq[-1] ** (1 / yrs) - 1
    t = np.array(trades); w = t[t > 0].sum(); l = -t[t < 0].sum(); pf = float(w / l) if l > 0 else float("inf")
    by = defaultdict(float)
    for d, p in pnl_days: by[d[:4]] += p
    by_m = defaultdict(float)
    for d, p in pnl_days: by_m[d[:7]] += p
    last = np.array([p for _, p in pnl_days[-365:]]); last_ret = float(np.prod(1 + last / np.maximum(eq[-366:-1], 1e-9)) - 1)
    verdict = "NOT_ENOUGH_DATA" if len(trades) < 30 else ("FALSIFIED" if (pf < 1.5 or last_ret < 0.05 or dd > 0.20) else "NOT_YET_FALSIFIED")
    lines = [f"PAIRS1 {verdict}: profit factor of trades {pf:.2f}, {len(trades)} trades, loss rate {100 * float((t < 0).mean()):.0f}%, net {100 * ann:+.2f}% a year on capital, max drawdown {100 * dd:.1f}%, worst month {100 * min(by_m.values()):+.1f}% (of capital units), last 365 days {100 * last_ret:+.1f}%, {days[0]} to {days[-1]}",
             "by year (profit in capital units): " + ", ".join(f"{y} {100 * v:+.1f}%" for y, v in sorted(by.items()))]
    for c0 in (500, 5000, 20000):
        lines.append(f"  on ${c0:,}: whole period final ${c0 * eq[-1]:,.0f}, last 12 months about ${c0 * last_ret:+,.0f}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
