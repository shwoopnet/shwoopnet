#!/usr/bin/env python3
"""OIFIELD_CHECK reader (Forensics desk, Nov 14, 2026). Reads ONLY market_ticker and open_interest_fp of each candle of the one landed answer; no price, bid, ask, volume, trade or result field is touched.
Per ticker: candles, open_interest_fp present (key there), populated (a finite number), nonzero, and the number of distinct values (a count, never a value). usage: python3 -I oifield_read.py <run folder>"""
import sys, os, json, gzip, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from listed_runs_guard import refuse_listed
folder = sys.argv[1]
refuse_listed(folder)
man = json.load(open(os.path.join(folder, "manifest.json")))
per = {}
for r in man["rows"]:
    body = json.load(gzip.open(os.path.join(folder, r["file"]), "rt"))
    for m in body.get("markets") or []:
        d = per.setdefault(m.get("market_ticker"), {"candles": 0, "present": 0, "populated": 0, "nonzero": 0, "vals": set()})
        for c in m.get("candlesticks") or []:
            d["candles"] += 1
            if "open_interest_fp" in c: d["present"] += 1
            try: v = float(c.get("open_interest_fp"))
            except (TypeError, ValueError): continue
            if math.isfinite(v):
                d["populated"] += 1; d["vals"].add(v)
                if v != 0: d["nonzero"] += 1
print("tickers in the answer:", len(per))
for t in sorted(per, key=str):
    d = per[t]; print("%-30s candles %2d present %2d populated %2d nonzero %2d distinct values %d" % (t, d["candles"], d["present"], d["populated"], d["nonzero"], len(d["vals"])))
