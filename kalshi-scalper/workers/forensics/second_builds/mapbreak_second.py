#!/usr/bin/env python3
"""MAPBREAK, an independent SECOND build of step 1 (Forensics desk, 2026-11-13, on the Head of R&D's order), rebuilt to the FINAL text:
Desk B's registration and Amendments 1 to 11 (workers/mapbreak/MAPBREAK_REGISTRATION.md at 31bf8552 on claude/idea-desk-b). The first version of this file
(commit db1c0354) followed Amendments 1 to 7 and is what found the float comparison on the 4c line.
DISCLOSURE: this desk leak-audited the Testing Desk's mapbreak.py and breakplay.py on Nov 12, so it is not a clean-room reader; every place where the text alone
did not settle a choice is listed in AMBIGUITIES and printed.

Step 1 only: counts, the observable state, decisions and fills at each look, the one-way cost, the gap share and its placebo. NO MATCH RESULT IS READ ANYWHERE IN
THIS FILE: the result field of a match market and of a map-3 market is never touched. A map-1 or map-2 result is read for ONE count only (Amendment 7, point 1):
looks where the observed winner differs from the posted result. It never names a team.
usage: python3 -I mapbreak_second.py measure [--second-look-planned-from-posted-results] --lists <run folder ...> --candles <run folder ...>
  --second-look-planned-from-posted-results: the DISCLOSED LIMIT of the landed data (Amendment 11, line 3): a second look only for matches whose POSTED map results say one map each.
Invented rows only until the Head says otherwise: this file refuses any HELDOUT_ folder and any match closing on or after 2026-10-23T00:00Z.
"""
import sys, os, json, gzip, math, calendar, time, statistics as st, collections
from datetime import datetime
from zoneinfo import ZoneInfo

TITLES = {"CS2": ("KXCS2GAME", "KXCS2MAP", "KXCS2TOTALMAPS"), "DOTA2": ("KXDOTA2GAME", "KXDOTA2MAP", "KXDOTA2TOTALMAPS"),
          "VALORANT": ("KXVALORANTGAME", "KXVALORANTMAP", "KXVALORANTTOTALMAPS"), "LOL": ("KXLOLGAME", "KXLOLMAP", "KXLOLTOTALMAPS")}
def _ts(s): return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
DEV_FROM, DEV_BEFORE = _ts("2026-09-12T00:00:00"), _ts("2026-10-23T00:00:00")
NY = ZoneInfo("America/New_York"); MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
START_LO, START_HI = 15 * 60, 150 * 60            # map 1 must have ended 15 to 150 minutes after S
PRE_BACK, PRE_MAX = 10 * 60, 40 * 60              # pre-match minute: S - 10, stepping back to S - 40
LOOK_AFTER, LOOK_MAX = 120, 300                   # the look: first whole minute at or after close + 120 s, forward to close + 5 minutes
GAP_LINE, SPREAD_LINE, SLIP = 0.08, 0.04, 0.01
MIN_FILLED, COST_KILL, SHARE_LINE = 150, 0.04, 0.10
OBS_BID = 0.90                                    # Amendments 8 and 9: the winner's OWN map contract shows a best bid of 0.90 or more
OBS_AGE = 10 * 60                                 # Amendment 10, line 7: that candle must end no earlier than 10 minutes before the map market's close
EPS = 1e-9                                        # Amendment 10, line 6: every "or less" and "or more" carries this tolerance
AMBIGUITIES = [
    "1. A match's close time (for the 2026-09-12 to 2026-10-23 window): the later close_time of its two match markets. A map's close: the later close_time of its two contracts; the age limit of Amendment 10 line 7 uses each contract's OWN close_time.",
    "2. A quote candle carries a bid above 0 or an ask below 1; a zero bid with an ask of 1 is an empty book (Amendment 10, line 9, no longer a choice). The state candle is the last quote candle ending at or before the map market's close (line 10); each contract's OWN close_time is used for the cap and for the 10 minute age limit.",
    "3. The age limit is applied to both teams' candles: a candle that ended more than 10 minutes before its map market's close shows no 0.90 bid for either team. A contract with no quote candle at all at or before its close makes the state not observable (Amendments 7 and 8, point 3).",
    "4. The pre-match minute for a named map-1 winner W: the first minute from S-10 back to S-40 at which W's match contract and BOTH map-1 contracts are two-sided (Amendment 3). 'Look reached' (Amendment 10, line 3) for a look whose state is NOT observable cannot name W; it is counted when such a minute exists for EITHER team, and the count for BOTH teams is printed beside it.",
    "5. Looks left = a look minute, an observable state and a pre-match minute for the map-1 winner. The gap share, the placebo share and the cost line are over the looks left, per title and look. The cost the kill reads is (ask minus mid) plus the fee at the limit (Amendment 11, line 1); (limit minus mid) plus the fee is printed beside it.",
    "6. Equal gaps (within 1e-9): no bet, counted (Amendment 10, line 4). The look stays in the looks left: it is in the gap distribution with its gap, it is not a hit for the gap share, and it has no cheaper side, so it is left out of the cost line.",
    "7. The fill (Amendment 9, point 2): the candle ending exactly one minute after the look minute must exist and carry an ask at or under the limit (the look candle's ask plus 1c). No candle that minute, or no ask in it, is 'not filled'. It does not have to be two-sided.",
    "8. 'Median spread of the match contracts' at the look: over BOTH match contracts of every look left (two values a look).",
    "9. Quartiles and the 90th percentile: linear interpolation between order statistics (position (n-1) x p).",
    "10. The placebo, per look: over the same matches as that look's looks left, at their pre-match minute: gap of the map-1 winner = q minus the ask of its MAP-1 contract; of the other team = (1 minus q) minus the ask of its map-1 contract; the cheaper side is the larger gap; the spread on the 4c line is that map-1 contract's. Equal gaps are not a hit.",
    "11. Second look: map 1's winner is the one observed at the first look; if it was not observable there (or there was no first look minute), it is taken again at the SECOND look's minute (Amendment 10, line 5). Map 2's winner is observed at the second look's minute. Same winner twice is 'no break'.",
    "12. Minutes from the map close to the look: (look minute minus the map's close) / 60, median over the looks left.",
    "13. Kill lines, first that applies: under 150 fired AND filled bets = 'no evidence at n = x'; median one-way cost above 4c = CLOSED on cost; gap share under 10% or under twice the placebo's = 'efficient, move on'; else IN at that look.",
    "14. 'Optimistic, same-candle fill' (Amendment 9, point 3): the number of decisions (fired), every one booked at the look candle's ask plus 1c. Printed beside the filled count; information only.",
]


