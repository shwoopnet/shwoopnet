import math, engine1_perps_driver_second as d, engine1_perps_second as p
# option counts (hand case): none 1, mom 2 each, spread 3, tod 5, orb 2, sess 2
sp1 = {"grid": {"filters": ["none", "mom1", "spread", "orb"], "side_rules": ["long", "short"], "exits": ["T3", "TC", "TS15"]}}
assert len(d.rules(sp1)) == 48 and len(d.rules({"grid": {"filters": ["none", "tod", "sess", "mom15"], "side_rules": ["long"], "exits": ["T30", "T60", "T240", "TO"]}})) == 40
assert d.rules(sp1)[0] == ("none", "long", "T3") and ("orb_down", "short", "TS15") in d.rules(sp1)
# a rising series: every minute the mid grows by 0.2% from 100; bid and ask are mid x (1 -/+ 5e-6); 14 days of 1440 candles, ts 0, 60, ...
N = 14 * 1440; ser = {}
for i in range(N): m = 100.0 * 1.002 ** i; ser[i * 60] = (m * (1 - 5e-6), m * (1 + 5e-6))
spec = {"kind": "perps_grid", "grid": {"filters": ["none"], "side_rules": ["long", "short"], "exits": ["T3"]}, "costs": {"haircuts_primary": [0.0002, 0.0005], "haircuts_stress": [0.001, 0.002]}, "gates": {"min_n": 100, "pf_primary": 1.3, "pf_secondary": 1.0, "min_trade_days": 3, "bh_alpha": 0.05}}
B = 11 * 86400
out = d.run_spec(spec, {"KXRISE": ser}, {"KXRISE": B}, None, prior_m=1000)
assert out["m"] == 1002 and out["rules_per_name"] == 2 and out["search_passes"] == [("KXRISE", "none", "long", "T3")] and out["validate_passes"] == out["search_passes"] and out["stress_passes"] == 0, out          # hand: at 0.2% a minute the 0.2% haircut pair gives gross 0.1985% < 0.24%: the stress pair fails
assert len(out["survivors"]) == 1 and out["survivors"][0]["n"] == 144 and out["survivors"][0]["days"] == 3 and out["survivors"][0]["pf_lo"] == math.inf and out["survivors"][0]["p"] is not None and out["search_n"][("KXRISE", "none", "long", "T3")] == 528
# two names: m = prior + 2 names x 2 rules
o2n = d.run_spec(spec, {"KXRISE": ser, "KXRISE2": ser}, {"KXRISE": B, "KXRISE2": B}, None, prior_m=1000); assert o2n["m"] == 1004 and len(o2n["search_passes"]) == 2
# the clip applies to SEARCH entries only: B = 11 days + 100 s: the entry at exactly 11 days has horizon + 180 s past B and is clipped (529 attempts, 528 kept); VALIDATE starts at B and is not clipped
B2 = B + 100
o4 = d.run_spec(spec, {"KXRISE": ser}, {"KXRISE": B2}); assert o4["search_n"][("KXRISE", "none", "long", "T3")] == 528 and o4["survivors"][0]["n"] == 144          # hand: VALIDATE entries from 950520 every 1800 s, exit +180 within the last candle 1209540: k = 0..143
# VALIDATE rules only on VALIDATE trades: rising for 11 days then falling: long passes SEARCH and fails VALIDATE, so no validate pass
mixed = {i * 60: ((100.0 * 1.002 ** min(i, 11 * 1440) * 0.998 ** max(0, i - 11 * 1440)) * (1 - 5e-6), (100.0 * 1.002 ** min(i, 11 * 1440) * 0.998 ** max(0, i - 11 * 1440)) * (1 + 5e-6)) for i in range(N)}
om = d.run_spec(spec, {"KXM": mixed}, {"KXM": B}); assert ("KXM", "none", "long", "T3") in om["search_passes"] and ("KXM", "none", "long", "T3") not in om["validate_passes"] and ("KXM", "none", "short", "T3") not in om["search_passes"]
# the p handed to BH comes from the net at the taker fee, and the funding rates are used (a T240 hold crosses the 21:00 print: 66 booked trades with rates, 55 without)
seen = []; real = d.day_p; d.day_p = lambda tr, key: (seen.append(key), 0.0)[1]
d.run_spec(spec, {"KXRISE": ser}, {"KXRISE": B}); d.day_p = real; assert seen == ["net_taker"]
sp4 = dict(spec, grid={"filters": ["none"], "side_rules": ["long"], "exits": ["T240"]}, gates=dict(spec["gates"], min_n=60))
rates = {dd: 0.0001 for dd in range(0, 14)}
assert len(d.run_spec(sp4, {"KXRISE": ser}, {"KXRISE": B}, {"KXRISE": rates})["search_passes"]) == 1 and d.run_spec(sp4, {"KXRISE": ser}, {"KXRISE": B}, None)["search_passes"] == []
# the spread cut points come from the SEARCH half only: the driver asks spread_cuts for the candles before B and nothing later
calls = []; real_sc = p.spread_cuts; p.spread_cuts = lambda ser, lo, hi: (calls.append((lo, hi)), real_sc(ser, lo, hi))[1]
try: d.run_spec(dict(spec, grid={"filters": ["spread"], "side_rules": ["long"], "exits": ["T3"]}), {"KXRISE": ser}, {"KXRISE": B})
finally: p.spread_cuts = real_sc
assert calls == [(-math.inf, B)], calls
ser3 = {i * 60: (100.0 * 1.003 ** i * (1 - 5e-6), 100.0 * 1.003 ** i * (1 + 5e-6)) for i in range(N)}
o3 = d.run_spec(spec, {"KXRISE": ser3}, {"KXRISE": B}); assert o3["search_passes"] == [("KXRISE", "none", "long", "T3")] and o3["stress_passes"] == 1          # hand: at 0.3% a minute even the 0.2% haircut leaves gross 0.4986% > 0.24%
# the gate: min_n 529 fails SEARCH; min trade days 12 fails
for kw in ({"min_n": 529}, {"min_trade_days": 12}):
    sp = dict(spec, gates=dict(spec["gates"], **kw)); assert d.run_spec(sp, {"KXRISE": ser}, {"KXRISE": B})["search_passes"] == []
