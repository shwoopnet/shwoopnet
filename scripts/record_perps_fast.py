#!/usr/bin/env python3
"""Samples Kalshi's public perpetual markets every 30 seconds around the US stock open and close (research only, 2026-11-05).

Why (the owner, Nov 5, 2026, after Kalshi listed single stock perps: "Faster data, then 10 to 20 tests"): the hourly recorder (record_perps.py) gives about 300 snapshots
per market in two weeks, too coarse to test whether a stock perp drifts from its stock around the cash open, the close or overnight. This keeps the same columns, one
plain GET of the public list per sample: no key, no login, no order. It writes files and nothing else.

Windows are in New York time so they follow daylight saving: 09:10 to 10:30 (the 09:30 open) and 15:40 to 17:00 (the 16:00 close), Monday to Friday. Run at any time:
outside a window it exits at once; inside one it records until the window ends, so a late start only records less and a second start for the same window does nothing.
It stops by itself after STOP_DATE.

Usage: python3 scripts/record_perps_fast.py OUT_DIR      (writes OUT_DIR/<YYYY-MM-DD>/<open|close>.csv.gz)
"""
import csv
import datetime as dt
import gzip
import importlib.util
import io
import json
import os
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("record_perps", os.path.join(HERE, "record_perps.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

NY = ZoneInfo("America/New_York")
WINDOWS = (("open", (9, 10), (10, 30)), ("close", (15, 40), (17, 0)))
EVERY_S = 30
STOP_DATE = dt.date(2026, 12, 7)   # 30 days of data, then a reviewed edit to extend


def current_window(now_utc):
    ny = now_utc.astimezone(NY)
    if ny.weekday() >= 5:
        return None
    for name, (h1, m1), (h2, m2) in WINDOWS:
        start = ny.replace(hour=h1, minute=m1, second=0, microsecond=0)
        end = ny.replace(hour=h2, minute=m2, second=0, microsecond=0)
        if start <= ny < end:
            return name, ny.date().isoformat(), end.astimezone(dt.timezone.utc)
    return None


def fetch():
    req = urllib.request.Request(base.URL, headers={"User-Agent": "shwoopnet-research-recorder"})
    return json.load(urllib.request.urlopen(req, timeout=20)).get("markets") or []


def main(out_dir, now_fn=lambda: dt.datetime.now(dt.timezone.utc), fetch_fn=fetch, sleep_fn=time.sleep):
    now = now_fn()
    if now.date() > STOP_DATE:
        print("past the stop date; nothing recorded")
        return 0
    win = current_window(now)
    if not win:
        print("outside the open and close windows; nothing recorded")
        return 0
    name, day, end = win
    path = os.path.join(out_dir, day, name + ".csv.gz")
    if os.path.exists(path):
        print("this window is already recorded; nothing to do")
        return 0
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(base.COLUMNS)
    samples = fails = 0
    while now_fn() < end:
        t0 = time.monotonic()
        try:
            markets = fetch_fn()
            if markets:
                w.writerows(base.rows(markets, now_fn().strftime("%Y-%m-%dT%H:%M:%SZ")))
                samples += 1
        except Exception as e:   # one failed read costs one sample, never the window
            fails += 1
            print("read failed: %s" % str(e)[:80])
        sleep_fn(max(0.0, EVERY_S - (time.monotonic() - t0)))
    if not samples:
        print("no samples; nothing written")
        return 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", newline="") as f:
        f.write(buf.getvalue())
    print("wrote %d samples (%d failed reads) to %s" % (samples, fails, path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "perps30"))
