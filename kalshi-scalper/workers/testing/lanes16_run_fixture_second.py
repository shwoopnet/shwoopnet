#!/usr/bin/env python3
"""python3 -B lanes16_run_fixture_second.py fixture.json -> the driver's lines on the fixture (page max 10.0 for every name: a fixture table)."""
import json, sys
import lanes16_driver_second as D
fx = json.load(open(sys.argv[1]))
data = {n: {int(t): tuple(c) for t, c in s.items()} for n, s in fx["data"].items()}; fund = {n: {int(t): r for t, r in f.items()} for n, f in fx["funding"].items()}
print("\n".join(D.run(data, fund, {n: 10.0 for n in data}, 6290660)))
