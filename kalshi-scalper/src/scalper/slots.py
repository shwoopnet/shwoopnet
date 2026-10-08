"""The four slot search (protocol fixed in the README before this file existed).

One rule per series per window: Bitcoin early, Bitcoin late, gold early, gold late. Same loop as `search.py` (fresh 50, fresh 50, 50
one-filter mutants, top 25 kept, search window = first half of the days, holdout = second half read once) with the minute drawn from
the slot's window, the series fixed by the slot, and one new filter, `pair`, that reads the other series' market closing at the same
time. A fair-market copy of the data runs the identical pipeline as the control. This can never produce a verdict that means trade.

Usage: python -m scalper.slots
"""
from __future__ import annotations

import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

from . import search as S
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .scalps import fee, load as load_markets

EARLY = (14, 13, 12, 11, 10)
LATE = (6, 5, 4, 3, 2, 1)
SLOTS = {
    "BTC-early": ("KXBTC15M", EARLY), "BTC-late": ("KXBTC15M", LATE),
    "GOLD-early": ("KXGOLD15M", EARLY), "GOLD-late": ("KXGOLD15M", LATE),
}
FILTER_TYPES = ("spread", "move", "pair")
PAIR_MARGIN = 0.05
STRESS = 1.2
MIN_N = 100
PASS_Z = 3.0
PASS_N = 300
OUT = Path(__file__).resolve().parents[2] / "search4"


def with_pairs(ms: list[dict]) -> list[dict]:
    """Attach each market's twin: the other series' market with the same close time (or None)."""
    by = {(m["series"], m["close"]): m for m in ms}
    other = {"KXBTC15M": "KXGOLD15M", "KXGOLD15M": "KXBTC15M"}
    return [dict(m, twin=by.get((other[m["series"]], m["close"]))) for m in ms]


def pair_ok(m: dict, rule_left: int, side: str, mode: str) -> bool:
    tw = m.get("twin")
    if tw is None:
        return False
    q = tw["book"].get(m["close"] - rule_left * 60)
    if q is None or not valid_quote(q[0], q[1]):
        return False
    mid = (q[0] + q[1]) / 2
    if mid >= 0.5 + PAIR_MARGIN - 1e-9:
        pointing = "yes"
    elif mid <= 0.5 - PAIR_MARGIN + 1e-9:
        pointing = "no"
    else:
        return False
    return (pointing == side) if mode == "agree" else (pointing != side)


def entry(m: dict, rule: dict):
    """(day, side, price) or None. Decided from prices only."""
    if m["series"] != rule["series"]:
        return None
    pairs = [f for f in rule["filters"] if f[0] == "pair"]
    base = dict(rule, filters=[f for f in rule["filters"] if f[0] != "pair"])
    e = S.entry(m, base)
    if e is None:
        return None
    day, side, price, _ = e
    for f in pairs:
        if not pair_ok(m, rule["left"], side, f[1]):
            return None
    return day, side, price


def trades(markets: list[dict], rule: dict) -> list[tuple]:
    out = []
    for m in markets:
        e = entry(m, rule)
        if e is None:
            continue
        day, side, price = e
        win = 1.0 if m["res"] == side else 0.0
        out.append((day, m["close"], win - price - fee(price), win - price - STRESS * fee(price)))
    return out


def score(markets, rule) -> dict:
    t = trades(markets, rule)
    mean, se, z = cluster_mean_z([(d, n) for d, _, n, _ in t])
    return {"n": len(t), "mean": mean, "se": se, "z": z if len(t) >= MIN_N else float("-inf")}


def hold_detail(markets, rule) -> dict:
    t = sorted(trades(markets, rule), key=lambda x: x[1])
    mean, se, z = cluster_mean_z([(d, n) for d, _, n, _ in t])
    h = len(t) // 2
    halves = [sum(x[2] for x in t[:h]) / h, sum(x[2] for x in t[h:]) / (len(t) - h)] if len(t) >= 2 else [0.0, 0.0]
    stress = sum(x[3] for x in t) / len(t) if t else 0.0
    return {"n": len(t), "mean": mean, "z": z, "halves": halves, "stress": stress}


