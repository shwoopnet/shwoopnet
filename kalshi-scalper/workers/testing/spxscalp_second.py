#!/usr/bin/env python3
"""SPXSCALP scorer, BUILD 2 (Testing Desk, Nov 13, 2026). Research only: reads files it is given, sends nothing, places nothing, writes NO file.
Built FROM THE CARD ALONE: Desk B's SPXSCALP_CARD_DRAFT_NOV13.md at 67bb024d (sha256 a30f8133) with Amendment 1; blind to Desk B's build 1, expected figures and fixture. Hand case: SPXSCALP_SECOND_HAND_CASE.md (committed first).
Test: test_spxscalp_second.py (INVENTED rows only). The ES csv is Databento-derived and licensed: nothing ES-derived is written anywhere; the path is an argument; results go by message only. NOT RUN on real data (conditions: Auditor B CLEAN on both scorers, SPXOI1_CANDLES's structure check, the Head's go).
Rule (card + Amendment 1): windows = KXINX15M markets closing before 2026-12-01T00:00Z (later ones are not touched); O = close - 900 s; looks = the candles ending at O + 60 m, m = 1..5; at a look |ES(t) - ES(O)| >= 0.0005 x ES(O) (1e-9), up = YES, down = NO;
candidate ask = YES ask close or 1 - YES bid close, band 0.20 to 0.25 (variant 0.20 to 0.30) inclusive on the ask seen; the first look where both hold is the one entry. Entry fill = ask + s (s = 1c and 2c). Exits: headline (2x target, else time exit at close - 300 s), variant (half at 2x, rest at bid >= 0.80, a 2-contract position), hold to settlement.
Per-order fees rounded up (scorekit.fee_rounded). A rule counts only at 1c PF >= 1.3 with both halves >= 1.0 AND 2c PF >= 1.0. Every figure is an upper bound, not fill-checked.
"""
import calendar, csv, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

TOL = 1e-9
SERIES = "KXINX15M"
DEV_END = calendar.timegm((2026, 12, 1, 0, 0, 0))
WINDOW_S, LOOKS, TIME_EXIT_BEFORE_CLOSE_S = 900, range(1, 6), 300
THRESHOLD = 0.0005
BAND_LO, BANDS, SLIPS = 0.20, (0.25, 0.30), (0.01, 0.02)
TARGET_MULT, REST_PRICE = 2.0, 0.80
MIN_ENTRIES, PF_BAR = 100, 1.3
EXITS = ("headline", "variant", "hold")
UPPER_BOUND = "upper bound, not fill-checked"
AMBIGUITIES = [
    "The variant exit (half at 2x, the rest at 80c) is modelled as a 2-contract position: one entry order of 2 contracts (fee on 2), two exit orders of 1 contract; the card says size 1 for the read. PF is scale-free.",
    "A half with no hit goes at the time exit as its own order; if a needed time-exit candle is missing the entry is dropped.",
    "An exit price at or below 0 (bid - s) is clamped to 0 for the fee only; the net uses the unclamped price.",
    "The hold arm's primary slip is 1c (entry slip only); every figure is also printed at 2c.",
    "A look whose candle lacks a bid or an ask has no price: no entry at that look. A look with a missing ES bar, or an instrument change from the start bar, is skipped (counted).",
    "Rule label order: fewer than 100 entries -> FALSIFIED; a half under 1.0 at 1c or PF under 1.0 at 2c -> FALSIFIED; counts -> 'counts the bar'; else 'no evidence'. An empty half is reported 'undefined' and does not by itself falsify.",
    "'Window-close order' for the halves = ascending close time, ties by ticker.",
]


def load_es(path):
    """{end_ts: (instrument_id, close)} keyed by the minute END (ts_event + 60 s); a duplicate ts_event stops the run naming the minute."""
    out, seen = {}, set()
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            ts = k.iso(r["ts_event"])
            if ts is None:
                continue
            if ts in seen:
                raise SystemExit("STOP: duplicate ES ts_event %s (two rows for one minute)" % r["ts_event"])
            seen.add(ts)
            try:
                out[ts + 60] = (int(r["instrument_id"]), float(r["close"]))
            except (KeyError, TypeError, ValueError):
                continue
    return out


def fee(p, contracts=1):
    return k.fee_rounded(min(max(p, 0.0), 1.0), contracts)


