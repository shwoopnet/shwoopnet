"""Synthetic test for socderiv.py against Desk B's frozen leagues file (made-up markets; no Kalshi). Run: python3 -W ignore test_socderiv.py"""
import calendar, gzip, json, os, random, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import socderiv as s
import kalshi_pull as kp
from datetime import datetime, timezone

random.seed(11)
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]])); rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

spec = s.load_cells()
try: s.load_cells(sha="0" * 64); raise SystemExit("wrong hash passed")
except SystemExit as e: assert "does not match" in str(e)
assert len(s.leagues(spec)) == 16
jl = s.build_lists(spec); kp.check_job(jl)
ids = [r["id"] for r in jl["requests"]]; assert len(ids) == 67 and sum(i.startswith("fee_") for i in ids) == 3 and "live_KXEPLGAME" in ids and "live_KXEFLTROPHYTEAMTOTAL" in ids
# the model recovers rates from exact prices
l1, l2 = 1.6, 1.1; h, d_, a_ = s.p_winner(l1, l2); r1, r2, rm = s.fit((h, d_, a_), {kk: s.over(l1 + l2, kk) for kk in (1.5, 2.5, 3.5)}); assert abs(r1 - l1) < 0.05 and abs(r2 - l2) < 0.05 and rm < 0.01

BASE = calendar.timegm((2026, 9, 20, 12, 0, 0)); NG = 70; lists = {i: {"markets": []} for i in ids if not i.startswith("fee_")}
def mk(series, gk, suffix, close, occ, **kw):
    return dict({"ticker": "%s-%s-%s" % (series, gk, suffix), "event_ticker": "%s-%s" % (series, gk), "close_time": F(close), "open_time": F(close - 90000), "occurrence_datetime": F(occ),
                 "expected_expiration_time": F(occ), "volume_fp": "5", "title": "x", "strike_type": "greater", "result": "yes"}, **kw)
gkeys = {}
for lg in ("EPL", "LALIGA", "SERIEA", "BUNDESLIGA", "LIGUE1", "MLS", "LIGAMX", "BRASILEIRO"):
    for i in range(NG):
        ko = BASE + 3 * 3600 * i + hash(lg) % 100 * 0; gk = "26SEP%03dAAABBB" % i; close = ko + 7200; occ = ko + 10800
        if lg == "EPL" and i == 5: close = ko + 20000                      # guard fails: closes 333 minutes after the kickoff
        for sfx in ("AAA", "BBB", "TIE"): lists["live_KX%sGAME" % lg]["markets"].append(mk("KX%sGAME" % lg, gk, sfx, close, occ))
        for kk in (0.5, 1.5, 2.5, 3.5, 4.5): lists["live_KX%sTOTAL" % lg]["markets"].append(mk("KX%sTOTAL" % lg, gk, "T%s" % kk, close, occ, floor_strike=kk))
        lists["live_KX%sBTTS" % lg]["markets"].append(mk("KX%sBTTS" % lg, gk, "YES", close, occ))
        for nm in ("AAA2", "BBB2"): lists["live_KX%sTEAMTOTAL" % lg]["markets"].append(mk("KX%sTEAMTOTAL" % lg, gk, nm, close, occ, floor_strike=1.5))
        lists["live_KX%sTEAMTOTAL" % lg]["markets"].append(mk("KX%sTEAMTOTAL" % lg, gk, "ZZZ2", close, occ, floor_strike=1.5))         # team not readable: counted
