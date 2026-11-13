#!/usr/bin/env python3
"""Two TIMES-ONLY counts (Desk B, Nov 13, 2026, ordered by the Head of R&D). Reads tickers, event tickers, open and close times; no price, size, result or volume.
  time_counts.py strikes <lists run folder>      late-added strikes in a landed lists run
  time_counts.py drift <git ref of pol-data>     close time drift between polls in pol-data quotes
"""
import csv, gzip, io, json, os, subprocess, sys
from datetime import datetime, timezone

def ts(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

def strikes(run):
    man = json.load(open(os.path.join(run, "manifest.json")))
    ms = []
    for row in man.get("rows", []):
        if row.get("status") != 200 or not str(row.get("id", "")).startswith("settled_"):
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []):
            ms.append((m["ticker"].split("-")[0], m.get("event_ticker"), ts(m["open_time"]), ts(m["close_time"])))
    ev = {}
    for s, e, o, c in ms:
        ev.setdefault((s, e), []).append(o)
    days = (max(m[3] for m in ms) - min(m[3] for m in ms)) / 86400
    print("markets %d, events %d, span %.1f days (times only)" % (len(ms), len(ev), days))
    for s in sorted({k[0] for k in ev}):
        es = {k: v for k, v in ev.items() if k[0] == s}
        late = sum(1 for v in es.values() for o in v if o > min(v) + 60)
        lev = sum(1 for v in es.values() if any(o > min(v) + 60 for o in v))
        print("%s: events %d, markets %d, late-added markets (open more than 60 s after the event's first open) %d, events with any %d" % (s, len(es), sum(len(v) for v in es.values()), late, lev))
    late = sum(1 for v in ev.values() for o in v if o > min(v) + 60)
    print("ALL: late-added markets %d of %d; per 30 days at this rate about %.0f" % (late, len(ms), late / days * 30))

def drift(ref):
    files = [f for f in subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref], text=True).split() if f.endswith("quotes.csv.gz")]
    seen, polls = {}, 0
    t0 = t1 = None
    for f in sorted(files):
        raw = subprocess.check_output(["git", "show", "%s:%s" % (ref, f)])
        for r in csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw)), "utf-8")):
            seen.setdefault(r["ticker"], set()).add(r["close_time"])
            d = r["server_date_header"]
            t0 = t0 or d; t1 = d
        polls += 1
    drifted = {t: v for t, v in seen.items() if len(v) > 1}
    print("quote files %d, tickers %d, first and last server dates %s, %s (close times only)" % (polls, len(seen), t0, t1))
    print("tickers whose close time differs between polls: %d" % len(drifted))
    for t, v in list(drifted.items())[:10]:
        print("  ", t.split("-")[0], sorted(v))

if __name__ == "__main__":
    {"strikes": strikes, "drift": drift}[sys.argv[1]](sys.argv[2])
