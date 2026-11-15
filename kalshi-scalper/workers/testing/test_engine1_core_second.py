#!/usr/bin/env python3
"""Tests for engine1_core_second.py on INVENTED entries (hand case ENGINE1_CORE_SECOND_HAND_CASE.md)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_core_second as c
near = lambda a, b: abs(a - b) < 1e-9
C0 = 20000000
def E(i, k, side, ask, result, day, entry_end, n=10): return {"id": i, "close_ts": C0 + 900 * k, "day": day, "series": "S", "side": side, "ask": ask, "n": n, "entry_end": C0 + 900 * k + entry_end, "result": result}
cl = lambda k, off, b, a: (C0 + 900 * k + off, b, a)
e1, e2, e3, e4, e5 = E("E1", 1, "yes", .40, "yes", "D1", -600), E("E2", 2, "no", .30, "yes", "D1", -600), E("E3", 3, "yes", .50, "void", "D2", -600), E("E4", 4, "yes", .985, "yes", "D3", -600), E("E5", 5, "yes", .50, "yes", "D3", -120)
P = {"E1": [cl(1, -540, .50, .52), cl(1, -480, .82, .84), cl(1, -420, .86, .88), cl(1, -180, .90, .92)],
     "E2": [cl(2, -540, .66, .68), cl(2, -480, .60, .62), cl(2, -360, .95, .95), cl(2, -300, .90, .92), cl(2, -180, .93, .95), cl(2, -60, .97, .98)],
     "E3": [], "E4": [cl(4, -300, .99, .995)], "E5": [cl(5, -60, .90, .92)]}
EN = {"E1": e1, "E2": e2, "E3": e3, "E4": e4, "E5": e5}
def cash(i, kind, h, n=None):
    r = c.score_entry(EN[i], P[i], kind, h, n); return None if r["status"] == "no_mark" else r["cash"]
exp = {  # (id, kind): (h0, h1, h2); None = no mark
    ("E1", "H"): (5.83, 5.73, 5.62), ("E1", "T"): (3.92, 3.72, 3.92), ("E1", "S"): (5.83, 5.73, 5.62), ("E1", "B"): (3.92, 3.72, 3.92), ("E1", "M180"): (4.76, 4.56, 4.34), ("E1", "M60"): None,
    ("E2", "H"): (-3.15, -3.25, -3.36), ("E2", "T"): (-3.15, -3.25, -3.36), ("E2", "S"): (-2.41, -2.60, -2.80), ("E2", "B"): (-2.41, -2.60, -2.80), ("E2", "M180"): (-2.69, -2.88, -3.09), ("E2", "M60"): (-2.97, -3.16, -3.27),
    ("E3", "H"): (-.18, -.18, -.18), ("E3", "T"): (-.18, -.18, -.18), ("E3", "S"): (-.18, -.18, -.18), ("E3", "B"): (-.18, -.18, -.18), ("E3", "M180"): None, ("E3", "M60"): None,
    ("E4", "H"): (.13, .09, .09), ("E4", "T"): (.02, -.13, -.24), ("E5", "H"): (4.82, None, None), ("E5", "M180"): None, ("E5", "M60"): (3.75, 3.55, 3.34)}
for (i, k), v in exp.items():
    for h, want in zip(c.HAIRCUTS, v if v is not None else (None, None, None)):
        if want is None and k == "H" and i == "E5": continue
        got = cash(i, k, h)
        assert (got is None and want is None) or (got is not None and want is not None and near(got, want)), (i, k, h, got, want)
assert near(cash("E5", "H", .01), 10 * .49 - c.fee_up_order(.51, 10)) and near(cash("E5", "H", .01), 4.90 - .18)
assert near(cash("E1", "H", 0.0, n=1), 0.58) and c.fee_up_order(.40, 1) == 0.02 and c.fee_up_order(.40, 10) == 0.17
assert c.fee_up_order(.5, 10) == 0.18 and c.fee_up_order(.9, 10) == 0.07 and c.fee_up_order(.985, 10) == 0.02 and c.fee_up_order(.99, 10) == 0.01
# aggregate H, h 0, n 10
ents = [e1, e2, e3, e4, e5]; a = c.aggregate(ents, P, "H", 0.0)
assert a["n"] == 5 and a["wins"] == 3 and near(a["net"], 7.45) and near(a["pf"], 10.78 / 3.33) and near(a["half1_pf"], 5.83 / 3.15) and near(a["half1_net"], 2.68) and near(a["half2_pf"], 4.95 / 0.18) and near(a["half2_net"], 4.77)
assert a["trade_days"] == 3 and near(a["day_clustered_z"], 1.673219667421461) and a["exit_counts"] == {"target": 0, "stop": 0, "time": 0, "settle": 5, "no_mark": 0}
m = c.aggregate(ents, P, "M180", 0.0); assert m["n"] == 2 and m["exit_counts"]["time"] == 2 and m["exit_counts"]["no_mark"] == 3 and near(m["net"], 4.76 - 2.69)
t = c.aggregate(ents, P, "T", 0.0); assert t["exit_counts"] == {"target": 2, "stop": 0, "time": 0, "settle": 3, "no_mark": 0}
s = c.aggregate(ents, P, "S", 0.0); assert s["exit_counts"]["stop"] == 1 and s["exit_counts"]["settle"] == 4
# PF edge cases and z edge cases
assert c.pf([1.0, 2.0]) == math.inf and c.pf([-1.0]) == 0.0 and math.isnan(c.pf([])) and math.isnan(c.pf([0.0])) and near(c.pf([3.0, -1.0, -2.0]), 1.0)
assert c.day_z([{"day": "a", "cash": 1.0}]) == (None, 1) and c.day_z([{"day": "a", "cash": 1.0}, {"day": "b", "cash": 1.0}]) == (None, 2) and near(c.day_z([{"day": "a", "cash": 1.0}, {"day": "a", "cash": 2.0}, {"day": "b", "cash": -1.0}])[0], 0.5)
# bid exactly at threshold triggers; unsellable candle never triggers; both-trigger: stop wins (unit on thresholds that cannot overlap here, so check the stop-first order with paid 0.99)
ex = E("X", 9, "yes", .40, "no", "D9", -600); px = [cl(9, -540, .80, .81)]
assert c.score_entry(ex, px, "T", 0.0)["reason"] == "target" and c.score_entry(ex, [cl(9, -540, .7999, .81)], "T", 0.0)["reason"] == "settle" and c.score_entry(ex, [cl(9, -540, .20, .21)], "S", 0.0)["reason"] == "stop" and c.score_entry(ex, [cl(9, -540, .2001, .21)], "S", 0.0)["reason"] == "settle"
assert c.score_entry(ex, [cl(9, -540, .90, .90)], "T", 0.0)["reason"] == "settle" and c.score_entry(ex, [cl(9, -540, 0.0, .5)], "S", 0.0)["reason"] == "settle" and c.score_entry(ex, [cl(9, -540, .5, 1.0)], "T", 0.0)["reason"] == "settle"
# the sale price floor 0.01 and the entry cap 0.99; a void after an early exit changes nothing
ev = E("V", 9, "yes", .40, "void", "D9", -600); assert near(c.score_entry(ev, px, "T", 0.0)["cash"], c.score_entry(ex, px, "T", 0.0)["cash"]) and near(c.score_entry(ev, px, "H", 0.0)["cash"], -c.fee_up_order(.40, 10))
print("engine1 core build 2 tests passed")
