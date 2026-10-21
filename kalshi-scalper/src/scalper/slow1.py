"""SLOW1 (README, Pre-registration: SLOW1): monthly time-series trend on nine liquid ETFs, long or cash.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.slow1 fetch   then   python -m scalper.slow1 run
The rule, costs and bar were written in the README before this file existed. `run` writes a result file and refuses a second run unless it is
deleted on purpose (a crash fix, never a chase for a pass).
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
import urllib.request

from .paths import DATA_DIR

BARS_FILE = DATA_DIR / "slow1_bars.json"
RESULT_FILE = DATA_DIR / "slow1_result.txt"
ETFS = ["SPY", "QQQ", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "UUP"]
START = "2007-03-01"
CELLS = {"S1": 252, "S2": 126, "S3": 63}
COST_SIDE, STRESS = 0.0005, 1.2
MIN_MONTHS, Z_BAR, PLACEBO_REPS, NW_LAGS = 120, 2.5, 200, 3


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    out = {}
    for s in ETFS:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1d&period1=0&period2={int(time.time())}"
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
        ac = res["indicators"]["adjclose"][0]["adjclose"]
        out[s] = {time.strftime("%Y-%m-%d", time.gmtime(t)): c for t, c in zip(res["timestamp"], ac) if c and c > 0}
        print(f"{s}: {len(out[s])} bars", flush=True)
    BARS_FILE.write_text(json.dumps(out))


def common_calendar(bars: dict) -> list[str]:
    dates = set.intersection(*(set(b) for b in bars.values()))
    return sorted(d for d in dates if d >= START)


def month_ends(dates: list[str]) -> list[int]:
    """Index of each month's last trading day (the signal day)."""
    return [i for i in range(len(dates) - 1) if dates[i][:7] != dates[i + 1][:7]]


def monthly_rows(bars: dict, dates: list[str], lookback: int) -> list[dict]:
    """One row per month: date, per-ETF invested flag (signal uses closes up to the signal day only), per-ETF return from the
    NEXT day's close after the signal to the next day's close after the following month end."""
    px = {s: [bars[s][d] for d in dates] for s in ETFS}
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < lookback or j + 1 >= len(dates):
            continue
        rows.append({
            "date": dates[i],
            "flag": {s: px[s][i] / px[s][i - lookback] - 1 > 0 for s in ETFS},
            "ret": {s: px[s][j + 1] / px[s][i + 1] - 1 for s in ETFS},
        })
    return rows


def strategy_series(rows: list[dict], flags: list[dict], cost_mult: float = 1.0) -> tuple[list[float], list[float]]:
    """(timed net monthly returns s, buy-and-hold monthly returns b). Cash earns zero; cost per side on traded weight."""
    n = len(ETFS)
    prev = {s: 0.0 for s in ETFS}
    s_out, b_out = [], []
    for row, fl in zip(rows, flags):
        w = {s: (1.0 / n if fl[s] else 0.0) for s in ETFS}
        turn = sum(abs(w[s] - prev[s]) for s in ETFS)
        s_out.append(sum(w[s] * row["ret"][s] for s in ETFS) - turn * COST_SIDE * cost_mult)
        b_out.append(sum(row["ret"][s] for s in ETFS) / n)
        prev = w
    return s_out, b_out


def ols_nw(y: list[float], x: list[float], lags: int = NW_LAGS) -> tuple[float, float, float]:
    """(intercept, beta, Newey-West z of the intercept) for y = a + b x."""
    n = len(y)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    beta = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx if sxx > 0 else 0.0
    alpha = my - beta * mx
    e = [b - alpha - beta * a for a, b in zip(x, y)]
    # sandwich: (X'X)^-1 S (X'X)^-1 with X = [1, x]
    sx = sum(x)
    xtx = [[n, sx], [sx, sum(v * v for v in x)]]
    det = xtx[0][0] * xtx[1][1] - xtx[0][1] * xtx[1][0]
    inv = [[xtx[1][1] / det, -xtx[0][1] / det], [-xtx[1][0] / det, xtx[0][0] / det]]
    g = [[e[t], e[t] * x[t]] for t in range(n)]

    def gamma(l: int):
        m = [[0.0, 0.0], [0.0, 0.0]]
        for t in range(l, n):
            for a in range(2):
                for b in range(2):
                    m[a][b] += g[t][a] * g[t - l][b]
        return m

    s_mat = gamma(0)
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        gl = gamma(l)
        for a in range(2):
            for b in range(2):
                s_mat[a][b] += w * (gl[a][b] + gl[b][a])
    v00 = sum(inv[0][a] * s_mat[a][b] * inv[b][0] for a in range(2) for b in range(2))
    se = math.sqrt(v00) if v00 > 0 else float("inf")
    return alpha, beta, alpha / se


