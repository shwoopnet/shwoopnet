#!/usr/bin/env python3
"""MAPBREAK (Desk B) MEASUREMENT reader, job builders and scorer on scorekit. Testing Desk, Nov 12, 2026.
Built to Desk B's REGISTRATION (kalshi-scalper/workers/mapbreak/MAPBREAK_REGISTRATION.md, commit 50a1729b on claude/idea-desk-b; the registration wins) and its frozen titles file (mapbreak_series_frozen.json here, byte for byte, sha256 below).
Research only: reads files, sends nothing. Desk B's AMENDMENTS 1 to 3 (Nov 12): the card is the registered RULE (2 tries, one per look), the first pull is both the measurement and the development read. Same family as NHLOT: ONE candidate for the owner's count, a second venue.
Enforced in code: records carry only the map-1 winner (the state) and the map-2 CLOSE time (second look); no map 3 result is ever read; map 1 and map 2 results are the STATES (Amendment 4). The match market's result is read ONLY for a bet the rule fires (result_fn), and NOT AT ALL if every title/look is out on its kill lines (step 1 first, no result);
development sample = EVERY best-of-three match closing 2026-09-12 to before 2026-10-23T00:00Z (the 1,500 cap is REMOVED); the held-out (from 2026-10-23T00:00Z) is never listed or requested and score refuses it without the Head's go;
the titles file must match CELLS_SHA256; prices only from minute-end candles, two-sided only (0 < bid < ask < 1), thin minutes counted not filled.
Instants: scheduled start S = the date and four-digit time at the front of the ticker key, read as America/New_York; GUARD map 1 ended 15 to 150 minutes after S, else 'start not derivable'; GUARD map 2 closes at least 15 minutes after map 1.
Pre-match: the minute candle ending at S minus 10 minutes, stepping back a minute at a time to S minus 40, taking the first minute at which the needed contracts are two-sided (INTERPRETED: the match contract of the team that won map 1 and both map-1 contracts, all in the SAME minute, so that the placebo uses the same minute).
The look: the candle ending at the first whole minute at or after map-1 close + 120 s, stepping FORWARD to map-1 close + 5 minutes until BOTH match contracts are two-sided.
Model: p = pre-match mid of the match contract of the team that went on to win map 1; q solves p = q*q*(3 - 2q); V = 1 - (1 - q)^2 for the team up, 1 - V for the other. Gap = value minus that team's own match-contract ask at the look; the cheaper side has the larger gap.
Placebo (pre-match instant): q against the ask of that team's MAP-1 contract, and 1 - q against the other team's.
Commands: build-lists | history-count <lists folders...> | matches <lists folders...> | build-candles <lists folders...> | measure <lists folders...> --candles <candle folders...> | score <lists folders...> --candles <candle folders...>   (score = the registered RULE, development read only)
"""
import calendar, hashlib, json, math, os, re, statistics as st, sys
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3
import breakplay as bp

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_FILE = os.path.join(HERE, "mapbreak_series_frozen.json")
CELLS_SHA256 = "bc9140cbe8934cb242664558d3bf79071ba9491473a8360d893a6d89e480b6fe"
WIN_FROM = calendar.timegm((2026, 9, 12, 0, 0, 0)); HELD_OUT_FROM = calendar.timegm((2026, 10, 23, 0, 0, 0))
SAMPLE, MIN_FILLED, EDGE, SPREAD_MAX, COST_MAX, EDGE_SHARE = None, 150, 0.08, 0.04, 0.05, 0.10
G_LO, G_HI, MAP2_MIN = 15 * 60, 150 * 60, 15 * 60
PRE_BACK, PRE_MAX_BACK, LOOK_AFTER, LOOK_MAX = 10 * 60, 40 * 60, 120, 5 * 60
PACK_LIMIT, MAX_TICKERS = 9000, 100
HIST_PAGES = 10                                  # history lists: at most 10 pages of 1,000 markets a match series (counts only)
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
NY = ZoneInfo("America/New_York")
REG = "kalshi-scalper/workers/mapbreak/MAPBREAK_REGISTRATION.md"          # Desk B's registration (claude/idea-desk-b); my build note is kalshi-scalper/workers/testing/MAPBREAK_MEASUREMENT.md
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
    for t in spec["titles"]:                       # page budgets by expected size: map series are the largest (2 markets a map, 2 to 3 maps a match), match and total-maps series about 6,000 markets each
        for s, pages in ((t["match_series"], 6), (t["map_series"], 12), (t["total_maps_series"], 6)):
            reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "min_close_ts": WIN_FROM, "max_close_ts": HELD_OUT_FROM - 1}, "max_pages": pages})
    for t in spec["titles"]:                       # Amendment 3: 4 history lists of the MATCH series (counts only: how many best-of-three matches exist before 2026-09-12); series_ticker, limit, cursor only
        reqs.append({"id": "hist_" + t["match_series"], "path": "/historical/markets", "params": {"series_ticker": t["match_series"], "limit": 1000}, "max_pages": HIST_PAGES})
    for s in spec["fee_field_reads"]:
        reqs.append({"id": "fee_" + s, "path": "/series/" + s})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]},
           {"name": "hist_markets_list", "method": "GET", "path_pattern": "/historical/markets", "params_allowed": ["series_ticker", "limit", "cursor"]},
           {"name": "series", "method": "GET", "path_pattern": "/series/(?P<series>[A-Z0-9]{2,32})", "params_allowed": []}]
    j = tie3.job("MAPBREAK_LISTS", "MAPBREAK stage 1: settled market lists of the match, map-winner and total-maps series for CS2, Dota 2, Valorant and League of Legends, closes 2026-09-12 to before 2026-10-23, plus 4 history match-series lists (counts of older matches) and 4 fee-field reads. Used: tickers, close times, strikes and the map-1 result only; a match result is read at scoring only for a bet the rule fires.", eps, reqs, series_all(spec) + list(spec["fee_field_reads"]), [])
    j["notes"] = "MAPBREAK registered rule (Amendments 1 to 3); 20 requests: 12 live lists (6 pages for each match and total-maps series, 12 for each map series), 4 history match-series lists (10 pages each, counts only) and 4 fee reads. A list that is still paging at its page cap shows a pending cursor in the manifest; the reader reports it as truncated (its own verdict), never silently."
    j["registration"] = REG; j["heldout"] = "none read; nothing closing on or after 2026-10-23T00:00Z is listed or requested (max_close_ts 1792713599); the registered rule, development read only"
    j["max_requests"] = sum(r.get("max_pages", 1) for r in reqs) + 14        # the runner counts pages against the cap
    return j


