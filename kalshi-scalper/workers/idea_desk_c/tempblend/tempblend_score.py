#!/usr/bin/env python3
"""TEMPBLEND scorer (Idea Desk C, Nov 13, 2026). Research only. [research]

Written before any data was read, and tested only on invented rows. It makes no
network request: it reads a JSON file of decision rows and a JSON map of the
watched station per city, and prints a JSON verdict. The rule is
TEMPBLEND_CARD.md (same branch) with Amendments 1 and 2; where the two differ,
the card is right.

Usage:
  python3 -I tempblend_score.py dev  ROWS.json WATCHED.json
  python3 -I tempblend_score.py held ROWS.json WATCHED.json MARKER_PATH

dev mode ignores (and counts) every held-out row. held mode refuses before
2026-12-10T00:00:00Z and refuses a second run: it writes MARKER_PATH after the
read and refuses if that file already exists (Amendment 2, F3).

WATCHED.json maps city -> station_id. It stays a parameter until probe A4 says
which station each city's daily high market names. The ROWS file is made by a
separate row builder (Amendment 2, Q3), written after probe A4.

One row is one city-hour decision:
  city, S (ISO UTC settlement time), t_ms (canonical index minute used),
  v (index value, F), calib_effective_ms (effective_at_ms of the city's
  config_version at the decision), stations (index stations[] at t:
  station_id, temp_f, code, obs_time_ms), external (optional, source B:
  station_id -> {temp_f, obs_time_ms}), strikes (each: K, yes_bid, yes_ask in
  dollars from the candle ending at S minus 900 s, result "yes", "no" or
  "void", for "K or above").

Readings A1 to A18 are the card's Amendment 1 and the rulings F1 to F6, Q1 and
Q2 are its Amendment 2. In short: band and spread first, then the strike
nearest (v + s) / 2, a tie within 1e-9 to the lower K (A6, A7, F4); NO ask is
1 - yes_bid and the spread is yes_ask - yes_bid (A8); the fill is at the ask
seen with no +1c, plus the fee 0.07 x p x (1 - p) rounded up to the cent
(A10, an upper bound: live taker fills land 60% to 73% of the time); a void
is a fee-only loss counted as a bet (A12); results other than yes, no or void
are refused (F6); a second row for the same city and S is refused (F5); the
calibration split is measured at the decision time (A15); no index point
within 10 minutes of the decision is a skip (A17); a Source A reading taken
after t is a skip (Q2); every bar test uses unrounded values (F1); z is
clustered by US Central settlement day (Q1); PASS needs the development read
to CONTINUE (F2).
"""
import json, math, os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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
RESULTS = ("yes", "no", "void")
CENTRAL = ZoneInfo("America/Chicago")

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
            obs = st.get("obs_time_ms")
            if obs is not None and obs > t:
                return True, None, "obs_after_point"            # Q2
            r, member = st, True
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
        return None, "no_index_point"                           # A1, A17
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
        cands.append((K, ask, k["result"]))
    if not cands:
        return None, "no_strike"
    d0 = min(abs(K - mid) for K, _, _ in cands)                 # F4: explicit 1e-9 tie test
    K, ask, result = min((c for c in cands if abs(c[0] - mid) <= d0 + EPS), key=lambda c: c[0])
    f = fee(ask)
    void = result == "void"                                     # A12
    pnl = round(-f if void else ((1 - ask - f) if result == side else -(ask + f)), 4)
    calib = "day0_1" if decision - row["calib_effective_ms"] < CALIB_SPLIT_MS else "day2_on"   # A15
    day = datetime.fromtimestamp(S / 1000, timezone.utc).astimezone(CENTRAL).date().isoformat()
    return {"city": row["city"], "S": row["S"], "window": w, "side": side, "K": K,
            "ask": ask, "fee": f, "won": (not void) and result == side, "void": void, "pnl": pnl,
            "member": member, "calib": calib, "day": day}, None

def check_rows(rows):
    """F5 and F6: refuse a second row for one city and S, and any unknown result."""
    seen = set()
    for row in rows:
        key = (row.get("city"), row.get("S"))
        if key in seen:
            raise ValueError("duplicate row for city %r and S %r (at most one bet per city-hour)" % key)
        seen.add(key)
        for k in row.get("strikes", []):
            if k.get("result") not in RESULTS:
                raise ValueError("result %r for %r at %r is not yes, no or void" % (k.get("result"), key, k.get("K")))

