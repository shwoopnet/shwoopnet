"""python3 -I spec_check_test.py"""
import os, sys, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as C
here = os.path.dirname(os.path.abspath(__file__))
hb = json.load(open(os.path.join(here, "specs", "HOURBRIDGE1.spec.json"))); gr = json.load(open(os.path.join(here, "specs", "EXAMPLE_GRID15M.spec.json")))
p, r = C.check(hb); assert p == [] and r == 1, (p, r)
p, r = C.check(gr); assert p == [] and r == 2 * 2 * 1 * 2 * 4 * 2, (p, r)       # buckets 2 x bands 2 x sides 1 x exits 2 x (none 1 + oi3 3) = 32 per series, times the 2 series in the wall = 64
x = copy.deepcopy(gr); x["tries"]["rules_this_spec"] = 63; assert any("rules_this_spec" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); del x["prediction"]; assert any("prediction" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["grid"]["exits"].append("ZZ"); assert any("exits" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["grid"]["buckets"] = [45]; assert any("buckets" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["data"]["loader_sha256"] = "abc"; assert any("loader_sha256" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["gates"]["pf_primary"] = 0.9; assert any("pf_primary" in q for q in C.check(x)[0])
pp = copy.deepcopy(gr); pp["kind"] = "perps_grid"; pp["grid"] = {"side_rules": ["long", "short"], "filters": ["none", "mom1"], "exits": ["T3", "T60", "TC"]}; pp["tries"]["rules_this_spec"] = 2 * 3 * (1 + 2) * 2
assert C.check(pp) == ([], 36)
x = copy.deepcopy(hb); del x["holds"]; assert any("holds" in q for q in C.check(x)[0])
x = copy.deepcopy(hb); x["holds"][0]["start_epoch"] = "2026-11-02"; assert any("integer epoch" in q for q in C.check(x)[0])
x = copy.deepcopy(hb); x["sources"]["new_host"] = True; assert any("new_host" in q for q in C.check(x)[0])
x = copy.deepcopy(hb); del x["plugin"]["hand_case_sha256"]; assert any("hand_case_sha256" in q for q in C.check(x)[0])
x = copy.deepcopy(hb); x["fee_form"] = "fee"; assert any("fee_form" in q for q in C.check(x)[0])
x = copy.deepcopy(hb); x["event"] = {}; assert any("event" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["data"]["ticker_wall"] = ["A", "B", "C", "D"]; x["tries"]["rules_this_spec"] = 32 * 4; assert C.check(x) == ([], 128)      # the grid is counted once per series
x = copy.deepcopy(gr); x["data"]["ticker_wall"] = "A, B, C"; x["tries"]["rules_this_spec"] = 32; assert any("rules_this_spec" in q for q in C.check(x)[0]) and C.check(x)[1] == 96   # an old per-series count is refused
print("ALL OK")
