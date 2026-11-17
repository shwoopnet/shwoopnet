"""Helper for test/shadowRunnerV4Gates.test.js: drives the V4 runner's pure functions on INVENTED data (no network). Prints one JSON line."""
import json, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, "scripts"))
import shadow_runner as R, shadow_runner_v4 as V
W = os.path.join(root, "kalshi-scalper", "workers")
cfg = V.load_config(root, "V4")
lst, mods, table, H, cuts = V.verified_inputs(root, cfg)
N, C = mods["engine1_enum"], mods["engine1_batchc"]
out = {"loaded": sorted(mods)}

# 1. Desk A's fixture: every case's x and class through the runner's own feature code
fx = json.load(open(os.path.join(W, "V4_RUNNER_FIXTURE_NOV16.json")))
e = 100000; bad = []
for c in fx["cases"]:
    f = c["feature"]; case = c.get("case")
    if f == "oiacc":
        oi = {-360: c.get("oi_e_minus_360"), -180: c.get("oi_e_minus_180"), 0: c.get("oi_e")}
        by = {e + k: (e + k, .5, .6, None, 1, v) for k, v in oi.items()}
        if case == "oi at e - 360 null": by[e - 360] = (e - 360, .5, .6, None, 1, None)
        elif case == "oi at e - 180 null": by[e - 180] = (e - 180, .5, .6, None, 1, None)
        elif case == "oi at e null": by[e] = (e, .5, .6, None, 1, None)
        elif case == "candle e - 180 absent": by = {e - 360: (e - 360, .5, .6, None, 1, 100), e: (e, .5, .6, None, 1, 130)}
        m = {"close": e + 100, "candles": sorted(by.values())}
        k = V.feature_class(mods, "oiacc", m, None, e); x = C.oiacc({c_[0]: c_ for c_ in m["candles"]}, e)
    else:
        if case == "other market absent": idx = None
        else:
            idx = {}
            if case != "candle e - 180 absent" and "other_e_minus_180" in c: idx[e - 180] = (e - 180, c["other_e_minus_180"][0], c["other_e_minus_180"][1], 0, 0, 0)
            if case != "candle e absent" and "other_e" in c: idx[e] = (e, c["other_e"][0], c["other_e"][1], 0, 0, 0)
            if case == "candle e - 180 absent": idx = {e: (e, .5, .6, 0, 0, 0)}
            if case == "candle e absent": idx = {e - 180: (e - 180, .5, .6, 0, 0, 0)}
        k = V.feature_class(mods, f, {"close": e + 100, "candles": []}, idx, e); x = None if idx is None else C.xmom(idx, e)
    want = c["expected_class"]; got = "missing" if k is None else k
    if got != want or (c["expected_x"] is None) != (x is None) or (x is not None and abs(x - c["expected_x"]) > 1e-12): bad.append([f, case, got, want, x, c["expected_x"]])
out["fixture_cases"] = len(fx["cases"]); out["fixture_bad"] = bad

# 2. end to end on an invented market for SH4_07_XRP (oiacc:down) and SH4_06_WTI (ethmom3:up)
specs = {s["spec"]["id"]: s for s in lst["specs"]}
def mk(close, spec, oi, yb, ya, result="yes"):
    b = spec["entry"]["seconds_left"]; ee = close - b
    cs = [(ee - 360, .5, .6, None, 1, oi[0]), (ee - 180, .5, .6, None, 1, oi[1]), (ee, yb, ya, None, 1, oi[2]), (close, 0.99, 1.0, None, 1, oi[2])]
    return {"series": spec["market"], "ticker": spec["market"] + "-T%d" % close, "close": close, "result": result, "candles": cs}
start = cfg["start_utc"]; close = start + 5 * 86400 + 3600
sp = specs["SH4_07_XRP"]["spec"]; sha = specs["SH4_07_XRP"]["spec_sha256"]
band, side_rule = sp["entry"]["price_band_5c"], sp["entry"]["side_rule"]
ok_guard = lambda info, t, c: (True, "clear"); no_guard = lambda info, t, c: (False, "held")
# find a bid and ask whose chosen side lands in the band
found = None
for cents in range(5, 95):
    yb, ya = (cents - 1) / 100.0, cents / 100.0
    ent_try = N.entries([(close - sp["entry"]["seconds_left"], yb, ya, None, 1, 1)], close, sp["entry"]["seconds_left"], band, side_rule, None, None)[0]
    if ent_try is not None: found = (yb, ya); break
