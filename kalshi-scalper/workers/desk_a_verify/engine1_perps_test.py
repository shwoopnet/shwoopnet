"""python3 -I engine1_perps_test.py : the perps block against ENGINE1_PERPS_HAND_CASE_NOV16.md."""
import os, sys, math, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_perps as P
T0 = calendar.timegm((2026, 11, 9, 15, 0, 0)) - 600          # candle i10 ends 15:00 UTC (tod "open")
near = lambda a, b, t=1e-9: abs(a - b) < t
mids = {i: 100.0 for i in range(0, 6)}; mids.update({6: 100.02, 7: 100.04, 8: 100.06, 9: 100.08, 11: 100.10, 12: 100.30})
C = []
for i in range(0, 41):
    e = T0 + 60 * i
    if i == 10: C.append((e, 100.00, 100.10, 0, 0, 0))
    elif i == 13: C.append((e, 100.60, 100.70, 0, 0, 0))
    else: m = mids.get(i, 100.0); C.append((e, round(m - .05, 6), round(m + .05, 6), 0, 0, 0))
by = {c[0]: c for c in C}; e = T0 + 600; h = 1e-4
assert P.RULES_PER_TICKER == 252 and len(P.FILTERS) == 21 and P.HAIRCUTS == (0.001, 0.002) and P.FEE == 0.0012 and P.FEE_MAKER == 0.0005
# features
assert P.feature_ok(by, e, ("mom1", "down"), None) is True and P.feature_ok(by, e, ("mom1", "up"), None) is False
assert P.feature_ok(by, e, ("mom3", "up"), None) is True and P.feature_ok(by, e, ("mom5", "up"), None) is True
assert P.feature_ok(by, e, ("mom15", "up"), None) is None and P.feature_ok(by, e, ("mom15", "down"), None) is None
spread = (100.10 - 100.00) / 100.05 * 1e4; assert near(spread, 9.995, 1e-3)
cuts = P.spread_cuts([8, 9, 9, 10, 12, 15]); assert cuts == (9, 10)
assert P.feature_ok(by, e, ("spread", "mid"), cuts) is True and P.feature_ok(by, e, ("spread", "low"), cuts) is False and P.feature_ok(by, e, ("spread", "high"), cuts) is False
# trades
r, why = P.trade(by, e, "long", "T3", h); assert why == "time" and near(r, 0.002394026092), (r, why)
r, why = P.trade(by, e, "long", "TS15", h); assert why == "target" and near(r, 0.002394026092), (r, why)
r, why = P.trade(by, e, "short", "TS15", h); assert why == "stop" and near(r, -0.00410032003), (r, why)
r, why = P.trade(by, e, "short", "T3", h); assert why == "time" and near(r, -0.00960142014), (r, why)
r, why = P.trade(by, e, "long", "T30", h); assert why == "time" and near(r, (99.95 * 0.9999 / (100.10 * 1.0001) - 1) - 0.0024, 1e-9)
by11 = {k: v for k, v in by.items()}; assert P.trade(by, T0 + 660, "long", "T30", h) == (None, "no mark")                 # i11 + 30 min is i41: missing
# long stop never hit; the target needs bid >= 100.260175015 (i12 bid 100.25 does not trigger)
assert by[T0 + 720][1] == 100.25 and 100.25 < 100.10 * 1.0001 * 1.0015
# cooldown: entry at i10 taken, i11 to i39 refused, i40 allowed
rows, cnt = P.run_rule(C, None, "long", "T3", h, None, lo=e, hi=T0 + 60 * 41)
assert [r[0] for r in rows] == [e], rows            # i11 to i39 refused by the cooldown; i40 has no T3 mark (i43 missing), so nothing else is entered
assert all(rows[i + 1][0] - rows[i][0] >= 1800 for i in range(len(rows) - 1))
# the break filters on the invented series (candle i ends 14:50 UTC + i minutes; here T0 = 14:50 UTC of Nov 9): hand values of ENGINE1_PERPS_HAND_CASE_NOV16.md
byx = {c[0]: c for c in C}
E_ = lambda i: T0 + 60 * i
assert P.feature_ok(byx, E_(10), ("orb", "up"), None) is None                       # i10 ends 15:00: the break needs an entry at 15:01 or later
assert P.feature_ok(byx, E_(11), ("orb", "up"), None) is True and P.feature_ok(byx, E_(11), ("orb", "down"), None) is False and P.feature_ok(byx, E_(12), ("orb", "up"), None) is True
assert P.feature_ok(byx, E_(10), ("sess", "high"), None) is False and P.feature_ok(byx, E_(11), ("sess", "high"), None) is True and P.feature_ok(byx, E_(12), ("sess", "high"), None) is True
assert P.feature_ok(byx, E_(13), ("sess", "high"), None) is True and P.feature_ok(byx, E_(14), ("sess", "high"), None) is False
assert all(P.feature_ok(byx, E_(i), ("sess", "low"), None) is False for i in (10, 11, 12, 13))
# time of day boundaries
d = calendar.timegm((2026, 11, 9, 0, 0, 0))
for (hh, mm, ss), want in (((15, 0, 0), "open"), ((14, 29, 59), "pre"), ((20, 0, 0), "close"), ((21, 0, 0), "post"), ((15, 30, 0), "mid"), ((8, 59, 59), "post"), ((9, 0, 0), "pre")):
    assert P.tod(d + hh * 3600 + mm * 60 + ss) == want, (hh, mm, ss, P.tod(d + hh * 3600 + mm * 60 + ss), want)
