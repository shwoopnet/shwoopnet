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
def add_match(title, i, day, hh, garbage_seed, bo3=True, map2_delay=40, start_ok=True, end_gap=50, two_nil=False, map2=True):
    ser = [t for t in spec["titles"] if t["cell"] == title][0]; key = "26OCT%02d%02d00AAABBB%d" % (day, hh, i); S = tz_start(day, hh, 0)
    c1 = S + (3600 if start_ok else 15000); c2 = c1 + map2_delay * 60; cm = c2 + end_gap * 60
    rnd = random.Random(garbage_seed); up = "AAA" if i % 2 == 0 else "BBB"; dn = "BBB" if up == "AAA" else "AAA"
    for team in ("AAA", "BBB"):
        lists["live_" + ser["match_series"]]["markets"].append(mk("%s-%s-%s" % (ser["match_series"], key, team), cm, rnd.choice(["yes", "no"])))        # GARBAGE results: must never be read
        lists["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-1-%s" % (ser["map_series"], key, team), c1, "yes" if team == up else "no"))     # the state
        if map2: lists["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-2-%s" % (ser["map_series"], key, team), c2, "yes" if (team == (up if two_nil else dn)) else "no"))     # the map-2 result IS the state of the second look
    lists["live_" + ser["total_maps_series"]]["markets"].append(mk("%s-%s-2" % (ser["total_maps_series"], key), cm, floor_strike=2.5))
    if not bo3: lists["live_" + ser["total_maps_series"]]["markets"].append(mk("%s-%s-3" % (ser["total_maps_series"], key), cm, floor_strike=3.5))
    return dict(title=title, key=key, S=S, c1=c1, up=up, dn=dn, ser=ser)
