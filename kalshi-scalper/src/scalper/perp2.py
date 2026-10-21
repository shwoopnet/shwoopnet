"""PERP2 (buy the dip in an uptrend) and PERP3 (gold against silver) (README, Pre-registration: PERP2 and PERP3). Same daily bars, costs and placebo method as PERP1 (`perp1.py`).
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.perp2 fetch   then   python -m scalper.perp2 run PERP2   and   python -m scalper.perp2 run PERP3
Each run writes a result file next to the data and a second run is refused unless it is deleted on purpose (a crash fix, never a chase for a pass).
"""
from __future__ import annotations

import json
import random
import statistics as st
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime

from .calibration import cluster_mean_z
from .paths import DATA_DIR
from . import perp1 as P1

SILVER_FILE = DATA_DIR / "perp2_silver.json"
SMA_N, DOWN_DAYS, STOP_ATR2, EXIT_HI, MAX_HOLD2 = 100, 3, 2.0, 5, 20
ZWIN, Z_ENTRY, Z_STOP, MAX_HOLD3 = 60, 2.0, 4.0, 30
Z_BAR2 = 2.4
SPEC = {"PERP2": {"min_trades": 100, "min_years": 4}, "PERP3": {"min_trades": 40, "min_years": 4}}


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    now = int(time.time())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1d&period1={P1._ts('2010-01-04')}&period2={now}"
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
    SILVER_FILE.write_text(json.dumps(bars))
    print(f"SILVER: {len(bars)} daily bars {bars[0][0]} to {bars[-1][0]}", flush=True)


def dip_trades(bars: list, market: str) -> list[dict]:
    """PERP2 on one market: long after three down closes while the close is above its 100 day average."""
    dates = [b[0] for b in bars]
    o = [b[1] for b in bars]; h = [b[2] for b in bars]; l = [b[3] for b in bars]; c = [b[4] for b in bars]
    n = len(bars)
    tr = [None] + [P1.true_range(h[i], l[i], c[i - 1]) for i in range(1, n)]
    trades, pos, pending = [], None, None

    def close_pos(i: int, price: float, stopped: bool) -> None:
        nonlocal pos
        days = max(1, (datetime.strptime(dates[i], "%Y-%m-%d") - datetime.strptime(pos["entry_date"], "%Y-%m-%d")).days)
        trades.append({"market": market, "side": 1, "entry_i": pos["entry_i"], "exit_i": i, "entry_date": pos["entry_date"], "exit_date": dates[i], "entry": pos["entry"], "exit": price,
                       "days": days, "gross": price / pos["entry"] - 1.0, "stopped": stopped, "stop_dist": pos["stop_dist"]})
        pos = None

    for i in range(n):
        if pending:
            act, pending = pending, None
            if act.get("exit") and pos:
                close_pos(i, o[i], False)
            if act.get("enter") and pos is None:
                atr = act["atr"]
                pos = {"entry": o[i], "entry_i": i, "entry_date": dates[i], "stop": o[i] - STOP_ATR2 * atr, "stop_dist": STOP_ATR2 * atr / o[i]}
        if pos and l[i] <= pos["stop"]:
            close_pos(i, o[i] if o[i] <= pos["stop"] else pos["stop"], True)
        if i >= max(SMA_N, DOWN_DAYS + 1, P1.ATR_N):
            if pos:
                if c[i] > max(c[i - EXIT_HI:i]) or (i - pos["entry_i"]) >= MAX_HOLD2:
                    pending = {"exit": True}
            else:
                sma = st.mean(c[i - SMA_N + 1:i + 1])
                down = all(c[i - k] < c[i - k - 1] for k in range(DOWN_DAYS))
                if c[i] > sma and down:
                    pending = {"enter": True, "atr": st.mean(tr[i - P1.ATR_N + 1:i + 1])}
    return trades


