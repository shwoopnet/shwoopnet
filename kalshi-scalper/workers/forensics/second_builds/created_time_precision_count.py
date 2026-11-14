#!/usr/bin/env python3
"""ONE aggregate (the Head's order, 2026-11-14 00:20Z): on the R6 pin, how many tape trades have a created_time with nonzero digits beyond the millisecond. Reads only the created_time and ticker columns
of each trades.csv.gz; prints counts, no row, no price, no side, no size. Gold and Bitcoin are the two markets DEPTH1 scores; all series are counted beside them.
usage: python3 -I created_time_precision_count.py <book15r6 folder>"""
import sys, os, csv, gzip, re, collections
root = sys.argv[1]
tot = collections.Counter()
for d, _, fs in os.walk(root):
    if "trades.csv.gz" not in fs: continue
    r = csv.reader(gzip.open(os.path.join(d, "trades.csv.gz"), "rt")); h = next(r); ic, it = h.index("created_time"), h.index("ticker")
    for row in r:
        grp = "gold_bitcoin" if row[it].startswith(("KXGOLD15M", "KXBTC15M")) else "other_series"
        m = re.search(r"\.(\d+)", row[ic]); frac = m.group(1) if m else ""
        k = "no_fraction" if not frac else "beyond_ms_nonzero" if frac[3:].strip("0") else "beyond_ms_all_zero" if len(frac) > 3 else "ms_or_coarser"
        tot[(grp, k)] += 1; tot[(grp, "all")] += 1; tot[(grp, "max_fraction_digits")] = max(tot[(grp, "max_fraction_digits")], len(frac))
for grp in ("gold_bitcoin", "other_series"):
    print(grp, {k: tot[(grp, k)] for k in ("all", "no_fraction", "ms_or_coarser", "beyond_ms_all_zero", "beyond_ms_nonzero", "max_fraction_digits")})
