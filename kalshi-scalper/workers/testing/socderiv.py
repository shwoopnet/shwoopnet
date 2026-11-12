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
Commands: build-lists | games <lists...> | build-candles <lists...> | measure <lists...> --candles <folders...>
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
GAP, SPREAD_MAX, MIN_FILLED, EDGE_SHARE, COST_MAX, PACK_LIMIT, PACK_SPAN_S = 0.08, 0.04, 150, 0.10, 0.05, 9000, 3 * 3600
SUFFIXES = {"winner": "GAME", "total": "TOTAL", "btts": "BTTS", "teamtotal": "TEAMTOTAL"}
REG = "kalshi-scalper/workers/testing/SOCDERIV_MEASUREMENT.md"
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
    j["registration"] = REG; j["max_requests"] = len(reqs) + 33         # 67 registered, about 80 pages; the runner counts pages against the cap
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
            if not btts: counts["no_btts_leg"] += 1
            tts = {}
            for m in by.get((ser["teamtotal"], gk), []):
                tm = next((c for c in teams if code(m["ticker"]).startswith(c)), None)
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
    j["registration"] = REG; return j, counts


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
    """Least squares by a coarse-to-fine grid over the two rates (step 0.2, then 0.04, then 0.01). win_mid = (team1, draw, team2); total_mid = {strike: mid of 'over strike'}. Returns (l1, l2, rmse over the fitted legs)."""
    s = sum(win_mid); wm = [x / s for x in win_mid] if s > 0 else list(win_mid)
    tm = list(total_mid.items())
    def err(a, b):
        h, d, c = p_winner(a, b); lam = a + b; e = math.exp(-lam); cdf, run, ov = {}, 0.0, {}
        for n in range(0, 9): run += e * lam ** n / math.factorial(n); cdf[n] = run
        return (h - wm[0]) ** 2 + (d - wm[1]) ** 2 + (c - wm[2]) ** 2 + sum((1 - cdf[int(kk)] - v) ** 2 for kk, v in tm)
    best = (1e9, 1.0, 1.0)
    for step, span, lo in ((0.2, 20, 0.1), (0.04, 5, None), (0.01, 4, None)):
        if lo is not None: cand = [(lo + i * step, lo + j * step) for i in range(span) for j in range(span)]
        else: cand = [(best[1] + i * step, best[2] + j * step) for i in range(-span, span + 1) for j in range(-span, span + 1)]
        best = min((err(a, b), a, b) for a, b in cand if a > 0.02 and b > 0.02)
    return best[1], best[2], (best[0] / (3 + len(tm))) ** 0.5


def two(idx, t, ts):
    c = idx.get(t, {}).get(ts)
    if not c or c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): return None
    return c["bid"], c["ask"]


def gap(value, b, a): return max(value - a, b - value)          # YES at the ask, or NO at 1 - bid: the cheaper side


def stats(rows):
    if not rows: return None
    gs = [r["gap"] for r in rows]; sp = [r["spread"] for r in rows]; fire = sum(1 for r in rows if r["gap"] >= GAP and r["spread"] <= SPREAD_MAX)
    qs = st.quantiles(gs, n=10, method="inclusive") if len(gs) > 2 else None
    q4 = st.quantiles(gs, n=4, method="inclusive") if len(gs) > 2 else None
    return {"n": len(rows), "median_spread": round(st.median(sp), 4), "median_round_trip": round(st.median([r["round_trip"] for r in rows]), 4),
            "gap_quartiles_p90": None if not q4 else [round(q4[0], 4), round(st.median(gs), 4), round(q4[2], 4), round(qs[8], 4)], "share_gap_ge_8c_spread_le_4c": round(fire / len(rows), 3)}


def measure(spec, list_folders, candle_folders):
    gs, counts = games(spec, list_folders)
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    rows = {}              # (group, type) -> list of target rows ; placebo rows kept alongside
    cache = {}
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
            row = {"gap": gap(val, b, a), "spread": a - b, "round_trip": (a - b) + 2 * 0.07 * mid * (1 - mid)}
            rows.setdefault((g["group"], typ), {"targets": [], "placebo": []})["targets"].append(row)
            # placebo: refit with the total strike nearest 50c left out, compare its model value with its own quote
            near = min(totm, key=lambda kk: abs(totm[kk] - 0.5)); rest = {kk: v for kk, v in totm.items() if kk != near}
            if len(rest) >= 2:
                pk = ck + (near,)
                if pk not in cache: cache[pk] = fit((wm[t1[0]], wm[tie[0]], wm[t2[0]]), rest)
                p1, p2, _ = cache[pk]
                tkk = [t for t, kk in g["totals"].items() if kk == near][0]; pb, pa = tot[near]
                rows[(g["group"], typ)]["placebo"].append({"gap": gap(over(p1 + p2, near), pb, pa), "spread": pa - pb, "round_trip": (pa - pb) + 2 * 0.07 * ((pa + pb) / 2) * (1 - (pa + pb) / 2)})
            got[typ] = True
        for typ in ("btts", "teamtotal"):
            if got[typ]: G[typ]["filled"] += 1
    out = {"counts_first": counts, "fit_residual_rmse_median": None if not resid else round(st.median(resid), 4), "groups": {}, "tries_added": 0, "rule_scored": False, "result_read": False, "freshness": FRESH,
           "model_note": "independent Poisson goals understate draws and low scores, moving both-teams-to-score by about one point; a gap of 2c to 3c means nothing; the placebo shows what model error alone produces"}
    for grp, G in games_by_group.items():
        out["groups"][grp] = {"games_with_derivable_kickoff": G["derivable"]}
        for typ in ("btts", "teamtotal"):
            R = rows.get((grp, typ), {"targets": [], "placebo": []}); filled = G[typ]["filled"]; der = G[typ]["derivable"]
            s_t, s_p = stats(R["targets"]), stats(R["placebo"])
            share_filled = None if not der else round(filled / der, 3)
            if filled < MIN_FILLED: verdict = "no evidence at n = %d filled games" % filled
            elif s_t["median_round_trip"] > COST_MAX: verdict = "CLOSED on cost: median round trip %.1fc is above 5c" % (100 * s_t["median_round_trip"])
            elif share_filled is not None and share_filled < 0.5: verdict = "CLOSED: not tradable (under half of the derivable-kickoff games are filled)"
            elif s_t["share_gap_ge_8c_spread_le_4c"] >= EDGE_SHARE and s_t["share_gap_ge_8c_spread_le_4c"] >= 2 * (s_p["share_gap_ge_8c_spread_le_4c"] if s_p else 0): verdict = "SURVIVES the measurement (share at least 10 percent and at least twice the placebo's): a separate registration, tries = surviving cells"
            else: verdict = "CLOSED: efficient, move on. The one number: the 90th percentile gap %s" % (s_t["gap_quartiles_p90"] and s_t["gap_quartiles_p90"][3])
            out["groups"][grp][typ] = {"games_with_a_target": der, "filled": filled, "share_filled": share_filled, "targets": s_t, "placebo": s_p, "verdict": verdict}
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    else:
        spec = load_cells()
        if a[0] == "build-lists": print(json.dumps(build_lists(spec), indent=1))
        elif a[0] == "games": print(json.dumps(games(spec, a[1:])[1], indent=1))
        elif a[0] == "build-candles": j, c = build_candles(spec, a[1:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
        elif a[0] == "measure": i = a.index("--candles"); print(json.dumps(measure(spec, a[1:i], a[i + 1:]), indent=1))
