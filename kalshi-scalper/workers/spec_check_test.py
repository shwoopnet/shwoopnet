"""python3 -I spec_check_test.py"""
import os, sys, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_check as C
here = os.path.dirname(os.path.abspath(__file__))
hb = json.load(open(os.path.join(here, "specs", "HOURBRIDGE1.spec.json"))); gr = json.load(open(os.path.join(here, "specs", "EXAMPLE_GRID15M.spec.json")))
p, r = C.check(hb); assert p == [] and r == 1, (p, r)
p, r = C.check(gr); assert p == [] and r == 2 * 2 * 1 * 2 * 4, (p, r)       # buckets 2 x bands 2 x sides 1 x exits 2 x (none 1 + oi3 3) = 32
x = copy.deepcopy(gr); x["tries"]["rules_this_spec"] = 31; assert any("rules_this_spec" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); del x["prediction"]; assert any("prediction" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["grid"]["exits"].append("ZZ"); assert any("exits" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["grid"]["buckets"] = [45]; assert any("buckets" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["data"]["loader_sha256"] = "abc"; assert any("loader_sha256" in q for q in C.check(x)[0])
x = copy.deepcopy(gr); x["gates"]["pf_primary"] = 0.9; assert any("pf_primary" in q for q in C.check(x)[0])
pp = copy.deepcopy(gr); pp["kind"] = "perps_grid"; pp["grid"] = {"side_rules": ["long", "short"], "filters": ["none", "mom1"], "exits": ["T3", "T60", "TC"]}; pp["tries"]["rules_this_spec"] = 2 * 3 * (1 + 2)
assert C.check(pp) == ([], 18)
x = copy.deepcopy(hb); x["event"] = {}; assert any("event" in q for q in C.check(x)[0])
print("ALL OK")
