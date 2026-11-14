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
    # ---- the two job files (Head: A and B by kickoff date, cut at a pack boundary, union equals the whole, no ticker in both, each with slack and the held-out line)
    A_, B_ = s.split_candles(jc); kp.check_job(A_); kp.check_job(B_)
    assert len(A_["requests"]) + len(B_["requests"]) == len(jc["requests"]) and A_["max_requests"] == len(A_["requests"]) + 20 and "HELDOUT_REGISTRY" in A_["heldout"] and "SHARP1" in B_["heldout"]
    assert not (set(A_["ticker_allowlist"]) & set(B_["ticker_allowlist"])) and A_["job_id"] == "SOCDERIV_CANDLES_A"
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
    d_pg = os.path.join(dc, "pg"); os.mkdir(d_pg); mkrun(d_pg, jc, build(edge_btts=0.0, half=0.005)); pgf = os.path.join(dc, "socderiv_pergame.csv")
    s.measure(spec, [dl], [d_pg], pergame=pgf); import csv as csv_; txt_ = open(pgf).read().splitlines(); assert txt_[0] == "game_key,fit_iters,cap_hit,rate_home,rate_away,sse,leg_ticker,leg_type,strike,model_value,market_mid,gap,side,edge,fires"
    pgl = list(csv_.DictReader(open(pgf))); keys_ = [(r["game_key"], r["leg_ticker"]) for r in pgl]; assert keys_ == sorted(keys_) and len(set(r["leg_ticker"] for r in pgl)) == len(pgl)
    nlegs_ = sum(len(g_["btts"]) + len(g_["teamtotals"]) + len(g_["teamtotals_unreadable"]) for g_ in gs); assert len(pgl) == nlegs_ and nlegs_ > 300, (len(pgl), nlegs_)          # a row for EVERY target leg of every derivable game
    assert all(r["game_key"] == "KX" + g_["league"] + "GAME-" + g_["game"] for r, g_ in [(r, next(x for x in gs if "KX" + x["league"] + "GAME-" + x["game"] == r["game_key"])) for r in pgl])
    assert all(r["game_key"].startswith("KX") and "GAME-" in r["game_key"] for r in pgl)
    assert not any(("result" in c_ or "settle" in c_) for c_ in txt_[0].split(",")) and {r["leg_type"] for r in pgl} == {"btts", "team_total"}
    bad_ = {tk_ for g_ in gs for tk_, _ in g_["teamtotals_unreadable"]}; assert len(bad_) == 8 * 60
    for r in pgl:
        if r["leg_ticker"] in bad_:
            assert all(r[c_] == "" for c_ in ("fit_iters", "cap_hit", "rate_home", "rate_away", "sse", "model_value", "market_mid", "gap")) and r["fires"] == "False" and r["leg_type"] == "team_total" and r["side"] == "" and r["edge"] == ""; continue
        for c_ in ("rate_home", "rate_away", "sse", "model_value", "market_mid", "gap", "edge"): assert repr(float(r[c_])) == r[c_], (c_, r[c_])
        assert abs(float(r["gap"]) - (float(r["model_value"]) - float(r["market_mid"]))) < 1e-12 and r["side"] in ("yes", "no")
        assert (r["strike"] == "") == (r["leg_type"] == "btts") and (r["strike"] == "1.5" or r["leg_type"] == "btts") and r["fires"] in ("True", "False") and r["cap_hit"] == "False" and 0 <= int(r["fit_iters"]) <= 200
        assert 0.01 <= float(r["rate_home"]) <= 6.0 and 0.01 <= float(r["rate_away"]) <= 6.0
        assert (r["fires"] == "True") == (float(r["edge"]) >= s.GAP - 1e-9)          # the fixture half-spread is 0.005, so the spread leg of the rule always holds
    assert sum(1 for r in pgl if r["leg_type"] == "btts") >= 150
    d_th = os.path.join(dc, "pgthin"); os.mkdir(d_th); mkrun(d_th, jc, build(edge_btts=0.0, half=0.005, thin=True)); pgt = os.path.join(dc, "thin.csv"); s.measure(spec, [dl], [d_th], pergame=pgt)
    thin_ = list(csv_.DictReader(open(pgt))); assert len(thin_) == nlegs_ and all(r["fit_iters"] == "" and r["rate_home"] == "" and r["model_value"] == "" and r["market_mid"] == "" and r["gap"] == "" and r["side"] == "" and r["edge"] == "" and r["fires"] == "False" and r["leg_ticker"] for r in thin_)
    assert [(r["game_key"], r["leg_ticker"]) for r in thin_] == keys_
    nopg = run("nopg", edge_btts=0.0, half=0.005); assert "polish" in nopg and nopg["polish"]["fits"] > 0 and nopg["polish"]["cap_hit"] == 0 and nopg["polish"]["max_iterations"] <= 200 and nopg["polish"]["fits_on_bound"] == 0
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
assert s.near_strike({3.5: (0.54, 0.56), 2.5: (0.44, 0.46)}) == 2.5 and s.near_strike({2.5: (0.44, 0.46), 3.5: (0.54, 0.56)}) == 2.5 and s.near_strike({1.5: (0.89, 0.91), 2.5: (0.51, 0.53), 3.5: (0.19, 0.21)}) == 2.5
assert s.near_strike({2.5: (0.495, 0.500), 3.5: (0.500, 0.505)}) == 2.5 and s.near_strike({3.5: (0.495, 0.500), 2.5: (0.4951, 0.5000)}) == 2.5          # sub-cent quotes: exact tie to the lower strike, no false tie
try: s.check_candle_runs(spec, [dl], ["/tmp/HELDOUT_X"]); raise AssertionError("held-out candle folder not refused")
except SystemExit as ex: assert "HELDOUT" in str(ex) or "held" in str(ex).lower(), ex
# ---- Fit polish and unrounded figures (SOCDERIV_FIT_ADDENDUM.md, Auditor B 02:48Z) ----
def exact(l1_, l2_, strikes):
    h_, d2_, a2_ = s.p_winner(l1_, l2_); return (h_, d2_, a2_), {kk: s.over(l1_ + l2_, kk) for kk in strikes}
