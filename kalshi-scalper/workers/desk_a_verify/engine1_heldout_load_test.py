import os, sys, json, gzip, tempfile, time, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_heldout_load as L, engine1_heldout_make_candle_jobs as G
def put(base, run, bodies):
    d = os.path.join(base, *run.split("/")); os.makedirs(d, exist_ok=True); rows = []
    for i, b in enumerate(bodies):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"status": "complete", "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
D = 86400; base = tempfile.mkdtemp(); mk = []; cand = []
def mkt(series, cl, tag, res="yes"):
    tk = "%s-%s" % (series, tag); mk.append({"ticker": tk, "close_time": iso(cl), "result": res, "status": "settled"})
    cs = [{"end_period_ts": cl - 600, "yes_bid": {"close_dollars": "0.88"}, "yes_ask": {"close_dollars": "0.90"}, "price": {"close_dollars": "0.89"}, "volume_fp": "12.00", "open_interest_fp": "100.00"},
          {"end_period_ts": cl - 60, "yes_bid": {"close_dollars": "0.95"}, "yes_ask": {"close_dollars": "0.96"}, "price": {"close_dollars": ""}, "volume_fp": "3.00", "open_interest_fp": "104.00"},
          {"end_period_ts": cl + 60, "yes_bid": {"close_dollars": "0.99"}, "yes_ask": {"close_dollars": "1.00"}}]               # after the close: never kept
    cand.append({"market_ticker": tk, "candlesticks": cs}); return tk
day = calendar.timegm((2026, 10, 10, 0, 0, 0))
ok_a = mkt("KXBTC15M", day + 3600, "OKA"); ok_b = mkt("KXHYPE15M", day + 7200, "OKB", "no"); void = mkt("KXGOLD15M", day + 10800, "VOID", "")
early = mkt("KXBTC15M", L.HELD_FROM - 900, "EARLY")                             # before the held-out start
a_late = mkt("KXBTC15M", L.A_TO, "ALATE")                                       # exactly at the A end: excluded (to before)
b_ok = mkt("KXWTI15M", L.A_TO + D, "WTIOK")                                     # group B runs to Nov 3 16:00
b_late = mkt("KXHYPE15M", L.B_TO, "BLATE"); other = mkt("KXFOO15M", day + 3600, "OTHER")
ev = mkt("KXWTI15M", day + 13 * 3600 + 30 * 60, "EV830"); ev2 = mkt("KXSILVER15M", day + 13 * 3600 + 34 * 60, "EVEDGE"); ev3 = mkt("KXSILVER15M", day + 13 * 3600 + 36 * 60, "EVOUT"); evb = mkt("KXBTC15M", day + 13 * 3600 + 30 * 60, "BTC1330")
put(base, "ENGINE1_HELD_LISTS_A/x1", [{"markets": mk[:6]}, {"markets": mk[6:]}]); put(base, "ENGINE1_HELD_CANDLES_01/x1", [{"markets": cand[:5]}, {"markets": cand[5:]}])
out, c = L.load(base, (["ENGINE1_HELD_LISTS_A/x1"], ["ENGINE1_HELD_CANDLES_01/x1"]))
tks = sorted(m["ticker"] for v in out.values() for m in v)
assert tks == sorted(["KXBTC15M-OKA", "KXHYPE15M-OKB", "KXGOLD15M-VOID", "KXWTI15M-WTIOK", "KXSILVER15M-EVOUT", "KXBTC15M-BTC1330"]), tks      # windows, EVENT830 cut (only WTI and Silver within 5 minutes), no other series
assert c["dropped: close outside the series window"] == 3 and c["dropped: series not in the plan"] == 1 and c["dropped: EVENT830 cut (13:30Z, WTI and Silver)"] == 2, c
v = [m for m in out["KXGOLD15M"]][0]; assert v["result"] == "void" and c["result not yes or no (kept as void)"] == 1                              # a result that is not yes or no is kept as void
m = out["KXBTC15M"][0]; assert m["candles"][0] == (m["close"] - 600, 0.88, 0.90, 0.89, 12.0, 100.0) and m["candles"][1][3] is None and m["candles"][1][5] == 104.0 and len(m["candles"]) == 2, m["candles"]
assert c["candle after close (dropped)"] == 6 and c.get("candle market not kept (not parsed)", 0) == 6, c          # 6 kept markets' after-close candles dropped; 6 unkept markets never parsed
assert L.N_FLOOR["KXBTC15M"] == 74 and L.N_FLOOR["KXWTI15M"] == 90
try: L.load(base); raise AssertionError("loaded without an allow line")
except SystemExit as e: assert "REFUSED" in str(e)
# generator: windows and cut before anything else, hour blocks sorted by close, at most 44 tickers, start = earliest close - 21 min, end = the LATEST close
jobs, gc, n = G.make(base, ["ENGINE1_HELD_LISTS_A/x1"], check_allow=False)
assert n == 6 and len(jobs) == 1 and len(jobs[0]["requests"]) == 1, (n, len(jobs))
r = jobs[0]["requests"][0]["params"]; cls = sorted(m["close"] for v in out.values() for m in v)
assert r["start_ts"] == cls[0] - 21 * 60 and r["end_ts"] == cls[-1] and r["period_interval"] == 1 and len(r["market_tickers"].split(",")) == 6
old = G.PER_REQ; G.PER_REQ = 2; j2, _, _ = G.make(base, ["ENGINE1_HELD_LISTS_A/x1"], check_allow=False); G.PER_REQ = old
spans = [(q["params"]["start_ts"], q["params"]["end_ts"]) for q in j2[0]["requests"]]; assert len(spans) == 3 and all(len(q["params"]["market_tickers"].split(",")) <= 2 for q in j2[0]["requests"])
assert all(hi <= max(cls) and lo >= min(cls) - 21 * 60 for lo, hi in spans) and all(q["params"]["end_ts"] == max(L.iso(mk_["close_time"]) for mk_ in mk if mk_["ticker"] in q["params"]["market_tickers"].split(",")) for q in j2[0]["requests"])
old = G.MAXREQ; G.PER_REQ = 1; G.MAXREQ = 4; j3, _, _ = G.make(base, ["ENGINE1_HELD_LISTS_A/x1"], check_allow=False); G.MAXREQ = old; G.PER_REQ = old if False else 44
assert [j["job_id"] for j in j3] == ["ENGINE1_HELD_CANDLES_01", "ENGINE1_HELD_CANDLES_02"] and [len(j["requests"]) for j in j3] == [4, 2]
try: G.make(base, ["ENGINE1_HELD_LISTS_A/x1"]); raise AssertionError("generated without an allow line")
except SystemExit as e: assert "REFUSED" in str(e)
json.dump(jobs[0], open(os.path.join(base, "ENGINE1_HELD_CANDLES_01.json"), "w"))

