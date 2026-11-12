"""NC15DEPTH1 counts only: book columns at the look. Reads NO result, trades or coverage outcome."""
import sys, glob, gzip, io, statistics
import pandas as pd, numpy as np
from email.utils import parsedate_to_datetime
root = sys.argv[1]
SC = ["KXSILVER15M","KXCOPPER15M","KXWTI15M","KXEURUSD15M","KXGBPUSD15M","KXUSDJPY15M","KXHYPE15M","KXBNB15M","KXAUDUSD15M","KXUSDCAD15M","KXNATGAS15M"]
rows = {s: dict(windows=0, look=0, cell=0, band=0) for s in SC}
byday = {}
for f in sorted(glob.glob(root + "/nc15/*/*/book.csv.gz")):
    d = pd.read_csv(f)
    if d.empty: continue
    h = d["server_date_header"].dropna()
    offs = [parsedate_to_datetime(x).timestamp() + 0.5 - r/1000 for x, r in zip(h, d.loc[h.index, "t_recv_ms"])]
    if not offs: continue
    off = statistics.median(offs)
    d["t"] = d["t_recv_ms"]/1000 + off
    d["close"] = pd.to_datetime(d["close_time"], utc=True).astype("int64")//10**9 if False else pd.to_datetime(d["close_time"], utc=True).map(lambda x: x.timestamp())
    for (tk, ser, cl), g in d.groupby(["ticker", "series", "close"]):
        if ser not in rows: continue
        rows[ser]["windows"] += 1
        g = g.sort_values("t")
        L = cl - 600
        a = g[(g.t <= L) & (g.t >= L - 10)]
        if a.empty: continue
        rows[ser]["look"] += 1
        p = a.iloc[-1]
        ys = sum(p[f"yes_bid_sz_{i}"] for i in range(1,6) if pd.notna(p[f"yes_bid_sz_{i}"]))
        ns = sum(p[f"no_bid_sz_{i}"] for i in range(1,6) if pd.notna(p[f"no_bid_sz_{i}"]))
        if ys + ns <= 0: continue
        imb = (ys - ns)/(ys + ns)
        if abs(imb) < 0.5: continue
        rows[ser]["cell"] += 1
        fp = g[(g.t >= L + 1) & (g.t <= L + 21)]
        if fp.empty: continue
        q = fp.iloc[0]
        ask = (1 - q["no_bid_px_1"]) if imb > 0 else (1 - q["yes_bid_px_1"])
        sz = q["no_bid_sz_1"] if imb > 0 else q["yes_bid_sz_1"]
        if pd.notna(ask) and 0.10 <= ask <= 0.90 and sz >= 1:
            rows[ser]["band"] += 1
            day = pd.Timestamp(cl, unit="s", tz="UTC").tz_convert("America/Chicago").date()
            byday[day] = byday.get(day, 0) + 1
tot = dict(windows=0, look=0, cell=0, band=0)
for s, r in rows.items():
    print(f"{s:14s} windows {r['windows']:5d} look {r['look']:5d} cell {r['cell']:5d} in band {r['band']:5d}")
    for k in tot: tot[k] += r[k]
print("TOTAL", tot)
print("in-band by Central day:", {str(k): v for k, v in sorted(byday.items())})
