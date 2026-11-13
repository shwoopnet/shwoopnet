#!/usr/bin/env python3
"""SPXSCALP scorer, BUILD 2 (Testing Desk, Nov 13, 2026). Research only: reads files it is given, sends nothing, places nothing, writes NO file.
Built FROM THE CARD ALONE: Desk B's SPXSCALP_CARD_DRAFT_NOV13.md, now at 40dfadd4 (Amendments 1 to 4); first built from 67bb024d (a30f8133) with Amendment 1; blind to Desk B's build 1, expected figures and fixture. Hand case: SPXSCALP_SECOND_HAND_CASE.md (committed first).
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
DEV_END = calendar.timegm((2026, 12, 1, 0, 0, 0))          # nothing at or after this is ever touched
CLOSE_FROM = calendar.timegm((2026, 11, 5, 0, 0, 0))          # Amendment 4 item 13: windows closing in [CLOSE_FROM, CLOSE_TO)
CLOSE_TO = calendar.timegm((2026, 11, 13, 0, 0, 0))
WINDOW_S, LOOKS, TIME_EXIT_BEFORE_CLOSE_S = 900, range(1, 6), 300
THRESHOLD = 0.0005
BAND_LO, BANDS, SLIPS = 0.20, (0.25, 0.30), (0.01, 0.02)
TARGET_MULT, REST_PRICE = 2.0, 0.80
MIN_ENTRIES, PF_BAR = 100, 1.3
EXITS = ("headline", "variant", "hold")
LABEL = {"headline": "HEADLINE", "variant": "HALF2X", "hold": "HOLD"}
UPPER_BOUND = "upper bound, not fill-checked"
AMBIGUITIES = [
    "The variant exit (half at 2x, the rest at 80c) is modelled as a 2-contract position: one entry order of 2 contracts (fee on 2), two exit orders of 1 contract; the card says size 1 for the read. PF is scale-free.",
    "A half with no hit goes at the time exit as its own order (or settles, Amendment 3).",
    "An exit price at or below 0 (bid - s) is clamped to 0 for the fee only; the net uses the unclamped price.",
    "The hold arm's primary slip is 1c (entry slip only); every figure is also printed at 2c.",
    "A look whose candle lacks a bid or an ask has no price: no entry at that look. A look with a missing ES bar, or an instrument change from the start bar, is skipped (counted).",
    "Rule 18 and Amendment 3 (ee92cf2f): every candle price used must be two-sided (0 < bid < ask < 1, 1e-9); at entry a candle that is not is no price (look_not_two_sided). The time exit is the first two-sided candle ending in [close - 300 s, close] (a missing candle counts as not two-sided); if none, each open half settles (payout, no exit fee, void refunds the price, entry fee kept). Nothing is dropped for the exit arms. A target or 80c hit needs a two-sided candle.",
    "ES loader: rows read, kept and skipped (timestamp, value, instrument) counted; the file's single instrument is the most frequent id (a tie stops); STOP if none kept or more than 5% skipped (MAX_SKIP_SHARE, my choice, the card does not state it).",
    "Rule label order: fewer than 100 entries -> FALSIFIED; a half under 1.0 at 1c or PF under 1.0 at 2c -> FALSIFIED; counts -> 'counts the bar'; else 'no evidence'. An empty half is reported 'undefined' and does not by itself falsify.",
    "'Window-close order' for the halves = ascending close time, ties by ticker.",
]


MAX_SKIP_SHARE = 0.05          # the ES loader STOPS if more than this share of rows is skipped, or if no row is kept


def load_es_counted(path):
    """-> ({end_ts: (instrument_id, close)} keyed by the minute END (ts_event + 60 s), counts). A duplicate ts_event stops the run naming the minute.
    counts: rows_read, rows_kept, skipped_ts (ts_event missing or not an ISO string), skipped_value (instrument_id or close does not parse)."""
    out, seen = {}, set()
    st = {"rows_read": 0, "rows_kept": 0, "skipped_ts": 0, "skipped_value": 0, "skipped_instrument": 0}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            st["rows_read"] += 1
            ts = k.iso(r.get("ts_event") or "")
            if ts is None:
                st["skipped_ts"] += 1; continue
            if ts in seen:
                raise SystemExit("STOP: duplicate ES ts_event %s (two rows for one minute)" % r["ts_event"])
            seen.add(ts)
            try:
                out[ts + 60] = (int(r["instrument_id"]), float(r["close"]))
            except (KeyError, TypeError, ValueError):
                st["skipped_value"] += 1; continue
            st["rows_kept"] += 1
    if out:
        cnt = {}
        for iid, _ in out.values():
            cnt[iid] = cnt.get(iid, 0) + 1
        top = max(cnt.values()); lead = sorted(i for i, n in cnt.items() if n == top)
        if len(lead) > 1:
            raise SystemExit("STOP: two instrument_ids tie for the most rows in the ES file: %s" % lead)
        for t in [t for t, (iid, _) in out.items() if iid != lead[0]]:
            del out[t]; st["skipped_instrument"] += 1; st["rows_kept"] -= 1
    return out, st


def check_es_rows(st):
    """STOP if no ES row was kept or the skipped share is above MAX_SKIP_SHARE; the message carries the counts."""
    skipped = st["skipped_ts"] + st["skipped_value"] + st["skipped_instrument"]
    desc = "rows_read %d, rows_kept %d, skipped_ts %d, skipped_value %d, skipped_instrument %d" % (st["rows_read"], st["rows_kept"], st["skipped_ts"], st["skipped_value"], st["skipped_instrument"])
    if st["rows_kept"] == 0:
        raise SystemExit("STOP: no ES row kept (%s): the file is not in the expected format" % desc)
    if skipped > MAX_SKIP_SHARE * st["rows_read"]:
        raise SystemExit("STOP: more than %.0f%% of ES rows skipped (%s)" % (MAX_SKIP_SHARE * 100, desc))


def load_es(path):
    return load_es_counted(path)[0]


def two_sided(c):
    """Standing rule 18: 0 < bid < ask < 1 with 1e-9 slack. An empty side (0.00 / 1.00), a locked or a crossed book is no price."""
    b, a = c.get("bid"), c.get("ask")
    return b is not None and a is not None and b > TOL and a < 1.0 - TOL and a - b > TOL


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
        if not two_sided(c):
            counts["look_not_two_sided"] += 1; continue
        ask = c["ask"] if side == "yes" else 1.0 - c["bid"]
        for hi in BANDS:
            if hi not in found and BAND_LO - TOL <= ask <= hi + TOL:
                found[hi] = (m, side, ask, t)
    return found


def after_entry(candles, t_entry, close):
    """Candles after the entry candle through the minute ending close - 300 s, in time order, as (t, bid)."""
    last = close - TIME_EXIT_BEFORE_CLOSE_S
    return [(c["ts"], c.get("bid")) for c in sorted(candles, key=lambda c: c["ts"]) if t_entry < c["ts"] <= last and two_sided(c)]


def time_exit(candles, close):
    """Amendment 3: the first TWO-SIDED candle ending in [close - 300 s, close]; its bid is the exit price. A missing or not-two-sided minute moves to the next two-sided one.
    -> ("bid", bid, moved) or ("settle", None, True) when none is left through the close (the position is held to the close and settled)."""
    for c in sorted(candles, key=lambda c: c["ts"]):
        if close - TIME_EXIT_BEFORE_CLOSE_S <= c["ts"] <= close and two_sided(c):
            return ("bid", c["bid"], c["ts"] != close - TIME_EXIT_BEFORE_CLOSE_S)
    return ("settle", None, True)


def first_hit(path, level):
    return next((bid for _, bid in path if bid is not None and bid >= level - TOL), None)


def close_leg(fill, s, texit, side, res):
    """One contract's result at the time exit (a sale at bid - s, fee on the exit) or at settlement (payout 1 or 0, price refunded on a void, no exit fee); the entry fee is NOT in it."""
    if texit[0] == "bid":
        ex = texit[1] - s
        return ex - fill - fee(ex)
    payout = fill if res == "void" else (1.0 if res == side else 0.0)
    return payout - fill


