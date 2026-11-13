#!/usr/bin/env python3
"""OICORE-mechanism shadow adapter for ANY NC15 or R6 market (Testing Desk, Nov 13, 2026; queue item 1 of the Head's 21:05Z message). Research only; INVENTED rows only in tests
(OICORE_ADAPTER_AND_PLACE_REPORT_HAND_CASES.md, committed first). spxoi1.py stays as audited; this module reuses its loader, book helpers and cents function and generalises the rule.
oicore_shadow(polls_by_ticker, cs, series, band_lo, band_hi, T, limit_add, log): series, band (the cheaper side's ASK in dollars, inclusive 1e-9), T, limit_add and log ('NC15' = second look the next poll within 6 s; 'R6' = within 4 s) are ALL required.
Mechanism: oi_rise = open interest at the candle ending close - 180 s minus the one ending close - 360 s (both needed), fires at >= T; signal poll = the FIRST poll in [close - 180, close - 120] whose cheaper side (lower ask, tie YES, both book sides needed) has its ask in the band; limit = ask + limit_add; one signal per market.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxoi1 as s1

TOL = s1.TOL
SECOND_LOOK = {"NC15": 6.0, "R6": 4.0}


def second_look_s(log):
    if log not in SECOND_LOOK:
        raise ValueError("log must be 'NC15' or 'R6', got %r" % (log,))
    return SECOND_LOOK[log]


def series_of(ticker):
    return str(ticker).split("-")[0]


def band_text(lo, hi):
    return "%.2f to %.2f" % (lo, hi)


def signal(polls, close_ts, oi_now, oi_prev, band_lo, band_hi, T, limit_add):
    """-> ('signal', index, side, ask, limit) | ('no_trade', reason) | ('no_data', reason). Nothing here has a default."""
    if oi_now is None or oi_prev is None:
        return ("no_data", "no open interest")
    if not (oi_now - oi_prev >= T - TOL):
        return ("no_trade", "oi rise under T")
    cand = [i for i, p in enumerate(polls) if close_ts - s1.LOOK_FROM_S - TOL <= p["t"] <= close_ts - s1.LOOK_TO_S + TOL]
    if not cand:
        return ("no_data", "no poll in window")
    for i in cand:
        c = s1.cheaper(polls[i])
        if c is None:
            continue
        if band_lo - TOL <= c[1] <= band_hi + TOL:
            return ("signal", i, c[0], c[1], c[1] + limit_add)
    return ("no_trade", "cheaper side outside " + band_text(band_lo, band_hi))


def fill_check(polls, i, side, limit, log):
    """-> ('filled', price) | ('miss', why) | ('not_fill_checked', why): the NEXT poll within 6 s (NC15) or 4 s (R6) of the signal poll; both polls offer 10 at or under the limit; fill = the higher walked price."""
    span = second_look_s(log)
    if i + 1 >= len(polls) or polls[i + 1]["t"] - polls[i]["t"] > span + TOL:
        return ("not_fill_checked", "no second poll within %g s" % span)
    a, b = polls[i], polls[i + 1]
    if not (s1.offers(a, side, limit) and s1.offers(b, side, limit)):
        return ("miss", "10 contracts not offered at or under the limit on both polls")
    return ("filled", max(s1.walked(a, side), s1.walked(b, side)))


def oicore_shadow(polls_by_ticker, cs, series, band_lo, band_hi, T, limit_add, log):
    second_look_s(log)          # validates log even when no ticker matches
    out = {}
    for tk, polls in polls_by_ticker.items():
        if series_of(tk) != series:
            continue
        closes = [p["close"] for p in polls if p.get("close") is not None]
        if not closes:
            out[tk] = ("no_data", "no close time"); continue
        close = closes[0]
        by = {c["ts"]: c for c in (cs.get(tk) or [])}
        a, b = by.get(close - s1.OI_RECENT_S), by.get(close - s1.OI_EARLIER_S)
        r = signal(polls, close, None if a is None else a.get("oi"), None if b is None else b.get("oi"), band_lo, band_hi, T, limit_add)
        out[tk] = ("trade", r[2], r[3], {"limit": r[4], "t": polls[r[1]]["t"]}) if r[0] == "signal" else r
    return out


if __name__ == "__main__":
    print(__doc__)
