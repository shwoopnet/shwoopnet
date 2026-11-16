"""Hand case in IGTOTDOG1_CARD_NOV16.md, invented rows. Run: python3 -I test_igtotdog1.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import igtotdog1 as D
I = D.I
A = lambda x, y: abs(x - y) < 1e-12
B = 1794200000
r = lambda t, k, tk, b, a: (B + t, "KXNBAGAME-G1", k, tk, b, a)
ml = [r(0, "ml", "M", 0.5, 0.52), r(100, "ml", "M", 0.5, 0.52), r(120, "ml", "M", 0.5, 0.52)]
e = D.entry(ml, [r(110, "total", "T", 0.06, 0.08), r(130, "total", "T", 0.50, 0.52), r(140, "total", "T", 0.0, 0.05), r(150, "total", "T", 0.06, 0.08)])
assert e[:4] == ("T", "yes", 0.08, B + 150), e
assert A(I.net(0.08, 0.02, "yes", "yes", 1), 0.89) and A(I.net(0.08, 0.02, "no", "yes", 1), -0.11)
assert D.entry(ml, [r(130, "total", "T", 0.85, 0.88)])[1:3] == ("no", 0.15)
assert D.entry(ml, [r(130, "total", "T", 0.30, 0.32)]) is None and D.entry(ml[:1], [r(130, "total", "T", 0.06, 0.08)]) is None
print("igtotdog1: ok")
assert D.entry(ml, [r(180, "total", "T", 0.06, 0.08)])[4] == B + 120
print("amendment 1 fields: ok")
