"""DL10 (README, Pre-registration: DL10): drop a series when its last 100 L1 entries at 10 minutes net below zero. A SKIP rule on the 10 minute entries of TREE2's pool,
with DL1's pass bar and a raised z bar. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.dl10 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import sys
from bisect import bisect_right
from collections import defaultdict

from . import lstrats as L
from . import tree1 as T
from . import tree2 as T2
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
ENTRY_S, WINDOW, MIN_PRIOR, BURN_DAYS = 600, 100, 50, 14
Z_BAR, DIFF_Z_BAR, PLACEBO_REPS, SEED = 2.8, 2.0, 100, 29
RESULT = DATA_DIR / "dl10_result.txt"


def walk(rows: list[dict], y: list[float]) -> tuple[dict[int, bool], int]:
    days = T.day_order(rows)
    burn_end = days[BURN_DAYS]
    by_series: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        by_series[r["series"]].append(i)
    dec, undecided = {}, 0
    for s, ix in by_series.items():
        acc, times = [0.0], []
        for i in ix:
            acc.append(acc[-1] + y[i])
            times.append(rows[i]["close_ts"])
        for i in ix:
            if rows[i]["day"] < burn_end:
                continue
            k = bisect_right(times, rows[i]["close_ts"] - ENTRY_S)      # entries whose market closed by the decision time
            if k < MIN_PRIOR:
                undecided += 1
                continue
            lo = max(0, k - WINDOW)
            dec[i] = not (acc[k] - acc[lo] > 0)
    return dec, undecided


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows = sorted(L.hold_rule(full, ENTRY_S, L.L1["band"]), key=lambda e: e["close_ts"])
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
    if v != "NOT_ENOUGH_DATA":                               # TREE2's judge uses its own z bar (2.6); DL10's registered bar is 2.8
        ok = (s["mean"] > 0 and s["z"] >= Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0 and s["diff"] > 0 and s["diff_z"] >= DIFF_Z_BAR
              and s["gain"] > p95 and s["month_ok"])
        v = "NOT_YET_FALSIFIED" if ok else "FALSIFIED"
    c = lambda x: f"{x * 100:+.2f}c"
    lines = [f"DL10 on {len(rows)} 10 minute entries; decided {s['decided']}, undecided (under {MIN_PRIOR} prior) {undecided}",
             f"   skipped {s['skipped']} ({s['skipped'] / max(1, s['decided']) * 100:.1f}%), kept n={s['n']} on {s['days']} days; all decided {c(s['base'])}",
             f"   kept net {c(s['mean'])} z {s['z']:+.2f} halves {c(s['h1'])} / {c(s['h2'])} fees x{T2.STRESS} {c(s['stress'])}",
             f"   kept minus skipped {c(s['diff'])} (day clustered z {s['diff_z']:+.2f}); gain {c(s['gain'])}; placebo 95th percentile {c(p95)}",
             "   by month:"] + s["months"] + [f"   VERDICT: {v}", "Per series (information): kept n / mean, skipped n / mean"]
    per = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for i, sk in dec.items():
        a = per[rows[i]["series"]]
        a[0 if not sk else 1] += 1
        a[2 if not sk else 3] += rows[i]["net"]
    for sr in sorted(per):
        k, sk, ks, ss = per[sr]
        lines.append(f"   {sr}: kept {k} at {(ks / k * 100 if k else float('nan')):+.2f}c, skipped {sk} at {(ss / sk * 100 if sk else float('nan')):+.2f}c")
    text = "\n".join(lines)
    RESULT.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv)