def verdict(d: dict, search_z: float, floor: float, control_best: float) -> str:
    if d["n"] < PASS_N:
        return "NOT_ENOUGH_DATA"
    ok = (search_z > floor and search_z > control_best and d["mean"] > 0 and d["z"] >= PASS_Z
          and all(h > 0 for h in d["halves"]) and d["stress"] > 0)
    return "NOT_YET_FALSIFIED" if ok else "FALSIFIED"


def random_filter(rng, kind):
    if kind == "spread":
        return ("spread", rng.choice(S.SPREADS))
    if kind == "move":
        return ("move", rng.choice(("toward", "away")), rng.choice(S.MOVE_D), rng.choice(S.MOVE_M))
    return ("pair", rng.choice(("agree", "disagree")))


def random_rule(rng, series, lefts):
    while True:
        i, j = sorted(rng.sample(range(len(S.EDGES)), 2))
        if S.EDGES[j] - S.EDGES[i] >= 0.07 - 1e-9:
            break
    k = rng.choices((0, 1, 2, 3), weights=(0.3, 0.35, 0.25, 0.1))[0]
    kinds = rng.sample(FILTER_TYPES, k)
    return {"series": series, "left": rng.choice(lefts), "lo": S.EDGES[i], "hi": S.EDGES[j], "side": rng.choice(S.SIDES),
            "filters": sorted((random_filter(rng, kd) for kd in kinds), key=lambda t: t[0])}


def mutate(rule, rng):
    fs = [tuple(f) for f in rule["filters"]]
    missing = [t for t in FILTER_TYPES if t not in {f[0] for f in fs}]
    if fs and (not missing or rng.random() < 0.5):
        fs.pop(rng.randrange(len(fs)))
    else:
        fs.append(random_filter(rng, rng.choice(missing)))
    return dict(rule, filters=sorted(fs, key=lambda t: t[0]))


def norm(rule):
    return dict(rule, filters=[tuple(f) for f in rule["filters"]])


def evaluate(markets, rules, seen):
    out = []
    for r in rules:
        r = norm(r)
        k = S.key(r)
        if k not in seen:
            seen[k] = score(markets, r)
        out.append({"rule": r, "key": k, **seen[k]})
    return out


def run_slot(markets, series, lefts, seed=11, cycles=3):
    rng = random.Random(seed)
    seen: dict = {}
    rounds, carried = [], []

    def fresh(count):
        out = []
        while len(out) < count:
            r = norm(random_rule(rng, series, lefts))
            if S.key(r) not in seen and all(S.key(r) != S.key(o) for o in out):
                out.append(r)
        return out

    for c in range(1, cycles + 1):
        A = S.top(evaluate(markets, fresh(50), seen) + carried)
        B = S.top(evaluate(markets, fresh(50), seen))
        pool = A + B
        mutants = []
        for _ in range(5000):
            if len(mutants) >= 50:
                break
            m = norm(mutate(rng.choice(pool)["rule"], rng))
            if all(S.key(m) != S.key(x) for x in mutants):
                mutants.append(m)
        C = S.top(evaluate(markets, mutants, seen))
        carried = C
        rounds += [(c, "A", A), (c, "B", B), (c, "C", C)]
    return {"rounds": rounds, "evaluated": len(seen)}


def describe(rule):
    f = []
    for t in rule["filters"]:
        if t[0] == "spread":
            f.append(f"spread<={t[1] * 100:.0f}c")
        elif t[0] == "pair":
            f.append(f"other market {t[1]}s")
        else:
            f.append(f"price moved {t[1]} the side by {t[2] * 100:.0f}c over {t[3]}m")
    return (f"{rule['series'][2:5]} {rule['left']}m left, side {rule['side']} priced {rule['lo']:.2f}-{rule['hi']:.2f}"
            + (", " + ", ".join(f) if f else ""))


