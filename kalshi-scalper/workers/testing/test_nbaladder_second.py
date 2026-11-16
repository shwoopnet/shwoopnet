import math
import nbaladder_second as m
O = 1792720800 - 1792720800 % 1800 + 1800 * 0          # a :00 or :30 instant
O = 1792720800
assert O % 1800 == 0
D = O - 3600
def rung(t, strike, player="P", event="G1", open_time=None, close_time=None, result="yes", occ=None):
    return {"ticker": t, "event": event, "player": player, "strike": strike, "open_time": D - 9 * 3600 if open_time is None else open_time, "close_time": O + 3600 if close_time is None else close_time, "occ": O if occ is None else occ, "result": result}
def cd(b, a, v=0.0): return (b, a, v)
# rung A of the hand case
A = rung("T-A", 25)
cs = {"T-A": {D - 120: cd(0.44, 0.46, 3), D - 60: cd(0.47, 0.46, 4), D - 1800 - 60: cd(0.49, 0.51, 2), D - 300: cd(0, 0, 5), D - 700: cd(0.4, 0.5, 2), O - 600: cd(0.60, 0.62)}}
O_by, c0 = m.games([A]); assert O_by == {"G1": O} and c0 == {"games_dropped_clock": 0}
dec, cnt = m.decisions([A], cs, O_by, 60); d = dec[0]
assert d["t"] == D - 120 and abs(d["bid"] - 0.44) < 1e-12 and abs(d["mv"] - (-0.05)) < 1e-9 and abs(d["spread"] - 0.02) < 1e-9, d
assert m.passes(d, "move_down") and not m.passes(d, "move_flat") and not m.passes(d, "move_up") and m.passes(d, "spread3") and m.passes(d, "spread6") and m.passes(d, "age_old") and not m.passes(d, "age_young")
assert m.side_ask(d, "yes") == 0.46 and abs(m.side_ask(d, "no") - 0.56) < 1e-12
assert m.in_band(0.46, (0.40, 0.50)) and m.in_band(0.56, (0.50, 0.60)) and not m.in_band(0.46, (0.50, 0.60))
c, mk = m.cash(d, "yes", "H", cs); assert abs(c - 5.12) < 1e-9 and not mk
r_no = dict(A, result="no"); d_no = dict(d, r=r_no); assert abs(m.cash(d_no, "yes", "H", cs)[0] - (-4.88)) < 1e-9
assert abs(m.cash(d, "yes", "H", cs, "two")[0] - 5.02) < 1e-9
# close_time = D + 100: the rung is open at D, entry haircut 2c, paid 0.48
d2 = dict(d, r=dict(A, close_time=D + 100)); assert abs(m.cash(d2, "yes", "H", cs)[0] - 5.02) < 1e-9
c, mk = m.cash(d, "yes", "M10", cs); assert mk and abs(c - 0.85) < 1e-9
d3 = dict(d, r=dict(A, close_time=O - 500)); c, mk = m.cash(d3, "yes", "M10", cs); assert mk and abs(c - 0.74) < 1e-9, c
c, mk = m.cash(dict(d, r=dict(A, close_time=O - 700)), "yes", "M10", cs); assert not mk and abs(c - 5.12) < 1e-9          # closed before the mark: held
cs2 = {"T-A": {k: v for k, v in cs["T-A"].items() if k != O - 600}}; c, mk = m.cash(d, "yes", "M10", cs2); assert not mk and abs(c - 5.12) < 1e-9
assert abs(m.cash(d, "yes", "H", cs, "weekly", 5)[0] - 2.56) < 1e-9
# a void keeps the entry fee
assert abs(m.cash(dict(d, r=dict(A, result="void")), "yes", "H", cs)[0] - (-0.18)) < 1e-9
# the no side at M10: bid_no = 1 - yes ask: yes ask at the mark 0.62 -> no bid 0.38, sale 0.37, paid 0.57
c, mk = m.cash(d, "no", "M10", cs); fee_in = m.core.fee_up_order(0.57, 10); fee_out = m.core.fee_up_order(0.37, 10); assert mk and abs(c - (3.7 - 5.7 - fee_in - fee_out)) < 1e-9
# decision candle windows and closed by D
assert m.decisions([A], {"T-A": {D - 181: cd(0.44, 0.46)}}, O_by, 60)[1]["no_quote"] == 1 and m.decisions([A], {"T-A": {D - 180: cd(0.44, 0.46)}}, O_by, 60)[0]
assert m.decisions([dict(A, close_time=D)], cs, O_by, 60)[1]["closed_by_D"] == 1
# anchor window [D - 1980, D - 1800]
assert m.decisions([A], {"T-A": {D - 120: cd(0.44, 0.46), D - 1981: cd(0.4, 0.5)}}, O_by, 60)[0][0]["mv"] is None
assert m.decisions([A], {"T-A": {D - 120: cd(0.44, 0.46), D - 1980: cd(0.4, 0.5)}}, O_by, 60)[0][0]["mv"] is not None
# volume: (D-10, D] 3, 4, 5 and (D-20, D-10] 2, 2
vs = {"T-A": {D - 120: cd(0.44, 0.46, 3), D - 300: cd(0, 0, 4), D - 590: cd(0.4, 0.5, 5), D - 700: cd(0.4, 0.5, 2), D - 1000: cd(0.4, 0.5, 2)}}; dv = m.decisions([A], vs, O_by, 60)[0][0]
assert dv["v1"] == 12 and dv["v0"] == 4 and m.passes(dv, "vol_rising") and not m.passes(dv, "vol_not")
# distance: rungs 15 (0.80), 20 (0.55), 25 (0.52), 30 (0.30): the line is 25
rs = [rung("T%d" % k, k) for k in (15, 20, 25, 30)]; mids = {15: (0.79, 0.81), 20: (0.54, 0.56), 25: (0.51, 0.53), 30: (0.29, 0.31)}
dd = m.decisions(rs, {"T%d" % k: {D - 60: cd(*mids[k])} for k in mids}, O_by, 60)[0]; assert {x["r"]["strike"]: x["dist"] for x in dd} == {15: "below", 20: "below", 25: "at", 30: "above"}
tie = [rung("U20", 20), rung("U25", 25)]; dt = m.decisions(tie, {"U20": {D - 60: cd(0.44, 0.46)}, "U25": {D - 60: cd(0.54, 0.56)}}, O_by, 60)[0]; assert {x["r"]["strike"]: x["dist"] for x in dt} == {20: "below", 25: "at"}
# a rung not open at D is out of the line; a game with two occurrence values is dropped; an occ off :00 / :30 is dropped
assert m.games([rung("a", 1), rung("b", 2, occ=O + 1800)])[0] == {} and m.games([rung("a", 1, occ=O + 60)])[0] == {} and m.games([rung("a", 1, occ=O + 1800)])[0] == {"G1": O + 1800}
# stats and the gate
def tr(i, c1, g, day=0, mk=False): return {"game": g, "day": day, "close_time": i, "ticker": "t%d" % i, "cash1": c1, "cash2": c1, "cashw": c1, "marked": mk}
s = m.cell_stats([tr(1, 10, "a"), tr(2, -4, "b"), tr(3, 6, "c")]); assert abs(s["z"] - 0.9608) < 1e-4 and s["games"] == 3 and abs(s["pf1"] - 16 / 4) < 1e-9
assert abs(m.zstat([10, -4, 6]) - 4 / (math.sqrt(52) / math.sqrt(3))) < 1e-12
big = [tr(i, 0.5 if i % 3 else -0.25, "g%d" % (i // 3), i // 12) for i in range(120)]; sb = m.cell_stats(big); assert sb["games"] == 40 and sb["days"] == 10 and m.gate_ok(sb) and sb["n"] == 120
for kill in ({"n": 99}, {"games": 39}, {"days": 9}, {"pf1": 1.29}, {"h1": 0.99}, {"h2": 0.99}, {"pf2": 0.99}): assert not m.gate_ok(dict(sb, **kill)), kill
# BH over the denominator m_total, ranks among the eligible cells
assert m.bh({"a": 0.00001, "b": 0.5, "c": 0.01}, 624) == {"a"} and m.bh({"a": 0.00001}, 624 + 10 ** 6) == set() and m.bh({"a": None}, 10) == set()
assert m.bh({"a": 0.00007, "b": 0.00015}, 624) == {"a", "b"} and m.bh({"a": 0.00007, "b": 0.0002}, 624) == {"a"} and m.bh({"a": 0.00009, "b": 0.00015}, 624) == {"a", "b"}          # thresholds 0.0000801 x k: rank 2 passes at 0.0001603 and then rank 1 passes with it (the step-up rule)
# round 2: boundaries
q0 = {"T-A": {D: cd(0.44, 0.46)}}; assert m.decisions([A], q0, O_by, 60)[0][0]["t"] == D          # a candle exactly at D is the decision candle
q1 = {"T-A": {D - 120: cd(0.44, 0.46), D - 1800: cd(0.4, 0.5)}}; assert m.decisions([A], q1, O_by, 60)[0][0]["mv"] is not None          # an anchor exactly at D - 1800
assert m.decisions([dict(A, open_time=D)], cs, O_by, 60)[0] and m.decisions([dict(A, open_time=D + 1)], cs, O_by, 60)[1]["not_open"] == 1
assert m.passes(m.decisions([dict(A, open_time=D - 21600)], cs, O_by, 60)[0][0], "age_old") and m.passes(m.decisions([dict(A, open_time=D - 21599)], cs, O_by, 60)[0][0], "age_young")
def with_mv(mv): return {"mv": mv}
for mv, want in ((-0.05, "move_down"), (0.05, "move_up"), (0.0, "move_flat"), (0.0499, "move_flat"), (-0.0499, "move_flat")):
    got = [f for f in ("move_down", "move_flat", "move_up") if m.passes(with_mv(mv), f)]; assert got == [want], (mv, got)
assert [f for f in ("move_down", "move_flat", "move_up") if m.passes(with_mv(None), f)] == []
assert m.passes({"spread": 0.03}, "spread3") and not m.passes({"spread": 0.0301}, "spread3") and m.passes({"spread": 0.06}, "spread6") and not m.passes({"spread": 0.061}, "spread6")
assert m.passes({"v1": 5, "v0": 5}, "vol_not") and not m.passes({"v1": 5, "v0": 5}, "vol_rising")
vb = {"T-A": {D - 120: cd(0.44, 0.46, 1), D: cd(0.44, 0.46, 2), D - 600: cd(0.4, 0.5, 7), D - 1200: cd(0.4, 0.5, 100), D - 601: cd(0.4, 0.5, 3)}}; dvb = m.decisions([A], vb, O_by, 60)[0][0]; assert dvb["v1"] == 3 and dvb["v0"] == 10, dvb
for ask, band, want in ((0.30, (0.30, 0.40), True), (0.40, (0.30, 0.40), False), (0.40, (0.40, 0.50), True), (0.6999999999, (0.60, 0.70), True), (0.70, (0.60, 0.70), True), (0.7001, (0.60, 0.70), False), (0.70, (0.50, 0.60), False), (0.60, (0.50, 0.60), False), (0.2999, (0.30, 0.40), False)): assert m.in_band(ask, band) == want, (ask, band)
for close, h in ((D + 120, 0.02), (D + 121, 0.01)):
    got = m.cash(dict(d, r=dict(A, close_time=close)), "yes", "H", cs)[0]; assert abs(got - (5.02 if h == 0.02 else 5.12)) < 1e-9, (close, got)
for close, want in ((O - 480, 0.74), (O - 479, 0.85)): assert abs(m.cash(dict(d, r=dict(A, close_time=close)), "yes", "M10", cs)[0] - want) < 1e-9, close          # sale leg: 2c at <= 120 s from the mark
assert m.cash(dict(d, r=dict(A, close_time=O - 600)), "yes", "M10", cs)[1] is False and m.cash(dict(d, r=dict(A, close_time=O - 599)), "yes", "M10", cs)[1] is True
assert abs(m.cell_stats([dict(tr(1, 1.0, "a"), cashw=16.0)])["weekly5"] - 7.0) < 1e-12
oo = [dict(tr(1, 1.0, "a"), close_time=10, day=9), dict(tr(2, 1.0, "b"), close_time=20, day=1), dict(tr(3, -1.0, "c"), close_time=30, day=2), dict(tr(4, -1.0, "d"), close_time=40, day=0)]
so = m.cell_stats(oo); assert so["h1"] == math.inf and so["h2"] == 0.0          # halves by close_time: the two wins first (by day they would not be)
assert m.bh({"a": 0.05 / 624}, 624) == {"a"}
cells = {"x": {"n": 48, "p": 0.1}, "y": {"n": 47, "p": 0.1}}; assert m.eligible(cells) == {"x": 0.1}
assert not m.passes(m.decisions([dict(A, open_time=D - 21600)], cs, O_by, 60)[0][0], "age_young")
e5 = 0.05 - m.TOL; assert m.passes({"mv": e5}, "move_up") and not m.passes({"mv": e5}, "move_flat") and m.passes({"mv": -e5}, "move_down") and not m.passes({"mv": -e5}, "move_flat")
cells_, cnt_, surv_ = m.search([A], cs); assert len(cells_) == 624 and surv_ == set() and cells_[(60, 0.40, "yes", "H", "none")]["n"] == 1 and cells_[(60, 0.50, "no", "H", "none")]["n"] == 1 and cells_[(120, 0.40, "yes", "H", "none")]["n"] == 0
print("nbaladder second tests passed")