out["band_found"] = found is not None
yb, ya = found
down = mk(close, sp, [100, 120, 130], yb, ya)       # (130-120)-(120-100) = -10 : down
up = mk(close, sp, [100, 110, 130], yb, ya)         # +10 : up
nulloi = mk(close, sp, [None, 120, 130], yb, ya)
args = (mods, sp, [down], {}, start, ok_guard, ["KXXRP15M"], sha)
out["down_trades"] = len(V.score_spec_v4(*args)[0])
out["up_trades"] = len(V.score_spec_v4(mods, sp, [up], {}, start, ok_guard, ["KXXRP15M"], sha)[0])
out["null_oi_trades"] = len(V.score_spec_v4(mods, sp, [nulloi], {}, start, ok_guard, ["KXXRP15M"], sha)[0])
t, refused = V.score_spec_v4(mods, sp, [down], {}, start, no_guard, ["KXXRP15M"], sha)
out["held_trades"], out["held_refused"] = len(t), refused
early = mk(start - 7200, sp, [100, 120, 130], yb, ya)
out["before_start_trades"] = len(V.score_spec_v4(mods, sp, [early], {}, start, ok_guard, ["KXXRP15M"], sha)[0])

# 3. cross series (SH4_06_WTI: ethmom3:up with the ETH market of the same close)
sw = specs["SH4_06_WTI"]["spec"]; shw = specs["SH4_06_WTI"]["spec_sha256"]
bw = sw["entry"]["seconds_left"]; cw = start + 6 * 86400 + 3600
fnd = None
for cents in range(5, 95):
    yb2, ya2 = (cents - 1) / 100.0, cents / 100.0
    if N.entries([(cw - bw, yb2, ya2, None, 1, 1)], cw, bw, sw["entry"]["price_band_5c"], sw["entry"]["side_rule"], None, None)[0] is not None: fnd = (yb2, ya2); break
wti = {"series": "KXWTI15M", "ticker": "KXWTI15M-T1", "close": cw, "result": "yes", "candles": [(cw - bw, fnd[0], fnd[1], None, 1, 1), (cw, 0.99, 1.0, None, 1, 1)]}
def eth(m0, m1, present=True):
    cs = [(cw - bw - 180, m0 - .01, m0 + .01, 0, 0, 0), (cw - bw, m1 - .01, m1 + .01, 0, 0, 0)] if present else []
    return {"KXETH15M": {cw: {"series": "KXETH15M", "ticker": "KXETH15M-T1", "close": cw, "result": "yes", "candles": cs}}}
g = ["KXWTI15M", "KXETH15M"]
out["eth_up_trades"] = len(V.score_spec_v4(mods, sw, [wti], eth(.50, .60), start, ok_guard, g, shw)[0])
out["eth_down_trades"] = len(V.score_spec_v4(mods, sw, [wti], eth(.60, .50), start, ok_guard, g, shw)[0])
out["eth_missing_trades"] = len(V.score_spec_v4(mods, sw, [wti], eth(.5, .6, False), start, ok_guard, g, shw)[0])
out["eth_absent_trades"] = len(V.score_spec_v4(mods, sw, [wti], {}, start, ok_guard, g, shw)[0])
out["eth_held_trades"] = len(V.score_spec_v4(mods, sw, [wti], eth(.50, .60), start, lambda i, t, c: (False, "held") if t.startswith("KXETH") else (True, "clear"), g, shw)[0])

# 4. the two Bitcoin picks start later than the config start
btc = specs["SH4_01_BTC"]["spec"]
out["btc_start"] = V.spec_start(btc, start); out["other_start"] = V.spec_start(sp, start)
out["cache_key"] = V.cache_key(root)

# 5. V2 (btcmom3: the Bitcoin market of the same close) and V3 (swid, and the vspike picks that are excluded until their cuts are pinned)
cfg2 = V.load_config(root, "V2"); lst2, mods2, _t, _h, _c = V.verified_inputs(root, cfg2)
fx2 = json.load(open(os.path.join(W, "BTCMOM3_RUNNER_FIXTURE_NOV16.json")))
bad2 = []
for c in fx2["cases"]:
    ee = c["e"]; idx = {}
    for key, off in (("btc_candle_e_minus_180", -180), ("btc_candle_e", 0)):
        k_ = c.get(key)
        if k_ is not None: idx[ee + off] = (k_["end"], k_["yes_bid"], k_["yes_ask"], 0, 0, 0)
    k = V.feature_class(mods2, "btcmom3", {"close": c["close"], "candles": [], "series": c["market"]}, idx, ee)
    if (k or "missing") != c["expected_class"]: bad2.append([c.get("constructed"), k, c["expected_class"]])
    xv = mods2["engine1_batchc"].xmom(idx, ee)
    if (c["expected_x"] is None) != (xv is None) or (xv is not None and abs(xv - c["expected_x"]) > 1e-12): bad2.append(["x", c.get("constructed"), xv, c["expected_x"]])
