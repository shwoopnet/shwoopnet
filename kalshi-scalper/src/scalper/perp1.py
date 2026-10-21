"""PERP1 (README, Pre-registration: PERP1): a daily trend breakout on four liquid perpetual markets, tested on years of public daily bars with Kalshi's perp fees applied.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.perp1 fetch   then   python -m scalper.perp1 run
The rule, costs and pass bar were written in the README before this file existed. `run` writes a result file next to the data and refuses a second run unless it is
deleted on purpose (a crash fix, never a chase for a pass).
"""
from __future__ import annotations

import json
import random
import statistics as st
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

BARS_FILE = DATA_DIR / "perp1_bars.json"
RESULT_FILE = DATA_DIR / "perp1_result.txt"
MARKETS = {"GOLD": ("GC=F", "2010-01-04"), "US500": ("^GSPC", "2010-01-04"), "BTC": ("BTC-USD", "2014-09-17"), "ETH": ("ETH-USD", "2017-11-09")}
N_ENTRY, N_EXIT, ATR_N, STOP_ATR = 20, 10, 14, 1.5
FEE_SIDE, SLIP_SIDE, FUNDING_DAY = 0.0012, 0.0001, 0.0002
STRESS = 1.2
RISK, LEV_CAP = 0.02, 3.0
MIN_TRADES, MIN_YEARS, Z_BAR, PLACEBO_REPS = 100, 4, 2.1, 200


def _ts(date: str) -> int:
    return int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    now = int(time.time())
    out = {}
    for name, (sym, start) in MARKETS.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&period1={_ts(start)}&period2={now}"
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    res = json.load(r)["chart"]["result"][0]
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5 * (attempt + 1))
        q = res["indicators"]["quote"][0]
        bars = []
        for i, t in enumerate(res["timestamp"]):
            o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
            if None in (o, h, l, c) or min(o, h, l, c) <= 0:
                continue
            bars.append([time.strftime("%Y-%m-%d", time.gmtime(t)), o, h, l, c])
        out[name] = bars
        print(f"{name}: {len(bars)} daily bars {bars[0][0]} to {bars[-1][0]}", flush=True)
    BARS_FILE.write_text(json.dumps(out))


def true_range(h: float, l: float, prev_close: float) -> float:
    return max(h - l, abs(h - prev_close), abs(l - prev_close))


def simulate(bars: list, market: str) -> list[dict]:
    """The registered rule on one market's daily bars [[date, o, h, l, c], ...]. A signal is read at a day's close and filled at the NEXT day's open. A position still open at the
    end of the data is not counted."""
    dates = [b[0] for b in bars]
    o = [b[1] for b in bars]; h = [b[2] for b in bars]; l = [b[3] for b in bars]; c = [b[4] for b in bars]
    n = len(bars)
    tr = [None] + [true_range(h[i], l[i], c[i - 1]) for i in range(1, n)]
    trades, pos, pending = [], None, None

    def close_pos(i: int, price: float, stopped: bool) -> None:
        nonlocal pos
        days = max(1, (datetime.strptime(dates[i], "%Y-%m-%d") - datetime.strptime(pos["entry_date"], "%Y-%m-%d")).days)
        gross = pos["side"] * (price / pos["entry"] - 1.0)
        trades.append({"market": market, "side": pos["side"], "entry_i": pos["entry_i"], "exit_i": i, "entry_date": pos["entry_date"], "exit_date": dates[i], "entry": pos["entry"],
                       "exit": price, "days": days, "gross": gross, "stopped": stopped, "stop_dist": pos["stop_dist"]})
        pos = None

    for i in range(n):
        if pending:                                           # orders decided at the previous close, filled at this open
            act, pending = pending, None
            if act.get("exit") and pos:
                close_pos(i, o[i], False)
            if act.get("enter") and pos is None:
                side, atr = act["enter"], act["atr"]
                stop = o[i] - side * STOP_ATR * atr
                pos = {"side": side, "entry": o[i], "entry_i": i, "entry_date": dates[i], "stop": stop, "stop_dist": STOP_ATR * atr / o[i]}
        if pos:                                               # the stop is a resting order: it fills intrabar, or at the open if the day gaps through it
            if pos["side"] == 1 and l[i] <= pos["stop"]:
                close_pos(i, o[i] if o[i] <= pos["stop"] else pos["stop"], True)
            elif pos["side"] == -1 and h[i] >= pos["stop"]:
                close_pos(i, o[i] if o[i] >= pos["stop"] else pos["stop"], True)
        if i >= max(N_ENTRY, ATR_N):                          # signals at the close of day i, from closes of earlier days only
            hi20, lo20 = max(c[i - N_ENTRY:i]), min(c[i - N_ENTRY:i])
            long_sig, short_sig = c[i] > hi20, c[i] < lo20
            atr = st.mean(tr[i - ATR_N + 1:i + 1])
            if pos:
                lo10, hi10 = min(c[i - N_EXIT:i]), max(c[i - N_EXIT:i])
                if (pos["side"] == 1 and c[i] < lo10) or (pos["side"] == -1 and c[i] > hi10):
                    pending = {"exit": True}
                    if pos["side"] == 1 and short_sig:
                        pending.update(enter=-1, atr=atr)
                    elif pos["side"] == -1 and long_sig:
                        pending.update(enter=1, atr=atr)
            elif long_sig:
                pending = {"enter": 1, "atr": atr}
            elif short_sig:
                pending = {"enter": -1, "atr": atr}
    return trades


