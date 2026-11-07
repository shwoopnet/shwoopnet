#!/usr/bin/env python3
"""Samples Kalshi's public perpetual markets every 10 seconds around the Sunday reopening (research only, 2026-11-06, V2's request, the owner approved).

Why: the stock and index perps trade while the cash market is shut, and the first minutes after the weekend reopening (Sunday 18:00 New York) show how the book
re-forms and where the perp sits against the Friday close. The 30 second recorder only covers the weekday open and close. Same columns as that recorder, one plain GET of
the public list per sample: no key, no login, no order.

The window is 17:55 to 18:35 New York time on Sundays (so it follows daylight saving). Run at any time: outside it, or past STOP_DATE, it exits at once; a second start for the
same Sunday does nothing.

Usage: python3 scripts/record_perps_sunday.py OUT_DIR      (writes OUT_DIR/<YYYY-MM-DD>/sunday.csv.gz)
"""
import csv
import datetime as dt
import gzip
import importlib.util
import io
import os
import sys
import time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("record_perps_fast", os.path.join(HERE, "record_perps_fast.py"))
fast = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fast)
base = fast.base

NY = ZoneInfo("America/New_York")
START, END = (17, 55), (18, 35)
EVERY_S = 10
STOP_DATE = dt.date(2027, 2, 26)


def current_window(now_utc):
    ny = now_utc.astimezone(NY)
    if ny.weekday() != 6:
        return None
    start = ny.replace(hour=START[0], minute=START[1], second=0, microsecond=0)
    end = ny.replace(hour=END[0], minute=END[1], second=0, microsecond=0)
    if start <= ny < end:
        return "sunday", ny.date().isoformat(), end.astimezone(dt.timezone.utc)
    return None


def main(out_dir, now_fn=lambda: dt.datetime.now(dt.timezone.utc), fetch_fn=fast.fetch, sleep_fn=time.sleep):
    now = now_fn()
    if now.date() > STOP_DATE:
        print("past the stop date; nothing recorded")
        return 0
    win = current_window(now)
    if not win:
        print("outside the Sunday reopening window; nothing recorded")
        return 0
    name, day, end = win
    path = os.path.join(out_dir, day, name + ".csv.gz")
    if os.path.exists(path):
        print("this window is already recorded; nothing to do")
        return 0
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(base.COLUMNS + fast.EXTRA_COLUMNS)
    samples = fails = 0
    while now_fn() < end:
        t0 = time.monotonic()
        try:
            markets = fetch_fn()
            if markets:
                w.writerows(fast.rows_with_flags(markets, now_fn().strftime("%Y-%m-%dT%H:%M:%SZ")))
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
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "perps10"))
