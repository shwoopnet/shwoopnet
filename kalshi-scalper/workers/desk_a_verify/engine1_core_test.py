"""python3 -I engine1_core_test.py : my core against the hand-computed fixture at 1e-9."""
import os, sys, json
d = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, d)
import engine1_core as K
fx = json.load(open(os.path.join(d, "..", "engine1", "ENGINE1_FIXTURE_ENTRIES.json")))["entries"]
ex = json.load(open(os.path.join(d, "..", "engine1", "ENGINE1_FIXTURE_EXPECTED_HAND.json")))
for key, h in (("h0", 0.0), ("h2", 0.02)):
    for e in fx:
        x, why = K.score(e, e["exit"], h, 1); want = ex[key][e["id"]]
        assert (x is None and want is None) or (x is not None and want is not None and abs(x - want) < 1e-9), (key, e["id"], x, want)
for i, want in ex["n10_h0_total"].items():
    e = [e for e in fx if e["id"] == i][0]; assert abs(K.score(e, e["exit"], 0.0, 10)[0] - want) < 1e-9, i
assert [K.score(e, e["exit"], 0.0, 1)[1] for e in fx if e["id"] in ("E7", "E8")] == ["no mark", "no mark"]
assert K.fee_up_order(0.5, 10) == 0.18 and K.fee_up_order(0.9, 10) == 0.07
a = K.aggregate(fx, "H", 0.0, 1)       # all 11 entries held to settlement, hand sum -0.975 (E1 .09, E2 -.91, E3 -.32, E4 .38, E5 -.42, E6-E8 .18 each, E9 .005, E10 -.32, E11 -.02)
assert a["n"] == 11 and a["wins"] == 6 and abs(a["net"] + 0.975) < 1e-9 and a["reasons"] == {"settle": 10, "void": 1} and a["day_z"] is None and a["trade_days"] == 1, a
fb = json.load(open(os.path.join(d, "..", "engine1", "ENGINE1_FIXTURE_ENTRIES_B.json")))["entries"]; eb = json.load(open(os.path.join(d, "..", "engine1", "ENGINE1_FIXTURE_EXPECTED_HAND_B.json")))
for key, h in (("h0", 0.0), ("h2", 0.02)):
    for e in fb:
        x, why = K.score(e, e["exit"], h, 1); assert why == "settle" and abs(x - eb[key][e["id"]]) < 1e-9, (key, e["id"], x, why)
print("ALL OK")
