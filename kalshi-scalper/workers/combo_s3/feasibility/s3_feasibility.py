#!/usr/bin/env python3
"""S3 feasibility count (Desk B). COUNTS ONLY: per UTC day, how many combos S3 would fill, from the registered entry rules.
Reads from combo/DATE/HHMM/quotes.csv.gz only these columns: t_recv_ms, ticker, event_ticker, close_time, yes_bid, yes_ask, no_ask, yes_bid_size, volume, legs.
It never opens results.csv.gz and reads no result, trade price, order book or leg ticker. Prints counts. Writes no file. stdlib only.
Constants are S3's (workers/S3_COMBO_HOUSE_SIDE_REGISTRATION.md); the threshold is fixed in EXPECTED_hand_feasibility.md.
Usage: s3_feasibility.py <checkout of combo-data> [--full-snapshots 40] [--min-days 3] [--threshold 5]"""
import argparse, csv, glob, gzip, os, sys
from collections import defaultdict
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()
START = datetime(2026, 11, 13, tzinfo=timezone.utc).timestamp()
P_MIN, P_MAX, SLIP, MIN_SIZE = 0.60, 0.90, 0.01, 3.0
LEGS_MIN, LEGS_MAX = 2, 30
CLOSE_MIN_S, CLOSE_MAX_S = 3600, 14 * 86400
MAX_PER_SNAP = 10
EPS = 1e-9

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def ts(iso): return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()

def two_sided(r):
    yb, ya, na = num(r.get("yes_bid")), num(r.get("yes_ask")), num(r.get("no_ask"))
    return yb is not None and ya is not None and na is not None and 0 < yb < ya < 1 and 0 < na < 1

def qualifies(r, t):
    if not two_sided(r): return None
    na, size, vol, legs = num(r.get("no_ask")), num(r.get("yes_bid_size")), num(r.get("volume")), num(r.get("legs"))
    if size is None or vol is None or legs is None or not r.get("close_time"): return None
    p = na + SLIP
    try: left = ts(r["close_time"]) - t
    except ValueError: return None
    if P_MIN - EPS <= p <= P_MAX + EPS and size >= MIN_SIZE and vol > 0 and LEGS_MIN <= legs <= LEGS_MAX and CLOSE_MIN_S <= left <= CLOSE_MAX_S:
        return {"ticker": r["ticker"], "event": r.get("event_ticker", "")}
    return None

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--full-snapshots", type=int, default=40)
    ap.add_argument("--min-days", type=int, default=3); ap.add_argument("--threshold", type=float, default=5.0)
    a = ap.parse_args(argv)
    days = defaultdict(lambda: {"snaps": 0, "rows": 0, "two": 0, "qual": 0, "fills": 0}); ignored_s = ignored_r = 0
    seen_t, seen_e = set(), set(); files = sorted(glob.glob(os.path.join(a.root, "combo", "*", "*", "quotes.csv.gz")))
    snaps = []
    for q in files:
        rows = list(csv.DictReader(gzip.open(q, "rt", newline="")))
        if rows: snaps.append(rows)
    snaps.sort(key=lambda rows: min((num(r.get("t_recv_ms")) or 0) for r in rows))
    for rows in snaps:
        t0 = min((num(r.get("t_recv_ms")) or 0) for r in rows) / 1000.0
        if t0 < START: ignored_s += 1; ignored_r += len(rows); continue
        day = datetime.fromtimestamp(t0, timezone.utc).strftime("%Y-%m-%d"); d = days[day]
        d["snaps"] += 1; d["rows"] += len(rows); cand = []
        for r in rows:
            t = (num(r.get("t_recv_ms")) or 0) / 1000.0
            if two_sided(r): d["two"] += 1
            f = qualifies(r, t)
            if f: d["qual"] += 1; cand.append(f)
        cand.sort(key=lambda f: f["ticker"]); n = 0
        for f in cand:
            if n >= MAX_PER_SNAP or f["ticker"] in seen_t or (f["event"] and f["event"] in seen_e): continue
            seen_t.add(f["ticker"]); seen_e.add(f["event"]); d["fills"] += 1; n += 1
    print("S3 feasibility count, counts only (no result read)")
    for day in sorted(days):
        d = days[day]
        print("%s: snapshots %d | rows %d | two-sided rows %d | qualifying rows %d | would-be fills %d%s" % (day, d["snaps"], d["rows"], d["two"], d["qual"], d["fills"], " | full day" if d["snaps"] >= a.full_snapshots else ""))
    print("ignored before 2026-11-13T00:00Z: %d snapshots, %d rows" % (ignored_s, ignored_r))
    full = [days[x]["fills"] for x in sorted(days) if days[x]["snaps"] >= a.full_snapshots]
    if len(full) < a.min_days: print("verdict: not decided yet (%d full days, need %d)" % (len(full), a.min_days))
    else:
        avg = sum(full) / len(full)
        print("verdict: %s (average %.1f would-be fills a full day over %d full days, threshold %.1f)" % ("no evidence: combos cannot be priced" if avg < a.threshold else "continue to the registered read", avg, len(full), a.threshold))
    return 0

if __name__ == "__main__": sys.exit(main())