def raw_stats(bets):
    n = len(bets)
    wins = sum(b["pnl"] for b in bets if b["pnl"] > 0)
    losses = -sum(b["pnl"] for b in bets if b["pnl"] < 0)
    pf = None if n == 0 else (math.inf if losses == 0 else wins / losses)
    net = sum(b["pnl"] for b in bets)
    days = {}
    for b in bets:                                              # Q1: clustered by US Central day
        days[b["day"]] = days.get(b["day"], 0.0) + b["pnl"]
    D, z = len(days), None
    if D >= 2:
        m = sum(days.values()) / D
        sd = math.sqrt(sum((x - m) ** 2 for x in days.values()) / (D - 1))
        z = None if sd == 0 else m / (sd / math.sqrt(D))
    return {"n": n, "won": sum(1 for b in bets if b["won"]), "void": sum(1 for b in bets if b["void"]),
            "days": D, "pf": pf, "net": net, "z": z}

def shown(st):
    """Rounded copy for printing only (F1)."""
    out = dict(st)
    pf = st["pf"]
    out["pf"] = None if pf is None else ("inf" if pf == math.inf else round(pf, 4))
    out["net"] = round(st["net"], 4)
    out["z"] = None if st["z"] is None else round(st["z"], 4)
    return out

def pf_val(st):
    return 0.0 if st["pf"] is None else st["pf"]

def dev_verdict(d, d1, d2):
    if d["n"] < DEV_MIN_BETS or pf_val(d) < 1.0 or pf_val(d1) < 1.2 or pf_val(d2) < 1.2:
        return "CLOSED"
    return "CONTINUE"

def held_verdict(dev_v, d1, d2, h, h2):
    if h2["n"] < HELD_DAY2_MIN:
        return "NO_EVIDENCE at n = %d" % h2["n"]
    if pf_val(h2) < 1.0:
        return "FAIL (calibration kill)"
    if dev_v == "CONTINUE" and all(pf_val(x) >= BAR_PF for x in (d1, d2, h)) and (h["z"] or 0) >= BAR_Z:
        return "PASS"
    return "FAIL"

def score(rows, watched, mode="dev"):
    if mode not in ("dev", "held"):
        raise ValueError("mode must be dev or held")
    check_rows(rows)
    bets, skips = [], {}
    for row in rows:
        b, why = decide(row, watched)
        if b and mode == "dev" and b["window"] == "held":
            b, why = None, "held_window_ignored"                # F3
        if b: bets.append(b)
        else: skips[why] = skips.get(why, 0) + 1
    sel = lambda f: raw_stats([b for b in bets if f(b)])
    dev_bets = [b for b in bets if b["window"] in ("dev1", "dev2")]
    d, d1, d2 = sel(lambda b: b["window"] in ("dev1", "dev2")), sel(lambda b: b["window"] == "dev1"), sel(lambda b: b["window"] == "dev2")
    out = {"mode": mode, "skips": dict(sorted(skips.items())),
           "dev": shown(d), "dev1": shown(d1), "dev2": shown(d2),
           "descriptive": {
               "dev_member": shown(raw_stats([b for b in dev_bets if b["member"]])),
               "dev_nonmember": shown(raw_stats([b for b in dev_bets if not b["member"]])),
               "dev_calib_day0_1": shown(raw_stats([b for b in dev_bets if b["calib"] == "day0_1"])),
               "dev_calib_day2_on": shown(raw_stats([b for b in dev_bets if b["calib"] == "day2_on"])),
           }}
    out["dev_verdict"] = dev_verdict(d, d1, d2)
    if mode == "held":
        held = [b for b in bets if b["window"] == "held"]
        h, h1 = raw_stats(held), raw_stats([b for b in held if b["calib"] == "day0_1"])
        h2 = raw_stats([b for b in held if b["calib"] == "day2_on"])
        out["held"], out["held_calib_day0_1"], out["held_calib_day2_on"] = shown(h), shown(h1), shown(h2)
        out["descriptive"]["held_member"] = shown(raw_stats([b for b in held if b["member"]]))
        out["descriptive"]["held_nonmember"] = shown(raw_stats([b for b in held if not b["member"]]))
        out["held_verdict"] = held_verdict(out["dev_verdict"], d1, d2, h, h2)
    return out

def held_guard(now_ms, marker):
    """F3: the held-out read is refused before 2026-12-10T00:00:00Z and after it has run once."""
    if now_ms < HELD_END:
        raise SystemExit("refused: the held-out read opens at 2026-12-10T00:00:00Z")
    if os.path.exists(marker):
        raise SystemExit("refused: the held-out read already ran (marker %s exists)" % marker)

if __name__ == "__main__":
    mode = sys.argv[1]
    rows = json.load(open(sys.argv[2]))
    watched = json.load(open(sys.argv[3]))
    if mode == "held":
        marker = sys.argv[4]
        held_guard(int(datetime.now(timezone.utc).timestamp() * 1000), marker)
        out = score(rows, watched, "held")
        with open(marker, "x") as f:
            f.write("TEMPBLEND held-out read at %s\n" % datetime.now(timezone.utc).isoformat())
    else:
        out = score(rows, watched, "dev")
    print(json.dumps(out, indent=1, sort_keys=True))
