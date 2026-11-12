#!/usr/bin/env python3
"""MAPBREAK (Desk B) MEASUREMENT reader, job builders and scorer on scorekit. Testing Desk, Nov 12, 2026.
Built to Desk B's REGISTRATION (kalshi-scalper/workers/mapbreak/MAPBREAK_REGISTRATION.md, commit 50a1729b on claude/idea-desk-b; the registration wins) and its frozen titles file (mapbreak_series_frozen.json here, byte for byte, sha256 below).
Research only: reads files, sends nothing. ZERO TRIES: no rule scored. Same family as NHLOT (a state change while play is stopped): ONE candidate for the owner's count, a second venue.
Enforced in code: the ONLY result ever used is the MAP-1 market's (the state: who is one map up); the match market's result and map 2's and map 3's are NEVER read (the records are built without them; tested by feeding garbage results);
sample = the 1,500 most recently closed best-of-three matches with match closes from 2026-09-12 to before 2026-10-23T00:00Z; the held-out (from 2026-10-23T00:00Z) is never listed or requested (lists max_close_ts 1792713599);
the titles file must match CELLS_SHA256; prices only from minute-end candles, two-sided only (0 < bid < ask < 1), thin minutes counted not filled.
Instants: scheduled start S = the date and four-digit time at the front of the ticker key, read as America/New_York; GUARD map 1 ended 15 to 150 minutes after S, else 'start not derivable'; GUARD map 2 closes at least 15 minutes after map 1.
Pre-match: the minute candle ending at S minus 10 minutes, stepping back a minute at a time to S minus 40, taking the first minute at which the needed contracts are two-sided (INTERPRETED: the match contract of the team that won map 1 and both map-1 contracts, all in the SAME minute, so that the placebo uses the same minute).
The look: the candle ending at the first whole minute at or after map-1 close + 120 s, stepping FORWARD to map-1 close + 5 minutes until BOTH match contracts are two-sided.
Model: p = pre-match mid of the match contract of the team that went on to win map 1; q solves p = q*q*(3 - 2q); V = 1 - (1 - q)^2 for the team up, 1 - V for the other. Gap = value minus that team's own match-contract ask at the look; the cheaper side has the larger gap.
Placebo (pre-match instant): q against the ask of that team's MAP-1 contract, and 1 - q against the other team's.
Commands: build-lists | matches <lists folders...> | build-candles <lists folders...> | measure <lists folders...> --candles <candle folders...>
"""
import calendar, hashlib, json, math, os, re, statistics as st, sys
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_FILE = os.path.join(HERE, "mapbreak_series_frozen.json")
CELLS_SHA256 = "bc9140cbe8934cb242664558d3bf79071ba9491473a8360d893a6d89e480b6fe"
WIN_FROM = calendar.timegm((2026, 9, 12, 0, 0, 0)); HELD_OUT_FROM = calendar.timegm((2026, 10, 23, 0, 0, 0))
SAMPLE, MIN_FILLED, EDGE, SPREAD_MAX, COST_MAX, EDGE_SHARE = 1500, 150, 0.08, 0.04, 0.05, 0.10
G_LO, G_HI, MAP2_MIN = 15 * 60, 150 * 60, 15 * 60
PRE_BACK, PRE_MAX_BACK, LOOK_AFTER, LOOK_MAX = 10 * 60, 40 * 60, 120, 5 * 60
PACK_LIMIT, MAX_TICKERS = 9000, 100
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
NY = ZoneInfo("America/New_York")
REG = "kalshi-scalper/workers/testing/MAPBREAK_MEASUREMENT.md"
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on esports"


def load_cells(path=CELLS_FILE, sha=None):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != (CELLS_SHA256 if sha is None else sha):
        raise SystemExit("refused: the titles file does not match the frozen sha256")
    return json.loads(raw)


def series_all(spec): return [s for t in spec["titles"] for s in (t["match_series"], t["map_series"], t["total_maps_series"])]