# partial A1 run (Nov 16): h00048 unanswered with 400 is accepted ONLY for ENGINE1_HELD_CANDLES_A1; any other failure or any other run refuses
def putp(base, run, rows_status, st):
    d = os.path.join(base, *run.split("/")); os.makedirs(d, exist_ok=True); rows = []
    for i, (rid, stt) in enumerate(rows_status):
        r = {"id": rid, "status": stt}
        if stt == 200: fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps({"markets": []})); r["file"] = fn
        rows.append(r)
    json.dump({"status": st, "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
pb = tempfile.mkdtemp()
putp(pb, "ENGINE1_HELD_CANDLES_A1/p1", [("h00001", 200), ("h00048", 400), ("h00048", 400), ("h00048", 400)], "stopped_failures"); list(L.run_bodies(pb, "ENGINE1_HELD_CANDLES_A1/p1"))
for bad, nm in ((([("h00001", 200), ("h00049", 400)], "stopped_failures"), "ENGINE1_HELD_CANDLES_A1/p2"), (([("h00001", 200), ("h00048", 200)], "stopped_failures"), "ENGINE1_HELD_CANDLES_A1/p3"), (([("h00001", 200), ("h00048", 500)], "stopped_failures"), "ENGINE1_HELD_CANDLES_A1/p4"), (([("h00001", 200), ("h00048", 400)], "complete"), "ENGINE1_HELD_CANDLES_A1/p5"), (([("h00001", 200), ("h00048", 400)], "stopped_failures"), "ENGINE1_HELD_CANDLES_B1/p6")):
    putp(pb, nm, *bad)
    try: list(L.run_bodies(pb, nm)); raise AssertionError("accepted " + nm)
    except SystemExit: pass
print("ENGINE1 HELDOUT LOADER AND GENERATOR OK", base)
