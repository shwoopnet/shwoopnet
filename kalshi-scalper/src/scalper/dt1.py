"""DT1 (README, Pre-registration: DT1): a shallow decision tree that skips L1 entries it flags as losers. Rules fixed in the README before any tree was fitted.
Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.dt1
"""
from __future__ import annotations

import math
import random
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import lstrats as L
from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB
from .scalps import Z_BAR

FEATURES = ("price", "side_yes", "spread", "d1", "d3", "d_open", "log_vol", "hour_utc", "is_gold", "is_eth", "prev_yes")
MAX_DEPTH = 3
MIN_LEAF = 150
SKIP_AT = -0.005               # skip entries whose leaf's TRAIN mean net is at or below -0.5c
TRAIN_DAYS = 20
MIN_SKIPPED = 100
NULL_REPS = 200
ENTRY_LEFT = L.L1["left_s"]
BAND = L.L1["band"]


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def mid_fav(side: str, bid: float, ask: float) -> float:
    m = (bid + ask) / 2.0
    return m if side == "yes" else 1.0 - m


def build_entries(markets: dict) -> list[dict]:
    """One row per L1 entry that has every feature. `markets` is {ticker: {series, close_ts, result, candles: {end_ts: (bid, ask, vol)}}}.
    Only candles ending at or before the entry candle (360 s before the close) and the previous market's RESULT are read."""
    close_by = {(m["series"], m["close_ts"]): m for m in markets.values()}
    rows = []
    for t, m in markets.items():
        if m["result"] not in ("yes", "no"):
            continue
        cs = m["candles"]
        c0 = cs.get(m["close_ts"] - ENTRY_LEFT)
        if c0 is None or not valid_quote(c0[0], c0[1]):
            continue
        pick = L.favorite(c0[0], c0[1], BAND)
        if pick is None:
            continue
        side, price = pick
        c1, c3 = cs.get(m["close_ts"] - ENTRY_LEFT - 60), cs.get(m["close_ts"] - ENTRY_LEFT - 180)
        first = next((cs[e] for e in sorted(cs) if valid_quote(cs[e][0], cs[e][1]) and e <= m["close_ts"] - ENTRY_LEFT), None)
        if c1 is None or c3 is None or first is None or not valid_quote(c1[0], c1[1]) or not valid_quote(c3[0], c3[1]):
            continue
        now = mid_fav(side, c0[0], c0[1])
        prev = close_by.get((m["series"], m["close_ts"] - 900))
        prev_yes = 0.5 if prev is None or prev["result"] not in ("yes", "no") else (1.0 if prev["result"] == "yes" else 0.0)
        vol = c0[2] if c0[2] is not None else 0.0
        x = [price, 1.0 if side == "yes" else 0.0, c0[1] - c0[0], now - mid_fav(side, c1[0], c1[1]), now - mid_fav(side, c3[0], c3[1]), now - mid_fav(side, first[0], first[1]),
             math.log1p(max(vol, 0.0)), float(datetime.fromtimestamp(m["close_ts"], timezone.utc).hour), 1.0 if m["series"] == "KXGOLD15M" else 0.0,
             1.0 if m["series"] == "KXETH15M" else 0.0, prev_yes]
        yes = m["result"] == "yes"
        rows.append({"ticker": t, "series": m["series"], "close_ts": m["close_ts"], "day": _day(m["close_ts"]), "x": x, "net": L.net(side, price, yes)})
    return sorted(rows, key=lambda r: r["close_ts"])


def fit_tree(X: np.ndarray, y: np.ndarray, depth: int = MAX_DEPTH, min_leaf: int = MIN_LEAF) -> dict:
    """A regression tree: splits at the deciles of each feature, chosen by variance reduction, never leaving fewer than `min_leaf` rows on a side."""
    node = {"mean": float(y.mean()), "n": int(len(y))}
    if depth == 0 or len(y) < 2 * min_leaf:
        return node
    best = None
    base = float(((y - y.mean()) ** 2).sum())
    for j in range(X.shape[1]):
        for thr in np.unique(np.quantile(X[:, j], np.linspace(0.1, 0.9, 9))):
            left = X[:, j] <= thr
            nl = int(left.sum())
            if nl < min_leaf or len(y) - nl < min_leaf:
                continue
            gain = base - float(((y[left] - y[left].mean()) ** 2).sum()) - float(((y[~left] - y[~left].mean()) ** 2).sum())
            if best is None or gain > best[0] + 1e-15:
                best = (gain, j, float(thr), left)
    if best is None or best[0] <= 0:
        return node
    _, j, thr, left = best
    node.update({"feat": j, "thr": thr, "left": fit_tree(X[left], y[left], depth - 1, min_leaf), "right": fit_tree(X[~left], y[~left], depth - 1, min_leaf)})
    return node


def leaf_of(tree: dict, x) -> dict:
    while "feat" in tree:
        tree = tree["left"] if x[tree["feat"]] <= tree["thr"] else tree["right"]
    return tree


def skip_mask(tree: dict, X: np.ndarray) -> np.ndarray:
    return np.array([leaf_of(tree, x)["mean"] <= SKIP_AT for x in X], dtype=bool)


