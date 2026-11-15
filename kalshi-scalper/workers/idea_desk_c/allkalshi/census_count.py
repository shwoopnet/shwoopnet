#!/usr/bin/env python3
"""ALL-KALSHI census, counts only (Idea Desk C, Nov 15, 2026; the owner's item 3 via the Head of R&D).

Reads one landed kalshi-pull run of CENSUS_LISTING (Desk B's job: the series list and every non-combo market settled on 2026-11-10 UTC).
Reads ONLY: from /series answers, ticker, category, frequency and title; from /markets answers, event_ticker and ticker. Never a price,
volume, result or settlement field. Prints, per category, the series listed and the series and markets that settled on Nov 10, and per
series in the four families (Sports, Politics, Entertainment, Mentions) the Nov 10 settled count.
Usage: python3 -I census_count.py <run folder>
"""
import collections
import gzip
import json
import os
import sys

FAMILIES = ("Sports", "Politics", "Entertainment", "Mentions")


def main(run):
    man = json.load(open(os.path.join(run, "manifest.json")))
    series, truncated_hours, bad = {}, [], 0
    settled = collections.Counter()
    events = collections.defaultdict(set)
    for row in man["rows"]:
        f = os.path.join(run, row["file"]) if row.get("file") else None
        if not f or not os.path.exists(f):
            continue
        try:
            body = json.loads(gzip.open(f).read())
        except Exception:
            bad += 1
            continue
        if not isinstance(body, dict):
            continue
        if row["path"] == "/series":
            for s in body.get("series") or []:
                if isinstance(s, dict) and s.get("ticker"):
                    series.setdefault(s["ticker"], {"category": s.get("category") or "", "frequency": s.get("frequency") or "", "title": (s.get("title") or "")[:80]})
        elif row["path"] == "/markets":
            if row.get("truncated") or (row.get("page") == 3 and body.get("cursor")):
                truncated_hours.append(row["id"])
            for m in body.get("markets") or []:
                if isinstance(m, dict) and m.get("event_ticker"):
                    sr = m["event_ticker"].split("-")[0]
                    settled[sr] += 1
                    events[sr].add(m["event_ticker"])
    cat = collections.defaultdict(lambda: {"series_listed": 0, "series_settled_1110": 0, "markets_settled_1110": 0, "events_settled_1110": 0})
    for t, s in series.items():
        cat[s["category"]]["series_listed"] += 1
    unknown = 0
    for sr, n in settled.items():
        c = series.get(sr, {}).get("category")
        if c is None:
            unknown += n
            c = "(series not in list)"
        cat[c]["series_settled_1110"] += 1
        cat[c]["markets_settled_1110"] += n
        cat[c]["events_settled_1110"] += len(events[sr])
    fam = {f: sorted(([sr, series[sr]["frequency"], series[sr]["title"], settled[sr], len(events[sr])] for sr in settled if series.get(sr, {}).get("category") == f), key=lambda x: -x[3]) for f in FAMILIES}
    print(json.dumps({"series_listed": len(series), "categories": dict(sorted(cat.items(), key=lambda kv: -kv[1]["markets_settled_1110"])),
                      "markets_of_series_not_in_list": unknown, "unreadable_files": bad, "hours_cut": truncated_hours,
                      "families": fam, "label": "counts only: no price, volume, result or settlement field read"}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
