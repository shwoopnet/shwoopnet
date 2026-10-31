"""R6T posted-order and signal counts per Central day per market. INFORMATION ONLY. Reads coverage rows (counts, times, usability
fields) and book PRICE rows through r6tests.posted_by_window; never trades.csv.gz; never prints or uses a result, fill, rate or P/L.
python3 workers/R6T_counts.py   (run with PYTHONPATH=src)"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from scalper import r6tests as R
from scalper.mm1 import central_date

ws = R.windows()
pw = R.posted_by_window(ws)
day = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0, 0, 0]))   # rec, usable_m5, usable_q, posted_m5, signals, ok_polls_share_n
for (c, ser), (r, row) in ws.items():
    d = central_date(c)
    x = day[d][ser]
    x[0] += 1
    x[1] += bool(R.usable("maker5", c, row))
    x[2] += bool(R.usable("l1q1", c, row))
    a, b = pw.get((c, ser), (False, False))
    x[3] += a
    x[4] += b
names = {s: s[2:-3] for s in R.SERIES}
print("day | " + " | ".join(f"{names[s]} rec/m5post/l1sig" for s in R.SERIES) + " | day rec, m5 posted, l1 signals")
tot = defaultdict(lambda: [0, 0, 0, 0, 0])
for d in sorted(day):
    cells, t = [], [0, 0, 0, 0, 0]
    for s in R.SERIES:
        x = day[d][s]
        cells.append(f"{x[0]}/{x[3]}/{x[4]}")
        for i, j in enumerate((0, 1, 2, 3, 4)):
            t[i] += x[j]; tot[s][i] += x[j]
    print(f"{d} | " + " | ".join(cells) + f" | {t[0]}, {t[3]}, {t[4]}")
print("TOTALS per market: rec, usable_m5, usable_l1q1, m5_posted, l1_signals")
for s in R.SERIES:
    print(names[s], tot[s])
g = [sum(tot[s][i] for s in R.SERIES) for i in range(5)]
print("ALL", g)
firsts = sorted(c for c, _ in ws)
print("first close", datetime.fromtimestamp(firsts[0], timezone.utc), "last close", datetime.fromtimestamp(firsts[-1], timezone.utc))
print("files/runs", R.runs()[1], len(R.runs()[0]))
