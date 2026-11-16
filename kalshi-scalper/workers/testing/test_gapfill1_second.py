import math, gapfill1_second as g
def near(a, b): return abs(a - b) < 1e-9
M = [("M1", "S", 900, "yes", 100.0), ("M2", "S", 3600, "no", 101.0), ("M3", "S", 4500, "yes", 101.4), ("M4", "S", 5400, "no", 101.0), ("M5", "S", 9000, "yes", 99.0),
     ("M6", "S", 9900, "yes", 98.5), ("M7", "S", 14400, "no", 98.5), ("M8", "S", 15300, "no", 98.8), ("M9", "S", 18000, "yes", None), ("M10", "S", 19800, "no", 99.0), ("M11", "S", 21599, "yes", 100.0)]
q = {"M2": (.48, .50), "M3": (.58, .60), "M5": (.60, .62), "M6": (.70, .72), "M7": (.48, .50), "M9": (.48, .50), "M10": (.48, .50), "M11": (.48, .50)}
close = {m[0]: m[2] for m in M}
cands = {k: {close[k] - 600: v} for k, v in q.items()}
tr, sk = g.trades(M, cands)
assert [t[1] for t in tr] == ["M2", "M3", "M5"] and [t[2] for t in tr] == ["no", "no", "yes"] and [t[3] for t in tr] == [.52, .42, .62], tr
assert sk == {"band": 1, "zero_gap": 1, "no_candle": 1, "no_strike": 2}, sk
day = lambda t: "d1" if t < 9000 else "d2"
want = {0.0: (3.87, 1.8836, 3.63 / 4.38), 0.01: (3.57, 1.7969, 3.53 / 4.48), 0.02: (3.27, 1.7140, 3.43 / 4.58)}
for h, (net, p, hh) in want.items():
    b = g.block(tr, h, day)
    assert near(b["net"], net) and abs(b["pf"] - p) < 5e-5 and b["h1"] == math.inf and abs(b["h2"] - hh) < 1e-9 and b["wins"] == 2, (h, b)
assert abs(g.block(tr, .02, day)["z"] - 0.9109) < 5e-5
assert [round(g.cash(t, 0), 2) for t in tr] == [4.62, -4.38, 3.63] and [round(g.cash(t, .02), 2) for t in tr] == [4.42, -4.58, 3.43]
assert g.cash((0, "x", "yes", .50, "void"), 0) == -0.18
# edges: halt exactly 1800 counts, 1799 does not; band edges inclusive; K2 must be exactly +900
E = [("A", "S", 1000, "no", 10.0), ("B", "S", 2800, "no", 11.0), ("C", "S", 3700, "no", 11.0), ("D", "S", 4600, "no", 11.0)]
cc = {"B": {2200: (.35, .37)}, "C": {3100: (.65, .66)}, "D": {4000: (.4, .5)}}
tr2, sk2 = g.trades(E, cc); assert [t[1] for t in tr2] == ["B", "C"] and tr2[0][2] == "no" and tr2[0][3] == .65 and tr2[1][3] == .35, tr2
E2 = [("A", "S", 1000, "no", 10.0), ("B", "S", 2799, "no", 11.0), ("C", "S", 3700, "no", 11.0)]
assert g.trades(E2, {"B": {2199: (.4, .5)}, "C": {3100: (.4, .5)}})[0] == []

assert g.HAIRCUTS == (0.0, 0.01, 0.02) and g.LOOK == 600 and g.HALT == 1800 and g.WIN == 900
print("gapfill1 tests passed")
