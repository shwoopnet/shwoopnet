"""Synthetic test for mapbreak.py against Desk B's frozen titles file (made-up markets; no Kalshi). Run: python3 -W ignore test_mapbreak.py"""
import calendar, gzip, json, os, random, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import mapbreak as m
import kalshi_pull as kp
from datetime import datetime, timezone

F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]])); rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

spec = m.load_cells()
try: m.load_cells(sha="0" * 64); raise SystemExit("wrong hash passed")
except SystemExit as e: assert "does not match" in str(e)
jl = m.build_lists(spec); kp.check_job(jl); ids = [r["id"] for r in jl["requests"]]
assert len(ids) == 16 and sum(i.startswith("fee_") for i in ids) == 4 and all(r["params"]["max_close_ts"] == 1792713599 and r["params"]["min_close_ts"] == 1789171200 for r in jl["requests"] if "params" in r)
assert abs(m.solve_q(0.5) - 0.5) < 1e-9 and abs(m.solve_q(0.8) ** 2 * (3 - 2 * m.solve_q(0.8)) - 0.8) < 1e-9

def tz_start(day, hh, mm):                                   # US Eastern: Oct 2026 is still daylight time (UTC-4)
    return calendar.timegm((2026, 10, day, hh + 4, mm, 0))
def mk(t, close, result="yes", **kw): return dict({"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "close_time": F(close), "open_time": F(close - 90000), "result": result, "volume_fp": "5", "title": "x"}, **kw)
random.seed(5)
lists = {"live_" + s: {"markets": []} for s in m.series_all(spec)}
sampled = []
def add_match(title, i, day, hh, garbage_seed, bo3=True, map2_delay=40, start_ok=True):
    ser = [t for t in spec["titles"] if t["cell"] == title][0]; key = "26OCT%02d%02d00AAABBB%d" % (day, hh, i); S = tz_start(day, hh, 0)
    c1 = S + (3600 if start_ok else 15000); c2 = c1 + map2_delay * 60; cm = c1 + 90 * 60
    rnd = random.Random(garbage_seed); up = "AAA" if i % 2 == 0 else "BBB"; dn = "BBB" if up == "AAA" else "AAA"
    for team in ("AAA", "BBB"):
        lists["live_" + ser["match_series"]]["markets"].append(mk("%s-%s-%s" % (ser["match_series"], key, team), cm, rnd.choice(["yes", "no"])))        # GARBAGE results: must never be read
        lists["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-1-%s" % (ser["map_series"], key, team), c1, "yes" if team == up else "no"))     # the state
        lists["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-2-%s" % (ser["map_series"], key, team), c2, rnd.choice(["yes", "no"])))
    lists["live_" + ser["total_maps_series"]]["markets"].append(mk("%s-%s-2" % (ser["total_maps_series"], key), cm, floor_strike=2.5))
    if not bo3: lists["live_" + ser["total_maps_series"]]["markets"].append(mk("%s-%s-3" % (ser["total_maps_series"], key), cm, floor_strike=3.5))
    return dict(title=title, key=key, S=S, c1=c1, up=up, dn=dn, ser=ser)
