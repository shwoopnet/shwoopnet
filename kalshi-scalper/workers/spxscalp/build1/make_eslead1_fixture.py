#!/usr/bin/env python3
"""Writes the MADE-UP ESLEAD1 fixture (not Databento, not Kalshi) into a directory given as argv[1]."""
import csv, gzip, json, os, sys
from datetime import datetime, timezone
d = sys.argv[1]; os.makedirs(d + "/cand", exist_ok=True); os.makedirs(d + "/lists", exist_ok=True)
C = int(datetime(2026, 11, 6, 15, 0, 0, tzinfo=timezone.utc).timestamp()); O = C - 900
es = [100, 101, 101, 103, 102, 104, 104, 105, 107, 106]
mid = [0.50, 0.50, 0.52, 0.52, 0.56, 0.55, 0.59, 0.59, 0.60, 0.64]
def iso(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
with open(d + "/es.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow("ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume".split(","))
    for t, p in enumerate(es): w.writerow([iso(O + 60 * t - 60), 33, 1, 7, p, p, p, p, 1])
cs = [{"end_period_ts": O + 60 * t, "yes_bid": {"close_dollars": "%.2f" % (m - 0.01)}, "yes_ask": {"close_dollars": "%.2f" % (m + 0.01)}} for t, m in enumerate(mid)]
json.dump({"markets": [{"market_ticker": "KXINX15M-FIX1", "candlesticks": cs}]}, open(d + "/cand/c1.json", "w"))
json.dump({"markets": [{"ticker": "KXINX15M-FIX1", "close_time": iso(C).replace(".000000000", "")}]}, open(d + "/lists/l1.json", "w"))
