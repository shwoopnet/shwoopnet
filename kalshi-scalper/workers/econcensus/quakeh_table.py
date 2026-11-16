#!/usr/bin/env python3
"""QUAKEH count reader (Desk B, Nov 16, 2026). Usage: quakeh_table.py <landed QUAKEH_LISTS run folder>
Per row, in this order: ticker (wrong series: dropped and counted, nothing else parsed), close_time (outside the window: dropped and counted before any other field), event_ticker.
No result, price, volume or status key is read. Expected figures: EXPECTED_quakeh_table_nov16.md."""
import os, sys
from collections import defaultdict
from datetime import datetime, timezone
import census_table as C
SERIES_PREFIX = "KXBIGGESTQUAKEH-"
LO, HI = C.ts("2026-09-17T00:00:00Z"), C.ts("2026-10-17T00:00:00Z")
ALLOWED_RUNS = frozenset()      # a reviewed edit names the one QUAKEH_LISTS run folder after it lands

def med(v):
    v = sorted(v); n = len(v)
    return None if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2)

def table(rows):
    day_m, day_e = defaultdict(int), defaultdict(set); out_series = out_window = 0; cursor = ""
    for rid, series, body in rows:
        cursor = body.get("cursor") or ""
        for m in body.get("markets") or []:
            try: tk = m["ticker"]
            except (KeyError, TypeError): out_series += 1; continue
            if not isinstance(tk, str) or not tk.startswith(SERIES_PREFIX): out_series += 1; continue
            try: t = C.ts(m["close_time"])
            except (KeyError, ValueError, TypeError): out_window += 1; continue
            if not (LO <= t < HI): out_window += 1; continue
            d = datetime.fromtimestamp(t, timezone.utc).date().isoformat()
            day_m[d] += 1; day_e[d].add(m.get("event_ticker", ""))
    days = sorted(day_m); fmt = lambda x: "n/a" if x is None else ("%g" % x)
    lines = ["markets %d | events %d | days %d | median markets a day %s | median events a day %s | dropped outside the series %d | dropped outside the window %d | last page %s" % (
        sum(day_m.values()), len({e for d in days for e in day_e[d]}), len(days), fmt(med([day_m[d] for d in days])), fmt(med([len(day_e[d]) for d in days])), out_series, out_window,
        "carries a cursor, so the list is cut" if cursor else "complete")]
    lines += ["%s: markets %d, events %d" % (d, day_m[d], len(day_e[d])) for d in days]
    return lines

def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    C.ALLOWED_RUNS = ALLOWED_RUNS; C.guard([a[0]])
    print("QUAKEH count table (counts only; ticker, close_time and event_ticker are the only fields read)")
    print("\n".join(table(C.rows_of(a[0]))))

if __name__ == "__main__": main()
