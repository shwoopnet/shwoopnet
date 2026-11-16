#!/usr/bin/env python3
"""SOCDRIFT census reader (Desk C, Nov 16, 2026): counts from the landed SOCDERIV_LISTS run, TIME FIELDS AND TICKERS ONLY (ticker, event_ticker, open_time,
close_time, occurrence_datetime, settlement_ts). No result, price or volume field is read. close_time is used only as a diagnostic for the clock calibration, never for timing or selection.
Usage: python3 -I socdrift_census.py <landed run dir>   (prints counts; makes no request)"""
import calendar, collections, glob, gzip, json, os, sys, time

def ts(s):
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")) if s else None

def games(d):
    man = json.load(open(os.path.join(d, "manifest.json")))
    g = collections.defaultdict(dict)
    trunc = []
    for r in man["rows"]:
        s = r["params"].get("series_ticker") if r.get("file") else None
        if not s or not s.endswith("GAME"):
            continue
        b = json.load(gzip.open(os.path.join(d, r["file"]), "rt"))
        if b.get("cursor"):
            trunc.append(s)
        for x in b.get("markets", []):
            e = g[s].setdefault(x["event_ticker"], {"o": ts(x["occurrence_datetime"]), "c": 0, "oc": set(), "s": None, "n": 0})
            e["c"] = max(e["c"], ts(x["close_time"])); e["oc"].add(x["occurrence_datetime"]); e["n"] += 1
            st = ts(x["settlement_ts"]) if x.get("settlement_ts") else None
            if st is not None:
                e["s"] = st if e["s"] is None else min(e["s"], st)
    return g, trunc

if __name__ == "__main__":
    d = sys.argv[1] if sys.argv[1].endswith("/") else sys.argv[1] + "/"
    g, trunc = games(d)
    q = lambda a, p: a[int(p * (len(a) - 1))] if a else None
    print("GAME lists with a cursor (truncated):", trunc)
    print("K calibration: close_time minus (occurrence - 3 h), hours, per league: n, 5th, median, 95th (close_time is a diagnostic only)")
    for s, ev in g.items():
        a = sorted((e["c"] - (e["o"] - 10800)) / 3600.0 for e in ev.values() if e["o"])
        print("  %-20s n %3d  p5 %6.2f  p50 %6.2f  p95 %6.2f" % (s, len(a), q(a, .05), q(a, .5), q(a, .95)))
    print("Data tier: games per close day, Sep 14 to Sep 19, and the earliest settlement_ts field present")
    day = collections.Counter(); earliest = None
    
    for s, ev in g.items():
        for e in ev.values():
            if e["s"] is not None:
                earliest = e["s"] if earliest is None else min(earliest, e["s"])
            if e["c"] and calendar.timegm((2026, 9, 12, 0, 0, 0)) <= e["c"] < calendar.timegm((2026, 9, 20, 0, 0, 0)):
                day[time.strftime("%m-%d", time.gmtime(e["c"]))] += 1
    print("  by close day:", sorted(day.items()))
    print("  earliest settlement_ts present:", None if earliest is None else time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(earliest)))
