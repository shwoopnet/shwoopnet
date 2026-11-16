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
assert P.RULES_PER_TICKER == 420 and len(P.FILTERS) == 21 and len(P.EXITS) == 10 and P.HAIRCUTS == (0.0002, 0.0005) and P.STRESS == (0.001, 0.002) and P.FEE == 0.0012 and P.FEE_MAKER == 0.0005
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
assert P.feature_ok(byx, E_(10), ("orb", "up"), None)  is False                       # i10 ends 15:00: the break needs an entry at 15:01 or later
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
rows, cnt = P.run_rule(C, None, "long", "T3", h, None, lo=e, hi=T0 + 60 * 41, boundary=e + 180)
assert cnt["exit crosses the boundary"] >= 1 and [r[0] for r in rows] == [], (rows, cnt)       # R1: the clip horizon is the rule's OWN exit (T3 = e + 180) = the boundary: dropped
rows2, cnt2 = P.run_rule(C, None, "long", "T3", h, None, lo=e, hi=T0 + 60 * 41, boundary=e + 181)
assert [r[0] for r in rows2] == [e]
# (2) the days floor: a rule with n and PF above the bar but under 10 days cannot pass
assert P.days([(T0, .01, 0), (T0 + 60, .01, 0)]) == 1 and P.MIN_DAYS == 10
# run_all: tried = 204 per ticker with a constant; a ticker without one is counted apart; thin data passes nothing
rep = P.run_all({"KXHAND": C, "KXSPYPERP": C})
assert rep["tried"] == 420 and rep["no_split_constant"] == ["KXHAND"] and rep["search_passes"] == 0 and rep["validate_passes"] == 0 and rep["survivors"] == [] and "insufficient_days" in rep, rep
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
# amendment 2: the long exits on KXHAND2 (Tuesday 2026-11-10, candle i ends 14:40 UTC + i minutes, bid = mid - 0.01, ask = mid + 0.01)
D2 = calendar.timegm((2026, 11, 10, 14, 40, 0)); mid2 = {60: 100.50, 240: 99.60, 380: 101.00, 1431: 102.00}
c2 = {}
for i in range(0, 1500):
    m = mid2.get(i, 100.00); c2[D2 + 60 * i] = (D2 + 60 * i, round(m - .01, 6), round(m + .01, 6), 0, 0, 0)
e0 = D2; h2 = 2e-4
for ex, want in (("T60", 0.0043976806), ("T240", -0.0045978205), ("TC", 0.0093951812), ("TO", 0.0193901825)):
    g, why, hold, fl = P.trade_full(c2, e0, "long", ex, h2); assert why == "time" and near(g, want, 2e-9), (ex, g, want)
