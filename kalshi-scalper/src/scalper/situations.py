"""Path situations: when a side reaches 70% early or late, how often does it flip?

EXPLORATORY. No verdict, no kill criterion, nothing here licenses a trade. It
describes what happened on the 30 days already seen. If a pattern looks different
from the price, that is a hypothesis, and it must be written down first and tested
on days this has not seen before anyone acts on it.

The comparison that matters. In a fair market a side that reaches 70% flips about
30% of the time, so "it flipped 28% of the time" is no finding at all. Every row
therefore prints the same-direction rate next to the price that side was
trading at when it triggered ("implied"), and the gap between them. The gap, not
the flip rate, is the thing to look at.

Definitions (fixed before the first run, 2026-10-05):
- Probability is the MID of the closing bid and ask of a 1 minute candle. A side
  "hits T" when its mid is at least T: YES when yes_mid >= T, NO when yes_mid <=
  1 - T. A bid-only reading would be slightly stricter; this is the market's
  chance as the app shows it.
- First window: the closing quotes 1 and 2 minutes after the market opens.
  Last window: the closing quotes 2 and 1 minutes before it closes. Two
  checkpoints each, so "first 2 minutes" is two looks, not a continuous watch.
- A quote must be usable (a real two sided book, no wider than 10c).
- One event per market per window: the first checkpoint at which a side hits T.
- Same direction: the triggered side wins. Flip: the other side wins.
- Tradability: buy that side at its ask at the trigger, hold to settlement, fee
  7% unrounded per contract, as in calibration.py.
- Thresholds: 70% is the question asked. 60% and 80% are printed as sensitivity so
  a result is not an accident of one threshold. Cuts examined: 3 thresholds x 2
  windows x 3 groupings (each series, and both).

Usage: python -m scalper.situations
"""
from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

from .analyze import valid_quote
from .calibration import cluster_mean_z, net_pnl
from .paths import DB

THRESHOLDS = (0.70, 0.60, 0.80)
HEADLINE = 0.70
FIRST = (60, 120)    # seconds after open of the two checkpoints
LAST = (120, 60)     # seconds before close of the two checkpoints


def first_trigger(quotes: list[tuple[float, float] | None], thr: float) -> tuple[str, float, float] | None:
    """(side, mid of that side, ask paid for that side) at the first checkpoint
    where a side's mid reaches thr, or None. quotes are (bid, ask) of the YES
    side in time order, or None where there is no candle."""
    for q in quotes:
        if q is None or not valid_quote(q[0], q[1]):
            continue
        bid, ask = q
        mid = (bid + ask) / 2
        if mid >= thr:
            return "yes", mid, ask
        if mid <= 1 - thr:
            return "no", 1 - mid, 1 - bid
    return None


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a rate. Plain +/- misbehaves near 0 and 1, which is where
    late-market rates live."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def summarise(events: list[tuple]) -> dict:
    """events: (side, mid_side, ask_side, same, net, day, close_ts)."""
    n = len(events)
    if n == 0:
        return {"n": 0}
    same = sum(e[3] for e in events)
    implied = sum(e[1] for e in events) / n
    lo, hi = wilson(same, n)
    mean, se, z = cluster_mean_z([(e[5], e[4]) for e in events])
    mid_t = (min(e[6] for e in events) + max(e[6] for e in events)) / 2
    halves = []
    for h in ([e for e in events if e[6] < mid_t], [e for e in events if e[6] >= mid_t]):
        halves.append((sum(x[3] for x in h) / len(h) - sum(x[1] for x in h) / len(h)) if h else 0.0)
    return {"n": n, "same": same / n, "flip": 1 - same / n, "implied": implied, "gap": same / n - implied,
            "lo": lo, "hi": hi, "net": mean, "net_z": z, "h1_gap": halves[0], "h2_gap": halves[1]}


def collect() -> tuple[dict, dict]:
    db = sqlite3.connect(DB)
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.open_ts, m.close_ts, m.result "
         "FROM candle c JOIN market m ON m.ticker = c.ticker "
         "WHERE c.end_ts - m.open_ts IN (60, 120) OR m.close_ts - c.end_ts IN (60, 120)")
    mk: dict = {}
    for series, ticker, end, bid, ask, o, c, res in db.execute(q):
        m = mk.setdefault(ticker, {"series": series, "open": {}, "close": {}, "close_ts": c, "result": res})
        if end - o in (60, 120):
            m["open"][end - o] = (bid, ask)
        if c - end in (60, 120):
            m["close"][c - end] = (bid, ask)
    events: dict = defaultdict(list)   # (series, window, thr) -> events
    skipped = {"unresolved": 0}
    for m in mk.values():
        if m["result"] not in ("yes", "no"):
            skipped["unresolved"] += 1
            continue
        day = datetime.fromtimestamp(m["close_ts"], timezone.utc).strftime("%Y-%m-%d")
        for window, quotes in (("first 2 min", [m["open"].get(s) for s in FIRST]),
                               ("last 2 min", [m["close"].get(s) for s in LAST])):
            for thr in THRESHOLDS:
                t = first_trigger(quotes, thr)
                if t is None:
                    continue
                side, mid, ask = t
                e = (side, mid, ask, m["result"] == side, net_pnl(side, ask, m["result"]), day, m["close_ts"])
                events[(m["series"], window, thr)].append(e)
                events[("BOTH", window, thr)].append(e)
    return events, {"markets": len(mk), **skipped}


def main() -> None:
    events, info = collect()
    if not events:
        print("No data. Run: python -m scalper.backfill")
        return
    print(f"{info['markets']} markets, 30 days. EXPLORATORY: no verdict. Compare 'same' with 'priced', not with 50%.\n")
    hdr = (f"{'window':>12} {'group':>9} {'n':>5} {'same':>6} {'flip':>6} {'priced':>7} {'gap':>6} "
           f"{'95% for same':>14} {'gap h1':>7} {'gap h2':>7} {'net/contract':>13} {'z':>5}")
    for thr in THRESHOLDS:
        print(f"--- a side reaches {thr:.0%}" + ("  (the question asked)" if thr == HEADLINE else "  (sensitivity)") + " ---")
        print(hdr)
        for window in ("first 2 min", "last 2 min"):
            for grp in ("KXBTC15M", "KXGOLD15M", "BOTH"):
                s = summarise(events.get((grp, window, thr), []))
                if s["n"] == 0:
                    continue
                print(f"{window:>12} {grp.replace('15M',''):>9} {s['n']:>5} {s['same']*100:>5.1f}% {s['flip']*100:>5.1f}% "
                      f"{s['implied']*100:>6.1f}% {s['gap']*100:>+5.1f} {s['lo']*100:>6.1f}-{s['hi']*100:<5.1f}% "
                      f"{s['h1_gap']*100:>+6.1f} {s['h2_gap']*100:>+6.1f} {s['net']*100:>+12.2f}c {s['net_z']:>5.1f}")
        print()
    print("gap = same-direction rate minus the price that side traded at when it triggered, in points.")
    print("net/contract = buy that side at its ask, hold to settlement, after fees. z is clustered by day.")
    print("Nothing here is a verdict. A gap that looks real is a hypothesis for days not yet seen.")


if __name__ == "__main__":
    main()
