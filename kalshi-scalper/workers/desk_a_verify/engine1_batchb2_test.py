import os, sys, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_batchb2 as B, engine1_driver as D, engine1_enum as N, engine1_core as K
D.MIN_N = 3; D.MIN_SPD = 2.0
def near(a, b, t=1e-9): return abs(a - b) < t
# score_ta hand case: close 12:00, entry end 11:51 (bucket 540), raw ask .90, h .01 -> paid .91, fee_in .06; the candle ending 11:54 has bid .93 ask .95 -> exit .92, fee_out ceil(5.152)/100 = .06; net = 9.20 - 9.10 - .06 - .06 = -0.02
close = calendar.timegm((2026, 9, 1, 12, 0, 0)); e0 = close - 540
ent = {"ask": .90, "close_ts": close, "entry_end": e0, "side": "yes", "path": [(e0 + 180, .93, .95), (e0 + 300, .96, .97)]}
x, r = B.score_ta(ent, 3, 0.01, 10); assert r == "time" and near(x, -0.02), (x, r)
x5, r5 = B.score_ta(ent, 5, 0.01, 10); assert r5 == "time" and near(x5, round(0.95 * 10 - 9.1 - 0.06 - K.fee_up_order(0.95, 10), 9)), x5       # exit .96 - .01 = .95
assert B.score_ta(dict(ent, entry_end=close - 300), 5, 0.01, 10) == (None, "too late")                       # entry + 300 s = the close, after close - 60
assert B.score_ta(dict(ent, path=[(e0 + 180, 0, .95)]), 3, 0.01, 10) == (None, "no mark")                    # the mark candle is not two sided
assert B.score_ta(dict(ent, path=[]), 3, 0.01, 10) == (None, "no mark")
# vspike: volumes at e, e-60 .. e-300 = 10, 2,2,2,2,2 -> 10 / 2 = 5.0
mk = lambda vols: {close - 60 * i: (close - 60 * i, .89, .90, .9, v, 1) for i, v in enumerate(vols, 1)}
byv = mk([10, 2, 2, 2, 2, 2]); e1 = close - 60
assert near(B.vspike(byv, e1), 5.0) and B.vspike(mk([10, 2, 2, 2, 2]), e1) is None and B.vspike(mk([10, 0, 0, 0, 0, 0]), e1) is None and B.vspike(mk([None, 2, 2, 2, 2, 2]), e1) is None
# swid: spread now 2c (.88/.90), 3 minutes earlier 1c (.89/.90) -> +1, class up; a one sided old candle is missing
by = {e0: (e0, .88, .90, .9, 1, 1), e0 - 180: (e0 - 180, .89, .90, .9, 1, 1)}; assert B.swid(by, e0) == 1 and N.cls(1) == "up"
by[e0 - 180] = (e0 - 180, 0, .90, .9, 1, 1); assert B.swid(by, e0) is None
# run_family on invented markets (patched sizes): ENGB3SPRW finds the (swid, up) group; ENGB1TIMESTOP scores TA3 on the winners
def cl(day, i): return calendar.timegm((2026, 9, day, 12, 15 * i, 0))
def mkt(day, i, ser="KXETH15M"):
    c = cl(day, i); e = c - 540
    return {"series": ser, "ticker": "%s-%d_%d" % (ser, day, i), "close": c, "result": "yes", "candles": [(e - 180, .89, .90, .9, 1, 10), (e, .88, .90, .9, 1, 10), (e + 180, .98, .99, .985, 1, 10), (c - 60, .96, .97, .96, 1, 10)]}
shape = {1: 2, 2: 3, 3: 4, 4: 2, 5: 3, 6: 4}; wa = {"KXETH15M": [mkt(d, i) for d in shape for i in range(shape[d])]}
r3 = B.run_family(wa, "ENGB3SPRW", prior_m=0); assert r3["tries_this_spec"] == r3["rules_per_series"] == 13 * 18 * 4 * 6 * 3 and r3["m_now"] == r3["tries_this_spec"], r3
assert r3["search_passes"] >= 1 and any(x["filter"] == ["swid", "up"] and x["bucket"] == 540 for x in r3["validate_bar_list"]), r3["validate_bar_list"][:2]
r1 = B.run_family(wa, "ENGB1TIMESTOP", prior_m=0); assert r1["rules_per_series"] == 13 * 18 * 4 * 2 * 22 == 41184
ok = [x for x in r1["validate_bar_list"] if x["exit"] == "TA3" and x["bucket"] == 540 and x["band"] == 18 and x["side"] == "favourite" and x["filter"] is None]
assert len(ok) == 1 and ok[0]["n"] == 9, r1["validate_bar_list"][:3]
# TA3 hand value per entry at 1c: net -0.02 per trade is a loser at paid .91 with exit .92; check PF < 1 there:
r1b = [x for x in r1["validate_bar_list"] if x["exit"] == "TA3"]
for x in r1b: assert x["pf_1c"] >= D.PF1
print("ENGB1 2 3 OK")
