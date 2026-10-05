"""Does a scalp have any room? Measure it from recorded books.

For every recorded market and several holding horizons, compare the mid-price
move over that horizon with the cost of crossing the spread and paying fees on
both legs. "move>cost" assumes perfect foresight of direction, so it is a
ceiling and not an estimate. The column that matters is "needs": the share of
direction calls that must be RIGHT just to break even. A guesser at 50% loses
the whole cost on every trade.

Two cuts expose what the headline averages hide:
- by price level: fees are cheap near 0 and 100, dear near 50
- by time left: prices collapse toward 0 or 100 as a market closes, and that
  late move inflates the average without being an opportunity anyone can
  call in advance

Samples overlap (a 10s window starts every 2s), so n is not a count of
independent trades. The header reports distinct markets and hours instead.

The last thing it prints is a VERDICT from a rule written down before the data
existed (see README, "Decision rule"). The thresholds below are part of that
rule. Changing one after seeing a result voids that result: the earlier verdict
stands and the new rule counts as a new trial.

Two data sources. The default is the live recorder's 2 second snapshots. With
--candles it reads Kalshi's own 1 minute history fetched by `scalper.backfill`,
which has no sleep gaps. The rule, thresholds and cuts are identical; only the
quotes come from a different place. Candles carry one quote per minute (the
closing bid and ask), so only 60s and 120s holds exist there.

Usage: python -m scalper.analyze [--candles]
"""
from __future__ import annotations

import sqlite3
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime

from .fees import round_trip_cost
from .recorder import DB
from .status import GAP_SECONDS

HORIZONS = (10, 30, 60, 120)  # seconds
CUT_HORIZON = 60
# An exit snapshot more than this far past the target time means the recorder
# was not running in between. That is not an N second hold, it is whatever
# happened across the hole, and the move over a hole is larger than the move
# over the window it claims to be. Such windows are dropped, never stretched.
MAX_SLIP_S = 6.0

# ---- Decision rule, fixed on 2026-10-02 before further data was seen ----
RULE_MIN_HOURS = 72     # market time PER SERIES (about 3 days of recording) before any other verdict
RULE_MIN_N = 500        # samples a bucket needs overall
RULE_MIN_HALF_N = 250   # and in each half of the recording period
RULE_BAR = 0.60         # break-even hit rate a bucket must beat, in BOTH halves

# ---- Candle source, fixed on 2026-10-05 before the first candle run ----
CANDLE_HORIZONS = (60, 120)
CANDLE_MAX_SPREAD = 0.10  # a book wider than this at either end is not a market: dropped, counted
PRICE_BANDS = [(0.0, 0.10), (0.10, 0.30), (0.30, 0.70), (0.70, 0.90), (0.90, 1.0001)]
TIME_BANDS = [(600, 1e9, "over 10 min left"), (300, 600, "5 to 10 min"),
              (120, 300, "2 to 5 min"), (0, 120, "under 2 min")]


def needed_accuracy(avg_cost: float, avg_move: float) -> float | None:
    """Hit rate needed to break even, assuming symmetric moves: a right call
    earns the move, a wrong one loses it, and both pay the cost.
        (2p - 1) * move - cost = 0   ->   p = 0.5 + cost / (2 * move)
    Above 1.0 means break-even is impossible even with a perfect predictor."""
    if not avg_move or avg_move <= 0:
        return None
    return 0.5 + avg_cost / (2 * avg_move)


def _acc(x: float | None) -> str:
    if x is None:
        return "-"
    return "never" if x > 1 else f"{x:.0%}"


def _secs_left(close_iso: str | None, ts: float) -> float | None:
    try:
        return datetime.fromisoformat(close_iso.replace("Z", "+00:00")).timestamp() - ts
    except Exception:
        return None


def _summ(rows: list[tuple]) -> tuple:
    n = len(rows)
    cost = sum(r[0] for r in rows) / n
    move = sum(r[1] for r in rows) / n
    beat = sum(r[1] > r[0] for r in rows) / n
    return n, cost, move, beat, needed_accuracy(cost, move)


def find_exit(ts: list[float], i: int, hold: float) -> int | None:
    """Index of the snapshot to exit at for an entry at ts[i], or None. None
    when the data ends first, or when the first snapshot at least `hold`
    seconds on is more than MAX_SLIP_S late (the recorder was off)."""
    j = bisect_left(ts, ts[i] + hold, i + 1)
    if j >= len(ts) or ts[j] - ts[i] - hold > MAX_SLIP_S:
        return None
    return j