NM = 170
for i in range(NM): sampled.append(add_match("DOTA2", i, 1 + i % 20, 10 + i % 8, i))
add_match("DOTA2", 900, 5, 10, 1, bo3=False); add_match("DOTA2", 901, 5, 11, 1, start_ok=False); add_match("DOTA2", 902, 5, 12, 1, map2_delay=5); add_match("DOTA2", 903, 5, 13, 1, two_nil=True); add_match("DOTA2", 904, 5, 14, 1, map2=False); add_match("DOTA2", 910, 6, 12, 2, end_gap=12); add_match("DOTA2", 911, 6, 13, 3, end_gap=5)
for i in range(20): add_match("CS2", i, 3, 9 + i % 5, 100 + i)                                        # only 20 CS2 matches: under 150 filled
ms, counts = m.matches(spec, [])  if False else (None, None)
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    mt, counts = m.matches(spec, [dl])
    assert counts["lists_truncated_at_the_page_cap"] == []
    assert counts["not_best_of_three"] == 2 and counts["start_not_derivable"] == 1 and counts["map2_closed_under_15_min_after_map1_count_only"] == 1 and counts["sampled"] == NM + 20 + 5, counts
    assert len(mt) == NM + 24, counts
    assert counts["second_look_matches"] == NM + 23 and counts["map2_won_by_map1_winner_no_second_look"] == 1, counts
    assert all(set(x) - {"state_close2", "map2"} == {"cell", "key", "S", "state_close", "posted_up", "match", "placebo"} for x in mt)           # no result field of any market in a match record
    g = [x for x in mt if x["key"] == sampled[0]["key"]][0]; assert g["posted_up"] == "AAA" and g["S"] == sampled[0]["S"] and g["state_close"] == sampled[0]["c1"]
    lists["live_KXDOTA2MAP"]["cursor"] = "abc123"; dlt = os.path.join(dc, "lt"); os.mkdir(dlt); mkrun(dlt, jl, lists); assert m.matches(spec, [dlt])[1]["lists_truncated_at_the_page_cap"] == ["live_KXDOTA2MAP"]; del lists["live_KXDOTA2MAP"]["cursor"]
    jc, _ = m.build_candles(spec, [dl]); kp.check_job(jc); assert 1 <= len(jc["requests"]) <= 250 and all(r["params"]["end_ts"] < m.HELD_OUT_FROM + 86400 * 400 for r in jc["requests"])
    assert all(len(r["params"]["market_tickers"].split(",")) <= 100 for r in jc["requests"]) and len(jc["ticker_allowlist"]) == 4 * len(mt) + 2 * sum(1 for x in mt if x.get("state_close2"))
    assert max(r["params"]["end_ts"] for r in jc["requests"]) >= max(x.get("state_close2", 0) for x in mt) + 300      # the window of a third-map match runs to map-2 close + 5 minutes
    def state_candle(ts, mid): return {"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % (mid - 0.01)}, "yes_ask": {"close_dollars": "%.4f" % (mid + 0.01)}, "volume_fp": "1"}
    def candles(look_edge, half, thin_pre=False, thin_look=0, q=0.55, bump=0.0):
        cm = {}
        for x in mt:
            x = dict(x, up=x["posted_up"], down=[tm for tm in x["match"] if tm != x["posted_up"]][0])
            p = q * q * (3 - 2 * q); V = 1 - (1 - q) ** 2
            def series(t, mid, window, bump=0.0):
                window = list(window)
                return [{"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % max(0.02, mid - half + (bump if ts != window[0] else 0))}, "yes_ask": {"close_dollars": "%.4f" % min(0.98, mid + half + (bump if ts != window[0] else 0))}, "volume_fp": "1"} for ts in window]          # bump: the asks AFTER the first look minute move up
            pre = range(x["S"] - 2400, x["S"] - 599, 60); look = range(x["state_close"] + 120 + 60 * thin_look, x["state_close"] + 301, 60)
            up_pre = p; dn_pre = 1 - p
            cm[x["match"][x["up"]]] = series("", up_pre, pre) + series("", V - look_edge, [ts for ts in look], bump if int(x["key"][-1]) % 2 == 0 else 0.0)
            cm[x["match"][x["down"]]] = series("", dn_pre, pre) + series("", (1 - V) + 0.01, [ts for ts in look])
            if x.get("state_close2"):
                look2 = range(x["state_close2"] + 120 + 60 * thin_look, x["state_close2"] + 301, 60)
                cm[x["match"][x["up"]]] += series("", q - look_edge, list(look2), bump if int(x["key"][-1]) % 2 == 0 else 0.0); cm[x["match"][x["down"]]] += series("", (1 - q) + 0.01, list(look2))
            cm[x["placebo"][x["up"]]] = series("", q, pre) + [state_candle(x["state_close"] - 60, 0.95)]; cm[x["placebo"][x["down"]]] = series("", 1 - q, pre) + [state_candle(x["state_close"] - 60, 0.04)]      # the map-1 contracts show the state (Amendment 7)
            if x.get("state_close2"):
                cm[x["map2"][x["down"]]] = [state_candle(x["state_close2"] - 60, 0.95)]; cm[x["map2"][x["up"]]] = [state_candle(x["state_close2"] - 60, 0.04)]          # map 2 won by the map-1 loser
        return {r["id"]: {"markets": [{"market_ticker": t, "candlesticks": cm[t]} for t in r["params"]["market_tickers"].split(",") if t in cm]} for r in jc["requests"]}
    def run(name, **kw):
        d = os.path.join(dc, name); os.mkdir(d); mkrun(d, jc, candles(**kw)); return m.measure(spec, [dl], [d])
    surv = run("s", look_edge=0.12, half=0.005)
    D = surv["titles"]["DOTA2"]
    assert surv["tries_added"] == 0 and surv["rule_scored"] is False and surv["match_result_read"] is False and "Bitcoin 15 minute only, not on esports" in surv["freshness"]
    assert D["filled_at_the_look"] == NM + 4 and D["filled_pre_match"] == NM + 4 and D["median_minutes_state_close_to_look"] == 2.0
    assert D["look"]["share_gap_ge_8c_spread_le_4c"] == 1.0 and D["look"]["share_when_team_up"] == 1.0 and D["placebo"]["share_gap_ge_8c_spread_le_4c"] == 0.0 and D["verdict"].startswith("SURVIVES"), D
    assert surv["titles"]["CS2"]["verdict"].startswith("no evidence at n = 20") and abs(D["median_spread_at_look"] - 0.01) < 1e-9
    assert D["dropped_pre_match_with_match_contract_ok_but_placebo_contracts_not_in_the_same_minute"] == 0
    # map-1 contracts never two-sided while the match contract is: every match is dropped at the pre-match step and COUNTED (Desk B's added count)
    def nomap1(**kw):
        body = candles(**kw)
        for b in body.values():
            for mk_ in b["markets"]:
                if "MAP" in mk_["market_ticker"].split("-")[0]: mk_["candlesticks"] = mk_["candlesticks"][-1:]          # keep only the state candle: no pre-match map-1 minutes
        return body
    dn = os.path.join(dc, "nm"); os.mkdir(dn); mkrun(dn, jc, nomap1(look_edge=0.12, half=0.005)); nm = m.measure(spec, [dl], [dn])["titles"]["DOTA2"]
    assert nm["filled_pre_match"] == 0 and nm["dropped_pre_match_with_match_contract_ok_but_placebo_contracts_not_in_the_same_minute"] == NM + 4, nm
    # efficient: ask at the value (gap 0 on the cheaper side but the other team 1c under)
    eff = run("e", look_edge=0.0, half=0.005); assert eff["titles"]["DOTA2"]["verdict"].startswith("no evidence at n = 0 filled bets"), eff["titles"]["DOTA2"]["verdict"]          # nothing fires: under 150 filled bets is "no evidence" (Amendment 9)
    # cost: spread 12c
    cost = run("c", look_edge=0.12, half=0.06); assert cost["titles"]["DOTA2"]["fired_signals_at_the_look"] == 0 and cost["titles"]["DOTA2"]["verdict"].startswith("no evidence"), cost["titles"]["DOTA2"]["verdict"]          # a 12c spread never fires (spread line 4c)
    # step forward: the first two minutes after close + 120 are thin -> the look moves later; 5 minutes max
    late = run("l", look_edge=0.12, half=0.005, thin_look=2); assert late["titles"]["DOTA2"]["median_minutes_state_close_to_look"] == 4.0
    nolook = run("n", look_edge=0.12, half=0.005, thin_look=4); assert nolook["titles"]["DOTA2"]["filled_at_the_look"] == 0
    # the match results are never read: change every garbage result and the output is identical
    for s_ in lists:
        for mk_ in lists[s_]["markets"]:
            if "-1-" not in mk_["ticker"] and "-2-" not in mk_["ticker"]: mk_["result"] = "no" if mk_["result"] == "yes" else "yes"
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
                    if x: mk_["result"] = "yes" if ((parts[2] == x[0]["posted_up"]) == up_wins) else "no"
    def sc(folder_l, folder_c): return m.score(spec, [folder_l], [folder_c])
    dsr = os.path.join(dc, "sr"); os.mkdir(dsr); mkrun(dsr, jc, candles(look_edge=0.12, half=0.005))
    # step 1 shows both looks per title with their own kill lines; CS2 is out at both (20 matches)
    st1 = m.measure(spec, [dl], [dsr])["titles"]; assert st1["DOTA2|second_look"]["filled_at_the_look"]
    assert st1["DOTA2|second_look"]["verdict"].startswith("SURVIVES") and st1["CS2|second_look"]["verdict"].startswith("no evidence")
    set_results(True); dlw = os.path.join(dc, "lw"); os.mkdir(dlw); mkrun(dlw, jl, lists)
    rw = sc(dlw, dsr)
    assert rw["in"] == ["DOTA2", "DOTA2|second_look"], (rw["in"], {k: (v["filled_at_the_look"], v["verdict"], v["look"], v["placebo"]) for k, v in rw["step1"].items()})
    assert rw["bets"] == rw["result_fn_calls"] and rw["bets"] == NM + 4 + NM + 3, (rw["bets"], rw["counts"])           # first look on all 172 DOTA2 matches, second look on the 170 third-map ones
    assert rw["all"]["wins"] == rw["bets"] and rw["all"]["cash_pf"] in ("inf", None) or rw["all"]["cash_pf"] > 5
    assert set(rw["by_look"]) == {"1", "2"} and set(rw["by_title"]) == {"DOTA2"} and len(rw["halves_by_date"]) == 2
    assert rw["z_match_cluster"]["clusters"] == NM + 4 and rw["z_day_cluster"]["clusters"] < rw["z_match_cluster"]["clusters"]
    # price = ask + 1c; the fee rounds UP to the cent
    p1 = (1 - (1 - 0.55) ** 2) - 0.12 + 0.005 + 0.01; p2 = 0.55 - 0.12 + 0.005 + 0.01; assert abs(rw["all"]["mean_price_paid"] - ((NM + 4) * p1 + (NM + 3) * p2) / (2 * NM + 7)) < 2e-3, rw["all"]["mean_price_paid"]
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
    # AMENDMENT 4: no time after the look may change which bets exist. Move every MATCH market close (and the total-maps close) to 5 minutes, 12 minutes and 5 hours after map 2: records and bets identical
    srt = lambda L: json.dumps(sorted(L, key=lambda r: r["key"]), sort_keys=True); base_recs = srt(m.matches(spec, [dl])[0]); base_bets = sc(dll, dsr)["bets"]
    for shift in (5 * 60, 12 * 60, 300 * 60):
        for s_ in lists:
            for mk_ in lists[s_]["markets"]:
                parts = mk_["ticker"].split("-")
                if parts[0] in [t["match_series"] for t in spec["titles"]] + [t["total_maps_series"] for t in spec["titles"]]:
                    x = [r for r in mt if r["key"] == parts[1]]
                    if x and x[0].get("state_close2"): mk_["close_time"] = F(x[0]["state_close2"] + shift)
        dsh = os.path.join(dc, "sh%d" % shift); os.mkdir(dsh); mkrun(dsh, jl, lists)
        assert srt(m.matches(spec, [dsh])[0]) == base_recs, shift
        assert sc(dsh, dsr)["bets"] == base_bets, shift
    # the state-known count is printed per title and look
    sk = m.measure(spec, [dl], [dsr])["titles"]; assert "state_known_at_close" in sk["DOTA2"] and "state_known_at_close" in sk["DOTA2|second_look"]
    # cost line: hold-to-settlement venues use the one-way entry cost (kill above 4c), a rule with an exit can keep the round trip (kill above 5c); the result says which
    cand = {"rt": 0.07, "half_spread": 0.02, "ask": 0.40}
    c_ow, c_rt = bp.VenueConfig("x", "bo3", cost_mode="one_way"), bp.VenueConfig("y", "bo3", cost_mode="round_trip")
    assert abs(bp.cost_of(cand, c_ow) - (0.02 + bp.fee_up(0.41))) < 1e-9 and bp.cost_of(cand, c_rt) == 0.07 and c_ow.cost_max == 0.04 and c_rt.cost_max == 0.05
    assert m.CFG.cost_mode == "one_way" and "one-way" in m.measure(spec, [dl], [dsr])["titles"]["DOTA2"]["cost_line_used"]
    # standing rule: a void (no yes/no result) is a fee-only loss, counted in n, PF and z, with the count printed
    calls_ms, _c = m.matches(spec, [dl]); void_keys = {r["key"] for r in calls_ms[:5]}
    ov = bp.score_rule2(calls_ms, [dsr], m.CFG, lambda rec: None if rec["key"] in void_keys else True)
    assert ov["counts"]["void_booked_as_fee_loss"] >= 5 and ov["bets"] == ov["counts"]["fired"] and ov["all"]["wins"] < ov["bets"], ov["counts"]
    vt = [x for x in ov["by_look"].values()]
    # both candle windows: own (S-40) and widened (S-70); the widened job never has fewer requests, same tickers
    jo, _ = m.build_candles(spec, [dl]); jw, _ = m.build_candles(spec, [dl], True)
    assert len(jw["requests"]) >= len(jo["requests"]) and jw["ticker_allowlist"] == jo["ticker_allowlist"] and min(r["params"]["start_ts"] for r in jw["requests"]) < min(r["params"]["start_ts"] for r in jo["requests"])
    # AMENDMENT 7: the observed winner (best YES bid >= 0.90, or the other team's YES ask <= 0.10; last candle at or before the look; one-sided allowed)
    cdl = lambda b, a: {"bid": b, "ask": a}
    ix7 = {"MA": {100: cdl(0.93, 0.97), 160: cdl(0.20, None)}, "MB": {100: cdl(0.05, 0.08)}, "MC": {100: cdl(None, 0.12)}, "MD": {100: cdl(0.91, None)}, "ME": {100: cdl(0.5, 0.6)}}
    ow = bp.observe_winner
    assert ow(ix7, {"A": "MA", "B": "MB"}, 100) == "A"                                   # A's bid .93, B's ask .08
    assert ow(ix7, {"A": "MB", "B": "MC"}, 100) is None                                   # Amendment 9: only a best bid of 0.90 or more counts; the other's low ask no longer does
    assert ow(ix7, {"A": "MD", "B": "ME"}, 100) == "A" and ow(ix7, {"A": "ME", "B": "ME"}, 100) is None            # a one-sided bid counts; neither: none
    assert ow(ix7, {"A": "MD", "B": "MD"}, 100) is None                                   # both teams observed: not observable
    assert ow(ix7, {"A": "MA", "B": "NOCANDLES"}, 100) is None and ow(ix7, {"A": "MA", "B": "MB"}, 99) is None          # a contract with no candle at or before the look
    assert ow(ix7, {"A": "MA", "B": "ME"}, 130) == "A" and ow(ix7, {"A": "MA", "B": "ME"}, 170) is None and ow(ix7, {"A": "MA", "B": "MB"}, 170) is None                  # the LAST candle at or before the look decides (MA at 160 has bid .20)
    # the bet's state ignores the posted result: flip posted_up on every record, nothing changes in the engine's resolved up
    ms_f, _c = m.matches(spec, [dl]); flipped = [dict(r, posted_up=[tm for tm in r["match"] if tm != r["posted_up"]][0]) for r in ms_f]
    a_ = bp.measure(ms_f, [dsr], m.CFG)["titles"]; b_ = bp.measure(flipped, [dsr], m.CFG)["titles"]
    assert a_["DOTA2"]["filled_at_the_look"] == b_["DOTA2"]["filled_at_the_look"] and b_["DOTA2"]["observed_winner_differs_from_posted_result"] == a_["DOTA2"]["sampled"] and a_["DOTA2"]["observed_winner_differs_from_posted_result"] == 0
    # AMENDMENT 9 fill: a LIMIT at the look ask + 1c, filled only if the NEXT minute shows an ask at or under it, paying the limit; the same-candle figure is printed beside it
    fl = run("fill", look_edge=0.12, half=0.005); assert fl["titles"]["DOTA2"]["fired_and_filled_next_minute"] == fl["titles"]["DOTA2"]["fired_signals_at_the_look"] == NM + 4
    nf = run("nofill", look_edge=0.12, half=0.005, bump=0.05); tn = nf["titles"]["DOTA2"]; assert tn["fired_signals_at_the_look"] == NM + 4 and 0 < tn["fired_and_filled_next_minute"] < NM + 4 and tn["fired_not_filled"] + tn["fired_and_filled_next_minute"] == NM + 4, tn          # half the matches see the ask run away at the next minute
    dnf = os.path.join(dc, "nf2"); os.mkdir(dnf); mkrun(dnf, jc, candles(look_edge=0.12, half=0.005, bump=0.05)); set_results(True); dlw2 = os.path.join(dc, "lw2"); os.mkdir(dlw2); mkrun(dlw2, jl, lists)
    msx, _c = m.matches(spec, [dlw2]); m.CFG.min_filled = 10                                    # the 150 line is for real data; a small fixture needs a small line to reach the scoring step
    try:
        calls_ = []; o_nf = bp.score_rule2(msx, [dnf], m.CFG, lambda rec: calls_.append(1) or True)
        o_ok = bp.score_rule2(msx, [dsr], m.CFG, lambda rec: True)
    finally: m.CFG.min_filled = 150
    assert 0 < o_nf["bets"] < o_nf["optimistic_same_candle_fill"]["bets"] and o_nf["counts"]["not_filled"] == o_nf["optimistic_same_candle_fill"]["bets"] - o_nf["bets"] and "optimistic" in o_nf["optimistic_same_candle_fill"]["label"], (o_nf.get("counts"), o_nf.get("verdict"))
    assert o_ok["bets"] == o_ok["optimistic_same_candle_fill"]["bets"] and o_ok["counts"]["not_filled"] == 0
    # AMENDMENT 10: tolerance, age limit, a candle carrying a bid or an ask
    cfgx = m.CFG
    assert bp.fired({"gap": 0.08, "spread": 0.54 - 0.50}, cfgx) and bp.fired({"gap": 0.58 - 0.50, "spread": 0.04}, cfgx) and not bp.fired({"gap": 0.0799, "spread": 0.04}, cfgx) and not bp.fired({"gap": 0.08, "spread": 0.0401}, cfgx)
    assert not bp.fired({"gap": 0.09, "spread": 0.02, "tie": True}, cfgx)                  # exactly equal gaps: no bet
    cdt = lambda ts, b, a: {"ts": ts, "bid": b, "ask": a}
    ixa = {"MA": {100: cdt(100, 0.93, None)}, "MB": {100: cdt(100, 0.05, 0.08)}}
    assert bp.observe_winner(ixa, {"A": "MA", "B": "MB"}, 200, close=700) == "A"          # ends exactly 10 minutes before the close: allowed
    assert bp.observe_winner(ixa, {"A": "MA", "B": "MB"}, 200, close=701) is None         # older than 10 minutes: not observable
    ixb = {"MA": {100: cdt(100, 0.93, None), 150: cdt(150, None, None)}, "MB": {100: cdt(100, 0.05, 0.08)}}
    assert bp.observe_winner(ixb, {"A": "MA", "B": "MB"}, 200, close=300) == "A"          # an empty candle (no bid, no ask) is not 'the last candle'
    ixe = {"MA": {100: cdt(100, 0.93, None), 150: cdt(150, 0.0, 1.0)}, "MB": {100: cdt(100, 0.05, 0.08), 150: cdt(150, 0.0, 1.0)}}
    assert bp.observe_winner(ixe, {"A": "MA", "B": "MB"}, 200, close=300) == "A"          # a closed market's empty book (bid 0.00, ask 1.00) is not a quote
print("mapbreak synthetic tests passed")