def cost(days: int, mult: float = 1.0) -> float:
    return mult * (2 * (FEE_SIDE + SLIP_SIDE) + FUNDING_DAY * days)


def net(t: dict, mult: float = 1.0) -> float:
    return t["gross"] - cost(t["days"], mult)


def placebo_means(bars_by: dict, trades: list[dict], reps: int = PLACEBO_REPS, seed: int = 11) -> list[float]:
    """Same sides and holding lengths, entry dates moved uniformly at random within each market's history, no stops, same costs."""
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        tot = 0.0
        for t in trades:
            bars = bars_by[t["market"]]
            hold = t["exit_i"] - t["entry_i"]
            j = rng.randrange(N_ENTRY, len(bars) - hold - 1)
            e, x = bars[j][1], bars[j + hold][1]
            days = max(1, (datetime.strptime(bars[j + hold][0], "%Y-%m-%d") - datetime.strptime(bars[j][0], "%Y-%m-%d")).days)
            tot += t["side"] * (x / e - 1.0) - cost(days)
        out.append(tot / len(trades))
    return out


def verdict(trades: list[dict], placebo: list[float]) -> tuple[str, dict]:
    n = len(trades)
    years = {t["entry_date"][:4] for t in trades}
    if n < MIN_TRADES or len(years) < MIN_YEARS:
        return "NOT_ENOUGH_DATA", {"n": n, "years": len(years)}
    nets = [net(t) for t in trades]
    mean, se, z = cluster_mean_z([(t["entry_date"][:7], r) for t, r in zip(trades, nets)])
    dates = sorted(t["entry_date"] for t in trades)
    mid = dates[len(dates) // 2]
    h1 = [r for t, r in zip(trades, nets) if t["entry_date"] < mid]
    h2 = [r for t, r in zip(trades, nets) if t["entry_date"] >= mid]
    m1, m2 = (st.mean(h1) if h1 else 0.0), (st.mean(h2) if h2 else 0.0)
    stress = st.mean(net(t, STRESS) for t in trades)
    p95 = sorted(placebo)[int(0.95 * (len(placebo) - 1))] if placebo else float("inf")
    ok = mean > 0 and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0 and mean > p95
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "years": len(years), "mean": mean, "se": se, "z": z, "h1": m1, "h2": m2, "stress": stress, "p95": p95, "mde": Z_BAR * se}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"PERP1 has been run once already ({RESULT_FILE}). A second read is only for a crash fix, and the file is deleted on purpose first.")
    bars_by = json.loads(BARS_FILE.read_text())
    trades = []
    for market, bars in bars_by.items():
        trades.extend(simulate(bars, market))
    trades.sort(key=lambda t: t["entry_date"])
    pl = placebo_means(bars_by, trades) if trades else []
    v, s = verdict(trades, pl)
    pc = lambda x: f"{x * 100:+.2f}%"
    L = [f"PERP1: {len(trades)} trades across {len(bars_by)} markets."]
    if "mean" in s:
        L.append(f"PERP1: n={s['n']} over {s['years']} years, mean net {pc(s['mean'])} per trade on notional, z {s['z']:+.2f}, halves {pc(s['h1'])} / {pc(s['h2'])}, costs x{STRESS} {pc(s['stress'])}, "
                 f"placebo 95th percentile {pc(s['p95'])} -> {v}")
        L.append(f"    minimum detectable edge {pc(s['mde'])}")
    else:
        L.append(f"PERP1: n={s['n']} over {s['years']} years -> {v}")
    L.append("Per market (information):")
    for m in bars_by:
        mt = [t for t in trades if t["market"] == m]
        if mt:
            bh = bars_by[m][-1][4] / bars_by[m][0][4] - 1.0
            L.append(f"  {m:<6} trades {len(mt):>4}  mean net {pc(st.mean(net(t) for t in mt)):>8}  win rate {sum(1 for t in mt if net(t) > 0) / len(mt) * 100:3.0f}%  stopped {sum(1 for t in mt if t['stopped']) / len(mt) * 100:3.0f}%  "
                     f"avg hold {st.mean(t['days'] for t in mt):4.1f} days  buy and hold {pc(bh)} over {bars_by[m][0][0]} to {bars_by[m][-1][0]}")
    L.append("Per calendar year of entry (information):")
    by_year = defaultdict(list)
    for t in trades:
        by_year[t["entry_date"][:4]].append(net(t))
    for y in sorted(by_year):
        L.append(f"  {y}: {len(by_year[y]):>3} trades, mean net {pc(st.mean(by_year[y]))}")
    eq = [min(LEV_CAP, RISK / t["stop_dist"]) * net(t) for t in trades]
    if eq:
        L.append(f"Equity return per trade at the leverage rule (2% risked, 3x cap, information): mean {pc(st.mean(eq))}, worst {pc(min(eq))}, best {pc(max(eq))}")
    text = "\n".join(L)
    print(text)
    RESULT_FILE.write_text(text + "\n")


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else run()