out["btcmom3_fixture_cases"] = len(fx2["cases"]); out["btcmom3_fixture_bad"] = bad2
sp2 = next(i for i in lst2["specs"] if i["spec"]["id"] == "SH2_02_ETH")
spec2, sha2 = sp2["spec"], sp2["spec_sha256"]; b2 = spec2["entry"]["seconds_left"]; c2 = cfg2["start_utc"] + 3 * 86400 + 3600
want = V.R.parse_filter(spec2["entry"]["filter"])[1]
fnd2 = None
for cents in range(5, 95):
    yb3, ya3 = (cents - 1) / 100.0, cents / 100.0
    if N.entries([(c2 - b2, yb3, ya3, None, 1, 1)], c2, b2, spec2["entry"]["price_band_5c"], spec2["entry"]["side_rule"], None, None)[0] is not None: fnd2 = (yb3, ya3); break
eth2 = {"series": "KXETH15M", "ticker": "KXETH15M-T9", "close": c2, "result": "yes", "candles": [(c2 - b2, fnd2[0], fnd2[1], None, 1, 1), (c2, 0.99, 1.0, None, 1, 1)]}
def btc(m0, m1): return {"KXBTC15M": {c2: {"series": "KXBTC15M", "ticker": "KXBTC15M-T9", "close": c2, "result": "yes", "candles": [(c2 - b2 - 180, m0 - .01, m0 + .01, 0, 0, 0), (c2 - b2, m1 - .01, m1 + .01, 0, 0, 0)]}}}
up_m, dn_m = (.50, .60), (.60, .50)
pair = up_m if want == "up" else dn_m; other = dn_m if want == "up" else up_m
out["v2_want"] = want
out["v2_match_trades"] = len(V.score_spec_v4(mods2, spec2, [eth2], btc(*pair), cfg2["start_utc"], ok_guard, ["KXETH15M", "KXBTC15M"], sha2)[0])
out["v2_other_class_trades"] = len(V.score_spec_v4(mods2, spec2, [eth2], btc(*other), cfg2["start_utc"], ok_guard, ["KXETH15M", "KXBTC15M"], sha2)[0])
out["v2_btc_absent_trades"] = len(V.score_spec_v4(mods2, spec2, [eth2], {}, cfg2["start_utc"], ok_guard, ["KXETH15M", "KXBTC15M"], sha2)[0])
out["v2_start"] = cfg2["start_utc"]
cfg3 = V.load_config(root, "V3"); lst3, mods3, _t3, _h3, _c3 = V.verified_inputs(root, cfg3)
out["v3_excluded"] = sorted(cfg3["excluded_picks"]); out["v3_vspike_ids"] = sorted(i["spec"]["id"] for i in lst3["specs"] if i["spec"]["entry"]["filter"].startswith("vspike"))
# a vspike pick that is not excluded and has no cuts refuses the whole list (no silent guess)
bad_cfg = json.loads(json.dumps(cfg3)); bad_cfg["excluded_picks"] = {}
try:
    V.verified_inputs(root, bad_cfg); out["v3_unexcluded_refused"] = False
except V.R.Refused:
    out["v3_unexcluded_refused"] = True
# swid: entry spread minus the spread 180 s earlier, sign class
B2 = mods3["engine1_batchb2"]
by = {10000 - 180: (10000 - 180, .50, .52, 0, 5, 0), 10000: (10000, .50, .54, 0, 5, 0)}
out["swid_up"] = B2.swid(by, 10000); by2 = {10000 - 180: (10000 - 180, .50, .52, 0, 5, 0)}; out["swid_missing"] = B2.swid(by2, 10000)
sw = next(i for i in lst3["specs"] if i["spec"]["entry"]["filter"].startswith("swid"))
out["v3_swid_pick"] = sw["spec"]["id"]
print(json.dumps(out))
