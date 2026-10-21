"""TREE2: a decision tree that chooses which series and hours L1 trades (README, Pre-registration: TREE2). A SKIP rule on L1's own entries across
every 15 minute series in the data; walk-forward by UTC day with a refit every 7 days on earlier days only. Verdict words: FALSIFIED,
NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade; a pass would only say which rows of the live per-market table to watch.

Usage: python -m scalper.tree2 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import sqlite3
import sys
from collections import defaultdict

from . import lstrats as L
from . import tree1 as T
from .filters import diff_z, summarize
from .paths import DATA_DIR
from .scalps import STRESS

# ---- fixed in the README before the first run ----
Z_BAR = 2.6
DIFF_Z_BAR = 2.0
MIN_KEPT = 1000
MIN_DAYS = 10
MONTH_MIN = 300
BURN_DAYS = 14
REFIT_EVERY = 7
DEPTH = 3
MIN_LEAF = 400
PLACEBO_REPS = 100
SEED = 17
NUMERIC = ["price", "spread", "d1", "d3", "d5", "rng5", "dip", "hi_gap", "hour", "dow"]
SOURCES = ["alts2", "alts3", "alts4", "book", "l1b", "e3b"]
RESULT = DATA_DIR / "tree2_result.txt"


def load_pool() -> tuple[list[dict], list[str]]:
    """Every 15M series' L1 entries from SOURCES, de-duplicated by ticker (the first source wins), with TREE1's features plus one flag per series."""
    by: dict = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.ask_l, m.close_ts, m.result "
             "FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
        mine: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
        for s, tk, end, bc, ac, bh, al, close_ts, res in db.execute(q):
            if not s.endswith("15M") or tk in by:
                continue
            m = mine[tk]
            m["c"].append((end, bc, ac, bh, al)); m["close"] = close_ts; m["res"] = res; m["s"] = s
        by.update(mine)
    markets = [(tk, m["s"], m["c"], m["close"], m["res"]) for tk, m in by.items()]
    series = sorted({m[1] for m in markets})
    entries = L.hold_rule(markets, **L.L1)
    cmap = {m[0]: m[2] for m in markets}
    for e in entries:
        f, _ = T.row_features(cmap[e["ticker"]], e["close_ts"] - L.L1["left_s"], e["side"], e["price"], e["close_ts"], e["series"])
        e["pat"] = None
        e["feats"] = None if f is None else f[:len(NUMERIC)] + [1.0 if e["series"] == s else 0.0 for s in series]
    return entries, series


def judge(rows: list[dict], decisions: dict[int, bool], null95: float | None):
    kept = [rows[i] for i, s in decisions.items() if not s]
    skipped = [rows[i] for i, s in decisions.items() if s]
    s = summarize(kept)
    dm, dz = diff_z(kept, skipped)
    allv = [rows[i]["net"] for i in decisions]
    base = sum(allv) / len(allv) if allv else 0.0
    g = (s["mean"] - base) if kept else 0.0
    months = defaultdict(lambda: [[], []])
    for i, sk in decisions.items():
        months[rows[i]["day"][:7]][0 if not sk else 1].append(rows[i]["net"])
    month_ok, month_lines = True, []
    for mo in sorted(months):
        k, sk = months[mo]
        if len(k) + len(sk) < MONTH_MIN:
            month_lines.append(f"   {mo}: {len(k) + len(sk)} decided (under {MONTH_MIN}, not judged)")
            continue
        mall = (sum(k) + sum(sk)) / (len(k) + len(sk))
        mk = sum(k) / len(k) if k else mall
        month_lines.append(f"   {mo}: kept {len(k)} at {mk * 100:+.2f}c, skipped {len(sk)}, all {mall * 100:+.2f}c")
        month_ok = month_ok and mk > mall
    s.update(diff=dm, diff_z=dz, gain=g, null95=null95, decided=len(decisions), skipped=len(skipped), base=base, month_ok=month_ok, months=month_lines)
    if s["n"] < MIN_KEPT or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    ok = (s["mean"] > 0 and s["z"] >= Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0
          and dm > 0 and dz >= DIFF_Z_BAR and null95 is not None and g > null95 and month_ok)
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), s


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    rows, series = load_pool()
    names = NUMERIC + series
    cuts = T.cut_points(rows)
    y = [r["net"] for r in rows]
    have = sum(1 for r in rows if r["feats"] is not None)
    lines = [f"TREE2 on {len(rows)} L1 entries, {len(series)} series, {len(T.day_order(rows))} days; with features {have} (the rest excluded and counted)."]
    walk = lambda yy: T.tree_walk(rows, yy, cuts, BURN_DAYS, REFIT_EVERY, DEPTH, MIN_LEAF)
    dec = walk(y)
    rng = random.Random(SEED)
    placebo = []
    for _ in range(PLACEBO_REPS):
        z = T.shuffled_within_day(rows, y, rng)
        placebo.append(T.gain(walk(z), z))
    placebo.sort()
    p95 = placebo[int(0.95 * (len(placebo) - 1))]
    v, s = judge(rows, dec, p95)
    c = lambda x: f"{x * 100:+.2f}c"
    lines += [f"TREE2: decided {s['decided']}, skipped {s['skipped']} ({s['skipped'] / max(1, s['decided']) * 100:.1f}%), kept n={s['n']} on {s['days']} days; all decided {c(s['base'])}",
              f"   kept net {c(s['mean'])} z {s['z']:+.2f} halves {c(s['h1'])} / {c(s['h2'])} fees x{STRESS} {c(s['stress'])}",
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
    ok = [r for r in rows if r["feats"] is not None]
    lines.append("Final tree on all days (information):")
    lines += ["   " + x for x in T.describe(T.fit_tree([r["feats"] for r in ok], [r["net"] for r in ok], cuts, DEPTH, MIN_LEAF), cuts, "", names)]
    lines.append("Nothing here means trade. NOT_YET_FALSIFIED would only say which rows of the live per-market table to watch.")
    text = "\n".join(lines)
    RESULT.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv)
