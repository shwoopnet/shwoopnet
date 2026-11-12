#!/usr/bin/env python3
"""REMATCH stage 1 reader: counts and the one-way cost line. ZERO tries.
Committed Nov 12, 2026, before any e-soccer list or candle was pulled.

It reads the result of an EARLIER match (A) only, to name the player who lost it: that is the state.
It never reads the result of a later match (B) for a pair, never joins a result to a bet, and prints no
win, loss or profit figure. It refuses any market closing on or after the held-out date.

Usage: python3 stage1_measure.py <folder of the lists run> <folder of the candles run> <pairs.json>
"""
import glob
import gzip
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (A_CLOSE_PLUS_S, ASK_BAND, BEFORE_S, COST_KILL_ONE_WAY, DECISION_S, DEV_DAYS, ENTRY_S, FALL, HELDOUT_FROM, LABEL, QUIET,  # noqa: E402
                    SLIP, SPREAD_MAX, STAGE1_BEFORE, STAGE1_FROM, fee, read_events, ts)


def price(side):
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if v > 1.0 else v
    return None


def walk(node, found, hint=None):
    if isinstance(node, dict):
        tk = node.get("market_ticker") or node.get("ticker") or hint
        c = node.get("candlesticks")
        if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0]:
            if tk:
                found.setdefault(tk, []).extend(c)
        for v in node.values():
            walk(v, found, tk)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, hint)


def two_sided(q):
    return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1


def loser_of(a):
    """The code of the player who lost match A, or None (a Tie, or no clear yes/no result). A's result only."""
    res = {c: (m.get("result") or "").lower() for c, m in a["markets"].items()}
    winners = [c for c in a["codes"] if res.get(c) == "yes"]
    if len(winners) != 1 or res.get("TIE") == "yes" or any(res.get(c) not in ("yes", "no") for c in a["codes"]):
        return None
    return [c for c in a["codes"] if c != winners[0]][0]


def main():
    lists_run, candles_run, pairs_path = sys.argv[1:4]
    events = {e["event"]: e for e in read_events(lists_run)}
    if any(e["close"] >= ts(HELDOUT_FROM) for e in events.values()):
        sys.exit("REFUSED: the lists hold a market closing on or after the held-out date")
    pairs = json.load(open(pairs_path))
    found = {}
    for f in sorted(glob.glob(os.path.join(candles_run, "[0-9]*.json.gz"))):
        walk(json.load(gzip.open(f, "rt")), found)
    quotes = {tk: {int(c["end_period_ts"]): (price(c.get("yes_bid")), price(c.get("yes_ask"))) for c in cs} for tk, cs in found.items()}

    n = dict(pairs=len(pairs), a_winner=0, a_closed_in_time=0, before_two_sided=0, tradeable_before=0, after_two_sided=0, state=0, quiet=0, state_entry=0, quiet_entry=0)
    costs, days, late = [], set(), []
    in_span = [e for e in events.values() if ts(STAGE1_FROM) <= e["close"] < ts(STAGE1_BEFORE)]
    start_ok = sum(1 for e in in_span if 4 * 60 <= e["close"] - e["S"] <= 90 * 60)
    for p in pairs:
        a, b = events.get(p["A"]), events.get(p["B"])
        if not a or not b:
            continue
        days.add(b["S"] // 86400)
        lose = loser_of(a)
        if lose is None:
            continue
        n["a_winner"] += 1
        if a["close"] + A_CLOSE_PLUS_S > b["S"] - DECISION_S:
            continue
        n["a_closed_in_time"] += 1
        q = quotes.get("%s-%s" % (b["event"], lose), {})
        q0, q1, q2 = q.get(a["S"] - BEFORE_S), q.get(b["S"] - DECISION_S), q.get(b["S"] - ENTRY_S)
        if not two_sided(q0):
            continue
        n["before_two_sided"] += 1
        if q0[1] - q0[0] <= SPREAD_MAX + 1e-9:
            n["tradeable_before"] += 1
        if not two_sided(q1):
            continue
        n["after_two_sided"] += 1
        move = (q1[0] + q1[1]) / 2 - (q0[0] + q0[1]) / 2
        kind = "state" if move <= -FALL + 1e-9 else ("quiet" if abs(move) < QUIET - 1e-9 else None)
        if kind is None:
            continue
        n[kind] += 1
        if two_sided(q2) and ASK_BAND[0] - 1e-9 <= q2[1] <= ASK_BAND[1] + 1e-9 and q2[1] - q2[0] <= SPREAD_MAX + 1e-9:
            n[kind + "_entry"] += 1
            if kind == "state":
                costs.append(q2[1] - (q2[0] + q2[1]) / 2 + fee(q2[1] + SLIP))
                late.append((b["close"] - b["S"]) / 60.0)   # diagnostic only, never a filter (Amendment 3, point 5)

    print("REMATCH stage 1: counts and cost only. No bet is scored. " + LABEL + ".")
    print("Every line below is 'selected on development': it can close the card, it cannot support it.")
    print(f"e-soccer matches in the slice {len(in_span)} | start check (market closed 4 to 90 minutes after the ticker clock) {start_ok} = {100.0 * start_ok / max(1, len(in_span)):.1f}% (under 80%: start not derivable)")
    for k, label in (("pairs", "pairs qualifying by schedule"), ("a_winner", "earlier match had a winner"), ("a_closed_in_time", "earlier match closed 300 s or more before the decision minute"),
                     ("before_two_sided", "loser's contract two-sided at the reference minute"), ("tradeable_before", "  of those, spread 4c or less (tradeability count)"),
                     ("after_two_sided", "two-sided at the decision minute"), ("state", "STATE: fell 5c or more"), ("state_entry", "  entries that pass the band and spread"),
                     ("quiet", "PLACEBO pool: moved under 2c"), ("quiet_entry", "  placebo entries that pass")):
        print(f"{label}: {n[k]}")
    nd = max(1, len(days))
    proj_bets, proj_trade = n["state_entry"] / nd * DEV_DAYS, n["tradeable_before"] / nd * DEV_DAYS
    print(f"days in the slice with a later match: {len(days)} | projected development bets over {DEV_DAYS} days: {proj_bets:.0f} (under 600 closes the card) | projected tradeable pairs: {proj_trade:.0f} (under 300 closes on tradeability)")
    if costs:
        med = statistics.median(costs)
        print(f"one-way entry cost at qualifying entries: median {100 * med:.1f}c over {len(costs)} (above {100 * COST_KILL_ONE_WAY:.0f}c closes on cost)")
    else:
        print("one-way entry cost: no qualifying entry")
    if late:
        late.sort()
        print(f"diagnostic only, never a filter: for matches with an entry, market close minus ticker clock, minutes: p10 {late[len(late) // 10]:.0f} median {late[len(late) // 2]:.0f} p90 {late[(9 * len(late)) // 10]:.0f} | "
              f"closed under 9 minutes after the clock (14 after the entry): {sum(1 for x in late if x < 9)} of {len(late)}")
    closed = (start_ok < 0.8 * len(in_span)) or proj_trade < 300 or proj_bets < 600 or (costs and statistics.median(costs) > COST_KILL_ONE_WAY + 1e-9) or not costs
    print("STAGE 1 LINE: " + ("CLOSED at stage 1, no try spent" if closed else "open: stage 2 may be asked for"))


if __name__ == "__main__":
    main()
