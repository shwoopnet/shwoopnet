"""Hand case in PREDRIFT1_CARD_NOV16.md, invented rows. Run: python3 -I test_predrift1.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import predrift1 as P
I = P.I
A = lambda x, y: abs(x - y) < 1e-12
tip = 1794200000; H = 3600; m = 60
e = P.entry([(tip - 6 * H - 5 * m, 0.40, 0.42), (tip - H - 2 * m, 0.47, 0.49)], tip)
assert e[:2] == ("yes", 0.49) and A(e[2], 0.07) and A(I.net(0.49, 0.02, "yes", "yes", 1), 0.47) and A(I.net(0.49, 0.02, "no", "yes", 1), -0.53)
assert P.entry([(tip - 6 * H - 15 * m, 0.40, 0.42), (tip - H - 2 * m, 0.47, 0.49)], tip) is None
assert P.entry([(tip - 6 * H - 5 * m, 0.40, 0.42), (tip - H - 2 * m, 0.43, 0.45)], tip) is None
assert P.entry([(tip - 6 * H - 5 * m, 0.70, 0.72), (tip - H - 2 * m, 0.85, 0.87)], tip) is None
assert P.entry([(tip - 6 * H - 5 * m, 0.40, 0.42), (tip - H - 2 * m, 0.30, 0.32)], tip)[:2] == ("no", 0.70)
assert P.pick({"B": 1, "A": 2}, "ml", "NHL") == {"A": 2} and P.pick({"A": 1}, "ml", "NBA") == {} and P.pick({"T": 1}, "total", "NBA") == {"T": 1}
print("predrift1: ok")
assert P.schedule_ok({"2026-11-12T06:00:00Z"}) and P.schedule_ok({"2026-11-12T06:05:00Z"}) and P.schedule_ok({"2026-11-12T06:30:00Z"})
assert not P.schedule_ok({"2026-11-12T04:15:00Z"}) and not P.schedule_ok({"2026-11-12T06:00:00Z", "2026-11-12T06:30:00Z"}) and not P.schedule_ok({None})
print("schedule test: ok")
assert P.schedule_ok({"2026-11-10T04:15:00Z"}, "KXNFL") and not P.schedule_ok({"2026-11-10T04:15:00Z"}, "KXNHL") and not P.schedule_ok({"2026-11-10T04:10:00Z"}, "KXNFL")
assert not P.schedule_ok({"2026-11-10T04:15:00Z", "2026-11-10T04:20:00Z"}, "KXNFL")
print("nfl minutes: ok")
