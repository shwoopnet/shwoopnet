#!/usr/bin/env python3
"""Runs egh.py on the hand files and checks every expected figure in HAND_CASE.md. Usage: python3 -I test_egh.py"""
import io, contextlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import egh
with contextlib.redirect_stdout(io.StringIO()):
    o = egh.main(os.path.join(HERE, "hand"))
assert o["counts"] == {"listed": 9, "cut_dropped": 2, "dropped_no_result": 1, "dropped_gap": 1, "no_look": 1, "no_band": 1, "entries": 3}, o["counts"]
assert (o["raw"]["pf"], o["raw"]["half1"], o["raw"]["half2"], o["raw"]["net"]) == (0.0947, "inf", 0.0211, -0.86), o["raw"]
assert (o["1c"]["pf"], o["1c"]["half1"], o["1c"]["half2"], o["1c"]["net"]) == (0.0729, "inf", 0.0104, -0.89), o["1c"]
assert (o["2c"]["pf"], o["2c"]["half1"], o["2c"]["half2"], o["2c"]["net"]) == (0.0515, "inf", 0.0, -0.92), o["2c"]
assert o["bar"] == "does not count: fails the haircut" and o["label"].startswith("book replay")
print("hand case: all expected figures match")