def build_lists(spec):
    """12 series settled with the two close bounds, plus the 4 match-series fee-field reads."""
    reqs = []
    for s in series_all(spec):
        reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "min_close_ts": WIN_FROM, "max_close_ts": HELD_OUT_FROM - 1}, "max_pages": 8})
    for s in spec["fee_field_reads"]:
        reqs.append({"id": "fee_" + s, "path": "/series/" + s})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]},
           {"name": "series", "method": "GET", "path_pattern": "/series/(?P<series>[A-Z0-9]{2,32})", "params_allowed": []}]
    j = tie3.job("MAPBREAK_LISTS", "MAPBREAK measurement stage 1: settled lists of the match, map and total-maps series of four esports titles, closes 2026-09-12 to before 2026-10-23, and 4 fee-field reads (times, strikes and the map-1 result only).", eps, reqs, series_all(spec) + list(spec["fee_field_reads"]), [])
    j["registration"] = REG; j["heldout"] = "none read; nothing closing on or after 2026-10-23T00:00Z is listed or requested (max_close_ts 1792713599); a measurement: no rule scored, no try"
    j["max_requests"] = sum(r.get("max_pages", 1) for r in reqs) + 14        # the runner counts pages against the cap
    return j


def start_ts(key):
    m = re.match(r"(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)", key)
    if not m or m.group(2) not in MONTHS: return None
    return int(datetime(2000 + int(m.group(1)), MONTHS[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=NY).timestamp())


def matches(spec, list_folders):
    """-> (matches, counts). A match record holds NO match result and no map 2 or 3 result: only the map-1 winner (the state)."""
    raw = k.markets(list_folders)
    by = {}
    for t, m in raw.items():
        parts = t.split("-")
        by.setdefault((parts[0], parts[1] if len(parts) > 1 else ""), []).append((parts, m))
    counts = {"matches_listed": 0, "not_best_of_three": 0, "held_out_dropped": 0, "start_not_derivable": 0, "map2_too_soon": 0, "no_map1_result": 0, "sampled": 0}
    cand = []
    for ti in spec["titles"]:
        keys = {key for (s, key) in by if s == ti["match_series"]}
        for key in sorted(keys):
            counts["matches_listed"] += 1
            mm = by[(ti["match_series"], key)]
            close = max(m["close"] for _, m in mm if m["close"])
            if close >= HELD_OUT_FROM: counts["held_out_dropped"] += 1; continue
            tot = by.get((ti["total_maps_series"], key), [])
            floors = [m["floor"] for _, m in tot if m["floor"] is not None]
            maps = by.get((ti["map_series"], key), [])
            ns = {p[2] for p, _ in maps if len(p) >= 4}
            if len(mm) != 2 or not floors or max(floors) != 2.5 or "1" not in ns or "2" not in ns:
                counts["not_best_of_three"] += 1; continue
            cand.append((close, ti["cell"], key, mm, maps))
    out = []
    for close, cell, key, mm, maps in sorted(cand, key=lambda x: (-x[0], x[2]))[:SAMPLE]:
        counts["sampled"] += 1
        S = start_ts(key)
        m1 = [(p, m) for p, m in maps if p[2] == "1"]
        m2 = [m for p, m in maps if p[2] == "2"]
        if S is None or len(m1) != 2 or not m1[0][1]["close"]: counts["start_not_derivable"] += 1; continue
        c1 = max(m["close"] for _, m in m1)
        if not (G_LO <= c1 - S <= G_HI): counts["start_not_derivable"] += 1; continue
        if not m2 or min(m["close"] for m in m2) < c1 + MAP2_MIN: counts["map2_too_soon"] += 1; continue
        win = [p[3] for p, m in m1 if m["result"] == "yes"]                    # THE state: the map-1 market's own result. No other result is read.
        if len(win) != 1: counts["no_map1_result"] += 1; continue
        teams = sorted(p[-1] for p, _ in mm)
        if win[0] not in teams or len(set(teams)) != 2: counts["no_map1_result"] += 1; continue
        base = {"cell": cell, "key": key, "S": S, "map1_close": c1}
        match_t = {p[-1]: m["ticker"] for p, m in mm}; map1_t = {p[3]: m["ticker"] for p, m in m1}
        out.append(dict(base, up=win[0], down=[x for x in teams if x != win[0]][0], match=match_t, map1=map1_t))
    return out, counts


def build_candles(spec, list_folders):
    """Per match four tickers (two match, two map-1) from S minus 40 minutes to map-1 close plus 5; matches sharing a start share a request (sorted by S; window minutes x tickers at most 9,000, at most 100 tickers)."""
    ms, counts = matches(spec, list_folders)
    ms = sorted(ms, key=lambda m: (m["S"], m["key"])); packs, cur = [], []
    def win(g): return (max(m["map1_close"] for m in g) + LOOK_MAX) - (min(m["S"] for m in g) - PRE_MAX_BACK)
    for m in ms:
        trial = cur + [m]
        if cur and (win(trial) / 60 * 4 * len(trial) > PACK_LIMIT or 4 * len(trial) > MAX_TICKERS):
            packs.append(cur); cur = [m]
        else: cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for m in g for t in list(m["match"].values()) + list(m["map1"].values())),
             "start_ts": min(m["S"] for m in g) - PRE_MAX_BACK - 60, "end_ts": max(m["map1_close"] for m in g) + LOOK_MAX, "period_interval": 1}} for i, g in enumerate(packs)]
    tickers = [t for m in ms for t in list(m["match"].values()) + list(m["map1"].values())]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    j = tie3.job("MAPBREAK_CANDLES", "MAPBREAK measurement stage 2: one minute candles of the two match and two map-1 contracts of each sampled match, from S minus 40 minutes to map-1 close plus 5.", eps, reqs, series_all(spec), tickers)
    j["registration"] = REG; j["heldout"] = "none read; the sample closes before 2026-10-23T00:00Z"; return j, counts