assert P.trade_full(c2, e0, "long", "T60", h2)[2] == 3600 and P.trade_full(c2, e0, "long", "TC", h2)[2] == 380 * 60 and P.trade_full(c2, e0, "long", "TO", h2)[2] == 1431 * 60
assert P.exit_time(D2 + 380 * 60, "TC") is None and P.trade_full(c2, D2 + 380 * 60, "long", "TC", h2)[1] == "no mark"                    # entry at 21:00: no mark for TC
fri = calendar.timegm((2026, 11, 13, 15, 0, 0)); sat = calendar.timegm((2026, 11, 14, 15, 0, 0)); sun = calendar.timegm((2026, 11, 15, 15, 0, 0)); mon = calendar.timegm((2026, 11, 16, 14, 31, 0))
assert P.exit_time(fri, "TO") == mon and P.exit_time(sat, "TO") == mon and P.exit_time(sun, "TO") == mon and P.exit_time(D2, "TO") == D2 + 1431 * 60
# cooldown = hold: a T60 rule enters at i0 and not again before i60; a TC rule once a day
rows, cnt = P.run_rule(list(c2.values()), None, "long", "T60", h2, None, lo=D2, hi=D2 + 61 * 60)
assert [r[0] for r in rows] == [D2, D2 + 3600], [(r[0] - D2) // 60 for r in rows]
rows, cnt = P.run_rule(list(c2.values()), None, "long", "TC", h2, None, lo=D2, hi=D2 + 380 * 60)
assert len(rows) == 1 and rows[0][0] == D2, [(r[0] - D2) // 60 for r in rows]
# the boundary clip uses the rule's own hold: an entry whose T240 exit reaches the boundary is dropped
rows, cnt = P.run_rule(list(c2.values()), None, "long", "T240", h2, None, lo=D2, hi=D2 + 61 * 60, boundary=D2 + 240 * 60)
assert rows == [] and cnt["exit crosses the boundary"] >= 1
# (2) funding: prints at 21:00 UTC strictly between the entry candle end and the exit candle end
ft = P.funding_times(D2, D2 + 1431 * 60); assert ft == [D2 + 380 * 60], ft                       # TO from Tuesday 14:40: one print (Tuesday 21:00)
assert P.funding_times(D2, D2 + 380 * 60) == [] and P.funding_times(D2, D2 + 3600) == []          # TC exits AT the print: nothing paid; T60 crosses none
fri21 = calendar.timegm((2026, 11, 13, 21, 0, 0)); assert P.funding_times(fri, calendar.timegm((2026, 11, 16, 14, 31, 0))) == [fri21, fri21 + 86400, fri21 + 2 * 86400]
g0, w0, hd, fl0 = P.trade_full(c2, e0, "long", "TO", h2); assert fl0 == "funding not booked" and near(g0, 0.0193901825, 2e-9)          # no funding map: labelled
g1, w1, hd, fl1 = P.trade_full(c2, e0, "long", "TO", h2, {D2 + 380 * 60: 0.0001}); assert fl1 is None and near(g1, 0.0193901825 - 0.0001, 2e-9)       # long pays a positive rate
g2, w2, hd, fl2 = P.trade_full(c2, e0, "short", "TO", h2, {D2 + 380 * 60: 0.0001}); g3, w3, hd, fl3 = P.trade_full(c2, e0, "short", "TO", h2, {D2 + 380 * 60: -0.0001})
assert fl2 is None and near(g2 - g3, 0.0002, 1e-12)                                              # a short receives a positive rate and pays a negative one
g4, w4, hd, fl4 = P.trade_full(c2, e0, "long", "T60", h2); assert fl4 is None                    # no print crossed: no label
# a flagged trade is left out of the gate figures and counted
rows = [(D2, .01, 60, None), (D2 + 86400, .02, 60, "funding not booked")]; st = P.stats(rows); assert st["n"] == 1 and st["funding_unbooked"] == 1
# BH keeps the prior tries in the denominator
rep = P.run_all({"KXSPYPERP": C}, m_prior=504); assert rep["m_total"] == rep["tried"] + 504 and rep["m_prior"] == 504
# amendment 3: ET clocks under EDT (Sep 4 to Oct 31) and the DST end (2026-11-01 06:00 UTC)
U = lambda *a: calendar.timegm(a)
for (hh, mm, ss), want in (((13, 30, 0), "open"), ((13, 29, 59), "pre"), ((8, 0, 0), "pre"), ((7, 59, 59), "post"), ((14, 30, 0), "mid"), ((19, 0, 0), "close"), ((19, 59, 59), "close"), ((20, 0, 0), "post")):
    assert P.tod(U(2026, 9, 10, hh, mm, ss)) == want, (hh, mm, ss)                                                     # EDT: ET = UTC - 4
assert P.tod(U(2026, 11, 9, 14, 30, 0)) == "open" and P.tod(U(2026, 11, 9, 21, 0, 0)) == "post"                           # EST (Nov 9): unchanged from the earlier UTC definitions
assert P.et_off(U(2026, 11, 1, 5, 59, 59)) == -4 * 3600 and P.et_off(U(2026, 11, 1, 6, 0, 0)) == -5 * 3600 and P.et_off(U(2026, 3, 8, 6, 59, 59)) == -5 * 3600 and P.et_off(U(2026, 3, 8, 7, 0, 0)) == -4 * 3600
e1 = U(2026, 9, 10, 14, 0, 0)
assert P.exit_time(e1, "TC") == U(2026, 9, 10, 20, 0, 0) and P.exit_time(U(2026, 9, 10, 20, 0, 0), "TC") is None and P.exit_time(U(2026, 9, 10, 20, 1, 0), "TC") is None
assert P.exit_time(U(2026, 9, 11, 15, 0, 0), "TO") == U(2026, 9, 14, 13, 31, 0) and P.exit_time(e1, "TO") == U(2026, 9, 11, 13, 31, 0)     # Friday to Monday 09:31 ET; Thursday to Friday
assert P.exit_time(U(2026, 10, 30, 15, 0, 0), "TO") == U(2026, 11, 2, 14, 31, 0)                                          # across the DST end: Monday 09:31 EST = 14:31 UTC
assert P.funding_times(U(2026, 10, 30, 15, 0, 0), U(2026, 11, 2, 14, 31, 0)) == [U(2026, 10, 30, 20, 0, 0), U(2026, 10, 31, 20, 0, 0), U(2026, 11, 1, 21, 0, 0)]
assert P.funding_times(U(2026, 9, 10, 14, 0, 0), U(2026, 9, 10, 20, 0, 0)) == []                                          # an exit at the print pays nothing
# opening range break in EDT: the window is the candles ending 13:31 to 14:00 UTC, the entry 14:01 UTC or later
dd = U(2026, 9, 10, 0, 0, 0); byE = {}
for i in range(0, 120):
    ts = U(2026, 9, 10, 13, 31, 0) + 60 * i
    m = 100 + 0.01 * i if i < 30 else 100.5 + 0.01 * (i - 30)
    byE[ts] = (ts, m - .005, m + .005, 0, 0, 0)
assert P.feature_ok(byE, U(2026, 9, 10, 14, 0, 0), ("orb", "up"), None)  is False                                         # 14:00 UTC = 10:00 ET: too early
assert P.feature_ok(byE, U(2026, 9, 10, 14, 1, 0), ("orb", "up"), None) is True and P.feature_ok(byE, U(2026, 9, 10, 14, 1, 0), ("orb", "down"), None) is False
assert P.feature_ok(byE, U(2026, 9, 10, 14, 1, 0), ("sess", "high"), None) is True
# run_all with its own split (pass 3): SEARCH to 2026-09-30, VALIDATE from 2026-10-01 for a name the default table lacks
cs3 = []
for d in range(1, 36):
    base = calendar.timegm((2026, 9, 1, 0, 0, 0)) + 86400 * (d - 1) + 14 * 3600
    for i in range(60): m = 100 + 0.001 * i; cs3.append((base + 60 * i, m - .005, m + .005, 0, 0, 0))
rep3 = P.run_all({"KXGOLDPERP": cs3}, last_search={"GOLDPERP": "2026-09-30"})
assert rep3["tried"] == 420 and rep3["no_split_constant"] == [] and rep3["by_ticker"]["KXGOLDPERP"]["search_days_max"] >= 10, rep3
assert P.run_all({"KXGOLDPERP": cs3})["no_split_constant"] == ["KXGOLDPERP"]
print("ALL OK")
# (Nov 16, Auditor B) funding booked from the extract's own print timestamps
import calendar as _c
_U = lambda *a: _c.timegm(a)
_e0 = _U(2026, 9, 10, 13, 0, 0)
_cs = {t: (t, 100.0, 100.0001, 100.0, 1, 1) for t in range(_e0, _e0 + 3 * 3600 + 60, 60)}
_f = {_U(2026, 9, 9, 14, 0, 0): 0.001, _U(2026, 9, 10, 14, 0, 0): 0.001, _U(2026, 9, 11, 14, 0, 0): 0.001}
_g, _w, _h, _fl = P.trade_full(_cs, _e0, "long", "T60", 0.0, _f)      # one print at 14:00 (gold's real hour) inside 13:00 to 14:00? exit AT print pays nothing
assert _fl is None and abs(_g) < 1e-5, (_g, _fl)
_g, _w, _h, _fl = P.trade_full(_cs, _e0, "long", "T60", 0.0, {_U(2026, 9, 10, 13, 30, 0): 0.002, **_f}); assert abs(_g + 0.002) < 1e-4 and _fl is None   # a print at 13:30 is booked, whatever the hour
_g, _w, _h, _fl = P.trade_full(_cs, _e0, "short", "T60", 0.0, {_U(2026, 9, 10, 13, 30, 0): 0.002, **_f}); assert abs(_g - 0.002) < 1e-4      # a short receives it
_far = {_U(2026, 9, 1, 14, 0, 0): 0.001, _U(2026, 9, 20, 14, 0, 0): 0.001}                           # a 19 day hole around the trade
_g, _w, _h, _fl = P.trade_full(_cs, _e0, "long", "T60", 0.0, _far); assert _fl == "funding not booked"
_g, _w, _h, _fl = P.trade_full(_cs, _e0, "long", "T60", 0.0, {}); assert _fl == "funding not booked"      # no print at all
print("EXTRACT FUNDING OK")

# (Nov 16, Auditor B rulings) R1 the clip uses the rule's own exit time; fix B the ET day's offset is read at its midday
import calendar as _c2
assert P.clip_of(e, "T3") == 180 and P.clip_of(e, "T10") == 600 and P.clip_of(e, "T15") == 900 and P.clip_of(e, "T60") == 3600 and P.clip_of(e, "TS15") == 1800
nov1 = _c2.timegm((2026, 11, 1, 4, 30, 0))                                   # Sun Nov 1 00:30 EDT, before the 02:00 step
assert P.et_day0(nov1) + 16 * 3600 == _c2.timegm((2026, 11, 1, 21, 0, 0)) and P.exit_time(nov1, "TC") == _c2.timegm((2026, 11, 1, 21, 0, 0))
mar = _c2.timegm((2026, 3, 8, 6, 0, 0))                                      # Sun Mar 8 01:00 EST, before the 02:00 step: 16:00 ET that day is EDT 20:00Z
assert P.et_day0(mar) + 16 * 3600 == _c2.timegm((2026, 3, 8, 20, 0, 0))
print("RULINGS R1 AND ET-DAY OK")
