"""Descriptive only: no returns, no test outcome. Quote counts, spreads by New York hour, funding table, 30 s file staleness."""
import sys, os, gzip, csv, json, statistics as st, collections, datetime as D
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York"); S = sys.argv[1]
c = collections.defaultdict(list); first = {}; last = {}; days = collections.defaultdict(set)
for r in csv.DictReader(gzip.open(S + "/candles_1m.csv.gz", "rt")):
    if r["ok"] != "1" or not r["ticker"].startswith("KX") or r["ticker"] in ("KXUS500PERP", "KXUSTECH100PERP"): continue
    ts = int(r["ts"]); b, a = float(r["bid_c"]), float(r["ask_c"]); e = D.datetime.fromtimestamp(ts, NY)
    c[e.hour].append((a - b) / ((a + b) / 2) * 1e4); first[r["ticker"]] = min(first.get(r["ticker"], ts), ts); last[r["ticker"]] = max(last.get(r["ticker"], ts), ts)
    days[e.strftime("%a %m-%d")].add(e.hour)
print("first candle", D.datetime.fromtimestamp(min(first.values()), D.timezone.utc), "last", D.datetime.fromtimestamp(max(last.values()), D.timezone.utc))
print("hours present by day:", {k: (min(v), max(v), len(v)) for k, v in sorted(days.items())})
print("ET hour: n minutes, median spread bp, p90")
for h in sorted(c): v = sorted(c[h]); print("  %02d  n=%6d  med %.1f  p90 %.1f" % (h, len(v), st.median(v), v[int(.9 * len(v))]))
fr = json.load(open(S + "/funding.json")); eq = {k: v for k, v in fr.items() if k not in ("KXUS500PERP", "KXUSTECH100PERP")}
rates = [r["funding_rate"] * 1e4 for v in eq.values() for r in v]; times = sorted({r["funding_time"] for v in eq.values() for r in v})
print("funding times", times, "n", len(rates), "share zero %.2f share positive %.2f share negative %.2f" % tuple(sum(f(x) for x in rates) / len(rates) for f in (lambda x: x == 0, lambda x: x > 0, lambda x: x < 0)))
print("funding bp/day: mean %.2f median %.2f max %.2f min %.2f (cap 200 bp)" % (st.mean(rates), st.median(rates), max(rates), min(rates)))
by = collections.defaultdict(list)
for r in (r for v in eq.values() for r in v): by[r["funding_time"][:10]].append(r["funding_rate"] * 1e4)
for k in sorted(by): print("  ", k, "n", len(by[k]), "mean %.2f" % st.mean(by[k]), "share>0 %.2f" % (sum(x > 0 for x in by[k]) / len(by[k])))
# 30 second file: same quote repeated between consecutive samples (staleness proxy), and sizes
d = collections.defaultdict(list)
for r in csv.DictReader(gzip.open(S + "/close30.csv.gz", "rt")):
    if r["asset_class"] == "Equities" and r["status"] == "active": d[r["ticker"]].append((r["bid"], r["ask"]))
same = [sum(v[i] == v[i + 1] for i in range(len(v) - 1)) / (len(v) - 1) for v in d.values()]
print("30s file: equity tickers", len(d), "share of consecutive samples with unchanged bid and ask: median %.2f min %.2f max %.2f" % (st.median(same), min(same), max(same)))
