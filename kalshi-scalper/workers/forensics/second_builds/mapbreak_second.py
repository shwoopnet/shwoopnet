#!/usr/bin/env python3
"""MAPBREAK, an independent SECOND build of step 1 (Forensics desk, 2026-11-13, on the Head of R&D's order).
Built from Desk B's registration text and its amendments (workers/mapbreak/MAPBREAK_REGISTRATION.md and MAPBREAK_SERIES.json on claude/idea-desk-b, Amendments 1 to 7),
not from the Testing Desk's mapbreak.py or breakplay.py. DISCLOSURE: this desk leak-audited those two files on Nov 12, so it is not a clean-room reader; every place where
the text alone did not settle a choice is listed in AMBIGUITIES and printed, and the choice made there is the text's nearest reading, not the other build's.

Step 1 only: counts, fills at each look, the one-way entry cost, the gap share and its placebo. NO MATCH RESULT IS READ ANYWHERE IN THIS FILE: the result field of a match
market and of a map-3 market is never touched. The map-1 and map-2 results are read only in state mode "result" (Amendments 4 to 6); in state mode "observed" (Amendment 7)
they are read only to count disagreements.
usage: python3 -I mapbreak_second.py measure <result|observed> --lists <run folder ...> --candles <run folder ...>
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
OBS_BID, OBS_ASK = 0.90, 0.10                     # Amendment 7
EPS = 1e-9
AMBIGUITIES = [
    "1. Best-of-three: the text (state point 1 and the series file) needs a total-maps market at 2.5, none higher, AND map markets 1 and 2 for the key. Built that way. Amendment 4 says every best-of-three with a derivable start gets a first look but does not drop the map-2 requirement.",
    "2. A match's close time (for the 2026-09-12 to 2026-10-23 window): the later close_time of its two match markets.",
    "3. Map 1's close time: the later close_time of its two map-1 markets. Same for map 2.",
    "4. State mode 'result': the team that is one map up is the one whose map-1 market has result yes; if not exactly one of the two map-1 markets says yes, the match has no state and is counted as 'map 1 has no single winner' and dropped. The text does not say.",
    "5. The one-way cost 'at qualifying decision minutes' (Amendment 5): built as the cheaper side's own contract at EVERY filled look ((ask minus mid) plus the fee at ask + 1c rounded up). The other reading, only the looks where the rule would fire (gap 8c or more and spread 4c or less), is printed beside it as one_way_cost_at_firing_looks.",
    "6. 'Median spread of the match contracts' at the look: over BOTH match contracts of every filled look (two values a look).",
    "7. The cheaper side when the two gaps are equal: the team that is up. The text does not say.",
    "8. Quartiles and the 90th percentile: linear interpolation between order statistics (position (n-1) x p).",
    "9. The placebo's 'same statistics': at the pre-match minute, gap of the up team = q minus the ask of its MAP-1 contract; of the other team = (1 minus q) minus the ask of its map-1 contract; the cheaper side is the larger gap; the spread on the 4c line is that map-1 contract's. Its share is over the matches filled at the pre-match minute (first look) and, for the second look's kill line, the same placebo share is used.",
    "10. The second look's fills and shares are over the matches that stand at one map each (the denominator of 'filled at the look' is those matches).",
    "11. The count of Amendment 4 point 3 (winner's own map contract bid 0.90 or more in its last two-sided candle at or before the map's close): counted over looks whose state is known, per title and look.",
    "12. Minutes from the map close to the look: (look minute minus the map's close) / 60, median over filled looks.",
    "13. Amendment 7, 'its last candle ending at or before the look minute, two-sided or one-sided': a candle counts if it carries a bid OR an ask; a missing bid cannot show 0.90 and a missing ask cannot show 0.10.",
    "14. Amendment 7 at the second look when map 1 was not observable at the first look: map 1's state is taken again from the map-1 contracts' last candles at or before the SECOND look minute.",
    "15. Kill lines are printed in this order and the first that applies is the verdict: under 150 filled = 'no evidence at n = x'; one-way cost above 4c = CLOSED on cost; share under 10% or under twice the placebo's = 'efficient, move on'; else the title is IN at that look.",
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


def last_candle(cd, ticker, ts):
    d = cd.get(ticker) or {}; ks = [k for k in d if k <= ts and (d[k][0] is not None or d[k][1] is not None)]
    return d[max(ks)] if ks else None


def observed_winner(cd, mp, ts):
    """Amendment 7. mp: {team: {ticker,...}} of one map. -> team, or None when the state is not observable at ts."""
    teams = sorted(mp); won = []
    for x in teams:
        o = [y for y in teams if y != x][0]; cx, co = last_candle(cd, mp[x]["ticker"], ts), last_candle(cd, mp[o]["ticker"], ts)
        if cx is None or co is None: return None
        if (cx[0] is not None and cx[0] >= OBS_BID - EPS) or (co[1] is not None and co[1] <= OBS_ASK + EPS): won.append(x)
    return won[0] if len(won) == 1 else None


def result_winner(mp):
    yes = [x for x in mp if mp[x]["result"] == "yes"]
    return yes[0] if len(yes) == 1 else None


def known_at_close(cd, mp, winner):
    """Amendment 4 point 3: the winner's own map contract had a bid of 0.90 or more in its last TWO-SIDED candle at or before the map's close. None if no such candle."""
    close = max(v["close"] for v in mp.values()); d = cd.get(mp[winner]["ticker"]) or {}
    ks = [k for k in d if k <= close and d[k][0] is not None and d[k][1] is not None and 0 < d[k][0] < d[k][1] < 1]
    return None if not ks else d[max(ks)][0] >= OBS_BID - EPS


def stats(rows):
    """rows: [{gap, spread, side}] on the cheaper side. The registered four numbers."""
    if not rows: return None
    g = [r["gap"] for r in rows]; hit = [r for r in rows if r["gap"] >= GAP_LINE - EPS and r["spread"] <= SPREAD_LINE + EPS]
    return {"n": len(rows), "gap_median": quant(g, .5), "gap_q25": quant(g, .25), "gap_q75": quant(g, .75), "gap_p90": quant(g, .9), "share_gap_8c_spread_4c": round(len(hit) / len(rows), 4),
            "of_which_team_up": round(sum(1 for r in hit if r["side"] == "up") / len(rows), 4), "of_which_team_down": round(sum(1 for r in hit if r["side"] == "down") / len(rows), 4)}


def cheaper(gu, su, au, gd, sd, ad):
    return {"gap": gu, "spread": su, "ask": au, "side": "up"} if gu >= gd - EPS else {"gap": gd, "spread": sd, "ask": ad, "side": "down"}


def measure(list_folders, candle_folders, state_mode, bo3_needs_map2=True):
    """bo3_needs_map2=True is the registration's text. False is offered ONLY to compare like for like with a build that does not require a map-2 market for a first look."""
    assert state_mode in ("result", "observed")
    ev = read_lists(list_folders); cd = read_candles(candle_folders)
    T = {c: {"counts": collections.Counter(), "L1": [], "L2": [], "placebo": [], "cost1": [], "cost2": [], "fire1": [], "fire2": [], "spr1": [], "spr2": [], "min1": [], "min2": [], "known1": [], "known2": []} for c in TITLES}
    for (cell, key), e in sorted(ev.items()):
        C = T[cell]["counts"]
        if len(e["match"]) != 2 or any(v["close"] is None for v in e["match"].values()): continue
        close = max(v["close"] for v in e["match"].values())
        if close >= DEV_BEFORE: C["held_out_refused"] += 1; continue
        if close < DEV_FROM: C["before_the_window"] += 1; continue
        C["matches_listed"] += 1
        m1, m2 = e["maps"].get(1, {}), e["maps"].get(2, {})
        has2 = len(m2) == 2 and set(m2) == set(e["match"]) and all(v["close"] is not None for v in m2.values())
        if not (e["strikes"] and max(e["strikes"]) == 2.5 and len(m1) == 2 and set(m1) == set(e["match"]) and all(v["close"] is not None for v in m1.values()) and (has2 or not bo3_needs_map2)):
            C["not_best_of_three"] += 1; continue
        C["best_of_three"] += 1
        if not has2: C["no_map_2_market_first_look_only"] += 1
        S = start_of(key); c1 = max(v["close"] for v in m1.values()); c2 = max(v["close"] for v in m2.values()) if has2 else None
        if S is None or not (START_LO <= c1 - S <= START_HI): C["start_not_derivable"] += 1; continue
        C["start_derivable"] += 1
        if has2 and c2 - c1 < 15 * 60: C["count_only_map_2_closed_under_15_minutes_after_map_1"] += 1
        teams = sorted(e["match"]); mt = {x: e["match"][x]["ticker"] for x in teams}
        # ---- the state of map 1
        look1 = look_minute(cd, c1, list(mt.values()))
        if state_mode == "result":
            up = result_winner(m1)
            if up is None: C["map_1_has_no_single_winner"] += 1; continue
        else:
            up = observed_winner(cd, m1, look1) if look1 is not None else None
            rw = result_winner(m1)
            if up is not None and rw is not None and up != rw: C["count_only_observed_map_1_winner_differs_from_the_posted_result"] += 1
        # ---- the pre-match minute needs the up team: in observed mode a match whose state was never observable has no model
        def pre_for(upteam):
            down = [x for x in teams if x != upteam][0]; lost_to_maps = False
            for back in range(PRE_BACK, PRE_MAX + 1, 60):
                ts_ = S - back; a = two(cd, mt[upteam], ts_)
                if a is None: continue
                b, c_ = two(cd, m1[upteam]["ticker"], ts_), two(cd, m1[down]["ticker"], ts_)
                if b is None or c_ is None: lost_to_maps = True; continue
                return ts_, a, b, c_, down, False
            return None, None, None, None, down, lost_to_maps
        pre = pre_for(up) if up is not None else None
        if up is not None:
            ts0, a0, b0, c0, down, lost = pre
            if ts0 is None:
                C["not_filled_pre_match"] += 1
                if lost: C["of_which_the_match_contract_was_two_sided_but_the_map_1_contracts_never_in_the_same_minute"] += 1
            else:
                C["filled_pre_match"] += 1
                p = (a0[0] + a0[1]) / 2; q = per_map_chance(p)
                T[cell]["placebo"].append(cheaper(q - b0[1], b0[1] - b0[0], b0[1], (1 - q) - c0[1], c0[1] - c0[0], c0[1]))
        # ---- first look
        if look1 is None: C["look_1_not_filled"] += 1
        elif up is None: C["look_1_state_not_observable"] += 1
        elif pre[0] is None: C["look_1_filled_but_no_pre_match_minute"] += 1
        else:
            V = 1 - (1 - q) ** 2; qu, qd = two(cd, mt[up], look1), two(cd, mt[down], look1)
            row = cheaper(V - qu[1], qu[1] - qu[0], qu[1], (1 - V) - qd[1], qd[1] - qd[0], qd[1])
            T[cell]["L1"].append(row); T[cell]["spr1"] += [qu[1] - qu[0], qd[1] - qd[0]]; T[cell]["min1"].append((look1 - c1) / 60.0)
            cost = row["spread"] / 2 + fee_up(round(row["ask"] + SLIP, 4)); T[cell]["cost1"].append(cost)
            if row["gap"] >= GAP_LINE - EPS and row["spread"] <= SPREAD_LINE + EPS: T[cell]["fire1"].append(cost)
            kn = known_at_close(cd, m1, up)
            if kn is not None: T[cell]["known1"].append(kn)
        # ---- second look: one map each
        if not has2: continue
        look2 = look_minute(cd, c2, list(mt.values()))
        if state_mode == "result":
            w1, w2 = up, result_winner(m2)
            if w2 is None: C["look_2_map_2_has_no_single_winner"] += 1; continue
        else:
            if look2 is None: C["look_2_not_filled_or_not_reached"] += 1; continue
            w1 = up if up is not None else observed_winner(cd, m1, look2); w2 = observed_winner(cd, m2, look2)
            if w1 is None or w2 is None: C["look_2_state_not_observable"] += 1; continue
            rw2 = result_winner(m2)
            if rw2 is not None and w2 != rw2: C["count_only_observed_map_2_winner_differs_from_the_posted_result"] += 1
        if w2 == w1: C["look_2_no_break_the_match_ended_two_nil"] += 1; continue
        C["one_map_each"] += 1
        pre2 = pre if (up is not None and w1 == up) else pre_for(w1)
        if look2 is None: C["look_2_not_filled"] += 1; continue
        if pre2[0] is None: C["look_2_filled_but_no_pre_match_minute"] += 1; continue
        ts0, a0, b0, c0, down2, _ = pre2; q2 = per_map_chance((a0[0] + a0[1]) / 2)
        qu, qd = two(cd, mt[w1], look2), two(cd, mt[down2], look2)
        row = cheaper(q2 - qu[1], qu[1] - qu[0], qu[1], (1 - q2) - qd[1], qd[1] - qd[0], qd[1])
        T[cell]["L2"].append(row); T[cell]["spr2"] += [qu[1] - qu[0], qd[1] - qd[0]]; T[cell]["min2"].append((look2 - c2) / 60.0)
        cost = row["spread"] / 2 + fee_up(round(row["ask"] + SLIP, 4)); T[cell]["cost2"].append(cost)
        if row["gap"] >= GAP_LINE - EPS and row["spread"] <= SPREAD_LINE + EPS: T[cell]["fire2"].append(cost)
        kn = known_at_close(cd, m2, w2)
        if kn is not None: T[cell]["known2"].append(kn)
    out = {"build": "Forensics second build of MAPBREAK step 1", "state_mode": state_mode, "match_results_read": 0, "freshness": "candle freshness measured on Bitcoin 15 minute only, not on esports",
           "label": "selected on development: these lines can close a title, they cannot support a result", "titles": {}, "ambiguities": AMBIGUITIES}
    for cell, D in T.items():
        pl = stats(D["placebo"]); res = {"counts": dict(sorted(D["counts"].items())), "placebo_at_the_pre_match_minute": pl}
        for k, name in (("1", "look_1_after_map_1"), ("2", "look_2_before_map_3")):
            s = stats(D["L" + k]); n = len(D["L" + k]); cost = quant(D["cost" + k], .5); share = s["share_gap_8c_spread_4c"] if s else 0.0; pshare = pl["share_gap_8c_spread_4c"] if pl else 0.0
            if n < MIN_FILLED: v = "no evidence at n = %d filled at the look" % n
            elif cost is not None and cost > COST_KILL + EPS: v = "CLOSED on cost: median one-way entry cost %.1fc above 4c" % (100 * cost)
            elif not (share >= SHARE_LINE - EPS and share >= 2 * pshare - EPS): v = "CLOSED: efficient, move on (90th percentile gap %s)" % s["gap_p90"]
            else: v = "IN at this look"
            res[name] = {"filled_at_the_look": n, "median_minutes_from_the_map_close": quant(D["min" + k], .5), "median_spread_of_the_match_contracts": quant(D["spr" + k], .5),
                         "median_one_way_entry_cost": cost, "one_way_cost_at_firing_looks": quant(D["fire" + k], .5), "firing_looks": len(D["fire" + k]), "gap_on_the_cheaper_side": s,
                         "winner_bid_090_at_the_map_close": None if not D["known" + k] else {"looks": len(D["known" + k]), "share": round(sum(D["known" + k]) / len(D["known" + k]), 4)}, "verdict": v}
        out["titles"][cell] = res
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] != "measure" or a[1] not in ("result", "observed"): print(__doc__); print("\n".join(AMBIGUITIES)); sys.exit(2)
    relax = "--first-look-without-map-2" in a; a = [x for x in a if x != "--first-look-without-map-2"]
    i, j = a.index("--lists"), a.index("--candles")
    print(json.dumps(measure(a[i + 1:j], a[j + 1:], a[1], bo3_needs_map2=not relax), indent=1))
