#!/usr/bin/env python3
"""SOCDERIV (Desk B card 19) MEASUREMENT reader, job builders and scorer on scorekit. Testing Desk, Nov 12, 2026.
Built to Desk B's REGISTRATION (kalshi-scalper/workers/socderiv/SOCDERIV_REGISTRATION.md at 9b37bd6, claude/idea-desk-b; the registration wins over the card) and its frozen leagues file
(socderiv_series_frozen.json here, byte for byte SOCDERIV_SERIES.json, sha256 below). Research only: reads files, sends nothing. ZERO TRIES: no rule scored, NO RESULT READ AT ALL (the `result` field is never used).
Enforced in code: sample = the 60 most recently settled games of each league with closes from 2026-09-12 to before 2026-11-13T00:00Z, never extended; held-out (from 2026-11-13) never listed or requested;
leagues file must match CELLS_SHA256; prices only from minute-end candles, EVERY leg read at the SAME minute, thin or one-sided minutes counted not filled.
Instant: kickoff = the GAME (winner) market's occurrence_datetime minus 180 min; GUARD: that market closed 100 to 135 minutes after kickoff, else 'kickoff not derivable'. From kickoff minus 30 step back a minute at a time to
kickoff minus 90; take the FIRST minute at which the three winner markets, at least three total-goals strikes and the target contract are all two-sided at the close; otherwise the target is 'not filled'.
Model: two independent Poisson goal rates (team 1 = the lower team code of the winner tickers, team 2 = the other) fitted by least squares to the winner mids and every two-sided total strike mid at the instant;
both-teams-to-score = (1 - e^-l1)(1 - e^-l2); team total over k.5 = P(count > k.5). PLACEBO: refit with the total strike nearest 50c left out and report the same gap statistics for that strike.
Team-total markets are used only where floor_strike is given and the team is readable from the ticker's last segment (a prefix equal to a team code of the game); else counted 'unreadable'.
Kill (registration): under 150 filled games in a group and target type = 'no evidence at n = x'; group CLOSED on cost if the median round trip of its targets is above 5c; 'not tradable' if under half of the games with a derivable kickoff are filled;
'efficient, move on' (with the 90th percentile gap) unless the share of targets with a gap of 8c or more and spread 4c or less is at least 10 percent AND at least twice the placebo's share.
Commands: build-lists | games <lists...> | build-candles <lists...> | build-candles-split <out folder> <lists...> |  | measure <lists...> --candles <folders...>
"""
import calendar, hashlib, json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_FILE = os.path.join(HERE, "socderiv_series_frozen.json")
CELLS_SHA256 = "01b7febcd1466f880aeac1d567a259e5803d42b0b72e16a72331fd11c6d031d2"     # SOCDERIV_SERIES.json at 9b37bd6 (Desk B, frozen 2026-11-12)
WIN_FROM = calendar.timegm((2026, 9, 12, 0, 0, 0)); HELD_OUT_FROM = calendar.timegm((2026, 11, 13, 0, 0, 0))
SAMPLE, OFFSET_S, START_BACK, SCAN_BACK = 60, 180 * 60, 30 * 60, 90 * 60
GUARD_LO, GUARD_HI = 100 * 60, 135 * 60
GAP, SPREAD_MAX, MIN_FILLED, EDGE_SHARE, COST_MAX, PACK_LIMIT, PACK_SPAN_S = 0.08, 0.04, 150, 0.10, 0.04, 9000, 3 * 3600
SUFFIXES = {"winner": "GAME", "total": "TOTAL", "btts": "BTTS", "teamtotal": "TEAMTOTAL"}
REG = "kalshi-scalper/workers/testing/SOCDERIV_MEASUREMENT.md"
HELDOUT_LINE = ("none read; nothing closing on or after 2026-11-13T00:00Z is listed or requested (this card's own held-out); a measurement: no rule scored, no try. Per HELDOUT_REGISTRY.md (rnd-queue cf3f4c06 copy) and Desk B's dated line (registration 03c50460 onward), cards found that ever held out these series (Desk B dated line, registration 03c50460 and later): W-CAT-SPORTS1 (five series, released 06:51Z), "
               "SOCCER1 and SOCCERELO1 (matches from 2026-10-03T16:00Z, eight leagues, 24 series; released 07:09Z), USWEEP2 (22 series; released 07:09Z), SHARP1 (open; kickoffs March to September 2026, before this window, untouched). The Head reads this line against the registry before dispatch.")
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on sports"