for (l1_, l2_, ks_) in ((1.4, 1.0, (1.5, 2.5, 3.5)), (0.9, 1.7, (0.5, 1.5, 2.5, 3.5, 4.5)), (2.1, 0.45, (1.5, 2.5, 3.5, 10.5))):
    wm_, tm_ = exact(l1_, l2_, ks_); g1, g2, grm = s.fit(wm_, tm_)
    assert abs(g1 - l1_) < 1e-9 and abs(g2 - l2_) < 1e-9 and grm < 1e-9, (l1_, l2_, g1, g2, grm)          # exact recovery to 1e-9 (the old grid: about 4e-5)
def sse_(a_, b_, wm_, tm_):
    h_, d2_, c_ = s.p_winner(a_, b_); lam_ = a_ + b_
    return (h_ - wm_[0]) ** 2 + (d2_ - wm_[1]) ** 2 + (c_ - wm_[2]) ** 2 + sum((s.over(lam_, kk) - v) ** 2 for kk, v in tm_.items())
def nelder_mead(f, x0, iters=4000):
    pts = [list(x0), [x0[0] + 0.01, x0[1]], [x0[0], x0[1] + 0.01]]; vals = [f(*p_) for p_ in pts]
    for _ in range(iters):
        o_ = sorted(range(3), key=lambda i: vals[i]); pts = [pts[i] for i in o_]; vals = [vals[i] for i in o_]
        if abs(vals[2] - vals[0]) < 1e-18: break
        c_ = [(pts[0][k_] + pts[1][k_]) / 2 for k_ in range(2)]
        r_ = [2 * c_[k_] - pts[2][k_] for k_ in range(2)]; fr = f(*r_) if min(r_) > 0.001 else 9
        if fr < vals[0]:
            e_ = [3 * c_[k_] - 2 * pts[2][k_] for k_ in range(2)]; fe = f(*e_) if min(e_) > 0.001 else 9
            pts[2], vals[2] = (e_, fe) if fe < fr else (r_, fr)
        elif fr < vals[1]: pts[2], vals[2] = r_, fr
        else:
            ic = [(c_[k_] + pts[2][k_]) / 2 for k_ in range(2)]; fi = f(*ic)
            if fi < vals[2]: pts[2], vals[2] = ic, fi
            else:
                for i in (1, 2): pts[i] = [(pts[0][k_] + pts[i][k_]) / 2 for k_ in range(2)]; vals[i] = f(*pts[i])
    return pts[0], vals[0]
for (l1_, l2_, ks_) in ((1.4, 1.0, (1.5, 2.5, 3.5)), (0.9, 1.7, (0.5, 1.5, 2.5, 3.5, 4.5)), (1.9, 0.7, (1.5, 2.5, 3.5))):
    wm_, tm_ = exact(l1_, l2_, ks_); wm_ = (wm_[0] + .01, wm_[1] - .015, wm_[2] + .005); tm_ = {kk: v + o_ for (kk, v), o_ in zip(tm_.items(), (.012, -.008, .004, .006, -.003))}
    g1, g2, grm = s.fit(wm_, tm_); (x_, y_), v_ = nelder_mead(lambda a_, b_: sse_(a_, b_, wm_, tm_), [g1, g2])
    assert sse_(g1, g2, wm_, tm_) <= v_ + 1e-14 and abs(g1 - x_) < 1e-5 and abs(g2 - y_) < 1e-5, (sse_(g1, g2, wm_, tm_), v_, g1, x_, g2, y_)          # at the reference minimum
    assert abs(grm - (sse_(g1, g2, wm_, tm_) / (3 + len(tm_))) ** 0.5) < 1e-12
