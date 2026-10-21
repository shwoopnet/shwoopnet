"""FUND1 (README, Pre-registration: FUND1): crypto cash-and-carry, long spot and short the perpetual, funding collected.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.fund1 run   (reads data/fund1_hl.json: Hyperliquid hourly funding for BTC and ETH)
`run` refuses a second run unless the result file is deleted on purpose.
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict

from .paths import DATA_DIR

FUND_FILE = DATA_DIR / "fund1_hl.json"
RESULT_FILE = DATA_DIR / "fund1_result.txt"
COINS = ["BTC", "ETH"]
COST = 0.0012 * 2 + 0.0025 * 2 + 0.0005 * 4   # perp fee, spot fee, spread: 0.94% round trip
STRESS, MIN_MONTHS, Z_BAR, NW_LAGS, MARGIN = 1.2, 36, 2.1, 3, 1.2


def nw_mean_z(y: list[float], lags: int = NW_LAGS) -> tuple[float, float]:
    n = len(y)
    m = sum(y) / n
    e = [v - m for v in y]
    s = sum(v * v for v in e)
    for l in range(1, lags + 1):
        s += 2 * (1 - l / (lags + 1)) * sum(e[t] * e[t - l] for t in range(l, n))
    se = math.sqrt(s) / n if s > 0 else float("inf")
    return m, m / se


def monthly(rows: list[list[float]]) -> dict[str, float]:
    """Sum of hourly funding rates by calendar month (positive: shorts earn)."""
    out: dict[str, float] = defaultdict(float)
    cnt: dict[str, int] = defaultdict(int)
    for t, r, _ in rows:
        k = time.strftime("%Y-%m", time.gmtime(t / 1000))
        out[k] += r
        cnt[k] += 1
    return {k: v for k, v in out.items() if cnt[k] >= 24 * 28}   # full months only


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: FUND1 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    raw = json.loads(FUND_FILE.read_text())
    per = {c: monthly(raw[c]) for c in COINS}
    months = sorted(set.intersection(*(set(per[c]) for c in COINS)))
    months = [m for m in months if "2023-06" <= m <= "2026-09"]
    basket = [sum(per[c][m] for c in COINS) / len(COINS) for m in months]
    n = len(months)

    def net(cost_mult: float, idx):
        hurdle = COST * cost_mult / 12
        return [basket[i] - hurdle for i in idx]

    allx = list(range(n))
    h1, h2, last12 = list(range(n // 2)), list(range(n // 2, n)), list(range(n - 12, n))
    m_all, z_all = nw_mean_z(net(1.0, allx))
    m_h1 = sum(net(1.0, h1)) / len(h1)
    m_h2 = sum(net(1.0, h2)) / len(h2)
    m_12 = sum(net(1.0, last12)) / 12
    m_st = sum(net(STRESS, allx)) / n
    checks = {"months>=36": n >= MIN_MONTHS, "net>0": m_all > 0, f"z>={Z_BAR}": z_all >= Z_BAR, "both_halves>0": m_h1 > 0 and m_h2 > 0,
              "last12>0": m_12 > 0, "stress>0": m_st > 0}
    verdict = "NOT_ENOUGH_DATA" if n < MIN_MONTHS else ("NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED")
    by_year = defaultdict(list)
    for m, v in zip(months, basket):
        by_year[m[:4]].append(v)
    by_coin_year = {c: {y: round(sum(per[c][m] for m in months if m[:4] == y) / sum(1 for m in months if m[:4] == y) * 12, 4) for y in sorted(by_year)} for c in COINS}
    # 30 day windows (rolling by calendar month sums is coarse; use the hourly basket for the share of negative 30 day windows)
    hours = list(zip(*[[r[1] for r in raw[c]] for c in COINS]))
    hb = [sum(h) / len(COINS) for h in hours]
    w = 24 * 30
    wins = [sum(hb[i:i + w]) for i in range(0, len(hb) - w, 24)]
    res = {"verdict": verdict, "checks": checks, "months": n, "first": months[0], "last": months[-1],
           "gross_ann": sum(basket) / n * 12, "net_monthly_mean": m_all, "net_ann": m_all * 12, "nw_z": z_all, "net_ann_h1": m_h1 * 12, "net_ann_h2": m_h2 * 12,
           "net_ann_last12": m_12 * 12, "net_ann_stress": m_st * 12, "gross_ann_by_year": {y: round(sum(v) / len(v) * 12, 4) for y, v in by_year.items()},
           "gross_ann_by_coin_year": by_coin_year, "share_30d_windows_negative": sum(1 for x in wins if x < 0) / len(wins), "worst_30d_gross": min(wins),
           "break_even_months_at_base_cost": COST / (sum(basket) / n), "dollars_per_year": {k: round(m_all * 12 * k / MARGIN, 2) for k in (200, 500)},
           "cost_round_trip": COST}
    text = json.dumps(res, indent=1)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"run": run}[sys.argv[1]]()