def alpha_only(y: list[float], x: list[float]) -> float:
    n = len(y)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    beta = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx if sxx > 0 else 0.0
    return my - beta * mx


def max_drawdown(r: list[float]) -> float:
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in r:
        eq *= 1 + v
        peak = max(peak, eq)
        dd = min(dd, eq / peak - 1)
    return dd


def stats(r: list[float]) -> dict:
    n = len(r)
    m = sum(r) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in r) / (n - 1))
    eq = 1.0
    for v in r:
        eq *= 1 + v
    return {"ann_return": eq ** (12 / n) - 1, "ann_vol": sd * math.sqrt(12), "sharpe": (m * 12) / (sd * math.sqrt(12)) if sd else 0.0, "max_dd": max_drawdown(r)}


def judge_cell(name: str, rows: list[dict], seed: int = 1) -> dict:
    flags = [row["flag"] for row in rows]
    s, b = strategy_series(rows, flags)
    s2, _ = strategy_series(rows, flags, STRESS)
    n = len(s)
    a, beta, z = ols_nw(s, b)
    half = n // 2
    a_h1, a_h2 = alpha_only(s[:half], b[:half]), alpha_only(s[half:], b[half:])
    idx22 = [i for i, row in enumerate(rows) if row["date"] >= "2022-01-01"]
    a_22 = alpha_only([s[i] for i in idx22], [b[i] for i in idx22]) if len(idx22) > 12 else float("nan")
    a_stress = alpha_only(s2, b)
    rng = random.Random(seed)
    k = {e: sum(1 for f in flags if f[e]) for e in ETFS}
    placebo = []
    for _ in range(PLACEBO_REPS):
        pick = {e: set(rng.sample(range(n), k[e])) for e in ETFS}
        pf = [{e: (i in pick[e]) for e in ETFS} for i in range(n)]
        ps, _ = strategy_series(rows, pf)
        placebo.append(alpha_only(ps, b))
    placebo.sort()
    p95 = placebo[int(0.95 * PLACEBO_REPS) - 1]
    by_year = {}
    for y in sorted({row["date"][:4] for row in rows}):
        ix = [i for i, row in enumerate(rows) if row["date"][:4] == y]
        by_year[y] = round(sum(s[i] - beta * b[i] for i in ix) / len(ix) * 12 - 0.0, 4) if len(ix) > 1 else None
    checks = {"months>=120": n >= MIN_MONTHS, "alpha>0": a > 0, f"z>={Z_BAR}": z >= Z_BAR, "both_halves>0": a_h1 > 0 and a_h2 > 0,
              "2022_on>0": a_22 > 0, "stress>0": a_stress > 0, "above_placebo_p95": a > p95}
    if n < MIN_MONTHS:
        verdict = "NOT_ENOUGH_DATA"
    else:
        verdict = "NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED"
    return {"cell": name, "months": n, "alpha_ann": a * 12, "beta": beta, "nw_z": z, "alpha_h1_ann": a_h1 * 12, "alpha_h2_ann": a_h2 * 12,
            "alpha_2022on_ann": a_22 * 12, "alpha_stress_ann": a_stress * 12, "placebo_p95_ann": p95 * 12, "checks": checks, "verdict": verdict,
            "dollars_per_year_on_200": round(a * 12 * 200, 2), "timed": stats(s), "buyhold": stats(b),
            "avg_share_invested": sum(sum(f.values()) for f in flags) / (n * len(ETFS)), "alpha_by_year_ann": by_year}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: SLOW1 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    dates = common_calendar(bars)
    out = [f"SLOW1 sample {dates[0]} to {dates[-1]} ({len(dates)} common days)"]
    for name, lb in CELLS.items():
        res = judge_cell(name, monthly_rows(bars, dates, lb))
        out.append(json.dumps(res, indent=1, default=str))
    text = "\n".join(out)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
