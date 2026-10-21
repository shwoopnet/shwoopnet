"""VM (README, Pre-registration: VM): volatility-managed SPY and QQQ, and USMV against SPY. Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.vm fetch   then   python -m scalper.vm run     (`run` refuses a second run unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
import urllib.request

from .paths import DATA_DIR
from .slow1 import alpha_only, month_ends, ols_nw, stats

BARS_FILE = DATA_DIR / "vm_bars.json"
RESULT_FILE = DATA_DIR / "vm_result.txt"
SYMS = ["SPY", "QQQ", "USMV"]
TARGET, VOL_DAYS, COST_SIDE, STRESS = 0.10, 21, 0.0005, 1.2
MIN_MONTHS, Z_BAR, PLACEBO_REPS = 120, 2.7, 200


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    out = {}
    for s in SYMS:
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


def realised_vol(px: list[float], i: int, n: int = VOL_DAYS) -> float:
    """Annualised standard deviation of the last n daily returns ending at index i (closes up to and including i)."""
    r = [px[k] / px[k - 1] - 1 for k in range(i - n + 1, i + 1)]
    m = sum(r) / n
    return math.sqrt(sum((v - m) ** 2 for v in r) / (n - 1)) * math.sqrt(252)


def managed_rows(dates: list[str], px: list[float]) -> list[dict]:
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < VOL_DAYS or j + 1 >= len(dates):
            continue
        v = realised_vol(px, i)
        rows.append({"date": dates[i], "w": min(1.0, TARGET / v) if v > 0 else 1.0, "ret": px[j + 1] / px[i + 1] - 1})
    return rows


def managed_series(rows: list[dict], weights: list[float], cost_mult: float = 1.0) -> tuple[list[float], list[float]]:
    prev = 0.0
    s, b = [], []
    for r, w in zip(rows, weights):
        s.append(w * r["ret"] - abs(w - prev) * COST_SIDE * cost_mult)
        b.append(r["ret"])
        prev = w
    return s, b


def judge(name: str, dates: list[str], s: list[float], b: list[float], s_stress: list[float], placebo: list[float] | None, extra: dict) -> dict:
    n = len(s)
    a, beta, z = ols_nw(s, b)
    half = n // 2
    a1, a2 = alpha_only(s[:half], b[:half]), alpha_only(s[half:], b[half:])
    ix = [i for i, d in enumerate(dates) if d >= "2019-01-01"]
    a19 = alpha_only([s[i] for i in ix], [b[i] for i in ix]) if len(ix) > 12 else float("nan")
    ast = alpha_only(s_stress, b)
    p95 = sorted(placebo)[int(0.95 * len(placebo)) - 1] if placebo else None
    checks = {"months>=120": n >= MIN_MONTHS, "alpha>0": a > 0, f"z>={Z_BAR}": z >= Z_BAR, "both_halves>0": a1 > 0 and a2 > 0, "2019_on>0": a19 > 0, "stress>0": ast > 0}
    if p95 is not None:
        checks["above_placebo_p95"] = a > p95
    verdict = "NOT_ENOUGH_DATA" if n < MIN_MONTHS else ("NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED")
    return {"cell": name, "months": n, "first": dates[0], "alpha_ann": a * 12, "beta": beta, "nw_z": z, "alpha_h1_ann": a1 * 12, "alpha_h2_ann": a2 * 12,
            "alpha_2019on_ann": a19 * 12, "alpha_stress_ann": ast * 12, "placebo_p95_ann": None if p95 is None else p95 * 12, "checks": checks, "verdict": verdict,
            "dollars_per_year_200_500": [round(a * 12 * 200, 2), round(a * 12 * 500, 2)], "strategy": stats(s), "benchmark": stats(b), **extra}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: VM is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())
    out = []
    for name, sym in (("V1", "SPY"), ("V2", "QQQ")):
        dates = sorted(bars[sym])
        rows = managed_rows(dates, [bars[sym][d] for d in dates])
        w = [r["w"] for r in rows]
        s, b = managed_series(rows, w)
        s2, _ = managed_series(rows, w, STRESS)
        rng = random.Random(1)
        pl = []
        for _ in range(PLACEBO_REPS):
            ww = w[:]
            rng.shuffle(ww)
            ps, _ = managed_series(rows, ww)
            pl.append(alpha_only(ps, b))
        out.append(judge(name, [r["date"] for r in rows], s, b, s2, pl, {"mean_weight": sum(w) / len(w)}))
    common = sorted(set(bars["USMV"]) & set(bars["SPY"]))
    me = month_ends(common)
    u, b, d = [], [], []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if j + 1 >= len(common):
            continue
        u.append(bars["USMV"][common[j + 1]] / bars["USMV"][common[i + 1]] - 1)
        b.append(bars["SPY"][common[j + 1]] / bars["SPY"][common[i + 1]] - 1)
        d.append(common[i])
    one_off = 2 * COST_SIDE / len(u)          # entry and exit once, spread over the sample
    s = [x - one_off for x in u]
    s2 = [x - one_off * STRESS for x in u]
    out.append(judge("L1m", d, s, b, s2, None, {}))
    text = json.dumps(out, indent=1, default=str)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
