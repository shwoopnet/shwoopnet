#!/usr/bin/env python3
"""Runs egh.py on the hand files and checks every expected figure in HAND_CASE.md. Usage: python3 -I test_egh.py"""
import io, contextlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import egh
with contextlib.redirect_stdout(io.StringIO()):
    o = egh.main(os.path.join(HERE, "hand"))
# Amendment 1 (cut at 2026-11-05T00:00Z)
assert o["counts"] == {"listed": 9, "cut_dropped": 4, "dropped_no_result": 0, "dropped_gap": 1, "no_look": 1, "no_band": 1, "entries": 2}, o["counts"]
assert (o["raw"]["pf"], o["raw"]["half1"], o["raw"]["half2"], o["raw"]["net"]) == (0.0737, "inf", 0.0, -0.88), o["raw"]
assert (o["1c"]["pf"], o["1c"]["half1"], o["1c"]["half2"], o["1c"]["net"]) == (0.0625, "inf", 0.0, -0.9), o["1c"]
assert (o["2c"]["pf"], o["2c"]["half1"], o["2c"]["half2"], o["2c"]["net"]) == (0.0515, "inf", 0.0, -0.92), o["2c"]
assert o["bar"] == "does not count: fails the haircut" and o["label"].startswith("book replay")
# Auditor B's fix 1: the bar is judged unrounded; 1.29996 rounds to 1.3 but fails, 1.30004 passes
assert egh.bar_ok(1.29996, 1.2, 1.4, 1.1) is False and egh.shown(1.29996) == 1.3
assert egh.bar_ok(1.30004, 1.2, 1.4, 1.1) is True
assert egh.bar_ok(1.30004, 0.99996, 1.4, 1.1) is False and egh.bar_ok(1.30004, 1.2, 1.4, 0.99996) is False
assert egh.bar_ok(float("inf"), float("inf"), 1.0, 1.0) is True and egh.bar_ok(None, 1.2, 1.4, 1.1) is False
assert "not a total" in o["window"]
print("hand case: all expected figures match")
