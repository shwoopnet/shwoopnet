"""PROG1 (README, Pre-registration: PROG1): four portfolio-level strategies across all 18 series on L1 entries. Research only: nothing here places an
order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.   python -m scalper.prog1 run   (once)
"""
from __future__ import annotations

import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timezone

from . import feat1 as F
from .calibration import cluster_mean_z
from .crowd1 import diff_z
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

RESULT = DATA_DIR / "prog1_result.txt"
BAR_C, BAR_Z, MIN_SERIES = 0.010, 2.5, 8
PREV_WINDOWS = 4
CELL_DAYS, CELL_MIN = 14, 30
FIRST_DAY = 14
SEL_C, SEL_OVER, SEL_MIN = 0.015, 0.010, 300


def hour_bucket(ts: int) -> int:
    return datetime.fromtimestamp(ts, timezone.utc).hour // 6


def adjust(rows: list[dict]) -> list[dict]:
    base = defaultdict(list)
    for r in rows:
        base[r["series"]].append(r["net"])
    mean = {s: st.mean(v) for s, v in base.items()}
    sb = defaultdict(list)
    for r in rows:
        sb[r["series"]].append(r["stress"])
    smean = {s: st.mean(v) for s, v in sb.items()}
    return [{**r, "net": r["net"] - mean[r["series"]], "stress": r["stress"] - smean[r["series"]], "raw": r["net"], "raw_stress": r["stress"]} for r in rows]


def group_test(rows: list[dict], pick) -> dict:
    g = [r for r in rows if pick(r) is True]
    rest = [r for r in rows if pick(r) is False]
    m, z, nd = diff_z(g, rest)
    ordered = sorted(rows, key=lambda r: r["close_ts"])
    mid = ordered[len(ordered) // 2]["close_ts"]
    h1 = diff_z([r for r in g if r["close_ts"] < mid], [r for r in rest if r["close_ts"] < mid])[0]
    h2 = diff_z([r for r in g if r["close_ts"] >= mid], [r for r in rest if r["close_ts"] >= mid])[0]
    s = diff_z(g, rest, "stress")[0]
    per = defaultdict(lambda: ([], []))
    for r in g:
        per[r["series"]][0].append(r["net"])
    for r in rest:
        per[r["series"]][1].append(r["net"])
    pos = sum(1 for a, b in per.values() if a and b and st.mean(a) > st.mean(b))
    ok = m >= BAR_C and z >= BAR_Z and h1 > 0 and h2 > 0 and s > 0 and pos >= MIN_SERIES
    verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < 0.003 or z < 1.0) else "NOT_ENOUGH_DATA")
    return {"verdict": verdict, "n_group": len(g), "n_rest": len(rest), "diff_c": 100 * m, "z": z, "h1_c": 100 * h1, "h2_c": 100 * h2, "stress_c": 100 * s, "series_pos": pos, "series_n": len(per), "share": len(g) / max(1, len(g) + len(rest))}


def previous_losses(rows: list[dict]) -> dict[int, int]:
    """Losing entries in the PREV_WINDOWS windows before each window (their outcomes are known at the 6 minute decision)."""
    lost = defaultdict(int)
    for r in rows:
        if r["gross"] < 0:
            lost[r["close_ts"]] += 1
    return {w: sum(lost.get(w - 900 * k, 0) for k in range(1, PREV_WINDOWS + 1)) for w in {r["close_ts"] for r in rows}}


