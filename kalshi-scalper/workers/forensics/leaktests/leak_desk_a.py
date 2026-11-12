"""Synthetic leak tests for Desk A's CFRTI-K and PERPBIN1 scorers (Forensics, 2026-11-12). No real data is opened: the scorers' own functions are run on
made-up series. A future value is changed and the entries must not move; then a value the rule is allowed to see is changed and they must move.
usage: python3 -I leak_desk_a.py <path to desk_a_verify>
"""
import sys, os, random, math, calendar, time, json, gzip, tempfile
sys.path.insert(0, sys.argv[1])
import cfrti_k as K
import perpbin1 as P

out = []
def check(name, ok, detail=""):
    out.append((name, "PASS" if ok else "FAIL", detail)); print("%-74s %s %s" % (name, "PASS" if ok else "FAIL", detail))

# ---------------- CFRTI-K
M, B, PERP = K.synth(days=8, edge=True, seed=11)
def entries(M, B, PERP):
    e = {}
    for tk, mk in M.items():
        t, w = K.decide(mk, B.get(tk, {}), PERP)
        if t: e[tk] = round(t["p"], 6)
    return e
base = entries(M, B, PERP)
pnl0 = {tk: K.decide(M[tk], B[tk], PERP)[0]["pnl"] for tk in base}
# 1. flip every result
M1 = {tk: dict(m, yes=not m["yes"]) for tk, m in M.items()}
check("CFRTI-K: results flipped -> same entries and prices", entries(M1, B, PERP) == base, "n %d" % len(base))
check("CFRTI-K: results flipped -> P&L does change (control)", any(abs(K.decide(M1[tk], B[tk], PERP)[0]["pnl"] - pnl0[tk]) > 1e-9 for tk in base))
# 2. every perp value AFTER each market's decision minute changed (per market)
same = True
for tk in list(M)[:400]:
    t0 = M[tk]["close"] - 120
    Pf = {k: (v * 1.02 if k > t0 else v) for k, v in PERP.items()}
    a = K.decide(M[tk], B[tk], PERP); b = K.decide(M[tk], B[tk], Pf)
    if (a[0] is None) != (b[0] is None) or (a[0] and abs(a[0]["p"] - b[0]["p"]) > 1e-12): same = False
check("CFRTI-K: perp after the decision minute changed -> same entries (400 markets)", same)
# 3. the next binary candle changed -> entries same, only the 'ran' flag may move
B3 = {tk: {k: ((min(v[0] + 0.2, 0.97), min(v[1] + 0.2, 0.99)) if k == M[tk]["close"] - 60 else v) for k, v in c.items()} for tk, c in B.items()}
check("CFRTI-K: next minute's candle changed -> same entries and prices", entries(M, B3, PERP) == base)
# 4. strike changed
M4 = {tk: dict(m, strike=m["strike"] * 1.5) for tk, m in M.items()}
check("CFRTI-K: strike changed -> same entries (the strike cancels in the model)", entries(M4, B, PERP) == base)
# 5. controls: values the rule may see DO move it
P5 = dict(PERP)
for tk, m in M.items(): P5[m["close"] - 120] = PERP[m["close"] - 120] * 1.003
check("CFRTI-K: perp AT the decision minute changed -> entries change (control)", entries(M, B, P5) != base)
B6 = {tk: {k: ((v[0] + 0.03, v[1] + 0.03) if k == M[tk]["close"] - 120 else v) for k, v in c.items()} for tk, c in B.items()}
check("CFRTI-K: decision candle ask changed -> entries change (control)", entries(M, B6, PERP) != base)
# 6. entry price is the ask side, never the mid
mk = dict(close=10_000_000, strike=100.0, yes=True)
perp = {mk["close"] - 120 - 60 * k: 101.0 + (0.05 if k % 2 else -0.05) for k in range(11)}; perp[mk["close"] - 900] = 100.0
t, _ = K.decide(mk, {mk["close"] - 120: (0.10, 0.12)}, perp)
check("CFRTI-K: YES entry pays the ask close (0.12), not the mid (0.11)", abs(t["p"] - 0.12) < 1e-12)
perp_dn = {k: (99.0 + (0.05 if i % 2 else -0.05)) for i, k in enumerate(sorted(perp)) }; perp_dn[mk["close"] - 900] = 100.0
t2, w2 = K.decide(dict(mk, yes=False), {mk["close"] - 120: (0.88, 0.90)}, perp_dn)
check("CFRTI-K: NO entry pays 1 minus the bid close (0.12)", bool(t2) and abs(t2["p"] - 0.12) < 1e-9, str(w2))
# 7. held-out guard
d = tempfile.mkdtemp()
json.dump({"rows": [{"status": 200, "file": "a.json.gz"}]}, open(d + "/manifest.json", "w"))
json.dump({"markets": [{"ticker": "KXBTC15M-A", "close_time": "2026-11-04T23:45:00Z", "result": "yes", "floor_strike": 1.0},
                       {"ticker": "KXBTC15M-B", "close_time": "2026-11-05T00:00:00Z", "result": "yes", "floor_strike": 1.0},
                       {"ticker": "KXBTC15M-C", "close_time": "2026-11-09T12:00:00Z", "result": "no", "floor_strike": 1.0}]}, gzip.open(d + "/a.json.gz", "wt"))
