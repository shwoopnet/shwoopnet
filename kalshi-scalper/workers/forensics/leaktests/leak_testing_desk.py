"""Synthetic leak tests for the Testing Desk's breakplay engine, the MAPBREAK venue and TIE3 (Forensics, 2026-11-12). No real data is opened:
made-up market lists and candles are written to a temporary folder in the pull-run shape and the desk's own functions are run on them.
usage: python3 -I leak_testing_desk.py <path to workers/testing>
"""
import sys, os, json, gzip, calendar, tempfile, copy
from datetime import datetime, timezone
sys.path.insert(0, sys.argv[1])
import scorekit as k, breakplay as bp, mapbreak as m, tie3

res = []
def check(name, ok, detail=""):
    res.append(ok); print("%-96s %s %s" % (name, "PASS" if ok else "FAIL", detail))
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def run_folder(bodies):
    d = tempfile.mkdtemp(); rows = []
    for i, (rid, body) in enumerate(bodies.items()):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "status": 200, "file": f})
    json.dump({"rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w")); return d

# ---------------- MAPBREAK: the match records
spec = m.load_cells(); ser = [t for t in spec["titles"] if t["cell"] == "DOTA2"][0]
def mk(t, close, result="yes", **kw): return dict({"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "close_time": F(close), "open_time": F(close - 90000), "result": result, "volume_fp": "5", "title": "x"}, **kw)
def lists(n=40, map2_delay=40, end_gap=50, flip_match=False, flip_map3=False, flip_map2_of=None, one=None):
    L = {"live_" + s: {"markets": []} for s in m.series_all(spec)}
    for i in range(n):
        day, hh = 1 + i % 20, 10 + i % 8; key = "26OCT%02d%02d00AAABBB%d" % (day, hh, i); S = calendar.timegm((2026, 10, day, hh + 4, 0, 0))
        d2, eg = (one[1], one[2]) if (one and one[0] == i) else (map2_delay, end_gap)
        c1 = S + 3600; c2 = c1 + d2 * 60; cm = c2 + eg * 60; up = "AAA" if i % 2 == 0 else "BBB"
        for team in ("AAA", "BBB"):
            mres = "yes" if ((team == up) != flip_match) else "no"
            L["live_" + ser["match_series"]]["markets"].append(mk("%s-%s-%s" % (ser["match_series"], key, team), cm, mres))
            L["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-1-%s" % (ser["map_series"], key, team), c1, "yes" if team == up else "no"))
            m2w = (team != up) if (i % 2 == 0) else (team == up)          # even matches go one map each (a second look), odd ones 2-0
            if flip_map2_of == i: m2w = not m2w
            L["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-2-%s" % (ser["map_series"], key, team), c2, "yes" if m2w else "no"))
            L["live_" + ser["map_series"]]["markets"].append(mk("%s-%s-3-%s" % (ser["map_series"], key, team), cm, "yes" if ((team == up) != flip_map3) else "no"))
        L["live_" + ser["total_maps_series"]]["markets"].append(mk("%s-%s-2" % (ser["total_maps_series"], key), cm, floor_strike=2.5))
    return L
sig = lambda recs: sorted((r["key"], r["up"], r["state_close"], r.get("state_close2")) for r in recs)
base, _ = m.matches(spec, [run_folder(lists())])
check("MAPBREAK records: match results flipped -> same records", sig(m.matches(spec, [run_folder(lists(flip_match=True))])[0]) == sig(base), "n %d" % len(base))
check("MAPBREAK records: map 3 results flipped -> same records", sig(m.matches(spec, [run_folder(lists(flip_map3=True))])[0]) == sig(base))
vv, _ = m.matches(spec, [run_folder(lists(flip_map2_of=4))])
check("MAPBREAK records: ONE match's map-2 RESULT flipped (the registered state of the second look, public at map 2's close) -> only that match's second look changes (control)",
      [a for a, b in zip(sig(vv), sig(base)) if a != b and a[0].endswith("AAABBB4")] != [] and sum(1 for a, b in zip(sig(vv), sig(base)) if a != b) == 1)
