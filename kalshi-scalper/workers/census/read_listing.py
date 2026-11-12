#!/usr/bin/env python3
"""Untouched-family census: reader for the CENSUS_LISTING pull. Committed Nov 12, 2026, before
the pull was dispatched. Plan: workers/FAMILY_CENSUS_NOV12.md.

It COUNTS. Per series: category, frequency and fee fields from the series list, and from one
full day of settled non-combo markets the number of markets, the number of events, the summed
volume and open interest. No candle is read, no rule is scored, and no result field is used
except to count that a market settled.

Usage: python3 read_listing.py <folder of the CENSUS_LISTING run> <out dir>
Writes series_day.csv (one row per series seen) and prints a summary by category.
"""
import csv
import gzip
import json
import os
import sys
from collections import defaultdict


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def main():
    run, out = sys.argv[1], sys.argv[2]
    man = json.load(open(os.path.join(run, "manifest.json")))
    series, day = {}, defaultdict(lambda: {"markets": 0, "events": set(), "volume": 0.0, "oi": 0.0, "with_volume": 0})
    last_page, cut_hours, hours_read, truncated_lists = {}, [], set(), 0
    for row in man.get("rows", []):
        if row.get("status") != 200 or "file" not in row:
            continue
        if row.get("truncated"):
            truncated_lists += 1
            continue
        try:
            body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        except (OSError, ValueError):
            continue
        if not isinstance(body, dict):
            continue
        if row["path"] == "/series":
            for s in body.get("series") or []:
                if isinstance(s, dict) and s.get("ticker"):
                    series.setdefault(s["ticker"], s)
            continue
        hours_read.add(row["id"])
        last_page[row["id"]] = bool(body.get("cursor"))          # a cursor on the last page read means the hour was cut
        for m in body.get("markets") or []:
            tk = m.get("ticker", "")
            if not tk:
                continue
            d = day[tk.split("-")[0]]
            d["markets"] += 1
            d["events"].add(m.get("event_ticker", ""))
            v = num(m.get("volume_fp", m.get("volume")))
            d["volume"] += v
            d["with_volume"] += 1 if v > 0 else 0
            d["oi"] += num(m.get("open_interest_fp", m.get("open_interest")))
    cut_hours = sorted(h for h, cut in last_page.items() if cut)
    os.makedirs(out, exist_ok=True)
    cols = ["series", "category", "frequency", "fee_type", "fee_multiplier", "title", "settled_markets_day", "settled_events_day", "markets_with_volume", "volume_day", "open_interest_day", "in_series_list"]
    rows = []
    for tk in sorted(set(series) | set(day)):
        s, d = series.get(tk, {}), day.get(tk)
        rows.append([tk, s.get("category", ""), s.get("frequency", ""), s.get("fee_type", ""), s.get("fee_multiplier", ""), (s.get("title") or "")[:80],
                     d["markets"] if d else 0, len(d["events"]) if d else 0, d["with_volume"] if d else 0, round(d["volume"], 2) if d else 0, round(d["oi"], 2) if d else 0, int(tk in series)])
    with open(os.path.join(out, "series_day.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    print(f"series in the list {len(series)} | series with a market settled that day {len(day)} | hours read {len(hours_read)} of 24 | hours cut at the page cap {len(cut_hours)} {cut_hours[:6]}{' ...' if len(cut_hours) > 6 else ''} | series lists cut by the size cap {truncated_lists}")
    cat = defaultdict(lambda: [0, 0, 0, 0, 0.0])
    for r in rows:
        c = cat[r[1] or "(not in the series list)"]
        c[0] += 1
        c[1] += 1 if r[6] else 0
        c[2] += r[6]
        c[3] += r[7]
        c[4] += r[9]
    print("category | series | series settling that day | markets | events | volume")
    for k, c in sorted(cat.items(), key=lambda kv: -kv[1][4]):
        print(f"{k} | {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[4]:.0f}")
    print("top series by events settled that day (series, category, frequency, events, markets, volume):")
    for r in sorted(rows, key=lambda r: -r[7])[:25]:
        print("  ", r[0], "|", r[1], "|", r[2], "|", r[7], "|", r[6], "|", r[9])


if __name__ == "__main__":
    main()
