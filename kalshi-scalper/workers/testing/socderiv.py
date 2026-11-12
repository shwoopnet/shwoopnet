#!/usr/bin/env python3
"""SOCDERIV (Desk B card 19) MEASUREMENT reader, job builders and scorer on scorekit. Testing Desk, Nov 12, 2026.
Research only: reads files, sends nothing. ZERO TRIES: scores no rule and adds no try. No outcome is read (settled lists are the only way to list finished games; their `result` field is never used here).
Built against synthetic data; Desk B's registration and the frozen cells file must exist before any data is opened.
Head's conditions, enforced in code:
  - prices from minute-end candles only, never a list quote; EVERY leg at the SAME minute (a winner x3, the total-goals ladder strikes, both-teams-to-score, the team totals): that minute must have a two-sided quote
    on every leg; thin, one-sided or missing minutes are COUNTED, not filled; the instant is the LAST such minute at or before kickoff minus 30 minutes, scanning back at most 60 minutes;
  - if fewer than SAME_MINUTE_SHARE (30 percent, the Head's suggestion, fixed now) of the games meet the same-minute condition, the measurement stops: "cannot be measured at minute resolution";
  - cutoffs are date constants: games closing from CUTOVER (2026-09-12, the live endpoint's range) to HELD_OUT_FROM (2026-11-13T00:00Z, never listed or requested);
  - cells fixed before data: the cells file sha256 must equal CELLS_SHA256 (None = not frozen, the code refuses to build jobs).
Cells file (socderiv_cells.json), one object per league: {"league","winner_series","total_series","btts_series","teamtotal_series","total_strikes":[1.5,2.5,3.5],"teamtotal_strike":1.5,
  "kickoff_rule":{...as tie3: field | ticker_local | close_offset}}. A game is the same suffix after the series prefix in each series' event ticker (ASSUMED, verify on the first list answer).
Model (Desk B's card): two independent Poisson goal rates fitted by least squares to the winner mids and the total ladder mids; implied BTTS yes = (1-e^-lh)(1-e^-la); implied team total over k = P(Poisson(l) > k).
Commands: build-lists <cells> | games <cells> <lists...> | build-candles <cells> <lists...> | measure <cells> <lists...> --candles <folders...>
"""
import calendar, hashlib, json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3

CUTOVER, HELD_OUT_FROM = tie3.CUTOVER, tie3.HELD_OUT_FROM
CELLS_SHA256 = None
GAP, SPREAD_MAX, SAME_MINUTE_SHARE, MIN_GAMES, EDGE_SHARE, TWO_SIDED_SHARE = 0.08, 0.04, 0.30, 150, 0.10, 0.50
BEFORE_S, SCAN_S, PACK_SPAN_S, PACK_LIMIT = 30 * 60, 60 * 60, 3 * 3600, 9000
REG = "kalshi-scalper/workers/testing/SOCDERIV_MEASUREMENT.md"
GROUPS = ("winner", "total", "btts", "teamtotal")


def load_cells(path, require_frozen=True):
    if require_frozen and CELLS_SHA256 is None:
        raise SystemExit("refused: CELLS_SHA256 is not set; the cells are not frozen (Desk B's registration must carry the hash)")
    raw = open(path, "rb").read()
    if require_frozen and hashlib.sha256(raw).hexdigest() != CELLS_SHA256:
        raise SystemExit("refused: the cells file does not match the frozen sha256")
    return json.loads(raw)


def series_of(c): return {g: c[g + "_series"] for g in GROUPS}


def build_lists(cells):
    reqs, series = [], sorted({s for c in cells for s in series_of(c).values()})
    for s in series:
        reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "min_close_ts": CUTOVER, "max_close_ts": HELD_OUT_FROM - 1}, "max_pages": 6})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]}]
    j = tie3.job("SOCDERIV_LISTS", "SOCDERIV measurement stage 1: settled lists of the soccer winner, total-goals, both-teams-to-score and team-total series (time and strike fields; no result used).", eps, reqs, series, [])
    j["registration"] = REG; return j


