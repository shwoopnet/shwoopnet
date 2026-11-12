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
assert len(ids) == 20 and sum(i.startswith("fee_") for i in ids) == 4 and sum(i.startswith("hist_") for i in ids) == 4 and sum(r.get("max_pages", 1) for r in jl["requests"]) == 96 + 4 + 40 and jl["registration"] == "kalshi-scalper/workers/mapbreak/MAPBREAK_REGISTRATION.md" and "TIE3" not in json.dumps(jl) and sum(1 for r in jl["requests"] if r.get("max_pages") == 12) == 4 and all(r["params"]["max_close_ts"] == 1792713599 and r["params"]["min_close_ts"] == 1789171200 for r in jl["requests"] if "params" in r and r["id"].startswith("live_"))
import breakplay as bp
V_, W_, q_, r_ = bp.model_bo3(0.5); assert abs(q_ - 0.5) < 1e-9 and abs(V_ - 0.75) < 1e-9
q8 = bp.model_bo3(0.8)[2]; assert abs(q8 ** 2 * (3 - 2 * q8) - 0.8) < 1e-9
assert abs(bp.model_bo5_after_map1(0.5)[0] - 0.6875) < 1e-9

def tz_start(day, hh, mm):                                   # US Eastern: Oct 2026 is still daylight time (UTC-4)
    return calendar.timegm((2026, 10, day, hh + 4, mm, 0))
