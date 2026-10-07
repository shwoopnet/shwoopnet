"""Automated rule search (protocol fixed in the README before this file existed).

make 50 rules and test them, keep the top 25; make 50 more, keep the top 25; take those top 50, add or remove ONE filter from
each, rerun, keep the top 25; repeat. The search sees ONLY the first half of the days. The second half is the holdout and is read
once, at the end, for the saved survivors. A shuffled-outcome copy of the data runs through the same pipeline as a control, so
the selection effect is visible: the best of N rules on pure noise looks real.

This is a parameter search. It cannot produce a verdict that means "trade", and it never reads the holdout while it searches.

Usage: python -m scalper.search          (writes search/*.json and prints the report)
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .scalps import fee, load as load_markets

LEFTS = (1, 2, 3, 4, 5, 6, 8, 10, 12, 14)
EDGES = (0.03, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.97)
SIDES = ("either", "yes", "no")
SPREADS = (0.01, 0.02, 0.04)
SERIES = ("KXBTC15M", "KXGOLD15M")
MOVE_D = (0.02, 0.05)
MOVE_M = (1, 3, 5)
FILTER_TYPES = ("spread", "series", "move")
MIN_N = 100
OUT = Path(__file__).resolve().parents[2] / "search"


def _r4(x: float) -> float:
    return round(x, 4)


def prep(markets: list[tuple]) -> list[dict]:
    out = []
    for ticker, series, candles, close_ts, res in markets:
        if res not in ("yes", "no"):
            continue
        out.append({"ticker": ticker, "series": series, "close": close_ts, "res": res,
                    "day": datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d"),
                    "book": {c[0]: (c[1], c[2]) for c in candles}})
    return sorted(out, key=lambda m: m["close"])


def split_days(ms: list[dict]) -> tuple[list[dict], list[dict]]:
    """The first half of the DAYS is the search window; the rest is the locked holdout."""
    days = sorted({m["day"] for m in ms})
    cut = set(days[: len(days) // 2])
    return [m for m in ms if m["day"] in cut], [m for m in ms if m["day"] not in cut]


def key(rule: dict) -> str:
    return json.dumps(rule, sort_keys=True)


def describe(rule: dict) -> str:
    f = []
    for t in rule["filters"]:
        if t[0] == "spread":
            f.append(f"spread<={t[1] * 100:.0f}c")
        elif t[0] == "series":
            f.append("only " + t[1][2:5])
        else:
            f.append(f"price moved {t[1]} the side by {t[2] * 100:.0f}c over {t[3]}m")
    return (f"{rule['left']}m left, side {rule['side']} priced {rule['lo']:.2f}-{rule['hi']:.2f}" + (", " + ", ".join(f) if f else ""))


def observe(m: dict, rule: dict):
    """(day, net per contract) for one market under one rule, or None. Nothing here reads a result except to settle the trade."""
    t = m["close"] - rule["left"] * 60
    q = m["book"].get(t)
    if q is None or not valid_quote(q[0], q[1]):
        return None
    bid, ask = q
    lo, hi = rule["lo"] - 1e-9, rule["hi"] + 1e-9
    yes_p, no_p = _r4(ask), _r4(1 - bid)
    pick = None
    if rule["side"] in ("either", "yes") and lo <= yes_p <= hi:
        pick = ("yes", yes_p)
    elif rule["side"] in ("either", "no") and lo <= no_p <= hi:
        pick = ("no", no_p)
    if pick is None:
        return None
    side, price = pick
    for f in rule["filters"]:
        if f[0] == "spread":
            if ask - bid > f[1] + 1e-9:
                return None
        elif f[0] == "series":
            if m["series"] != f[1]:
                return None
        else:
            _, direction, d, mins = f
            prev = m["book"].get(t - mins * 60)
            if prev is None or not valid_quote(prev[0], prev[1]):
                return None
            yes_move = (bid + ask) / 2 - (prev[0] + prev[1]) / 2
            toward = yes_move >= d - 1e-9 if side == "yes" else yes_move <= -d + 1e-9
            away = yes_move <= -d + 1e-9 if side == "yes" else yes_move >= d - 1e-9
            if not (toward if direction == "toward" else away):
                return None
    won = m["res"] == side
    return m["day"], (1.0 if won else 0.0) - price - fee(price)


def score(markets: list[dict], rule: dict) -> dict:
    obs = [o for o in (observe(m, rule) for m in markets) if o is not None]
    mean, se, z = cluster_mean_z(obs)
    n = len(obs)
    return {"n": n, "mean": mean, "se": se, "z": z if n >= MIN_N else float("-inf")}


def random_filter(rng: random.Random, kind: str) -> tuple:
    if kind == "spread":
        return ("spread", rng.choice(SPREADS))
    if kind == "series":
        return ("series", rng.choice(SERIES))
    return ("move", rng.choice(("toward", "away")), rng.choice(MOVE_D), rng.choice(MOVE_M))


def random_rule(rng: random.Random) -> dict:
    while True:
        i, j = sorted(rng.sample(range(len(EDGES)), 2))
        if EDGES[j] - EDGES[i] >= 0.07 - 1e-9:
            break
    k = rng.choices((0, 1, 2, 3), weights=(0.3, 0.35, 0.25, 0.1))[0]
    kinds = rng.sample(FILTER_TYPES, k)
    return {"left": rng.choice(LEFTS), "lo": EDGES[i], "hi": EDGES[j], "side": rng.choice(SIDES),
            "filters": sorted((random_filter(rng, kd) for kd in kinds), key=lambda t: t[0])}


def mutate(rule: dict, rng: random.Random) -> dict:
    """Add one filter or remove one filter. Nothing else changes."""
    fs = [tuple(f) for f in rule["filters"]]
    have = {f[0] for f in fs}
    missing = [t for t in FILTER_TYPES if t not in have]
    if fs and (not missing or rng.random() < 0.5):
        fs.pop(rng.randrange(len(fs)))
    else:
        fs.append(random_filter(rng, rng.choice(missing)))
    return dict(rule, filters=sorted(fs, key=lambda t: t[0]))


def normalize(rule: dict) -> dict:
    return dict(rule, filters=[tuple(f) for f in rule["filters"]])


def evaluate(markets, rules, seen: dict) -> list[dict]:
    out = []
    for r in rules:
        r = normalize(r)
        k = key(r)
        if k not in seen:
            seen[k] = score(markets, r)
        out.append({"rule": r, "key": k, **seen[k]})
    return out


def top(rows: list[dict], n: int = 25) -> list[dict]:
    return sorted(rows, key=lambda r: (r["z"], r["mean"]), reverse=True)[:n]


def fresh(rng, seen, count):
    out = []
    while len(out) < count:
        r = random_rule(rng)
        if key(normalize(r)) not in seen and all(key(normalize(r)) != key(normalize(o)) for o in out):
            out.append(r)
    return out


def run_search(search_markets: list[dict], seed: int = 7, cycles: int = 3) -> dict:
    """The whole loop on the SEARCH window only. Returns every round's top 25 and the number of distinct rules evaluated."""
    rng = random.Random(seed)
    seen: dict = {}
    rounds, carried = [], []
    for c in range(1, cycles + 1):
        a_rows = evaluate(search_markets, fresh(rng, seen, 50), seen) + carried
        A = top(a_rows)
        B = top(evaluate(search_markets, fresh(rng, seen, 50), seen))
        pool = A + B
        mutants, tries = [], 0
        while len(mutants) < 50 and tries < 5000:
            tries += 1
            m = mutate(rng.choice(pool)["rule"], rng)
            if all(key(normalize(m)) != x["key"] for x in mutants):
                mutants.append({"rule": normalize(m), "key": key(normalize(m))})
        C = top(evaluate(search_markets, [x["rule"] for x in mutants], seen))
        carried = C
        rounds += [{"cycle": c, "phase": "A", "top": A}, {"cycle": c, "phase": "B", "top": B}, {"cycle": c, "phase": "C", "top": C}]
    return {"rounds": rounds, "evaluated": len(seen), "seen": seen}


