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
print("tempblend scorer checks: 5 scenarios and the fixture passed")
