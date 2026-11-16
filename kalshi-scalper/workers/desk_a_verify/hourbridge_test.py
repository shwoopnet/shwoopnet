"""python3 -I hourbridge_test.py : HOURBRIDGE1 against the hand case in HOURBRIDGE1_REGISTRATION_NOV16.md."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hourbridge as H
T = 1793400000; D = (T - 100) * 1000; near = lambda a, b, t=1e-9: abs(a - b) < t
def ev(strikes=(100000, 100100, 100200), k15=100050, q=(0.60, 0.64), res="yes", lad=None, qt=D - 1000):
    lad = lad or {100000: (0.79, 0.81), 100100: (0.59, 0.61), 100200: (0.39, 0.41)}
    return {"H": T, "ladder": {k: [(D - 2000, b, a)] for k, (b, a) in lad.items() if k in strikes}, "q15": {"strike": k15, "rows": [(qt, q[0], q[1])]}, "result": res}
why, det = H.decide(ev()); assert why == "ok" and det["side"] == "yes" and near(det["ask"], 0.64) and near(det["g"], 0.08), (why, det)
assert near(H.cash(ev(), det, 0.02), 3.24) and near(H.cash(ev(), det, 0.01), 3.34)
assert near(H.cash(ev(res="no"), det, 0.02), -6.76) and near(H.cash(ev(res="no"), det, 0.01), -6.66)
assert near(H.cash(ev(res="void"), det, 0.02), -0.16)
why2, det2 = H.decide(ev(q=(0.76, 0.80), res="no")); assert why2 == "ok" and det2["side"] == "no" and near(det2["ask"], 0.24) and near(det2["g"], -0.08)
assert near(H.cash(ev(q=(0.76, 0.80), res="no"), det2, 0.02), 7.26)
assert H.decide(ev(k15=100300))[0] == "K15 outside the ladder"
stale = ev(); stale["ladder"][100000] = [(D - 7000, 0.79, 0.81)]; assert H.decide(stale)[0] == "K15 outside the ladder"      # the 100,000 row is 7 s old: dropped, no lower strike
assert H.decide(ev(q=(0.58, 0.64)))[0] == "15m spread wide"
assert H.decide(ev(lad={100000: (0.77, 0.83), 100100: (0.59, 0.61), 100200: (0.39, 0.41)}))[0] == "ladder spread wide"
assert H.decide(ev(q=(0.67, 0.71)))[0] == "no signal"                                              # mid 0.69, g = +0.01
assert H.decide(ev(q=(0, 0.64)))[0] == "one-sided"
assert H.decide(ev(qt=D - 9000))[0] == "stale 15m quote"
# a strike exactly at K15 uses its own mid
assert near(H.decide(ev(k15=100100, q=(0.50, 0.54)))[1]["g"], 0.60 - 0.52)
# the three-trade stats: +3.24, +7.26, -6.76 -> PF 10.50 / 6.76 and no evidence
evs = []
for i, (e_, res) in enumerate(((ev(res="yes"), 0), (ev(q=(0.76, 0.80), res="no"), 0), (ev(res="no"), 0))):
    e_ = dict(e_); e_["H"] = T + 3600 * i
    shift = 3600 * 1000 * i
    e_["ladder"] = {k: [(t + shift, b, a) for t, b, a in v] for k, v in e_["ladder"].items()}; e_["q15"] = {"strike": e_["q15"]["strike"], "rows": [(t + shift, b, a) for t, b, a in e_["q15"]["rows"]]}
    evs.append(e_)
r = H.run(evs); assert r["h2"]["n"] == 3 and near(r["h2"]["pf"], 10.50 / 6.76, 1e-9) and r["h2"]["evidence"] == "no evidence at n = 3", r
print("ALL OK")