def refuse_heldout(path):
    if any(p.upper().startswith("HELDOUT_") for p in os.path.realpath(path).split(os.sep) + os.path.abspath(path).split(os.sep)):
        raise SystemExit("refused: %s is a HELDOUT_ folder (standing rule (h))" % path)


def answers(folder):
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and row.get("file") and not row.get("truncated"):
            yield json.load(gzip.open(os.path.join(folder, row["file"])))


def start_of(key):
    try: return int(datetime(2000 + int(key[0:2]), MON[key[2:5]], int(key[5:7]), int(key[7:9]), int(key[9:11]), tzinfo=NY).timestamp())
    except (KeyError, ValueError, IndexError): return None


def read_lists(folders):
    """-> {(cell, key): {"match": {team: {close}}, "maps": {n: {team: {close, result}}}, "strikes": [floor_strike...]}}. A match market's result is never stored."""
    ser = {}
    for cell, (g, m, t) in TITLES.items(): ser[g] = (cell, "match"); ser[m] = (cell, "map"); ser[t] = (cell, "total")
    ev = collections.defaultdict(lambda: {"match": {}, "maps": collections.defaultdict(dict), "strikes": []})
    for f in folders:
        for body in answers(f):
            for mk in body.get("markets", []) if isinstance(body, dict) else []:
                if not isinstance(mk, dict) or "candlesticks" in mk: continue
                tk = str(mk.get("ticker", "")); parts = tk.split("-")
                if parts[0] not in ser or len(parts) < 3: continue
                cell, kind = ser[parts[0]]; key = parts[1]
                try: close = _ts(mk.get("close_time") or "")
                except Exception: close = None
                e = ev[(cell, key)]
                if kind == "match" and len(parts) == 3: e["match"][parts[2]] = {"ticker": tk, "close": close}
                elif kind == "map" and len(parts) == 4:
                    try: n = int(parts[2])
                    except ValueError: continue
                    e["maps"][n][parts[3]] = {"ticker": tk, "close": close, "result": (mk.get("result") or "").lower()}
                elif kind == "total":
                    try: e["strikes"].append(float(mk.get("floor_strike")))
                    except (TypeError, ValueError): pass
    return ev