def main():
    markets, _ = load_markets()
    ms = with_pairs(S.prep(markets))
    search_w, hold = S.split_days(ms)
    print(f"{len(ms)} markets; search window {len(search_w)}, holdout {len(hold)} locked until the end.\n")
    null_search = S.fair_market(search_w, 12)
    null_hold = S.fair_market(hold, 13)
    # the fair-market copies keep the twin link by close time
    null_search, null_hold = with_pairs(null_search), with_pairs(null_hold)
    OUT.mkdir(exist_ok=True)
    total, report = 0, {}
    for name, (series, lefts) in SLOTS.items():
        real = run_slot(search_w, series, lefts)
        ctl = run_slot(null_search, series, lefts)
        n = real["evaluated"]
        total += n
        floor = math.sqrt(2 * math.log(n))
        final, cfinal = real["rounds"][-1][2], ctl["rounds"][-1][2]
        cbest = max(r["z"] for _, _, rows in ctl["rounds"] for r in rows)
        rbest = max(r["z"] for _, _, rows in real["rounds"] for r in rows)
        print(f"== {name}: {n} rules; best search z real {rbest:.2f} vs control {cbest:.2f}; floor sqrt(2 ln N) {floor:.2f}")
        rows, cpos = [], 0
        for r in final:
            d = hold_detail(hold, r["rule"])
            rows.append({"rule": describe(r["rule"]), "spec": r["rule"], "search_n": r["n"], "search_mean_c": round(r["mean"] * 100, 3),
                         "search_z": round(r["z"], 3), "hold_n": d["n"], "hold_mean_c": round(d["mean"] * 100, 3),
                         "hold_z": round(d["z"], 3) if d["z"] != float("-inf") else None,
                         "halves_c": [round(h * 100, 2) for h in d["halves"]], "stress_c": round(d["stress"] * 100, 3),
                         "verdict": verdict(d, r["z"], floor, cbest)})
        for r in cfinal:
            if hold_detail(null_hold, r["rule"])["mean"] > 0:
                cpos += 1
        pos = sum(1 for x in rows if x["hold_mean_c"] > 0)
        vs = {}
        for x in rows:
            vs[x["verdict"]] = vs.get(x["verdict"], 0) + 1
        print(f"   holdout of final 25: {pos} positive (control rules on a fair holdout: {cpos}); mean {sum(x['hold_mean_c'] for x in rows) / len(rows):+.2f}c; verdicts {vs}")
        best = max(rows, key=lambda x: (x["hold_z"] if x["hold_z"] is not None else -9))
        print(f"   best holdout row: {best['rule']} | n={best['hold_n']} {best['hold_mean_c']:+.2f}c z={best['hold_z']} -> {best['verdict']}")
        if name.endswith("late"):
            l1 = {"series": series, "left": 6, "lo": 0.88, "hi": 0.97, "side": "either", "filters": []}
            a, b = score(search_w, l1), hold_detail(hold, l1)
            print(f"   information: L1 as live in this slot: search n={a['n']} {a['mean'] * 100:+.2f}c z={a['z']:.2f}; holdout n={b['n']} {b['mean'] * 100:+.2f}c z={b['z']:.2f}")
        report[name] = {"evaluated": n, "floor": round(floor, 3), "real_best_z": round(rbest, 3), "control_best_z": round(cbest, 3), "final25": rows}
    (OUT / "slots.json").write_text(json.dumps(report, indent=1, default=list))
    print(f"\ndistinct rules evaluated in the real runs: {total}. Tally 793 + {total} = {793 + total}.")
    passes = [(k, x) for k, v in report.items() for x in v["final25"] if x["verdict"] == "NOT_YET_FALSIFIED"]
    print(f"rules with NOT_YET_FALSIFIED: {len(passes)}")


if __name__ == "__main__":
    main()
