#!/usr/bin/env python3
"""Live-against-shadow check harness for the trial seats (Testing Desk, Nov 13, 2026). Research only: reads rows it is given, sends nothing, places nothing.
TOOLS ONLY, tested on INVENTED rows (test_liveshadow.py, hand case LIVESHADOW_HAND_CASE.md committed first). No live figure is stored in any file; the live orders arrive later from the nightly report through Main.

compare(live_rows, windows, shadow, books) -> aggregates:
  live_rows : nightly-report rows of ONE seat: dicts with ticker, side ('yes'/'no'), count (filled), orderedCount, fill (dollars; a value above 1.0 is read as cents), sentAtMs (else tickStartMs).
  windows   : the universe of tickers examined (every window of the period); live and shadow tickers are added to it.
  shadow    : {ticker: ('trade', side, price) | ('no_trade', reason) | ('no_data', reason)} from the card's own rule (a data gap is not a rule decision).
  books     : {ticker: [poll]} with poll = dict(t seconds, yes_bids [(price, size)], no_bids [(price, size)]) best first: scorekit.r6_book shape (R6 for Bitcoin and gold); NC15 polls for KXINX15M must be loaded into the same shape by the caller (that layout is not read here).
Touch seen: the last poll at or before the order's send time and no more than MAX_AGE_S before it; YES touch = 1 - best NO bid, NO touch = 1 - best YES bid. Fill gap (cents) = live fill - touch; positive = the live fill was WORSE than the touch.
Agreement universe: windows where the seat attempted (orderedCount or count above 0) OR the shadow traded. Agree = same window, same side, both traded (a live attempt that did not fill still agrees).
Reason codes: AGREE, AGREE_LIVE_NOFILL, SIDE_MISMATCH, LIVE_ONLY_SHADOW_NO_TRADE, LIVE_ONLY_SHADOW_NO_DATA, SHADOW_ONLY, LIVE_BOTH_SIDES.
cfrti_k_shadow(...) builds the shadow dict for CFRTI-K from the audited reader's own functions (signal, decide), unchanged.
"""
import bisect, json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAX_AGE_S = 4.0
TOL = 1e-9
CODES = ("AGREE", "AGREE_LIVE_NOFILL", "SIDE_MISMATCH", "LIVE_ONLY_SHADOW_NO_TRADE", "LIVE_ONLY_SHADOW_NO_DATA", "SHADOW_ONLY", "LIVE_BOTH_SIDES")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _price(v):
    x = _num(v)
    if x is None:
        return None
    return x / 100.0 if x > 1.0 + TOL else x


def _qty(v):
    x = _num(v)
    return 0.0 if x is None else x


def send_time(row):
    for key in ("sentAtMs", "tickStartMs"):
        x = _num(row.get(key))
        if x is not None:
            return x / 1000.0
    return None


def touch_seen(polls, side, t_send, max_age=MAX_AGE_S):
    """The best ask of `side` on the last poll at or before t_send and within max_age seconds of it; None when there is no such poll or the side has no opposite bid."""
    if not polls or t_send is None:
        return None
    times = [p["t"] for p in polls]
    j = bisect.bisect_right(times, t_send + TOL) - 1
    if j < 0 or t_send - times[j] > max_age + TOL:
        return None
    lv = polls[j]["no_bids"] if side == "yes" else polls[j]["yes_bids"]
    if not lv:
        return None
    return 1.0 - max(px for px, _ in lv)


def _pct(xs, q):
    s = sorted(xs)
    return s[max(0, int(math.ceil(q * len(s))) - 1)]


