#!/usr/bin/env python3
"""REMATCH stage 1 INDEPENDENT second reader (Testing Desk, Nov 13, 2026), built from REMATCH_REGISTRATION.md (Amendments 1 to 6) and REMATCH_SERIES.json at claude/idea-desk-b 4da23d43/ae52bf48 ALONE; Desk B's common.py and stage1_measure.py were not read.
Stage 1 = counts and cost only: NO bet is scored, only the EARLIER match's result is read (to name the loser). Research only: reads files, sends nothing.
Inputs: lists (KXESOCCERGAME market lists), candles. Refuses HELDOUT_ paths (scorekit.guard/real path) and any market closing on or after 2026-10-23T00:00Z (counted).
Readings of the text where it is not exact are in AMBIGUITIES (the Head rules)."""
import json, math, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

NY = ZoneInfo("America/New_York")
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
SLICE_FROM, SLICE_TO = calendar.timegm((2026, 10, 15, 0, 0, 0)), calendar.timegm((2026, 10, 23, 0, 0, 0))
DEV_FROM = calendar.timegm((2026, 10, 8, 0, 0, 0))            # Amendment 5: the series began 2026-10-08 (the registered constant is 2026-09-12; nothing earlier exists)
TOL = 1e-9
SLICE_A_IN_SLICE = True          # variant under test: both matches of a pair close inside the stage 1 slice
FLOOR = 300
AMBIGUITIES = [
    "1. Slice membership: a PAIR is in the stage 1 slice when the LATER match B's market closes in [2026-10-15, 2026-10-23); the earlier match A may be earlier (Oct 8 on).",
    "2. 'Next meeting of the pair': pairs are grouped by the two player codes (either order); inside a pair matches are ordered by scheduled start S; B is the match that directly follows A in that order; the pair counts when S_B - S_A is 20 to 120 minutes.",
    "3. 'Qualifying pairs' = pairs by the schedule test whose A is fully readable (every market of A has a close_time, A has a winner, A's close + 300 s is at or before B's decision minute). Funnel counts are printed at every step.",
    "4. 'Entries' = pairs with the STATE true (fall of 5c or more) and the entry conditions met (loser's contract two-sided at the entry instant, ask 20c to 80c inclusive, spread 4c or less). Placebo pool = pairs whose fall is under 2c in absolute value, same entry conditions.",
    "5. Projections: projected development bets = entries in the slice x 15/8 (15 development days, 8 in the slice); projected tradeable pairs = pairs whose loser's contract is two-sided with spread 4c or less at the 'before' instant, x 15/8. Floors 300.",
    "6. One-way cost per entry = (entry ask minus entry mid) + fee rounded up at (ask + 1c); medians over all entries and over entries whose three instants were all read from their own minute; the worse median decides against 4c.",
    "7. Quote at an instant (Amendment 4): the candle ending exactly at the minute, else the last PRESENT candle ending before it and at most 5 minutes earlier; if none, 'no candle' and the pair is dropped; a candle present but one-sided is counted apart.",
    "8. Start check: the share of matches in the slice whose market closed 4 to 90 minutes after S, in whole numbers (count x 100 >= 80 x matches).",
]


def start_ts(event):
    key = event.split("-", 1)[1] if "-" in event else ""
    try: return int(datetime(2000 + int(key[0:2]), MONTHS[key[2:5]], int(key[5:7]), int(key[7:9]), int(key[9:11]), tzinfo=NY).timestamp())
    except (KeyError, ValueError, IndexError): return None


def fee_up(p): return math.ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100


