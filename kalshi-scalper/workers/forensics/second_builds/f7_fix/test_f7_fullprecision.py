#!/usr/bin/env python3
"""Hand case for f7 at full precision (F7_HAND_CASE.md). Invented trades only. usage: python3 -I test_f7_fullprecision.py  (run from this folder or anywhere)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import depth1_second as D
T = 1000000.0
C1 = [(990999600, 0.50, "yes"), (990400000, 0.51, "yes")]
C2 = [(940000000, 0.50, "yes"), (940000000, 0.51, "yes"), (940000001, 0.50, "yes"), (940000400, 0.52, "yes")]
C3 = [(1000000000, 0.60, "no"), (1000000001, 0.61, "no")]
C4 = [(960100000, 0.50004, "yes"), (960200000, 0.5000, "yes")]
C5 = [(970000000, 0.40, "yes"), (970500000, 0.41, "yes"), (980000000, 0.40, "no"), (980500000, 0.41, "no"), (981000000, 0.42, "no")]
cases = [("case 1", C1, 1.0), ("case 2", C2, 1.0), ("case 3", C3, 0.0), ("case 4", C4, 0.0), ("case 5", C5, 0.0), ("case 6", C1 + C2 + C3 + C4 + C5, 2.0)]
bad = 0
for name, tr, want in cases:
    got = D.f7(tr, T)
    print(name, "expected", want, "got", got, "OK" if got == want else "MISMATCH"); bad += got != want
print("ALL MATCH" if not bad else "%d MISMATCH" % bad); sys.exit(1 if bad else 0)