# a one-sided candle is never an entry or an exit mark
bad = [c if c[0] != T0 + 780 else (c[0], 0, 100.7, 0, 0, 0) for c in C]
assert P.trade({c[0]: c for c in bad if P.ok(c)}, e, "long", "T3", h) == (None, "no mark")
s = P.stats([(T0, .0124, 180), (T0 + 86400, -.0026, 300), (T0 + 2 * 86400, .0224, 60)]); assert s["n"] == 3 and near(s["pf"], .03 / .005) and s["evidence"] == "no evidence at n = 3" and near(s["avg_hold_min"], 180 / 60 / 1 * 0 + (180 + 300 + 60) / 3 / 60) and near(s["avg_gross_bp"], (.0124 - .0026 + .0224) / 3 * 1e4)
sm = P.stats([(T0, .0124, 180)], P.FEE_MAKER); assert near(sm["net"], .0124 - .0010)
# (1) the boundary: an entry whose e + 1800 reaches the boundary is dropped and counted
rows, cnt = P.run_rule(C, None, "long", "T3", h, None, lo=e, hi=T0 + 60 * 41, boundary=T0 + 2400)
assert cnt["exit crosses the boundary"] >= 1 and [r[0] for r in rows] == [], (rows, cnt)       # e + 1800 = i40 = the boundary: dropped
rows2, cnt2 = P.run_rule(C, None, "long", "T3", h, None, lo=e, hi=T0 + 60 * 41, boundary=T0 + 2401)
assert [r[0] for r in rows2] == [e]
# (2) the days floor: a rule with n and PF above the bar but under 10 days cannot pass
assert P.days([(T0, .01, 0), (T0 + 60, .01, 0)]) == 1 and P.MIN_DAYS == 10
# run_all: tried = 204 per ticker with a constant; a ticker without one is counted apart; thin data passes nothing
rep = P.run_all({"KXHAND": C, "KXSPYPERP": C})
assert rep["tried"] == 252 and rep["no_split_constant"] == ["KXHAND"] and rep["search_passes"] == 0 and rep["validate_passes"] == 0 and rep["survivors"] == [] and "insufficient_days" in rep, rep
# the days floor in run_all on an invented rising series (every long T3 entry is profitable): under MIN_DAYS it is counted and cannot pass
cs = []
for d in (9, 10, 11, 12):
    base = calendar.timegm((2026, 11, d, 15, 30, 0))
    for i in range(100):
        m = 100 * (1.0017 ** i); cs.append((base + 60 * i, m - .001, m + .001, 0, 0, 0))
P.MIN_N = 3; P.MIN_DAYS = 10
r1 = P.run_all({"KXSPYPERP": cs}); assert r1["search_passes"] == 0 and r1["insufficient_days"] > 0 and r1["survivors"] == [], r1
P.MIN_DAYS = 2
r2 = P.run_all({"KXSPYPERP": cs}); assert r2["search_passes"] > 0 and r2["insufficient_days"] >= 0, r2
print("ALL OK")
