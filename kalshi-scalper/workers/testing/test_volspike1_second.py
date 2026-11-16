import math, os, sqlite3, tempfile, volspike1_second as v
def near(a, b): return abs(a - b) < 1e-9
PR = [10, 20, 10, 30, 10, 20]
spec = {  # name: (priors oldest..P, volE, P quote, E quote, result)
 "V1": (PR, 45, (.60, .62), (.60, .62), "yes"), "V2": (PR, 44, (.60, .62), (.60, .62), "yes"), "V3": (PR, 100, (.60, .62), (.62, .64), "yes"),
 "V4": (PR, 60, (.60, .62), (.61, .63), "no"), "V5": (PR, 60, (.30, .32), (.30, .32), "no"), "V6": (PR, 60, (.49, .51), (.49, .51), "yes"),
 "V7": (PR, 60, (.84, .86), (.84, .86), "yes"), "V8": (PR, 60, (.78, .80), (.78, .80), "yes"), "V9": ([10, 0, 20, 10, 30], 60, (.60, .62), (.60, .62), "yes"),
 "V10": (PR, 60, None, (.60, .62), "no"), "V11": (PR, 60, (.60, .62), (.0, .62), "yes")}
mk, cands = [], {}
for k in range(1, 12):
    n = "V%d" % k; pri, ve, pq, eq, r = spec[n]; C = 10000 * k; tk = "KXSILVER15M-" + n
    mk.append((tk, "KXSILVER15M", C, r)); cs = {}
    for j, vol in enumerate(reversed(pri)):          # newest (P) first
        end = C - 660 - 60 * j
        cs[end] = (pq[0], pq[1], vol) if (j == 0 and pq) else (.5, .52, vol)
    if pq is None: cs.pop(C - 660, None)
    cs[C - 600] = (eq[0], eq[1], ve); cands[tk] = cs
tr, base, sk = v.trades(mk, cands)
assert [t[1][-2:] if t[1][-2] != "V" else t[1][-2:] for t in tr] == ["V1", "V4", "V5", "V6", "V8"] or [t[1].split("-")[1] for t in tr] == ["V1", "V4", "V5", "V6", "V8"], tr
assert [t[2] for t in tr] == ["yes", "yes", "no", "yes", "yes"] and [t[3] for t in tr] == [.62, .63, .70, .51, .80], tr
assert sk == {"no_candle": 2, "no_prior": 1, "no_spike": 1, "moved": 1, "band": 1}, sk
want = {0.0: (6.61, 2.0216, 3.63 / 6.47), 0.01: (6.12, 1.9315, 3.53 / 6.57), 0.02: (5.63, 1.8453, 3.43 / 6.66)}
day = lambda t: "d1" if t <= 40000 else "d2"
for h, (net, p, h1) in want.items():
    b = v.block(tr, h, day); assert near(b["net"], net) and abs(b["pf"] - p) < 5e-5 and abs(b["h1"] - h1) < 1e-9 and b["h2"] == math.inf and b["wins"] == 4, (h, b)
assert abs(v.block(tr, .02, day)["z"] - 0.4657) < 5e-5
assert [round(v.cash(t, 0), 2) for t in tr] == [3.63, -6.47, 2.85, 4.72, 1.88] and [round(v.cash(t, .02), 2) for t in tr] == [3.43, -6.66, 2.65, 4.52, 1.69]
assert len(base) == 9 and sum(1 for t in base if v.cash(t, 0) > 0) == 7
assert v.median([1, 3, 2]) == 2 and v.median([10, 10, 10, 20, 20, 30]) == 15
assert v.cash((0, "x", "yes", .5, "void"), 0) == -0.18
assert (v.HAIRCUTS, v.E_LOOK, v.P_LOOK, v.MIN_PRIOR, v.MULT, v.STILL, v.LO, v.HI, v.CUT_TS) == ((0.0, 0.01, 0.02), 600, 660, 5, 3.0, 0.01, 0.50, 0.80, 1791043200)
b1, b2 = v.block(tr, .01), v.block(tr, .02)
assert v.verdict({"pf": 2, "n": 90, "h1": 1, "h2": 1, "z": 3}, {"pf": 2, "n": 90, "h1": 1, "h2": 1, "z": 3}) is True
ok = {"pf": 2, "n": 90, "h1": 1, "h2": 1, "z": 3}
assert v.verdict(ok, ok, {"pf": 1.49}, {"pf": 1.49}) is True and v.verdict(ok, ok, {"pf": 1.5}, {"pf": 1.2}) is False and v.verdict(ok, ok, {"pf": 1.2}, {"pf": 1.5}) is False
# exactly 5 positive priors is enough (edge), 4 is not
for pri, want_n in (([10, 10, 20, 10, 30], 1), ([10, 20, 10, 30], 0)):
    cs = {10000 - 660 - 60 * j: (.60, .62, vol) for j, vol in enumerate(reversed(pri))}; cs[10000 - 600] = (.60, .62, 60)
    t2, _, _ = v.trades([("X", "S", 10000, "yes")], {"X": cs}); assert len(t2) == want_n, (pri, t2)
# volume diagnostic: cumulative (never decreasing) gives 0, per-candle gives a share
assert v.decrease_share({"a": {1: (0, 0, 1), 2: (0, 0, 2), 3: (0, 0, 2)}}) == (0.0, 0, 2) and v.decrease_share({"a": {1: (0, 0, 5), 2: (0, 0, 2), 3: (0, 0, 9), 4: (0, 0, None)}}) == (0.5, 1, 2) and v.decrease_share({}) == (0.0, 0, 0)
# reader: refuses at the cut, loads below, drops after-close candles, reads volume
f = os.path.join(tempfile.mkdtemp(), "t.sqlite"); db = sqlite3.connect(f)
db.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); db.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
for r in (("KXGOLD15M-A", "KXGOLD15M", 0, 1791043199, "yes", 1.0), ("KXGOLD15M-B", "KXGOLD15M", 0, 1791043200, "yes", 1.0), ("KXBTC15M-C", "KXBTC15M", 0, 900, "yes", 1.0)): db.execute("insert into market values(?,?,?,?,?,?,'x')", r)
db.execute("insert into candle values('KXGOLD15M-A', 1791043300, .4, .5, 7, 1)"); db.execute("insert into candle values('KXGOLD15M-A', 1791043000, .4, .5, 7, 1)"); db.commit(); db.close()
try: v.load(f); raise AssertionError("must refuse")
except SystemExit as e: assert "REFUSED" in str(e) and "max 1791043200" in str(e) and "min 1791043199" in str(e), str(e)
db = sqlite3.connect(f); db.execute("delete from market where ticker='KXGOLD15M-B'"); db.commit(); db.close()
sha, ms, cd, dr = v.load(f); assert dr == 1 and cd["KXGOLD15M-A"] == {1791043000: (.4, .5, 7)}
print("volspike1 tests passed")

# main aborts on a cumulative volume column
f2 = os.path.join(tempfile.mkdtemp(), "c.sqlite"); db = sqlite3.connect(f2)
db.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); db.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
db.execute("insert into market values('KXGOLD15M-A','KXGOLD15M',0,5000,'yes',1.0,'x')")
for i, vol in enumerate((1, 2, 3, 4)): db.execute("insert into candle values('KXGOLD15M-A',?,.4,.5,?,1)", (1000 + 60 * i, vol))
db.commit(); db.close()
try: v.main(f2); raise AssertionError("must abort")
except SystemExit as e: assert "ABORTED" in str(e)