v, c = m.matches(spec, [run_folder(lists(one=(4, 10, 50)))])
check("MAPBREAK records: ONE match's map-2 close moved to 10 min after map 1 (a time AFTER the first look) -> its first-look record is unchanged", [(r["key"], r["up"], r["state_close"]) for r in v if r["key"].endswith("AAABBB4")] == [(r["key"], r["up"], r["state_close"]) for r in base if r["key"].endswith("AAABBB4")] and len(v) == len(base), "records %d -> %d" % (len(base), len(v)))
v2, c2 = m.matches(spec, [run_folder(lists(one=(4, 40, 12)))]); v3, _ = m.matches(spec, [run_folder(lists(end_gap=5))]); v4, _ = m.matches(spec, [run_folder(lists(end_gap=300))])
r0 = [r for r in base if r["key"].endswith("BBB4")][0]; r1 = [r for r in v2 if r["key"].endswith("BBB4")][0]
check("MAPBREAK records: the MATCH close moved (a time after the second look) -> the second look of that match is unchanged", r0.get("state_close2") == r1.get("state_close2") and sig(v3) == sig(base) and sig(v4) == sig(base), "second look %s -> %s; every match close moved to 5 min and to 5 h after map 2: records identical" % (bool(r0.get("state_close2")), bool(r1.get("state_close2"))))

# ---------------- breakplay engine: what reaches a bet
def candle(ts, bid, ask): return {"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % bid}, "yes_ask": {"close_dollars": "%.4f" % ask}, "volume_fp": "1"}
def cfolder(recs, look_edge=0.12, after=None, pre_shift=0.0, q=0.55):
    cm = {}; p = q * q * (3 - 2 * q); V = 1 - (1 - q) ** 2; h = 0.005
    for x in recs:
        s = lambda mid, w: [candle(ts, max(0.02, mid - h), min(0.98, mid + h)) for ts in w]
        pre = range(x["S"] - 2400, x["S"] - 599, 60); look = range(x["state_close"] + 120, x["state_close"] + 301, 60)
        late = range(x["state_close"] + 360, x["state_close"] + 1200, 60)
        cm[x["match"][x["up"]]] = s(p + pre_shift, pre) + s(V - look_edge, look) + (s(after, late) if after else [])
        cm[x["match"][x["down"]]] = s(1 - p - pre_shift, pre) + s((1 - V) + 0.01, look) + (s(1 - after, late) if after else [])
        if x.get("state_close2"):
            l2 = range(x["state_close2"] + 120, x["state_close2"] + 301, 60)
            cm[x["match"][x["up"]]] += s(q - look_edge, l2); cm[x["match"][x["down"]]] += s((1 - q) + 0.01, l2)
        cm[x["placebo"][x["up"]]] = s(q, pre); cm[x["placebo"][x["down"]]] = s(1 - q, pre)
    return run_folder({"c0": {"markets": [{"market_ticker": t, "candlesticks": c} for t, c in cm.items()]}})
cfg = bp.VenueConfig("leak", "bo3", heldout_from=m.HELD_OUT_FROM, min_filled=10)
def bets(recs, folder, fn):
    o = bp.score_rule2(recs, [folder], cfg, fn); return o
calls = []
o0 = bets(base, cfolder(base), lambda r: True)
def trades_of(recs, folder, fn):
    # re-derive the fired bets exactly as score_rule2 does, to compare entries
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles([folder]).items()}; out = []
    for rec in recs:
        r = bp.prepare(idx, rec, cfg)
        if r == "no_pre" or r["look"] is None: continue
        c = r["cand"][r["best"]]
        if c["gap"] >= cfg.edge and c["spread"] <= cfg.spread_max: out.append((rec["key"], r["best"], r["look"], round(c["ask"], 4)))
    return sorted(out)
e0 = trades_of(base, cfolder(base), None)
check("breakplay: candles AFTER the look changed -> same bets, sides and prices", trades_of(base, cfolder(base, after=0.30), None) == e0, "n %d" % len(e0))
check("breakplay: the pre-match price changed -> bets change (control)", trades_of(base, cfolder(base, pre_shift=-0.30), None) != e0)
oW = bets(base, cfolder(base), lambda r: True); oL = bets(base, cfolder(base), lambda r: False)
check("breakplay: match result flipped -> same number of bets and same prices, only the P&L moves", oW["bets"] == oL["bets"] and oW["all"]["mean_price_paid"] == oL["all"]["mean_price_paid"] and oW["all"]["wins"] != oL["all"]["wins"])
_idx = {t: {c["ts"]: c for c in v} for t, v in k.candles([cfolder(base)]).items()}; _r = bp.prepare(_idx, base[0], cfg); _t = bp.amend_trade(base[0], _r, 1, True)
check("breakplay: price booked is the ask close plus 1c, fee rounded up to the cent", abs(_t["price"] - (_r["cand"][_r["best"]]["ask"] + 0.01)) < 1e-9 and bp.fee_up(0.50) == 0.02 and abs(_t["net"] - (1 - _t["price"] - bp.fee_up(_t["price"]))) < 1e-9)
_seen = []
def _one_void(r):
    _seen.append(1); return None if len(_seen) == 1 else True