def compare(live_rows, windows, shadow, books):
    by = {}
    for r in live_rows:
        by.setdefault(r.get("ticker"), []).append(r)
    universe = set(t for t in windows if t) | set(t for t in by if t) | set(shadow)
    gaps, no_touch, filled_orders, live_orders = [], 0, 0, 0
    codes = {c: 0 for c in CODES}
    out_rows = []
    agree_n = union_n = 0
    for tkr in sorted(universe):
        rows = by.get(tkr, [])
        live_rows_attempt = [r for r in rows if _qty(r.get("orderedCount")) > 0 or _qty(r.get("count")) > 0]
        live_orders += len(live_rows_attempt)
        for r in live_rows_attempt:
            if _qty(r.get("count")) > 0:
                filled_orders += 1
                fill, side, ts = _price(r.get("fill")), str(r.get("side", "")).lower(), send_time(r)
                tch = touch_seen(books.get(tkr), side, ts)
                if tch is None or fill is None:
                    no_touch += 1
                else:
                    gaps.append(round((fill - tch) * 100.0, 6))
        sh = shadow.get(tkr)
        shadow_trades = bool(sh and sh[0] == "trade")
        live_sides = sorted({str(r.get("side", "")).lower() for r in live_rows_attempt})
        attempted = bool(live_rows_attempt)
        if not (attempted or shadow_trades):
            continue
        union_n += 1
        filled = any(_qty(r.get("count")) > 0 for r in live_rows_attempt)
        if len(live_sides) > 1:
            code, detail = "LIVE_BOTH_SIDES", "live sides %s" % live_sides
        elif attempted and shadow_trades:
            if live_sides[0] == sh[1]:
                code, detail = ("AGREE" if filled else "AGREE_LIVE_NOFILL"), live_sides[0]
            else:
                code, detail = "SIDE_MISMATCH", "live %s, shadow %s" % (live_sides[0], sh[1])
        elif attempted:
            if sh is None or sh[0] == "no_data":
                code, detail = "LIVE_ONLY_SHADOW_NO_DATA", (sh[1] if sh else "no shadow decision supplied")
            else:
                code, detail = "LIVE_ONLY_SHADOW_NO_TRADE", sh[1]
        else:
            code, detail = "SHADOW_ONLY", "shadow %s" % sh[1]
        codes[code] += 1
        if code in ("AGREE", "AGREE_LIVE_NOFILL"):
            agree_n += 1
        else:
            out_rows.append({"ticker": tkr, "code": code, "detail": detail})
    fg = {"orders_with_a_touch": len(gaps), "filled_orders_with_no_touch": no_touch}
    if gaps:
        fg.update({"median_cents": st.median(gaps), "mean_cents": sum(gaps) / len(gaps), "worse_than_touch_share": sum(1 for g in gaps if g > TOL) / len(gaps),
                   "max_cents": max(gaps), "min_cents": min(gaps), "p90_cents": _pct(gaps, 0.9)})
    return {"windows_considered": len(universe), "live_orders": live_orders, "filled_live_orders": filled_orders, "agreement_universe": union_n, "agree": agree_n,
            "agreement_rate": (agree_n / union_n if union_n else None), "codes": codes, "fill_gap": fg, "disagreements": out_rows,
            "note": "aggregates only; positive fill gap = the live fill was worse than the touch seen; touch = last book poll at or before the send time within %.0f s" % MAX_AGE_S}


def cfrti_k_shadow(mk, cs, mids):
    """CFRTI-K's shadow decision per KXBTC15M window from the audited reader's own functions: {ticker: ('trade', side, ask) | ('no_trade', reason) | ('no_data', reason)}.
    mk = scorekit.markets, cs = scorekit.candles (KXBTC15M), mids = cfrti_k_heldout_second.perp_mids(...). Rule-says-no reasons are the three decision tests; everything else is a data gap."""
    import cfrti_k_heldout_second as r
    rule_no = {"edge under 5c", "spread above 3c", "cheap side outside 0.05 to 0.30"}
    out = {}
    for tkr, m in mk.items():
        if m["series"] != r.SERIES or m["close"] is None:
            continue
        c = m["close"]
        dec = {x["ts"]: x for x in cs.get(tkr, [])}.get(c - 120)
        if dec is None or dec.get("bid") is None or dec.get("ask") is None:
            out[tkr] = ("no_data", "no decision candle"); continue
        why, sd, z = r.signal(c, mids)
        if why:
            out[tkr] = ("no_data", why); continue
        pick, reason = r.decide(dec["bid"], dec["ask"], r.phi(z))
        out[tkr] = ("trade", pick[0], pick[1]) if pick else (("no_trade", reason) if reason in rule_no else ("no_data", reason))
    return out


if __name__ == "__main__":
    print(__doc__)