# the primary pair must both hold: at 0.1% a minute the 0.02% line is positive (net +0.0192%) and the 0.05% line negative (-0.0410%)
ser1 = {i * 60: (100.0 * 1.001 ** i * (1 - 5e-6), 100.0 * 1.001 ** i * (1 + 5e-6)) for i in range(N)}
assert d.run_spec(spec, {"KXRISE": ser1}, {"KXRISE": B})["search_passes"] == []
# a falling series: only the short rule passes, not the long
serd = {i * 60: (100.0 * 0.998 ** i * (1 - 5e-6), 100.0 * 0.998 ** i * (1 + 5e-6)) for i in range(N)}
o2 = d.run_spec(spec, {"KXFALL": serd}, {"KXFALL": B}); assert o2["search_passes"] == [("KXFALL", "none", "short", "T3")] and len(o2["survivors"]) == 1
# BH inside the driver: with the p stubbed to 0.03: m 1002 and m 2 reject it (0.03 > 0.05 / 2 = 0.025), m 1 keeps it
real = d.day_p; d.day_p = lambda tr, key: 0.03
try:
    assert d.run_spec(spec, {"KXRISE": ser}, {"KXRISE": B}, None, prior_m=1000)["survivors"] == [] and d.run_spec(spec, {"KXRISE": ser}, {"KXRISE": B}, None, prior_m=0)["survivors"] == []
    one = dict(spec, grid=dict(spec["grid"], side_rules=["long"]))
    assert len(d.run_spec(one, {"KXRISE": ser}, {"KXRISE": B}, None, prior_m=0)["survivors"]) == 1          # m = 1: 0.03 <= 0.05
finally: d.day_p = real
assert any(l.startswith("BH survivors 1") for l in d.report(out)) and d.report(out)[0].startswith("m 1002 (rules per name 2, names KXRISE)")
# VALIDATE also needs both primary haircuts: SEARCH rises 0.2% a minute, VALIDATE 0.1% (0.02% line positive, 0.05% line negative): passes SEARCH, fails VALIDATE
def grow(i):
    k = 11 * 1440; return 100.0 * 1.002 ** min(i, k) * 1.001 ** max(0, i - k)
slow = {i * 60: (grow(i) * (1 - 5e-6), grow(i) * (1 + 5e-6)) for i in range(N)}
osl = d.run_spec(spec, {"KXSLOW": slow}, {"KXSLOW": B}); assert osl["search_passes"] == [("KXSLOW", "none", "long", "T3")] and osl["validate_passes"] == []
print("engine1 perps driver second tests passed")
