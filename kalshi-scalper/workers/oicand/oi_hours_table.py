#!/usr/bin/env python3
"""Makes the hours table for oi_nightly_job.py from the answers of the OICAND_LISTS run. Usage: oi_hours_table.py <lists run folder> <out json>.
Reads ONLY ticker and close_time. For each of the 12 listed series, a (weekday, HH:MM) close (weekday of the close's UTC date, Monday = 0) is kept if it was seen on at least MINDAYS
distinct dates (default 2, OICAND_MINDAYS). KXETH15M (not in the lists run, a 24 hour crypto series) gets every close of every weekday. Standard library only."""
import gzip, json, os, sys
from collections import defaultdict
from datetime import datetime

MINDAYS = int(os.environ.get("OICAND_MINDAYS", "2"))

def main():
    man = json.load(open(os.path.join(sys.argv[1], "manifest.json")))
    seen = defaultdict(set)
    for row in man.get("rows", []):
        if row.get("status") != 200 or not str(row.get("id", "")).startswith("settled_"):
            continue
        body = json.load(gzip.open(os.path.join(sys.argv[1], row["file"]), "rt"))
        for m in (body.get("markets", []) if isinstance(body, dict) else []):
            ct = m["close_time"]
            seen[(m["ticker"].split("-")[0], datetime.strptime(ct[:10], "%Y-%m-%d").weekday(), ct[11:16])].add(ct[:10])
    t = defaultdict(lambda: defaultdict(list))
    for (s, wd, hm), days in sorted(seen.items()):
        if len(days) >= MINDAYS:
            t[s][str(wd)].append(hm)
    allc = ["%02d:%02d" % (h, m) for h in range(24) for m in (0, 15, 30, 45)]
    t["KXETH15M"] = {str(w): allc for w in range(7)}
    json.dump(t, open(sys.argv[2], "w"), indent=1, sort_keys=True)
    print("series %d | (series, weekday, close) entries %d | MINDAYS %d" % (len(t), sum(len(v) for s in t.values() for v in s.values()), MINDAYS))

if __name__ == "__main__":
    main()
