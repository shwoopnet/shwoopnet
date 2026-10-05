"""Target scalps: buy at 40c or 50c, sell at 80c, otherwise hold to settlement.

Hypothesis H2 (fixed 2026-10-05, before this was run on any data): buying a side
at about 40c or about 50c and selling it at 80c, holding to settlement when 80c
is never reached, earns more than it costs.

Why it can look attractive and why the prior is zero. In a fair market a price at
40c reaches 80c before 0c half the time (40/80), and a price at 50c does so 62.5%
of the time. The payoff is lopsided to match (win 40c, lose 40c; win 30c, lose
50c), so the expected profit is ZERO before costs whatever the target. Costs are
the fee on the way in, the fee on the way out and the spread, about 4c. So H2 can
only work if prices CONTINUE (trend) more than a fair game, or are otherwise
wrong. The earlier path study found no continuation (a side reaching 70% early
kept going 74.8% against a price of 75.4%), so the expectation is FALSIFIED.

Counterparty: the person who sells us the contract at 40c to 50c, or buys it from
us at 80c, on a view that prices are momentum-driven and so lag a move. If they
are right, buying early in a move gets us 80c more often than 40c/80 says.

Rule (all fixed before the first run):
- Bands: ask of the side in [0.38, 0.42] ("40c") or [0.48, 0.52] ("50c").
- Entry: at the FIRST minute close, with at least 5 minutes left and a usable
  quote (real two sided book, spread 10c or less), where YES then NO has its ask
  in the band. One entry per market per band.
- Exit: the first LATER minute close at which that side's bid is 80c or more,
  sold at 80c (a resting limit order). Never on the entry minute itself.
  Otherwise held to settlement.
- Costs: entry at the ask, taker fee on the way in AND on the way out, 7%
  unrounded per contract. No stop.
- Unit: a market. Net profit per contract is the statistic.

Kill criteria. FALSIFIED unless, for at least one band: n >= MIN_N, mean net
profit positive with a day clustered z of at least Z_BAR (Bonferroni for the two
bands), positive in BOTH halves of the window, and positive with fees 20% higher.
Passing is NOT_YET_FALSIFIED: permission to test on data not yet seen, never
evidence of an edge. No verdict means "trade".

DESCRIPTIVE, affecting nothing above: touching by the minute's high instead of
its close, a maker (no fee) exit, and a stop 20c below entry. A stop does not
change the expected profit of a fair game; the table is there to show that.

Usage: python -m scalper.scalps
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z
from .paths import DB

# ---- fixed before the first run ----
BANDS = {"40c": (0.38, 0.42), "50c": (0.48, 0.52)}
TARGET = 0.80
MIN_LEFT_S = 300
FEE_RATE = 0.07
STRESS = 1.2
MIN_N = 300
Z_BAR = 2.1          # one sided about 0.025 (two bands), 29 degrees of freedom
STOP = 0.20          # descriptive variant only


def fee(price: float, mult: float = 1.0) -> float:
    return FEE_RATE * mult * price * (1 - price)


def sides(c: tuple) -> dict:
    """Per side: ask, closing bid, bid high. c = (end, bid_c, ask_c, bid_h, ask_l)."""
    _, bid, ask, bid_h, ask_l = c
    return {"yes": (ask, bid, bid_h), "no": (1 - bid, 1 - ask, None if ask_l is None else 1 - ask_l)}


def simulate(candles: list[tuple], close_ts: int, result: str, band: tuple[float, float],
             fee_mult: float = 1.0, touch: str = "close", exit_fee: bool = True,
             stop: float | None = None) -> dict | None:
    """One market, one band. candles: (end, bid_c, ask_c, bid_h, ask_l) in time
    order. Returns the trade, or None if there was no entry or no resolution."""
    if result not in ("yes", "no"):
        return None
    lo, hi = band
    entry = None
    for i, c in enumerate(candles):
        if close_ts - c[0] < MIN_LEFT_S or not valid_quote(c[1], c[2]):
            continue
        for side in ("yes", "no"):
            ask = sides(c)[side][0]
            if lo <= ask <= hi:
                entry = (i, side, ask)
                break
        if entry:
            break
    if entry is None:
        return None
    i, side, ask = entry
    cost = ask + fee(ask, fee_mult)
    for c in candles[i + 1:]:          # strictly later than the entry minute
        _, bid_c, bid_h = sides(c)[side]
        reached = (bid_h if (touch == "high" and bid_h is not None) else bid_c) >= TARGET
        if reached:
            out = TARGET - (fee(TARGET, fee_mult) if exit_fee else 0.0) - cost
            return {"side": side, "ask": ask, "outcome": "target", "net": out}
        if stop is not None and bid_c <= ask - stop:
            return {"side": side, "ask": ask, "outcome": "stop", "net": bid_c - fee(bid_c, fee_mult) - cost}
    won = result == side
    return {"side": side, "ask": ask, "outcome": "win" if won else "loss", "net": (1.0 if won else 0.0) - cost}


def judge(rows: dict[str, list[tuple]], midpoint: float) -> tuple[str, list[dict]]:
    """rows[band]: (day, close_ts, net, net_stressed)."""
    out, passed = [], False
    for band in sorted(rows):
        r = rows[band]
        mean, se, z = cluster_mean_z([(x[0], x[2]) for x in r])
        h1 = [x[2] for x in r if x[1] < midpoint]
        h2 = [x[2] for x in r if x[1] >= midpoint]
        m1 = sum(h1) / len(h1) if h1 else 0.0
        m2 = sum(h2) / len(h2) if h2 else 0.0
        stress = sum(x[3] for x in r) / len(r) if r else 0.0
        ok = len(r) >= MIN_N and z >= Z_BAR and m1 > 0 and m2 > 0 and stress > 0
        passed = passed or ok
        out.append({"band": band, "n": len(r), "mean": mean, "se": se, "z": z, "h1": m1, "h2": m2,
                    "stress": stress, "detectable": 2.8 * se if se != float("inf") else float("inf"), "ok": ok})
    return ("NOT_YET_FALSIFIED" if passed else "FALSIFIED"), out


def load() -> tuple[list[tuple], float]:
    db = sqlite3.connect(DB)
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, c.bid_h, c.ask_l, m.close_ts, m.result "
         "FROM candle c JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
    by: dict = defaultdict(lambda: {"c": [], "close": 0, "res": "", "s": ""})
    for s, t, end, bc, ac, bh, al, close_ts, res in db.execute(q):
        m = by[t]
        m["c"].append((end, bc, ac, bh, al)); m["close"] = close_ts; m["res"] = res; m["s"] = s
    closes = [m["close"] for m in by.values()]
    mid = (min(closes) + max(closes)) / 2 if closes else 0.0
    return [(t, m["s"], m["c"], m["close"], m["res"]) for t, m in by.items()], mid


def run_variant(markets: list[tuple], **kw) -> dict[str, list[tuple]]:
    rows: dict[str, list[tuple]] = {b: [] for b in BANDS}
    mult = kw.get("fee_mult", 1.0)
    for _, _, candles, close_ts, res in markets:
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        for b, band in BANDS.items():
            t = simulate(candles, close_ts, res, band, **kw)
            if t:
                s = simulate(candles, close_ts, res, band, **{**kw, "fee_mult": STRESS})
                rows[b].append((day, close_ts, t["net"], s["net"], t["outcome"]))
    return rows


def main() -> None:
    markets, mid = load()
    if not markets:
        print("No data. Run: python -m scalper.backfill")
        return
    rows = run_variant(markets)
    v, summ = judge({b: [x[:4] for x in r] for b, r in rows.items()}, mid)
    print(f"{len(markets)} markets. H2: buy at ~40c or ~50c, sell at 80c, else hold to settlement. Net profit per contract, cents.\n")
    print(f"{'band':>5} {'n':>6} {'mean':>7} {'se':>6} {'z':>6} {'1st half':>9} {'2nd half':>9} {'fees x1.2':>10} {'detectable':>11} {'passes':>7}")
    for s in summ:
        print(f"{s['band']:>5} {s['n']:>6} {s['mean']*100:>7.2f} {s['se']*100:>6.2f} {s['z']:>6.2f} {s['h1']*100:>9.2f} "
              f"{s['h2']*100:>9.2f} {s['stress']*100:>10.2f} {s['detectable']*100:>10.2f}c {str(s['ok']):>7}")
    print(f"\nVERDICT (pre-registered, bar z>={Z_BAR}, n>={MIN_N}, both halves, fees x{STRESS}): {v}")
    print("  " + ("No band clears every criterion: no 40c/50c to 80c scalp edge as large as 'detectable'."
                   if v == "FALSIFIED" else "Permission to test on unseen data. Not evidence of an edge."))

    print("\nHow the trades ended, and the hit rate needed to break even (the '50/50' question):")
    print(f"{'band':>5} {'target':>8} {'settle win':>11} {'settle loss':>12} {'avg win':>9} {'avg loss':>9} {'break-even wins':>16} {'got':>7}")
    for b in BANDS:
        r = rows[b]
        if not r:
            continue
        wins = [x[2] for x in r if x[2] > 0]
        losses = [x[2] for x in r if x[2] <= 0]
        n = len(r)
        cnt = lambda k: sum(1 for x in r if x[4] == k)
        need = (-sum(losses) / len(losses)) / (sum(wins) / len(wins) + (-sum(losses) / len(losses))) if wins and losses else float("nan")
        print(f"{b:>5} {cnt('target')/n*100:>7.1f}% {cnt('win')/n*100:>10.1f}% {cnt('loss')/n*100:>11.1f}% "
              f"{(sum(wins)/len(wins)*100 if wins else 0):>8.1f}c {(sum(losses)/len(losses)*100 if losses else 0):>8.1f}c "
              f"{need*100:>15.1f}% {len(wins)/n*100:>6.1f}%")

    print("\nDESCRIPTIVE ONLY, affects nothing above. Mean net per contract, cents:")
    print(f"{'variant':>34} {'40c':>8} {'50c':>8}")
    for name, kw in (("primary (close touch, taker exit)", {}), ("touch by the minute's high", {"touch": "high"}),
                     ("maker exit (no exit fee)", {"exit_fee": False}), ("stop 20c below entry", {"stop": STOP})):
        rr = run_variant(markets, **kw)
        cells = [f"{sum(x[2] for x in rr[b]) / len(rr[b]) * 100:>8.2f}" if rr[b] else f"{'-':>8}" for b in BANDS]
        print(f"{name:>34} " + " ".join(cells))


if __name__ == "__main__":
    main()
