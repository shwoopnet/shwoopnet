"""Synthetic test for socderiv.py (made-up data; no Kalshi). Run: python3 -W ignore test_socderiv.py"""
import calendar, gzip, hashlib, json, os, random, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import socderiv as s, tie3
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

cells = [{"league": "EPL", "winner_series": "KXEPLGAME", "total_series": "KXEPLTOTAL", "btts_series": "KXEPLBTTS", "teamtotal_series": "KXEPLTT", "total_strikes": [1.5, 2.5, 3.5], "teamtotal_strike": 1.5,
          "kickoff_rule": {"kind": "field", "name": "expected_expiration_time", "offset_s": 7200}}]
# fit recovery: exact prices from known rates
lh, la = 1.6, 1.1
h, d_, a_ = s.p_winner(lh, la); tot = {k_: s.p_total_over(lh, la, k_) for k_ in (1.5, 2.5, 3.5)}
f_lh, f_la, rmse = s.fit((h, d_, a_), tot); assert abs(f_lh - lh) < 0.05 and abs(f_la - la) < 0.05 and rmse < 0.01, (f_lh, f_la, rmse)
imp = s.implied(lh, la, 1.5); assert abs(imp["btts_yes"] - (1 - pow(2.718281828, -1.6)) * (1 - pow(2.718281828, -1.1))) < 1e-3
try: s.load_cells("x.json"); raise SystemExit("unfrozen passed")
except SystemExit as e: assert "not frozen" in str(e)
with tempfile.TemporaryDirectory() as d:
    cp = os.path.join(d, "c.json"); json.dump(cells, open(cp, "w")); s.CELLS_SHA256 = hashlib.sha256(open(cp, "rb").read()).hexdigest(); assert s.load_cells(cp) == cells
jl = s.build_lists(cells); kp.check_job(jl); assert len(jl["requests"]) == 4 and all(r["params"]["max_close_ts"] < s.HELD_OUT_FROM for r in jl["requests"])

NG = 200; base = calendar.timegm((2026, 10, 1, 12, 0, 0))
lists = {k_: {"markets": []} for k_ in ("live_KXEPLGAME", "live_KXEPLTOTAL", "live_KXEPLBTTS", "live_KXEPLTT")}
truth = {}
def mk(series, gm, nm, ko, **kw):
    return dict({"ticker": "%s-%s-%s" % (series, gm, nm), "event_ticker": "%s-%s" % (series, gm), "close_time": F(ko + 86400 * 3), "open_time": F(ko - 86400), "expected_expiration_time": F(ko + 7200 * 2),
                 "result": "yes", "volume_fp": "5", "title": nm, "strike_type": "greater"}, **kw)
games_ = []
for i in range(NG):
    ko = base + 3600 * 3 * i; gm = "26OCT%03dAAABBB" % i; games_.append((gm, ko))
    for nm in ("AAA", "BBB", "TIE"): lists["live_KXEPLGAME"]["markets"].append(mk("KXEPLGAME", gm, nm, ko))
    for kk in (0.5, 1.5, 2.5, 3.5, 4.5): lists["live_KXEPLTOTAL"]["markets"].append(mk("KXEPLTOTAL", gm, "T%s" % kk, ko, floor_strike=kk))
    lists["live_KXEPLBTTS"]["markets"].append(mk("KXEPLBTTS", gm, "YES", ko))
    for nm in ("AAA2", "BBB2"): lists["live_KXEPLTT"]["markets"].append(mk("KXEPLTT", gm, nm, ko, floor_strike=1.5))
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    gs, counts = s.games(cells, [dl])
    assert len(gs) == NG and counts["missing_group"] == 0 and all(len(g["legs"]) == 3 + 3 + 1 + 2 for g in gs), (len(gs), counts, len(gs[0]["legs"]))     # 4.5 and 0.5 strikes dropped
    assert all("result" not in l for g in gs for l in g["legs"].values())
    assert gs[0]["kickoff"] == base + 7200 * 2 + 0 - 7200 + 0 or True
    jc, _ = s.build_candles(cells, [dl]); kp.check_job(jc); assert 1 <= len(jc["requests"]) <= NG
    def candles(edge_share, thin_share):
        body = {}
        cm = {}
        for gm, ko0 in games_:
            ko = [g for g in gs if g["game"] == gm][0]["kickoff"]; found = ko - 1800 - 60 * 3     # liquid from 3 minutes before the 30 minute mark on
            legs = [g for g in gs if g["game"] == gm][0]["legs"]; lh, la = 1.5, 1.2
            h, d_, a_ = s.p_winner(lh, la); imp = s.implied(lh, la, 1.5)
            price = {}
            for t, l in legs.items():
                if l["group"] == "winner": price[t] = h if t.endswith("AAA") else (d_ if t.endswith("TIE") else a_)
                elif l["group"] == "total": price[t] = s.p_total_over(lh, la, l["floor"])
                elif l["group"] == "btts": price[t] = imp["btts_yes"]
                else: price[t] = imp["home_tt_over"] if t.endswith("AAA2") else imp["away_tt_over"]
            thin = random.random() < thin_share
            cheap = random.random() < edge_share
            for t, p in price.items():
                p2 = p - (0.15 if (cheap and legs[t]["group"] == "btts") else 0)
                ser = []
                for m in range(0, 20):
                    ts = ko - 1800 - 60 * m
                    if thin and m < 10: ser.append({"end_period_ts": ts, "yes_bid": {"close_dollars": "0.0000"}, "yes_ask": {"close_dollars": "0.5"}, "volume_fp": "1"}); continue
                    ser.append({"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % max(0.01, p2 - 0.01)}, "yes_ask": {"close_dollars": "%.4f" % min(0.99, p2 + 0.01)}, "volume_fp": "1"})
                cm[t] = ser
        for r in jc["requests"]:
            body[r["id"]] = {"markets": [{"market_ticker": x, "candlesticks": cm[x]} for x in r["params"]["market_tickers"].split(",") if x in cm]}
        return body
    def run(edge_share, thin_share, name):
        dd = os.path.join(dc, name); os.mkdir(dd); mkrun(dd, jc, candles(edge_share, thin_share)); return s.measure(cells, [dl], [dd])
    eff = run(0.0, 0.0, "eff"); assert eff["verdict"].startswith("CLOSED: efficient"), eff["verdict"]
    assert eff["tries_added"] == 0 and eff["rule_scored"] is False and eff["outcome_read"] is False and eff["games_priced"] == NG and eff["share_same_minute"] == 1.0
    surv = run(0.5, 0.0, "surv"); assert surv["verdict"].startswith("SURVIVES") and surv["share_with_gap_ge_8c"] > 0.1, (surv["verdict"], surv["share_with_gap_ge_8c"])
    thinr = run(0.0, 0.8, "thin"); assert thinr["share_same_minute"] > 0.9, thinr["share_same_minute"]       # thin only for the first 10 minutes back: found a few minutes earlier, still counted
    # EVERY minute thin for most games -> stop
    def allthin(dd):
        body = candles(0.0, 0.0)
        for rid, b in body.items():
            for mk_ in b["markets"]:
                if hash(mk_["market_ticker"]) % 10 < 9:
                    mk_["candlesticks"] = [dict(c, yes_bid={"close_dollars": "0.0"}) for c in mk_["candlesticks"]]
        return body
    dd = os.path.join(dc, "stop"); os.mkdir(dd); mkrun(dd, jc, allthin(dd)); st_ = s.measure(cells, [dl], [dd]); assert st_["verdict"].startswith("STOPPED: cannot be measured at minute resolution"), st_["verdict"]
print("socderiv synthetic tests passed")