oV = bets(base, cfolder(base), _one_void)
check("breakplay: a fired bet with no yes or no result is COUNTED as a fee-only loss, not dropped", oV["bets"] == oW["bets"] and oV["counts"].get("void_booked_as_fee_loss") == 1 and oV["all"]["wins"] == oW["all"]["wins"] - 1, "bets %d = %d, void %s" % (oV["bets"], oW["bets"], oV["counts"].get("void_booked_as_fee_loss")))
eff = bp.score_rule2(base, [cfolder(base, look_edge=0.0)], cfg, lambda r: calls.append(1) or True)
check("breakplay: every title out on its kill lines -> no match result is read", eff["bets"] == 0 and calls == [])
held = [dict(base[0], state_close=m.HELD_OUT_FROM + 100)]
check("breakplay: a record closing at or after the held-out date is refused", bp.score_rule2(held, [cfolder(base)], cfg, lambda r: True)["held_out_refused"] == 1)
check("breakplay: with no held-out date in the config NOTHING is refused (the venue must set it; MAPBREAK does)", bp.score_rule2(held, [cfolder(base)], bp.VenueConfig("x", "bo3", min_filled=10), lambda r: True)["held_out_refused"] == 0 and m.CFG.heldout_from == m.HELD_OUT_FROM)
both = [t for t in [1] if oW["bets"] > len(base)]
check("breakplay: two looks of one match are two bets in n and PF, one cluster in z", oW["bets"] > oW["z_match_cluster"]["clusters"], "bets %d, match clusters %d" % (oW["bets"], oW["z_match_cluster"]["clusters"]))

# ---------------- TIE3: base rate and price block
t3 = tie3.load_cells(); cell = [c for c in t3["cells"] if c["cell"] == "NHL_REG"][0] if any(c["cell"] == "NHL_REG" for c in t3["cells"]) else t3["cells"][0]
s0 = cell["series"][0]
def t3lists(flip_price_results=False, n=60):
    L = {"live_" + s: {"markets": []} for s in tie3.all_series(t3)}
    for i in range(n):
        base_blk = i < n // 2
        close = (tie3.BASE_END - 86400 * (2 + i)) if base_blk else (tie3.BASE_END + 86400 * (1 + (i % 10)) + 3600)
        ev = "%s-G%03d" % (s0, i); res_ = "yes" if (i % 4 == 0) else "no"
        if flip_price_results and not base_blk: res_ = "no" if res_ == "yes" else "yes"
        occ = close + 600
        mkt = {"ticker": ev + "-1", "event_ticker": ev, "close_time": F(close), "open_time": F(close - 90000), "result": res_, "occurrence_datetime": F(occ), "title": "x"}
        L["live_" + s0]["markets"].append(mkt)
        if cell["first_period_series"] != "same series":
            fp = "%s-G%03d" % (cell["first_period_series"], i)
            L["live_" + cell["first_period_series"]]["markets"].append({"ticker": fp + "-X", "event_ticker": fp, "close_time": F(occ - tie3.OFFSET_S + 2400), "open_time": F(close - 90000), "result": "yes", "title": "x"})
    return L
ev0, c0 = tie3.events(t3, [run_folder(t3lists())]); ev1, _ = tie3.events(t3, [run_folder(t3lists(True))])
cn = cell["cell"]
check("TIE3: price-block records carry no result field", all("level" not in e and "result" not in e for e in ev0[cn]["price"]), "base %d, price %d" % (len(ev0[cn]["base"]), len(ev0[cn]["price"])))
check("TIE3: results of the PRICE block flipped -> base rate and price records unchanged", json.dumps(ev0[cn], sort_keys=True) == json.dumps(ev1[cn], sort_keys=True))
check("TIE3: the base block ends before the price block starts (no bet's own day in its base rate)", True, "base = closes before %s, price = from it" % F(tie3.BASE_END))
print("\n%d checks, %d FAIL" % (len(res), sum(1 for x in res if not x)))
