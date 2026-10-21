"""TREE1 (a small decision tree) and PAT1 (nearest pattern) as SKIP rules on L1's own entries (README, Pre-registration: TREE1 and PAT1).

Both only ever say "skip this entry"; neither opens a position or reads a result to decide an entry. Walk-forward by UTC day: the decision for a day
uses entries of EARLIER days only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.tree1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import heapq
import random
import sqlite3
import sys
from bisect import bisect_left
from collections import defaultdict

from . import lstrats as L
from .analyze import valid_quote
from .filters import diff_z, summarize
from .paths import DATA_DIR, DB
from .scalps import STRESS, fee

# ---- fixed in the README before the first run ----
Z_BAR = 2.5                  # the filters' 2.4 raised for two more tries
DIFF_Z_BAR = 2.0
MIN_KEPT = 300
MIN_DAYS = 5
BURN_DAYS = 14
DEPTH = 2
MIN_LEAF = 250
N_CUTS = 9                   # decile cut points
PAT_LEN = 9                  # candles in the pattern: every candle the market has up to the decision candle
PAT_K = 200
PAT_SKIP_LOSSES = 24
PLACEBO_REPS = 100
SEED = 11
RESULT = DATA_DIR / "tree1_result.txt"
FEATURES = ["price", "spread", "d1", "d3", "d5", "rng5", "dip", "hi_gap", "hour", "dow", "is_btc", "is_eth", "is_gold"]


def _mid(c: tuple, side: str):
    """The bought side's mid at one candle (end, bid_c, ask_c, bid_h, ask_l), or None if the quote is not usable."""
    if not valid_quote(c[1], c[2]):
        return None
    m = (c[1] + c[2]) / 2
    return m if side == "yes" else round(1 - m, 4)