def headline(fill, s, path, texit, side, res):
    """Sell at the first bid >= 2 x fill, else at the time exit (or settle). Never dropped."""
    hit = first_hit(path, TARGET_MULT * fill)
    if hit is not None:
        ex = hit - s
        return ex - fill - fee(fill) - fee(ex)
    return close_leg(fill, s, texit, side, res) - fee(fill)


def variant(fill, s, path, texit, side, res):
    """2-contract position: half at the first bid >= 2 x fill, the rest at the first bid >= 0.80, a half with no hit at the time exit (or settled). Never dropped."""
    total = -fee(fill, 2)
    for level in (TARGET_MULT * fill, REST_PRICE):
        hit = first_hit(path, level)
        if hit is not None:
            ex = hit - s
            total += ex - fill - fee(ex)
        else:
            total += close_leg(fill, s, texit, side, res)
    return total


def uses_time_exit(path, fill, kind):
    """True if this arm's closing leg (a half, for the variant) goes at the time exit."""
    if kind == "headline":
        return first_hit(path, TARGET_MULT * fill) is None
    return first_hit(path, TARGET_MULT * fill) is None or first_hit(path, REST_PRICE) is None


def settles(path, fill, texit, kind):
    """True if this arm's closing leg ended at settlement instead of a sale (entry counted in the 'settled at close' print)."""
    return texit[0] == "settle" and uses_time_exit(path, fill, kind)


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
    counts = (one["n"] >= MIN_ENTRIES and one["pf"] is not None and one["pf"] >= PF_BAR - TOL and one["half1_pf"] is not None and one["half1_pf"] >= 1.0 - TOL and one["half2_pf"] is not None and one["half2_pf"] >= 1.0 - TOL
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


SETTLED_NOTE = "Amendment 3: an exit minute with no two-sided candle moves to the next two-sided minute; if none through the close the position is held to the close and settled. Those entries carry the full win or loss at settlement, not a sale at a quote."


def line_of(key, r):
    f = lambda x: "n/a" if x is None else ("inf" if x == float("inf") else "%.4f" % x)
    one, two = r["1c"], r["2c"]
    return "%s | 1c n=%d PF=%s net=%.2f h1=%s h2=%s | 2c n=%d PF=%s net=%.2f | %s" % (key, one["n"], f(one["pf"]), one["net"], f(one["half1_pf"]), f(one["half2_pf"]), two["n"], f(two["pf"]), two["net"], r["label"])


def run_windows(markets, cs, es, es_stats=None):
    c = {"windows_listed": 0, "not_touched_on_or_after_2026-12-01": 0, "outside_2026-11-05_to_2026-11-13_not_touched": 0, "no_es_start_bar": 0, "look_no_es_bar": 0, "look_es_roll": 0, "look_no_price": 0, "look_not_two_sided": 0}
    spreads, n_two_sided, looks_total = [], 0, 0
    arms = {(hi, ex, s): [] for hi in BANDS for ex in EXITS for s in SLIPS}
    settled = {(hi, ex): 0 for hi in BANDS for ex in EXITS}
    settled_fill = {(hi, ex): 0.0 for hi in BANDS for ex in EXITS}
    moved = {(hi, ex): 0 for hi in BANDS for ex in EXITS}
    entered = {hi: 0 for hi in BANDS}
    no_entry = {hi: 0 for hi in BANDS}
    voids = {hi: 0 for hi in BANDS}
    for tk in sorted(markets, key=lambda t: (markets[t]["close"] if markets[t]["close"] is not None else 0, t)):
        m = markets[tk]
        if m["series"] != SERIES:
            continue
        c["windows_listed"] += 1
        close = m["close"]
        if close is not None and close >= DEV_END:
            c["not_touched_on_or_after_2026-12-01"] += 1; continue
        if close is None or not (CLOSE_FROM <= close < CLOSE_TO):
            c["outside_2026-11-05_to_2026-11-13_not_touched"] += 1; continue
        candles = cs.get(tk, [])
        found = find_entries(close, es, candles, c)
        if found is None:
            c["no_es_start_bar"] += 1; continue
        O = close - WINDOW_S
        for mm in LOOKS:
            cd = {x["ts"]: x for x in candles}.get(O + 60 * mm)
            if cd is not None:
                looks_total += 1
                if two_sided(cd):
                    n_two_sided += 1; spreads.append(round((cd["ask"] - cd["bid"]) * 100.0, 6))
        for hi in BANDS:
            if hi not in found:
                no_entry[hi] += 1; continue
            entered[hi] += 1
            mm, side, ask, t = found[hi]
            res = m["result"]
            if res is None or str(res).strip() == "" or res not in ("yes", "no", "void"):
                raise SystemExit("STOP: result %r on entered window %s is not yes, no or void" % (res, tk))
            voids[hi] += (res == "void")
            path, texit = after_entry(candles, t, close), time_exit(candles, close)
            for s in SLIPS:
                fill = ask + s
                key = (close, tk)
                arms[(hi, "headline", s)].append((key, headline(fill, s, path, texit, side, res)))
                arms[(hi, "variant", s)].append((key, variant(fill, s, path, texit, side, res)))
                arms[(hi, "hold", s)].append((key, hold(fill, side, res)))
                if s == SLIPS[0]:
                    for ex in ("headline", "variant"):
                        if settles(path, fill, texit, ex):
                            settled[(hi, ex)] += 1; settled_fill[(hi, ex)] += fill
                        elif texit[0] == "bid" and texit[2] and uses_time_exit(path, fill, ex):
                            moved[(hi, ex)] += 1
    rep = {}
    for hi in BANDS:
        for ex in EXITS:
            rows = {s: sorted(arms[(hi, ex, s)]) for s in SLIPS}
            r = arm_report(rows)
            r["entries_found"] = entered[hi]; r["windows_without_entry"] = no_entry[hi]
            if ex != "hold":
                r["settled_at_close_count"] = settled[(hi, ex)]; r["settled_at_close_share"] = (settled[(hi, ex)] / entered[hi]) if entered[hi] else None
                r["settled_at_close_entry_fill_sum_1c"] = settled_fill[(hi, ex)]; r["time_exit_moved_count"] = moved[(hi, ex)]; r["settled_at_close_note"] = SETTLED_NOTE
            if ex == "hold": r["voids"] = voids[hi]
            rep["B%02d %s" % (round(hi * 100), LABEL[ex])] = r
    spreads.sort()
    nr = lambda q: (spreads[max(0, int(math.ceil(q * len(spreads))) - 1)] if spreads else None)
    c1 = {"look_candles": looks_total, "two_sided": n_two_sided, "two_sided_share": (n_two_sided / looks_total if looks_total else None), "spread_cents_median": nr(0.5), "spread_cents_p90": nr(0.9)}
    lines = [line_of(key, r) for key, r in rep.items()]
    return {"C1_candles_two_sided_and_spread": c1, "counts": c, "arms": rep, "lines": lines, "headline_arm": "band_25_headline at 1c", "upper_bound_note": UPPER_BOUND, "es_rows": es_stats, "ambiguities": AMBIGUITIES}


def run(lists, candle_runs, es_path):
    for f in list(lists) + list(candle_runs):
        k.guard(f)
    es, st = load_es_counted(es_path)
    check_es_rows(st)
    return run_windows(k.markets(lists), k.candles(candle_runs), es, st)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--candles" in a and "--es" in a:
        import json
        i, j = a.index("--candles"), a.index("--es")
        print(json.dumps(run(a[:i], a[i + 1:j], a[j + 1]), indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