def shuffled_within_series(rows: list[dict], rng: random.Random) -> np.ndarray:
    """The training net values permuted among entries of the SAME series: a tree fitted to this has nothing real to find."""
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["series"]].append(i)
    y = np.array([r["net"] for r in rows], dtype=float)
    out = y.copy()
    for idx in by.values():
        vals = [y[i] for i in idx]
        rng.shuffle(vals)
        for i, v in zip(idx, vals):
            out[i] = v
    return out


def improvement_per_day(valid_rows: list[dict], skipped: np.ndarray) -> float:
    days = len({r["day"] for r in valid_rows}) or 1
    return -sum(r["net"] for r, s in zip(valid_rows, skipped) if s) / days


def verdict(valid_rows: list[dict], skipped: np.ndarray, null: list[float]) -> tuple[str, dict]:
    sk = [r for r, s in zip(valid_rows, skipped) if s]
    kept = [r for r, s in zip(valid_rows, skipped) if not s]
    if len(sk) < MIN_SKIPPED:
        return "NOT_ENOUGH_DATA", {"skipped": len(sk)}
    mean, _, z = cluster_mean_z([(r["day"], r["net"]) for r in sk])
    imp = improvement_per_day(valid_rows, skipped)
    p95 = sorted(null)[int(0.95 * (len(null) - 1))] if null else float("inf")
    days = sorted({r["day"] for r in valid_rows})
    mid = days[len(days) // 2]
    h1 = [r["net"] for r in sk if r["day"] < mid]
    h2 = [r["net"] for r in sk if r["day"] >= mid]
    base = sum(r["net"] for r in valid_rows) / len(valid_rows)
    kept_mean = sum(r["net"] for r in kept) / len(kept) if kept else float("-inf")
    ok = (mean < 0 and z <= -Z_BAR and imp > p95 and h1 and h2 and sum(h1) / len(h1) < 0 and sum(h2) / len(h2) < 0 and kept_mean > base)
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), {"skipped": len(sk), "mean": mean, "z": z, "imp": imp, "p95": p95, "kept": kept_mean, "base": base,
                                                          "h1": sum(h1) / len(h1) if h1 else None, "h2": sum(h2) / len(h2) if h2 else None}


def describe(tree: dict, indent: str = "") -> list[str]:
    if "feat" not in tree:
        return [f"{indent}leaf: train mean {tree['mean'] * 100:+.2f}c over {tree['n']} entries" + ("  -> SKIP" if tree["mean"] <= SKIP_AT else "")]
    out = [f"{indent}if {FEATURES[tree['feat']]} <= {tree['thr']:.4f}:"]
    out += describe(tree["left"], indent + "    ")
    out.append(f"{indent}else:")
    out += describe(tree["right"], indent + "    ")
    return out


def load_markets() -> dict:
    db = sqlite3.connect(DB)
    markets: dict = {}
    for t, s, close_ts, res in db.execute("SELECT ticker, series, close_ts, result FROM market WHERE series IN ('KXBTC15M','KXGOLD15M','KXETH15M')"):
        markets[t] = {"series": s, "close_ts": close_ts, "result": res, "candles": {}}
    for t, end, bc, ac, v in db.execute("SELECT ticker, end_ts, bid_c, ask_c, volume FROM candle WHERE series IN ('KXBTC15M','KXGOLD15M','KXETH15M')"):
        if t in markets and bc is not None and ac is not None:
            markets[t]["candles"][end] = (bc, ac, v)
    return markets


def main() -> None:
    rows = build_entries(load_markets())
    t0 = rows[0]["close_ts"]
    cut = t0 + TRAIN_DAYS * 86400
    train = [r for r in rows if r["close_ts"] < cut]
    valid = [r for r in rows if r["close_ts"] >= cut]
    print(f"{len(rows)} L1 entries with every feature: TRAIN {len(train)} (before {_day(cut)}), VALIDATION {len(valid)}. Signal counts first.\n")
    Xt = np.array([r["x"] for r in train]); yt = np.array([r["net"] for r in train])
    Xv = np.array([r["x"] for r in valid])
    tree = fit_tree(Xt, yt)
    print("The tree fitted on TRAIN:")
    print("\n".join(describe(tree)))
    skip = skip_mask(tree, Xv)
    rng = random.Random(23)
    null = []
    for _ in range(NULL_REPS):
        tr = fit_tree(Xt, shuffled_within_series(train, rng))
        null.append(improvement_per_day(valid, skip_mask(tr, Xv)))
    v, s = verdict(valid, skip, null)
    c = lambda x: f"{x * 100:+.2f}c"
    print(f"\nDT1: skipped {int(skip.sum())} of {len(valid)} validation entries ({skip.mean():.1%})")
    if "mean" in s:
        print(f"  skipped entries' mean net {c(s['mean'])} (day clustered z {s['z']:+.2f}); halves {c(s['h1']) if s['h1'] is not None else 'n/a'} / {c(s['h2']) if s['h2'] is not None else 'n/a'}")
        print(f"  traded entries' mean net {c(s['kept'])} against baseline {c(s['base'])}")
        print(f"  improvement {c(s['imp'])} per day; shuffled-label null 5th/50th/95th percentile: {c(sorted(null)[int(0.05 * (len(null) - 1))])} / {c(sorted(null)[len(null) // 2])} / {c(s['p95'])}")
    print(f"  -> {v}")


if __name__ == "__main__":
    main()