gst = s.stats([{"gap": g_, "spread": 0.02, "round_trip": 0.05 + g_ / 10, "one_way": 0.03} for g_ in (0.0123456789, 0.0234567891, 0.0345678912, 0.0456789123)])
q1_ = 0.0123456789 + 0.75 * (0.0234567891 - 0.0123456789); md_ = (0.0234567891 + 0.0345678912) / 2; q3_ = 0.0345678912 + 0.25 * (0.0456789123 - 0.0345678912); p90_ = 0.0345678912 + 0.7 * (0.0456789123 - 0.0345678912) if False else None
gq = gst["gap_quartiles_p90"]
assert abs(gq[0] - q1_) < 1e-12 and abs(gq[1] - md_) < 1e-12 and abs(gq[2] - q3_) < 1e-12 and gq[0] != round(gq[0], 4) and gq[3] != round(gq[3], 4) and gst["median_spread"] == 0.02 and gst["median_one_way_entry_cost"] == 0.03
assert gst["share_gap_ge_8c_spread_le_4c"] == 0.0 and abs(s.stats(rows4)["share_gap_ge_8c_spread_le_4c"] - 0.1) < 1e-15 and s.stats([{"gap": 0.1, "spread": 0.03, "round_trip": 0.1, "one_way": 0.04}] * 3)["share_gap_ge_8c_spread_le_4c"] == 1.0
st3 = s.stats([{"gap": 0.1 / 3 * i, "spread": 0.0123456, "round_trip": 0.07, "one_way": 0.04123456} for i in (1, 2, 3)]); assert st3["median_spread"] == 0.0123456 and st3["median_one_way_entry_cost"] == 0.04123456
# ---- Addendum 2 (Head rulings 02:59Z): box [0.01, 6.0], Poisson sums to 40 goals, polish rule and cap, reported iterations ----
def p80(l1_, l2_):
    p1_ = [math.exp(-l1_) * l1_ ** n / math.factorial(n) for n in range(80)]; p2_ = [math.exp(-l2_) * l2_ ** n / math.factorial(n) for n in range(80)]
    return (math.fsum(p1_[i] * p2_[j] for i in range(80) for j in range(i)), math.fsum(p1_[i] * p2_[i] for i in range(80)), math.fsum(p1_[i] * p2_[j] for i in range(80) for j in range(i + 1, 80)))
import math
for (a_, b_) in ((5.0, 4.0), (1.5, 1.2), (6.0, 6.0), (0.3, 0.02)):
    h_, d_, c_ = s.p_winner(a_, b_); r_ = p80(a_, b_)
    assert abs(h_ + d_ + c_ - 1) < 1e-14 and all(abs(x - y) < 1e-14 for x, y in zip((h_, d_, c_), r_)), (a_, b_, (h_, d_, c_), r_)
h12 = s.p_winner(1.5, 1.2, N=12); h40 = s.p_winner(1.5, 1.2); assert max(abs(x - y) for x, y in zip(h12, h40)) > 1e-9          # N = 12 was wrong at 1e-9
for (l1_, l2_) in ((0.5, 0.015), (0.012, 1.4), (5.2, 0.8)):
    wm_, tm_ = exact(l1_, l2_, (1.5, 2.5, 3.5)); g1, g2, grm = s.fit(wm_, tm_)
    assert abs(g1 - l1_) < 1e-9 and abs(g2 - l2_) < 1e-9, (l1_, l2_, g1, g2)
for wm_, tm_ in (((0.02, 0.03, 0.95), {1.5: 0.99, 2.5: 0.99}), ((0.4, 0.3, 0.3), {1.5: 0.0001, 2.5: 0.00001})):
    g1, g2, _ = s.fit(wm_, tm_); assert 0.01 <= g1 <= 6.0 and 0.01 <= g2 <= 6.0, (g1, g2)
