"""SS1: a train and validation search for an opening scalp that is flat before L1 buys. Rules fixed in the README ("Pre-registration: SS1") before this file ran on any market.

216 cells, selected on the training days only (highest mean net with at least 300 entries on 5 days), ONE cell frozen and read once on the validation days. Verdict words: FALSIFIED,
NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

Usage: python -m scalper.ss1
"""
from __future__ import annotations

import itertools
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .cheapscalp import side_prices
from .scalps import STRESS, fee, load as load_markets

ENTRY_LEFTS = (840, 780, 720, 660)
BANDS = ((0.20, 0.40), (0.40, 0.60), (0.60, 0.80))
CONDITIONS = ("none", "momentum", "dip")
TARGETS = (0.03, 0.05, 0.08)
STOPS = (None, 0.04)
EXIT_LEFT_S = 480
MOVE = 0.03
TRAIN_DAYS = 21
MIN_N = 300
MIN_DAYS = 5
Z_BAR = 2.5
CELLS = [dict(left=l, band=b, cond=c, target=t, stop=s) for l, b, c, t, s in itertools.product(ENTRY_LEFTS, BANDS, CONDITIONS, TARGETS, STOPS)]


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def find_entry(candles: list[tuple], close_ts: int, cell: dict):
    """The cell's one entry minute: a side's ask is in the band and the condition holds on the candle ending cell["left"] s before the close. Never another minute, never two entries."""
    by = {c[0]: c for c in candles}
    left = cell["left"]
    c = by.get(close_ts - left)
    if c is None or not valid_quote(c[1], c[2]):
        return None
    prev = by.get(close_ts - left - 60)
    for side in ("yes", "no"):
        ask, _ = side_prices(side, c)
        if ask is None or not (cell["band"][0] - 1e-9 <= ask <= cell["band"][1] + 1e-9):
            continue
        if cell["cond"] != "none":
            if prev is None or not valid_quote(prev[1], prev[2]):
                continue
            pask, _ = side_prices(side, prev)
            if pask is None:
                continue
            if cell["cond"] == "momentum" and ask - pask < MOVE - 1e-9:
                continue
            if cell["cond"] == "dip" and pask - ask < MOVE - 1e-9:
                continue
        return {"side": side, "ask": ask, "left": left}
    return None


def trade(candles: list[tuple], close_ts: int, cell: dict, mult: float = 1.0):
    e = find_entry(candles, close_ts, cell)
    if e is None:
        return None
    side, ask = e["side"], e["ask"]
    cost = ask + fee(ask, mult)
    for c in sorted((c for c in candles if EXIT_LEFT_S <= close_ts - c[0] < e["left"]), key=lambda c: c[0]):
        _, bid = side_prices(side, c)
        if bid is None or not valid_quote(c[1], c[2]) or bid < 0.001:
            continue
        if bid >= ask + cell["target"] - 1e-9:
            return {"net": bid - cost - fee(bid, mult), "how": "target", "exit_left": close_ts - c[0]}
        if cell["stop"] is not None and bid <= ask - cell["stop"] + 1e-9:
            return {"net": bid - cost - fee(bid, mult), "how": "stop", "exit_left": close_ts - c[0]}
    cx = next((c for c in candles if close_ts - c[0] == EXIT_LEFT_S), None)
    if cx is None:
        return {"unresolvable": True}
    _, bid = side_prices(side, cx)
    bid = 0.0 if bid is None or bid < 0.001 else bid
    return {"net": bid - cost - fee(bid, mult), "how": "time", "exit_left": EXIT_LEFT_S}


def run(markets: list[tuple], cell: dict):
    rows, unresolvable = [], 0
    for ticker, series, candles, close_ts, _res in markets:
        t = trade(candles, close_ts, cell)
        if t is None:
            continue
        if t.get("unresolvable"):
            unresolvable += 1
            continue
        s = trade(candles, close_ts, cell, STRESS)
        rows.append(dict(t, ticker=ticker, series=series, day=_day(close_ts), close_ts=close_ts, stress=s["net"] if s and "net" in s else t["net"]))
    return rows, unresolvable


def split_ts(markets: list[tuple]) -> int:
    """Train is everything closing before this: TRAIN_DAYS after the first close, a function of the data's first date and nothing else."""
    return min(m[3] for m in markets) + TRAIN_DAYS * 86400