def mk(t, close, result="yes", **kw): return dict({"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "close_time": F(close), "open_time": F(close - 90000), "result": result, "volume_fp": "5", "title": "x"}, **kw)
random.seed(5)
lists = {"live_" + s: {"markets": []} for s in m.series_all(spec)}
sampled = []
def add_match(title, i, day, hh, garbage_seed, bo3=True, map2_delay=40, start_ok=True, end_gap=50):
    ser = [t for t in spec["titles"] if t["cell"] == title][0]; key = "26OCT%02d%02d00AAABBB%d" % (day, hh, i); S = tz_start(day, hh, 0)
    c1 = S + (3600 if start_ok else 15000); c2 = c1 + map2_delay * 60; cm = c2 + end_gap * 60
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
add_match("DOTA2", 900, 5, 10, 1, bo3=False); add_match("DOTA2", 901, 5, 11, 1, start_ok=False); add_match("DOTA2", 902, 5, 12, 1, map2_delay=5); add_match("DOTA2", 910, 6, 12, 2, end_gap=12); add_match("DOTA2", 911, 6, 13, 3, end_gap=5)
for i in range(20): add_match("CS2", i, 3, 9 + i % 5, 100 + i)                                        # only 20 CS2 matches: under 150 filled
ms, counts = m.matches(spec, [])  if False else (None, None)
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    mt, counts = m.matches(spec, [dl])
    assert counts["lists_truncated_at_the_page_cap"] == []
    assert counts["not_best_of_three"] == 1 and counts["start_not_derivable"] == 1 and counts["map2_too_soon"] == 1 and counts["sampled"] == NM + 20 + 5 - 1 and len(mt) == NM + 22, counts
    assert counts["second_look_matches"] == NM + 20 and counts["second_look_dropped_10_to_15_min"] == 1 and counts["ended_two_nil_no_second_look"] == 1, counts
    assert all(set(x) - {"state_close2"} == {"cell", "key", "S", "state_close", "up", "down", "match", "placebo"} for x in mt)           # no result field of any market in a match record
    g = [x for x in mt if x["key"] == sampled[0]["key"]][0]; assert g["up"] == "AAA" and g["S"] == sampled[0]["S"] and g["state_close"] == sampled[0]["c1"]
    lists["live_KXDOTA2MAP"]["cursor"] = "abc123"; dlt = os.path.join(dc, "lt"); os.mkdir(dlt); mkrun(dlt, jl, lists); assert m.matches(spec, [dlt])[1]["lists_truncated_at_the_page_cap"] == ["live_KXDOTA2MAP"]; del lists["live_KXDOTA2MAP"]["cursor"]
    jc, _ = m.build_candles(spec, [dl]); kp.check_job(jc); assert 1 <= len(jc["requests"]) <= 250 and all(r["params"]["end_ts"] < m.HELD_OUT_FROM + 86400 * 400 for r in jc["requests"])
    assert all(len(r["params"]["market_tickers"].split(",")) <= 100 for r in jc["requests"]) and len(jc["ticker_allowlist"]) == 4 * len(mt)
    assert max(r["params"]["end_ts"] for r in jc["requests"]) >= max(x.get("state_close2", 0) for x in mt) + 300      # the window of a third-map match runs to map-2 close + 5 minutes
    def candles(look_edge, half, thin_pre=False, thin_look=0, q=0.55):
        cm = {}
        for x in mt:
            p = q * q * (3 - 2 * q); V = 1 - (1 - q) ** 2
            def series(t, mid, window):
                return [{"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % max(0.02, mid - half)}, "yes_ask": {"close_dollars": "%.4f" % min(0.98, mid + half)}, "volume_fp": "1"} for ts in window]
            pre = range(x["S"] - 2400, x["S"] - 599, 60); look = range(x["state_close"] + 120 + 60 * thin_look, x["state_close"] + 301, 60)
            up_pre = p; dn_pre = 1 - p
            cm[x["match"][x["up"]]] = series("", up_pre, pre) + series("", V - look_edge, [ts for ts in look])
            cm[x["match"][x["down"]]] = series("", dn_pre, pre) + series("", (1 - V) + 0.01, [ts for ts in look])
            if x.get("state_close2"):
                look2 = range(x["state_close2"] + 120 + 60 * thin_look, x["state_close2"] + 301, 60)
                cm[x["match"][x["up"]]] += series("", q - look_edge, list(look2)); cm[x["match"][x["down"]]] += series("", (1 - q) + 0.01, list(look2))
            cm[x["placebo"][x["up"]]] = series("", q, pre); cm[x["placebo"][x["down"]]] = series("", 1 - q, pre)
        return {r["id"]: {"markets": [{"market_ticker": t, "candlesticks": cm[t]} for t in r["params"]["market_tickers"].split(",") if t in cm]} for r in jc["requests"]}
    def run(name, **kw):
        d = os.path.join(dc, name); os.mkdir(d); mkrun(d, jc, candles(**kw)); return m.measure(spec, [dl], [d])
    surv = run("s", look_edge=0.12, half=0.005)
    D = surv["titles"]["DOTA2"]
    assert surv["tries_added"] == 0 and surv["rule_scored"] is False and surv["match_result_read"] is False and "Bitcoin 15 minute only, not on esports" in surv["freshness"]
    assert D["filled_at_the_look"] == NM + 2 and D["filled_pre_match"] == NM + 2 and D["median_minutes_state_close_to_look"] == 2.0
    assert D["look"]["share_gap_ge_8c_spread_le_4c"] == 1.0 and D["look"]["share_when_team_up"] == 1.0 and D["placebo"]["share_gap_ge_8c_spread_le_4c"] == 0.0 and D["verdict"].startswith("SURVIVES"), D
    assert surv["titles"]["CS2"]["verdict"].startswith("no evidence at n = 20") and abs(D["median_spread_at_look"] - 0.01) < 1e-9
    assert D["dropped_pre_match_with_match_contract_ok_but_placebo_contracts_not_in_the_same_minute"] == 0
    # map-1 contracts never two-sided while the match contract is: every match is dropped at the pre-match step and COUNTED (Desk B's added count)
    def nomap1(**kw):
        body = candles(**kw)
        for b in body.values():
            for mk_ in b["markets"]:
                if "MAP-" in mk_["market_ticker"] or "MAP" in mk_["market_ticker"].split("-")[0]: mk_["candlesticks"] = []
        return body
    dn = os.path.join(dc, "nm"); os.mkdir(dn); mkrun(dn, jc, nomap1(look_edge=0.12, half=0.005)); nm = m.measure(spec, [dl], [dn])["titles"]["DOTA2"]
    assert nm["filled_pre_match"] == 0 and nm["dropped_pre_match_with_match_contract_ok_but_placebo_contracts_not_in_the_same_minute"] == NM + 2, nm
    # efficient: ask at the value (gap 0 on the cheaper side but the other team 1c under)
    eff = run("e", look_edge=0.0, half=0.005); assert eff["titles"]["DOTA2"]["verdict"].startswith("CLOSED: efficient"), eff["titles"]["DOTA2"]["verdict"]
    # cost: spread 12c
    cost = run("c", look_edge=0.12, half=0.06); assert cost["titles"]["DOTA2"]["verdict"].startswith("CLOSED on cost"), cost["titles"]["DOTA2"]["verdict"]
    # step forward: the first two minutes after close + 120 are thin -> the look moves later; 5 minutes max
    late = run("l", look_edge=0.12, half=0.005, thin_look=2); assert late["titles"]["DOTA2"]["median_minutes_state_close_to_look"] == 4.0
    nolook = run("n", look_edge=0.12, half=0.005, thin_look=4); assert nolook["titles"]["DOTA2"]["filled_at_the_look"] == 0
    # the match results are never read: change every garbage result and the output is identical
    for s_ in lists:
        for mk_ in lists[s_]["markets"]:
            if "MAP-1-" not in mk_["ticker"] and "-1-" not in mk_["ticker"]: mk_["result"] = "no" if mk_["result"] == "yes" else "yes"
    dl2 = os.path.join(dc, "lists2"); os.mkdir(dl2); mkrun(dl2, jl, lists)
    d2 = os.path.join(dc, "s2"); os.mkdir(d2); mkrun(d2, jc, candles(look_edge=0.12, half=0.005)); again = m.measure(spec, [dl2], [d2])
    assert json.dumps(again["titles"]["DOTA2"], sort_keys=True) == json.dumps(surv["titles"]["DOTA2"], sort_keys=True)
    # the REGISTERED RULE (Amendments 1 to 3)
    def set_results(up_wins):
        for s_ in lists:
            for mk_ in lists[s_]["markets"]:
                parts = mk_["ticker"].split("-")
                if parts[0] in [t["match_series"] for t in spec["titles"]]:
                    key = parts[1]; x = [r for r in mt if r["key"] == key]
                    if x: mk_["result"] = "yes" if ((parts[2] == x[0]["up"]) == up_wins) else "no"
    def sc(folder_l, folder_c): return m.score(spec, [folder_l], [folder_c])
    dsr = os.path.join(dc, "sr"); os.mkdir(dsr); mkrun(dsr, jc, candles(look_edge=0.12, half=0.005))
    # step 1 shows both looks per title with their own kill lines; CS2 is out at both (20 matches)
    st1 = m.measure(spec, [dl], [dsr])["titles"]; assert st1["DOTA2|second_look"]["filled_at_the_look"]
    assert st1["DOTA2|second_look"]["verdict"].startswith("SURVIVES") and st1["CS2|second_look"]["verdict"].startswith("no evidence")
    set_results(True); dlw = os.path.join(dc, "lw"); os.mkdir(dlw); mkrun(dlw, jl, lists)
    rw = sc(dlw, dsr)
    assert rw["in"] == ["DOTA2", "DOTA2|second_look"], rw["in"]
    assert rw["bets"] == rw["result_fn_calls"] and rw["bets"] == NM + 2 + NM, (rw["bets"], rw["counts"])           # first look on all 172 DOTA2 matches, second look on the 170 third-map ones
    assert rw["all"]["wins"] == rw["bets"] and rw["all"]["cash_pf"] in ("inf", None) or rw["all"]["cash_pf"] > 5
    assert set(rw["by_look"]) == {"1", "2"} and set(rw["by_title"]) == {"DOTA2"} and len(rw["halves_by_date"]) == 2
    assert rw["z_match_cluster"]["clusters"] == NM + 2 and rw["z_day_cluster"]["clusters"] < rw["z_match_cluster"]["clusters"]
    # price = ask + 1c; the fee rounds UP to the cent
    p1 = (1 - (1 - 0.55) ** 2) - 0.12 + 0.005 + 0.01; p2 = 0.55 - 0.12 + 0.005 + 0.01; assert abs(rw["all"]["mean_price_paid"] - ((NM + 2) * p1 + NM * p2) / (2 * NM + 2)) < 2e-3, rw["all"]["mean_price_paid"]
    assert bp.fee_up(0.50) == 0.02 and bp.fee_up(0.10) == 0.01 and bp.fee_up(0.90) == 0.01
    assert bp.verdict_amended(99, 3.0, [3.0, 3.0]) == "NOT_ENOUGH_DATA at n = 99" and bp.verdict_amended(100, 0.99, [2, 2]) == "FALSIFIED" and bp.verdict_amended(100, 1.6, [2, 0.9]) == "FALSIFIED"
    assert bp.verdict_amended(100, 1.6, [2, 1.2]) == "development bar met" and bp.verdict_amended(100, 1.3, [2, 1.2]) == "bar not met"
    assert rw["verdict"] == "development bar met", rw["verdict"]
    set_results(False); dll = os.path.join(dc, "ll"); os.mkdir(dll); mkrun(dll, jl, lists)
    rl = sc(dll, dsr); assert rl["all"]["cash_pf"] == 0.0 and rl["verdict"] == "FALSIFIED", rl["verdict"]
    # every title/look out (efficient book): CLOSED and NO match result is read (the callback is never called)
    deff = os.path.join(dc, "eff2"); os.mkdir(deff); mkrun(deff, jc, candles(look_edge=0.0, half=0.005))
    calls = []; ms_, _c = m.matches(spec, [dl]); out = bp.score_rule2(ms_, [deff], m.CFG, lambda rec: calls.append(1) or True)
    assert out["verdict"].startswith("CLOSED") and calls == [] and out["bets"] == 0 and out["result_fn_calls"] == 0
    # held-out refusal: a record closing at or after the constant is dropped unless the Head's go
    held = [dict(ms_[0], state_close=m.HELD_OUT_FROM + 100)]
    o2 = bp.score_rule2(held, [dsr], m.CFG, lambda rec: True); assert o2["held_out_refused"] == 1 and o2["verdict"].startswith("CLOSED")
    # the lists job: 20 requests with the 4 history lists, only series_ticker/limit/cursor
    jlst = m.build_lists(spec); kp.check_job(jlst); assert len(jlst["requests"]) == 20 and sum(1 for r in jlst["requests"] if r["path"] == "/historical/markets") == 4
    assert all(set(r["params"]) <= {"series_ticker", "limit"} for r in jlst["requests"] if r["path"] == "/historical/markets")
    # history count: matches before 2026-09-12 by match series; two markets a match
    hl = {"hist_" + t["match_series"]: {"markets": [mk("%s-26AUG%02d1000AAABBB%d-%s" % (t["match_series"], 1 + i % 28, i, tm), calendar.timegm((2026, 8, 1 + i % 28, 12, 0, 0))) for i in range(5) for tm in ("AAA", "BBB")]} for t in spec["titles"]}
    dh = os.path.join(dc, "hh"); os.mkdir(dh); mkrun(dh, jlst, hl); hc = m.history_count(spec, [dh]); assert hc["total"] == 20 and hc["candle_requests_if_one_market_a_request"] == 80, hc
print("mapbreak synthetic tests passed")
