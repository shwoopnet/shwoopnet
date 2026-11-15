"""python3 -I perpscalp1_test.py : the hand case of PERPSCALP1_HAND_CASE_NOV15.md on invented candles."""
import os, sys, time, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpscalp1 as P
t0 = calendar.timegm(time.strptime("2026-11-10T15:00:00Z", "%Y-%m-%dT%H:%M:%SZ"))          # a Tuesday
mids = [100.0 if m % 2 == 0 else 100.1 for m in range(60)] + [100.1, 100.1, 100.1, 100.2, 101.0, 101.1, 101.3, 101.3, 101.3, 101.3]
cs = [(t0 + 60 * m, x - 0.005, x + 0.005) for m, x in enumerate(mids)]
sg = list(P.signals(cs)); ok = lambda a, b, t=1e-6: abs(a - b) < t
assert len(sg) == 1 and sg[0][0] == 64 and sg[0][1] == 1 and ok(sg[0][2], 0.00225381, 1e-8) and ok(sg[0][3], 101.0, 1e-9), sg
for h, (rt, nt, rr, nr) in {0.0: (0.0028711, 0.0004711, -0.0030695, -0.0054695), 1e-4: (0.0026706, 0.0002706, -0.0032701, -0.0056701), 2e-4: (0.0024701, 0.0000701, -0.0034708, -0.0058708)}.items():
    e, x, k = P.trade(cs, 64, 1, sg[0][2], sg[0][3], h); assert k == "target" and ok((x - e) / e, rt, 1e-6) and ok(P.net(e, x, 1), nt, 1e-6), (h, e, x, k)
    e, x, k = P.trade(cs, 64, -1, sg[0][2], sg[0][3], h); assert k == "stop" and ok((e - x) / e, rr, 1e-6) and ok(P.net(e, x, -1), nr, 1e-6), (h, e, x, k)
e, x, k = P.trade(cs, 64, 1, sg[0][2], sg[0][3], 0.0); assert ok(e, 101.005, 1e-9) and ok(x, 101.295, 1e-9)
# outside the hours (same series shifted to 20:46Z start of the signal candle is out): shift so candle 64 ends 20:46Z
t1 = calendar.timegm(time.strptime("2026-11-10T19:42:00Z", "%Y-%m-%dT%H:%M:%SZ")); cs2 = [(t1 + 60 * m, x - 0.005, x + 0.005) for m, x in enumerate(mids)]
assert list(P.signals(cs2)) == [], "a signal at 20:46Z is outside the hours"
# a 5 minute move of 0.005 gives no signal
mids3 = [100.0 if m % 2 == 0 else 100.1 for m in range(60)] + [100.1] * 4 + [100.6] + [100.6] * 5
cs3 = [(t0 + 60 * m, x - 0.005, x + 0.005) for m, x in enumerate(mids3)]; assert list(P.signals(cs3)) == []
# the pause: with the same series the second candidate signals (m 65, 66) are inside the 15 minute pause
assert len(sg) == 1
# weekends are out
t4 = calendar.timegm(time.strptime("2026-11-14T15:00:00Z", "%Y-%m-%dT%H:%M:%SZ")); cs4 = [(t4 + 60 * m, x - 0.005, x + 0.005) for m, x in enumerate(mids)]
assert list(P.signals(cs4)) == []
assert P.day_z([(t0, 0.001), (t0 + 86400, -0.001), (t0 + 2 * 86400, 0.001)]) is not None and P.day_z([(t0, 0.001)]) is None
r = P.run({"KXSPYPERP": cs}); a = r["names"]["KXSPYPERP"]["arms"]
assert a["T"]["h0bp"]["n"] == 1 and ok(a["T"]["h0bp"]["net_sum"], 0.0004711, 1e-6) and ok(a["R"]["h2bp"]["net_sum"], -0.0058708, 1e-6) and a["T"]["h0bp"]["evidence"] == "no evidence at n = 1" and r["tries"] == 2 and r["names"]["KXNVDAPERP"] == {"no_data": True}
import subprocess; rr = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "perpscalp1.py"), "/tmp/x.json", "/tmp/none.gz"], capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
assert rr.returncode != 0 and "PERPSCALP_READ" in rr.stdout + rr.stderr
print("ALL OK")
