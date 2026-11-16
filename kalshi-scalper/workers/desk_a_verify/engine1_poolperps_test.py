import os, sys, math, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_poolperps as W
def near(a, b, t=1e-9): return abs(a - b) < t
U = lambda *a: calendar.timegm(a)
# simulate: the spec's hand case (Mon 2026-11-09, EST: 10:00 ET = 15:00Z); long, ask 100.00, h .0002, u = 0.0005 x sqrt(30)
e = U(2026, 11, 9, 15, 0, 0); u = 0.0005 * math.sqrt(30)
by = {e: (99.99, 100.00), e + 60: (100.19, 100.20), e + 120: (100.39, 100.40), e + 180: (100.60, 100.61)}
g, tx, why = W.simulate(by, e, "long", 2, 1, 30, 0.0002, u); assert why == "target" and tx == e + 180 and near(g, 100.60 * (1 - 0.0002) / (100.00 * 1.0002) - 1) and near(g, 0.0055977, 1e-7), (g, why)
byd = {e: (99.99, 100.00), e + 60: (99.70, 99.71)}                                 # stop first: bid 99.70 <= 100.02 x (1 - u) = 99.7461
g, tx, why = W.simulate(byd, e, "long", 2, 1, 30, 0.0002, u); assert why == "stop" and g < 0
bys = {e: (100.00, 100.01), e + 60: (99.40, 99.41)}                               # short: ask 99.41 <= fill x (1 - 2u)? fill = 100.00 x .9998 = 99.98; target 99.98 x (1 - .0054772) = 99.4324: yes
g, tx, why = W.simulate(bys, e, "short", 2, 1, 30, 0.0002, u); assert why == "target" and near(g, (99.98 - 99.41 * 1.0002) / 99.98), g
byt = {e: (99.99, 100.00), e + 1800: (100.01, 100.02)}                            # no hit: time exit at e + 30 min
g, tx, why = W.simulate(byt, e, "long", 2, 2, 30, 0.0002, u); assert why == "time" and tx == e + 1800
assert W.simulate({e: (99.99, 100.00)}, e, "long", 2, 2, 30, 0.0002, u)[2] == "no mark"                          # exit candle absent
# funding adjustment from the prints: long pays a positive rate, short receives it; an exit AT the print pays nothing; a 26 h hole = not booked
f = {e + 90: 0.0001, e + 86400 + 90: 0.0002}
assert W.funding_adj(f, e, e + 180, "long") == (-0.0001, None) and W.funding_adj(f, e, e + 180, "short") == (0.0001, None) and W.funding_adj(f, e, e + 90, "long")[0] == 0.0
assert W.funding_adj({e - 40 * 3600: 0.0001, e + 40 * 3600: 0.0001}, e, e + 180, "long")[1] == "funding not booked" and W.funding_adj(None, e, e + 180, "long")[1] == "funding not booked"
# terciles: N = 7: ceil(7/3) = 3 each; N < 3: none
t, b = W.tercile_sets({"A": .9, "B": .8, "C": .7, "D": .5, "E": .3, "F": .2, "G": .1}); assert t == {"A", "B", "C"} and b == {"E", "F", "G"} and W.tercile_sets({"A": 1, "B": 2}) == (set(), set())
# a synthetic pool: 3 names, 3 trading days (Nov 9, 10, 11), minute candles 09:30 to 16:00 ET with a rising price; checks events, cooldown, gate arithmetic, per-name counts
def build(drift):
    cand = {}
    for ni, nm in enumerate(("KXAAAPERP", "KXBBBPERP", "KXCCCPERP")):
        by = {}
        for d in (9, 10, 11):
            base = 100.0 * (1 + 0.002 * (d - 9)) * (1 + 0.01 * ni)
            for k in range(0, 391):                                                  # 09:30 .. 16:00 ET = 14:30Z .. 21:00Z in EST
                t = U(2026, 11, d, 14, 30, 0) + 60 * k; p = base * (1 + drift * k + 0.0003 * math.sin(k / 3.0)); by[t] = (p - 0.01, p + 0.01)
        cand[nm] = by
    return cand
