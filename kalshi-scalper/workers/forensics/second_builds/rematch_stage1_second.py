#!/usr/bin/env python3
"""REMATCH stage 1, an INDEPENDENT SECOND BUILD (Forensics desk, 2026-11-13), written from Desk B's registration text and Amendments 1 to 6
(claude/idea-desk-b, kalshi-scalper/workers/rematch/REMATCH_REGISTRATION.md and REMATCH_SERIES.json). Ordered by the Head of R&D under rule 16b.
Disclosure: this desk leak-tested Desk B's stage 1 scripts on Nov 12 and scanned them for float comparisons on Nov 13, so it is not a clean-room reader.

COUNTS AND COST ONLY. No bet is scored. The result of an EARLIER match is read only to name its loser. The result of a LATER match is never read:
the reader drops the result field of every market that is not used as an earlier match.
Development only: a market closing on or after 2026-10-23T00:00:00Z is refused, and any path in or resolving into a HELDOUT_ folder is refused.

usage: python3 -I rematch_stage1_second.py <lists run folder> <candles run folder> [...more candle run folders]

Places where the text leaves a choice (AMBIGUITIES, printed with the output):
 1. "Every market of A": the two team contracts and the Tie contract of the earlier event, all three.
 2. An event's close for the slice test and the start check: the LATEST close_time over its markets.
 3. "The NEXT meeting of that pair": events of the same two player codes ordered by scheduled start; A and B are neighbours in that order.
    A pair whose earlier match is not in the lists (it closed before the slice) cannot be formed and is not counted.
 4. A had a winner: exactly one team contract of A has result "yes". The Tie contract "yes" is a tie. Anything else is "no readable winner".
 5. A present candle with no usable bid and no usable ask (bid missing or 0, ask missing or 1) is counted as "empty book", apart from "one-sided".
 6. The missing-candle rule is applied to each of the three instants separately (reference, decision, entry).
 7. The tradeability count: eligible pairs whose loser's contract is two-sided with a spread of 4c or less at the reference ("before") instant.
 8. Projected development bets: entries on the slice x 15 / 8 (Amendment 5, point 3). Projected tradeable: the tradeability count x 15 / 8.
 9. Entries: pairs with the state true (fell 5c or more) whose entry instant passes the band and the spread line. Placebo entries are counted apart.
10. The entry instant is looked up only for pairs in the state or in the placebo pool (a pair that moved 2c or more without falling 5c has no entry to price).
"""
import sys, os, json, gzip, re, math, statistics, collections
from datetime import datetime
from zoneinfo import ZoneInfo

SERIES = "KXESOCCERGAME"
ET = ZoneInfo("America/New_York")
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
def iso(s): return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())
SLICE_FROM, SLICE_BEFORE = iso("2026-10-15T00:00:00Z"), iso("2026-10-23T00:00:00Z")
HELDOUT_FROM = iso("2026-10-23T00:00:00Z")
GAP_LO, GAP_HI = 20 * 60, 120 * 60
REF_BACK, DEC_BACK, ENT_BACK = 2 * 60, 6 * 60, 5 * 60      # reference: A's S minus 2 min; decision: B's S minus 6 min; entry: B's S minus 5 min
A_CLOSE_PLUS = 300
CARRY = 5 * 60
FALL, QUIET = 0.05, 0.02
BAND, SPREAD_MAX, SLIP = (0.20, 0.80), 0.04, 0.01
COST_KILL, FLOOR = 0.04, 300
DEV_DAYS, SLICE_DAYS = 15, 8
EPS = 1e-9
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on sports"
AMBIGUITIES = [l.strip() for l in __doc__.split("AMBIGUITIES, printed with the output):")[1].strip().split("\n")]


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def bodies(folder):
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") != 200 or not row.get("file"): continue
        yield row, json.load(gzip.open(os.path.join(folder, row["file"]), "rt"))


def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100.0


def clock(event_ticker):
    """scheduled start from the ticker key: yy MON dd HHMM, US Eastern. None when the key has no such clock."""
    key = event_ticker.split("-", 1)[1] if "-" in event_ticker else ""
    m = re.match(r"^(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})", key)
    if not m or m.group(2) not in MON: return None
    try: return int(datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=ET).timestamp())
    except ValueError: return None


def num(d, k="close_dollars"):
    if not isinstance(d, dict): return None
    v = d.get(k)
    try: return float(v)
    except (TypeError, ValueError): return None


