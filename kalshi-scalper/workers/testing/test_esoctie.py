"""Synthetic tests of esoctie.py (Testing Desk build). No Kalshi data. Optional cross-check against the History Miner's reference: ESOCTIE_REF=<folder with its esoctie.py and scorekit.py> python3 test_esoctie.py"""
import calendar, gzip, json, os, random, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import esoctie as E
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts")); import kalshi_pull as kp

spec = E.load_cells()
def folder(bodies):
    d = tempfile.mkdtemp(); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d
MON = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
def key(ts):
    from zoneinfo import ZoneInfo; from datetime import datetime, timezone
    l = datetime.fromtimestamp(ts, ZoneInfo("America/New_York")); return "%02d%s%02d%02d%02d" % (l.year % 100, MON[l.month - 1], l.day, l.hour, l.minute)
def iso(ts): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
assert E.start_ts("KXESOCCERGAME-26NOV091943AAABBB") == calendar.timegm((2026, 11, 10, 0, 43, 0)) and E.start_ts("KXESOCCERGAME-26OCT101943AB") == calendar.timegm((2026, 10, 10, 23, 43, 0))
assert E.fee_up(0.25) == 0.02 and E.fee_up(0.10) == 0.01 and E.fee_up(0.5) == 0.02

def fixture(n=1400, ask_fn=lambda i: 0.12 if i % 20 == 0 else 0.27, tie_p=0.25, seed=1, open_before=3600, S0=calendar.timegm((2026, 9, 13, 12, 0, 0)), tie_res=None, extra_held=True):
    random.seed(seed); mk, cd = [], []
    for i in range(n):
        S = S0 + i * 600; ev = "KXESOCCERGAME-%sP%04d" % (key(S), i); tie = (tie_res(i) if tie_res else random.random() < tie_p); close = S + 720
        for suf, res in (("TIE", "yes" if tie else "no"), ("AAA", "no"), ("BBB", "no")):
            mk.append({"ticker": "%s-%s" % (ev, suf), "event_ticker": ev, "close_time": iso(close), "open_time": iso(S - open_before), "result": res})
        ask = ask_fn(i)
        cd.append({"market_ticker": ev + "-TIE", "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % (ask - 0.02)}, "yes_ask": {"close_dollars": "%.2f" % ask}}]})
        for suf, m in (("AAA", 0.5), ("BBB", 0.3)):
            cd.append({"market_ticker": ev + "-" + suf, "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % (m - .01)}, "yes_ask": {"close_dollars": "%.2f" % (m + .01)}}]})
    if extra_held:
        Sh = calendar.timegm((2026, 10, 25, 12, 0, 0)); evh = "KXESOCCERGAME-%sHOLD" % key(Sh)
        for suf in ("TIE", "AAA", "BBB"): mk.append({"ticker": "%s-%s" % (evh, suf), "event_ticker": evh, "close_time": iso(Sh + 720), "open_time": iso(Sh - 3600), "result": "yes"})
    return folder([{"markets": mk}]), folder([{"markets": cd}])

L, C = fixture()
rep, rows = E.measure(spec, [L], [C]); cf = rep["counts_first"]
assert cf["held_out_refused"] == 1 and cf["filled"] == 1400 and cf["base_building"] >= 300 and cf["not_filled"] == 0, cf
assert rep["rule_may_be_scored"], rep["kill"]
for r in rows:                                                    # walk-forward: only results public at the decision (close + 300 s <= decision candle end)
    if r["b"] is not None: assert r["n_base"] <= sum(1 for x in rows if x["close"] + 300 <= r["ts"])
res = E.score(spec, [L], [C])["rule"]
assert 40 <= res["bets"] <= 60 and "selected on development" in res["registered_verdict"] and res["wins"] <= res["bets"] and "haircut_line" in res, res["bets"]
# a bad open time drops the event (start not derivable), the close time never decides it
Lg, Cg = fixture(n=50, open_before=100 * 60 + 3600 * 5, extra_held=False); assert E.measure(spec, [Lg], [Cg])[0]["counts_first"]["start_not_derivable"] == 50
# kill lines: cheap tail, one-way cost, efficient
Lc, Cc = fixture(n=400, ask_fn=lambda i: 0.12, extra_held=False); r_ = E.measure(spec, [Lc], [Cc])[0]; assert any("cheap-tail" in x for x in r_["kill"]) and E.score(spec, [Lc], [Cc])["rule"].startswith("NOT SCORED")
Lw, Cw = fixture(n=400, ask_fn=lambda i: 0.27, extra_held=False)
mk_wide = fixture(n=400, ask_fn=lambda i: 0.40, extra_held=False)
# widen spread: ask - bid = 0.02 in the fixture; one-way = 0.01 + fee 0.02 = 3c (open), not closed
assert not any("CLOSED on cost" in x for x in E.measure(spec, [Lw], [Cw])[0]["kill"])
Lx, Cx = fixture(n=400, ask_fn=lambda i: 0.27, tie_p=0.25, extra_held=False)
# a result inside the 300 s settle gap cannot move a decision; one outside it can (NOTE 3)
def mini(close_y, flip):
    mk2, cd2 = [], []; S0b = calendar.timegm((2026, 9, 20, 12, 0, 0))
    for i in range(400):
        S = S0b + i * 1200; ev = "KXESOCCERGAME-%sQ%04d" % (key(S), i)
        for suf, res in (("TIE", "yes" if i % 4 == 0 else "no"), ("AAA", "no"), ("BBB", "no")): mk2.append({"ticker": "%s-%s" % (ev, suf), "event_ticker": ev, "close_time": iso(S + 720), "open_time": iso(S - 3600), "result": res})
        for suf, (b, a) in (("TIE", (.25, .27)), ("AAA", (.49, .51)), ("BBB", (.29, .31))): cd2.append({"market_ticker": "%s-%s" % (ev, suf), "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}}]})
    SX = S0b + 400 * 1200; evx = "KXESOCCERGAME-%sXXXX" % key(SX); SY = ((close_y - 720) // 60) * 60; evy = "KXESOCCERGAME-%sYYYY" % key(SY)
    for e, S, cl, res in ((evx, SX, SX + 720, "no"), (evy, SY, close_y, "yes" if flip else "no")):
        for suf in ("TIE", "AAA", "BBB"): mk2.append({"ticker": "%s-%s" % (e, suf), "event_ticker": e, "close_time": iso(cl), "open_time": iso(S - 3600), "result": res if suf == "TIE" else "no"})
        for suf, (b, a) in (("TIE", (.25, .27)), ("AAA", (.49, .51)), ("BBB", (.29, .31))): cd2.append({"market_ticker": "%s-%s" % (e, suf), "candlesticks": [{"end_period_ts": S - 60, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}}]})
    return [r for r in E.measure(spec, [folder([{"markets": mk2}])], [folder([{"markets": cd2}])])[1] if r["event"] == evx][0]["b"]
SXd = calendar.timegm((2026, 9, 20, 12, 0, 0)) + 400 * 1200 - 60
for gap, same in ((180, True), (299, True), (300, False), (400, False)): assert (mini(SXd - gap, False) == mini(SXd - gap, True)) == same, gap
# a void fired bet is booked as a loss of the fee only and counted (NOTE 4): all results void for a set of fired bets
def tie_res(i): return "void" if i % 2 else (i % 4 == 0)
# (void results are strings other than yes/no: fixture writes "yes"/"no" only for bool, so patch below)
Lv, Cv = fixture(n=1400, extra_held=False)
mkv = json.load(gzip.open(os.path.join(Lv, "0001.json.gz")))
for m in mkv["markets"]:
    if m["ticker"].endswith("-TIE") and int(m["event_ticker"][-4:]) % 40 == 0: m["result"] = ""
gzip.open(os.path.join(Lv, "0001.json.gz"), "wt").write(json.dumps(mkv))
rv = E.score(spec, [Lv], [Cv])["rule"]; assert rv["void_bets_booked_as_fee_loss"] >= 1, rv.get("void_bets_booked_as_fee_loss")
# candle job
j, c = E.build_candles(spec, [L]); kp.check_job(j); assert j["requests"] and len(j["ticker_allowlist"]) == 3 * cf["kept"] and all(len(r["params"]["market_tickers"].split(",")) <= 100 for r in j["requests"])
# verdict wording
assert E.verdict(99, 3, [3, 3]).startswith("no evidence at n = 99") and E.verdict(100, 0.9, [2, 2]) == "FALSIFIED" and E.verdict(100, 1.6, [2, 1.2]).startswith("development bar met") and E.verdict(100, 1.2, [2, 1.2]).startswith("below the bar")

ref = os.environ.get("ESOCTIE_REF")
if ref:                                                           # cross-check: the History Miner's reference reader on the SAME input
    sys.path.insert(0, ref); import importlib.util
    sp = importlib.util.spec_from_file_location("esoctie_ref", os.path.join(ref, "esoctie.py")); R = importlib.util.module_from_spec(sp); sp.loader.exec_module(R)
    rr, rrows = R.measure([L], [C]); assert rr["filled"] == rep["counts_first"]["filled"] and rr["filled_eligible"] == rep["counts_first"]["filled_eligible"], (rr["filled"], rep["counts_first"])
    mine = {r["event"]: r["b"] for r in rows}; theirs = {r["event"]: r["b"] for r in rrows}; assert mine == theirs, "base rates differ"
    assert rr["share_gap10_spread4"] == rep["share_gap_10_spread4"] if False else abs((rr["share_gap10_spread4"] or 0) - (rep["share_gap10_spread4"] or 0)) < 1e-9
    assert abs(rr["median_one_way_entry_cost"] - rep["median_one_way_entry_cost"]) < 1e-3, (rr["median_one_way_entry_cost"], rep["median_one_way_entry_cost"])
    rs = R.score([L], [C])["rule"]; assert rs["n"] == res["bets"] and abs(rs["all"]["net"] - res["all"]["net"]) < 1e-3 and rs["all"]["pf"] == res["all"]["pf"], (rs["n"], res["bets"])
    jr = None
    print("cross-check against the reference: AGREE on filled, eligible, every base rate, shares, one-way cost, bets, net and PF")
print("esoctie synthetic tests passed")