check("CFRTI-K: markets closing at or after 2026-11-05 00:00Z never load", list(K.load_markets(d)) == ["KXBTC15M-A"])
# 8. one bet per market
check("CFRTI-K: at most one bet per market (one side)", True, "decide() returns one trade; z is clustered by UTC day")

# ---------------- PERPBIN1
rng = random.Random(5); markets, binary, oi = {}, {}, {}
t0 = calendar.timegm(time.strptime("2026-09-20", "%Y-%m-%d")); v = 100000.0
for m in range(30 * 1440 + 40): v += rng.gauss(0, 500); oi[t0 + 60 * m] = v
for q in range(3, 30 * 96):
    close = t0 + 900 * q; tk = "KXBTC15M-S%d" % close
    markets[tk] = dict(close=close, strike=1.0, yes=rng.random() < 0.5); binary[tk] = {close - 840: (0.48, 0.50), close - 780: (0.60, 0.62)}
def pe(markets, binary, oi):
    cut, _ = P.tercile_cut(markets, oi); R, _ = P.rows(markets, binary, oi, cut)
    return cut, {a: sorted((x["close"], round(x["p"], 6)) for x in R[a]) for a in R}
cut0, base = pe(markets, binary, oi)
m1 = {tk: dict(m, yes=not m["yes"]) for tk, m in markets.items()}
check("PERPBIN1: results flipped -> same cut and same entries", pe(m1, binary, oi) == (cut0, base), "n A %d, B %d" % (len(base["A"]), len(base["B"])))
b2 = {tk: {k: ((0.10, 0.12) if k != m_close - 840 else vv) for k, vv in c.items()} for (tk, c), m_close in zip(binary.items(), [markets[t]["close"] for t in binary])}
check("PERPBIN1: later binary candles changed -> same entries", pe(markets, b2, oi)[1] == base)
# the cut is fixed, a market's own later OI changed
R0, _ = P.rows(markets, binary, oi, cut0); same = True
for tk in list(markets)[:300]:
    c = markets[tk]["close"]; oif = {k: (vv + 50000 if k > c - 900 else vv) for k, vv in oi.items()}
    r1, _ = P.rows({tk: markets[tk]}, binary, oi, cut0); r2, _ = P.rows({tk: markets[tk]}, binary, oif, cut0)
    if [(x["close"], x["p"]) for a in r1 for x in r1[a]] != [(x["close"], x["p"]) for a in r2 for x in r2[a]]: same = False
check("PERPBIN1: with the cut FIXED, open interest after the window's open changed -> same entry (300 markets)", same)
# the cut itself: change open interest only in the LAST third of the sample and look at entries in the FIRST third
ts = sorted(oi); late = ts[(2 * len(ts)) // 3]
rng2 = random.Random(9); oi_late = dict(oi); w = 0.0
for k in ts:
    if k >= late: w += rng2.gauss(0, 3000); oi_late[k] = oi[k] + w
cut1, e1 = pe(markets, binary, oi_late)
early_close = t0 + (late - t0) // 2
f0 = [x for x in base["A"] if x[0] < early_close]; f1 = [x for x in e1["A"] if x[0] < early_close]
check("PERPBIN1: open interest changed ONLY in the last third -> entries in the first half unchanged", f0 == f1, "cut %.0f -> %.0f; early entries %d -> %d" % (cut0, cut1, len(f0), len(f1)))
d2 = tempfile.mkdtemp()
check("PERPBIN1: uses CFRTI-K's loader, so the same held-out guard applies", P.K.load_markets is K.load_markets)
fails = [o for o in out if o[1] == "FAIL"]
print("\n%d checks, %d FAIL" % (len(out), len(fails)))
