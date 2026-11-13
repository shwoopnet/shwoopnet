#!/usr/bin/env python3
"""Lane-place report (Testing Desk, Nov 13, 2026; queue item 2 of the Head's 21:05Z message). Research only: reads recorded book files it is given, sends nothing. INVENTED rows only in tests
(OICORE_ADAPTER_AND_PLACE_REPORT_HAND_CASES.md item 2, committed first). NOT RUN on any real file: a real run needs the Head's go and Auditor B's CLEAN under rule 16.
For each registered wheel place: how many fill-checked signals it would log per US Central trading day on recorded data. COUNTS AND DATES ONLY: no result or outcome column is read, no price or book value is kept in the output,
a window that closes on or after the place's heldout_first is NOT read (counted), a signal decided before the place's start time is not counted (l), every folder goes through scorekit.guard.
Place kinds: 'depth' (the NC15 depth cell, frozen sheet section 2) and 'oicore' (the OICORE mechanism, oicore_shadow). 'cfrti' needs the perpetual's marks (not in the archive yet): reported as not built.
place spec (dicts, every field required): name, kind, series, start_ts, heldout_first (a UTC timestamp or None), log ('NC15' or 'R6'); 'oicore' also band_lo, band_hi, T, limit_add.
Counted signal = fill-checked and fillable (status filled) and not skipped under lane (i) (a limit of 88c or above is skipped, not counted, not a miss). Day = the US Central day of the signal poll's exchange time (lane (d)).
rate = counted signals / days with data; days to a 60-signal block = max(7, ceil(60 / rate)) (the lane's 7 day minimum), None at rate 0.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import spxoi1 as s1
import oicore_shadow as oc
import lane_block as lb

TOL = 1e-9
DEPTH_BAND = (0.10, 0.90)
DEPTH_IMB = 0.50
DEPTH_LOOK_S = 600
DEPTH_SIGNAL_MAX_AGE_S = 10.0
DEPTH_LIMIT_ADD = 0.01
BLOCK_N, BLOCK_DAYS = 60, 7
REQUIRED = ("name", "kind", "series", "start_ts", "heldout_first", "log")


def depth_signal(polls, close_ts):
    """-> ('signal', index, side, ask, limit) | ('no_signal', reason). Signal poll = the last poll at or before D = close - 600 s and at most 10 s before it."""
    D = close_ts - DEPTH_LOOK_S
    idx = [i for i, p in enumerate(polls) if D - DEPTH_SIGNAL_MAX_AGE_S - TOL <= p["t"] <= D + TOL]
    if not idx:
        return ("no_signal", "no poll in the 10 s before D")
    i = idx[-1]
    p = polls[i]
    y, n = sum(z for _, z in p["yes_bids"][:5]), sum(z for _, z in p["no_bids"][:5])
    if y + n <= 0:
        return ("no_signal", "no book sizes")
    imb = (y - n) / (y + n)
    if not abs(imb) >= DEPTH_IMB - TOL:
        return ("no_signal", "not in the cell", i)
    side = "yes" if imb > 0 else "no"
    ask = s1.ask_of(p, side)
    if ask is None:
        return ("no_signal", "no ask on the implied side", i)
    if not (DEPTH_BAND[0] - TOL <= ask <= DEPTH_BAND[1] + TOL):
        return ("no_signal", "ask outside 0.10 to 0.90", i)
    return ("signal", i, side, ask, ask + DEPTH_LIMIT_ADD)


def _check_spec(sp):
    for f in REQUIRED:
        if f not in sp:
            raise ValueError("place %r lacks the required field %r" % (sp.get("name"), f))
    if sp["kind"] == "oicore":
        for f in ("band_lo", "band_hi", "T", "limit_add"):
            if f not in sp:
                raise ValueError("place %r lacks the required field %r" % (sp["name"], f))
    oc.second_look_s(sp["log"])


def report_place(sp, polls_by_ticker, cs):
    _check_spec(sp)
    out = {"name": sp["name"], "kind": sp["kind"], "series": sp["series"]}
    if sp["kind"] not in ("depth", "oicore"):
        out["state"] = "not built (%s needs inputs this report does not read)" % sp["kind"]
        return out
    days, data_days = {}, set()
    held = no_poll = 0
    for tk in sorted(polls_by_ticker):
        if oc.series_of(tk) != sp["series"]:
            continue
        polls = polls_by_ticker[tk]
        closes = [p["close"] for p in polls if p.get("close") is not None]
        if not closes:
            no_poll += 1; continue
        close = closes[0]
        if sp["heldout_first"] is not None and close >= sp["heldout_first"]:
            held += 1; continue          # a held-out window is never read
        for p in polls:
            if p["t"] >= sp["start_ts"]:
                data_days.add(lb.central_day(p["t"]))
        if sp["kind"] == "depth":
            r = depth_signal(polls, close)
            if r[0] == "no_signal":
                if len(r) == 2:
                    no_poll += 1; continue
                pi, sig = r[2], None
            else:
                pi, sig = r[1], r
        else:
            by = {c["ts"]: c for c in (cs.get(tk) or [])}
            a, b = by.get(close - s1.OI_RECENT_S), by.get(close - s1.OI_EARLIER_S)
            r = oc.signal(polls, close, None if a is None else a.get("oi"), None if b is None else b.get("oi"), sp["band_lo"], sp["band_hi"], sp["T"], sp["limit_add"])
            if r[0] == "no_data" and r[1] == "no poll in window":
                no_poll += 1; continue
            if r[0] == "signal":
                pi, sig = r[1], r
            else:
                look = [i for i, p in enumerate(polls) if close - 180 - TOL <= p["t"] <= close - 120 + TOL]
                pi, sig = (look[0] if look else None), None
                if pi is None:
                    no_poll += 1; continue
        t = polls[pi]["t"]
        if t < sp["start_ts"]:
            continue          # decided before the start time (l)
        day = lb.central_day(t)
        d = days.setdefault(day, {"windows_examined": 0, "signals_counted": 0, "misses": 0, "not_fill_checked": 0, "skipped_88c": 0})
        d["windows_examined"] += 1
        if sig is None:
            continue
        side, limit = sig[2], sig[4]
        if int(math.floor(100.0 * limit + 1e-6)) >= lb.FAV_CENTS:
            d["skipped_88c"] += 1; continue
        st = oc.fill_check(polls, pi, side, limit, sp["log"])
        if st[0] == "filled":
            d["signals_counted"] += 1
        elif st[0] == "miss":
            d["misses"] += 1
        else:
            d["not_fill_checked"] += 1
    total = sum(d["signals_counted"] for d in days.values())
    nd = len(data_days)
    rate = (total / nd) if nd else None
    out.update({"per_day": {k_: days[k_] for k_ in sorted(days)}, "days_with_data": nd, "signals_counted": total, "held_out_windows_not_read": held, "windows_without_a_signal_poll": no_poll,
                "signals_per_day": rate, "days_to_a_%d_signal_block" % BLOCK_N: (max(BLOCK_DAYS, int(math.ceil(BLOCK_N / rate - 1e-12))) if rate else None)})
    return out


def report(places, polls_by_ticker, cs):
    return {"note": "counts and dates only; no outcome, no price; held-out windows not read", "places": [report_place(sp, polls_by_ticker, cs) for sp in places]}


def load_books(book_files, candle_folders=()):
    """Guarded loading: every folder goes through scorekit.guard (a HELDOUT_ folder or a listed run is refused)."""
    polls = {}
    for f in book_files:
        k.guard(os.path.dirname(os.path.abspath(f)))
        for tk, v in s1.load_nc15(f).items():
            polls.setdefault(tk, []).extend(v)
    polls = {tk: sorted(v, key=lambda p: p["t"]) for tk, v in polls.items()}
    cs = k.candles(list(candle_folders)) if candle_folders else {}
    for f in candle_folders:
        k.guard(f)
    return polls, cs


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[1] == "--books":
        places = json.load(open(a[0]))
        j = a.index("--candles") if "--candles" in a else len(a)
        polls, cs = load_books(a[2:j], a[j + 1:])
        print(json.dumps(report(places, polls, cs), indent=1, default=str))
    else:
        print(__doc__)