def solve_q(p):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if mid * mid * (3 - 2 * mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def two(idx, t, ts):
    c = idx.get(t, {}).get(ts)
    if not c or c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): return None
    return c["bid"], c["ask"]


def rt(b, a):
    mid = (a + b) / 2
    return (a - b) + 2 * 0.07 * mid * (1 - mid)


def stat(rows):
    if not rows: return None
    g = [r["gap"] for r in rows]; q = st.quantiles(g, n=4, method="inclusive") if len(g) > 2 else None; d = st.quantiles(g, n=10, method="inclusive") if len(g) > 2 else None
    fire = [r for r in rows if r["gap"] >= EDGE and r["spread"] <= SPREAD_MAX]
    return {"n": len(rows), "gap_median": round(st.median(g), 4), "gap_quartiles": None if not q else [round(q[0], 4), round(q[2], 4)], "gap_p90": None if not d else round(d[8], 4),
            "share_gap_ge_8c_spread_le_4c": round(len(fire) / len(rows), 3), "share_when_team_up": round(sum(1 for r in fire if r.get("side") == "up") / len(rows), 3), "share_when_team_down": round(sum(1 for r in fire if r.get("side") == "down") / len(rows), 3)}


def measure(spec, list_folders, candle_folders):
    ms, counts = matches(spec, list_folders)
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    per = {}
    for m in ms:
        P = per.setdefault(m["cell"], {"sampled": 0, "pre": [], "look": [], "placebo": [], "minutes": [], "contract_rt": [], "contract_spread": [], "pre_filled": 0, "look_filled": 0})
        P["sampled"] += 1
        need = [m["match"][m["up"]], m["map1"][m["up"]], m["map1"][m["down"]]]
        pre = None
        for back in range(PRE_BACK, PRE_MAX_BACK + 1, 60):
            ts = m["S"] - back
            if all(two(idx, t, ts) for t in need): pre = ts; break
        if pre is None: continue
        P["pre_filled"] += 1
        pm = sum(two(idx, m["match"][m["up"]], pre)) / 2; q = solve_q(pm)
        for team, val in ((m["up"], q), (m["down"], 1 - q)):
            b, a = two(idx, m["map1"][team], pre); P["placebo"].append({"gap": val - a, "spread": a - b, "team": team})
        pb = {"up": P["placebo"][-2], "down": P["placebo"][-1]}
        best = max(pb, key=lambda s: pb[s]["gap"]); P["placebo"][-2:] = [dict(pb[best], side=best)]
        t0 = -(-(m["map1_close"] + LOOK_AFTER) // 60) * 60; look = None
        for ts in range(t0, m["map1_close"] + LOOK_MAX + 1, 60):
            if all(two(idx, m["match"][x], ts) for x in (m["up"], m["down"])): look = ts; break
        if look is None: continue
        P["look_filled"] += 1; P["minutes"].append((look - m["map1_close"]) / 60)
        V = 1 - (1 - q) ** 2
        cand = {}
        for side, team, val in (("up", m["up"], V), ("down", m["down"], 1 - V)):
            b, a = two(idx, m["match"][team], look); cand[side] = {"gap": val - a, "spread": a - b, "side": side}
            P["contract_rt"].append(rt(b, a)); P["contract_spread"].append(a - b)
        bs = max(cand, key=lambda s: cand[s]["gap"]); P["look"].append(cand[bs])
    out = {"counts_first": counts, "titles": {}, "tries_added": 0, "rule_scored": False, "match_result_read": False, "freshness": FRESH, "family_note": "same family as NHLOT: ONE candidate for the owner's count; the Head's probability that it reaches the research bar is 2 percent"}
    verdicts = []
    for cell, P in sorted(per.items()):
        s_l, s_p = stat(P["look"]), stat(P["placebo"]); n = P["look_filled"]
        medrt = None if not P["contract_rt"] else round(st.median(P["contract_rt"]), 4)
        if n < MIN_FILLED: v = "no evidence at n = %d filled at the look" % n
        elif medrt > COST_MAX: v = "CLOSED on cost: median round trip %.1fc at the look is above 5c" % (100 * medrt)
        elif s_l["share_gap_ge_8c_spread_le_4c"] >= EDGE_SHARE and s_l["share_gap_ge_8c_spread_le_4c"] >= 2 * (s_p["share_gap_ge_8c_spread_le_4c"] if s_p else 0): v = "SURVIVES the measurement (share at least 10 percent and at least twice the placebo's): a separate registration and the Head's go"
        else: v = "CLOSED: efficient, move on. The one number: the 90th percentile gap %s" % s_l["gap_p90"]
        verdicts.append(v)
        out["titles"][cell] = {"sampled_matches": P["sampled"], "filled_pre_match": P["pre_filled"], "filled_at_the_look": n, "median_minutes_map1_close_to_look": None if not P["minutes"] else round(st.median(P["minutes"]), 2),
                               "median_spread_at_look": None if not P["contract_spread"] else round(st.median(P["contract_spread"]), 4), "median_round_trip_at_look": medrt, "look": s_l, "placebo": s_p, "verdict": v}
    out["card"] = "CLOSED: every title is closed or has no evidence" if verdicts and all(not v.startswith("SURVIVES") for v in verdicts) else ("a title survives the measurement" if verdicts else "no title measured")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    else:
        spec = load_cells()
        if a[0] == "build-lists": print(json.dumps(build_lists(spec), indent=1))
        elif a[0] == "matches": print(json.dumps(matches(spec, a[1:])[1], indent=1))
        elif a[0] == "build-candles": j, c = build_candles(spec, a[1:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
        elif a[0] == "measure": i = a.index("--candles"); print(json.dumps(measure(spec, a[1:i], a[i + 1:]), indent=1))
