#!/usr/bin/env python3
"""Compare the second build (shadow_rank_b2.py, committed first at 1501e55d) with Desk A's rescore table and shadow list, AFTER the second build was committed. usage: python3 -I compare_b2.py <barlist> <extract> <rescore.json> <shadow_list.json>"""
import sys, json, sqlite3, calendar
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import shadow_rank_b2 as X
bl, ex, rs, sl = sys.argv[1:5]
L = json.load(open(bl))["validate_bar_list"]; db = sqlite3.connect("file:%s?mode=ro" % ex, uri=True); series = sorted({r["series"] for r in L}); ms = {}
for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market where series in (%s)" % ",".join("?" * len(series)), series): ms[tk] = X.Mkt(tk, ser, close, res, {})
for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
    if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
markets = sorted(ms.values(), key=lambda m: (m.close, m.tk))
ls = {s: calendar.timegm(tuple(int(x) for x in X.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in series}; phase_of = lambda m: "S" if m.close < ls[m.ser] else "V"; cache = {}
def cuts_for(ser, bucket):
    k = (ser, bucket)
    if k not in cache: cache[k] = X.terciles([m for m in markets if m.ser == ser and phase_of(m) == "S"], ser, bucket)
    return cache[k]
vd, sd = {}, {}
for s in series:
    v = [m.close for m in markets if m.ser == s and phase_of(m) == "V"]; sr = [m.close for m in markets if m.ser == s and phase_of(m) == "S"]; vd[s] = (max(v) - ls[s]) / 86400; sd[s] = (max(sr) - min(sr)) / 86400 + 1
R = json.load(open(rs))["rows"]; worst = collections = {}; names = {"signals_per_day": "spd", "search_signals_per_day": "sspd", "edge_1c_cents_per_contract": "e1", "edge_2c_cents_per_contract": "e2", "dollars_week_5c_1c": "d1", "dollars_week_5c_2c": "d2"}
mx = {k: 0.0 for k in names}; bad = []; rows = []
for i, (r, q) in enumerate(zip(L, R)):
    assert (r["series"], r["bucket"], r["band"], r["side"], r["exit"], r["filter"]) == (q["series"], q["bucket"], q["band"], q["side"], q["exit"], q["filter"]), i
    rule = dict(r); rule["phase"] = "V"; rule["filter"] = tuple(r["filter"]) if r["filter"] else None
    x1 = [x[2] for x in X.run_rule(markets, rule, phase_of, cuts_for, 0.01)]; x2 = [x[2] for x in X.run_rule(markets, rule, phase_of, cuts_for, 0.02)]; n = len(x1)
    sr = dict(rule); sr["phase"] = "S"; sn = len(X.run_rule(markets, sr, phase_of, cuts_for, 0.01))
    spd = n / vd[r["series"]]; e1 = sum(x1) / (n * 10) * 100; e2 = sum(x2) / (n * 10) * 100
    mine = {"signals_per_day": spd, "search_signals_per_day": sn / sd[r["series"]], "edge_1c_cents_per_contract": e1, "edge_2c_cents_per_contract": e2, "dollars_week_5c_1c": spd * e1 / 100 * 35, "dollars_week_5c_2c": spd * e2 / 100 * 35}
    for k, v in mine.items():
        d = abs(v - q[k]); mx[k] = max(mx[k], d)
        if d >= 1e-9: bad.append((i, k, v, q[k]))
    if n != q["n"] or sn != q["search_n"]: bad.append((i, "n or search_n", n, sn, q["n"], q["search_n"]))
print("rows", len(L), "max abs difference per field:", {k: "%.3e" % v for k, v in mx.items()}, "| fields at or above 1e-9:", len(bad)); [print(b) for b in bad[:10]]
S = json.load(open(sl))["specs"]; print("shadow list picks", len(S))
