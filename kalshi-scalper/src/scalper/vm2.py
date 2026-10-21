"""VM2 (README, Pre-registration: VM2): a recovery rule (R1) and a walk-forward tree (T1) on top of volatility-managed QQQ, scored against buy-and-hold QQQ.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.vm2 run   (reads data/vm_bars.json from `python -m scalper.vm fetch`; refuses a second run unless the result file is deleted on purpose)
"""
from __future__ import annotations

import json
import random
import sys

from .fund1 import nw_mean_z
from .paths import DATA_DIR
from .slow1 import month_ends, stats
from .tree1 import cut_points, fit_tree, predict
from .vm import COST_SIDE, STRESS, TARGET, realised_vol

BARS_FILE = DATA_DIR / "vm_bars.json"
RESULT_FILE = DATA_DIR / "vm2_result.txt"
BURN_MONTHS, REFIT_EVERY, DEPTH, MIN_LEAF = 120, 12, 2, 40
DD_TRIGGER, VOL_RATIO_TRIGGER = 0.15, 0.8
Z_BAR, PLACEBO_REPS = 2.8, 100


def build_rows(dates: list[str], px: list[float]) -> list[dict]:
    me = month_ends(dates)
    rows = []
    for k in range(len(me) - 1):
        i, j = me[k], me[k + 1]
        if i < 252 or j + 1 >= len(dates):
            continue
        v21, v63 = realised_vol(px, i, 21), realised_vol(px, i, 63)
        hi = max(px[:i + 1])
        feats = [v21, px[i] / px[i - 21] - 1, px[i] / px[i - 63] - 1, px[i] / px[i - 252] - 1, px[i] / hi - 1, v21 / v63 if v63 > 0 else 1.0,
                 px[i] / (sum(px[i - 199:i + 1]) / 200) - 1]
        rows.append({"date": dates[i], "feats": feats, "dd": px[i] / hi - 1, "vol_ratio": feats[5], "w2": min(1.0, TARGET / v21) if v21 > 0 else 1.0,
                     "ret": px[j + 1] / px[i + 1] - 1})
    return rows


def r1_weights(rows: list[dict]) -> list[float]:
    return [1.0 if (r["dd"] < -DD_TRIGGER and r["vol_ratio"] < VOL_RATIO_TRIGGER) else r["w2"] for r in rows]


def t1_weights(rows: list[dict], y: list[float], cuts, start: int) -> list[float]:
    """Weights for rows[start:]. A month's tree is fitted on months that ended before its signal day (a label is only complete one day
    after the next signal, so month m uses rows[:m-1]). Refit every REFIT_EVERY months."""
    out, tree, mean_y = [], None, 0.0
    for m in range(start, len(rows)):
        if tree is None or (m - start) % REFIT_EVERY == 0:
            tr = list(range(m - 1))
            tree = fit_tree([rows[i]["feats"] for i in tr], [y[i] for i in tr], cuts, DEPTH, MIN_LEAF)
            mean_y = sum(y[i] for i in tr) / len(tr)
        up = predict(tree, rows[m]["feats"], cuts) > mean_y
        out.append(1.0 if up else rows[m]["w2"])
    return out


def score(rows: list[dict], w: list[float], cost_mult: float = 1.0) -> list[float]:
    prev, out = 0.0, []
    for r, x in zip(rows, w):
        out.append(x * r["ret"] - abs(x - prev) * COST_SIDE * cost_mult)
        prev = x
    return out


def judge(name: str, rows: list[dict], w: list[float], bench: list[float], v2: list[float], placebo_excess: list[float] | None) -> dict:
    s, s2 = score(rows, w), score(rows, w, STRESS)
    n = len(s)
    ex = [a - b for a, b in zip(s, bench)]
    m, z = nw_mean_z(ex)
    half = n // 2
    h1, h2 = sum(ex[:half]) / half, sum(ex[half:]) / (n - half)
    vs_v2 = sum(a - b for a, b in zip(s, v2)) / n
    stress_ex = sum(a - b for a, b in zip(s2, bench)) / n
    p95 = sorted(placebo_excess)[int(0.95 * len(placebo_excess)) - 1] if placebo_excess else None
    checks = {"excess>0": m > 0, f"z>={Z_BAR}": z >= Z_BAR, "beats_V2": vs_v2 > 0, "both_halves>0": h1 > 0 and h2 > 0, "stress>0": stress_ex > 0}
    if p95 is not None:
        checks["above_placebo_p95"] = m > p95
    return {"cell": name, "months": n, "first": rows[0]["date"], "excess_ann": m * 12, "nw_z": z, "excess_h1_ann": h1 * 12, "excess_h2_ann": h2 * 12,
            "excess_vs_v2_ann": vs_v2 * 12, "excess_stress_ann": stress_ex * 12, "placebo_p95_excess_ann": None if p95 is None else p95 * 12, "checks": checks,
            "verdict": "FALSIFIED" if not all(checks.values()) else "NOT_YET_FALSIFIED", "strategy": stats(s), "months_fully_invested": sum(1 for x in w if x == 1.0),
            "mean_weight": sum(w) / n}


def run() -> None:
    if RESULT_FILE.exists():
        sys.exit(f"{RESULT_FILE} exists: VM2 is a single read. Delete it on purpose (a crash fix only) to rerun.")
    bars = json.loads(BARS_FILE.read_text())["QQQ"]
    dates = sorted(bars)
    px = [bars[d] for d in dates]
    rows = build_rows(dates, px)
    y = [r["ret"] for r in rows]
    cuts = cut_points([{"feats": r["feats"]} for r in rows])
    start = BURN_MONTHS
    test = rows[start:]
    bench = [r["ret"] for r in test]
    v2 = score(test, [r["w2"] for r in test])
    out = {"test_first": test[0]["date"], "test_months": len(test), "qqq": stats(bench), "v2": stats(v2)}
    out["R1"] = judge("R1", test, r1_weights(test), bench, v2, None)
    w_t1 = t1_weights(rows, y, cuts, start)
    rng = random.Random(1)
    pl = []
    for _ in range(PLACEBO_REPS):
        ys = y[:]
        rng.shuffle(ys)
        wp = t1_weights(rows, ys, cuts, start)
        pl.append(sum(a - b for a, b in zip(score(test, wp), bench)) / len(test))
    out["T1"] = judge("T1", test, w_t1, bench, v2, pl)
    text = json.dumps(out, indent=1, default=str)
    RESULT_FILE.write_text(text)
    print(text)


if __name__ == "__main__":
    {"run": run}[sys.argv[1]]()