HELD = s.HELD_OUT_FROM + 7200
for sfx in ("AAA", "BBB", "TIE"): lists["live_KXEPLGAME"]["markets"].append(mk("KXEPLGAME", "26NOV20HELD", sfx, HELD, HELD + 3600))   # held out: never kept
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    gs, counts = s.games(spec, [dl])
    assert counts["sampled"] == 8 * 60 and counts["games_in_window"] >= 8 * 70, counts                    # the 60 most recently settled per league, never extended
    assert counts["teamtotal_unreadable_markets"] == 8 * 60, counts
    epl = [g for g in gs if g["league"] == "EPL"]
    assert len(epl) <= 60 and all(g["kickoff"] == (g["kickoff"]) for g in epl)
    assert all(len(g["winner"]) == 3 and len(g["totals"]) == 5 and len(g["teamtotals"]) == 2 for g in gs)
    assert "result" not in json.dumps(gs)                                                                 # no result field kept anywhere
    jc, _ = s.build_candles(spec, [dl]); kp.check_job(jc); assert 1 <= len(jc["requests"]) <= 500
    def build(edge_btts, half, placebo_noise=0.0, thin=False):
        cm = {}
        for g in gs:
            l1, l2 = 1.5, 1.2; h, d_, a_ = s.p_winner(l1, l2); price = {}
            for w in g["winner"]: price[w] = d_ if w.endswith("-TIE") else (h if s.code(w) == g["team1"] else a_)
            for t, kk in g["totals"].items(): price[t] = s.over(l1 + l2, kk) + random.uniform(-placebo_noise, placebo_noise)
            for t in g["btts"]: price[t] = (1 - 2.718281828 ** -l1) * (1 - 2.718281828 ** -l2) - edge_btts
            for t, (tm, kk) in g["teamtotals"].items(): price[t] = s.over(l1 if tm == g["team1"] else l2, kk)
            for t, p in price.items():
                cm[t] = [{"end_period_ts": g["kickoff"] - 1800 - 60 * m, "yes_bid": {"close_dollars": "%.4f" % max(0.01, p - half)}, "yes_ask": {"close_dollars": "%.4f" % min(0.99, p + half)}, "volume_fp": "1"}
                         for m in range(0, 61) if not (thin and m < 61)]
        return {r["id"]: {"markets": [{"market_ticker": x, "candlesticks": cm[x]} for x in r["params"]["market_tickers"].split(",") if x in cm]} for r in jc["requests"]}
    def run(name, **kw):
        d = os.path.join(dc, name); os.mkdir(d); mkrun(d, jc, build(**kw)); return s.measure(spec, [dl], [d])
    eff = run("eff", edge_btts=0.0, half=0.005)
    A = eff["groups"]["A_big"]
    assert eff["tries_added"] == 0 and eff["rule_scored"] is False and eff["result_read"] is False and "Bitcoin 15 minute only" in eff["freshness"]
    assert A["btts"]["filled"] >= 150 and A["btts"]["verdict"].startswith("CLOSED: efficient"), A["btts"]
    assert A["btts"]["placebo"]["n"] >= 150 and A["teamtotal"]["filled"] >= 150
    sur = run("sur", edge_btts=0.15, half=0.005)
    assert sur["groups"]["A_big"]["btts"]["verdict"].startswith("SURVIVES"), sur["groups"]["A_big"]["btts"]
    nse = run("noise", edge_btts=0.09, half=0.005, placebo_noise=0.25)              # a noisy ladder makes the placebo as large as the target: model error, not the market
    assert not nse["groups"]["A_big"]["btts"]["verdict"].startswith("SURVIVES"), nse["groups"]["A_big"]["btts"]
    cost = run("cost", edge_btts=0.0, half=0.04); assert cost["groups"]["A_big"]["btts"]["verdict"].startswith("CLOSED on cost"), cost["groups"]["A_big"]["btts"]["verdict"]
    bad = os.path.join(dc, "incomplete"); os.mkdir(bad); bb = build(edge_btts=0.0, half=0.005); drop = jc["requests"][0]["id"]; bb.pop(drop); mkrun(bad, jc, bb)
    try: s.measure(spec, [dl], [bad]); raise AssertionError("incomplete candle run not refused")
    except SystemExit as ex: assert "not whole" in str(ex), ex
    thin = run("thin", edge_btts=0.0, half=0.005, thin=True); assert thin["groups"]["A_big"]["btts"]["filled"] == 0 and thin["groups"]["A_big"]["btts"]["verdict"].startswith("no evidence at n = 0")
assert abs(s.one_way(0.5, 0.40, 0.45) - (0.025 + 0.02)) < 1e-9 and s.COST_MAX == 0.04
# ---- Auditor B F1 to F5 ----
assert abs(s.gap(0.7, 0.46, 0.54) - (0.7 - 0.54)) < 1e-9 and abs(s.gap(0.3, 0.46, 0.54) - (0.3 - 0.54)) < 1e-9          # ask + bid = 1.00 (a tie) takes YES
assert abs(s.one_way(0.7, 0.46, 0.54) - (0.04 + s.fee_up(0.55))) < 1e-9
rows4 = [{"gap": 0.15, "spread": 0.54 - 0.50, "round_trip": 0.1, "one_way": 0.04} for _ in range(10)] + [{"gap": 0.0, "spread": 0.02, "round_trip": 0.1, "one_way": 0.04} for _ in range(90)]
assert s.stats(rows4)["fires"] == 10 and abs(s.stats(rows4)["share_gap_ge_8c_spread_le_4c"] - 0.1) < 1e-9          # a 4c spread written 0.54 - 0.50 counts
f1, f2, rr = s.fit((0.40, 0.30, 0.30), {1.5: 0.80, 10.5: 0.001}); assert f1 > 0 and f2 > 0                                  # a 10.5 strike does not crash the fit
assert s.near_strike({3.5: 0.55, 2.5: 0.45}) == 2.5 and s.near_strike({2.5: 0.45, 3.5: 0.55}) == 2.5 and s.near_strike({1.5: 0.9, 2.5: 0.52, 3.5: 0.2}) == 2.5
print("socderiv synthetic tests passed")
