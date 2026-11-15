"""python3 -I cfrtik_place_model_test.py : parity with the 20 committed vectors and the missing-data cases (invented)."""
import os, sys, json, math
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import cfrtik_place_model as M
V = json.load(open(os.path.join(here, "..", "DESK_A_CFRTI_K_PARITY_VECTORS.json")))["vectors"]
for v in V:
    by = {m["end_ts"]: m["price"] for m in v["marks"]}; D = v["decision_ts"]
    marks = [by.get(D - 60 * k) for k in range(11)]; om = v["open_mark"]["price"] if v.get("open_mark") else None
    d, why = M.decide(v["floor_strike"], v.get("yes_bid"), v.get("yes_ask"), marks, om)
    if v["reason"] == "trade":
        assert why == "trade" and d["side"] == v["side"], (v["case"], why, d)
        assert abs(d["edge"] - v["edge"]) < 1e-12 and abs(d["sd"] - v["sd"]) < 1e-15, (v["case"], d["edge"], v["edge"])
    else:
        assert d is None, (v["case"], why, v["reason"])
print("parity: %d vectors OK" % len(V))
marks = [100.0 + 0.01 * k for k in range(11)]
assert M.decide(77000.0, 0.20, 0.21, marks, 100.0)[1] in ("trade", "no edge", "no volatility")
assert M.decide(77000.0, 0.20, 0.21, [None] + marks[1:], 100.0)[1] == "no mark 0"
assert M.decide(77000.0, 0.20, 0.21, marks, None)[1] == "no opening mark"
assert M.decide(77000.0, 0.20, 0.21, marks[:5] + [None] * 6, 100.0)[1] == "under 6 changes"
assert M.decide(None, 0.20, 0.21, marks, 100.0)[1] == "no strike"
assert M.decide(77000.0, 0.20, 0.25, marks, 100.0)[1] == "spread over 3c or crossed"
assert M.decide(77000.0, 0.50, 0.51, marks, 100.0)[1] == "not cheap"
assert M.decide(77000.0, None, 0.21, marks, 100.0)[1] == "no quote"
assert M.mark(0, 5) is None and M.mark("", 5) is None and abs(M.mark(1, 3) - 20000.0) < 1e-9
print("ALL OK")