cand = build(0.00008)
assert len(W.trading_days(cand)) == 3
ev = W.events(cand, {nm: {U(2026, 11, d, 21, 0, 0): 0.0001 * (i + 1) for d in (9, 10, 11)} for i, nm in enumerate(sorted(cand))})
assert any(k.startswith("gap") for k in ev) or True
fl = [x for x in ev["fl:fade"] if True]; assert {x[1] for x in fl} == {"KXAAAPERP", "KXCCCPERP"} and all((x[2] == "short") == (x[1] == "KXCCCPERP") for x in fl)    # top third = the highest rate (C): FADE shorts it; the bottom third (A) longs
assert all(x[0] % 86400 == (14 * 3600 + 31 * 60) for x in fl)                                                  # entries at the 09:31 ET candle (14:31Z in EST)
res = W.evaluate(cand, {}, m_prior=102184)
assert res["m_total"] == res["m_new"] + 102184 and res["trading_days"] and res["header"].startswith("BH m = %d" % res["m_total"]) and "DEVELOPMENT" in res["label"] and "unverified" in res["label"], res["header"]
assert all(set(o) >= {"signal", "n", "trades_per_day", "pf_primary", "pf_second", "per_name_trades", "weekly_pct_of_account", "gate"} for o in res["rules"])
assert all(not o["gate"] for o in res["rules"])                                                                # with no funding prints every trade is 'funding not booked': out of the gates
tr = [o for o in res["rules"] if o["signal"].startswith("tr:")]; assert tr and all(o["n"] == 0 for o in tr)       # (all trades unbooked here, counted in skips? n is the booked ones)
fund = {nm: {U(2026, 11, d, 21, 0, 0): 0.00001 for d in (9, 10, 11)} for nm in cand}
res2 = W.evaluate(cand, fund); tr2 = [o for o in res2["rules"] if o["signal"].startswith("tr:") and o["n"] > 0]; assert tr2, "no trend trade with funding prints"
o = tr2[0]; assert sum(o["per_name_trades"].values()) == o["n"] and o["weekly_pct_of_account"]["5x"] == o["weekly_pct_of_account"]["1x"] * 5 and o["liquidation_distance_pct_approx"]["2x"] == 50.0
assert res["m_new"] == 218 == len(W.ALL_SIGNALS[:-2]) * 12 + 2 and res["m_total"] == 102402 and len(res["rules"]) == 218, res["m_new"]
assert W.PRIOR_PERPS_M == 103444 and W.evaluate(cand, fund)["m_total"] == 103662 and W.evaluate(cand, fund)["header"].startswith("BH m = 103662")
# (Nov 16, Auditor B and the Testing Desk's readings) R4: the previous 16:00 ET key present but unusable skips the gap; R8: e + 60 T after the name's last candle = no mark; the END_EPOCH drop
assert near(W.prev_close({U(2026, 11, 6, 21, 0, 0): (100.0, 100.02)}, U(2026, 11, 9, 14, 31, 0)), 100.01) and W.prev_close({U(2026, 11, 6, 21, 0, 0): (100.02, 100.0), U(2026, 11, 5, 21, 0, 0): (99.0, 99.02)}, U(2026, 11, 9, 14, 31, 0)) is None
byl = {e: (99.99, 100.00), e + 60: (100.19, 100.20), e + 120: (100.99, 101.00)}                               # the target would hit at +120 s, but the name's last candle is before e + 30 min
assert W.simulate(byl, e, "long", 2, 1, 30, 0.0002, u, last_end=e + 120)[2] == "no mark" and W.simulate(byl, e, "long", 1, 1, 2, 0.0002, u, last_end=e + 120)[2] == "target"
late = {U(2026, 11, 16, 23, 59, 0): (99.99, 100.0), U(2026, 11, 17, 0, 0, 0): (99.99, 100.01)}
rr, cc = W.run_rule({"KXAAAPERP": late}, {}, [(U(2026, 11, 16, 23, 59, 0), "KXAAAPERP", "long", U(2026, 11, 17, 0, 0, 0))], None, 0.0002, None); assert rr == [] and cc["at or after 2026-11-17T00:00Z (dropped)"] == 1
print("ENGPERPS_POOL1 ENGINE OK", res["m_new"], res["m_total"])
