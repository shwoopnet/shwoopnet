#!/usr/bin/env python3
"""Compares my ETHLATE1 build (Desk A's engine files through the adapter's cell selection) with the Testing Desk's second build on THEIR INVENTED fixture, rule by rule at 1e-9.
Usage: compare_second_build.py <engine dir> <their 97 lines file> <their fixture .json.gz>. Invented data only; no Kalshi data."""
import sys, os, gzip, json, math, time, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ethlate1_run as R
eng, theirs, fx = sys.argv[1:4]
K, N, S, D = R.import_engine(eng)
d = json.load(gzip.open(fx, "rt")); mk = []
for tk, m in d["markets"].items():
    cs = sorted((int(e), v[0], v[1]) for e, v in d["candles"].get(tk, {}).items())
    mk.append({"series": "KXETHD", "ticker": tk, "close": m["close_ts"], "result": m["result"], "candles": [(e, b, a, None, 0, 0) for e, b, a in cs]})
lines = open(theirs).read().splitlines(); hdr = lines[0].split()
last_day = int(hdr[hdr.index("last_search_day") + 1]); S.LAST_SEARCH["ETHD"] = time.strftime("%Y-%m-%d", time.gmtime(last_day * 86400))
series = "ETHD"; sm = [m for m in mk if S.phase(series, m["close"]) == "search"]; vm = [m for m in mk if S.phase(series, m["close"]) == "validate"]
cuts = {b: None for b in N.BUCKETS}
for b in N.BUCKETS:
    sp = [N.cents(c[2] - c[1]) for m in sm for c in m["candles"] if c[0] == m["close"] - b and 0 < c[1] < c[2] < 1]
    cuts[b] = N.spread_cuts(sp) if sp else None
sg, vg = D.groups(sm, cuts, None), D.groups(vm, cuts, None)
print("my header: SEARCH markets %d VALIDATE markets %d cuts(120) %s last_search %s" % (len(sm), len(vm), cuts[120], S.LAST_SEARCH["ETHD"])); print("their header:", lines[0][:200])
def mine(g, band, filt, x):
    items = g.get((120, band, "cheap", filt), [])
    if not items: return {"n": 0, "days": 0, "pf2": 0.0, "h1": 0.0, "h2": 0.0, "pf1": 0.0, "z": None, "events": 0}
    agg, _ = D.score_group(items, x); a2, a1 = agg[0.02], agg[0.01]
    return {"n": a2["n"], "days": a2["trade_days"], "pf2": a2["pf"], "h1": a2["half1"], "h2": a2["half2"], "pf1": a1["pf"], "z": a2["day_z"], "events": R.events_of(items)}
def parse(seg):
    t = seg.split(); out = {}
    for i in range(0, len(t), 2): out[t[i]] = t[i + 1]
    return out
fmap = {"none": None, "low": ("spread", "low"), "mid": ("spread", "mid"), "high": ("spread", "high")}
def eq(a, b):
    if b in ("None",): return a is None or (isinstance(a, float) and math.isnan(a))
    if b == "inf": return a == float("inf")
    if a is None or (isinstance(a, float) and (math.isnan(a) or math.isinf(a))): return False
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))
diffs = 0; total = 0; empty = 0
for ln in lines[1:]:
    head, s, v = [p.strip() for p in ln.split("|")[:1]] + [None, None]
    parts = ln.split(" | "); key = parts[0].split("|"); band = int(key[0][4:]); filt = key[1]; x = key[2].strip()
    S_, V_ = parse(parts[1][2:].strip()), parse(parts[2][2:].split(" search ")[0].strip())
    for ph, g, th in (("S", sg, S_), ("V", vg, V_)):
        mm = mine(g, band, fmap[filt], x)
        for f in ("n", "days", "events", "pf2", "h1", "h2", "pf1", "z"):
            total += 1
            ok = (int(th[f]) == mm[f]) if f in ("n", "days", "events") else eq(mm[f], th[f])
            if not ok and mm["n"] == 0 and f in ("pf2", "h1", "h2", "pf1", "z"): empty += 1; continue
            if not ok: diffs += 1; print("DIFF band%d %s %s %s %s mine %r theirs %s" % (band, filt, x, ph, f, mm[f], th[f])) 
print("fields compared %d, differing %d (plus %d empty-cell nan vs 0.0, display only)" % (total, diffs, empty))