def read_candles(folders):
    out = {}
    for f in folders:
        for body in answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list): continue
                t = n.get("market_ticker") or n.get("ticker"); d = out.setdefault(t, {})
                for c in n["candlesticks"]:
                    def px(side):
                        s = c.get(side)
                        if not isinstance(s, dict): return None
                        for k in ("close_dollars", "close"):
                            v = s.get(k)
                            if v in (None, ""): continue
                            try: v = float(v)
                            except (TypeError, ValueError): continue
                            return v / 100.0 if (k == "close" and v > 1.0) else v
                        return None
                    try: d[int(c["end_period_ts"])] = (px("yes_bid"), px("yes_ask"))
                    except (KeyError, TypeError, ValueError): pass
    return out


def two(cd, ticker, ts):
    q = (cd.get(ticker) or {}).get(ts)
    return q if q and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1 else None


def per_map_chance(p):
    """q in (0, 1) with q*q*(3 - 2q) = p (the chance of two maps of three at q a map)."""
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if mid * mid * (3 - 2 * mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def fee_up(p): return math.ceil(0.07 * p * (1 - p) * 100 - 1e-9) / 100.0


def quant(xs, p):
    xs = sorted(xs)
    if not xs: return None
    i = (len(xs) - 1) * p; a, b = math.floor(i), math.ceil(i)
    return round(xs[a] + (xs[b] - xs[a]) * (i - a), 4)


def look_minute(cd, close, tickers):
    t = ((close + LOOK_AFTER + 59) // 60) * 60
    while t <= close + LOOK_MAX:
        if all(two(cd, x, t) for x in tickers): return t
        t += 60
    return None


def quote_candle(cd, ticker, ts):
    """the LAST candle ending at or before ts that carries a bid or an ask -> (end, bid or None, ask or None), else None.
    Amendment 10, line 9: a bid of 0.00 with an ask of 1.00 is an empty book, not a quote."""
    d = cd.get(ticker) or {}; best = None
    for k, (b, a) in d.items():
        if k > ts: continue
        hb, ha = (b is not None and b > EPS), (a is not None and a < 1 - EPS)
        if (hb or ha) and (best is None or k > best[0]): best = (k, b if hb else None, a if ha else None)
    return best


def observed_winner(cd, mp, ts):
    """Amendments 8, 9 and 10. mp: {team: {ticker, close}} of one map. -> team, or None when the state is not observable at ts."""
    shows = {}
    for x, v in mp.items():
        c = quote_candle(cd, v["ticker"], min(ts, v["close"]))                       # Amendment 10, line 10: never a candle ending after the map market's close
        if c is None: return None
        shows[x] = c[1] is not None and c[1] >= OBS_BID - EPS and c[0] >= v["close"] - OBS_AGE
    won = [x for x in shows if shows[x]]
    return won[0] if len(won) == 1 else None


def result_winner(mp):
    yes = [x for x in mp if mp[x]["result"] == "yes"]
    return yes[0] if len(yes) == 1 else None


def pre_minute(cd, S, match_ticker, map1_tickers):
    for back in range(PRE_BACK, PRE_MAX + 1, 60):
        t = S - back; a = two(cd, match_ticker, t)
        if a is None: continue
        bs = [two(cd, x, t) for x in map1_tickers]
        if all(bs): return t, a, bs
    return None


def side_row(gw, qw, go, qo):
    """the cheaper side = the larger gap. qw, qo: (bid, ask) of the two contracts. Equal gaps: no side."""
    if abs(gw - go) < EPS: return {"gap": gw, "side": None}
    g, q, side = (gw, qw, "map-1 winner") if gw > go else (go, qo, "other team")
    return {"gap": g, "side": side, "bid": q[0], "ask": q[1], "spread": q[1] - q[0], "hit": g >= GAP_LINE - EPS and q[1] - q[0] <= SPREAD_LINE + EPS}


def stats(rows):
    if not rows: return None
    g = [r["gap"] for r in rows]; hit = [r for r in rows if r.get("hit")]
    return {"n": len(rows), "gap_median": quant(g, .5), "gap_q25": quant(g, .25), "gap_q75": quant(g, .75), "gap_p90": quant(g, .9), "share_gap_8c_spread_4c": round(len(hit) / len(rows), 4),
            "of_which_map_1_winner": round(sum(1 for r in hit if r["side"] == "map-1 winner") / len(rows), 4), "of_which_other_team": round(sum(1 for r in hit if r["side"] == "other team") / len(rows), 4)}


def measure(list_folders, candle_folders, second_look_planned_from_posted_results=False):
    ev = read_lists(list_folders); cd = read_candles(candle_folders)
    T = {c: {"counts": collections.Counter(), "L": {1: [], 2: []}, "P": {1: [], 2: []}, "cost": {1: [], 2: []}, "paid": {1: [], 2: []}, "spr": {1: [], 2: []}, "mins": {1: [], 2: []}} for c in TITLES}
    for (cell, key), e in sorted(ev.items()):
        C = T[cell]["counts"]
        if len(e["match"]) != 2 or any(v["close"] is None for v in e["match"].values()): continue
        close = max(v["close"] for v in e["match"].values())
        if close >= DEV_BEFORE: C["held_out_refused"] += 1; continue
        if close < DEV_FROM: C["before_the_window"] += 1; continue
        C["matches_listed"] += 1
        m1, m2 = e["maps"].get(1, {}), e["maps"].get(2, {})
        okmap = lambda m: len(m) == 2 and set(m) == set(e["match"]) and all(v["close"] is not None for v in m.values())
        if not (e["strikes"] and max(e["strikes"]) == 2.5 and okmap(m1) and okmap(m2)): C["not_best_of_three"] += 1; continue      # Amendment 10, line 1: map markets 1 AND 2
        C["best_of_three"] += 1
        S = start_of(key); c1 = max(v["close"] for v in m1.values()); c2 = max(v["close"] for v in m2.values())
        if S is None or not (START_LO <= c1 - S <= START_HI): C["start_not_derivable"] += 1; continue
        C["start_derivable"] += 1
        teams = sorted(e["match"]); mt = {x: e["match"][x]["ticker"] for x in teams}; m1t = [m1[x]["ticker"] for x in teams]
        pre = {x: pre_minute(cd, S, mt[x], m1t) for x in teams}

        def look(k, L, w1, value_of_w1):
            """one look that has a minute L and a named map-1 winner w1 with a pre-match minute. value_of_w1: the model's value of w1's match contract at this look, from q."""
            other = [x for x in teams if x != w1][0]; t0, a0, bs = pre[w1]; q = per_map_chance((a0[0] + a0[1]) / 2); v = value_of_w1(q)
            qw, qo = two(cd, mt[w1], L), two(cd, mt[other], L)
            row = side_row(v - qw[1], qw, (1 - v) - qo[1], qo)
            T[cell]["L"][k].append(row); T[cell]["spr"][k] += [qw[1] - qw[0], qo[1] - qo[0]]
            bw, bo = bs[teams.index(w1)], bs[teams.index(other)]
            T[cell]["P"][k].append(side_row(q - bw[1], bw, (1 - q) - bo[1], bo))
            C["look_%d_looks_left" % k] += 1
            if row["side"] is None: C["look_%d_equal_gaps_no_bet" % k] += 1; return
            limit = round(row["ask"] + SLIP, 6); mid_ = (row["ask"] + row["bid"]) / 2
            T[cell]["cost"][k].append((row["ask"] - mid_) + fee_up(limit))              # Amendment 11, line 1: the KILL reads the template, (ask minus mid) plus the fee as charged at the limit
            T[cell]["paid"][k].append((limit - mid_) + fee_up(limit))                   # printed beside it: cost as paid at the limit, information only
            if not row["hit"]: return
            C["look_%d_fired_optimistic_same_candle_fill" % k] += 1
            nxt = (cd.get(mt[w1 if row["side"] == "map-1 winner" else other]) or {}).get(L + 60)
            if nxt is not None and nxt[1] is not None and nxt[1] < 1 - EPS and nxt[1] <= limit + EPS: C["look_%d_fired_and_filled" % k] += 1
            else: C["look_%d_fired_not_filled" % k] += 1

        def reached_unnamed(k):
            if any(pre.values()): C["look_%d_reached_state_not_observable" % k] += 1
            if all(pre.values()): C["look_%d_reached_state_not_observable_pre_match_minute_for_both_teams" % k] += 1
            if not any(pre.values()): C["look_%d_minute_found_but_no_pre_match_minute_and_state_not_observable" % k] += 1

        # ---- first look
        L1 = look_minute(cd, c1, list(mt.values())); w1 = None
        if L1 is None: C["look_1_no_look_minute"] += 1
        else:
            C["look_1_minute_found"] += 1
            w1 = observed_winner(cd, m1, L1)
            if w1 is None: reached_unnamed(1)
            else:
                rw = result_winner(m1)
                if rw is not None and rw != w1: C["count_only_look_1_observed_winner_differs_from_the_posted_map_result"] += 1
                if pre[w1] is None: C["look_1_observable_but_no_pre_match_minute"] += 1
                else:
                    C["look_1_reached_state_observable"] += 1; T[cell]["mins"][1].append((L1 - c1) / 60.0)
                    look(1, L1, w1, lambda q: 1 - (1 - q) ** 2)
        # ---- second look: one map each
        L2 = look_minute(cd, c2, list(mt.values()))
        p1, p2 = result_winner(m1), result_winner(m2); posted_one_each = p1 is not None and p2 is not None and p1 != p2       # MAP results only, for the disclosed limit and one count; never names a team
        if second_look_planned_from_posted_results and not posted_one_each: C["look_2_not_in_the_posted_results_plan"] += 1; continue
        if L2 is None: C["look_2_no_look_minute"] += 1; continue
        C["look_2_minute_found"] += 1
        w1b = w1 if w1 is not None else observed_winner(cd, m1, L2); w2 = observed_winner(cd, m2, L2)
        if w1b is None or w2 is None: reached_unnamed(2); continue
        rw2 = result_winner(m2)
        if rw2 is not None and rw2 != w2: C["count_only_look_2_observed_map_2_winner_differs_from_the_posted_map_result"] += 1
        if w2 == w1b: C["look_2_no_break_same_winner_twice"] += 1; continue
        C["look_2_one_map_each"] += 1
        if not posted_one_each: C["count_only_look_2_observed_one_map_each_but_the_posted_results_do_not_say_so"] += 1
        if pre[w1b] is None: C["look_2_observable_but_no_pre_match_minute"] += 1; continue
        C["look_2_reached_state_observable"] += 1; T[cell]["mins"][2].append((L2 - c2) / 60.0)
        look(2, L2, w1b, lambda q: q)
    out = {"build": "Forensics second build of MAPBREAK step 1, Amendments 1 to 11", "match_results_read": 0,
           "second_look_sample": ("planned from posted results: a known limit; it can only flatter the second look (Amendment 11, line 3)" if second_look_planned_from_posted_results else "by observed winners, as the text says (on landed data the candles were pulled only for matches whose posted results say one map each)"), "freshness": "candle freshness measured on Bitcoin 15 minute only, not on esports",
           "label": "selected on development: these lines can close a title, they cannot support a result", "titles": {}, "ambiguities": AMBIGUITIES}
    for cell, D in T.items():
        C = D["counts"]; res = {"counts": dict(sorted(C.items()))}
        for k, name in ((1, "look_1_after_map_1"), (2, "look_2_before_map_3")):
            s, pl = stats(D["L"][k]), stats(D["P"][k]); cost = quant(D["cost"][k], .5); filled = C["look_%d_fired_and_filled" % k]
            share = s["share_gap_8c_spread_4c"] if s else 0.0; pshare = pl["share_gap_8c_spread_4c"] if pl else 0.0
            if filled < MIN_FILLED: v = "no evidence at n = %d fired and filled" % filled
            elif cost is not None and cost > COST_KILL + EPS: v = "CLOSED on cost: median one-way entry cost %.1fc above 4c" % (100 * cost)
            elif not (share >= SHARE_LINE - EPS and share >= 2 * pshare - EPS): v = "CLOSED: efficient, move on (90th percentile gap %s)" % s["gap_p90"]
            else: v = "IN at this look"
            reached = C["look_%d_reached_state_observable" % k] + C["look_%d_reached_state_not_observable" % k]
            res[name] = {"looks_reached": reached, "of_which_state_observable": C["look_%d_reached_state_observable" % k], "looks_left": len(D["L"][k]),
                         "fired_optimistic_same_candle_fill": C["look_%d_fired_optimistic_same_candle_fill" % k], "fired_and_filled": filled,
                         "median_minutes_from_the_map_close": quant(D["mins"][k], .5), "median_spread_of_the_match_contracts": quant(D["spr"][k], .5),
                         "median_one_way_cost_over_the_looks_left": cost, "cost_as_paid_at_the_limit_information_only": quant(D["paid"][k], .5), "gap_on_the_cheaper_side": s,
                         "placebo_at_the_pre_match_minute_same_matches": pl, "placebo_denominators": "this look's own looks: %d; the title's first-look looks: %d" % (len(D["P"][k]), len(D["P"][1])), "verdict": v}
        out["titles"][cell] = res
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 5 or a[0] != "measure" or "--lists" not in a or "--candles" not in a: print(__doc__); print("\n".join(AMBIGUITIES)); sys.exit(2)
    plan = "--second-look-planned-from-posted-results" in a; a = [x for x in a if x != "--second-look-planned-from-posted-results"]
    i, j = a.index("--lists"), a.index("--candles")
    print(json.dumps(measure(a[i + 1:j], a[j + 1:], second_look_planned_from_posted_results=plan), indent=1))
