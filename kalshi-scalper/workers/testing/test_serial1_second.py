import math, serial1_second as s
def near(a, b): return abs(a - b) < 1e-9
M = lambda k, c, r: ("T%d" % k, "S", c, r)
mk = [M(1, 900, "yes"), M(2, 1800, "no"), M(3, 2700, "no"), M(4, 3600, "no"), M(5, 5400, "yes"), M(6, 6300, "yes"), M(7, 7200, "void"), M(8, 8100, "yes")]
q = {"T1": .48, "T2": .48, "T3": .60, "T4": .80, "T5": .48, "T6": .38, "T8": .48}
a = {"T1": .50, "T2": .50, "T3": .62, "T4": .82, "T5": .50, "T6": .40, "T8": .50}
cands = {t: {c - 600: (q[t], a[t])} for t, _, c, _ in mk if t in q}
cands["T6"][6300 + 60] = (0.01, 0.99)  # never read: dropped by loader; here proves no effect since we only read C-600
for v, nets, pfs, h1, h2 in (("C", (6.48, 6.18, 5.86), (2.2510, 2.1705, 2.0892), (0.0, 0.0, 0.0), None), ("F", (-8.12, -8.42, -8.72), (.3626, .3493, .3364), None, (0, 0, 0))):
    tr, sk = s.trades(mk, cands, v)
    assert len(tr) == 3 and sk == {"no_prev": 3, "no_candle": 1, "band": 1}, (sk,)
    for i, h in enumerate(s.HAIRCUTS):
        b = s.block(tr, h)
        assert near(b["net"], nets[i]) and abs(b["pf"] - pfs[i]) < 5e-5, (v, h, b)
    b2 = s.block(tr, 0.02)
    if v == "C": assert b2["h1"] == 0.0 and b2["h2"] == math.inf
    else: assert b2["h1"] == math.inf and b2["h2"] == 0.0
cash = lambda v, h: [s.cash(t, h) for t in s.trades(mk, cands, v)[0]]
assert [round(x, 2) for x in cash("C", 0)] == [-5.18, 5.83, 5.83] and [round(x, 2) for x in cash("C", .02)] == [-5.38, 5.62, 5.62]
assert [round(x, 2) for x in cash("F", 0)] == [4.62, -6.37, -6.37] and [round(x, 2) for x in cash("F", .02)] == [4.42, -6.57, -6.57]
# day z: W2 on day 1, W3 and W6 on day 2 (hand 0.3526)
assert abs(s.day_z([("d1", -5.38), ("d2", 5.62), ("d2", 5.62)]) - 2.93 / (16.62 / 2)) < 1e-9
# band edges inclusive, candle at C-600 only, price cap
assert s.cash(( 0, "x", "yes", .985, "yes"), .02) == round(10 * (1 - .99) - s.fee_up_order(.99), 9)
b = [("A", "S", 900, "yes"), ("B", "S", 1800, "yes"), ("C", "S", 2700, "no")]
c = {"B": {1200: (.34, .35)}, "C": {2100: (.64, .66)}}
tr, sk = s.trades(b, c, "C"); assert len(tr) == 1 and tr[0][3] == .35 and sk["band"] == 1   # ask .35 in band; C: previous yes, YES ask .35 in; third: prev yes, YES ask .66 out
c2 = {"B": {1200: (.34, .36)}, "C": {2100: (.64, .65)}}
tr, sk = s.trades(b, c2, "C"); assert len(tr) == 2 and tr[1][3] == .65
print("serial1 tests passed")
assert s.cash((0, "x", "yes", .50, "void"), 0) == -0.18 and s.cash((0, "x", "no", .52, "void"), .02) == -0.18