def summary(rows: list[dict]):
    n = len(rows)
    if n == 0:
        return None
    mean = sum(r["net"] for r in rows) / n
    wins = sum(r["net"] for r in rows if r["net"] > 0)
    losses = -sum(r["net"] for r in rows if r["net"] < 0)
    return {"n": n, "days": len({r["day"] for r in rows}), "mean": mean, "pf": (wins / losses) if losses > 0 else float("inf"),
            "stress": sum(r["stress"] for r in rows) / n, "hit": sum(1 for r in rows if r["how"] == "target") / n}


def select(train_by_cell: list[tuple[dict, list[dict]]]):
    """The one cell the training days pick: highest mean net among cells with at least MIN_N entries on MIN_DAYS days. None if no cell qualifies."""
    best = None
    for cell, rows in train_by_cell:
        s = summary(rows)
        if s and s["n"] >= MIN_N and s["days"] >= MIN_DAYS and (best is None or s["mean"] > best[2]["mean"]):
            best = (cell, rows, s)
    return best


def verdict(rows: list[dict]):
    s = summary(rows)
    if s is None or s["n"] < MIN_N or s["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA", s
    mean, se, z = cluster_mean_z([(r["day"], r["net"]) for r in rows])
    ok = z >= Z_BAR and mean > 0 and s["stress"] > 0
    return ("NOT_YET_FALSIFIED" if ok else "FALSIFIED"), dict(s, z=z, se=se)


def label(cell: dict) -> str:
    return f"entry {cell['left']}s, band {cell['band'][0]:.2f}-{cell['band'][1]:.2f}, {cell['cond']}, target +{cell['target']*100:.0f}c, stop {'none' if cell['stop'] is None else '-%dc' % round(cell['stop']*100)}"


def main() -> None:
    markets, _ = load_markets()
    cut = split_ts(markets)
    train = [m for m in markets if m[3] < cut]
    valid = [m for m in markets if m[3] >= cut]
    print(f"{len(markets)} markets; train {len(train)} (before {_day(cut)}), validation {len(valid)}. {len(CELLS)} cells.\n")
    by_cell = []
    for cell in CELLS:
        rows, _ = run(train, cell)
        by_cell.append((cell, rows))
    ranked = sorted(((summary(r), c) for c, r in by_cell if summary(r)), key=lambda x: -x[0]["mean"])
    print("TRAINING DAYS, top 8 by mean net (the selector), then the 8 with the best profit factor (printed, not used):")
    print(f"{'n':>5} {'days':>5} {'mean c':>8} {'PF':>6} {'hit%':>6}  cell")
    for s, c in ranked[:8]:
        print(f"{s['n']:>5} {s['days']:>5} {s['mean']*100:>8.2f} {s['pf']:>6.2f} {s['hit']*100:>6.1f}  {label(c)}")
    print("  --- best profit factor, n >= 300:")
    for s, c in sorted([x for x in ranked if x[0]["n"] >= MIN_N], key=lambda x: -x[0]["pf"])[:8]:
        print(f"{s['n']:>5} {s['days']:>5} {s['mean']*100:>8.2f} {s['pf']:>6.2f} {s['hit']*100:>6.1f}  {label(c)}")
    n_pos = sum(1 for s, _ in ranked if s["mean"] > 0)
    print(f"\ncells with a positive training mean: {n_pos} of {len(ranked)}")
    pick = select(by_cell)
    if pick is None:
        print("\nNo cell has 300 training entries on 5 days: NOT_ENOUGH_DATA. Nothing is read on validation.")
        return
    cell, rows, s = pick
    print(f"\nFROZEN: {label(cell)}  (train n={s['n']}, mean {s['mean']*100:+.2f}c, PF {s['pf']:.2f})")
    v_rows, unres = run(valid, cell)
    v, vs = verdict(v_rows)
    print(f"VALIDATION, read once: {v}")
    if vs and "z" in vs:
        print(f"  n={vs['n']} days={vs['days']} mean {vs['mean']*100:+.2f}c  z {vs['z']:+.2f}  PF {vs['pf']:.2f}  hit {vs['hit']*100:.1f}%  fees x1.2 {vs['stress']*100:+.2f}c  unresolvable {unres}")
    elif vs:
        print(f"  n={vs['n']} days={vs['days']} mean {vs['mean']*100:+.2f}c  (too few to judge)")


if __name__ == "__main__":
    main()
