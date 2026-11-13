#!/usr/bin/env python3
"""LIQREV build 1 checks: the hand case and the guards. Invented rows only. [research]"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import liqrev_score as T
case = json.load(open(os.path.join(HERE, "hand_case_rows.json")))
exp = json.load(open(os.path.join(HERE, "hand_case_expected.json")))
out = T.score(case, "dev")
assert out["skips"] == exp["skips"], out["skips"]
for g, e in zip(out["bets"], exp["bets"]):
    for k in ("ticker", "trigger_minute", "side", "ask", "fee", "pnl"):
        assert g[k] == e[k], (k, g[k], e[k])
    assert abs(g["L_btc"] - e["L_btc"]) < 1e-9
assert len(out["bets"]) == len(exp["bets"])
for k in ("n", "won", "void"): assert out["dev"][k] == exp["dev"][k]
assert out["dev"]["pf"] == exp["dev"]["pf"] and out["dev"]["net"] == exp["dev"]["net"], out["dev"]
assert out["dev_verdict"].startswith("CLOSED (zero-try") and out["dev_label"] == "no evidence at n = 2"
# guards
try: T.guard("dev", T.DEV_READ_FROM - 1); raise AssertionError
except SystemExit as e: assert "2026-11-30" in str(e)
try: T.guard("held", T.HELD_READ_FROM - 1, "/x"); raise AssertionError
except SystemExit as e: assert "2027-01-02" in str(e)
with tempfile.TemporaryDirectory() as d:
    m = os.path.join(d, "m"); T.guard("held", T.HELD_READ_FROM, m); open(m, "w").write("x")
    try: T.guard("held", T.HELD_READ_FROM, m); raise AssertionError
    except SystemExit as e: assert "already ran" in str(e)
# refusals
bad = json.loads(json.dumps(case)); bad["windows"][0]["result"] = ""
try: T.score(bad); raise AssertionError
except ValueError: pass
bad = json.loads(json.dumps(case)); bad["windows"].append(bad["windows"][0])
try: T.score(bad); raise AssertionError
except ValueError: pass
# coverage gap: drop the Nov 18 interval -> every dev window skipped for coverage
gap = json.loads(json.dumps(case)); gap["coverage"] = gap["coverage"][1:]
assert T.score(gap)["skips"].get("no_liq_coverage") == 5
print("liqrev build 1: hand case and 6 guard or refusal checks passed")