def matches_from(raw, counts):
    """-> {event: dict(event, S, close (latest over markets, None if any missing), codes {code: ticker}, tie ticker, results)} for KXESOCCERGAME events with exactly two team codes plus -TIE."""
    by = {}
    for t, m in raw.items():
        if m["series"] == "KXESOCCERGAME": by.setdefault(m["event"], []).append(m)
    out = {}
    counts["events_listed"] = len(by)
    for e, ms in sorted(by.items()):
        teams = [m for m in ms if not m["ticker"].endswith("-TIE")]; ties = [m for m in ms if m["ticker"].endswith("-TIE")]
        if len(teams) != 2 or len(ties) != 1 or len({m["ticker"].rsplit("-", 1)[-1] for m in teams}) != 2: counts["not_exactly_two_team_codes"] += 1; continue
        S = start_ts(e)
        if S is None: counts["no_clock_in_ticker"] += 1; continue
        closes = [m["close"] for m in ms]
        close = None if any(c is None for c in closes) else max(closes)
        if close is None: counts["market_with_no_close_time"] += 1
        if close is not None and close >= SLICE_TO: counts["held_out_refused"] += 1; continue
        out[e] = {"event": e, "S": S, "close": close, "codes": {m["ticker"].rsplit("-", 1)[-1]: m["ticker"] for m in teams}, "tie": ties[0], "teams": teams}
    return out


def quote(idx, ticker, T):
    """-> (status, bid, ask, exact). status 'ok' | 'no_candle' | 'one_sided'."""
    d = idx.get(ticker, {})
    if T in d: c, exact = d[T], True
    else:
        prev = [x for x in d if T - 300 <= x < T]
        if not prev: return "no_candle", None, None, False
        c, exact = d[max(prev)], False
    b, a = c.get("bid"), c.get("ask")
    if b is None or a is None or not (0 < b < a < 1): return "one_sided", b, a, exact
    return "ok", b, a, exact


