#!/usr/bin/env python3
"""ECONHIST count table (Desk B, Nov 15, 2026). Usage: econhist_table.py <landed ECONHIST_LISTS run folder>
Counts per series only. Reads close_time FIRST (held-out cut, dropped and counted before any other field), then event_ticker. No result, price or volume.
Expected figures: EXPECTED_econhist_table_nov15.md. Hold map: Auditor B, Nov 15, 2026 21:30Z."""
import json, os, sys
from collections import defaultdict
from datetime import datetime, timezone
import census_table as C   # the same loaders and guard; ALLOWED_RUNS is replaced below
SERIES = ["KXCPI", "KXPAYROLLS", "KXPCECORE", "KXJOBLESSCLAIMS", "KXCONTCLAIMS", "KXUE", "KXISMPMI", "KXUSISMSERV", "KXUSPPIYOY", "KXCPINDEX"]
CUTS = {"KXCPI": 1758844800, "KXPCECORE": 1758844800}   # 2025-09-26T00:00:00Z: NOWCAST1's frozen holdout (forward read 2027-03-01); the other eight have no cut
ALLOWED_RUNS = frozenset(["2026-11-16T1522Z_43895509363"])   # the one ECONHIST_LISTS run (loaded for NOWCAST1; tickers, close times, counts only)

def table(rows):
    agg = defaultdict(lambda: {"n": 0, "dropped": 0, "dates": set(), "events": set(), "pages": 0, "cursor": ""})
    for rid, series, body in rows:
        if series not in SERIES: continue
        a = agg[series]; cut = CUTS.get(series)
        a["pages"] += 1; a["cursor"] = body.get("cursor") or ""
        for m in body.get("markets") or []:
            try: t = C.ts(m["close_time"])
            except (KeyError, ValueError, TypeError): continue
            if cut is not None and t >= cut: a["dropped"] += 1; continue
            a["n"] += 1; a["dates"].add(datetime.fromtimestamp(t, timezone.utc).date().isoformat()); a["events"].add(m.get("event_ticker", ""))
    out = []
    for s in sorted(agg):
        a = agg[s]; ds = sorted(a["dates"])
        out.append("%s: settled markets %d, after the held-out date dropped %d, close dates %d%s, events %d, %s" % (s, a["n"], a["dropped"], len(ds), " (%s to %s)" % (ds[0], ds[-1]) if ds else "", len(a["events"]),
                   ("truncated at %d pages, counts are a floor" if a["cursor"] else "complete at %d pages") % a["pages"]))
    return out

def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    C.ALLOWED_RUNS = ALLOWED_RUNS; C.guard([a[0]])
    print("ECONHIST count table (counts only; no result, price or volume read; the endpoint ends 2026-09-10). KXCPI and KXPCECORE are counted only before 2025-09-26; the held part is not counted.")
    print("\n".join(table(C.rows_of(a[0]))))

if __name__ == "__main__": main()