def start_ts(key):
    m = re.match(r"(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)", key)
    if not m or m.group(2) not in MONTHS: return None
    return int(datetime(2000 + int(m.group(1)), MONTHS[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=NY).timestamp())


def matches(spec, list_folders):
    """-> (records, counts) in the breakplay engine shape. A record holds NO match result and no map 3 result: the map-1 winner (state of look 1) and, when the map-2 result names the team that lost map 1 (Amendment 4), state_close2 and state_ticker2 (state of look 2). The match market's close time is never used."""
    raw = k.markets(list_folders)
    trunc = set()
    for f in ([list_folders] if isinstance(list_folders, str) else list_folders):
        last = {}
        for row, body in k.iter_answers(f):
            last[row["id"]] = body.get("cursor") if isinstance(body, dict) else None           # the LAST page stored for each request
        trunc |= {i for i, c in last.items() if c}
    by = {}
    for t, m in raw.items():
        parts = t.split("-")
        by.setdefault((parts[0], parts[1] if len(parts) > 1 else ""), []).append((parts, m))
    counts = {"lists_truncated_at_the_page_cap": sorted(trunc), "matches_listed": 0, "not_best_of_three": 0, "held_out_dropped": 0, "start_not_derivable": 0, "no_map1_result": 0, "sampled": 0, "second_look_matches": 0, "map2_closed_under_15_min_after_map1_count_only": 0, "map2_won_by_map1_winner_no_second_look": 0, "no_map2_result_no_second_look": 0}
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
            if len(mm) != 2 or not floors or max(floors) != 2.5 or "1" not in ns:
                counts["not_best_of_three"] += 1; continue
            cand.append((close, ti["cell"], key, mm, maps))
    out = []
    for close, cell, key, mm, maps in sorted(cand, key=lambda x: (-x[0], x[2])):
        counts["sampled"] += 1
        S = start_ts(key)
        m1 = [(p, m) for p, m in maps if p[2] == "1"]
        m2 = [m for p, m in maps if p[2] == "2"]
        if S is None or len(m1) != 2 or not m1[0][1]["close"]: counts["start_not_derivable"] += 1; continue
        c1 = max(m["close"] for _, m in m1)
        if not (G_LO <= c1 - S <= G_HI): counts["start_not_derivable"] += 1; continue
        win = [p[3] for p, m in m1 if m["result"] == "yes"]                    # THE state: the map-1 market's own result. No other result is read.
        if len(win) != 1: counts["no_map1_result"] += 1; continue
        teams = sorted(p[-1] for p, _ in mm)
        if win[0] not in teams or len(set(teams)) != 2: counts["no_map1_result"] += 1; continue
        match_t = {p[-1]: m["ticker"] for p, m in mm}; map1_t = {p[3]: m["ticker"] for p, m in m1}
        rec = {"cell": cell, "key": key, "S": S, "state_close": c1, "up": win[0], "down": [x for x in teams if x != win[0]][0], "match": match_t, "placebo": map1_t}
        if m2 and min(p_m["close"] for p_m in m2) < c1 + MAP2_MIN: counts["map2_closed_under_15_min_after_map1_count_only"] += 1          # Amendment 4: a COUNT, it decides nothing
        # Amendment 4: the second look exists when the map-2 market's own RESULT names the team that lost map 1 (one map each); the match market's close is never used
        m2p = [(p, m) for p, m in maps if p[2] == "2"]
        w2 = [(p[3], m["ticker"]) for p, m in m2p if m["result"] == "yes"]
        if len(m2p) == 2 and len(w2) == 1 and all(m["close"] for _, m in m2p):
            if w2[0][0] == rec["down"]:
                rec["state_close2"] = max(m["close"] for _, m in m2p); rec["state_ticker2"] = w2[0][1]; counts["second_look_matches"] += 1
            else: counts["map2_won_by_map1_winner_no_second_look"] += 1
        else: counts["no_map2_result_no_second_look"] += 1
        out.append(rec)
    return out, counts


CFG = bp.VenueConfig("mapbreak", "bo3", heldout_from=HELD_OUT_FROM, freshness=FRESH)


def build_candles(spec, list_folders):
    """Per match four tickers (two match, two map-1) from S minus 40 minutes to map-1 close plus 5 (the engine packs by scheduled start)."""
    ms, counts = matches(spec, list_folders)
    j = bp.candle_job(ms, CFG, series_all(spec), "MAPBREAK_CANDLES", REG)
    j["heldout"] = "none read; the sample closes before 2026-10-23T00:00Z"; j["notes"] = "MAPBREAK zero-try gap measurement stage 2: candles of the two match and two map-1 contracts of each sampled match"; return j, counts


def measure(spec, list_folders, candle_folders):
    ms, counts = matches(spec, list_folders)
    out = bp.measure(ms, candle_folders, CFG); out["counts_first"] = counts; out["match_result_read"] = False
    out["family_note"] = "same family as NHLOT: ONE candidate for the owner's count; the Head's probability that it reaches the research bar is 2 percent"
    return out


def result_lookup(list_folders):
    """-> result_fn(rec): True if the team up after map 1 won the match, read from the match market's own result. Called by the rule ONLY for a bet it fires."""
    raw = k.markets(list_folders)
    def fn(rec):
        res = {t: raw.get(tk, {}).get("result") for t, tk in rec["match"].items()}
        if sorted(res.values(), key=str) != ["no", "yes"]: return None
        return res[rec["up"]] == "yes"
    return fn


def score(spec, list_folders, candle_folders, heldout_go=False):
    """The REGISTERED RULE (Desk B's Amendments 1 to 3): the first pull is both the measurement and the development read; match results are read only for matches where the rule fired, and not at all if every title/look is out."""
    ms, counts = matches(spec, list_folders)
    out = bp.score_rule2(ms, candle_folders, CFG, result_lookup(list_folders), heldout_go=heldout_go, name="MAPBREAK rule")
    out["counts_first"] = counts; return out


HIST_RE = "hist_"


def history_count(spec, list_folders):
    """Amendment 3 item 3: print for the Head the number of best-of-three-candidate matches before 2026-09-12 by title (match-series history lists, two markets a match) and the candle request count a history stage would need
    (4 contracts a match; history candles may be one market a request, so the upper figure is matches x 4, the lower is one request a match). Counts only, no result."""
    out = {}
    for f in ([list_folders] if isinstance(list_folders, str) else list_folders):
        last = {}
        for row, body in k.iter_answers(f):
            if not row["id"].startswith(HIST_RE): continue
            last[row["id"]] = body.get("cursor") if isinstance(body, dict) else None
            for m in body.get("markets", []) if isinstance(body, dict) else []:
                ct = k.iso(m.get("close_time", ""))
                if m.get("ticker") and ct and ct < WIN_FROM:
                    parts = m["ticker"].split("-"); out.setdefault(row["id"][len(HIST_RE):], set()).add(parts[1] if len(parts) > 1 else "")
        out["_truncated"] = sorted(i for i, c in last.items() if c)
    t = {s: len(v) for s, v in out.items() if s != "_truncated"}
    tot = sum(t.values())
    return {"matches_before_2026_09_12_by_match_series": t, "total": tot, "truncated_lists": out.get("_truncated", []),
            "candle_requests_if_one_market_a_request": tot * 4, "candle_requests_if_one_a_match": tot,
            "note": "the match series alone cannot say best-of-three; the total-maps market (strike 2.5) is needed and may not exist on the history endpoint; those matches are then unusable and counted"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    else:
        spec = load_cells()
        if a[0] == "build-lists": print(json.dumps(build_lists(spec), indent=1))
        elif a[0] == "matches": print(json.dumps(matches(spec, a[1:])[1], indent=1))
        elif a[0] == "build-candles": j, c = build_candles(spec, a[1:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
        elif a[0] == "measure": i = a.index("--candles"); print(json.dumps(measure(spec, a[1:i], a[i + 1:]), indent=1))
        elif a[0] == "history-count": print(json.dumps(history_count(spec, a[1:]), indent=1))
        elif a[0] == "score": i = a.index("--candles"); print(json.dumps(score(spec, a[1:i], a[i + 1:]), indent=1, default=str))