def shuffle_within_day(ms: list[dict], seed: int) -> list[dict]:
    """Same markets, same prices, but each market's result swapped with another market's from the SAME day. A pure noise world."""
    rng = random.Random(seed)
    by = defaultdict(list)
    for m in ms:
        by[m["day"]].append(m)
    out = []
    for day, items in by.items():
        res = [m["res"] for m in items]
        rng.shuffle(res)
        out += [dict(m, res=r) for m, r in zip(items, res)]
    return sorted(out, key=lambda m: m["close"])


def holdout_report(final: list[dict], holdout: list[dict]) -> list[dict]:
    """The one place the holdout is read: the final saved rules, once."""
    return [{**{k: v for k, v in r.items() if k not in ("seen",)}, "hold": score(holdout, r["rule"])} for r in final]


def save(name: str, rows: list[dict]) -> None:
    OUT.mkdir(exist_ok=True)
    slim = [{"rank": i + 1, "rule": describe(r["rule"]), "spec": {**r["rule"], "filters": [list(f) for f in r["rule"]["filters"]]},
             "n": r["n"], "mean_cents": round(r["mean"] * 100, 3), "z": round(r["z"], 3) if r["z"] != float("-inf") else None}
            for i, r in enumerate(rows)]
    (OUT / f"{name}.json").write_text(json.dumps(slim, indent=1))