def find_entries(close, es, candles, counts):
    """-> {band_hi: (m, side, ask, t)} for the bands that found an entry. Looks m = 1..5; the move direction is re-evaluated at each look."""
    O = close - WINDOW_S
    start = es.get(O)
    if start is None:
        return None
    by = {c["ts"]: c for c in candles}
    found = {}
    for m in LOOKS:
        t = O + 60 * m
        cur = es.get(t)
        if cur is None:
            counts["look_no_es_bar"] += 1; continue
        if cur[0] != start[0]:
            counts["look_es_roll"] += 1; continue
        move = cur[1] - start[1]
        if not abs(move) >= THRESHOLD * start[1] - TOL:
            continue
        side = "yes" if move > 0 else "no"
        c = by.get(t)
        if c is None or c.get("bid") is None or c.get("ask") is None:
            counts["look_no_price"] += 1; continue
        ask = c["ask"] if side == "yes" else 1.0 - c["bid"]
        for hi in BANDS:
            if hi not in found and BAND_LO - TOL <= ask <= hi + TOL:
                found[hi] = (m, side, ask, t)
    return found


def after_entry(candles, t_entry, close):
    """Candles after the entry candle through the minute ending close - 300 s, in time order, as (t, bid)."""
    last = close - TIME_EXIT_BEFORE_CLOSE_S
    return [(c["ts"], c.get("bid")) for c in sorted(candles, key=lambda c: c["ts"]) if t_entry < c["ts"] <= last]


def time_exit_bid(candles, close):
    c = {x["ts"]: x for x in candles}.get(close - TIME_EXIT_BEFORE_CLOSE_S)
    return None if c is None else c.get("bid")


def headline(fill, s, path, tbid):
    """-> (net, exit_price) or None (dropped). Target: first bid >= 2 x fill; else the time exit."""
    target = TARGET_MULT * fill
    for _, bid in path:
        if bid is not None and bid >= target - TOL:
            ex = bid - s
            return ex - fill - fee(fill) - fee(ex)
    if tbid is None:
        return None
    ex = tbid - s
    return ex - fill - fee(fill) - fee(ex)


def variant(fill, s, path, tbid):
    """2-contract position: half at 2x, the rest at the first bid >= 0.80, a half with no hit at the time exit. -> net or None."""
    target = TARGET_MULT * fill
    a = next((bid for _, bid in path if bid is not None and bid >= target - TOL), None)
    b = next((bid for _, bid in path if bid is not None and bid >= REST_PRICE - TOL), None)
    if (a is None or b is None) and tbid is None:
        return None
    ea = (a if a is not None else tbid) - s
    eb = (b if b is not None else tbid) - s
    return (ea - fill) + (eb - fill) - fee(fill, 2) - fee(ea) - fee(eb)


def hold(fill, side, result):
    if result == "void":
        return -fee(fill)
    return (1.0 if result == side else 0.0) - fill - fee(fill)


def pf_of(nets):
    return k.pf(nets) if nets else None


def half_split(rows):
    h = len(rows) // 2
    return rows[:h], rows[h:]


def arm_report(rows_by_slip):
    """rows_by_slip: {s: [(close_key, net)]} sorted by close. -> the arm's figures at each slip and the verdict."""
    out = {}
    for s, rows in rows_by_slip.items():
        nets = [n for _, n in rows]
        h1, h2 = half_split(nets)
        out["%dc" % round(s * 100)] = {"n": len(nets), "pf": pf_of(nets), "net": sum(nets), "half1_pf": pf_of(h1), "half2_pf": pf_of(h2), "n_half1": len(h1), "n_half2": len(h2)}
    one, two = out["1c"], out["2c"]
    def lt1(p): return p is not None and p < 1.0 - TOL
    counts = (one["pf"] is not None and one["pf"] >= PF_BAR - TOL and one["half1_pf"] is not None and one["half1_pf"] >= 1.0 - TOL and one["half2_pf"] is not None and one["half2_pf"] >= 1.0 - TOL
              and two["pf"] is not None and two["pf"] >= 1.0 - TOL)
    if one["n"] < MIN_ENTRIES:
        label = "FALSIFIED (fewer than %d entries, n = %d)" % (MIN_ENTRIES, one["n"])
    elif lt1(one["half1_pf"]) or lt1(one["half2_pf"]) or lt1(two["pf"]):
        label = "FALSIFIED (a half PF under 1.0 at 1c, or 2c PF under 1.0)"
    elif counts:
        label = "counts the bar (PF 1.3, both halves 1.0 at 1c, 2c PF 1.0)"
    else:
        label = "no evidence"
    out["counts_the_bar"] = counts; out["label"] = label + " (" + UPPER_BOUND + ")"
    return out


