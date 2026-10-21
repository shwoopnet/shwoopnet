"""LQ1 (README, Pre-registration: LQ1): volatility-managed QLD (a 2x QQQ fund) scored against buy-and-hold QQQ. Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.lq1 fetch   (QLD; QQQ comes from `python -m scalper.vm fetch`)   then   python -m scalper.lq1 run   (once; a second run is refused unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import random
import sys
import time
import urllib.request

from .fund1 import nw_mean_z
from .paths import DATA_DIR
from .slow1 import month_ends, stats
from .vm import COST_SIDE, STRESS, realised_vol

QLD_FILE = DATA_DIR / "lq1_qld.json"
QQQ_FILE = DATA_DIR / "vm_bars.json"
RESULT_FILE = DATA_DIR / "lq1_result.txt"
TARGET, VOL_DAYS, MIN_MONTHS, Z_BAR, PLACEBO_REPS = 0.20, 21, 120, 2.8, 200


def fetch() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/QLD?interval=1d&period1=0&period2={int(time.time())}"
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
    out = {time.strftime("%Y-%m-%d", time.gmtime(t)): c for t, c in zip(res["timestamp"], ac) if c and c > 0}
    QLD_FILE.write_text(json.dumps(out))
    d = sorted(out)
    print(f"QLD: {len(out)} bars {d[0]} to {d[-1]}")


def monthly(dates: list[str], qld: list[float], qqq: list[float]) -> list[dict]:
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < VOL_DAYS or j + 1 >= len(dates):
            continue
        v = realised_vol(qld, i)
        rows.append({"date": dates[i], "w": min(1.0, TARGET / v) if v > 0 else 1.0, "ret": qld[j + 1] / qld[i + 1] - 1, "qqq": qqq[j + 1] / qqq[i + 1] - 1})
    return rows


def score(rows: list[dict], w: list[float], cost_mult: float = 1.0) -> list[float]:
    prev, out = 0.0, []
    for r, x in zip(rows, w):
        out.append(x * r["ret"] - abs(x - prev) * COST_SIDE * cost_mult)
        prev = x
    return out


def drawdown(r: list[float]) -> float:
    return stats(r)["max_dd"]


def judge(rows: list[dict]) -> dict:
    w = [r["w"] for r in rows]
    s, s2 = score(rows, w), score(rows, w, STRESS)
    b = [r["qqq"] for r in rows]
    n = len(s)
    ex = [x - y for x, y in zip(s, b)]
    m, z = nw_mean_z(ex)
    half = n // 2
    h1, h2 = sum(ex[:half]) / half, sum(ex[half:]) / (n - half)
    stress_ex = sum(x - y for x, y in zip(s2, b)) / n
    rng = random.Random(1)
    pl = []
    for _ in range(PLACEBO_REPS):
        ww = w[:]
        rng.shuffle(ww)
        pl.append(sum(x - y for x, y in zip(score(rows, ww), b)) / n)
    p95 = sorted(pl)[int(0.95 * PLACEBO_REPS) - 1]
    dd_s, dd_b = drawdown(s), drawdown(b)
    checks = {"months>=120": n >= MIN_MONTHS, "excess>0": m > 0, f"z>={Z_BAR}": z >= Z_BAR, "both_halves>0": h1 > 0 and h2 > 0, "stress>0": stress_ex > 0,
              "above_placebo_p95": m > p95, "drawdown_no_worse_than_QQQ": dd_s >= dd_b}
    verdict = "NOT_ENOUGH_DATA" if n < MIN_MONTHS else ("NOT_YET_FALSIFIED" if all(checks.values()) else "FALSIFIED")
    return {"verdict": verdict, "checks": checks, "months": n, "first": rows[0]["date"], "excess_ann": m * 12, "nw_z": z, "excess_h1_ann": h1 * 12, "excess_h2_ann": h2 * 12,
            "excess_stress_ann": stress_ex * 12, "placebo_p95_ann": p95 * 12, "managed": stats(s), "qqq": stats(b), "qld_buy_hold": stats([r["ret"] for r in rows]),
            "mean_weight": sum(w) / n, "dollars_per_year_200_500": [round(m * 12 * 200, 2), round(m * 12 * 500, 2)]}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: LQ1 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    qld, qqq = json.loads(QLD_FILE.read_text()), json.loads(QQQ_FILE.read_text())["QQQ"]
    dates = sorted(set(qld) & set(qqq))
    rows = monthly(dates, [qld[d] for d in dates], [qqq[d] for d in dates])
    text = json.dumps(judge(rows), indent=1, default=str)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
