import os, sys, json, gzip, tempfile, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import volfair1_load as L, volfair1_make_candle_jobs as G
def put(base, run, bodies):
    d = os.path.join(base, *run.split("/")); os.makedirs(d, exist_ok=True); rows = []
    for i, b in enumerate(bodies):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"status": "complete", "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
def iso(t):
    import time; return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
base = tempfile.mkdtemp(); mk = []; cand = []
C_VAL = L.DEV_TO + 3600 * 5; C_DEV = L.DEV_FROM + 3600 * 7; C_HELD = L.VAL_TO; C_THIN = L.DEV_TO + 3600 * 9; C_BEFORE = L.DEV_FROM - 3600
def event(cl, n, tag, nobid=False):
    for j in range(n):
        tk = "KXBTCD-%s-T%d" % (tag, j); strike = 100000.0 + 100 * j
        mk.append({"ticker": tk, "close_time": iso(cl), "floor_strike": strike, "result": "yes" if j % 2 else "no", "status": "settled"})
        mid = 0.05 + 0.1 * j if j < 10 else 0.95
        bid, ask = round(mid - 0.01, 2), round(mid + 0.01, 2)
        cs = [{"end_period_ts": cl - 55 * 60, "yes_bid": {"close_dollars": str(bid)}, "yes_ask": {"close_dollars": str(ask)}},
              {"end_period_ts": cl - 54 * 60, "yes_bid": {"close_dollars": "0.50"}, "yes_ask": {"close_dollars": "0.51"}},     # a later candle must never pick a strike
              {"end_period_ts": cl - 16 * 60, "yes_bid": {"close_dollars": "0.01"}, "yes_ask": {"close_dollars": "0.99"}},     # a -16 candle must never serve as the entry
              {"end_period_ts": cl - 15 * 60, "yes_bid": {"close_dollars": str(bid + .01)}, "yes_ask": {"close_dollars": str(ask + .01)}}]
        cand.append({"market_ticker": tk, "candlesticks": cs})
event(C_VAL, 10, "VAL"); event(C_DEV, 10, "DEV"); event(C_HELD, 10, "HELD"); event(C_THIN, 5, "THIN"); event(C_BEFORE, 10, "OLD")
put(base, "VOLFAIR1_LISTS/x1", [{"markets": mk[:25]}, {"markets": mk[25:]}]); put(base, "VOLFAIR1_CANDLES_01/x1", [{"markets": cand[:20]}, {"markets": cand[20:]}])
out, c = L.load(base, (["VOLFAIR1_LISTS/x1"], ["VOLFAIR1_CANDLES_01/x1"]))
assert [x["close"] for x in out] == [C_DEV, C_VAL] and [x["window"] for x in out] == ["development", "validation"], out
assert c["dropped: at or after 2026-09-21 (held thirds H18 and H19)"] == 10 and c["dropped: before 2026-06-01"] == 10, c      # the held close is dropped unparsed, counted
assert c["close with fewer than 7 strikes quoted at -55 (skipped)"] == 1, c                                                    # C_THIN has 5
v = out[1]["strikes"]; assert len(v) == 7
# strikes 0..9 have mids 0.05..0.95; nearest 0.50 are j=4 (0.45), 5 (0.55), 3 (0.35), 6 (0.65), 2 (0.25), 7 (0.75), 1 (0.15): the tie between j=4 and j=5 (both 0.05 away) goes to the LOWER strike first
assert [s["strike"] for s in v] == [100000 + 100 * j for j in (4, 5, 3, 6, 2, 7, 1)], [s["strike"] for s in v]
assert abs(v[0]["mid55"] - 0.45) < 1e-9 and abs(v[0]["bid15"] - 0.45) < 1e-9 and abs(v[0]["ask15"] - 0.47) < 1e-9 and v[0]["result"] in ("yes", "no")
assert c["candle at another time (discarded unread)"] > 0                                                                      # the -54 candles were never read
# the loader refuses without its allow line (the real HELDOUT_PULL_RUNS.md has none for this file)
try: L.load(base); raise AssertionError("loaded without an allow line")
except SystemExit as e: assert "REFUSED" in str(e)
# a run that is not complete is refused
d = os.path.join(base, "VOLFAIR1_LISTS", "x1", "manifest.json"); m = json.load(open(d)); m["status"] = "partial"; json.dump(m, open(d, "w"))
try: L.load(base, (["VOLFAIR1_LISTS/x1"], ["VOLFAIR1_CANDLES_01/x1"])); raise AssertionError("loaded a partial run")
except SystemExit as e: assert "not a complete run" in str(e)
m["status"] = "complete"; json.dump(m, open(d, "w"))
# the generator: ticker and close_time only, windows cut, one request per close at most 100 strikes, -56 to -14 minutes
jobs, gc, n = G.make(base, "VOLFAIR1_LISTS/x1", check_allow=False)
assert n == 3 and len(jobs) == 1 and len(jobs[0]["requests"]) == 3, (n, len(jobs))                                             # DEV, VAL, THIN; HELD and OLD dropped
for r in jobs[0]["requests"]:
    p = r["params"]; assert p["end_ts"] - p["start_ts"] == 41 * 60 and p["period_interval"] == 1 and len(p["market_tickers"].split(",")) <= 100
assert all(r["params"]["end_ts"] % 60 == 0 for j in jobs for r in j["requests"]); assert all(max(r["params"]["end_ts"] for r in j["requests"]) < L.VAL_TO for j in jobs) and "KXBTCD-HELD-T0" not in jobs[0]["ticker_allowlist"]
old = G.MAXREQ; G.MAXREQ = 2; j2, _, _ = G.make(base, "VOLFAIR1_LISTS/x1", check_allow=False); G.MAXREQ = old
assert [j["job_id"] for j in j2] == ["VOLFAIR1_CANDLES_01", "VOLFAIR1_CANDLES_02"] and [len(j["requests"]) for j in j2] == [2, 1]
try: G.make(base, "VOLFAIR1_LISTS/x1"); raise AssertionError("generated without an allow line")
except SystemExit as e: assert "REFUSED" in str(e)
json.dump(jobs[0], open(os.path.join(base, "VOLFAIR1_CANDLES_01.json"), "w"))
print("VOLFAIR1 LOADER AND GENERATOR OK", base)
