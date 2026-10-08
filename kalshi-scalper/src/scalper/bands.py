"""B1 to B3: which L1 price bands to trade (rules in the README, fixed before this file existed).

B1 walk-forward: choose bands on one half of the days, trade them on the other half, both ways round. A band is chosen if its net per contract is above zero after the
cent rounding at two contracts, with at least 100 entries in the choosing half. B2 trades only 88c to 95c and B3 only 90c to 97c on all days. The comparison is always against
all entries over the same days, and the fair-market null applies the same selection to outcomes drawn from each market's own late price.

Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.bands
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

from . import exits as EX
from . import feerounding as FR
from . import lstrats as L
from .calibration import cluster_mean_z
from .scalps import STRESS, fee, load as load_markets

BANDS = ((0.88, 0.90, "88c to 90c"), (0.90, 0.92, "90c to 92c"), (0.92, 0.95, "92c to 95c"), (0.95, 0.9701, "95c to 97c"))
MIN_SELECT_N = 100
MIN_N = 300
MIN_DAYS = 5
PASS_Z = 2.4
NULL_REPS = 500


def band_of(price: float) -> int | None:
    for i, (lo, hi, _) in enumerate(BANDS):
        if lo - 1e-9 <= price < hi - 1e-9 or (i == len(BANDS) - 1 and lo - 1e-9 <= price <= hi):
            return i
    return None


def split_days(entries: list[dict]) -> tuple[set, set]:
    days = sorted({e["day"] for e in entries})
    h = len(days) // 2
    return set(days[:h]), set(days[h:])


def rounded_net(es: list[dict], count: int = 2) -> float:
    return FR.net_per_contract(es, count, True) if es else 0.0


def choose(entries: list[dict], days: set) -> set:
    """Bands chosen on the entries of `days`: cent-rounded net above zero and at least MIN_SELECT_N entries there."""
    by = defaultdict(list)
    for e in entries:
        if e["day"] in days and band_of(e["price"]) is not None:
            by[band_of(e["price"])].append(e)
    return {i for i, es in by.items() if len(es) >= MIN_SELECT_N and rounded_net(es) > 0}


def walk_forward(entries: list[dict]) -> tuple[list[dict], dict]:
    h1, h2 = split_days(entries)
    chosen, trades = {}, []
    for name, sel, test in (("fold1", h1, h2), ("fold2", h2, h1)):
        keep = choose(entries, sel)
        chosen[name] = sorted(keep)
        trades += [e for e in entries if e["day"] in test and band_of(e["price"]) in keep]
    return trades, chosen


def fixed(entries: list[dict], lo: float, hi: float) -> list[dict]:
    return [e for e in entries if lo - 1e-9 <= e["price"] <= hi + 1e-9 and band_of(e["price"]) is not None]


def mean(es: list[dict], key: str = "net") -> float:
    return sum(e[key] for e in es) / len(es) if es else 0.0


def diff_stats(chosen_set: list[dict], base: list[dict]) -> tuple[float, float]:
    """Per UTC day, the chosen set's mean net minus the baseline's mean net, over days where the chosen set traded: (mean difference, day clustered z)."""
    a, b = defaultdict(list), defaultdict(list)
    for e in chosen_set:
        a[e["day"]].append(e["net"])
    for e in base:
        b[e["day"]].append(e["net"])
    days = sorted(set(a) & set(b))
    if len(days) < 2:
        return 0.0, 0.0
    d = [(str(i), sum(a[x]) / len(a[x]) - sum(b[x]) / len(b[x])) for i, x in enumerate(days)]
    m, _, z = cluster_mean_z(d)
    return m, z


def redraw(entries: list[dict], late: dict, rng: random.Random) -> list[dict]:
    """The fair-market world: each market's outcome drawn from its own late price, nets recomputed (the entry price and fee are the real ones)."""
    outs = {}
    for e in entries:
        if e["ticker"] not in outs:
            outs[e["ticker"]] = rng.random() < late.get(e["ticker"], 0.5)
    new = []
    for e in entries:
        yes = outs[e["ticker"]]
        won = 1.0 if (yes if e["side"] == "yes" else not yes) else 0.0
        new.append(dict(e, net=won - e["price"] - fee(e["price"]), stress=won - e["price"] - fee(e["price"], STRESS), gross=won - e["price"]))
    return new


def null_p95(entries: list[dict], late: dict, select, reps: int = NULL_REPS, seed: int = 5) -> float:
    rng = random.Random(seed)
    ds = []
    for _ in range(reps):
        w = redraw(entries, late, rng)
        sel = select(w)
        ds.append(mean(sel) - mean(w) if sel else 0.0)
    ds.sort()
    return ds[int(0.95 * (len(ds) - 1))]


