"""CARRY1 (README, Strategy card CARRY1): delta-neutral funding carry on Bitcoin and Ethereum (Binance spot long, USD-M perpetual short). Research only.
Usage: python -m scalper.carry1 run   (once; a second run is refused). Data: data/binance_carry/*.zip (funding rate and 1 day klines).
"""
from __future__ import annotations

import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from .paths import DATA_DIR

D = DATA_DIR / "binance_carry"
RESULT = DATA_DIR / "carry1_result.txt"
ENTER_ANN, EXIT_ANN, ENTER_DAYS, EXIT_DAYS, BASIS_EXIT = 0.10, 0.03, 14, 7, 0.02
COST_LEG_IN = 0.0010 + 0.0005 + 2 * 0.0002  # spot taker, perp taker, slippage on both legs, per notional
COST_LEG_OUT = COST_LEG_IN


def day(ms):
    ms = int(ms)
    ms = ms // 1000 if ms > 10 ** 14 else ms
    return datetime.fromtimestamp(ms / 1000 if ms > 10 ** 11 else ms, timezone.utc).strftime("%Y-%m-%d")


def read_csv(path):
    z = zipfile.ZipFile(path)
    for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        yield row


def load(sym):
    funding = defaultdict(float); spot = {}; fut = {}
    for f in sorted(D.glob(f"fr_{sym}_*.zip")):
        for r in read_csv(f):
            try:
                ts = int(r[0])
            except ValueError:
                continue
            funding[day(ts)] += float(r[2])
    for f in sorted(D.glob(f"spot_{sym}_*.zip")):
        for r in read_csv(f):
            try:
                int(r[0])
            except ValueError:
                continue
            spot[day(r[0])] = float(r[4])
    for f in sorted(D.glob(f"fut_{sym}_*.zip")):
        for r in read_csv(f):
            try:
                int(r[0])
            except ValueError:
                continue
            fut[day(r[0])] = float(r[4])
    days = sorted(set(spot) & set(fut) & set(funding))
    return days, funding, spot, fut


def simulate(sym):
    days, fr, S, F = load(sym)
    cap = 1.0; eq = []; pnl_days = []; in_pos = False; trades = 0; hist = []
    N = S0 = F0 = prevS = prevF = 0.0; inpos_days = 0; entry_day = None; liq = False
    for i, d in enumerate(days):
        pnl = 0.0
        if in_pos:
            pnl += N * fr[d] + N * ((S[d] - prevS) / S0 - (F[d] - prevF) / F0)
            prevS, prevF = S[d], F[d]; inpos_days += 1
            if F[d] / F0 >= 2.0:
                liq = True
        cap += pnl
        hist.append(fr[d])
        ann14 = np.mean(hist[-ENTER_DAYS:]) * 365 if len(hist) >= ENTER_DAYS else 0.0
        ann7 = np.mean(hist[-EXIT_DAYS:]) * 365 if len(hist) >= EXIT_DAYS else 0.0
        basis = F[d] / S[d] - 1
        if in_pos and (ann7 < EXIT_ANN or basis <= -BASIS_EXIT):
            cap -= N * COST_LEG_OUT; pnl -= N * COST_LEG_OUT; in_pos = False
        elif (not in_pos) and ann14 >= ENTER_ANN and len(hist) >= ENTER_DAYS:
            N = 0.5 * cap; S0 = prevS = S[d]; F0 = prevF = F[d]
            cap -= N * COST_LEG_IN; pnl -= N * COST_LEG_IN; in_pos = True; trades += 1
        eq.append(cap); pnl_days.append((d, pnl))
    return days, np.array(eq), pnl_days, trades, inpos_days, liq


def metrics(days, eq, pnls, trades, inpos, label):
    dd = float(np.max(np.maximum.accumulate(eq) - eq) / np.maximum.accumulate(eq).max()) if len(eq) else 0.0
    peak = np.maximum.accumulate(eq); dd = float(((peak - eq) / peak).max())
    yrs = len(days) / 365
    ann = eq[-1] ** (1 / yrs) - 1 if yrs > 0 else 0.0
    pn = np.array([p for _, p in pnls]); w = pn[pn > 0].sum(); l = -pn[pn < 0].sum()
    by_m = defaultdict(float)
    for (d, p) in pnls:
        by_m[d[:7]] += p
    return {"label": label, "days": len(days), "ann": ann, "dd": dd, "pf": float(w / l) if l > 0 else float("inf"), "worst_day": float(pn.min()), "worst_month": min(by_m.values()), "trades": trades, "time_in": inpos / max(len(days), 1), "final": float(eq[-1])}


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    res = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        res[sym] = simulate(sym)
    n = min(len(res[s][0]) for s in res)
    days = res["BTCUSDT"][0][-n:]
    # 50/50 portfolio of the two coin books (each normalised to 1.0 at its own start); daily returns averaged
    rets = []
    for s in res:
        eq = res[s][1][-n:]; r = np.diff(np.insert(eq, 0, eq[0])) / np.insert(eq, 0, eq[0])[:-1]
        rets.append(r)
    pr = np.mean(rets, axis=0); eqp = np.cumprod(1 + pr)
    pnls = list(zip(days, pr))
    trades = sum(res[s][3] for s in res); inpos = int(np.mean([res[s][4] for s in res]))
    out = []
    whole = metrics(days, eqp, pnls, trades, inpos, "whole period")
    out.append(whole)
    for y in sorted({d[:4] for d in days}):
        idx = [i for i, d in enumerate(days) if d.startswith(y)]
        e = np.cumprod(1 + pr[idx]); out.append(metrics([days[i] for i in idx], e, [pnls[i] for i in idx], 0, 0, y))
    last = list(range(len(days) - 365, len(days)))
    e = np.cumprod(1 + pr[last]); out.append(metrics([days[i] for i in last], e, [pnls[i] for i in last], 0, 0, "last 365 days"))
    lines = [f"CARRY1: Bitcoin and Ethereum carry, 50/50, {days[0]} to {days[-1]} ({n} days), entry funding >= {100 * ENTER_ANN:.0f}% a year (14 day mean), exit < {100 * EXIT_ANN:.0f}% (7 day) or basis -2%; cost {100 * (COST_LEG_IN + COST_LEG_OUT):.2f}% of notional per round trip; liquidation breach (perp doubled while held): {[s for s in res if res[s][5]]}"]
    for m in out:
        lines.append(f"{m['label']:14s} net {100 * m['ann']:+.2f}% a year, max drawdown {100 * m['dd']:.2f}%, daily PF {m['pf']:.2f}, worst day {100 * m['worst_day']:+.3f}%, worst month {100 * m['worst_month']:+.2f}%" + (f", trades {m['trades']}, in position {100 * m['time_in']:.0f}% of days" if m['label'] == 'whole period' else ""))
    last_ann = out[-1]["ann"]; dd = out[0]["dd"]; tr = trades
    verdict = "NOT_ENOUGH_DATA" if tr < 20 else ("NOT_YET_FALSIFIED" if (last_ann >= 0.03 and dd <= 0.05) else "FALSIFIED")
    lines.insert(0, f"CARRY1 {verdict} (as a deployable: last 12 months net {100 * last_ann:+.2f}% a year, whole-period drawdown {100 * dd:.2f}%, {tr} entries)")
    for cap in (500, 5000, 20000):
        lines.append(f"  on ${cap:,}: last 12 months about ${cap * last_ann:+,.0f}, whole period final ${cap * out[0]['final']:,.0f}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
