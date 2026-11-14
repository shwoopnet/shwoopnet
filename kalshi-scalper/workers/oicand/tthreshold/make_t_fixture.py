#!/usr/bin/env python3
"""MADE-UP fixture for the OICORE-NC15 threshold reader (not Kalshi data). argv[1] = output directory (cand/ and lists/)."""
import json, os, sys
from datetime import datetime, timezone
d = sys.argv[1]; os.makedirs(d + "/cand", exist_ok=True); os.makedirs(d + "/lists", exist_ok=True)
def T(s): return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
def iso(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
lists, cands, n = [], [], [0]
def window(series, close, rise, mode="ok"):
    n[0] += 1; tk = "%s-W%03d" % (series, n[0]); c = T(close)
    lists.append({"ticker": tk, "close_time": close})
    cs = []
    if mode != "no360": cs.append({"end_period_ts": c - 360, "open_interest_fp": "1000.00"})
    cs.append({"end_period_ts": c - 180} if mode == "nooi" else {"end_period_ts": c - 180, "open_interest_fp": "%.2f" % (1000 + rise)})
    cs.append({"end_period_ts": c - 120, "open_interest_fp": "9999.00"})     # a later candle that must never be used
    cands.append({"market_ticker": tk, "candlesticks": cs})
def day(series, date, rises, extra=None):
    for i, r in enumerate(rises): window(series, "%sT16:%02d:00Z" % (date, 15 * i), r)
day("S1", "2026-11-02", [1000, 2000, 3000, 4000])
for i, r in enumerate([10, 20, 30]): window("S1", "2026-11-03T16:%02d:00Z" % (15 * i), r)
window("S1", "2026-11-04T05:30:00Z", 40)
day("S1", "2026-11-04", [50, 60, 70, 80]); day("S1", "2026-11-05", [90, 100, 110, 120])
window("S1", "2026-11-05T17:00:00Z", 5, "no360"); window("S1", "2026-11-05T17:15:00Z", 5, "nooi")
for dt, rs in (("2026-11-03", [1, 1, 1, 2]), ("2026-11-04", [2, 2, 3, 3]), ("2026-11-05", [3, 4, 4, 4])): day("S2", dt, rs)
day("S3", "2026-11-03", [10, 20, 30, 40]); day("S3", "2026-11-04", [50, 60, 70, 80])
for dt, rs in (("2026-11-03", [10, 20, 30, 40]), ("2026-11-04", [50, 60, 70, 80]), ("2026-11-05", [90, 100, 110, 120])): day("S4", dt, rs)
def case(i, fields):
    n[0] += 1; tk = "S4-W%03d" % n[0]; c = T("2026-11-05T18:%02d:00Z" % (15 * i if i < 4 else 15 * (i - 4))) if i < 4 else T("2026-11-05T19:%02d:00Z" % (15 * (i - 4)))
    lists.append({"ticker": tk, "close_time": iso(c)})
    c180 = {"end_period_ts": c - 180}; c180.update(fields)
    cands.append({"market_ticker": tk, "candlesticks": [{"end_period_ts": c - 360, "open_interest_fp": "1000.00"}, c180]})
case(0, {"open_interest_fp": "1500.00", "open_interest": "9999"})
case(1, {"open_interest_fp": "abc", "open_interest": "9999"})
case(2, {"open_interest_fp": True, "open_interest": "9999"})
case(3, {"open_interest_fp": "nan"})
case(4, {"open_interest_fp": "inf"})
case(5, {"open_interest_fp": ""})
case(6, {"open_interest": "1700"})
for dt, rs in (("2026-11-03", [10, 20, 30, 40]), ("2026-11-04", [50, 60, 70, 80]), ("2026-11-05", [90, 100, 110, 120])): day("S5", dt, rs)
window("S5", "2026-11-04T13:30:00Z", 3000); window("S5", "2026-11-05T13:30:00Z", 5000)
json.dump({"markets": lists}, open(d + "/lists/l1.json", "w")); json.dump({"markets": cands}, open(d + "/cand/c1.json", "w"))
