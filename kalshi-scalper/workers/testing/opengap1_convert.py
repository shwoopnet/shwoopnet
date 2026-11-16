#!/usr/bin/env python3
"""OPENGAP1 conversion (Testing Desk, Nov 16, 2026): raw Databento CSV files (scratch only) -> underlying.csv for opengap1_second.py. Prints counts only, never a price.
Rules (fixed before the pull): STAT_OPEN = 1 (OPENING_PRICE), STAT_CLOSE = 11 (CLOSE_PRICE) from the databento_dbn StatType enum order. For a symbol and an ET date
(ts_event in UTC - 5): the open is the FIRST OPENING_PRICE record with price > 0, the close the LAST CLOSE_PRICE record with price > 0. The consolidated daily bar (EQUS.SUMMARY ohlcv-1d)
gives the cross-check x_open and x_close; if a statistic differs from its bar by more than TOL_BPS the statistic is set missing (the day becomes no_underlying), counted, never guessed. An OPENING_PRICE record stamped after 09:31:00 ET is not known at the entry candle (ends 09:31 ET): the day is missing and counted.
Trading dates per symbol = the dates present in its ohlcv-1d file; prev_date = the previous such date.
Usage: opengap1_convert.py <scratch dir with xnas_stat.csv arcx_stat.csv equs_1d.csv> <out underlying.csv>
"""
import csv, datetime, os, sys

STAT_OPEN, STAT_CLOSE, TOL_BPS = 1, 11, 25.0
PERP_OF = {"SPY": "KXSPYPERP", "QQQ": "KXQQQPERP", "NVDA": "KXNVDAPERP", "AAPL": "KXAAPLPERP"}
FIRST_EVENT_DATE = "2026-11-06"


def et_dt(ts):
    s = ts.strip().replace("Z", "")
    base, _, frac = s.partition(".")
    d = datetime.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S")
    return d - datetime.timedelta(hours=5)          # ET = UTC - 5 on these dates (DST ended 2026-11-01)


def read_stats(path):
    opens, closes = {}, {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("symbol") not in PERP_OF: continue          # only the four symbols; every other row is dropped before any other column is used
            try: st, px = int(r["stat_type"]), float(r["price"])
            except (KeyError, TypeError, ValueError): continue
            if px <= 0 or st not in (STAT_OPEN, STAT_CLOSE): continue
            t = et_dt(r["ts_event"]); key = (r["symbol"], t.strftime("%Y-%m-%d"))
            if st == STAT_OPEN:
                if key not in opens or t < opens[key][0]: opens[key] = (t, px)
            elif key not in closes or t >= closes[key][0]: closes[key] = (t, px)
    return {k: v for k, v in opens.items()}, {k: v[1] for k, v in closes.items()}


def read_bars(path):
    bo, bc, dates = {}, {}, {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("symbol") not in PERP_OF: continue
            d = r["ts_event"][:10]          # the bar's trading date (the daily bar is stamped on its UTC date)
            bo[(r["symbol"], d)], bc[(r["symbol"], d)] = float(r["open"]), float(r["close"]); dates.setdefault(r["symbol"], set()).add(d)
    return bo, bc, {k: sorted(v) for k, v in dates.items()}


def convert(sdir, out):
    so, sc = {}, {}
    for f in ("xnas_stat.csv", "arcx_stat.csv"):
        o, c = read_stats(os.path.join(sdir, f)); so.update(o); sc.update(c)
    bo, bc, dates = read_bars(os.path.join(sdir, "equs_1d.csv"))
    miss = bad = late = 0
    def ok(stat, bar):
        nonlocal miss, bad
        if stat is None: miss += 1; return None
        if bar is not None and abs(stat / bar - 1) * 1e4 > TOL_BPS: bad += 1; return None
        return stat
    rows = []
    for sym in PERP_OF:
        ds = dates.get(sym, [])
        for i, d in enumerate(ds):
            if d < FIRST_EVENT_DATE or i == 0: continue
            pd = ds[i - 1]
            op = so.get((sym, d))
            if op is not None and op[0] > datetime.datetime.strptime(d + " 09:31:00", "%Y-%m-%d %H:%M:%S"): late += 1; op = None          # an opening print stamped after 09:31:00 ET was not known at the entry candle: the day is missing
            uo = ok(None if op is None else op[1], bo.get((sym, d))); up = ok(sc.get((sym, pd)), bc.get((sym, pd)))
            rows.append({"perp": PERP_OF[sym], "date": d, "prev_date": pd, "u_open": "" if uo is None else repr(uo), "u_prev_close": "" if up is None else repr(up), "x_open": repr(bo[(sym, d)]) if (sym, d) in bo else "", "x_prev_close": repr(bc[(sym, pd)]) if (sym, pd) in bc else ""})
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["perp", "date", "prev_date", "u_open", "u_prev_close", "x_open", "x_prev_close"]); w.writeheader(); w.writerows(rows)
    print("underlying rows", len(rows), "opening print after 09:31:00 ET (set missing)", late, "statistic missing", miss, "statistic differs from the daily bar by more than", TOL_BPS, "bps (set missing)", bad)
    return rows


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
