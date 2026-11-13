#!/usr/bin/env python3
"""Checks the TEMPBLEND scorer on invented rows only. No network, no data. [research]"""
import json, math, os, sys, tempfile
from datetime import datetime, timedelta, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tempblend_score as T

def same(got, path):
    want = json.load(open(os.path.join(HERE, path)))
    assert json.loads(json.dumps(got, sort_keys=True)) == want, "fixture output changed: " + path

rows = json.load(open(os.path.join(HERE, "test_rows.json")))
watched = json.load(open(os.path.join(HERE, "test_watched.json")))
same(T.score(rows, watched, "dev"), "test_expected_dev.json")
same(T.score(rows, watched, "held"), "test_expected_held.json")

def synth(start, n, won_every, calib_days, ask=0.50, step_hours=1):
    out, t0 = [], datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    for i in range(n):
        S = t0 + timedelta(hours=i * step_hours)
        Sms = int(S.timestamp() * 1000)
        res = "yes" if i % won_every == 0 else "no"
        out.append({"city": "AAA", "S": S.strftime("%Y-%m-%dT%H:%M:%SZ"), "t_ms": Sms - 1200000,
                    "v": 61.4, "calib_effective_ms": Sms - calib_days * 86400000,
                    "stations": [{"station_id": "S1", "temp_f": 60.7, "code": "ok", "obs_time_ms": Sms - 1200000}],
                    "strikes": [{"K": 61, "yes_bid": ask - 0.02, "yes_ask": ask, "result": res}]})
    return out
W = {"AAA": "S1"}
n = 0
# 1. Dev with 260 bets, all winning: CONTINUE.
r = T.score(synth("2026-09-14T00:00:00Z", 130, 1, 5) + synth("2026-10-10T00:00:00Z", 130, 1, 5), W); n += 1
assert r["dev_verdict"] == "CONTINUE", r["dev_verdict"]
# 2. Dev with 199 winning bets: CLOSED on count.
assert T.score(synth("2026-09-14T00:00:00Z", 199, 1, 5), W)["dev_verdict"] == "CLOSED"; n += 1
# 3. Held: 39 day2-onward bets that all lose -> calibration kill, whatever day 0 to 1 does.
r = T.score(synth("2026-11-13T00:00:00Z", 40, 10**9 + 1, 5)[1:] + synth("2026-11-20T00:00:00Z", 60, 1, 1), W, "held"); n += 1
assert r["held_verdict"] == "FAIL (calibration kill)", r["held_verdict"]
# 4. Held: 29 day2-onward bets -> no evidence.
assert T.score(synth("2026-11-13T00:00:00Z", 29, 1, 5), W, "held")["held_verdict"] == "NO_EVIDENCE at n = 29"; n += 1
# 5. Nov 5 to 11 rows are never scored.
assert T.score(synth("2026-11-05T00:00:00Z", 100, 1, 5), W)["skips"] == {"outside_windows": 100}; n += 1
# 6. A12: a void is a fee-only loss, counted as a bet (fee at 50c is 2c).
v = synth("2026-09-14T00:00:00Z", 1, 1, 5); v[0]["strikes"][0]["result"] = "void"
r = T.score(v, W); n += 1
assert r["dev"]["n"] == 1 and r["dev"]["void"] == 1 and r["dev"]["net"] == -0.02, r["dev"]
# 7. A17 and A1: an index point older than 10 minutes, or not yet published, is a skip.
v = synth("2026-09-14T00:00:00Z", 2, 1, 5)
v[0]["t_ms"] -= 6 * 60000
v[1]["t_ms"] += 6 * 60000
assert T.score(v, W)["skips"] == {"no_index_point": 2}; n += 1
# 8. A8: a quote is usable only if 0 < yes_bid < yes_ask < 1.
v = synth("2026-09-14T00:00:00Z", 1, 1, 5); v[0]["strikes"][0]["yes_bid"] = 0.0
assert T.score(v, W)["skips"] == {"no_strike": 1}; n += 1
# 9. A15: a calibration exactly 2 days before S is under 2 days at the decision: day 0 to 1.
assert T.score(synth("2026-11-13T00:00:00Z", 1, 1, 2), W, "held")["held_calib_day0_1"]["n"] == 1; n += 1
# 10. A7 and F4, Forensics' edge row T03: distances 0.4 and 0.4 on paper, not in floating point; the LOWER K wins.
v = synth("2026-09-14T00:00:00Z", 1, 1, 5)
v[0]["v"], v[0]["stations"][0]["temp_f"] = 70.7, 69.1
v[0]["strikes"] = [{"K": 69.5, "yes_bid": 0.43, "yes_ask": 0.45, "result": "yes"},
                   {"K": 70.3, "yes_bid": 0.53, "yes_ask": 0.55, "result": "no"}]