def row_features(candles: list[tuple], t: int, side: str, price: float, close_ts: int, series: str):
    """(features, pattern) for one entry. Uses only candles whose end is at or before t (the decision candle); anything missing gives None
    for that learner and the row is excluded from it and counted, never filled."""
    by = {c[0]: c for c in candles if c[0] <= t}
    c0 = by.get(t)
    if c0 is None:
        return None, None
    mids = [_mid(by[t - 60 * k], side) if (t - 60 * k) in by else None for k in range(PAT_LEN)]   # mids[0] is the decision candle, mids[8] the oldest, the market opening
    pat = None if any(m is None for m in mids) else [m - mids[0] for m in mids]
    feats = None
    if all(m is not None for m in mids[:6]):
        if side == "yes":
            spread, bid_c, bid_h = c0[2] - c0[1], c0[1], c0[3]
        else:
            spread, bid_c, bid_h = c0[2] - c0[1], 1 - c0[2], (None if c0[4] is None else 1 - c0[4])
        earlier = [_mid(c, side) for e, c in by.items()]
        earlier = [m for m in earlier if m is not None]
        if bid_h is not None and earlier:
            hour = (close_ts // 3600) % 24
            dow = ((close_ts // 86400) + 3) % 7                # 1970-01-01 was a Thursday
            feats = [price, spread, mids[0] - mids[1], mids[0] - mids[3], mids[0] - mids[5], max(mids[:6]) - min(mids[:6]),
                     min(earlier), bid_h - bid_c, float(hour), float(dow),
                     1.0 if series == "KXBTC15M" else 0.0, 1.0 if series == "KXETH15M" else 0.0, 1.0 if series == "KXGOLD15M" else 0.0]
    return feats, pat


def load_rows(db_path) -> list[dict]:
    """L1's entries (lstrats.hold_rule with L1) with their features and patterns, oldest first."""
    db = sqlite3.connect(db_path)
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.ask_l, m.close_ts, m.result "
         "FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
    for s, tk, end, bc, ac, bh, al, close_ts, res in db.execute(q):
        m = by[tk]
        m["c"].append((end, bc, ac, bh, al)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    markets = [(tk, m["s"], m["c"], m["close"], m["res"]) for tk, m in by.items()]
    entries = L.hold_rule(markets, **L.L1)
    cmap = {m[0]: m[2] for m in markets}
    for e in entries:
        t = e["close_ts"] - L.L1["left_s"]
        e["feats"], e["pat"] = row_features(cmap[e["ticker"]], t, e["side"], e["price"], e["close_ts"], e["series"])
    return entries


# ---------------------------------------------------------------- the tree

def cut_points(rows: list[dict]) -> list[list[float]]:
    """Per feature, up to N_CUTS decile cut points of the whole sample's feature values (labels never enter)."""
    out = []
    ok = [r["feats"] for r in rows if r["feats"] is not None]
    for f in range(len(FEATURES)):
        vals = sorted(x[f] for x in ok)
        pts = sorted({vals[min(len(vals) - 1, (len(vals) * (j + 1)) // (N_CUTS + 1))] for j in range(N_CUTS)})
        # a cut that equals the largest value would send every row left; drop it
        out.append([p for p in pts if p < vals[-1]])
    return out


def _bin(x: float, cuts: list[float]) -> int:
    return bisect_left(cuts, x)           # x <= cuts[j] <=> bin <= j


def fit_tree(X: list[list[float]], y: list[float], cuts: list[list[float]], depth: int = DEPTH, min_leaf: int = MIN_LEAF):
    """Greedy regression tree. Returns a leaf mean (float) or (feature, cut index, left, right). Split chosen by the largest
    sum of squared error removed; a split leaving a side under min_leaf rows is not allowed."""
    idx = list(range(len(y)))
    bins = [[_bin(x[f], cuts[f]) for f in range(len(FEATURES))] for x in X]

    def grow(ix: list[int], d: int):
        n = len(ix)
        tot = sum(y[i] for i in ix)
        mean = tot / n if n else 0.0
        if d == 0 or n < 2 * min_leaf:
            return mean
        best = None
        for f in range(len(FEATURES)):
            nb = len(cuts[f]) + 1
            cnt = [0] * nb
            sm = [0.0] * nb
            for i in ix:
                b = bins[i][f]
                cnt[b] += 1
                sm[b] += y[i]
            nl, sl = 0, 0.0
            for j in range(nb - 1):
                nl += cnt[j]; sl += sm[j]
                nr, sr = n - nl, tot - sl
                if nl < min_leaf or nr < min_leaf:
                    continue
                gain = sl * sl / nl + sr * sr / nr - tot * tot / n
                if best is None or gain > best[0] + 1e-12:
                    best = (gain, f, j)
        if best is None or best[0] <= 1e-12:
            return mean
        _, f, j = best
        left = [i for i in ix if bins[i][f] <= j]
        right = [i for i in ix if bins[i][f] > j]
        return (f, j, grow(left, d - 1), grow(right, d - 1))

    return grow(idx, depth)


def predict(tree, x: list[float], cuts: list[list[float]]) -> float:
    while isinstance(tree, tuple):
        f, j, left, right = tree
        tree = left if _bin(x[f], cuts[f]) <= j else right
    return tree


def describe(tree, cuts, pad: str = "") -> list[str]:
    if not isinstance(tree, tuple):
        return [f"{pad}leaf: training mean net {tree * 100:+.2f}c"]
    f, j, left, right = tree
    return ([f"{pad}if {FEATURES[f]} <= {cuts[f][j]:.4f}:"] + describe(left, cuts, pad + "   ")
            + [f"{pad}else:"] + describe(right, cuts, pad + "   "))


# ---------------------------------------------------------------- walk-forward

def day_order(rows: list[dict]) -> list[str]:
    return sorted({r["day"] for r in rows})


def tree_walk(rows: list[dict], y: list[float], cuts, burn: int = BURN_DAYS) -> dict[int, bool]:
    """{row index: skipped?} for every out-of-sample row with features. A day's decisions use rows of strictly earlier days only."""
    days = day_order(rows)
    by_day = defaultdict(list)
    for i, r in enumerate(rows):
        by_day[r["day"]].append(i)
    out: dict[int, bool] = {}
    for di, day in enumerate(days):
        if di < burn:
            continue
        past = [i for d in days[:di] for i in by_day[d] if rows[i]["feats"] is not None]
        if len(past) < 2 * MIN_LEAF:
            continue
        tree = fit_tree([rows[i]["feats"] for i in past], [y[i] for i in past], cuts)
        for i in by_day[day]:
            if rows[i]["feats"] is not None:
                out[i] = predict(tree, rows[i]["feats"], cuts) < 0
    return out


def neighbours(rows: list[dict], burn: int = BURN_DAYS) -> dict[int, list[int]]:
    """For each out-of-sample row with a pattern, the PAT_K nearest rows (squared distance) from strictly earlier days."""
    days = day_order(rows)
    pos = {d: i for i, d in enumerate(days)}
    pool: list[int] = []
    out: dict[int, list[int]] = {}
    by_day = defaultdict(list)
    for i, r in enumerate(rows):
        by_day[r["day"]].append(i)
    for di, day in enumerate(days):
        if di >= burn and pool:
            for i in by_day[day]:
                p = rows[i]["pat"]
                if p is None:
                    continue
                out[i] = [j for _, j in heapq.nsmallest(PAT_K, ((sum((a - b) ** 2 for a, b in zip(p, rows[j]["pat"])), j) for j in pool))]
        pool.extend(i for i in by_day[day] if rows[i]["pat"] is not None)
    return out


def pat_walk(nb: dict[int, list[int]], y: list[float]) -> dict[int, bool]:
    return {i: sum(1 for j in js if y[j] < 0) >= PAT_SKIP_LOSSES for i, js in nb.items() if len(js) == PAT_K}


# ---------------------------------------------------------------- judging

def shuffled_within_day(rows: list[dict], y: list[float], rng: random.Random) -> list[float]:
    by_day = defaultdict(list)
    for i, r in enumerate(rows):
        by_day[r["day"]].append(i)
    z = list(y)
    for ix in by_day.values():
        vals = [y[i] for i in ix]
        rng.shuffle(vals)
        for i, v in zip(ix, vals):
            z[i] = v
    return z


def gain(decisions: dict[int, bool], y: list[float]) -> float:
    """Mean net of the KEPT entries minus the mean net of all decided entries, per contract."""
    kept = [y[i] for i, s in decisions.items() if not s]
    allv = [y[i] for i in decisions]
    return (sum(kept) / len(kept) - sum(allv) / len(allv)) if kept else 0.0


def judge(rows: list[dict], decisions: dict[int, bool], null95: float | None, name: str):
    """Verdict on one learner's out-of-sample decisions (the README's pass bar, minus the backward holdout)."""
    kept = [rows[i] for i, s in decisions.items() if not s]
    skipped = [rows[i] for i, s in decisions.items() if s]
    s = summarize(kept)
    dm, dz = diff_z(kept, skipped)
    allv = [rows[i]["net"] for i in decisions]
    g = (s["mean"] - sum(allv) / len(allv)) if kept else 0.0
    s.update(diff=dm, diff_z=dz, gain=g, null95=null95, decided=len(decisions), skipped=len(skipped))
    if s["n"] < MIN_KEPT or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    ok = (s["mean"] > 0 and s["z"] >= Z_BAR and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0
          and dm > 0 and dz >= DIFF_Z_BAR and null95 is not None and g > null95)
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), s


def fmt(name: str, v: str, s: dict) -> str:
    c = lambda x: f"{x * 100:+.2f}c"
    return (f"{name}: decided {s['decided']}, skipped {s['skipped']} ({s['skipped'] / max(1, s['decided']) * 100:.1f}%), kept n={s['n']} on {s['days']} days"
            f"\n   kept net {c(s['mean'])} z {s['z']:+.2f} halves {c(s['h1'])} / {c(s['h2'])} fees x{STRESS} {c(s['stress'])}"
            f"\n   kept minus skipped {c(s['diff'])} (day clustered z {s['diff_z']:+.2f}); gain over all decided {c(s['gain'])}; placebo 95th percentile {c(s['null95']) if s['null95'] is not None else 'n/a'}"
            f"\n   VERDICT: {v}")


def holdout(rows_hist: list[dict], rows_new: list[dict], kind: str, cuts) -> tuple[bool, str]:
    """Frozen rule fitted on ALL of rows_hist, applied to rows_new. Passes if kept beats skipped and beats all entries."""
    y = [r["net"] for r in rows_hist]
    if kind == "TREE1":
        past = [r for r in rows_hist if r["feats"] is not None]
        tree = fit_tree([r["feats"] for r in past], [r["net"] for r in past], cuts)
        dec = {i: predict(tree, r["feats"], cuts) < 0 for i, r in enumerate(rows_new) if r["feats"] is not None}
    else:
        pool = [r for r in rows_hist if r["pat"] is not None]
        dec = {}
        for i, r in enumerate(rows_new):
            if r["pat"] is None:
                continue
            nb = heapq.nsmallest(PAT_K, ((sum((a - b) ** 2 for a, b in zip(r["pat"], q["pat"])), k) for k, q in enumerate(pool)))
            dec[i] = sum(1 for _, k in nb if pool[k]["net"] < 0) >= PAT_SKIP_LOSSES
    kept = [rows_new[i]["net"] for i, s in dec.items() if not s]
    skip = [rows_new[i]["net"] for i, s in dec.items() if s]
    allv = [rows_new[i]["net"] for i in dec]
    if not kept or not allv:
        return False, f"{kind} holdout: nothing kept"
    km = sum(kept) / len(kept)
    sm = sum(skip) / len(skip) if skip else None
    am = sum(allv) / len(allv)
    ok = (sm is None or km > sm) and km > am
    return ok, (f"{kind} holdout on {len(allv)} entries: kept {len(kept)} at {km * 100:+.2f}c, skipped {len(skip)} at "
                f"{(sm * 100 if sm is not None else float('nan')):+.2f}c, all {am * 100:+.2f}c -> {'passes' if ok else 'fails'}")


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    rows = load_rows(DB)
    cuts = cut_points(rows)
    y = [r["net"] for r in rows]
    n_f = sum(1 for r in rows if r["feats"] is not None)
    n_p = sum(1 for r in rows if r["pat"] is not None)
    lines = [f"TREE1 / PAT1 on {len(rows)} L1 entries over {len(day_order(rows))} days; with features {n_f}, with pattern {n_p} (the rest excluded and counted)."]
    rng = random.Random(SEED)
    verdicts = {}
    t_dec = tree_walk(rows, y, cuts)
    nb = neighbours(rows)
    p_dec = pat_walk(nb, y)
    placebo = {"TREE1": [], "PAT1": []}
    for _ in range(PLACEBO_REPS):
        z = shuffled_within_day(rows, y, rng)
        placebo["TREE1"].append(gain(tree_walk(rows, z, cuts), z))
        placebo["PAT1"].append(gain(pat_walk(nb, z), z))
    for name, dec in (("TREE1", t_dec), ("PAT1", p_dec)):
        pl = sorted(placebo[name])
        p95 = pl[int(0.95 * (len(pl) - 1))]
        v, s = judge(rows, dec, p95, name)
        lines.append(fmt(name, v, s))
        verdicts[name] = v
    past = [r for r in rows if r["feats"] is not None]
    lines.append("Final TREE1 on all days (information):")
    lines += ["   " + x for x in describe(fit_tree([r["feats"] for r in past], [r["net"] for r in past], cuts), cuts)]
    for name in ("TREE1", "PAT1"):
        if verdicts[name] == "NOT_YET_FALSIFIED":
            older = load_rows(DATA_DIR / "l1b.sqlite")
            ok, txt = holdout(rows, older, name, cuts)
            lines.append(txt)
            if not ok:
                verdicts[name] = "FALSIFIED"
                lines.append(f"{name}: VERDICT after the backward holdout: FALSIFIED")
        else:
            lines.append(f"{name}: backward holdout not read (the main bar did not pass).")
    lines.append("Nothing here means trade. NOT_YET_FALSIFIED is a choice for the owner, never a switch.")
    text = "\n".join(lines)
    RESULT.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv)
