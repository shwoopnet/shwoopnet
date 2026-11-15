"""python3 -I calib3_stats_test.py : the hand case of CALIB3_HAND_CASE_NOV15.md."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib3_stats as C
ok = lambda a, b, t=1e-9: abs(a - b) < t
r = C.bucket_stats([("E1", 0.52, 1), ("E1", 0.53, 0), ("E2", 0.51, 1), ("E2", 0.54, 1)])
assert r["n"] == 4 and r["wins"] == 3 and ok(r["w"], 0.75) and ok(r["mean_ask"], 0.525) and ok(r["gap"], 0.225) and ok(r["fee"], 0.02) and r["events"] == 2
assert ok(r["event_z"], 0.9, 1e-9), r["event_z"]
assert ok(r["sd_null"], 0.35311, 1e-4) and ok(r["p_pass_third"], 0.4549, 1e-3), (r["sd_null"], r["p_pass_third"])
assert r["evidence"].startswith("no evidence")
assert C.bucket_stats([("E1", 0.52, 1), ("E1", 0.53, 0)])["event_z"] is None                       # one event
assert C.bucket_stats([("E1", 0.5, 1), ("E2", 0.5, 1)])["event_z"] is None                         # equal s_e: sd 0
assert C.bucket(0.50) == 10 and C.bucket(0.55) == 11 and C.bucket(0.5499999999) == 10 and C.bucket(1.0) == 19 and C.bucket(0.0) == 0
assert C.bucket_stats([(i, 0.5, i % 2) for i in range(60)])["evidence"] == "ok"
print("ALL OK")
