#!/usr/bin/env python3
"""CROWDLEG and NOTAKER feasibility: counts only (Idea Desk C, Nov 14, 2026, the Head of R&D's go at 02:31Z; hand case HAND_CASE.md committed first at a06cfe15).

Reads combo-data quotes files (combo/DATE/HHMM/quotes.csv.gz) and counts, per UTC day, the distinct combo tickers that are listed, two-sided (rule 18: 0 < yes_bid < yes_ask < 1,
1e-9), and qualifying (two-sided, NO ask = 1 - yes_bid in [0.20, 0.50], spread = yes_ask - yes_bid <= 0.04), and how many qualifying ones carry leg_tickers.
Only the columns ticker, yes_bid, yes_ask and leg_tickers are read. No result, volume, size, last price or other price is read.
Guard: a folder dated on or after HELDOUT_FROM (S3's held-out window may start there, rule 17) and any path part starting HELDOUT are refused (listed, never opened).
Verdict (fixed before the run): the average of qualifying distinct combos per complete UTC day (>= --complete-polls polls, default 40) under 5 means CLOSE, 5 or more means FIX TO OWNER.

Usage: python3 -I feasibility_count.py <folder that holds combo/> [--complete-polls N]"""
import csv
import gzip
import json
import os
import sys

HELDOUT_FROM = "2026-11-26"
EPS = 1e-9
BAND = (0.20, 0.50)
MAX_SPREAD = 0.04
THRESHOLD = 5.0


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def two_sided(yb, ya):
    return yb is not None and ya is not None and yb > EPS and ya < 1 - EPS and ya - yb > EPS


def qualifies(yb, ya):
    if not two_sided(yb, ya):
        return False
    no_ask, spread = 1 - yb, ya - yb
    return BAND[0] - EPS <= no_ask <= BAND[1] + EPS and spread <= MAX_SPREAD + EPS


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    root, complete = argv[0], 40
    if "--complete-polls" in argv:
        complete = int(argv[argv.index("--complete-polls") + 1])
    base = os.path.join(root, "combo")
    days, refused = {}, []
    for day in sorted(os.listdir(base)):
        dpath = os.path.join(base, day)
        if not os.path.isdir(dpath):
            continue
        if day >= HELDOUT_FROM or day.upper().startswith("HELDOUT"):
            refused.append(day)
            continue
        d = days.setdefault(day, {"polls": 0, "rows": 0, "listed": set(), "two_sided": set(), "qualifying": set(), "qual_legs": set()})
        for poll in sorted(os.listdir(dpath)):
            if poll.upper().startswith("HELDOUT"):
                refused.append(day + "/" + poll)
                continue
            f = os.path.join(dpath, poll, "quotes.csv.gz")
            if not os.path.isfile(f):
                continue
            d["polls"] += 1
            with gzip.open(f, "rt", newline="") as fh:
                for r in csv.DictReader(fh):
                    t = r.get("ticker") or ""
                    if not t:
                        continue
                    d["rows"] += 1
                    d["listed"].add(t)
                    yb, ya = num(r.get("yes_bid")), num(r.get("yes_ask"))
                    if two_sided(yb, ya):
                        d["two_sided"].add(t)
                    if qualifies(yb, ya):
                        d["qualifying"].add(t)
                        if (r.get("leg_tickers") or "").strip():
                            d["qual_legs"].add(t)
    out, full = {}, []
    for day, d in days.items():
        out[day] = {"polls": d["polls"], "rows": d["rows"], "listed_distinct": len(d["listed"]), "two_sided_distinct": len(d["two_sided"]),
                    "qualifying_distinct": len(d["qualifying"]), "qualifying_with_legs": len(d["qual_legs"]), "complete_day": d["polls"] >= complete}
        if d["polls"] >= complete:
            full.append(len(d["qualifying"]))
    avg = (sum(full) / len(full)) if full else None
    verdict = "no complete day" if avg is None else ("CLOSE: no evidence, combos cannot be priced" if avg < THRESHOLD else "FIX TO OWNER")
    print(json.dumps({"days": out, "refused_unread": refused, "complete_days": len(full), "avg_qualifying_per_complete_day": avg, "threshold": THRESHOLD,
                      "verdict": verdict, "label": "counts only; no result, volume or price beyond the two-sided flag and the band"}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