def load_cells(path=CELLS_FILE, sha=None):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != (CELLS_SHA256 if sha is None else sha):
        raise SystemExit("refused: the leagues file does not match the frozen sha256")
    return json.loads(raw)


def leagues(spec): return [(g, lg) for g, ls in spec["groups"].items() for lg in ls]
def series_of(lg): return {n: "KX" + lg + sfx for n, sfx in SUFFIXES.items()}


def build_lists(spec):
    """16 leagues x 4 series = 64 live lists plus the 3 fee-field reads = 67 requests (registered)."""
    reqs, series = [], []
    for g, lg in leagues(spec):
        for n, s in series_of(lg).items():
            series.append(s)
            reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "min_close_ts": WIN_FROM, "max_close_ts": HELD_OUT_FROM - 1}, "max_pages": 2})
    for s in spec["fee_field_reads"]:
        reqs.append({"id": "fee_" + s, "path": "/series/" + s})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]},
           {"name": "series", "method": "GET", "path_pattern": "/series/(?P<series>[A-Z0-9]{2,32})", "params_allowed": []}]
    j = tie3.job("SOCDERIV_LISTS", "SOCDERIV measurement stage 1: settled lists of the 16 leagues' winner, total-goals, both-teams-to-score and team-total series, and 3 fee-field reads (times and strikes only; no result used).", eps, reqs, series + list(spec["fee_field_reads"]), [])
    j["notes"] = "SOCDERIV zero-try gap measurement stage 1: 64 league series lists and 3 fee-field reads"
    j["registration"] = REG; j["max_requests"] = sum(r.get("max_pages", 1) for r in reqs) + 9         # 67 requests, 131 pages at most; the runner counts pages against the cap (Main raised it to 131)
    return j


def game_key(event): return event.split("-", 1)[1] if "-" in event else event
def code(ticker): return ticker.rsplit("-", 1)[-1]


def games(spec, list_folders):
    """-> (games, counts). games: [ {group, league, game, kickoff, winner:[3 tickers], team1, team2, totals:{ticker: strike}, btts:[tickers], teamtotals:{ticker: (team, strike)}} ]. NO result field."""
    ms = k.markets(list_folders)
    by = {}
    for t, m in ms.items(): by.setdefault((m["series"], game_key(m["event"])), []).append(m)
    out = []
    counts = {"leagues_no_such_series": 0, "games_in_window": 0, "sampled": 0, "kickoff_not_derivable": 0, "no_btts_leg": 0, "teamtotal_unreadable_markets": 0}
    listed = {m["series"] for m in ms.values()}
    for g, lg in leagues(spec):
        ser = series_of(lg)
        counts["leagues_no_such_series"] += sum(1 for s in ser.values() if s not in listed)
        cand = []
        for (s, gk), mk in by.items():
            if s != ser["winner"]: continue
            close = max(m["close"] for m in mk if m["close"])
            if WIN_FROM <= close < HELD_OUT_FROM: cand.append((close, gk, mk))
        counts["games_in_window"] += len(cand)
        for close, gk, mk in sorted(cand, key=lambda x: (-x[0], x[1]))[:SAMPLE]:          # the 60 most recently settled, never extended
            counts["sampled"] += 1
            occ = [k.iso((m.get("times") or {}).get("occurrence_datetime") or "") for m in mk]
            if len(mk) != 3 or None in occ or max(occ) != min(occ):
                counts["kickoff_not_derivable"] += 1; continue
            ko = occ[0] - OFFSET_S
            if not (GUARD_LO <= close - ko <= GUARD_HI): counts["kickoff_not_derivable"] += 1; continue
            teams = sorted(code(m["ticker"]) for m in mk if not m["ticker"].endswith("-TIE"))
            if len(teams) != 2: counts["kickoff_not_derivable"] += 1; continue
            tot = {m["ticker"]: m["floor"] for m in by.get((ser["total"], gk), []) if m["floor"] is not None}
            btts = [m["ticker"] for m in by.get((ser["btts"], gk), [])]
            if len(btts) != 1: counts["no_btts_leg"] += 1; btts = []          # the BTTS leg is the ONE market of the event KX<LG>BTTS-<game key> (Head ruling Nov 13 08:21Z); none or more than one: no BTTS leg, counted
            tts = {}
            for m in by.get((ser["teamtotal"], gk), []):
                hits = [c for c in teams if code(m["ticker"]).startswith(c)]          # exactly one team code must prefix the last segment; two (one code the start of the other, e.g. CR and CRU) is not guessed: unreadable (registration: "if their shape cannot be read, unreadable, not guessed")
                tm = hits[0] if len(hits) == 1 else None
                if tm is None or m["floor"] is None: counts["teamtotal_unreadable_markets"] += 1; continue
                tts[m["ticker"]] = (tm, m["floor"])
            winner = sorted(m["ticker"] for m in mk)
            out.append({"group": g, "league": lg, "game": gk, "kickoff": ko, "winner": winner, "team1": teams[0], "team2": teams[1], "totals": tot, "btts": btts, "teamtotals": tts})
    return out, counts


