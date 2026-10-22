"""CM1 and VT1 (README, Pre-registration: CM1 and VT1): cross-country momentum on 17 iShares country ETFs, and short volatility (SVXY) only when VIX / VIX3M is below 0.95.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.fam5 run   (reads data/fam5_bars.json and data/slow1_bars.json; once, a second run is refused unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import random
import sys

from . import sect1
from .paths import DATA_DIR
from .slow1 import alpha_only, ols_nw, stats

BARS_FILE, SPY_FILE, RESULT_FILE = DATA_DIR / "fam5_bars.json", DATA_DIR / "slow1_bars.json", DATA_DIR / "fam5_result.txt"
COUNTRIES = ["EWA", "EWC", "EWG", "EWH", "EWI", "EWJ", "EWK", "EWL", "EWM", "EWN", "EWO", "EWP", "EWQ", "EWS", "EWD", "EWU", "EWW"]
CM_TOP, CM_COST, Z_BAR, PLACEBO_REPS = 5, 0.0008, 3.0, 200
VT_THRESHOLD, VT_COST, VT_LAGS, VT_MIN_DAYS, STRESS = 0.95, 0.0006, 10, 2500, 1.2


def vt_positions(flags: list[bool]) -> list[bool]:
    """Position held over day u comes from the signal at day u-2's close (signal, then the next close fill, then the day's return)."""
    return [False, False] + flags[:-2]


def vt_series(ret: list[float], flags: list[bool], mult: float = 1.0) -> list[float]:
    pos, prev, out = vt_positions(flags), False, []
    for r, p in zip(ret, pos):
        out.append((r if p else 0.0) - (VT_COST * mult if p != prev else 0.0))
        prev = p
    return out


def drawdown(r: list[float]) -> float:
    eq, peak, dd = 1.0, 1.0, 0.0
    for v in r:
        eq *= 1 + v
        peak = max(peak, eq)
        dd = min(dd, eq / peak - 1)
    return dd


def run_cm(bars: dict) -> dict:
    sect1.SECTORS, sect1.TOP_N, sect1.COST_SIDE, sect1.Z_BAR = COUNTRIES, CM_TOP, CM_COST, Z_BAR
    dates = sorted(set.intersection(*(set(bars[c]) for c in COUNTRIES)))
    res = sect1.judge_cell("CM1", sect1.monthly_rows({c: bars[c] for c in COUNTRIES}, dates, 252))
    res["dollars_per_year_200_500"] = [round(res["alpha_ann"] * 200, 2), round(res["alpha_ann"] * 500, 2)]
    return res


def run_vt(bars: dict, spy: dict) -> dict:
    dates = sorted(set(bars["SVXY"]) & set(bars["^VIX"]) & set(bars["^VIX3M"]) & set(spy))
    px = [bars["SVXY"][d] for d in dates]
    mkt = [spy[d] for d in dates]
    ret = [px[i] / px[i - 1] - 1 for i in range(1, len(dates))]
    bench = [mkt[i] / mkt[i - 1] - 1 for i in range(1, len(dates))]
    dd = dates[1:]
    flags = [bars["^VIX"][d] / bars["^VIX3M"][d] < VT_THRESHOLD for d in dd]
    s, s2 = vt_series(ret, flags), vt_series(ret, flags, STRESS)
    n = len(s)
    a, beta, z = ols_nw(s, bench, VT_LAGS)
    half = n // 2
    a1, a2 = alpha_only(s[:half], bench[:half]), alpha_only(s[half:], bench[half:])
    ix = [i for i, d in enumerate(dd) if d >= "2019-01-01"]
    a19 = alpha_only([s[i] for i in ix], [bench[i] for i in ix])
    a_st = alpha_only(s2, bench)
    pos = vt_positions(flags)
    k = sum(pos)
    rng = random.Random(1)
    pl = []
    for _ in range(PLACEBO_REPS):
        chosen = set(rng.sample(range(n), k))
        ps, prev = [], False
        for i, r in enumerate(ret):
            p = i in chosen
            ps.append((r if p else 0.0) - (VT_COST if p != prev else 0.0))
            prev = p
        pl.append(alpha_only(ps, bench))
    p95 = sorted(pl)[int(0.95 * PLACEBO_REPS) - 1]
    checks = {"days>=2500": n >= VT_MIN_DAYS, "alpha>0": a > 0, f"z>={Z_BAR}": z >= Z_BAR, "both_halves>0": a1 > 0 and a2 > 0, "2019_on>0": a19 > 0, "stress>0": a_st > 0, "above_placebo_p95": a > p95}
    verdict = "NOT_ENOUGH_DATA" if n < VT_MIN_DAYS else ("NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED")
    feb = dd.index("2018-02-05") if "2018-02-05" in dd else None
    return {"cell": "VT1", "verdict": verdict, "checks": checks, "days": n, "first": dd[0], "share_invested": k / n, "alpha_ann": a * 252, "beta": beta, "nw_z": z,
            "alpha_h1_ann": a1 * 252, "alpha_h2_ann": a2 * 252, "alpha_2019on_ann": a19 * 252, "alpha_stress_ann": a_st * 252, "placebo_p95_ann": p95 * 252,
            "strategy_max_drawdown": drawdown(s), "svxy_buy_hold_max_drawdown": drawdown(ret), "strategy": stats([sum(s[i:i + 21]) for i in range(0, n - 21, 21)]),
            "svxy_return_2018_02_05": None if feb is None else ret[feb], "strategy_return_2018_02_05": None if feb is None else s[feb], "position_2018_02_05": None if feb is None else vt_positions(flags)[feb],
            "dollars_per_year_200_500": [round(a * 252 * 200, 2), round(a * 252 * 500, 2)]}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: this is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    spy = json.loads(SPY_FILE.read_text())["SPY"]
    text = json.dumps([run_cm(bars), run_vt(bars, spy)], indent=1, default=str)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"run": run}[sys.argv[1]]()
