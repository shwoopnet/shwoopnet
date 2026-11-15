"""python3 -I adjwin1_test.py : ADJWIN1_HAND_CASE_NOV15.md on invented windows."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adjwin1 as A
ok = lambda a, b, t=1e-9: abs(a - b) < t
T = 1790000000                                    # before the cut
def P(close, p_last_mid=0.85, extra=()):
    c = [(close - 840, .49, .51), (close - 60, p_last_mid - .01, p_last_mid + .01), (close, .98, 1.0)] + list(extra)
    return {"series": "KXZZ15M", "close": close, "result": "yes", "candles": c}
def W(close, bid=.49, ask=.51, res="yes", pre=()):
    return {"series": "KXZZ15M", "close": close, "result": res, "candles": list(pre) + [(close - 900 + 60, bid, ask)]}
p1, w1 = P(T), W(T + 900)
for h, m, r in ((0.0, .472, -.528), (.01, .462, -.538), (.02, .452, -.548)):
    x, why = A.trade(p1, w1, "M", h); assert why == "ok" and ok(x, m), (h, x, why)
    x, why = A.trade(p1, w1, "R", h); assert why == "ok" and ok(x, r), (h, x, why)
w1n = W(T + 900, res="no")
assert ok(A.trade(p1, w1n, "R", 0.0)[0], .472) and ok(A.trade(p1, w1n, "M", 0.0)[0], -.528)
assert A.signal(P(T, .74), w1)[0] == "no signal"                       # case 1: drift .24
p2 = P(T + 1800, .15); w2 = W(T + 2700)                                 # case 2: drift -.35, W settles YES
assert ok(A.trade(p2, w2, "R", 0.0)[0], .472) and ok(A.trade(p2, w2, "M", 0.0)[0], -.528)
assert A.trade(p1, W(T + 900, ask=.62), "M", 0.0) == (None, "out of band")  # case 3
assert A.trade(p1, W(T + 900, bid=0, ask=.51), "M", 0.0) == (None, "one-sided")   # case 4
pb = P(T); pb["candles"] = [c for c in pb["candles"] if c[0] != T - 60]
assert A.signal(pb, w1)[0] == "P incomplete"                            # case 5
wpre = W(T + 900, pre=[(T, .10, .20)])                                  # case 6: a candle ending at T is not W's first
assert A.signal(p1, wpre)[2] == (T + 60, .49, .51)
cut = 1791043200
assert A.signal(P(cut + 900), W(cut + 1800))[0] == "after the cut"      # case 7
assert A.signal(P(cut - 900), W(cut))[0] == "after the cut"
r = A.run({"KXZZ15M": [p1, w1, p2, w2]})["KXZZ15M"]            # hand case stats: n 2, PF .472/.528, no evidence
for arm in "RM":
    assert r["arms"][arm]["h0"]["val"]["n"] == 2 and r["arms"][arm]["h0"]["dev"]["n"] == 0 and ok(r["arms"][arm]["h0"]["val"]["pf"], .472 / .528, 1e-9) and r["arms"][arm]["h0"]["val"]["evidence"] == "no evidence at n = 2", r
assert r["skips"].get("P incomplete") == 1, r["skips"]                     # (w1, p2): w1 has no usable path
# Auditor B's three cases, each expects a skip
pl = P(T); pl["candles"][0] = (T - 600, .49, .51)
assert A.signal(pl, w1)[0] == "P incomplete"                              # P first candle late
assert A.signal(p1, dict(w1, candles=[(T + 480, .49, .51)]))[0] == "W incomplete"   # W first candle late
pm = P(T); pm["candles"] = [c for c in pm["candles"] if c[0] != T - 60] + [(T - 120, .84, .86)]
assert A.signal(pm, w1)[0] == "P incomplete"                              # t-60 missing, t-120 present
assert A.fee_up_order(0.51) == 0.18 and A.fee_up_order(0.5) == 0.18
assert A.trade(p1, W(T + 900, bid=.39, ask=.41), "M", 0.0)[1] == "ok" and A.trade(p1, W(T + 900, bid=.59, ask=.61), "M", 0.0)[1] == "out of band"
assert A.trade(p1, W(T + 900, bid=.39, ask=.41), "R", 0.0)[1] == "out of band"       # NO ask 0.61
assert A.day_z([(T, .1), (T + 86400, -.1), (T + 2 * 86400, .1)]) is not None and A.day_z([(T, .1)]) is None
print("ALL OK")