def build_candles(spec, list_folders):
    gs, counts = games(spec, list_folders)
    items = sorted(((g["kickoff"], t) for g in gs for t in g["winner"] + list(g["totals"]) + g["btts"] + list(g["teamtotals"])), key=lambda x: x[0])
    win = SCAN_BACK - START_BACK + 60
    packs, cur = [], []
    for ko, t in items:
        trial = cur + [(ko, t)]
        span = trial[-1][0] - trial[0][0] + win
        if cur and (span > PACK_SPAN_S + win or span / 60 * len(trial) > PACK_LIMIT or len(trial) > 100):
            packs.append(cur); cur = [(ko, t)]
        else:
            cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for _, t in p), "start_ts": p[0][0] - SCAN_BACK - 60, "end_ts": p[-1][0] - START_BACK, "period_interval": 1}} for i, p in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    j = tie3.job("SOCDERIV_CANDLES", "SOCDERIV measurement stage 2: one minute candles of every leg of the sampled games, the 61 minutes ending at kickoff minus 30.", eps, reqs, {t.split("-")[0] for _, t in items}, [t for _, t in items])
    j["notes"] = "SOCDERIV zero-try gap measurement stage 2: candles of every leg of the sampled games"
    j["registration"] = REG; j["max_requests"] = len(reqs) + 20          # slack for a retry or a second page (Auditor B, point b)
    j["heldout"] = HELDOUT_LINE
    return j, counts


def pois(l, n): return math.exp(-l) * l ** n / math.factorial(n)
def over(lam, strike): return 1 - sum(pois(lam, n) for n in range(0, int(strike) + 1))        # strike x.5: count > x.5
_FACT = [math.factorial(n) for n in range(0, 13)]


def p_winner(l1, l2, N=12):
    """(team1 wins, draw, team2 wins) for independent Poisson counts, O(N)."""
    e1, e2 = math.exp(-l1), math.exp(-l2)
    p1 = [e1 * l1 ** n / _FACT[n] for n in range(N)]; p2 = [e2 * l2 ** n / _FACT[n] for n in range(N)]
    c2, run = [], 0.0
    for x in p2: run += x; c2.append(run)
    h = sum(p1[i] * c2[i - 1] for i in range(1, N)); d = sum(p1[i] * p2[i] for i in range(N)); a = max(0.0, sum(p1) * sum(p2) - h - d)
    return h, d, a


def fit(win_mid, total_mid):
    """Least squares by a coarse-to-fine grid over the two rates (step 0.2, then 0.04, 0.01, 0.0025, 0.0006, 0.00015, 0.00004). win_mid = (team1, draw, team2); total_mid = {strike: mid of 'over strike'}. Returns (l1, l2, rmse over the fitted legs)."""
    wm = list(win_mid)          # not renormalised: the fit absorbs the winner overround (registration, stated weakness)
    tm = list(total_mid.items()); NMAX = max([8] + [int(kk) for kk, _ in tm])          # cdf up to the largest strike (a 10.5 line exists on the real lists)
    def err(a, b):
        h, d, c = p_winner(a, b); lam = a + b; e = math.exp(-lam); cdf, run, ov = {}, 0.0, {}
        for n in range(0, NMAX + 1): run += e * lam ** n / math.factorial(n); cdf[n] = run
        return (h - wm[0]) ** 2 + (d - wm[1]) ** 2 + (c - wm[2]) ** 2 + sum((1 - cdf[int(kk)] - v) ** 2 for kk, v in tm)
    best = (1e9, 1.0, 1.0)
    for step, span, lo in ((0.2, 20, 0.1), (0.04, 5, None), (0.01, 4, None), (0.0025, 4, None), (0.0006, 4, None), (0.00015, 4, None), (0.00004, 4, None)):
        if lo is not None: cand = [(lo + i * step, lo + j * step) for i in range(span) for j in range(span)]
        else: cand = [(best[1] + i * step, best[2] + j * step) for i in range(-span, span + 1) for j in range(-span, span + 1)]
        best = min((err(a, b), a, b) for a, b in cand if a > 0.02 and b > 0.02)
    return best[1], best[2], (best[0] / (3 + len(tm))) ** 0.5


