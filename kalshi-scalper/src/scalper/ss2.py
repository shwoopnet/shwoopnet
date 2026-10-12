"""SS2: a 1,760 cell search on 40 days of Bitcoin, gold and Ethereum 15 minute markets, with a train and validation split and a fair-market placebo. Rules fixed in the README
("Pre-registration: SS2") before this file ran on any market. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.ss2
"""
from __future__ import annotations

import itertools
import random
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .cheapscalp import side_prices
from .scalps import STRESS, fee, load as load_markets

SERIES = ("KXBTC15M", "KXGOLD15M", "KXETH15M", "ALL")
LEFTS = (840, 720, 600, 480, 360)
BANDS = ((0.05, 0.15), (0.15, 0.30), (0.30, 0.50), (0.50, 0.70), (0.70, 0.82), (0.82, 0.88), (0.88, 0.93), (0.93, 0.97))
CONDS = ("none", "momentum", "dip", "wide", "tight")
SCALP_LEFTS = (840, 720, 600)
TARGETS = (0.03, 0.05)
EXIT_LEFT_S = 480
MOVE = 0.03
TRAIN_DAYS = 24
MIN_TRAIN_N = 150
MIN_N = 300
MIN_DAYS = 5
Z_BAR = 3.0
TOP = 10


def _cells():
    out = []
    for s, l, b, c in itertools.product(SERIES, LEFTS, BANDS, CONDS):
        out.append(dict(series=s, left=l, band=b, cond=c, exit="hold", target=None))
    for s, l, t, b, c in itertools.product(SERIES, SCALP_LEFTS, TARGETS, BANDS, CONDS):
        out.append(dict(series=s, left=l, band=b, cond=c, exit="scalp", target=t))
    return out


CELLS = _cells()


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def find_entry(candles_by: dict, close_ts: int, cell: dict):
    """The cell's one entry: a side whose ask is in the band and whose condition holds on the candle ending cell['left'] s before the close. YES before NO."""
    c = candles_by.get(close_ts - cell["left"])
    if c is None or not valid_quote(c[1], c[2]):
        return None
    prev = candles_by.get(close_ts - cell["left"] - 60)
    spread = c[2] - c[1]
    if cell["cond"] == "wide" and spread < 0.03 - 1e-9:
        return None
    if cell["cond"] == "tight" and spread > 0.01 + 1e-9:
        return None
    for side in ("yes", "no"):
        ask, bid = side_prices(side, c)
        if ask is None or not (cell["band"][0] - 1e-9 <= ask <= cell["band"][1] + 1e-9):
            continue
        if cell["cond"] in ("momentum", "dip"):
            if prev is None or not valid_quote(prev[1], prev[2]):
                continue
            pask, _ = side_prices(side, prev)
            if pask is None:
                continue
            if cell["cond"] == "momentum" and ask - pask < MOVE - 1e-9:
                continue
            if cell["cond"] == "dip" and pask - ask < MOVE - 1e-9:
                continue
        return {"side": side, "ask": ask, "bid": bid}
    return None


def _scalp(candles_by: dict, close_ts: int, cell: dict, e: dict, mult: float):
    side, ask, left = e["side"], e["ask"], cell["left"]
    cost = ask + fee(ask, mult)
    for end in sorted(t for t in candles_by if EXIT_LEFT_S <= close_ts - t < left):
        c = candles_by[end]
        _, bid = side_prices(side, c)
        if bid is not None and valid_quote(c[1], c[2]) and bid >= ask + cell["target"] - 1e-9 and bid >= 0.001:
            return bid - cost - fee(bid, mult)
    cx = candles_by.get(close_ts - EXIT_LEFT_S)
    if cx is None:
        return None
    _, bid = side_prices(side, cx)
    bid = 0.0 if bid is None or bid < 0.001 else bid
    return bid - cost - fee(bid, mult)


def build(markets: list[tuple]):
    """Per market: its candle dict, close, series and settled result. Computed once."""
    return [(t, s, {c[0]: c for c in cs}, close, res) for t, s, cs, close, res in markets if res in ("yes", "no")]


def rows_for(cell: dict, built: list[tuple]) -> list[dict]:
    out = []
    for ticker, series, by, close_ts, res in built:
        if cell["series"] != "ALL" and series != cell["series"]:
            continue
        e = find_entry(by, close_ts, cell)
        if e is None:
            continue
        if cell["exit"] == "hold":
            win = 1.0 if res == e["side"] else 0.0
            net = win - e["ask"] - fee(e["ask"], 1.0)
            stress = win - e["ask"] - fee(e["ask"], STRESS)
        else:
            net = _scalp(by, close_ts, cell, e, 1.0)
            if net is None:
                continue
            stress = _scalp(by, close_ts, cell, e, STRESS)
            win = None
        out.append({"day": _day(close_ts), "close_ts": close_ts, "net": net, "stress": stress if stress is not None else net, "ask": e["ask"], "bid": e["bid"], "mid": (e["ask"] + e["bid"]) / 2, "win": win})
    return out


def split_ts(built: list[tuple]) -> int:
    return min(b[3] for b in built) + TRAIN_DAYS * 86400


