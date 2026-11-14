#!/usr/bin/env python3
"""Runs feasibility_count.py on the hand files and checks every expected count in HAND_CASE.md. Usage: python3 -I test_feasibility.py"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
out = json.loads(subprocess.run([sys.executable, "-I", os.path.join(HERE, "feasibility_count.py"), os.path.join(HERE, "hand"), "--complete-polls", "2"], capture_output=True, text=True, check=True).stdout)
d = out["days"]["2026-11-13"]
assert (d["polls"], d["rows"], d["listed_distinct"], d["two_sided_distinct"], d["qualifying_distinct"], d["qualifying_with_legs"]) == (2, 9, 8, 6, 4, 1), d
assert out["refused_unread"] == ["2026-11-26"] and "2026-11-26" not in out["days"]
assert out["avg_qualifying_per_complete_day"] == 4.0 and out["verdict"].startswith("CLOSE")
print("hand case: all expected counts match")