def read_events(lists_folder):
    """events of the series from the lists. Results are kept in a SEPARATE table that only the earlier-match step may read."""
    raw = {}
    for row, body in bodies(lists_folder):
        if (row.get("params") or {}).get("series_ticker") != SERIES or row.get("path") != "/markets": continue
        for m in body.get("markets") or []:
            if isinstance(m, dict) and str(m.get("ticker", "")).startswith(SERIES + "-"): raw[m["ticker"]] = m
    by_event = collections.defaultdict(list)
    for t, m in raw.items(): by_event[m.get("event_ticker") or t.rsplit("-", 1)[0]].append(m)
    drops = collections.Counter(); events = {}; results = {}; refused = 0
    for ev, ms in by_event.items():
        teams = sorted({m["ticker"].rsplit("-", 1)[1] for m in ms if not m["ticker"].endswith("-TIE")})
        if len(teams) != 2: drops["not exactly two team codes"] += 1; continue
        S = clock(ev)
        if S is None: drops["no clock in the ticker"] += 1; continue
        closes = []
        for m in ms:
            try: closes.append(iso(m["close_time"]))
            except Exception: closes.append(None)
        if any(c is None for c in closes): drops["a market with no close time"] += 1; continue
        if max(closes) >= HELDOUT_FROM: refused += 1; continue                    # held-out closed by default: never used, counted
        events[ev] = {"event": ev, "S": S, "close": max(closes), "teams": teams, "tickers": {m["ticker"].rsplit("-", 1)[1]: m["ticker"] for m in ms}}
        results[ev] = {m["ticker"].rsplit("-", 1)[1]: (m.get("result") or "") for m in ms}
    return events, results, drops, refused, len(by_event)


def read_candles(folders, wanted):
    """{ticker: {end_ts: (bid, ask)}} for the wanted tickers only. bid or ask None when the candle carries none."""
    out = {}; asked = set()
    for f in folders:
        for row, body in bodies(f):
            for t in str((row.get("params") or {}).get("market_tickers", "")).split(","):
                if t: asked.add(t)
            for m in body.get("markets") or []:
                t = m.get("market_ticker")
                if t not in wanted: continue
                d = out.setdefault(t, {})
                for c in m.get("candlesticks") or []:
                    ts = c.get("end_period_ts")
                    if isinstance(ts, int): d[ts] = (num(c.get("yes_bid")), num(c.get("yes_ask")))
    return out, asked


def quote_at(cd, T):
    """the candle ending exactly at T, else the last present candle ending before T and no more than 5 minutes earlier. Never a later candle.
    returns (kind, bid, ask, exact) with kind in: none, empty, one-sided, two-sided."""
    for back in range(0, CARRY + 1, 60):
        q = cd.get(T - back)
        if q is None: continue
        b, a = q
        hb, ha = (b is not None and b > EPS), (a is not None and a < 1 - EPS)
        if hb and ha and b < a - EPS: return "two-sided", b, a, back == 0
        if not hb and not ha: return "empty", b, a, back == 0
        return "one-sided", b, a, back == 0
    return "none", None, None, False


