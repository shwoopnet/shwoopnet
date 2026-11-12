#!/usr/bin/env python3
"""Break-in-play sweep of the Nov 10, 2026 census listing (zero requests, counts and times only).

Finds every series whose markets CLOSE MID-EVENT: a market that closed 10 minutes or more
before the last-closing market that shares its event key (the second part of the ticker).
Such a market can be the STATE for a break-in-play rule (a set, map, half, period, inning,
frame or leg that Kalshi itself settles while the event goes on).

It reads tickers, close times and volume. It reads no price and no result.

Usage: python3 sweep_listing.py <folder of the CENSUS_LISTING run> <out dir>
"""
import csv, glob, gzip, json, os, sys
from collections import Counter, defaultdict
from datetime import datetime

LEAD_MIN = 10


def ts(x):
    try:
        return datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def main(run, out):
    groups = defaultdict(list)                       # event key -> [(series, ticker, close, volume)]
    for f in sorted(glob.glob(os.path.join(run, "0*.json.gz"))):
        try:
            body = json.load(gzip.open(f, "rt"))
        except (OSError, ValueError):
            continue
        for m in (body.get("markets") or []) if isinstance(body, dict) else []:
            tk, c = m.get("ticker", ""), ts(m.get("close_time"))
            parts = tk.split("-")
            if len(parts) < 3 or c is None:
                continue
            try:
                v = float(m.get("volume_fp", m.get("volume", 0)) or 0)
            except (TypeError, ValueError):
                v = 0.0
            groups[parts[1]].append((parts[0], tk, c, v))
    agg = defaultdict(lambda: {"keys": set(), "lead": [], "vol": [], "markets": 0, "parents": Counter(), "subs": Counter()})
    import re
    for key, ms in groups.items():
        if len({s for s, _, _, _ in ms}) < 2 or re.fullmatch(r"\d{2}[A-Z]{3}\d{2}\d{0,4}", key):
            continue                                 # a key that is only a date or a date and clock time groups unrelated markets
        last = max(c for _, _, c, _ in ms)
        last_series = Counter(s for s, _, c, _ in ms if last - c < 120)
        for s, tk, c, v in ms:
            if last - c >= LEAD_MIN * 60:
                a = agg[s]
                a["keys"].add(key); a["lead"].append((last - c) / 60); a["vol"].append(v); a["markets"] += 1
                for p in last_series:
                    a["parents"][p] += 1
                parts = tk.split("-")
                if len(parts) >= 4:
                    a["subs"][parts[2]] += 1
    os.makedirs(out, exist_ok=True)
    rows = []
    for s, a in agg.items():
        lead, vol = sorted(a["lead"]), sorted(a["vol"])
        rows.append([s, len(a["keys"]), a["markets"], round(lead[len(lead) // 2]), round(lead[0]), round(lead[-1]), round(vol[len(vol) // 2]),
                     " ".join(p for p, _ in a["parents"].most_common(3)), " ".join(f"{k}:{n}" for k, n in a["subs"].most_common(6))])
    rows.sort(key=lambda r: -r[1])
    with open(os.path.join(out, "mid_event_series.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["state_series", "events_nov10", "markets", "median_minutes_before_last_close", "min", "max", "median_contracts_a_market", "last_closing_siblings", "sub_event_labels"])
        w.writerows(rows)
    for r in rows:
        print(" | ".join(str(x) for x in r))
    print("series with a mid-event close:", len(rows))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