def two(idx, t, ts):
    c = idx.get(t, {}).get(ts)
    if not c or c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): return None
    return c["bid"], c["ask"]


def fee_up(p): return math.ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100


def one_way(value, b, a):
    """Desk B dated amendment (Nov 12): the cost line is ONE-WAY: (ask minus mid) of the side taken plus the entry fee at its price plus 1c, rounded up. The side taken is the cheaper one, as for the gap."""
    price = a if a <= 1 - b + 1e-9 else 1 - b
    return (a - b) / 2 + fee_up(round(price + 0.01, 4))


def gap(value, b, a):
    """The cheaper side = the side with the LOWER ask (YES ask a, or NO ask 1 - bid; a tie takes YES); gap = the model value of that side minus its ask."""
    return (value - a) if a <= 1 - b + 1e-9 else ((1 - value) - (1 - b))          # whole cents: a + b = 1.00 is a tie (float residue) and takes YES


def near_strike(tot):
    """The total-goals strike whose mid is nearest 50c, measured EXACTLY: bid and ask in hundredths of a cent (Kalshi quotes carry four decimals), so a sub-cent quote cannot create or hide a tie; an exact tie takes the LOWER strike (Head, Desk B dated line 26ae3495). tot = {strike: (bid, ask)}."""
    return min(tot, key=lambda kk: (abs(round(tot[kk][0] * 10000) + round(tot[kk][1] * 10000) - 10000), kk))


def stats(rows):
    if not rows: return None
    gs = [r["gap"] for r in rows]; sp = [r["spread"] for r in rows]; fire = sum(1 for r in rows if r["gap"] >= GAP - 1e-9 and r["spread"] <= SPREAD_MAX + 1e-9)          # 1e-9: a 4c spread written as 0.54 - 0.50 is 0.04000000000000004
    qs = st.quantiles(gs, n=10, method="inclusive") if len(gs) > 2 else None
    q4 = st.quantiles(gs, n=4, method="inclusive") if len(gs) > 2 else None
    return {"n": len(rows), "median_spread": round(st.median(sp), 4), "median_round_trip_information_only": round(st.median([r["round_trip"] for r in rows]), 4), "median_one_way_entry_cost": round(st.median([r["one_way"] for r in rows]), 4),
            "gap_quartiles_p90": None if not q4 else [round(q4[0], 4), round(st.median(gs), 4), round(q4[2], 4), round(qs[8], 4)], "share_gap_ge_8c_spread_le_4c": round(fire / len(rows), 3), "fires": fire}


def check_candle_runs(spec, list_folders, candle_folders):
    """Auditor B F4: refuse unless every candle folder is a COMPLETE run whose embedded job requests equal the ones built from these lists, the folders together cover every request, and every request was answered whole (status 200, not truncated, a file).
    -> (answered, asked)."""
    jc, _ = build_candles(spec, list_folders); want = {r["id"]: (r["path"], r["params"]) for r in jc["requests"]}; seen = {}
    for f in candle_folders:
        k.refuse_heldout(f)          # standing rule (h): the guard before any file of the folder is opened
        m = json.load(open(os.path.join(f, "manifest.json")))
        if m.get("status") != "complete" or not isinstance(m.get("job"), dict): raise SystemExit("refused: %s is not a complete candle run with its job" % f)
        for r in m["job"].get("requests", []):
            if r["id"] not in want or (r["path"], r["params"]) != want[r["id"]]: raise SystemExit("refused: request %s of %s is not one of the requests built from these lists" % (r["id"], f))
            rows = [x for x in m.get("rows", []) if x.get("id") == r["id"]]
            seen[r["id"]] = seen.get(r["id"], False) or (bool(rows) and all(x.get("status") == 200 and not x.get("truncated") and x.get("file") for x in rows))
    if set(seen) != set(want) or not all(seen.values()): raise SystemExit("refused: the candle pull is not whole (%d of %d requests answered whole)" % (sum(seen.values()), len(want)))
    return sum(seen.values()), len(want)