def run_windows(markets, cs, es):
    c = {"windows_listed": 0, "not_touched_on_or_after_2026-12-01": 0, "no_es_start_bar": 0, "look_no_es_bar": 0, "look_es_roll": 0, "look_no_price": 0}
    spreads, two_sided, looks_total = [], 0, 0
    arms = {(hi, ex, s): [] for hi in BANDS for ex in EXITS for s in SLIPS}
    drops = {(hi, ex): 0 for hi in BANDS for ex in EXITS}
    entered = {hi: 0 for hi in BANDS}
    no_entry = {hi: 0 for hi in BANDS}
    voids = {hi: 0 for hi in BANDS}
    for tk in sorted(markets, key=lambda t: (markets[t]["close"] if markets[t]["close"] is not None else 0, t)):
        m = markets[tk]
        if m["series"] != SERIES:
            continue
        c["windows_listed"] += 1
        close = m["close"]
        if close is None or close >= DEV_END:
            c["not_touched_on_or_after_2026-12-01"] += 1; continue
        candles = cs.get(tk, [])
        found = find_entries(close, es, candles, c)
        if found is None:
            c["no_es_start_bar"] += 1; continue
        O = close - WINDOW_S
        for mm in LOOKS:
            cd = {x["ts"]: x for x in candles}.get(O + 60 * mm)
            if cd is not None:
                looks_total += 1
                if cd.get("bid") is not None and cd.get("ask") is not None:
                    two_sided += 1; spreads.append(round((cd["ask"] - cd["bid"]) * 100.0, 6))
        for hi in BANDS:
            if hi not in found:
                no_entry[hi] += 1; continue
            entered[hi] += 1
            mm, side, ask, t = found[hi]
            res = m["result"]
            if res is None or str(res).strip() == "" or res not in ("yes", "no", "void"):
                raise SystemExit("STOP: result %r on entered window %s is not yes, no or void" % (res, tk))
            voids[hi] += (res == "void")
            path, tbid = after_entry(candles, t, close), time_exit_bid(candles, close)
            for s in SLIPS:
                fill = ask + s
                key = (close, tk)
                nh = headline(fill, s, path, tbid)
                if nh is None:
                    if s == SLIPS[0]: drops[(hi, "headline")] += 1
                else:
                    arms[(hi, "headline", s)].append((key, nh))
                nv = variant(fill, s, path, tbid)
                if nv is None:
                    if s == SLIPS[0]: drops[(hi, "variant")] += 1
                else:
                    arms[(hi, "variant", s)].append((key, nv))
                arms[(hi, "hold", s)].append((key, hold(fill, side, res)))
    rep = {}
    for hi in BANDS:
        for ex in EXITS:
            rows = {s: sorted(arms[(hi, ex, s)]) for s in SLIPS}
            r = arm_report(rows)
            r["entries_found"] = entered[hi]; r["dropped_no_time_exit_candle"] = drops[(hi, ex)]; r["windows_without_entry"] = no_entry[hi]
            if ex == "hold": r["voids"] = voids[hi]
            rep["band_%02d_%s" % (round(hi * 100), ex)] = r
    spreads.sort()
    nr = lambda q: (spreads[max(0, int(math.ceil(q * len(spreads))) - 1)] if spreads else None)
    c1 = {"look_candles": looks_total, "two_sided": two_sided, "two_sided_share": (two_sided / looks_total if looks_total else None), "spread_cents_median": nr(0.5), "spread_cents_p90": nr(0.9)}
    return {"C1_candles_two_sided_and_spread": c1, "counts": c, "arms": rep, "headline_arm": "band_25_headline at 1c", "upper_bound_note": UPPER_BOUND, "ambiguities": AMBIGUITIES}


def run(lists, candle_runs, es_path):
    for f in list(lists) + list(candle_runs):
        k.guard(f)
    return run_windows(k.markets(lists), k.candles(candle_runs), load_es(es_path))


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--candles" in a and "--es" in a:
        import json
        i, j = a.index("--candles"), a.index("--es")
        print(json.dumps(run(a[:i], a[i + 1:j], a[j + 1]), indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
