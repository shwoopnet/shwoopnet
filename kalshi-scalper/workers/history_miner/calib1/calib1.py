#!/usr/bin/env python3
"""CALIB1 calibration census (History Miner, Nov 15, 2026). Card CALIB1_CARD_NOV15.md (with Amendment 1); hand case CALIB1_HAND_CASE_NOV15.md.
Descriptive table, not a rule: no try is counted. Reuses underdog2x.load() unchanged (cuts, SOL cut, third 3 dropped before any candle or result).

Usage (python3 -I, from outside the data folder):  python3 -I calib1.py <data folder> <out.json>"""
import json, math, os, statistics, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "underdog2x"))
sys.path.insert(0, os.path.dirname(HERE))
import underdog2x as U  # noqa: E402
import hm_guard  # noqa: E402

LOOKS = (600, 300, 120)
NB = 20
MIN_N = 300
EPS = 1e-9


def bucket(p):
    return min(NB - 1, int(math.floor(p * 20 + EPS)))


def fee1(p):
    return math.ceil(round(100 * 0.07 * p * (1 - p), 9)) / 100


def rows_for(cands, close, result):
    """[(look, side, ask, won, spread)], and per-look counts of missing and not two-sided."""
    out, miss = [], []
    for L in LOOKS:
        q = cands.get(close - L)
        if q is None:
            miss.append((L, "missing")); continue
        if not U.two_sided(q):
            miss.append((L, "not two-sided")); continue
        b, a = q
        for side, ask in (("yes", a), ("no", round(1 - b, 6))):
            out.append((L, side, ask, result == side, a - b))
    return out, miss


def stats(rs):
    """rs: list of (ask, won, spread)."""
    n = len(rs)
    if not n:
        return {"n": 0}
    w = sum(1 for r in rs if r[1]); asks = [r[0] for r in rs]
    var = sum(a * (1 - a) for a in asks)
    mfee = sum(fee1(a) for a in asks) / n
    sd = math.sqrt(var) / n
    p_null = 1 - 0.5 * (1 + math.erf(((mfee + 0.02) / sd) / math.sqrt(2))) if sd > 0 else 0.0
    return {"n": n, "wins": w, "p_pass_null": p_null, "win_rate": w / n, "mean_ask": sum(asks) / n, "gap": w / n - sum(asks) / n,
            "mean_fee1": mfee, "z": (w - sum(asks)) / math.sqrt(var) if var > 0 else None,
            "median_spread": statistics.median(r[2] for r in rs)}


def candidate(t1, t2):
    if t1.get("n", 0) < MIN_N or t2.get("n", 0) < MIN_N:
        return False
    ok = lambda s: s["gap"] >= s["mean_fee1"] + 0.02 - EPS
    return ok(t1) and ok(t2)


def run(folder):
    mk, cd, dropped = U.load(folder)
    cells = defaultdict(list)                  # (pool, look, side, bucket, third) -> rows
    counts = defaultdict(int)
    for t in sorted(mk, key=lambda x: (mk[x][1], x)):
        ser, close, res = mk[t]
        if res not in ("yes", "no"):
            counts["void"] += 1; continue
        rows, miss = rows_for(cd.get(t, {}), close, res)
        for L, why in miss:
            counts["%s_%d" % (why, L)] += 1
        th = U.third(ser, close)
        for L, side, ask, won, spr in rows:
            for pool in (ser, "POOLED"):
                cells[(pool, L, side, bucket(ask), th)].append((ask, won, spr))
    pools = sorted(U.THIRDS) + ["POOLED"]
    table, cands = {}, []
    eligible, exp_null = 0, 0.0
    for pool in pools:
        for L in LOOKS:
            for side in ("yes", "no"):
                for b in range(NB):
                    t1 = stats(cells.get((pool, L, side, b, 1), [])); t2 = stats(cells.get((pool, L, side, b, 2), []))
                    both = stats(cells.get((pool, L, side, b, 1), []) + cells.get((pool, L, side, b, 2), []))
                    key = "%s|%d|%s|%02d" % (pool, L, side, b)
                    table[key] = {"bucket": [b / 20, (b + 1) / 20], "third1": t1, "third2": t2, "thirds12": both}
                    if t1.get("n", 0) >= MIN_N and t2.get("n", 0) >= MIN_N:
                        eligible += 1; exp_null += t1["p_pass_null"] * t2["p_pass_null"]
                    if candidate(t1, t2):
                        cands.append(key)
    for key in cands:
        pool, L, side, b = key.split("|"); b = int(b)
        table[key]["candidate"] = True
        table[key]["neighbours"] = {k: table[k] for k in ("%s|%s|%s|%02d" % (pool, L, side, x) for x in (b - 1, b + 1)) if k in table}
    return {"label": "CALIB1 calibration census, thirds 1 and 2 only; descriptive; no try counted; rows not independent (both sides of a market, three looks)",
            "dropped_before_read": dropped, "markets_read": len(mk), "counts": dict(counts),
            "buckets_inspected": len(pools) * len(LOOKS) * NB * 2, "buckets_eligible_300_both": eligible,
            "expected_chance_candidates_null": exp_null,
            "expected_chance_note": "assumes calibration and independent rows; UNDERSTATES the chance count (rows are not independent)",
            "candidates": cands, "table": table}


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a)
    res = run(a[0])
    json.dump(res, open(a[1], "w"), indent=1, sort_keys=True)
    print(json.dumps({"markets_read": res["markets_read"], "candidates": res["candidates"], "counts": res["counts"]}, sort_keys=True)[:2000])
