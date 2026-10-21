"""SECT1 (README, Pre-registration: SECT1): sector momentum, top 3 of the nine original SPDR sector ETFs, held a month.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.sect1 fetch   then   python -m scalper.sect1 run
The rule, costs and bar were written in the README before this file existed. `run` refuses a second run unless the result file is deleted on purpose.
"""
from __future__ import annotations

import json
import random
import sys
import time
import urllib.request

from .paths import DATA_DIR
from .slow1 import alpha_only, month_ends, ols_nw, stats

BARS_FILE = DATA_DIR / "sect1_bars.json"
RESULT_FILE = DATA_DIR / "sect1_result.txt"
SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
CELLS = {"C1": 252, "C2": 126}
SKIP, TOP_N, COST_SIDE, STRESS = 21, 3, 0.0005, 1.2
MIN_MONTHS, Z_BAR, PLACEBO_REPS = 120, 2.6, 200


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    out = {}
    for s in SECTORS:
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


def monthly_rows(bars: dict, dates: list[str], lookback: int) -> list[dict]:
    """Per month: the top-3 picks (ranked on closes up to the signal day only) and every sector's return from the NEXT day's close after the
    signal to the next day's close after the following month end."""
    px = {s: [bars[s][d] for d in dates] for s in SECTORS}
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < lookback or j + 1 >= len(dates):
            continue
        score = {s: px[s][i - SKIP] / px[s][i - lookback] - 1 for s in SECTORS}
        picks = sorted(SECTORS, key=lambda s: (-score[s], s))[:TOP_N]
        rows.append({"date": dates[i], "picks": picks, "ret": {s: px[s][j + 1] / px[s][i + 1] - 1 for s in SECTORS}})
    return rows


def series(rows: list[dict], picks: list[list[str]], cost_mult: float = 1.0) -> tuple[list[float], list[float]]:
    n = len(SECTORS)
    prev = {s: 0.0 for s in SECTORS}
    s_out, b_out = [], []
    for row, pk in zip(rows, picks):
        w = {s: (1.0 / TOP_N if s in pk else 0.0) for s in SECTORS}
        turn = sum(abs(w[s] - prev[s]) for s in SECTORS)
        s_out.append(sum(w[s] * row["ret"][s] for s in SECTORS) - turn * COST_SIDE * cost_mult)
        b_out.append(sum(row["ret"][s] for s in SECTORS) / n)
        prev = w
    return s_out, b_out


def judge_cell(name: str, rows: list[dict], seed: int = 1) -> dict:
    picks = [r["picks"] for r in rows]
    s, b = series(rows, picks)
    s2, _ = series(rows, picks, STRESS)
    n = len(s)
    a, beta, z = ols_nw(s, b)
    half = n // 2
    a_h1, a_h2 = alpha_only(s[:half], b[:half]), alpha_only(s[half:], b[half:])
    ix = [i for i, r in enumerate(rows) if r["date"] >= "2019-01-01"]
    a_19 = alpha_only([s[i] for i in ix], [b[i] for i in ix]) if len(ix) > 12 else float("nan")
    a_st = alpha_only(s2, b)
    rng = random.Random(seed)
    placebo = []
    for _ in range(PLACEBO_REPS):
        ps, _ = series(rows, [rng.sample(SECTORS, TOP_N) for _ in range(n)])
        placebo.append(alpha_only(ps, b))
    placebo.sort()
    p95 = placebo[int(0.95 * PLACEBO_REPS) - 1]
    by_year = {}
    for y in sorted({r["date"][:4] for r in rows}):
        k = [i for i, r in enumerate(rows) if r["date"][:4] == y]
        by_year[y] = round(sum(s[i] - beta * b[i] for i in k) / len(k) * 12, 4)
    held = {e: sum(1 for p in picks if e in p) / n for e in SECTORS}
    checks = {"months>=120": n >= MIN_MONTHS, "alpha>0": a > 0, f"z>={Z_BAR}": z >= Z_BAR, "both_halves>0": a_h1 > 0 and a_h2 > 0,
              "2019_on>0": a_19 > 0, "stress>0": a_st > 0, "above_placebo_p95": a > p95}
    verdict = "NOT_ENOUGH_DATA" if n < MIN_MONTHS else ("NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED")
    return {"cell": name, "first_signal": rows[0]["date"], "months": n, "alpha_ann": a * 12, "beta": beta, "nw_z": z, "alpha_h1_ann": a_h1 * 12,
            "alpha_h2_ann": a_h2 * 12, "alpha_2019on_ann": a_19 * 12, "alpha_stress_ann": a_st * 12, "placebo_p95_ann": p95 * 12, "checks": checks,
            "verdict": verdict, "dollars_per_year_on_200": round(a * 12 * 200, 2), "dollars_per_year_on_500": round(a * 12 * 500, 2),
            "held": s and {k: round(v, 3) for k, v in held.items()}, "picked": stats(s), "equal_weight": stats(b), "alpha_by_year_ann": by_year}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: SECT1 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    dates = sorted(set.intersection(*(set(b) for b in bars.values())))
    out = [f"SECT1 sample {dates[0]} to {dates[-1]} ({len(dates)} common days)"]
    for name, lb in CELLS.items():
        out.append(json.dumps(judge_cell(name, monthly_rows(bars, dates, lb)), indent=1, default=str))
    text = "\n".join(out)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