wm_, tm_ = exact(1.4, 1.0, (1.5, 2.5, 3.5)); fr = s.fit_full(wm_, tm_)
assert fr["cap_hit"] is False and 0 <= fr["iterations"] <= 200 and abs(fr["l1"] - 1.4) < 1e-9
wm2_ = (wm_[0] + .01, wm_[1] - .015, wm_[2] + .005); fr1 = s.fit_full(wm2_, tm_, cap=1); assert fr1["cap_hit"] is True and fr1["iterations"] == 1
fr200 = s.fit_full(wm2_, tm_); assert fr200["cap_hit"] is False and fr200["iterations"] > 1 and fr200["sse"] <= fr1["sse"]
print("socderiv addendum 2 tests passed")
# ---- Addendum 5: boundary rule ----
def sse2_(a_, b_, wm_, tm_): return sse_(a_, b_, wm_, tm_)
def golden(f, lo, hi):
    g_ = (math.sqrt(5) - 1) / 2; c_, d_ = hi - g_ * (hi - lo), lo + g_ * (hi - lo)
    for _ in range(200):
        if f(c_) < f(d_): hi = d_
        else: lo = c_
        c_, d_ = hi - g_ * (hi - lo), lo + g_ * (hi - lo)
    return (lo + hi) / 2
def grad_(a_, b_, wm_, tm_, which):
    hh = 1e-6
    if which == 0: return (sse_(a_ + hh, b_, wm_, tm_) - sse_(a_ - hh, b_, wm_, tm_)) / (2 * hh)
    return (sse_(a_, b_ + hh, wm_, tm_) - sse_(a_, b_ - hh, wm_, tm_)) / (2 * hh)
wm_, tm_ = exact(0.5, 0.005, (1.5, 2.5, 3.5)); fb = s.fit_full(wm_, tm_)
ref_ = golden(lambda v_: sse_(v_, 0.01, wm_, tm_), 0.01, 6.0)
assert fb["l2"] == 0.01 and abs(fb["l1"] - ref_) < 1e-8 and fb["on_bound"] is True and abs(grad_(fb["l1"], 0.01, wm_, tm_, 0)) < 1e-9, (fb, ref_)
wm_, tm_ = exact(6.8, 1.0, (1.5, 2.5, 3.5)); fb = s.fit_full(wm_, tm_)
ref_ = golden(lambda v_: sse_(6.0, v_, wm_, tm_), 0.01, 6.0)
assert fb["l1"] == 6.0 and abs(fb["l2"] - ref_) < 1e-8 and fb["on_bound"] is True and abs(grad_(6.0, fb["l2"], wm_, tm_, 1)) < 1e-9, (fb, ref_)
wm_, tm_ = exact(0.001, 0.002, (1.5, 2.5, 3.5)); fb = s.fit_full(wm_, tm_)
assert fb["l1"] == 0.01 and fb["l2"] == 0.01 and fb["on_bound"] is True and fb["iterations"] == 1 and fb["cap_hit"] is False, fb          # nothing iterated in the 1-D stage
for (l1_, l2_) in ((1.4, 1.0), (0.012, 1.4)):
    wm_, tm_ = exact(l1_, l2_, (1.5, 2.5, 3.5)); fb = s.fit_full(wm_, tm_); assert fb["on_bound"] is False and abs(fb["l1"] - l1_) < 1e-9
# a rate within 1e-12 of a bound whose gradient points INTO the box is not held
wm_, tm_ = exact(1.4, 1.0, (1.5, 2.5, 3.5)); res_ = lambda a_, b_: [x_ - y_ for x_, y_ in zip(list(s.p_winner(a_, b_)) + [1 - sum(s.pois(a_ + b_, n_) for n_ in range(int(kk_) + 1)) for kk_ in (1.5, 2.5, 3.5)], list(wm_) + list(tm_.values()))]
inward = s.boundary_stage(res_, sse_(0.01, 1.0, wm_, tm_), 0.01, 1.0, 5, False, 200); assert inward[5] is False and inward[1] == 0.01 and inward[3] == 5
# the 1-D result is discarded when its SSE is above the 2-D result's by more than 1e-15 (stub)
wm_, tm_ = exact(0.5, 0.005, (1.5, 2.5, 3.5)); res_ = lambda a_, b_: [x_ - y_ for x_, y_ in zip(list(s.p_winner(a_, b_)) + [1 - sum(s.pois(a_ + b_, n_) for n_ in range(int(kk_) + 1)) for kk_ in (1.5, 2.5, 3.5)], list(wm_) + list(tm_.values()))]
base_ = sse_(0.3, 0.01, wm_, tm_); worse = s.boundary_stage(res_, base_, 0.3, 0.01, 7, False, 200, stub=(base_ + 1e-9, 0.3, 0.01, 9, False, True)); assert worse == (base_, 0.3, 0.01, 7, False, False), worse
print("socderiv addendum 5 tests passed")
print("socderiv synthetic tests passed")