def measure(spec, list_folders, candle_folders):
    answered, asked = check_candle_runs(spec, list_folders, candle_folders)
    gs, counts = games(spec, list_folders)
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    rows = {}              # (group, type) -> list of target rows ; placebo rows kept alongside
    cache = {}; seen_pl = set()          # one placebo per (game, instant) of a filled target of that type (Miner R10)
    games_by_group = {}
    resid = []
    for g in gs:
        G = games_by_group.setdefault(g["group"], {"derivable": 0, "btts": {"derivable": 0, "filled": 0}, "teamtotal": {"derivable": 0, "filled": 0}})
        G["derivable"] += 1
        targets = [("btts", t, None) for t in g["btts"]] + [("teamtotal", t, v) for t, v in g["teamtotals"].items()]
        for typ in ("btts", "teamtotal"):
            if any(x[0] == typ for x in targets): G[typ]["derivable"] += 1
        got = {"btts": False, "teamtotal": False}
        for typ, tk, tt in targets:
            found = None
            for m in range(0, (SCAN_BACK - START_BACK) // 60 + 1):
                ts = g["kickoff"] - START_BACK - 60 * m
                if not all(two(idx, w, ts) for w in g["winner"]): continue
                tot = {kk: two(idx, t, ts) for t, kk in g["totals"].items() if two(idx, t, ts)}
                if len(tot) < 3 or not two(idx, tk, ts): continue
                found = (ts, tot); break
            if found is None: continue
            ts, tot = found
            wm = {w: sum(two(idx, w, ts)) / 2 for w in g["winner"]}
            tie = [w for w in g["winner"] if w.endswith("-TIE")]
            t1 = [w for w in g["winner"] if code(w) == g["team1"]]; t2 = [w for w in g["winner"] if code(w) == g["team2"]]
            if len(tie) != 1 or len(t1) != 1 or len(t2) != 1: continue
            totm = {kk: sum(v) / 2 for kk, v in tot.items()}
            ck = (g["game"], g["league"], ts)
            if ck not in cache: cache[ck] = fit((wm[t1[0]], wm[tie[0]], wm[t2[0]]), totm)
            l1, l2, rmse = cache[ck]; resid.append(rmse)
            b, a = two(idx, tk, ts)
            if typ == "btts": val = (1 - math.exp(-l1)) * (1 - math.exp(-l2))
            else: val = over(l1 if tt[0] == g["team1"] else l2, tt[1])
            mid = (a + b) / 2
            row = {"gap": gap(val, b, a), "spread": a - b, "round_trip": (a - b) + 2 * 0.07 * mid * (1 - mid), "one_way": one_way(val, b, a)}
            rows.setdefault((g["group"], typ), {"targets": [], "placebo": []})["targets"].append(row)
            # placebo: refit with the total strike nearest 50c left out, compare its model value with its own quote
            near = near_strike(tot); rest = {kk: v for kk, v in totm.items() if kk != near}
            if len(rest) >= 2 and (g["league"], g["game"], ts, typ) not in seen_pl:
                seen_pl.add((g["league"], g["game"], ts, typ))
                pk = ck + (near,)
                if pk not in cache: cache[pk] = fit((wm[t1[0]], wm[tie[0]], wm[t2[0]]), rest)
                p1, p2, _ = cache[pk]
                tkk = [t for t, kk in g["totals"].items() if kk == near][0]; pb, pa = tot[near]
                rows[(g["group"], typ)]["placebo"].append({"gap": gap(over(p1 + p2, near), pb, pa), "spread": pa - pb, "one_way": one_way(over(p1 + p2, near), pb, pa), "round_trip": (pa - pb) + 2 * 0.07 * ((pa + pb) / 2) * (1 - (pa + pb) / 2)})
            got[typ] = True
        for typ in ("btts", "teamtotal"):
            if got[typ]: G[typ]["filled"] += 1
    series_listed = {m["series"] for m in k.markets(list_folders).values()}
    out = {"counts_first": counts, "candle_requests_answered_whole": "%d of %d asked" % (answered, asked), "fit_residual_rmse_median": None if not resid else round(st.median(resid), 4), "groups": {}, "tries_added": 0, "rule_scored": False, "result_read": False, "freshness": FRESH,
           "model_note": "independent Poisson goals understate draws and low scores, moving both-teams-to-score by about one point; a gap of 2c to 3c means nothing; the placebo shows what model error alone produces"}
    for grp, G in games_by_group.items():
        out["groups"][grp] = {"games_with_derivable_kickoff": G["derivable"]}
        for typ in ("btts", "teamtotal"):
            R = rows.get((grp, typ), {"targets": [], "placebo": []}); filled = G[typ]["filled"]; with_target = G[typ]["derivable"]; der = G["derivable"]          # F6 (Head, literal text): the denominator is ALL the group's games with a derivable kickoff
            s_t, s_p = stats(R["targets"]), stats(R["placebo"])
            share_filled = None if not der else round(filled / der, 3)          # printed only; the test below is on the integers
            if filled < MIN_FILLED: verdict = "no evidence at n = %d filled games" % filled
            elif s_t["median_one_way_entry_cost"] > COST_MAX: verdict = "CLOSED on cost: median one-way entry cost %.1fc is above 4c (hold to settlement; Desk B dated amendment)" % (100 * s_t["median_one_way_entry_cost"])
            elif der and filled * 2 < der: verdict = "CLOSED: not tradable (under half of the games with a derivable kickoff are filled: %d of %d)" % (filled, der)
            elif s_t["fires"] * 10 >= s_t["n"] and s_t["fires"] * (s_p["n"] if s_p else 1) >= 2 * (s_p["fires"] if s_p else 0) * s_t["n"]: verdict = "SURVIVES the measurement (share at least 10 percent and at least twice the placebo's): a separate registration, tries = surviving cells"
            else: verdict = "CLOSED: efficient, move on. The one number: the 90th percentile gap %s" % (s_t["gap_quartiles_p90"] and s_t["gap_quartiles_p90"][3])
            out["groups"][grp][typ] = {"games_with_a_derivable_kickoff_in_the_group": der, "games_with_a_target_of_this_type": with_target, "no_such_market_in_this_group": not any(("KX" + lg + SUFFIXES[typ.replace("teamtotal", "teamtotal")]) in series_listed for lg in spec["groups"][grp]), "no_game_of_the_group_has_a_target_of_this_type": (with_target == 0), "filled": filled, "share_filled_of_all_derivable_games": share_filled, "targets": s_t, "placebo": s_p, "verdict": verdict}
    return out


def split_candles(j):
    """Two job files, A and B, by kickoff date: the requests are packed by kickoff time, so the cut is made at a request (pack) boundary near the middle and never through a request; the union of the two equals the whole job and no ticker is in both.
    max_requests = requests + 20 each; each carries the held-out line."""
    reqs = j["requests"]; cut = len(reqs) // 2; out = []
    for name, part in (("A", reqs[:cut]), ("B", reqs[cut:])):
        tk = sorted({t for r in part for t in r["params"]["market_tickers"].split(",")})
        jj = dict(j, job_id="SOCDERIV_CANDLES_" + name, requests=part, ticker_allowlist=tk, series_allowlist=sorted({t.split("-")[0] for t in tk}), max_requests=len(part) + 20)
        jj["purpose"] = j["purpose"] + " Part %s of two runs (the registration's size cap), by kickoff date." % name
        jj["notes"] = j["notes"] + "; part %s of two" % name
        out.append(jj)
    A, B = out
    assert not (set(A["ticker_allowlist"]) & set(B["ticker_allowlist"])) and set(A["ticker_allowlist"]) | set(B["ticker_allowlist"]) == set(j["ticker_allowlist"]) and len(A["requests"]) + len(B["requests"]) == len(reqs)
    return A, B


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    else:
        spec = load_cells()
        if a[0] == "build-lists": print(json.dumps(build_lists(spec), indent=1))
        elif a[0] == "games": print(json.dumps(games(spec, a[1:])[1], indent=1))
        elif a[0] == "build-candles": j, c = build_candles(spec, a[1:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
        elif a[0] == "build-candles-split":
            j, c = build_candles(spec, a[2:]); A, B = split_candles(j)
            for nm, jj in (("A", A), ("B", B)): open(os.path.join(a[1], "SOCDERIV_CANDLES_%s.json" % nm), "w").write(json.dumps(jj, indent=1) + "\n")
            print(json.dumps({"requests": [len(A["requests"]), len(B["requests"])], "tickers": [len(A["ticker_allowlist"]), len(B["ticker_allowlist"])]}))
        elif a[0] == "measure": i = a.index("--candles"); print(json.dumps(measure(spec, a[1:i], a[i + 1:]), indent=1))
