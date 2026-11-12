"""Test that a NEW venue is just records plus a config (made-up basketball-style venue; no Kalshi). Run: python3 -W ignore test_breakplay.py"""
import gzip, json, os, sys, tempfile
import breakplay as bp

def mkrun(d, bodies):
    rows = []
    for i, (rid, b) in enumerate(bodies.items()):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(b)); rows.append({"id": rid, "status": 200, "file": f})
    json.dump({"job": {}, "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
# venue config: best-of-five after map 1, a 90 s look (stepping forward to 240 s), pre-match search 5 to 20 minutes before the start, held-out constant 10_000_000
cfg = bp.VenueConfig("fiveset", "bo5_after_map1", pre_back=300, pre_max_back=1200, look_after=90, look_max=240, heldout_from=10_000_000, min_filled=3)
recs = []
for i in range(6):
    S = 1_000_000 + i * 20000; sc = S + 3000
    recs.append({"cell": "V", "key": "K%d" % i, "S": S, "state_close": sc, "up": "A", "down": "B", "match": {"A": "M-K%d-A" % i, "B": "M-K%d-B" % i}, "placebo": {"A": "P-K%d-A" % i, "B": "P-K%d-B" % i}, "result_up": i % 2 == 0})
def cs(mid, half, ts_list): return [{"end_period_ts": t, "yes_bid": {"close_dollars": "%.4f" % (mid - half)}, "yes_ask": {"close_dollars": "%.4f" % (mid + half)}, "volume_fp": "1"} for t in ts_list]
V, W, q, r = bp.model_bo5_after_map1(0.6)
body = {}
for x in recs:
    pre = [x["S"] - b for b in range(300, 1201, 60)]; look = [x["state_close"] + 90 + 30 + 60 * j for j in range(0, 4)]       # first whole minute at or after close + 90 s
    look = [(-(-(x["state_close"] + 90) // 60) * 60) + 60 * j for j in range(0, 4)]
    body["a%s" % x["key"]] = {"markets": [{"market_ticker": x["match"]["A"], "candlesticks": cs(0.6, 0.005, pre) + cs(V - 0.12, 0.005, look)}, {"market_ticker": x["match"]["B"], "candlesticks": cs(0.4, 0.005, pre) + cs(1 - V + 0.01, 0.005, look)},
                                    {"market_ticker": x["placebo"]["A"], "candlesticks": cs(q, 0.005, pre)}, {"market_ticker": x["placebo"]["B"], "candlesticks": cs(1 - q, 0.005, pre)}]}
with tempfile.TemporaryDirectory() as d:
    mkrun(d, body)
    out = bp.measure([{k_: v for k_, v in x.items() if k_ != "result_up"} for x in recs], [d], cfg)
    t = out["titles"]["V"]
    assert t["filled_at_the_look"] == 6 and t["look"]["share_gap_ge_8c_spread_le_4c"] == 1.0 and t["placebo"]["share_gap_ge_8c_spread_le_4c"] == 0.0 and t["verdict"].startswith("SURVIVES") and out["rule_scored"] is False
    try: bp.measure(recs, [d], cfg); raise SystemExit("the measurement accepted a record that carries a result")
    except AssertionError: pass
    sc = bp.score_rule(recs, [d], cfg)
    assert sc["counts"]["traded"] == 6 and sc["result"]["n"] == 6 and sc["development_read_only"] is True
    j = bp.candle_job(recs, cfg, ["M", "P"], "FIVESET_CANDLES", "kalshi-scalper/workers/testing/BREAKPLAY.md"); assert len(j["requests"]) >= 1 and len(j["ticker_allowlist"]) == 24
    held = dict(recs[0], state_close=10_000_001)
    assert bp.rule_trades([held], [d], cfg)[1]["held_out_refused"] == 1 and bp.rule_trades([held], [d], cfg, heldout_go=True)[1]["held_out_refused"] == 0
print("breakplay synthetic tests passed")
