#!/usr/bin/env python3
"""The hand case for tape_count.py. Invented rows only. [research]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tape_count as T
got = T.count(os.path.join(HERE, "hand_case", "run"))
exp = json.load(open(os.path.join(HERE, "hand_case", "expected.json")))
for k in ("pages", "rows", "kxmve_rows", "kxmve_share"):
    assert got[k] == exp[k], (k, got[k], exp[k])
assert got["unreadable_pages"] == 0 and got["notes"] == []
print("tape_count hand case passed:", {k: got[k] for k in ("pages", "rows", "kxmve_rows", "kxmve_share")})
