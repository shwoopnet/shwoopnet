#!/usr/bin/env python3
"""TEMPBLEND scorer (Idea Desk C, Nov 13, 2026). Research only. [research]

Written before any data was read, and tested only on invented rows. It makes no
network request: it reads a JSON file of decision rows and a JSON map of the
watched station per city, and prints a JSON verdict. The rule is
TEMPBLEND_CARD.md (same branch); where the two differ, the card is right.

Usage: python3 -I tempblend_score.py ROWS.json WATCHED.json

WATCHED.json maps city -> station_id. It stays a parameter until probe A4 says
which station each city's daily high market names.

One row is one city-hour decision (the minute t that the rule reads):
  city, S (ISO UTC settlement time), t_ms (latest canonical index minute),
  v (index value, F), calib_effective_ms (effective_at_ms of the city's
  config_version at t), stations (index stations[] at t: station_id, temp_f,
  code, obs_time_ms), external (optional, source B: station_id -> {temp_f,
  obs_time_ms}), strikes (each: K, yes_bid, yes_ask in dollars from the candle
  ending at S minus 900 s, result "yes", "no" or anything else for a void, for
  "K or above").

Readings A1 to A18 are the card's Amendment 1 (ruled by the Head of R&D on
Nov 13, 2026); this file follows them. In short: band and spread first, then
the strike nearest (v + s) / 2, ties to the lower K (A6, A7); NO ask is
1 - yes_bid and the spread is yes_ask - yes_bid (A8); the fill is at the ask
seen with no +1c, plus the fee 0.07 x p x (1 - p) rounded up to the cent
(A10, an upper bound: live taker fills land 60% to 73% of the time); a void is
a fee-only loss counted as a bet (A12); the calibration split is measured at
the decision time (A15); no index point within 10 minutes of the decision is a
skip (A17).
"""
import json, math, sys
from datetime import datetime, timezone

def ms(iso):
    return int(datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000)

DEV_START = ms("2026-09-13T00:00:00Z")
DEV_SPLIT = ms("2026-10-09T00:00:00Z")
DEV_END = ms("2026-11-05T00:00:00Z")      # Nov 5 to 11: used by neither read
HELD_START = ms("2026-11-12T00:00:00Z")
HELD_END = ms("2026-12-10T00:00:00Z")

GAP_MIN = 0.5            # F
ASK_LO, ASK_HI = 0.20, 0.80
SPREAD_MAX = 0.04
READ_MAX_AGE_MS = 10 * 60 * 1000
DECISION_LEAD_MS = 15 * 60 * 1000   # decision at S minus 15 minutes
PUBLISH_LAG_MS = 300 * 1000         # a canonical point is published at t + 300 s
CALIB_SPLIT_MS = 2 * 24 * 3600 * 1000
DEV_MIN_BETS = 200
HELD_DAY2_MIN = 30
BAR_PF, BAR_Z = 1.5, 5.46
EPS = 1e-9

def fee(p):
    return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100

def window(S):
    if DEV_START <= S < DEV_SPLIT: return "dev1"
    if DEV_SPLIT <= S < DEV_END: return "dev2"
    if HELD_START <= S < HELD_END: return "held"
    return None

def watched_reading(row, sid):
    t = row["t_ms"]
    for st in row.get("stations", []):
        if st.get("station_id") == sid:
            if st.get("code") != "ok":
                return True, None, "member_not_ok"
            r = st
            member = True
            break
    else:
        member = False
        r = (row.get("external") or {}).get(sid)
        if r is None:
            return False, None, "no_reading"
    obs = r.get("obs_time_ms")
    if obs is None or r.get("temp_f") is None or obs > t or t - obs > READ_MAX_AGE_MS:
        return member, None, "stale_reading"
    return member, float(r["temp_f"]), None

