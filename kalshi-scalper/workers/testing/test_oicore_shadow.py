"""Test for oicore_shadow.py: INVENTED rows only (OICORE_ADAPTER_AND_PLACE_REPORT_HAND_CASES.md item 1). Run: python3 -B -W ignore test_oicore_shadow.py"""
import calendar, inspect, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oicore_shadow as o
import spxoi1 as s1
import liveshadow as ls

C = calendar.timegm((2026, 11, 13, 15, 0, 0))
def poll(t, no=None, yes=None): return {"t": float(t), "recv": float(t), "yes_bids": yes if yes is not None else ([(0.15, 20)] if no else []), "no_bids": no or [], "close": C}
def oi(rise_from=1000, rise_to=1600): return [{"ts": C - 360, "oi": rise_from}, {"ts": C - 180, "oi": rise_to}]
A = {"KXAAA15M-1": [poll(C - 175, no=[(0.80, 20)])], "KXAAA15M-2": [poll(C - 175, no=[(0.45, 20)], yes=[(0.40, 20)])], "KXAAA15M-3": [poll(C - 175, no=[(0.80, 20)])]}
B = {"KXBBB15M-1": [poll(C - 175, no=[(0.88, 20)])], "KXBBB15M-2": [poll(C - 175, no=[(0.55, 20)])], "KXBBB15M-3": [poll(C - 175, no=[(0.88, 20)])]}
polls = dict(A); polls.update(B)
cs = {"KXAAA15M-1": oi(1000, 1600), "KXAAA15M-2": oi(1000, 1600), "KXAAA15M-3": oi(1000, 1499), "KXBBB15M-1": oi(1000, 2000), "KXBBB15M-2": oi(1000, 2000), "KXBBB15M-3": oi(1000, 1999)}
# market A: NC15, band .08 to .50, T 500
a = o.oicore_shadow(polls, cs, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15")
assert set(a) == set(A) and a["KXAAA15M-1"][:2] == ("trade", "yes") and abs(a["KXAAA15M-1"][2] - 0.20) < 1e-12 and abs(a["KXAAA15M-1"][3]["limit"] - 0.20) < 1e-12 and a["KXAAA15M-1"][3]["t"] == C - 175
assert a["KXAAA15M-2"] == ("no_trade", "cheaper side outside 0.08 to 0.50") and a["KXAAA15M-3"] == ("no_trade", "oi rise under T")
# market B: R6, band .10 to .40, T 1000: oi rise exactly T fires; its own band
b = o.oicore_shadow(polls, cs, "KXBBB15M", 0.10, 0.40, 1000, 0.0, "R6")
assert set(b) == set(B) and b["KXBBB15M-1"][:2] == ("trade", "yes") and abs(b["KXBBB15M-1"][2] - 0.12) < 1e-12
assert b["KXBBB15M-2"] == ("no_trade", "cheaper side outside 0.10 to 0.40") and b["KXBBB15M-3"] == ("no_trade", "oi rise under T")
# the same ask .45 is inside A's band and outside B's: the band is the caller's
assert o.oicore_shadow({"KXAAA15M-9": [poll(C - 175, no=[(0.55, 20)])]}, {"KXAAA15M-9": oi()}, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15")["KXAAA15M-9"][0] == "trade"
assert o.oicore_shadow({"KXAAA15M-9": [poll(C - 175, no=[(0.55, 20)])]}, {"KXAAA15M-9": oi()}, "KXAAA15M", 0.10, 0.40, 500, 0.0, "NC15")["KXAAA15M-9"][0] == "no_trade"
# limit_add moves the limit and nothing else
assert abs(o.oicore_shadow(A, cs, "KXAAA15M", 0.08, 0.50, 500, 0.01, "NC15")["KXAAA15M-1"][3]["limit"] - 0.21) < 1e-12
# the other series is ignored in both directions; an unknown series gives an empty dict; data gaps
assert o.oicore_shadow(polls, cs, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15").keys().isdisjoint(B) and o.oicore_shadow(polls, cs, "KXZZZ15M", 0.08, 0.50, 500, 0.0, "NC15") == {}
assert o.oicore_shadow({"KXAAA15M-4": [poll(C - 175, no=[(0.80, 20)])]}, {}, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15")["KXAAA15M-4"] == ("no_data", "no open interest")
assert o.oicore_shadow({"KXAAA15M-5": [poll(C - 300, no=[(0.80, 20)])]}, {"KXAAA15M-5": oi()}, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15")["KXAAA15M-5"] == ("no_data", "no poll in window")
nc = {"KXAAA15M-6": [dict(poll(C - 175, no=[(0.80, 20)]), close=None)]}; assert o.oicore_shadow(nc, {}, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15")["KXAAA15M-6"] == ("no_data", "no close time")
# nothing has a default; a bad log raises
for fn in (o.oicore_shadow, o.signal, o.fill_check):
    assert all(p.default is inspect.Parameter.empty for p in inspect.signature(fn).parameters.values()), fn
for bad in ("nc15", "R6 ", "", None):
    try: o.oicore_shadow(A, cs, "KXAAA15M", 0.08, 0.50, 500, 0.0, bad); assert 0
    except ValueError: pass
# the mechanism equals spxoi1's when the band is .08 to .50: the same decisions on the same polls
assert o.oicore_shadow(A, cs, "KXAAA15M", 0.08, 0.50, 500, 0.0, "NC15") == s1.spxoi1_shadow(A, cs, 500, 0.0)
# window and OI edges
assert o.signal([poll(C - 180, no=[(0.80, 20)])], C, 1600, 1000, 0.08, 0.50, 600, 0.0)[0] == "signal" and o.signal([poll(C - 120, no=[(0.80, 20)])], C, 1600, 1000, 0.08, 0.50, 600 + 1e-10, 0.0)[0] == "signal"
assert o.signal([poll(C - 180.1, no=[(0.80, 20)])], C, 1600, 1000, 0.08, 0.50, 600, 0.0)[0] == "no_data" and o.signal([poll(C - 119.9, no=[(0.80, 20)])], C, 1600, 1000, 0.08, 0.50, 600, 0.0)[0] == "no_data"
assert o.signal([poll(C - 150, no=[(0.92, 20)])], C, 1600, 1000, 0.08, 0.50, 600, 0.0)[0] == "signal" and o.signal([poll(C - 150, no=[(0.92, 20)])], C, 1600, 1000, 0.09, 0.50, 600, 0.0)[0] == "no_trade"          # ask .08 inside .08, outside .09
# the first poll in the window that passes the band is the signal
assert o.signal([poll(C - 178, no=[(0.40, 20)], yes=[(0.45, 20)]), poll(C - 170, no=[(0.80, 20)]), poll(C - 160, no=[(0.85, 20)])], C, 2, 0, 0.08, 0.50, 1, 0.0)[1] == 1
# --- fill checks: NC15 within 6 s, R6 within 4 s ---
sp = lambda dt: [poll(C - 175, no=[(0.80, 12)]), poll(C - 175 + dt, no=[(0.80, 12)])]
for dt, nc_ok, r6_ok in ((4.0, True, True), (5.0, True, False), (6.0, True, False), (6.1, False, False), (3.9, True, True), (4.1, True, False)):
    assert (o.fill_check(sp(dt), 0, "yes", 0.20, "NC15")[0] == "filled") is nc_ok, (dt, "NC15")
    assert (o.fill_check(sp(dt), 0, "yes", 0.20, "R6")[0] == "filled") is r6_ok, (dt, "R6")
assert o.fill_check(sp(5.0), 0, "yes", 0.20, "R6")[0] == "not_fill_checked" and o.fill_check([sp(5.0)[0]], 0, "yes", 0.20, "R6")[0] == "not_fill_checked"
assert o.fill_check([poll(C - 175, no=[(0.80, 12)]), poll(C - 171, no=[(0.80, 4)])], 0, "yes", 0.20, "R6")[0] == "miss"
fw = o.fill_check([poll(C - 175, no=[(0.80, 12)]), poll(C - 171, no=[(0.78, 12)])], 0, "yes", 0.22, "R6"); assert fw[0] == "filled" and abs(fw[1] - 0.22) < 1e-9          # the higher walked price
# the shadow feeds liveshadow.compare
live = [{"ticker": "KXBBB15M-1", "side": "yes", "count": 10, "orderedCount": 10, "fill": 0.13, "sentAtMs": (C - 174) * 1000}]
cm = ls.compare(live, list(B), b, {"KXBBB15M-1": [poll(C - 175, no=[(0.88, 20)])]})
assert cm["agree"] == 1 and cm["codes"]["AGREE"] == 1 and abs(cm["fill_gap"]["mean_cents"] - 1.0) < 1e-9, cm
print("test_oicore_shadow: all checks passed")