def pair_trades(gold: list, silver: list) -> list[dict]:
    """PERP3: the gold to silver ratio against its 60 day range, two legs of equal dollars; r is per $1 of each leg."""
    sd_ = {b[0]: b for b in silver}
    rows = [(g, sd_[g[0]]) for g in gold if g[0] in sd_]
    dates = [g[0] for g, s in rows]
    go = [g[1] for g, s in rows]; gc = [g[4] for g, s in rows]
    so = [s[1] for g, s in rows]; sc = [s[4] for g, s in rows]
    ratio = [gc[i] / sc[i] for i in range(len(rows))]
    n = len(rows)
    trades, pos, pending = [], None, None

    def close_pos(i: int) -> None:
        nonlocal pos
        days = max(1, (datetime.strptime(dates[i], "%Y-%m-%d") - datetime.strptime(pos["entry_date"], "%Y-%m-%d")).days)
        rg, rs = go[i] / pos["g"] - 1.0, so[i] / pos["s"] - 1.0
        trades.append({"market": "GOLD/SILVER", "side": pos["side"], "entry_i": pos["entry_i"], "exit_i": i, "entry_date": pos["entry_date"], "exit_date": dates[i], "days": days,
                       "gross": pos["side"] * (rg - rs), "stopped": pos["stopped"], "stop_dist": 0.02})
        pos = None

    for i in range(n):
        if pending:
            act, pending = pending, None
            if act.get("exit") and pos:
                pos["stopped"] = act.get("stopped", False)
                close_pos(i)
            if act.get("enter") and pos is None:
                pos = {"side": act["enter"], "g": go[i], "s": so[i], "entry_i": i, "entry_date": dates[i], "stopped": False}
        if i >= ZWIN - 1:
            w = ratio[i - ZWIN + 1:i + 1]
            sd = st.pstdev(w)
            if sd <= 0:
                continue
            z = (ratio[i] - st.mean(w)) / sd
            if pos:
                crossed = (pos["side"] == -1 and z <= 0) or (pos["side"] == 1 and z >= 0)
                if crossed or abs(z) >= Z_STOP or (i - pos["entry_i"]) >= MAX_HOLD3:
                    pending = {"exit": True, "stopped": abs(z) >= Z_STOP}
            elif z > Z_ENTRY:
                pending = {"enter": -1}
            elif z < -Z_ENTRY:
                pending = {"enter": 1}
    return trades


def leg_mult(t: dict) -> int:
    return 2 if t["market"] == "GOLD/SILVER" else 1


def net(t: dict, mult: float = 1.0) -> float:
    return t["gross"] - leg_mult(t) * P1.cost(t["days"], mult)


def placebo(series_by: dict, trades: list[dict], reps: int = P1.PLACEBO_REPS, seed: int = 11) -> list[float]:
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        tot = 0.0
        for t in trades:
            hold = t["exit_i"] - t["entry_i"]
            if t["market"] == "GOLD/SILVER":
                rows = series_by["GOLD/SILVER"]
                j = rng.randrange(P1.N_ENTRY, len(rows) - hold - 1)
                (g0, s0, _d0), (g1, s1, _d1) = rows[j], rows[j + hold]
                days = max(1, (datetime.strptime(rows[j + hold][2], "%Y-%m-%d") - datetime.strptime(rows[j][2], "%Y-%m-%d")).days)
                tot += t["side"] * ((g1 / g0 - 1.0) - (s1 / s0 - 1.0)) - 2 * P1.cost(days)
            else:
                bars = series_by[t["market"]]
                j = rng.randrange(P1.N_ENTRY, len(bars) - hold - 1)
                days = max(1, (datetime.strptime(bars[j + hold][0], "%Y-%m-%d") - datetime.strptime(bars[j][0], "%Y-%m-%d")).days)
                tot += (bars[j + hold][1] / bars[j][1] - 1.0) - P1.cost(days)
        out.append(tot / len(trades))
    return out