def allocator(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Walk-forward: score each candidate by its (series, 6 hour bucket) cell mean over the CELL_DAYS days before the candidate's day; take the best if above 0."""
    days = sorted({r["day"] for r in rows})
    dix = {d: i for i, d in enumerate(days)}
    cell = defaultdict(lambda: defaultdict(list))
    for r in rows:
        cell[(r["series"], hour_bucket(r["close_ts"]))][dix[r["day"]]].append(r["raw"])
    by_w = defaultdict(list)
    for r in rows:
        by_w[r["close_ts"]].append(r)
    picked, pool = [], []
    for w in sorted(by_w):
        cands = by_w[w]
        d = dix[cands[0]["day"]]
        if d < FIRST_DAY:
            continue
        best, best_s = None, 0.0
        for r in cands:
            hist = [x for k in range(max(0, d - CELL_DAYS), d) for x in cell[(r["series"], hour_bucket(r["close_ts"]))].get(k, [])]
            sc = st.mean(hist) if len(hist) >= CELL_MIN else 0.0
            if sc > best_s:
                best, best_s = r, sc
        pool.extend(cands)
        if best is not None:
            picked.append(best)
    return picked, pool


def judge_alloc(picked: list[dict], pool: list[dict]) -> dict:
    if len(picked) < SEL_MIN:
        return {"verdict": "NOT_ENOUGH_DATA", "n": len(picked)}
    m, _, z = cluster_mean_z([(r["day"], r["raw"]) for r in picked])
    pm = st.mean(r["raw"] for r in pool)
    ordered = sorted(picked, key=lambda r: r["close_ts"])
    h = len(ordered) // 2
    h1 = st.mean(r["raw"] for r in ordered[:h]); h2 = st.mean(r["raw"] for r in ordered[h:])
    s = st.mean(r["raw_stress"] for r in picked)
    ok = m >= SEL_C and m - pm >= SEL_OVER and z >= BAR_Z and h1 > 0 and h2 > 0 and s > 0
    return {"verdict": "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if m < 0.005 else "NOT_ENOUGH_DATA"), "n": len(picked), "mean_c": 100 * m, "pool_c": 100 * pm, "z": z, "h1_c": 100 * h1, "h2_c": 100 * h2, "stress_c": 100 * s}


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    mk = {}
    for m in load() + load_fresh():
        if all(x[1] is not None and x[2] is not None for x in m[2]) and m[4] in ("yes", "no"):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    rows.sort(key=lambda r: r["close_ts"])
    adj = adjust(rows)
    out = [f"PROG1: {len(rows)} L1 entries, {len({r['series'] for r in rows})} series, {len({r['day'] for r in rows})} days"]
    p1 = group_test(adj, lambda r: 12 <= datetime.fromtimestamp(r["close_ts"], timezone.utc).hour < 18)
    out.append(f"P1 US-hours (12-18 UTC)   {p1}")
    loss = previous_losses(adj)
    q = group_test(adj, lambda r: loss[r["close_ts"]] == 0)
    out.append(f"P2 cooling-off (clean 4 windows vs any loss)   {q}")
    breadth = defaultdict(int)
    for r in adj:
        breadth[r["close_ts"]] += 1
    vals = sorted(breadth.values())
    lo, hi = vals[len(vals) // 3], vals[(2 * len(vals)) // 3]
    q3 = group_test(adj, lambda r: True if breadth[r["close_ts"]] >= hi else (False if breadth[r["close_ts"]] <= lo else None))
    out.append(f"P3 breadth (top third vs bottom third; cuts {lo}, {hi})   {q3}")
    picked, pool = allocator(adj)
    out.append(f"P4 allocator   {judge_alloc(picked, pool)}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] != "p6"):
    main(sys.argv)


# ---- P6: adaptive timing-and-series allocator with shrinkage (README, Pre-registration: P6) ----
P6_LEFTS = (540, 450, 360, 270)
P6_SHRINK, P6_MIN_SERIES, P6_THRESHOLD = 30, 30, 0.005


def allocator_p6(cands: list[dict]) -> tuple[list[dict], list[dict]]:
    """cands: L1-band entries tagged with their entry time `left`. Past 14 days only; shrink the (series, left, bucket) cell towards the (series, left) mean."""
    days = sorted({r["day"] for r in cands})
    dix = {d: i for i, d in enumerate(days)}
    cell = defaultdict(lambda: defaultdict(list))
    par = defaultdict(lambda: defaultdict(list))
    for r in cands:
        cell[(r["series"], r["left"], hour_bucket(r["close_ts"]))][dix[r["day"]]].append(r["net"])
        par[(r["series"], r["left"])][dix[r["day"]]].append(r["net"])
    by_w = defaultdict(list)
    for r in cands:
        by_w[r["close_ts"]].append(r)
    picked, pool = [], []
    for w in sorted(by_w):
        cs = by_w[w]
        d = dix[cs[0]["day"]]
        if d < FIRST_DAY:
            continue
        best, best_s = None, P6_THRESHOLD
        for r in cs:
            lo = max(0, d - CELL_DAYS)
            ph = [x for k in range(lo, d) for x in par[(r["series"], r["left"])].get(k, [])]
            if len(ph) < P6_MIN_SERIES:
                continue
            ch = [x for k in range(lo, d) for x in cell[(r["series"], r["left"], hour_bucket(r["close_ts"]))].get(k, [])]
            mp = st.mean(ph)
            sc = (len(ch) * (st.mean(ch) if ch else 0.0) + P6_SHRINK * mp) / (len(ch) + P6_SHRINK)
            if sc > best_s:
                best, best_s = r, sc
        pool.extend(cs)
        if best is not None:
            picked.append(best)
    return picked, pool


def run_p6() -> str:
    mk = {}
    for m in load() + load_fresh():
        if all(x[1] is not None and x[2] is not None for x in m[2]) and m[4] in ("yes", "no"):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    cands = []
    for left in P6_LEFTS:
        rows, _, _ = F.build(list(mk.values()), left)
        for r in rows:
            cands.append({**r, "left": left, "raw": r["net"], "raw_stress": r["stress"]})
    cands.sort(key=lambda r: r["close_ts"])
    picked, pool = allocator_p6(cands)
    res = judge_alloc(picked, pool)
    return f"P6 adaptive allocator ({len(cands)} candidates over {len(P6_LEFTS)} entry times)   {res}"


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "p6":
    out = run_p6()
    (DATA_DIR / "p6_result.txt").write_text(out + "\n")
    print(out)


# ---- P6F: the forward read of P6 (README, Registered: P6F). Needs data/fresh.sqlite refreshed (python -m scalper.fresh_update). Once. ----
P6F_CUT = "2026-10-26"
P6F_MIN_N, P6F_C, P6F_OVER, P6F_Z = 300, 0.005, 0.003, 2.0


def run_p6f() -> str:
    import time
    if time.strftime("%Y-%m-%d", time.gmtime()) < "2026-11-12":
        return "P6F refuses before 2026-11-12 (the read day); nothing was computed."
    out_path = DATA_DIR / "p6f_result.txt"
    if out_path.exists():
        return f"Refusing to run again: {out_path} exists."
    mk = {}
    for m in load() + load_fresh():
        if all(x[1] is not None and x[2] is not None for x in m[2]) and m[4] in ("yes", "no"):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    cands = []
    for left in P6_LEFTS:
        rows, _, _ = F.build(list(mk.values()), left)
        for r in rows:
            cands.append({**r, "left": left, "raw": r["net"], "raw_stress": r["stress"]})
    cands.sort(key=lambda r: r["close_ts"])
    picked, pool = allocator_p6(cands)           # walk-forward over all days; only days from the cut on are scored
    picked = [r for r in picked if r["day"] >= P6F_CUT]
    pool = [r for r in pool if r["day"] >= P6F_CUT]
    if len(picked) < P6F_MIN_N:
        res = {"verdict": "NOT_ENOUGH_DATA", "n": len(picked)}
    else:
        m, _, z = cluster_mean_z([(r["day"], r["raw"]) for r in picked])
        pm = st.mean(r["raw"] for r in pool)
        ordered = sorted(picked, key=lambda r: r["close_ts"])
        h = len(ordered) // 2
        h1, h2 = st.mean(r["raw"] for r in ordered[:h]), st.mean(r["raw"] for r in ordered[h:])
        s = st.mean(r["raw_stress"] for r in picked)
        ok = m >= P6F_C and m - pm >= P6F_OVER and z >= P6F_Z and h1 > 0 and h2 > 0 and s > 0
        res = {"verdict": "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if m <= 0 else "NOT_ENOUGH_DATA"), "n": len(picked), "mean_c": 100 * m, "pool_c": 100 * pm, "z": z,
               "h1_c": 100 * h1, "h2_c": 100 * h2, "stress_c": 100 * s}
    text = f"P6F forward (days from {P6F_CUT})   {res}"
    out_path.write_text(text + "\n")
    return text


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "p6f":
    print(run_p6f())