b, why = T.decide(v[0], W); n += 1
assert why is None and b["K"] == 69.5 and b["ask"] == 0.45, (b, why)
# 11. F1: the bar lines use unrounded values: PF 0.99996 closes, PF 1.49996 is not 1.5.
d = {"n": 500, "pf": 0.99996, "z": 9.0}; ok = {"n": 250, "pf": 2.0, "z": 9.0}; n += 1
assert T.dev_verdict(d, ok, ok) == "CLOSED"
almost = {"n": 250, "pf": 1.49996, "z": 9.0}
assert T.held_verdict("CONTINUE", ok, ok, almost, ok) == "FAIL"
assert T.held_verdict("CONTINUE", ok, ok, {"n": 250, "pf": 2.0, "z": 5.45996}, ok) == "FAIL"
assert T.held_verdict("CONTINUE", ok, ok, ok, ok) == "PASS"
# 12. F2: PASS needs the development read to CONTINUE.
assert T.held_verdict("CLOSED", ok, ok, ok, ok) == "FAIL"; n += 1
# 13. F3: dev mode ignores and counts held rows; held mode refuses before 2026-12-10 and refuses a second run.
r = T.score(synth("2026-11-13T00:00:00Z", 3, 1, 5), W, "dev"); n += 1
assert r["skips"] == {"held_window_ignored": 3} and "held" not in r and "held_verdict" not in r, r
try:
    T.held_guard(T.HELD_END - 1, "/nonexistent/marker"); raise AssertionError("held read allowed early")
except SystemExit as e:
    assert "opens at 2026-12-10" in str(e)
with tempfile.TemporaryDirectory() as tmp:
    mk = os.path.join(tmp, "marker")
    T.held_guard(T.HELD_END, mk)
    open(mk, "w").write("ran\n")
    try:
        T.held_guard(T.HELD_END + 1, mk); raise AssertionError("second held read allowed")
    except SystemExit as e:
        assert "already ran" in str(e)
# 14. F5: a second row for the same city and S is refused.
v = synth("2026-09-14T00:00:00Z", 1, 1, 5); n += 1
try:
    T.score(v + v, W); raise AssertionError("duplicate accepted")
except ValueError as e:
    assert "duplicate" in str(e)
# 15. F6: a result other than yes, no or void (including "" and None) is refused.
for bad in ("", None, "YES", "settled"):
    v = synth("2026-09-14T00:00:00Z", 1, 1, 5); v[0]["strikes"][0]["result"] = bad
    try:
        T.score(v, W); raise AssertionError("bad result accepted: %r" % bad)
    except ValueError as e:
        assert "not yes, no or void" in str(e)
n += 1
# 16. Q2: a Source A reading taken after t is a skip named obs_after_point.
v = synth("2026-09-14T00:00:00Z", 1, 1, 5); v[0]["stations"][0]["obs_time_ms"] = v[0]["t_ms"] + 1
assert T.score(v, W)["skips"] == {"obs_after_point": 1}; n += 1
# 17. Q1: z is clustered by US Central settlement day: 48 hourly bets over 2 UTC days span 3 Central days.
r = T.score(synth("2026-09-14T00:00:00Z", 48, 2, 5), W); n += 1
assert r["dev"]["days"] == 3, r["dev"]
print("tempblend scorer checks: %d scenarios and the two fixtures passed" % n)