NM = 170
for i in range(NM): sampled.append(add_match("DOTA2", i, 1 + i % 20, 10 + i % 8, i))
add_match("DOTA2", 900, 5, 10, 1, bo3=False); add_match("DOTA2", 901, 5, 11, 1, start_ok=False); add_match("DOTA2", 902, 5, 12, 1, map2_delay=5)
for i in range(20): add_match("CS2", i, 3, 9 + i % 5, 100 + i)                                        # only 20 CS2 matches: under 150 filled
ms, counts = m.matches(spec, [])  if False else (None, None)
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    mt, counts = m.matches(spec, [dl])
    assert counts["not_best_of_three"] == 1 and counts["start_not_derivable"] == 1 and counts["map2_too_soon"] == 1 and counts["sampled"] == NM + 20 + 3 - 1 and len(mt) == NM + 20, counts
    assert all(set(x) == {"cell", "key", "S", "map1_close", "up", "down", "match", "map1"} for x in mt)           # no result field of any market in a match record
    g = [x for x in mt if x["key"] == sampled[0]["key"]][0]; assert g["up"] == "AAA" and g["S"] == sampled[0]["S"] and g["map1_close"] == sampled[0]["c1"]
    jc, _ = m.build_candles(spec, [dl]); kp.check_job(jc); assert 1 <= len(jc["requests"]) <= 250 and all(r["params"]["end_ts"] < m.HELD_OUT_FROM + 86400 * 400 for r in jc["requests"])
    assert all(len(r["params"]["market_tickers"].split(",")) <= 100 for r in jc["requests"]) and len(jc["ticker_allowlist"]) == 4 * len(mt)
    def candles(look_edge, half, thin_pre=False, thin_look=0, q=0.55):
        cm = {}
        for x in mt:
            p = q * q * (3 - 2 * q); V = 1 - (1 - q) ** 2
            def series(t, mid, window):
                return [{"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % max(0.02, mid - half)}, "yes_ask": {"close_dollars": "%.4f" % min(0.98, mid + half)}, "volume_fp": "1"} for ts in window]
            pre = range(x["S"] - 2400, x["S"] - 599, 60); look = range(x["map1_close"] + 120 + 60 * thin_look, x["map1_close"] + 301, 60)
            up_pre = p; dn_pre = 1 - p
            cm[x["match"][x["up"]]] = series("", up_pre, pre) + series("", V - look_edge, [ts for ts in look])
            cm[x["match"][x["down"]]] = series("", dn_pre, pre) + series("", (1 - V) + 0.01, [ts for ts in look])
            cm[x["map1"][x["up"]]] = series("", q, pre); cm[x["map1"][x["down"]]] = series("", 1 - q, pre)
        return {r["id"]: {"markets": [{"market_ticker": t, "candlesticks": cm[t]} for t in r["params"]["market_tickers"].split(",") if t in cm]} for r in jc["requests"]}
    def run(name, **kw):
        d = os.path.join(dc, name); os.mkdir(d); mkrun(d, jc, candles(**kw)); return m.measure(spec, [dl], [d])
    surv = run("s", look_edge=0.12, half=0.005)
    D = surv["titles"]["DOTA2"]
    assert surv["tries_added"] == 0 and surv["rule_scored"] is False and surv["match_result_read"] is False and "Bitcoin 15 minute only, not on esports" in surv["freshness"]
    assert D["filled_at_the_look"] == NM and D["filled_pre_match"] == NM and D["median_minutes_map1_close_to_look"] == 2.0
    assert D["look"]["share_gap_ge_8c_spread_le_4c"] == 1.0 and D["look"]["share_when_team_up"] == 1.0 and D["placebo"]["share_gap_ge_8c_spread_le_4c"] == 0.0 and D["verdict"].startswith("SURVIVES"), D
    assert surv["titles"]["CS2"]["verdict"].startswith("no evidence at n = 20") and abs(D["median_spread_at_look"] - 0.01) < 1e-9
    # efficient: ask at the value (gap 0 on the cheaper side but the other team 1c under)
    eff = run("e", look_edge=0.0, half=0.005); assert eff["titles"]["DOTA2"]["verdict"].startswith("CLOSED: efficient"), eff["titles"]["DOTA2"]["verdict"]
    # cost: spread 12c
    cost = run("c", look_edge=0.12, half=0.06); assert cost["titles"]["DOTA2"]["verdict"].startswith("CLOSED on cost"), cost["titles"]["DOTA2"]["verdict"]
    # step forward: the first two minutes after close + 120 are thin -> the look moves later; 5 minutes max
    late = run("l", look_edge=0.12, half=0.005, thin_look=2); assert late["titles"]["DOTA2"]["median_minutes_map1_close_to_look"] == 4.0
    nolook = run("n", look_edge=0.12, half=0.005, thin_look=4); assert nolook["titles"]["DOTA2"]["filled_at_the_look"] == 0
    # the match results are never read: change every garbage result and the output is identical
    for s_ in lists:
        for mk_ in lists[s_]["markets"]:
            if "MAP-1-" not in mk_["ticker"] and "-1-" not in mk_["ticker"]: mk_["result"] = "no" if mk_["result"] == "yes" else "yes"
    dl2 = os.path.join(dc, "lists2"); os.mkdir(dl2); mkrun(dl2, jl, lists)
    d2 = os.path.join(dc, "s2"); os.mkdir(d2); mkrun(d2, jc, candles(look_edge=0.12, half=0.005)); again = m.measure(spec, [dl2], [d2])
    assert json.dumps(again["titles"]["DOTA2"], sort_keys=True) == json.dumps(surv["titles"]["DOTA2"], sort_keys=True)
print("mapbreak synthetic tests passed")