def verdict(trades: list[dict], base: list[dict], halves: list[list[dict]], null95: float | None, z_bar: float = PASS_Z) -> tuple[str, dict]:
    dm, dz = diff_stats(trades, base)
    s = {"n": len(trades), "days": len({e["day"] for e in trades}), "mean": mean(trades), "base": mean(base), "diff": dm, "diff_z": dz,
         "stress": mean(trades, "stress"), "halves": [mean(h) for h in halves], "null95": null95, "rounded2": rounded_net(trades)}
    if s["n"] < MIN_N or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    ok = (dm > 0 and dz >= z_bar and s["mean"] > 0 and all(h > 0 for h in s["halves"]) and s["stress"] > 0 and (null95 is None or dm > null95))
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), s


def band_table(entries: list[dict]) -> list[dict]:
    rows = []
    for i, (lo, hi, name) in enumerate(BANDS):
        es = [e for e in entries if band_of(e["price"]) == i]
        if not es:
            continue
        n = len(es)
        wins = sum(1 for e in es if e["gross"] + e["price"] > 0.5)
        p = sum(e["price"] for e in es) / n
        need = sum(e["price"] + fee(e["price"]) for e in es) / n
        rate = wins / n
        se = math.sqrt(rate * (1 - rate) / n)
        rows.append({"band": name, "n": n, "price": p, "win": rate, "need": need, "margin": rate - need, "se": se, "net": mean(es), "rounded2": rounded_net(es),
                     "per_dollar": sum(e["net"] for e in es) / sum(e["price"] for e in es)})
    return rows


def main() -> None:
    markets, _ = load_markets()
    entries = [e for e in L.hold_rule(markets, **L.L1) if band_of(e["price"]) is not None]
    late = EX.late_prices(markets)
    h1d, h2d = split_days(entries)
    base_h = [[e for e in entries if e["day"] in h1d], [e for e in entries if e["day"] in h2d]]
    f = lambda x: f"{x * 100:+.2f}c"
    print(f"{len(entries)} L1 entries in 88c to 97c over {len({e['day'] for e in entries})} days; baseline mean {f(mean(entries))}\n")
    print("INFORMATION (all days, post hoc, decides nothing): win rate against the win rate needed to break even")
    print("band         n   price   win rate  needed  margin (se)       net   rounded x2  per $ risked")
    for r in band_table(entries):
        print(f"{r['band']:<11}{r['n']:>5}  {r['price'] * 100:5.1f}c  {r['win'] * 100:6.1f}%  {r['need'] * 100:5.1f}%  {r['margin'] * 100:+5.1f} ({r['se'] * 100:.1f})  {f(r['net'])}  {f(r['rounded2'])}  {r['per_dollar'] * 100:+.2f}%")
    print()
    trades, chosen = walk_forward(entries)
    names = lambda ks: ", ".join(BANDS[k][2] for k in ks) or "none"
    print(f"B1 walk-forward: fold 1 (chosen on the first {len(h1d)} days) trades {names(chosen['fold1'])}; fold 2 (chosen on the last {len(h2d)} days) trades {names(chosen['fold2'])}")
    fold_tests = [[e for e in trades if e["day"] in h2d], [e for e in trades if e["day"] in h1d]]
    v, s = verdict(trades, entries, fold_tests, null_p95(entries, late, lambda w: walk_forward(w)[0]))
    out = [("B1", v, s)]
    for name, lo, hi in (("B2 (88c to 95c)", 0.88, 0.9499), ("B3 (90c to 97c)", 0.90, 0.9701)):
        tr = fixed(entries, lo, hi)
        v2, s2 = verdict(tr, entries, [[e for e in tr if e["day"] in h1d], [e for e in tr if e["day"] in h2d]], null_p95(entries, late, lambda w, lo=lo, hi=hi: fixed(w, lo, hi)))
        out.append((name, v2, s2))
    for name, v, s in out:
        print(f"{name}: {s['n']} trades on {s['days']} days, mean {f(s['mean'])} vs baseline {f(s['base'])}: difference {f(s['diff'])} (day clustered z {s['diff_z']:+.2f}), fair-market 95th percentile {f(s['null95'])}")
        print(f"   halves {f(s['halves'][0])} / {f(s['halves'][1])}, fees x{STRESS} {f(s['stress'])}, two contracts rounded {f(s['rounded2'])}; baseline rounded {f(rounded_net(entries))}")
        print(f"   VERDICT (bar z>={PASS_Z}, n>={MIN_N}, both halves, fees x{STRESS}, above the fair-market difference): {v}\n")
    print("No verdict here means trade.")


if __name__ == "__main__":
    main()
