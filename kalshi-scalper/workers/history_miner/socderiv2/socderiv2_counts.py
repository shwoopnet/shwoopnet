"""SOCDERIV second build, stage 1 counts on a LISTS run only (no candle, no price, no result field). Imports the reading layer of socderiv2.py (41d07198) and repeats its
sampling and kickoff rules word for word: R1 lists proof, R2 a game = one GAME event with its three winner markets, R3 the 60 latest closes per league in the window,
R16 the BTTS leg found by its event ticker (one market an event), R4 the kickoff guard on all three winner markets, R8 a team-total market is readable only with a numeric floor_strike and a last segment starting with exactly one team code.
Usage: python3 -I socderiv2_counts.py <series.json> <lists run folder>"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import socderiv2 as D

ser_raw = open(sys.argv[1], "rb").read()
if hashlib.sha256(ser_raw).hexdigest() != D.SERIES_SHA:
    raise SystemExit("series file hash")
ser = json.loads(ser_raw)
lo, hi = D.iso(ser["window"]["closes_from"]), D.iso(ser["window"]["closes_before"])
group_of = {lg: g for g, lgs in ser["groups"].items() for lg in lgs}
lists = D.load_run(sys.argv[2], lambda i: i.startswith("live_"))
markets, no_such = {}, []
for rid, (q, pages) in lists.items():
    s = rid[len("live_"):]
    got = [mk for pg in pages for mk in pg.get("markets", [])]
    if not got:
        no_such.append(s)
    for mk in got:
        if mk["ticker"].split("-")[0] != s:
            raise SystemExit("market %s in the list of %s" % (mk["ticker"], s))
        markets[mk["ticker"]] = {k: v for k, v in mk.items() if k != "result"}
out = {"freshness": D.FRESH, "no_such_series": sorted(no_such), "leagues": {}, "totals": {}}
tot = {"games_in_window": 0, "sampled": 0, "kickoff_not_derivable": 0, "kickoff_derivable": 0, "no_btts_leg": 0,
       "teamtotal_markets": 0, "teamtotal_unreadable": 0, "winner_legs_incomplete": 0, "btts_unreadable": 0}
for lg in sorted(group_of):
    gs = "KX%sGAME" % lg
    events = {}
    for t, mk in markets.items():
        if t.split("-")[0] == gs:
            events.setdefault(mk["event_ticker"], []).append(mk)
    games, incomplete = [], 0
    for ev, mks in events.items():
        codes = sorted(m["ticker"].split("-")[-1] for m in mks if not m["ticker"].endswith("-TIE"))
        ties = [m for m in mks if m["ticker"].endswith("-TIE")]
        if len(codes) != 2 or len(ties) != 1 or len(mks) != 3:
            incomplete += 1
            continue
        cl = max(D.iso(m["close_time"]) for m in mks)
        if lo <= cl < hi:
            games.append((cl, ev, mks, codes))
    games.sort(key=lambda g: (-g[0], g[1]))
    sample = games[:D.SAMPLE_N]
    r = {"group": group_of[lg], "series_with_no_market": [s for s in ("GAME", "TOTAL", "BTTS", "TEAMTOTAL") if "KX%s%s" % (lg, s) in no_such],
         "winner_legs_incomplete": incomplete, "games_in_window": len(games), "sampled": len(sample),
         "kickoff_not_derivable": 0, "kickoff_derivable": 0, "no_btts_leg": 0, "btts_unreadable": 0, "teamtotal_markets": 0, "teamtotal_unreadable": 0}
    for cl, ev, mks, codes in sample:
        occ = {m.get("occurrence_datetime") for m in mks}
        if len(occ) != 1 or None in occ:
            r["kickoff_not_derivable"] += 1; continue
        ko = D.iso(occ.pop()) - 180 * 60
        if not all(100 * 60 - D.EPS <= D.iso(m["close_time"]) - ko <= 135 * 60 + D.EPS for m in mks):
            r["kickoff_not_derivable"] += 1; continue
        r["kickoff_derivable"] += 1
        key = ev.split("-", 1)[1]
        nb = sum(1 for m in markets.values() if m.get("event_ticker") == "KX%sBTTS-%s" % (lg, key))
        if nb == 0:
            r["no_btts_leg"] += 1
        elif nb > 1:
            r["btts_unreadable"] = r.get("btts_unreadable", 0) + 1
        for t, m in markets.items():
            if t.startswith("KX%sTEAMTOTAL-%s-" % (lg, key)):
                r["teamtotal_markets"] += 1
                last = t.split("-")[-1]
                if sum(1 for c in codes if last.startswith(c)) != 1 or not isinstance(m.get("floor_strike"), (int, float)):
                    r["teamtotal_unreadable"] += 1
    out["leagues"][lg] = r
    for k in tot:
        tot[k] += r[k]
out["totals"] = tot
out["leagues_with_any_series_missing"] = sorted(lg for lg, r in out["leagues"].items() if r["series_with_no_market"])
out["leagues_with_no_game_series"] = sorted(lg for lg, r in out["leagues"].items() if "GAME" in r["series_with_no_market"])
out["notes"] = ["no_btts_leg and team totals are counted over sampled games whose kickoff is derivable (the targets of a game that is dropped are not looked at)",
                "a league with all four series empty is 'no such series' for each; series_with_no_market lists them per league"]
print(json.dumps(out, indent=1, sort_keys=True))
