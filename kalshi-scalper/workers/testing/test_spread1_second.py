import math, os, sqlite3, tempfile, spread1_second as s
def near(a, b): return abs(a - b) < 1e-9
Q = lambda b, a: (b, a)
# per market: prior candles oldest..P as list of (end offset from close, bid, ask) ; E quote or None
def pri(*qs, offs=(840, 780, 720, 660)):
    return {o: q for o, q in zip(offs[-len(qs):], qs)}
S1p = pri(*[(.50, .52)] * 4)
spec = {
 "S1": (S1p, (.54, .58), "yes"), "S2": (S1p, (.54, .57), "yes"), "S3": (pri(*[(.50, .51)] * 4), (.48, .51), "no"), "S4": (S1p, (.49, .53), "yes"),
 "S5": (pri(*[(.30, .32)] * 4), (.20, .24), "yes"), "S6": (pri(*[(.85, .87)] * 4), (.88, .92), "yes"), "S7": (pri(*[(.30, .32)] * 4), (.31, .35), "no"),
 "S8": (pri(*[(.50, .52)] * 3), (.54, .58), "no"), "S9": ({780: (.0, .52), 720: (.50, .52), 660: (.50, .52)}, (.54, .58), "yes"),
 "S10": (pri((.50, .52), (.50, .52), (.50, .56), (.50, .56)), (.55, .61), "yes"), "S11": (S1p, None, "yes"),
 "S12": ({840: (.50, .52), 780: (.50, .52), 720: (.50, .52)}, (.54, .58), "yes")}
mk, cands = [], {}
for k in range(1, 13):
    n = "S%d" % k; pq, eq, r = spec[n]; C = 10000 * k; tk = "KXSILVER15M-" + n
    mk.append((tk, "KXSILVER15M", C, r)); cs = {C - o: q for o, q in pq.items()}
    if eq: cs[C - 600] = eq
    cands[tk] = cs
tr, base, sk = s.trades(mk, cands)
assert [t[1].split("-")[1] for t in tr] == ["S1", "S3", "S5", "S7", "S8"], tr
assert [t[2] for t in tr] == ["yes", "no", "no", "yes", "yes"] and [t[3] for t in tr] == [.58, .52, .80, .35, .58], tr
assert sk == {"no_candle": 2, "no_prior": 1, "no_widen": 2, "no_move": 1, "band": 1}, sk
day = lambda t: "d1" if t <= 30000 else "d2"
want = {0.0: (-9.12, 0.4865), 0.01: (-9.60, 0.4681), 0.02: (-10.10, 0.4496)}
for h, (net, p) in want.items():
    b = s.block(tr, h, day); assert near(b["net"], net) and abs(b["pf"] - p) < 5e-5 and b["h1"] == math.inf and b["h2"] == 0.0 and b["wins"] == 2, (h, b)
assert abs(s.block(tr, .02, day)["z"] - (-0.3797)) < 5e-5
assert [round(s.cash(t, 0), 2) for t in tr] == [4.02, 4.62, -8.12, -3.66, -5.98] and [round(s.cash(t, .02), 2) for t in tr] == [3.83, 4.42, -8.31, -3.87, -6.17]
assert [t[1].split("-")[1] for t in base] == ["S1", "S2", "S3", "S5", "S7", "S8", "S9", "S10"] and sum(1 for t in base if s.cash(t, 0) > 0) == 5
assert s.median([.02, .02, .06, .06]) == .04 and s.median([3, 1, 2]) == 2 and s.cash((0, "x", "yes", .5, "void"), 0) == -0.18
assert (s.HAIRCUTS, s.E_LOOK, s.P_LOOK, s.MIN_PRIOR, s.FLOOR, s.MULT, s.MOVE, s.LO, s.HI, s.CUT_TS) == ((0.0, 0.01, 0.02), 600, 660, 3, 0.03, 2.0, 0.01, 0.35, 0.80, 1791043200)
ok = {"pf": 2, "n": 90, "h1": 1, "h2": 1, "z": 3}
assert s.verdict(ok, ok) is True and s.verdict(ok, ok, {"pf": 1.49}, {"pf": 1.49}) is True and s.verdict(ok, ok, {"pf": 1.5}, {"pf": 1.2}) is False and s.verdict(ok, ok, {"pf": 1.2}, {"pf": 1.5}) is False
assert s.verdict(dict(ok, n=79), dict(ok, n=79)) is False and s.verdict(ok, dict(ok, z=1.99)) is False and s.verdict(ok, dict(ok, h1=.99)) is False
# the 0.03 floor binds below 2 x median; a move of exactly 0.01 that floats to 0.00999... still counts (rounding)
fl = {("X", "S", 10000, "yes")}
cc = {"X": {10000 - 840: (.50, .51), 10000 - 780: (.50, .51), 10000 - 720: (.50, .51), 10000 - 660: (.50, .51), 10000 - 600: (.52, .545)}}
assert s.trades(list(fl), cc)[0] == [] and s.trades(list(fl), cc)[2]["no_widen"] == 1
cm = {"X": {10000 - 840: (.31, .33), 10000 - 780: (.31, .33), 10000 - 720: (.31, .33), 10000 - 660: (.31, .33), 10000 - 600: (.31, .35)}}
assert (.31 + .35) / 2 - (.31 + .33) / 2 < 0.01 and len(s.trades(list(fl), cm)[0]) == 1 and s.trades(list(fl), cm)[0][0][2] == "yes"
# reader: refuses at the cut, loads below, drops after-close candles
f = os.path.join(tempfile.mkdtemp(), "t.sqlite"); db = sqlite3.connect(f)
db.execute("create table market(ticker,series,open_ts,close_ts,result,strike,src)"); db.execute("create table candle(ticker,end_ts,bid_c,ask_c,volume,oi)")
for r in (("KXGOLD15M-A", "KXGOLD15M", 0, 1791043199, "yes", 1.0), ("KXGOLD15M-B", "KXGOLD15M", 0, 1791043200, "yes", 1.0), ("KXBTC15M-C", "KXBTC15M", 0, 900, "yes", 1.0)): db.execute("insert into market values(?,?,?,?,?,?,'x')", r)
db.execute("insert into candle values('KXGOLD15M-A', 1791043300, .4, .5, 7, 1)"); db.execute("insert into candle values('KXGOLD15M-A', 1791043000, .4, .5, 7, 1)"); db.commit(); db.close()
try: s.load(f); raise AssertionError("must refuse")
except SystemExit as e: assert "REFUSED" in str(e) and "max 1791043200" in str(e) and "min 1791043199" in str(e), str(e)
db = sqlite3.connect(f); db.execute("delete from market where ticker='KXGOLD15M-B'"); db.commit(); db.close()
sha, ms, cd, dr = s.load(f); assert dr == 1 and cd["KXGOLD15M-A"] == {1791043000: (.4, .5)}
print("spread1 tests passed")