def main(seed: int = 7, cycles: int = 3) -> None:
    markets, _ = load_markets()
    ms = prep(markets)
    search, hold = split_days(ms)
    print(f"{len(ms)} markets; search window {len(search)} (first {len({m['day'] for m in search})} days), holdout {len(hold)} locked until the end.\n")
    real = run_search(search, seed, cycles)
    null_world = shuffle_within_day(search, seed + 1)
    null = run_search(null_world, seed, cycles)
    for r in real["rounds"]:
        save(f"cycle{r['cycle']}_{r['phase']}_top25", r["top"])
    print("round        best z (real)  25th z (real)   best z (shuffled)  25th z (shuffled)")
    for a, b in zip(real["rounds"], null["rounds"]):
        ta, tb = a["top"], b["top"]
        print(f"c{a['cycle']} {a['phase']}   {ta[0]['z']:>13.2f} {ta[-1]['z']:>14.2f} {tb[0]['z']:>17.2f} {tb[-1]['z']:>18.2f}")
    n = real["evaluated"]
    print(f"\ndistinct rules evaluated: {n}. Best of N on pure noise is expected near z = {math.sqrt(2 * math.log(n)):.2f}.")
    final = real["rounds"][-1]["top"]
    nfinal = null["rounds"][-1]["top"]
    print("\nHOLDOUT (read once, for the final 25 only; the shuffled column is the same rules on a shuffled holdout):")
    rep = holdout_report(final, hold)
    nrep = holdout_report(nfinal, shuffle_within_day(hold, seed + 2))
    pos = sum(1 for r in rep if r["hold"]["mean"] > 0)
    print(f"  real: {pos} of {len(rep)} positive on the holdout; mean net {sum(r['hold']['mean'] for r in rep) / len(rep) * 100:+.2f}c; best z {max(r['hold']['z'] for r in rep):+.2f}")
    npos = sum(1 for r in nrep if r["hold"]["mean"] > 0)
    print(f"  noise: {npos} of {len(nrep)} positive; mean net {sum(r['hold']['mean'] for r in nrep) / len(nrep) * 100:+.2f}c; best z {max(r['hold']['z'] for r in nrep):+.2f}")
    OUT.mkdir(exist_ok=True)
    (OUT / "holdout_final25.json").write_text(json.dumps([{"rule": describe(r["rule"]), "search_n": r["n"], "search_mean_cents": round(r["mean"] * 100, 3),
        "search_z": round(r["z"], 3), "holdout_n": r["hold"]["n"], "holdout_mean_cents": round(r["hold"]["mean"] * 100, 3),
        "holdout_z": round(r["hold"]["z"], 3) if r["hold"]["z"] != float("-inf") else None} for r in rep], indent=1))
    print("\nVERDICT: this is a search. FALSIFIED unless a rule beats both the noise control and the holdout, and even then it only earns a forward test.")


if __name__ == "__main__":
    main()
