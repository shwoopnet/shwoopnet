"""Descriptive only: 30 s file against the 1 minute candle quotes (same venue, two sources). No returns."""
import sys, gzip, csv, statistics as st, collections, datetime as D
S = sys.argv[1]
c = {}
for r in csv.DictReader(gzip.open(S + "/candles_1m.csv.gz", "rt")):
    if r["ok"] == "1": c[(r["ticker"], int(r["ts"]))] = (float(r["bid_c"]), float(r["ask_c"]))
d, n, miss = [], 0, 0
for r in csv.DictReader(gzip.open(S + "/close30.csv.gz", "rt")):
    if r["asset_class"] != "Equities" or r["status"] != "active": continue
    t = int(D.datetime.strptime(r["ts_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=D.timezone.utc).timestamp())
    if t % 60 < 50: continue                    # the sample taken in the last 10 s of a minute, compared with that minute's candle close
    q = c.get((r["ticker"], t - t % 60 + 60)); n += 1
    if q is None: miss += 1; continue
    b, a = float(r["bid"]), float(r["ask"])
    if not (0 < a < 1e9): continue
    d.append(abs(((a + b) / 2) / ((q[0] + q[1]) / 2) - 1) * 1e4)
print("samples at :5x", n, "no candle", miss, "compared", len(d), "|mid_30s / mid_candle - 1| bp: median %.2f p90 %.2f max %.2f" % (st.median(d), sorted(d)[int(.9 * len(d))], max(d)))