def market_hours(by: dict) -> dict[str, float]:
    """Hours of market time actually RECORDED, per series. Only the intervals
    between consecutive snapshots count, and only when they are no longer than
    GAP_SECONDS, so a sleeping laptop adds nothing. (Measuring first-to-last
    snapshot of each market would credit a market for time the recorder was
    off in the middle of it.) Each market is about 15 minutes, so one series
    records about one market-hour per wall-clock hour; summing across series
    would double it. The rule needs the thinner series to have enough."""
    out: dict[str, float] = defaultdict(float)
    for (series, _), pts in by.items():
        for a, b in zip(pts, pts[1:]):
            if b[0] - a[0] <= GAP_SECONDS:
                out[series] += (b[0] - a[0]) / 3600
    return dict(out)


def valid_quote(bid: float | None, ask: float | None) -> bool:
    """A usable two sided quote. A market that has just opened shows a bid of
    0.1c and an ask of $1.00 (an empty book), and nothing can be traded there."""
    return (bid is not None and ask is not None and bid >= 0.001 and ask <= 0.999
            and ask >= bid and ask - bid <= CANDLE_MAX_SPREAD)


def candle_windows(series: str, close_ts: int, candles: list[tuple]) -> tuple[list[tuple], int]:
    """Holds built from one market's candles: (end_ts, bid_close, ask_close) each.
    Entry at one candle's closing quote, exit at the closing quote exactly N
    seconds later. A missing minute or an unusable quote drops the window; it is
    never bridged. Returns (records, dropped)."""
    by_t = {c[0]: c for c in candles}
    recs, dropped = [], 0
    for end, bid, ask in sorted(candles):
        for h in CANDLE_HORIZONS:
            nxt = by_t.get(end + h)
            if nxt is None:
                continue  # end of the market or a missing minute
            if not (valid_quote(bid, ask) and valid_quote(nxt[1], nxt[2])):
                dropped += 1
                continue
            recs.append((series, h, (ask + bid) / 2, close_ts - end, round_trip_cost(ask, bid),
                         abs((nxt[2] + nxt[1]) / 2 - (ask + bid) / 2), float(end)))
    return recs, dropped


def collect_candles() -> tuple[list[tuple], dict]:
    db = sqlite3.connect(DB)
    q = ("SELECT c.series, c.ticker, c.end_ts, c.bid_c, c.ask_c, m.close_ts FROM candle c "
         "JOIN market m ON m.ticker = c.ticker ORDER BY c.ticker, c.end_ts")
    by: dict = defaultdict(list)
    close: dict = {}
    for series, ticker, end, b, a, close_ts in db.execute(q):
        by[(series, ticker)].append((end, b, a))
        close[ticker] = close_ts
    recs: list[tuple] = []
    dropped = 0
    hours: dict[str, float] = defaultdict(float)
    for (series, ticker), cs in by.items():
        r, d = candle_windows(series, close[ticker], cs)
        recs += r
        dropped += d
        hours[series] += len(cs) / 60  # one candle is one recorded minute
    per = dict(hours)
    return recs, {"markets": len(by), "hours_by_series": per, "dropped": dropped,
                  "hours": min(per.values()) if per else 0.0,
                  "dropped_label": "windows dropped for an unusable quote (empty or wider than 10c)"}


def collect() -> tuple[list[tuple], dict]:
    db = sqlite3.connect(DB)
    q = ("SELECT series,ticker,ts,yes_bid,yes_ask,close_time FROM snap "
         "WHERE yes_bid IS NOT NULL AND yes_ask IS NOT NULL ORDER BY ticker,ts")
    by = defaultdict(list)
    for s, t, ts, b, a, c in db.execute(q):
        by[(s, t)].append((ts, b, a, c))
    recs = []  # (series, horizon, mid, secs_left, cost, move, ts)
    dropped = 0
    for (s, _), pts in by.items():
        tss = [p[0] for p in pts]
        for i, (ts, b, a, c) in enumerate(pts):
            for h in HORIZONS:
                j = find_exit(tss, i, h)
                if j is None:
                    dropped += 1
                    continue
                _, b2, a2, _ = pts[j]
                recs.append((s, h, (a + b) / 2, _secs_left(c, ts),
                             round_trip_cost(a, b), abs((b2 + a2) / 2 - (b + a) / 2), ts))
    per = market_hours(by)
    return recs, {"markets": len(by), "hours_by_series": per, "dropped": dropped,
                  "hours": min(per.values()) if per else 0.0}


def _buckets() -> list[tuple[str, object]]:
    """The 9 cuts per series the rule looks at. Fixed: adding one is a new trial."""
    out = [(f"price {lo*100:.0f}-{min(hi,1)*100:.0f}c", lambda r, lo=lo, hi=hi: lo <= r[2] < hi)
           for lo, hi in PRICE_BANDS]
    out += [(f"time left {label}", lambda r, lo=lo, hi=hi: r[3] is not None and lo <= r[3] < hi)
            for lo, hi, label in TIME_BANDS]
    return out


