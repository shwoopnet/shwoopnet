#!/usr/bin/env python3
"""Checks the TEMPBLEND scorer on invented rows only. No network, no data. [research]"""
import json, os, sys
from datetime import datetime, timedelta, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tempblend_score as T

rows = json.load(open(os.path.join(HERE, "test_rows.json")))
watched = json.load(open(os.path.join(HERE, "test_watched.json")))
got = json.loads(json.dumps(T.score(rows, watched), sort_keys=True))
want = json.load(open(os.path.join(HERE, "test_expected.json")))
assert got == want, "fixture output changed"

def synth(start, n, won_every, calib_days, ask=0.50):
    out, t0 = [], datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    for i in range(n):
        S = t0 + timedelta(hours=i)
        Sms = int(S.timestamp() * 1000)
        res = "yes" if i % won_every == 0 else "no"
        out.append({"city": "AAA", "S": S.strftime("%Y-%m-%dT%H:%M:%SZ"), "t_ms": Sms - 1200000,
                    "v": 61.4, "calib_effective_ms": Sms - calib_days * 86400000,
                    "stations": [{"station_id": "S1", "temp_f": 60.7, "code": "ok", "obs_time_ms": Sms - 1200000}],
                    "strikes": [{"K": 61, "yes_bid": ask - 0.02, "yes_ask": ask, "no_bid": 0.48, "no_ask": 0.52, "result": res}]})
    return out
W = {"AAA": "S1"}
# 1. Dev with 260 bets, all winning: CONTINUE.
r = T.score(synth("2026-09-14T00:00:00Z", 130, 1, 5) + synth("2026-10-10T00:00:00Z", 130, 1, 5), W)
assert r["dev_verdict"] == "CONTINUE", r["dev_verdict"]
# 2. Dev with 199 winning bets: CLOSED on count.
assert T.score(synth("2026-09-14T00:00:00Z", 199, 1, 5), W)["dev_verdict"] == "CLOSED"
# 3. Held: 40 day2-onward bets that all lose -> calibration kill, whatever day 0 to 1 does.
r = T.score(synth("2026-11-13T00:00:00Z", 40, 10**9 + 1, 5)[1:] + synth("2026-11-20T00:00:00Z", 60, 1, 1), W)
assert r["held_verdict"] == "FAIL (calibration kill)", r["held_verdict"]
# 4. Held: 29 day2-onward bets -> no evidence.
assert T.score(synth("2026-11-13T00:00:00Z", 29, 1, 5), W)["held_verdict"] == "NO_EVIDENCE at n = 29"
# 5. Nov 5 to 11 rows are never scored.
assert T.score(synth("2026-11-05T00:00:00Z", 100, 1, 5), W)["skips"] == {"outside_windows": 100}
# 6. A12: a void is a fee-only loss, counted as a bet (fee at 50c is 2c).
v = synth("2026-09-14T00:00:00Z", 1, 1, 5); v[0]["strikes"][0]["result"] = "void"
r = T.score(v, W)
assert r["dev"]["n"] == 1 and r["dev"]["void"] == 1 and r["dev"]["net"] == -0.02, r["dev"]
# 7. A17 and A1: an index point older than 10 minutes, or not yet published, is a skip.
v = synth("2026-09-14T00:00:00Z", 2, 1, 5)
v[0]["t_ms"] -= 6 * 60000          # 26 minutes before S: 11 minutes before the decision
v[1]["t_ms"] += 6 * 60000          # 14 minutes before S: published after the decision
assert T.score(v, W)["skips"] == {"no_index_point": 2}
# 8. A8: a quote is usable only if 0 < yes_bid < yes_ask < 1.
v = synth("2026-09-14T00:00:00Z", 1, 1, 5); v[0]["strikes"][0]["yes_bid"] = 0.0
assert T.score(v, W)["skips"] == {"no_strike": 1}
# 9. A15: a calibration exactly 2 days before S is under 2 days at the decision (S minus 15 min): day 0 to 1.
v = synth("2026-11-13T00:00:00Z", 1, 1, 2)
assert T.score(v, W)["held_calib_day0_1"]["n"] == 1
# 10. A7, Forensics' edge row T03: mid 69.9, distances 0.4 and 0.4 on paper but not in floating point; the LOWER K wins.
v = synth("2026-09-14T00:00:00Z", 1, 1, 5)
v[0]["v"], v[0]["stations"][0]["temp_f"] = 70.7, 69.1
v[0]["strikes"] = [{"K": 69.5, "yes_bid": 0.43, "yes_ask": 0.45, "result": "yes"},
                   {"K": 70.3, "yes_bid": 0.53, "yes_ask": 0.55, "result": "no"}]
b, why = T.decide(v[0], W)
assert why is None and b["K"] == 69.5 and b["ask"] == 0.45, (b, why)
print("tempblend scorer checks: 10 scenarios and the fixture passed")