def summary(rows: list[dict]):
    n = len(rows)
    if not n:
        return None
    wins = sum(r["net"] for r in rows if r["net"] > 0)
    losses = -sum(r["net"] for r in rows if r["net"] < 0)
    return {"n": n, "days": len({r["day"] for r in rows}), "mean": sum(r["net"] for r in rows) / n, "pf": wins / losses if losses > 0 else float("inf"),
            "stress": sum(r["stress"] for r in rows) / n}


def select(by_cell: list[tuple[dict, list[dict]]], top: int = TOP):
    """The cells the training days pick: highest mean net among cells with at least MIN_TRAIN_N entries on MIN_DAYS days."""
    ok = []
    for cell, rows in by_cell:
        s = summary(rows)
        if s and s["n"] >= MIN_TRAIN_N and s["days"] >= MIN_DAYS:
            ok.append((s["mean"], cell, rows, s))
    ok.sort(key=lambda x: -x[0])
    return ok[:top]


def verdict(rows: list[dict]):
    s = summary(rows)
    if s is None or s["n"] < MIN_N or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    mean, se, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    ok = z >= Z_BAR and mean > 0 and s["stress"] > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), dict(s, z=z)


def label(c: dict) -> str:
    ex = "hold" if c["exit"] == "hold" else "scalp +%dc" % round(c["target"] * 100)
    return f"{c['series']:<9} {c['left']:>3}s band {c['band'][0]:.2f}-{c['band'][1]:.2f} {c['cond']:<8} {ex}"


def placebo_rows(rows: list[dict], rng: random.Random) -> list[dict]:
    """A fair market: the same entries, prices, days and fees, with the outcome drawn as a Bernoulli at the entry's mid price. Hold cells only."""
    out = []
    for r in rows:
        win = 1.0 if rng.random() < r["mid"] else 0.0
        out.append(dict(r, net=win - r["ask"] - fee(r["ask"], 1.0), stress=win - r["ask"] - fee(r["ask"], STRESS), win=win))
    return out


def main() -> None:
    markets, _ = load_markets()
    built = build(markets)
    cut = split_ts(built)
    train = [b for b in built if b[3] < cut]
    valid = [b for b in built if b[3] >= cut]
    print(f"{len(built)} settled markets; train {len(train)} (before {_day(cut)}), validation {len(valid)}. {len(CELLS)} cells.\n")
    tr_by, va_by = [], {}
    for i, cell in enumerate(CELLS):
        tr_by.append((cell, rows_for(cell, train)))
        va_by[i] = rows_for(cell, valid)
    picks = select(tr_by)
    idx = {id(c): i for i, c in enumerate(CELLS)}
    print(f"cells with enough training data: {sum(1 for c, r in tr_by if (summary(r) or {}).get('n', 0) >= MIN_TRAIN_N)}; cells with a positive training mean: {sum(1 for c, r in tr_by if summary(r) and summary(r)['mean'] > 0 and summary(r)['n'] >= MIN_TRAIN_N)}\n")
    print("TRAINING: top 10 by mean net, then validation read once")
    print(f"{'train n':>8} {'mean c':>7} {'PF':>5}  {'val n':>6} {'val mean c':>10} {'z':>6}  verdict    cell")
    best_ver = []
    for mean, cell, rows, s in picks:
        v, vs = verdict(va_by[idx[id(cell)]])
        best_ver.append(v)
        if vs and "z" in vs:
            print(f"{s['n']:>8} {mean*100:>7.2f} {s['pf']:>5.2f}  {vs['n']:>6} {vs['mean']*100:>10.2f} {vs['z']:>6.2f}  {v[:10]:<10} {label(cell)}")
        else:
            print(f"{s['n']:>8} {mean*100:>7.2f} {s['pf']:>5.2f}  {(vs or {}).get('n', 0):>6} {'':>10} {'':>6}  {v[:10]:<10} {label(cell)}")
    print("\nverdicts of the 10:", {k: best_ver.count(k) for k in set(best_ver)})
    # Fair-market placebo on the hold cells.
    hold = [(i, c) for i, c in enumerate(CELLS) if c["exit"] == "hold"]
    rng = random.Random(7)
    pbest, pvalid, pz = [], [], []
    for rep in range(10):
        by = [(c, placebo_rows(tr_by[i][1], rng)) for i, c in hold]
        pk = select(by)
        if not pk:
            continue
        pbest.append(pk[0][0] * 100)
        zs = []
        for mean, cell, rows, s in pk:
            i = [j for j, c in hold if c is cell][0]
            vr = placebo_rows(va_by[i], rng)
            vv, vs = verdict(vr)
            if vs and "z" in vs:
                zs.append(vs["z"])
        if zs:
            pz.append(max(zs))
    real_hold = select([(c, r) for (c, r) in tr_by if c["exit"] == "hold"])
    if pbest and real_hold:
        pbest.sort()
        print(f"\nPLACEBO (fair market, 10 reps, hold cells): best training mean {min(pbest):+.2f}c to {max(pbest):+.2f}c, median {pbest[len(pbest)//2]:+.2f}c; real best hold cell {real_hold[0][0]*100:+.2f}c.")
        if pz:
            pz.sort()
            print(f"  placebo best validation z of the frozen 10: median {pz[len(pz)//2]:+.2f}, max {max(pz):+.2f}  (the bar is {Z_BAR})")


if __name__ == "__main__":
    main()