def verdict(name: str, trades: list[dict], pl: list[float]) -> tuple[str, dict]:
    spec = SPEC[name]
    n = len(trades)
    years = {t["entry_date"][:4] for t in trades}
    if n < spec["min_trades"] or len(years) < spec["min_years"]:
        return "NOT_ENOUGH_DATA", {"n": n, "years": len(years)}
    nets = [net(t) for t in trades]
    mean, se, z = cluster_mean_z([(t["entry_date"][:7], r) for t, r in zip(trades, nets)])
    mid = sorted(t["entry_date"] for t in trades)[n // 2]
    h1 = [r for t, r in zip(trades, nets) if t["entry_date"] < mid]
    h2 = [r for t, r in zip(trades, nets) if t["entry_date"] >= mid]
    m1, m2 = (st.mean(h1) if h1 else 0.0), (st.mean(h2) if h2 else 0.0)
    stress = st.mean(net(t, P1.STRESS) for t in trades)
    p95 = sorted(pl)[int(0.95 * (len(pl) - 1))] if pl else float("inf")
    ok = mean > 0 and z >= Z_BAR2 and m1 > 0 and m2 > 0 and stress > 0 and mean > p95
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"n": n, "years": len(years), "mean": mean, "se": se, "z": z, "h1": m1, "h2": m2, "stress": stress, "p95": p95, "mde": Z_BAR2 * se}


def run(name: str) -> None:
    out = DATA_DIR / f"perp2_result_{name}.txt"
    if out.exists():
        sys.exit(f"{name} has been run once already ({out}). A second read is only for a crash fix, and the file is deleted on purpose first.")
    bars_by = json.loads(P1.BARS_FILE.read_text())
    silver = json.loads(SILVER_FILE.read_text())
    if name == "PERP2":
        trades = []
        for m, b in bars_by.items():
            trades += dip_trades(b, m)
        series_by = bars_by
    else:
        trades = pair_trades(bars_by["GOLD"], silver)
        sd_ = {b[0]: b for b in silver}
        series_by = {"GOLD/SILVER": [(g[1], sd_[g[0]][1], g[0]) for g in bars_by["GOLD"] if g[0] in sd_]}
    trades.sort(key=lambda t: t["entry_date"])
    pl = placebo(series_by, trades) if trades else []
    v, s = verdict(name, trades, pl)
    pc = lambda x: f"{x * 100:+.2f}%"
    L = [f"{name}: {len(trades)} trades."]
    if "mean" in s:
        L.append(f"{name}: n={s['n']} over {s['years']} years, mean net {pc(s['mean'])} per trade, z {s['z']:+.2f}, halves {pc(s['h1'])} / {pc(s['h2'])}, costs x{P1.STRESS} {pc(s['stress'])}, "
                 f"placebo 95th percentile {pc(s['p95'])} -> {v}")
        L.append(f"    minimum detectable edge {pc(s['mde'])}")
    else:
        L.append(f"{name}: n={s['n']} over {s['years']} years -> {v}")
    L.append("Per market (information):")
    for m in sorted({t["market"] for t in trades}):
        mt = [t for t in trades if t["market"] == m]
        extra = ""
        if name == "PERP2":
            extra = f"  buy and hold {pc(bars_by[m][-1][4] / bars_by[m][0][4] - 1.0)}"
        L.append(f"  {m:<12} trades {len(mt):>4}  mean net {pc(st.mean(net(t) for t in mt)):>8}  win rate {sum(1 for t in mt if net(t) > 0) / len(mt) * 100:3.0f}%  stopped {sum(1 for t in mt if t['stopped']) / len(mt) * 100:3.0f}%  "
                 f"avg hold {st.mean(t['days'] for t in mt):4.1f} days{extra}")
    if name == "PERP3":
        for side, label in ((1, "long gold / short silver"), (-1, "short gold / long silver")):
            ss = [t for t in trades if t["side"] == side]
            if ss:
                L.append(f"  {label:<26} trades {len(ss):>3}  mean net {pc(st.mean(net(t) for t in ss))}")
    L.append("Per calendar year of entry (information):")
    by_year = defaultdict(list)
    for t in trades:
        by_year[t["entry_date"][:4]].append(net(t))
    for y in sorted(by_year):
        L.append(f"  {y}: {len(by_year[y]):>3} trades, mean net {pc(st.mean(by_year[y]))}")
    text = "\n".join(L)
    print(text)
    out.write_text(text + "\n")


if __name__ == "__main__":
    if sys.argv[1:2] == ["fetch"]:
        fetch()
    elif sys.argv[1:2] == ["run"] and sys.argv[2:3] and sys.argv[2] in SPEC:
        run(sys.argv[2])
    else:
        sys.exit("usage: python -m scalper.perp2 fetch | run PERP2|PERP3")