def verdict(recs: list[tuple], hours: float) -> tuple[str, list[str]]:
    """Apply the pre-registered rule. There is deliberately no verdict that
    means "trade this": the best outcome is NOT_YET_FALSIFIED, which only
    permits writing down a hypothesis and testing it on data not yet recorded.

    NOT_ENOUGH_DATA     under RULE_MIN_HOURS of market time in the thinner series, or no usable rows
    NOT_YET_FALSIFIED   some bucket needs under RULE_BAR in BOTH halves of the period
    FALSIFIED           no bucket does: a directional scalp has no room here
    """
    rows60 = [r for r in recs if r[1] == CUT_HORIZON]
    if hours < RULE_MIN_HOURS or not rows60:
        return "NOT_ENOUGH_DATA", [f"{hours:.1f} of {RULE_MIN_HOURS} hours recorded"]
    mid_t = (min(r[6] for r in rows60) + max(r[6] for r in rows60)) / 2
    found: list[str] = []
    for series in sorted({r[0] for r in rows60}):
        mine = [r for r in rows60 if r[0] == series]
        for label, pred in _buckets():
            rows = [r for r in mine if pred(r)]
            halves = [[r for r in rows if r[6] < mid_t], [r for r in rows if r[6] >= mid_t]]
            if len(rows) < RULE_MIN_N or any(len(h) < RULE_MIN_HALF_N for h in halves):
                continue
            needs = [needed_accuracy(sum(r[4] for r in h) / len(h), sum(r[5] for r in h) / len(h)) for h in halves]
            if all(n is not None and n < RULE_BAR for n in needs):
                found.append(f"{series} {label}: needs {needs[0]:.0%} then {needs[1]:.0%}")
    return ("NOT_YET_FALSIFIED", found) if found else ("FALSIFIED", [])


def main() -> None:
    candles = "--candles" in sys.argv
    recs, info = collect_candles() if candles else collect()
    if not recs:
        print("Not enough data yet." + (" Run: python -m scalper.backfill" if candles else ""))
        return
    if candles:
        print("Source: Kalshi 1 minute history (closing bid and ask), holds of 60s and 120s only")
    per = ", ".join(f"{k} {v:.1f}h" for k, v in sorted(info["hours_by_series"].items()))
    print(f"{info['markets']} markets. Market time recorded per series: {per} (rule needs {RULE_MIN_HOURS}h in each)")
    label = info.get("dropped_label", "windows dropped for spanning a recording gap or the end of a market")
    print(f"{info['dropped']:,} {label}\n")

    print(f"{'series':10} {'hold':>5} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'move>cost':>10} {'needs':>7}")
    for s in sorted({r[0] for r in recs}):
        for h in HORIZONS:
            rows = [(r[4], r[5]) for r in recs if r[0] == s and r[1] == h]
            if rows:
                n, c, m, beat, need = _summ(rows)
                print(f"{s:10} {h:>4}s {n:>7} {c:>9.4f} {m:>11.4f} {beat:>9.1%} {_acc(need):>7}")
    print("\n'needs' = share of direction calls that must be right to break even.")
    print("move>cost assumes perfect foresight. Random calls lose the full cost.\n")

    print(f"--- {CUT_HORIZON}s hold, by price level (mid at entry) ---")
    print(f"{'series':10} {'price':>9} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'needs':>7}")
    for s in sorted({r[0] for r in recs}):
        for lo, hi in PRICE_BANDS:
            rows = [(r[4], r[5]) for r in recs if r[0] == s and r[1] == CUT_HORIZON and lo <= r[2] < hi]
            if len(rows) >= 30:
                n, c, m, _, need = _summ(rows)
                print(f"{s:10} {lo*100:>3.0f}-{min(hi,1)*100:<4.0f}c {n:>7} {c:>9.4f} {m:>11.4f} {_acc(need):>7}")

    print(f"\n--- {CUT_HORIZON}s hold, by time left in the market ---")
    print(f"{'series':10} {'time left':>17} {'n':>7} {'avg cost':>9} {'avg |move|':>11} {'needs':>7}")
    for s in sorted({r[0] for r in recs}):
        for lo, hi, label in TIME_BANDS:
            rows = [(r[4], r[5]) for r in recs if r[0] == s and r[1] == CUT_HORIZON
                    and r[3] is not None and lo <= r[3] < hi]
            if len(rows) >= 30:
                n, c, m, _, need = _summ(rows)
                print(f"{s:10} {label:>17} {n:>7} {c:>9.4f} {m:>11.4f} {_acc(need):>7}")
    print("\nA bucket with few markets behind it is noise. Judge on days of data, not rows.")

    v, why = verdict(recs, info["hours"])
    print(f"\nVERDICT (pre-registered rule, 60s hold, bar {RULE_BAR:.0%} in both halves): {v}")
    for line in why:
        print("  " + line)
    if v == "NOT_YET_FALSIFIED":
        print("  This is permission to write a hypothesis down, not evidence of an edge.")
    if v == "FALSIFIED":
        print("  No bucket clears the bar. Do not build a directional scalping strategy.")


if __name__ == "__main__":
    main()
