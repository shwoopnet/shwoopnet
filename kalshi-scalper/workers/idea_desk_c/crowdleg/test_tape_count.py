#!/usr/bin/env python3
"""Hand cases for tape_count.py version 2 (complete, stopped, truncated, corrupt page, wrong job) and the
guard. Invented rows only. [research]"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tape_count as T
exp = json.load(open(os.path.join(HERE, "hand_cases", "expected.json")))
for case in ("complete", "stopped", "truncated", "corrupt"):
    got = T.count(os.path.join(HERE, "hand_cases", case))
    for k in ("rows", "kxmve_rows", "kxmve_share", "unreadable", "labels"):
        assert got[k] == exp[case][k], (case, k, got[k], exp[case][k])
try:
    T.count(os.path.join(HERE, "hand_cases", "wrongjob")); raise AssertionError("wrong job accepted")
except SystemExit as e:
    assert "canonical hash" in str(e)
# guard: a HELDOUT_ folder name, and a run listed in the list file
with tempfile.TemporaryDirectory() as d:
    h = os.path.join(d, "HELDOUT_x"); os.makedirs(h)
    try: T.count(h); raise AssertionError
    except SystemExit as e: assert "HELDOUT_" in str(e)
    lst = os.path.join(d, "list.md")
    open(lst, "w").write("| Run folder (under `pull/`) | Job |\n|---|---|\n| `CROWDLEG_TAPE_TRIAL/2026-11-14T0100Z_1` | x |\n")
    r = os.path.join(d, "2026-11-14T0100Z_1"); os.makedirs(r)
    try: T.count(r, lst); raise AssertionError
    except SystemExit as e: assert "listed" in str(e)
    bad = os.path.join(d, "badlist.md"); open(bad, "w").write("no table\n")
    try: T.count(os.path.join(HERE, "hand_cases", "complete"), bad); raise AssertionError
    except SystemExit as e: assert "table header" in str(e)
print("tape_count v2: 5 hand cases and 3 guard checks passed")