def stage1(list_folders, candle_folders):
    c = {"events_listed": 0, "not_exactly_two_team_codes": 0, "no_clock_in_ticker": 0, "market_with_no_close_time": 0, "held_out_refused": 0}
    raw = k.markets(list_folders); ms = matches_from(raw, c)
    idx = {t: {x["ts"]: x for x in v} for t, v in k.candles(candle_folders).items()}
    # start check on the slice
    in_slice = [m for m in ms.values() if m["close"] is not None and SLICE_FROM <= m["close"] < SLICE_TO]
    ok4_90 = sum(1 for m in in_slice if 4 * 60 - TOL <= m["close"] - m["S"] <= 90 * 60 + TOL)
    c["matches_in_the_slice"] = len(in_slice); c["start_check_closed_4_to_90_min_after_S"] = ok4_90
    c["start_check_share"] = None if not in_slice else round(ok4_90 / len(in_slice), 4); c["start_check_passes_80_percent"] = bool(in_slice) and ok4_90 * 100 >= 80 * len(in_slice)
    # pairs by schedule
    pairs = {}
    for m in ms.values(): pairs.setdefault(frozenset(m["codes"]), []).append(m)
    F = {k_: 0 for k_ in ("pairs_by_schedule_B_in_slice", "earlier_has_a_winner", "earlier_closed_300s_before_decision", "earlier_close_missing", "reference_no_candle", "reference_one_sided", "reference_two_sided", "reference_two_sided_spread_le_4c", "decision_no_candle", "decision_one_sided", "two_sided_at_decision",
                          "state_true_fall_5c_or_more", "entries", "placebo_pool_move_under_2c", "placebo_entries", "entry_no_candle", "one_sided_at_entry", "earlier_winner_missing_or_tie")}
    instants = {"exact": 0, "carried": 0}; costs_all, costs_exact = [], []; tradeable = 0
    for key, lst in pairs.items():
        if len(key) != 2: continue
        lst.sort(key=lambda m: (m["S"], m["event"]))
        for A, B in zip(lst, lst[1:]):
            if not (B["close"] is not None and SLICE_FROM <= B["close"] < SLICE_TO): continue
            if SLICE_A_IN_SLICE and not (A["close"] is not None and SLICE_FROM <= A["close"] < SLICE_TO): F["pairs_dropped_A_outside_slice"] = F.get("pairs_dropped_A_outside_slice", 0) + 1; continue
            if not (20 * 60 - TOL <= B["S"] - A["S"] <= 120 * 60 + TOL): continue
            F["pairs_by_schedule_B_in_slice"] += 1
            dec = B["S"] - 6 * 60
            if A["close"] is None: F["earlier_close_missing"] += 1; continue
            res = {m["ticker"].rsplit("-", 1)[-1]: m["result"] for m in A["teams"]}; tie_res = A["tie"]["result"]
            yes = [cd for cd, r in res.items() if r == "yes"]
            if len(yes) != 1 or tie_res == "yes": F["earlier_winner_missing_or_tie"] += 1; continue
            F["earlier_has_a_winner"] += 1
            loser = [cd for cd in res if cd != yes[0]][0]
            if A["close"] + 300 > dec: continue
            F["earlier_closed_300s_before_decision"] += 1
            lt = B["codes"].get(loser)
            if lt is None: continue
            q_ref = quote(idx, lt, A["S"] - 2 * 60); q_dec = quote(idx, lt, dec); q_ent = quote(idx, lt, B["S"] - 5 * 60)
            if q_ref[0] == "no_candle":
                F["reference_no_candle"] += 1
                if idx.get(lt): F["of_which_reference_no_candle_but_a_candle_anywhere_in_the_pulled_window"] = F.get("of_which_reference_no_candle_but_a_candle_anywhere_in_the_pulled_window", 0) + 1
                continue
            if q_ref[0] == "one_sided": F["reference_one_sided"] += 1; continue
            F["reference_two_sided"] += 1
            if q_ref[2] - q_ref[1] <= 0.04 + TOL: F["reference_two_sided_spread_le_4c"] += 1; tradeable += 1
            if q_dec[0] == "no_candle": F["decision_no_candle"] += 1; continue
            if q_dec[0] == "one_sided": F["decision_one_sided"] += 1; continue
            F["two_sided_at_decision"] += 1
            fall = (q_ref[1] + q_ref[2]) / 2 - (q_dec[1] + q_dec[2]) / 2
            state = fall >= 0.05 - TOL; placebo = abs(fall) < 0.02 - TOL
            if state: F["state_true_fall_5c_or_more"] += 1
            if placebo: F["placebo_pool_move_under_2c"] += 1
            if not (state or placebo): continue
            if q_ent[0] == "no_candle": F["entry_no_candle"] += 1; continue
            if q_ent[0] == "one_sided": F["one_sided_at_entry"] += 1; continue
            _, b, a, ex = q_ent
            if not (0.20 - TOL <= a <= 0.80 + TOL and a - b <= 0.04 + TOL): continue
            if placebo and not state: F["placebo_entries"] += 1; continue
            F["entries"] += 1
            for q in (q_ref, q_dec, q_ent): instants["exact" if q[3] else "carried"] += 1
            cost = (a - (a + b) / 2) + fee_up(round(a + 0.01, 4)); costs_all.append(cost)
            if q_ref[3] and q_dec[3] and q_ent[3]: costs_exact.append(cost)
    med = lambda xs: None if not xs else sorted(xs)[len(xs) // 2] if len(xs) % 2 else (sorted(xs)[len(xs) // 2 - 1] + sorted(xs)[len(xs) // 2]) / 2
    ma, me = med(costs_all), med(costs_exact); worse = None if ma is None and me is None else max(x for x in (ma, me) if x is not None)
    proj_bets = F["entries"] * 15 / 8; proj_trade = tradeable * 15 / 8
    return {"counts_first": c, "funnel": F, "instants_read": instants,
            "projected_development_bets_15_days": round(proj_bets, 1), "bets_floor_300_passes": proj_bets >= FLOOR - TOL,
            "projected_tradeable_pairs_15_days": round(proj_trade, 1), "tradeable_floor_300_passes": proj_trade >= FLOOR - TOL,
            "one_way_cost_median_all_quotes": None if ma is None else round(ma, 4), "one_way_cost_median_exact_minute_quotes": None if me is None else round(me, 4), "cost_n_all": len(costs_all), "cost_n_exact": len(costs_exact),
            "cost_line_worse_decides": None if worse is None else round(worse, 4), "cost_over_4c": None if worse is None else worse > 0.04 + TOL,
            "label": "selected on development: these lines can close the card, they cannot support a result; candle freshness measured on the Bitcoin 15 minute series only; no bet scored; the earlier match's result was read only to name the loser"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--candles" not in a: print(__doc__); print("\n".join(AMBIGUITIES))
    else: i = a.index("--candles"); print(json.dumps(stage1(a[:i], a[i + 1:]), indent=1))
