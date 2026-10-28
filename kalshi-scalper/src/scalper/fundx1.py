"""FUNDX1 (README, Strategy card FUNDX1): Binance against Deribit funding difference, delta neutral. Research only.
Usage: python -m scalper.fundx1 run   (once; a second run is refused).
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np

from .carry1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "fundx1_result.txt"
ENTER_ANN, EXIT_ANN, LOOK = 0.05, 0.015, 3
COST_SIDE = 2 * (0.0005 + 0.0002)


def d_of(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def deribit(cur):
    db = sqlite3.connect(DATA_DIR / "search5k.sqlite")
    f = {}
    for ts, i8 in db.execute("select ts, i8 from fund where cur=? order by ts", (cur,)):
        f.setdefault(d_of(ts), []).append(i8)
    px = {}
    for ts, c in db.execute("select ts, c from bar where cur=? order by ts", (cur,)):
        px[d_of(ts)] = c
    # a day's funding = mean of the 8 hour rate x 3; the bar close is the last 1 minute close of the day
    return {d: float(np.mean(v)) * 3 for d, v in f.items()}, px


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    out = []; tot_trades = 0; eqs = []
    for coin, sym in (("BTC", "BTCUSDT"), ("ETH", "ETHUSDT")):
        days, fr, S, F = load(sym)
        fd, dpx = deribit(coin)
        common = sorted(set(days) & set(fd) & set(dpx))
        diff = np.array([fr[d] - fd[d] for d in common])
        cap = 1.0; eq = [1.0]; pos = 0; N = 0.0; trades = 0
        for i in range(1, len(common)):
            d, p = common[i], common[i - 1]
            pnl = 0.0
            if pos != 0:
                pnl = N * pos * (fr[d] - fd[d]) * -1 * -1  # pos=+1: short Binance (receives fr) long Deribit (pays fd)
                pnl += N * pos * ((dpx[d] / dpx[p] - 1) - (F[d] / F[p] - 1))
                cap += pnl
            if i >= LOOK:
                ann = float(np.mean(diff[i - LOOK + 1:i + 1])) * 365
                if pos != 0 and (abs(ann) < EXIT_ANN or np.sign(ann) != pos):
                    cap -= N * COST_SIDE; pos = 0
                elif pos == 0 and abs(ann) >= ENTER_ANN:
                    pos = 1 if ann > 0 else -1; N = 0.5 * cap; cap -= N * COST_SIDE; trades += 1
            eq.append(cap)
        eq = np.array(eq); yrs = (len(common) - 1) / 365
        out.append((coin, len(common), float(np.mean(np.abs(diff))) * 365, trades, eq[-1] ** (1 / yrs) - 1 if yrs > 0 else 0.0, float(((np.maximum.accumulate(eq) - eq) / np.maximum.accumulate(eq)).max())))
        tot_trades += trades
    lines = []
    for coin, n, mabs, tr, ann, dd in out:
        lines.append(f"{coin}: {n} overlapping days, mean absolute funding difference {100 * mabs:.2f}% a year, {tr} entries, net {100 * ann:+.2f}% a year, max drawdown {100 * dd:.2f}%")
    net = float(np.mean([o[4] for o in out]))
    verdict = "NOT_ENOUGH_DATA" if tot_trades < 8 else ("FALSIFIED" if net < 0.03 else "NOT_YET_FALSIFIED")
    lines.insert(0, f"FUNDX1 {verdict}: {tot_trades} entries in total, mean net {100 * net:+.2f}% a year (kill: under 8 entries is NOT_ENOUGH_DATA; under 3% a year is FALSIFIED)")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