def decide(row, watched):
    S = ms(row["S"])
    w = window(S)
    if w is None:
        return None, "outside_windows"
    decision = S - DECISION_LEAD_MS
    t = row.get("t_ms")
    if t is None or t > decision - PUBLISH_LAG_MS or decision - t > READ_MAX_AGE_MS:
        return None, "no_index_point"                       # A1, A17
    sid = watched.get(row["city"])
    if sid is None:
        return None, "no_watched_station"
    member, s, why = watched_reading(row, sid)
    if why:
        return None, why
    v = float(row["v"])
    g = v - s
    if abs(g) < GAP_MIN - EPS:
        return None, "gap_small"
    side = "yes" if g > 0 else "no"
    lo, hi = (s, v) if g > 0 else (v, s)
    mid = (v + s) / 2
    cands = []
    for k in row.get("strikes", []):
        K = float(k["K"])
        if not (lo < K <= hi):
            continue
        yb, ya = k.get("yes_bid"), k.get("yes_ask")
        if yb is None or ya is None or not (0 < yb < ya < 1):  # A2, A8
            continue
        ask = ya if side == "yes" else round(1 - yb, 6)
        if not (ASK_LO - EPS <= ask <= ASK_HI + EPS) or ya - yb > SPREAD_MAX + EPS:
            continue
        cands.append((round(abs(K - mid), 9), K, ask, k["result"]))   # A7: equal within 1e-9 goes to the lower K
    if not cands:
        return None, "no_strike"
    cands.sort()
    _, K, ask, result = cands[0]
    f = fee(ask)
    void = result not in ("yes", "no")                      # A12
    pnl = round(-f if void else ((1 - ask - f) if result == side else -(ask + f)), 4)
    calib = "day0_1" if decision - row["calib_effective_ms"] < CALIB_SPLIT_MS else "day2_on"   # A15
    return {"city": row["city"], "S": row["S"], "window": w, "side": side, "K": K,
            "ask": ask, "fee": f, "won": (not void) and result == side, "void": void, "pnl": pnl,
            "member": member, "calib": calib}, None

def stats(bets):
    n = len(bets)
    wins = sum(b["pnl"] for b in bets if b["pnl"] > 0)
    losses = -sum(b["pnl"] for b in bets if b["pnl"] < 0)
    pf = None if n == 0 else ("inf" if losses == 0 else round(wins / losses, 4))
    net = round(sum(b["pnl"] for b in bets), 4)
    z = None
    if n >= 2:
        m = net / n
        sd = math.sqrt(sum((b["pnl"] - m) ** 2 for b in bets) / (n - 1))
        z = None if sd == 0 else round(m / (sd / math.sqrt(n)), 4)
    return {"n": n, "won": sum(1 for b in bets if b["won"]), "void": sum(1 for b in bets if b["void"]),
            "pf": pf, "net": net, "z": z}

def pf_num(st):
    return math.inf if st["pf"] == "inf" else (st["pf"] if st["pf"] is not None else 0.0)

def score(rows, watched):
    bets, skips = [], {}
    for row in rows:
        b, why = decide(row, watched)
        if b: bets.append(b)
        else: skips[why] = skips.get(why, 0) + 1
    by = lambda f: [b for b in bets if f(b)]
    dev = by(lambda b: b["window"] in ("dev1", "dev2"))
    held = by(lambda b: b["window"] == "held")
    out = {
        "skips": dict(sorted(skips.items())),
        "dev": stats(dev), "dev1": stats(by(lambda b: b["window"] == "dev1")),
        "dev2": stats(by(lambda b: b["window"] == "dev2")), "held": stats(held),
        "descriptive": {
            "dev_member": stats([b for b in dev if b["member"]]),
            "dev_nonmember": stats([b for b in dev if not b["member"]]),
            "dev_calib_day0_1": stats([b for b in dev if b["calib"] == "day0_1"]),
            "dev_calib_day2_on": stats([b for b in dev if b["calib"] == "day2_on"]),
            "held_member": stats([b for b in held if b["member"]]),
            "held_nonmember": stats([b for b in held if not b["member"]]),
        },
        "held_calib_day0_1": stats([b for b in held if b["calib"] == "day0_1"]),
        "held_calib_day2_on": stats([b for b in held if b["calib"] == "day2_on"]),
    }
    d, d1, d2 = out["dev"], out["dev1"], out["dev2"]
    if d["n"] < DEV_MIN_BETS or pf_num(d) < 1.0 or pf_num(d1) < 1.2 or pf_num(d2) < 1.2:
        out["dev_verdict"] = "CLOSED"
    else:
        out["dev_verdict"] = "CONTINUE"
    h2 = out["held_calib_day2_on"]
    if h2["n"] < HELD_DAY2_MIN:
        out["held_verdict"] = "NO_EVIDENCE at n = %d" % h2["n"]
    elif pf_num(h2) < 1.0:
        out["held_verdict"] = "FAIL (calibration kill)"
    elif all(pf_num(out[k]) >= BAR_PF for k in ("dev1", "dev2", "held")) and (out["held"]["z"] or 0) >= BAR_Z:
        out["held_verdict"] = "PASS"
    else:
        out["held_verdict"] = "FAIL"
    return out

if __name__ == "__main__":
    rows = json.load(open(sys.argv[1]))
    watched = json.load(open(sys.argv[2]))
    print(json.dumps(score(rows, watched), indent=1, sort_keys=True))