def games(cells, list_folders):
    """-> [ {league, game, kickoff, legs: {ticker: leg}} ] and counts. legs hold group, strike_type, floor, cap, side; NO result field is kept."""
    ms = k.markets(list_folders)
    by = {}
    for t, m in ms.items():
        by.setdefault((m["series"], m["event"].split("-", 1)[1] if "-" in m["event"] else m["event"]), []).append(m)
    out, counts = [], {"games_seen": 0, "missing_group": 0, "no_kickoff": 0, "held_out_dropped": 0}
    for c in cells:
        ser = series_of(c); suffixes = {g: {gm for (s, gm) in by if s == ser[g]} for g in GROUPS}
        for gm in sorted(suffixes["winner"]):
            counts["games_seen"] += 1
            if not all(gm in suffixes[g] for g in GROUPS):
                counts["missing_group"] += 1; continue
            legs, allm = {}, []
            for g in GROUPS:
                for m in by[(ser[g], gm)]:
                    allm.append(m)
                    legs[m["ticker"]] = {"group": g, "type": m["type"], "floor": m["floor"], "cap": m["cap"], "title": m["title"], "close": m["close"], "ticker": m["ticker"]}
            if max(m["close"] for m in allm if m["close"]) >= HELD_OUT_FROM:
                counts["held_out_dropped"] += 1; continue
            ko = tie3.start_ts(gm, allm, c.get("kickoff_rule"))
            if ko is None:
                counts["no_kickoff"] += 1; continue
            keep = {t: l for t, l in legs.items() if l["group"] in ("winner", "btts", "teamtotal") or (l["group"] == "total" and l["floor"] in set(c.get("total_strikes", [])))}
            out.append({"league": c["league"], "game": gm, "kickoff": ko, "legs": keep, "teamtotal_strike": c.get("teamtotal_strike", 1.5)})
    return out, counts


def build_candles(cells, list_folders):
    gs, counts = games(cells, list_folders)
    items = sorted(((g["kickoff"], t) for g in gs for t in g["legs"]), key=lambda x: x[0])
    packs, cur = [], []
    for ko, t in items:
        trial = cur + [(ko, t)]
        span = trial[-1][0] - trial[0][0] + BEFORE_S + SCAN_S + 120
        if cur and (span > PACK_SPAN_S + BEFORE_S + SCAN_S or span / 60 * len(trial) > PACK_LIMIT):
            packs.append(cur); cur = [(ko, t)]
        else:
            cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for _, t in p), "start_ts": p[0][0] - BEFORE_S - SCAN_S - 60, "end_ts": p[-1][0] - BEFORE_S + 60, "period_interval": 1}} for i, p in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    j = tie3.job("SOCDERIV_CANDLES", "SOCDERIV measurement stage 2: one minute candles of every leg of each game, the 90 minutes before kickoff minus 30 minutes.", eps, reqs, {s for c in cells for s in series_of(c).values()}, [t for _, t in items])
    j["registration"] = REG; return j, counts


def pois(l, n):
    return math.exp(-l) * l ** n / math.factorial(n)


def p_total_over(lh, la, strike):
    lam = lh + la; return 1 - sum(pois(lam, n) for n in range(0, int(strike) + 1))        # strike x.5: total > x.5 is total >= x+1


def p_winner(lh, la, N=14):
    h = a = d = 0.0
    for i in range(N):
        for j in range(N):
            p = pois(lh, i) * pois(la, j)
            if i > j: h += p
            elif i == j: d += p
            else: a += p
    return h, d, a


def fit(win_mid, total_mid):
    """Least squares over a coarse then a fine grid of (lh, la). win_mid = (home, draw, away) mids; total_mid = {strike: mid of 'over strike'}. Returns (lh, la, rmse)."""
    s = sum(win_mid); wm = [x / s for x in win_mid] if s > 0 else win_mid
    def err(lh, la):
        h, d, a = p_winner(lh, la)
        e = [(h - wm[0]) ** 2, (d - wm[1]) ** 2, (a - wm[2]) ** 2] + [(p_total_over(lh, la, kk) - v) ** 2 for kk, v in total_mid.items()]
        return sum(e)
    best = min(((err(lh / 20, la / 20), lh / 20, la / 20) for lh in range(2, 81, 2) for la in range(2, 81, 2)))
    e0, lh0, la0 = best
    best = min(((err(lh0 + i / 200, la0 + j / 200), lh0 + i / 200, la0 + j / 200) for i in range(-10, 11) for j in range(-10, 11) if lh0 + i / 200 > 0.02 and la0 + j / 200 > 0.02))
    n = 3 + len(total_mid)
    return best[1], best[2], (best[0] / n) ** 0.5


def implied(lh, la, tt_strike):
    return {"btts_yes": (1 - math.exp(-lh)) * (1 - math.exp(-la)), "home_tt_over": 1 - sum(pois(lh, n) for n in range(0, int(tt_strike) + 1)), "away_tt_over": 1 - sum(pois(la, n) for n in range(0, int(tt_strike) + 1))}


def quote(by_ts, ts):
    c = by_ts.get(ts)
    if not c or c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): return None
    return c["bid"], c["ask"]


