"""DL1 (README, Pre-registration: DL1): drop a Kalshi series when its last 200 L1 entries net below zero. A SKIP rule on L1's own entries, scored on TREE2's
pool, with TREE2's pass bar and a raised z bar. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.dl1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import sys
from bisect import bisect_right
from collections import defaultdict

from . import lstrats as L
from . import tree1 as T
from . import tree2 as T2
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
WINDOW, MIN_PRIOR, BURN_DAYS, LAG_S = 200, 100, 14, L.L1["left_s"]
Z_BAR, DIFF_Z_BAR, PLACEBO_REPS, SEED = 2.7, 2.0, 100, 23
RESULT = DATA_DIR / "dl1_result.txt"


def walk(rows: list[dict], y: list[float]) -> tuple[dict[int, bool], int]:
    """{row index: skipped?} for rows after the burn-in with at least MIN_PRIOR prior entries in their series; the second value counts the rest."""
    days = T.day_order(rows)
    burn_end = days[BURN_DAYS]
    by_series: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        by_series[r["series"]].append(i)
    prefix, times = {}, {}
    for s, ix in by_series.items():
        acc = [0.0]
        for i in ix:
            acc.append(acc[-1] + y[i])
        prefix[s] = acc
        times[s] = [rows[i]["close_ts"] for i in ix]
    dec, undecided = {}, 0
    for s, ix in by_series.items():
        for pos, i in enumerate(ix):
            if rows[i]["day"] < burn_end:
                continue
            k = bisect_right(times[s], rows[i]["close_ts"] - LAG_S)       # entries whose market closed by the decision time
            if k < MIN_PRIOR:
                undecided += 1
                continue
            lo = max(0, k - WINDOW)
            dec[i] = not (prefix[s][k] - prefix[s][lo] > 0)
    return dec, undecided


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    rows, series = T2.load_pool()
    y = [r["net"] for r in rows]
    dec, undecided = walk(rows, y)
    rng = random.Random(SEED)
    placebo = []
    for _ in range(PLACEBO_REPS):
        z = T.shuffled_within_day(rows, y, rng)
        placebo.append(T.gain(walk(rows, z)[0], z))
    placebo.sort()
    p95 = placebo[int(0.95 * (len(placebo) - 1))]
    v, s = T2.judge(rows, dec, p95)
    if v != "NOT_ENOUGH_DATA":                               # TREE2's judge uses its own z bar (2.6); DL1's registered bar is 2.7
        ok = (s["mean"] > 0 and s["z"] >= Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0 and s["diff"] > 0 and s["diff_z"] >= DIFF_Z_BAR
              and s["gain"] > p95 and s["month_ok"])
        v = "NOT_YET_FALSIFIED" if ok else "FALSIFIED"
    c = lambda x: f"{x * 100:+.2f}c"
    lines = [f"DL1 on {len(rows)} L1 entries, {len(series)} series, {len(T.day_order(rows))} days; decided {s['decided']}, undecided (under {MIN_PRIOR} prior entries) {undecided}",
             f"DL1: skipped {s['skipped']} ({s['skipped'] / max(1, s['decided']) * 100:.1f}%), kept n={s['n']} on {s['days']} days; all decided {c(s['base'])}",
             f"   kept net {c(s['mean'])} z {s['z']:+.2f} halves {c(s['h1'])} / {c(s['h2'])} fees x{T2.STRESS} {c(s['stress'])}",
             f"   kept minus skipped {c(s['diff'])} (day clustered z {s['diff_z']:+.2f}); gain {c(s['gain'])}; placebo 95th percentile {c(p95)}",
             "   by month (kept must beat all decided in every judged month):"] + s["months"] + [f"   VERDICT: {v}"]
    per = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for i, sk in dec.items():
        a = per[rows[i]["series"]]
        a[0 if not sk else 1] += 1
        a[2 if not sk else 3] += rows[i]["net"]
    lines.append("Per series (information): kept n / mean, skipped n / mean")
    for sr in sorted(per):
        k, sk, ks, ss = per[sr]
        lines.append(f"   {sr}: kept {k} at {(ks / k * 100 if k else float('nan')):+.2f}c, skipped {sk} at {(ss / sk * 100 if sk else float('nan')):+.2f}c")
    text = "\n".join(lines)
    RESULT.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv)
