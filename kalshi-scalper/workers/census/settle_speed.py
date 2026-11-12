#!/usr/bin/env python3
"""Family census: settlement speed by family from the CENSUS_LISTING pull.

For every settled market read: seconds from close_time to settlement_ts. Grouped by the
families of family_day.py. Times only; no price and no result field is read.

Usage: python3 settle_speed.py <folder of the CENSUS_LISTING run> <out dir>
"""
import csv, glob, gzip, json, os, sys
from datetime import datetime
from family_day import family

def ts(x):
    try:
        return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None

def main(run, out):
    d = {}
    for f in sorted(glob.glob(os.path.join(run, "0*.json.gz"))):
        try:
            body = json.load(gzip.open(f, "rt"))
        except (OSError, ValueError):
            continue
        for m in (body.get("markets") or []) if isinstance(body, dict) else []:
            a, b = ts(m.get("close_time")), ts(m.get("settlement_ts"))
            if a is None or b is None:
                continue
            d.setdefault(family(m.get("ticker", "").split("-")[0]), []).append(b - a)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "settle_speed.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "markets", "median_minutes_close_to_settled", "p90_minutes"])
        for k, v in sorted(d.items(), key=lambda kv: -len(kv[1])):
            v.sort()
            row = [k, len(v), round(v[len(v) // 2] / 60, 1), round(v[int(len(v) * 0.9)] / 60, 1)]
            w.writerow(row); print(" | ".join(str(x) for x in row))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