def measure(cells, list_folders, candle_folders):
    gs, counts = games(cells, list_folders)
    cs = k.candles(candle_folders)
    idx = {t: {c["ts"]: c for c in v} for t, v in cs.items()}
    n_games, n_same, priced, gaps_all, two_thin = 0, 0, 0, [], 0
    thin_quoted, edge_hits, per_league = 0, 0, {}
    for g in gs:
        n_games += 1; L = per_league.setdefault(g["league"], {"games": 0, "same_minute": 0})
        L["games"] += 1
        last = g["kickoff"] - BEFORE_S
        found = None
        for m in range(0, SCAN_S // 60 + 1):                  # the last minute at or before kickoff - 30 min with EVERY leg two-sided
            ts = last - 60 * m
            if all(quote(idx.get(t, {}), ts) for t in g["legs"]): found = ts; break
        if found is None: continue
        n_same += 1; L["same_minute"] += 1
        mid = lambda t: sum(quote(idx[t], found)) / 2
        legs = g["legs"]
        win = {l["title"]: t for t, l in legs.items() if l["group"] == "winner"}
        wt = [t for t, l in legs.items() if l["group"] == "winner"]
        if len(wt) != 3: continue
        # winner legs sorted by their 'yes_sub_title' is unknown here; require exactly home, tie, away by ticker suffix order: TIE is the draw, the others ordered by ticker
        draw = [t for t in wt if t.endswith("-TIE")]
        if len(draw) != 1: continue
        teams = sorted(t for t in wt if t not in draw)
        totals = {l["floor"]: mid(t) for t, l in legs.items() if l["group"] == "total" and l["floor"] is not None}
        if not totals: continue
        lh, la, rmse = fit((mid(teams[0]), mid(draw[0]), mid(teams[1])), totals)
        imp = implied(lh, la, g["teamtotal_strike"])
        priced += 1
        for t, l in legs.items():
            if l["group"] == "btts": key = "btts_yes"
            elif l["group"] == "teamtotal": key = "home_tt_over" if t == (sorted(x for x, y in legs.items() if y["group"] == "teamtotal")[0]) else "away_tt_over"
            else: continue
            b, a = quote(idx[t], found)
            if a - b > SPREAD_MAX: continue
            thin_quoted += 1
            yes_gap, no_gap = imp[key] - a, (1 - imp[key]) - (1 - b)       # YES at the ask; NO at 1 - bid
            gap = max(yes_gap, no_gap); gaps_all.append(gap)
            if gap >= GAP: edge_hits += 1
    share_same = n_same / n_games if n_games else 0
    res = {"counts_first": counts, "games_with_all_four_groups_and_a_kickoff": n_games, "games_with_every_leg_two_sided_in_one_minute": n_same, "share_same_minute": round(share_same, 3), "games_priced": priced,
           "contracts_quoted_spread_le_4c": thin_quoted, "contracts_with_gap_ge_8c": edge_hits, "share_with_gap_ge_8c": round(edge_hits / thin_quoted, 3) if thin_quoted else None,
           "gap_q1_median_q3_p90": (lambda q: [round(x, 4) for x in q])([st.quantiles(gaps_all, n=4, method="inclusive")[0], st.median(gaps_all), st.quantiles(gaps_all, n=4, method="inclusive")[2], st.quantiles(gaps_all, n=10, method="inclusive")[8]]) if len(gaps_all) > 2 else None,
           "per_league": per_league, "tries_added": 0, "rule_scored": False, "outcome_read": False,
           "price_source": "1 minute candle bid/ask close, every leg in the same minute (not a list quote); freshness assumed on these series (CANDLEVSBOOK1 measured KXBTC15M only)",
           "model_note": "independent Poisson goals understate draws and low scores, moving both-teams-to-score by about a point (Desk B's own note); a gap may be the model's, not the market's"}
    if n_games and share_same < SAME_MINUTE_SHARE: res["verdict"] = "STOPPED: cannot be measured at minute resolution (%.0f%% of games have every leg two-sided in one minute, under the fixed %.0f%%)" % (100 * share_same, 100 * SAME_MINUTE_SHARE)
    elif priced < MIN_GAMES: res["verdict"] = "no evidence at n = %d priced games (under %d)" % (priced, MIN_GAMES)
    elif priced and n_same / max(1, n_games) < TWO_SIDED_SHARE: res["verdict"] = "CLOSED: not tradable (under half of the games have a two-sided quote on the thin contracts)"
    elif thin_quoted and edge_hits / thin_quoted < EDGE_SHARE: res["verdict"] = "CLOSED: efficient, move on. The one number: the 90th percentile gap %s" % (res["gap_q1_median_q3_p90"] and res["gap_q1_median_q3_p90"][3])
    else: res["verdict"] = "SURVIVES the measurement: at least 10 percent of quoted contracts show an ask 8c or more under the implied value; the registered try is separate (1 try, date constants, read once)"
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == "build-lists": print(json.dumps(build_lists(load_cells(a[1])), indent=1))
    elif a[0] == "games": print(json.dumps(games(load_cells(a[1]), a[2:])[1], indent=1))
    elif a[0] == "build-candles": j, c = build_candles(load_cells(a[1]), a[2:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
    elif a[0] == "measure":
        i = a.index("--candles"); print(json.dumps(measure(load_cells(a[1]), a[2:i], a[i + 1:]), indent=1, default=str))