def measure(lists_folder, candle_folders):
    events, results, drops, refused, listed = read_events(lists_folder)
    C = collections.Counter(); C["events listed"] = listed; C["events refused as held-out (close on or after 2026-10-23)"] = refused
    for k, v in drops.items(): C["dropped: " + k] = v
    C["events kept"] = len(events)
    in_slice = [e for e in events.values() if SLICE_FROM <= e["close"] < SLICE_BEFORE]
    C["events in the stage 1 slice"] = len(in_slice)
    start_ok = sum(1 for e in in_slice if 4 * 60 <= e["close"] - e["S"] <= 90 * 60)
    C["start check: closed 4 to 90 minutes after the ticker clock"] = start_ok
    by_pair = collections.defaultdict(list)
    for e in events.values(): by_pair[frozenset(e["teams"])].append(e)
    pairs = []
    for key, es in by_pair.items():
        es.sort(key=lambda e: (e["S"], e["event"]))
        for a, b in zip(es, es[1:]):
            C["next meetings of the same pair"] += 1
            if not (SLICE_FROM <= b["close"] < SLICE_BEFORE): C["later match outside the slice"] += 1; continue
            if not (GAP_LO <= b["S"] - a["S"] <= GAP_HI): C["starts not 20 to 120 minutes apart"] += 1; continue
            C["pairs that qualify by schedule"] += 1
            if a["close"] + A_CLOSE_PLUS > b["S"] - DEC_BACK: C["earlier match's close plus 300 s is after the decision minute"] += 1; continue
            ra = results[a["event"]]                                                  # the ONLY place a result is read: the earlier match
            winners = [t for t in a["teams"] if ra.get(t) == "yes"]
            if ra.get("TIE") == "yes" and not winners: C["earlier match was a tie"] += 1; continue
            if len(winners) != 1: C["earlier match has no readable winner"] += 1; continue
            loser = [t for t in a["teams"] if t != winners[0]][0]
            pairs.append((a, b, loser))
    C["eligible pairs (schedule, earlier match closed in time, it had a winner)"] = len(pairs)
    del results                                                                        # nothing below can read a result
    wanted = {b["tickers"][l] for _, b, l in pairs}
    cd, asked = read_candles(candle_folders, wanted)
    costs_all, costs_exact = [], []; nocandle = collections.Counter(); late = []
    for a, b, l in pairs:
        tk = b["tickers"][l]; c = cd.get(tk, {})
        Tref, Tdec, Tent = a["S"] - REF_BACK, b["S"] - DEC_BACK, b["S"] - ENT_BACK
        for T in (Tref, Tdec, Tent):                                                  # a tally over every eligible pair and all three instants, whatever happens to the pair later
            kk, _, _, xx = quote_at(c, T)
            if kk != "none": C["every eligible pair, three instants: candle at the exact minute" if xx else "every eligible pair, three instants: candle carried from an earlier minute"] += 1
        k0, b0, a0, x0 = quote_at(c, Tref)
        C["reference instant: " + k0] += 1
        if k0 == "none":                                                              # the Head's extra count: presence only, no price
            nocandle["ticker asked for in a candle request" if tk in asked else "ticker NOT in any candle request"] += 1
            if not c: nocandle["no candle anywhere in the pulled file"] += 1
            else:
                nocandle["some candle somewhere in the pulled file"] += 1
                if any(ts <= Tref for ts in c): nocandle["  of which a candle at or before the reference minute (more than 5 minutes before it)"] += 1
                else: nocandle["  of which the first candle is after the reference minute"] += 1
                if any(Tref < ts <= Tent for ts in c): nocandle["  of which a candle between the reference minute and the entry minute"] += 1
            continue
        if k0 != "two-sided": continue
        C["reference instant read from its own minute" if x0 else "reference instant carried from an earlier minute"] += 1
        if a0 - b0 <= SPREAD_MAX + EPS: C["TRADEABILITY: two-sided with a spread of 4c or less at the reference instant"] += 1
        k1, b1, a1, x1 = quote_at(c, Tdec)
        C["decision instant: " + k1] += 1
        if k1 != "two-sided": continue
        C["both instants two-sided"] += 1
        move = (b1 + a1) / 2 - (b0 + a0) / 2
        fell, quiet = move <= -FALL + EPS, abs(move) < QUIET - EPS
        if fell: C["STATE: fell 5c or more"] += 1
        elif quiet: C["placebo state: moved under 2c"] += 1
        else: C["neither (moved 2c or more but did not fall 5c)"] += 1
        if not (fell or quiet): continue
        k2, b2, a2, x2 = quote_at(c, Tent)
        tag = "state" if fell else "placebo"
        C["%s, entry instant: %s" % (tag, k2)] += 1
        if k2 != "two-sided": continue
        if not (BAND[0] - EPS <= a2 <= BAND[1] + EPS): C["%s, entry ask outside 20c to 80c" % tag] += 1; continue
        if a2 - b2 > SPREAD_MAX + EPS: C["%s, entry spread over 4c" % tag] += 1; continue
        C["ENTRIES" if fell else "placebo entries"] += 1
        if fell:
            price = round(a2 + SLIP, 6); cost = (a2 - (a2 + b2) / 2) + fee_up(price)
            costs_all.append(cost); late.append((b["close"] - b["S"]) / 60.0)      # diagnostic only, never a filter (Amendment 3, point 5): a close TIME of the later match, no result
            if x2: C["entries whose price came from the exact entry minute"] += 1
            if x0 and x1 and x2: costs_exact.append(cost); C["entries with all three instants from their own minute"] += 1
    n_ent, n_trd = C["ENTRIES"], C["TRADEABILITY: two-sided with a spread of 4c or less at the reference instant"]
    proj_bets, proj_trd = n_ent * DEV_DAYS / SLICE_DAYS, n_trd * DEV_DAYS / SLICE_DAYS
    med_all = statistics.median(costs_all) if costs_all else None; med_exact = statistics.median(costs_exact) if costs_exact else None
    worse = max([x for x in (med_all, med_exact) if x is not None], default=None)
    start_fail = start_ok * 5 < 4 * len(in_slice)                                    # under 80%, in whole numbers
    reasons = []
    if start_fail: reasons.append("start not derivable (under 80%)")
    if proj_trd < FLOOR - EPS: reasons.append("tradeability: projected %.1f under %d" % (proj_trd, FLOOR))
    if proj_bets < FLOOR - EPS: reasons.append("projected bets %.1f under %d" % (proj_bets, FLOOR))
    if worse is not None and worse > COST_KILL + EPS: reasons.append("cost: worse median one-way entry cost %.4f over %.2f" % (worse, COST_KILL))
    if not costs_all: reasons.append("no entry, so no cost line")
    return {"label": FRESH, "selected_on_development": "every line here can close the card and cannot support it", "counts": dict(C), "no_candle_at_reference_breakdown": dict(nocandle),
            "start_share": (start_ok / len(in_slice)) if in_slice else None,
            "median_one_way_entry_cost_all_entries": med_all, "median_one_way_entry_cost_exact_minute_entries": med_exact, "worse_of_the_two": worse,
            "projected_development_bets": proj_bets, "projected_tradeable_pairs": proj_trd,
            "diagnostic_never_a_filter_minutes_from_ticker_clock_to_market_close_for_matches_with_an_entry": sorted(round(x, 1) for x in late),
            "diagnostic_closed_under_9_minutes_after_the_clock": sum(1 for x in late if x < 9),
            "stage_1_line": ("CLOSED at stage 1, no try spent: " + "; ".join(reasons)) if reasons else "open: stage 2 may be asked for", "ambiguities": AMBIGUITIES}


if __name__ == "__main__":
    if len(sys.argv) < 3: raise SystemExit(__doc__)
    print(json.dumps(measure(sys.argv[1], sys.argv[2:]), indent=1))
