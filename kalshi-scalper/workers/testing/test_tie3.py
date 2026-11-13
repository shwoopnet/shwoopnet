"""Synthetic test for tie3.py against Desk B's frozen cells (made-up markets; no Kalshi). Run: python3 -W ignore test_tie3.py"""
import calendar, gzip, hashlib, json, os, random, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
import tie3 as t
import kalshi_pull as kp
from datetime import datetime, timezone

random.seed(7)
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def mkrun(d, job, bodies):
    rows = []
    for i, r in enumerate(job["requests"]):
        if r["id"] in bodies:
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(bodies[r["id"]])); rows.append({"id": r["id"], "status": 200, "file": f})
    json.dump({"job": job, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

spec = t.load_cells()                                    # the real frozen file, hash-checked
assert [c["cell"] for c in spec["cells"]] == ["NHL_P1", "NHL_P2", "NHL_P3", "NHL_REG", "NFL_Q", "SOC_1H"] and len(t.all_series(spec)) == 20
try: t.load_cells(sha="0" * 64); raise SystemExit("wrong hash passed")
except SystemExit as e: assert "does not match" in str(e)
jl = t.build_lists(spec); kp.check_job(jl)
ids = [r["id"] for r in jl["requests"]]
assert len(ids) == 32 and sum(i.startswith("live_") for i in ids) == 20 and sum(i.startswith("hist_") for i in ids) == 8 and sum(i.startswith("fee_") for i in ids) == 4 and jl["max_requests"] == 60
assert all(r["params"].get("max_close_ts", 0) < t.HELD_OUT_FROM for r in jl["requests"] if "params" in r)

def mk(series, gk, nm, close, occ, res):
    return {"ticker": "%s-%s-%s" % (series, gk, nm), "event_ticker": "%s-%s" % (series, gk), "close_time": F(close), "open_time": F(close - 90000), "occurrence_datetime": F(occ), "expected_expiration_time": F(occ),
            "result": res, "volume_fp": "5", "title": "x", "strike_type": "greater"}
lists = {r["id"]: {"markets": []} for r in jl["requests"] if not r["id"].startswith("fee_")}
def game(series, gk, tie_yes, close, start, first_close_after=3600, reg=False, first_series=None, same=False):
    """One game: Tie market (or the single NHL_REG market) with occurrence = start + 180 min; first-period market closing first_close_after seconds after the start."""
    occ = start + 10800; out = {}
    names = ["1"] if reg else ["AAA", "BBB", "TIE"]
    for nm in names:
        yes = (nm == "1" and tie_yes) if reg else ((nm == "TIE") if tie_yes else (nm == "AAA"))
        lists["live_" + series]["markets"].append(mk(series, gk, nm, close, occ, "yes" if yes else "no"))
    if first_series and not same:
        for nm in ["AAA", "BBB", "TIE"]:
            lists["live_" + first_series]["markets"].append(mk(first_series, gk, nm, start + first_close_after, occ, "no"))
base_t = calendar.timegm((2026, 10, 5, 22, 0, 0)); price_t = calendar.timegm((2026, 11, 2, 22, 0, 0))
NB, NP = 200, 60
for i in range(NB):                                       # NHL_P1 base: 40 percent level; NFL_Q 1Q base: 20 percent; NHL_REG base 22 percent
    st_ = base_t + 7200 * i
    game("KXNHL1P", "26OCT%03d" % i, i % 5 < 2, st_ + 4000, st_)
    game("KXNFL1Q", "26OCT%03d" % i, i % 5 == 0, st_ + 4000, st_)
    game("KXNHLOT", "26OCT%03d" % i, i % 9 < 2, st_ + 11000, st_, reg=True)
bad = base_t + 99
lists["live_KXNHL1P"]["markets"] += [mk("KXNHL1P", "26OCT999BAD", "AAA", bad, bad, "yes"), mk("KXNHL1P", "26OCT999BAD", "TIE", bad, bad, "no")]          # only two markets: dropped and counted
HELD = t.HELD_OUT_FROM + 7200
game("KXNHL1P", "26NOV20HELD", True, HELD, HELD - 4000)                                  # held out: never kept
starts = []
for i in range(NP):
    st_ = price_t + 7200 * i; starts.append(st_)
    game("KXNHL1P", "26NOV%03d" % i, i % 2 == 0, st_ + 4000, st_)                         # first-period market closes 4000 s = 67 min after the start: inside the 20 to 120 minute guard
badg = price_t + 7200 * NP + 5000; lists["live_KXNHL1P"]["markets"] += [mk("KXNHL1P", "26NOV998G", nm, badg + 9000, badg, "no") for nm in ("AAA", "BBB", "TIE")]   # closes 9000 s after the start: guard fails
for i in range(NP):                                       # NFL_Q price: quarter 1 only, base rate for KXNFL1Q
    st_ = price_t + 86400 + 7200 * i
    game("KXNFL1Q", "26NOV%03d" % (300 + i), i % 5 == 0, st_ + 4000, st_)
with tempfile.TemporaryDirectory() as dl, tempfile.TemporaryDirectory() as dc:
    mkrun(dl, jl, lists)
    ev, counts = t.events(spec, [dl])
    assert len(ev["NHL_P1"]["base"]) == NB and len(ev["NFL_Q"]["base"]) == NB and len(ev["NHL_REG"]["base"]) == NB, [len(v["base"]) for v in ev.values()]
    assert counts["held_out_dropped"] >= 1 and counts["dropped_wrong_market_count"] >= 1 and counts["start_not_derivable"] >= 1, counts
    assert len(ev["NHL_P1"]["price"]) == NP, len(ev["NHL_P1"]["price"])
    assert all(set(e) == {"event", "key", "tie_ticker", "T"} for v in ev.values() for e in v["price"])           # the price block carries no result and no level
    e0 = ev["NHL_P1"]["price"][0]; assert e0["T"] == starts[0] - 1800
    assert ev["NFL_Q"]["base"][0]["key"] == "KXNFL1Q"
    jc, _ = t.build_candles(spec, [dl]); kp.check_job(jc)
    assert 1 <= len(jc["requests"]) <= 40 and all(r["params"]["end_ts"] < t.HELD_OUT_FROM + 86400 * 3 for r in jc["requests"])
    ties = {e["tie_ticker"]: e for v in ev.values() for e in v["price"]}
    assert set(jc["ticker_allowlist"]) == set(ties)
    def candles(ask_for, half, skip_first=0):
        out = {}
        for tk, e in ties.items():
            a = ask_for(tk)
            out[tk] = [{"end_period_ts": e["T"] - 60 * j, "yes_bid": {"close_dollars": "%.4f" % (a - 2 * half)}, "yes_ask": {"close_dollars": "%.4f" % a}, "volume_fp": "1"} for j in range(skip_first, 31)]
        return out
    def body(cm): return {r["id"]: {"markets": [{"market_ticker": x, "candlesticks": cm[x]} for x in r["params"]["market_tickers"].split(",") if x in cm]} for r in jc["requests"]}
    cm = candles(lambda tk: 0.28 if "NHL1P" in tk else 0.15, 0.015)
    mkrun(dc, jc, body(cm)); out = t.measure(spec, [dl], [dc])
    c = out["cells"]["NHL_P1"]
    assert out["tries_added"] == 0 and out["rule_scored"] is False and out["result_of_priced_game_read"] is False and "Bitcoin 15 minute only" in out["freshness"]
    assert c["status"] == "measured" and abs(c["base_rates_by_key"]["NHL_P1"]["rate"] - 0.4) < 1e-9 and c["share_two_sided"] == 1.0
    assert abs(c["gap_q1_median_q3"][1] - 0.12) < 1e-9 and abs(c["median_spread"] - 0.03) < 1e-9 and c["share_two_sided_games_with_ask_10c_under_and_spread_le_4c"] == 1.0
    assert abs(out["cells"]["NFL_Q"]["gap_q1_median_q3"][1] - 0.05) < 1e-9 and out["verdict"].startswith("SURVIVES") and "NHL_P1" in out["verdict"], out["verdict"]
    assert out["cells"]["SOC_1H"]["status"].startswith("no evidence") and out["cells"]["NHL_P2"]["status"].startswith("no evidence")
    # step back: the minute at T missing, the first two-sided minute within 30 back is used; none within 30 -> not two-sided
    dc2 = os.path.join(dc, "b"); os.mkdir(dc2); mkrun(dc2, jc, body(candles(lambda tk: 0.28, 0.015, skip_first=7))); r2 = t.measure(spec, [dl], [dc2])["cells"]["NHL_P1"]; assert r2["share_two_sided"] == 1.0
    dc3 = os.path.join(dc, "c"); os.mkdir(dc3); mkrun(dc3, jc, body(candles(lambda tk: 0.28, 0.015, skip_first=31))); r3 = t.measure(spec, [dl], [dc3]); assert r3["cells"]["NHL_P1"]["two_sided"] == 0
    # one-sided (bid 0) candles are not filled
    dc4 = os.path.join(dc, "d"); os.mkdir(dc4); mkrun(dc4, jc, body(candles(lambda tk: 0.28, 0.14))); assert t.measure(spec, [dl], [dc4])["cells"]["NHL_P1"]["two_sided"] == 0
    # efficient: ask at the base rate
    dc5 = os.path.join(dc, "e"); os.mkdir(dc5); mkrun(dc5, jc, body(candles(lambda tk: 0.40 if "NHL1P" in tk else 0.2, 0.015))); assert t.measure(spec, [dl], [dc5])["verdict"].startswith("CLOSED: efficient")
    # Head's ruling Nov 13: a price-block game with a market that carries no yes/no result is KEPT and counted (family-level), nothing is filtered on a result field
    ntot = len(ev["NHL_P1"]["price"]); lists["live_KXNHL1P"]["markets"][-4]["result"] = ""
    for mk_ in lists["live_KXNHL1P"]["markets"]:
        if mk_["ticker"].split("-")[1] == ev["NHL_P1"]["price"][0]["event"]: mk_["result"] = ""
    dl3 = os.path.join(dc, "unset"); os.mkdir(dl3); mkrun(dl3, jl, lists); ev3, c3 = t.events(spec, [dl3])
    assert len(ev3["NHL_P1"]["price"]) == ntot and c3["price_block_games_not_all_settled_COUNTED_NOT_FILTERED"] >= 1, c3
print("tie3 synthetic tests passed")
