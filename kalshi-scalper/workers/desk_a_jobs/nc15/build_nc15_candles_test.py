"""build_nc15_candles test, written BEFORE the builder (Auditor B's process note), on INVENTED lists. python3 -I build_nc15_candles_test.py"""
import sys, os, json, gzip, hashlib, tempfile, calendar, time, io, contextlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, ".."))
sys.path.insert(0, os.path.join(here, "..", "..", "desk_a_verify"))
import build_nc15_candles as C
def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def folder(d, name, body, extra=None):
    p = os.path.join(d, name); os.makedirs(p); raw = json.dumps(body).encode()
    with gzip.open(p + "/0001.json.gz", "wb") as f: f.write(raw)
    json.dump({"job": {"job_id": "NC15_LISTS", "requests": [{"id": "r1"}]}, "status": "complete", "rows": [{"index": 1, "id": "r1", "page": 1, "status": 200, "bytes": len(raw), "file": "0001.json.gz", "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False, "body_kind": "object"}]}, open(p + "/manifest.json", "w")); return p
S = C.SERIES; n_series = len(S)
def mk(series, close, result="yes"): return {"ticker": "%s-%s" % (series, iso(close)), "close_time": iso(close), "result": result, "yes_bid_dollars": "0.5", "volume_fp": "9"}
markets = []
day0 = ts("2026-11-09T00:00:00Z")
# 2 full days of 96 closes for every series (192 closes x 11 = 2,112 markets): the base case
for k in range(1, 193):
    for s in S: markets.append(mk(s, day0 + 900 * k))
# EVENT830 cut: its 8 series at the 13:30Z closes on 2026-11-10 and 2026-11-12 are dropped +-5 minutes; the other 3 series are kept
cut1 = ts("2026-11-10T13:30:00Z")
# a close ABOVE the end date and an unknown series must be ignored; a market with no close_time is counted
markets.append(mk("KXSILVER15M", C.END + 900)); markets.append(mk("KXFOO15M", day0 + 900 * 5)); markets.append({"ticker": "KXSILVER15M-NOCLOSE"})
d = tempfile.mkdtemp(); lists = folder(d, "lists", {"markets": markets})
plan = C.plan(lists)
# 1. the cut: the 8 EVENT830 series have no ticker closing within 5 minutes of 13:30Z on a calendar date; the other 3 keep theirs
ev = set(C.EVENT830_SERIES); assert len(ev) == 8 and ev <= set(S)
for t, c in plan["closes"].items():
    s = t.split("-")[0]
    if s in ev: assert all(abs(c - ts(x + "T13:30:00Z")) > 300 for x in C.EVENT830_DATES), (t, iso(c))
assert any(c == cut1 for t, c in plan["closes"].items() if t.split("-")[0] not in ev), "a non-EVENT830 series must keep its 13:30Z close"
assert C.EVENT830_DATES == ["2026-11-05", "2026-11-06", "2026-11-10", "2026-11-12", "2026-11-13"], C.EVENT830_DATES      # the five calendar dates up to the end date (Nov 13 included)
assert plan["dropped_event830"] == 8, plan["dropped_event830"]           # one close (Nov 10 13:30Z) x 8 series in this invented set (Nov 12 is not in it)
# 2. ignored: after the end date, unknown series, no close_time (counted)
assert plan["ignored_after_end"] == 1 and plan["ignored_unknown_series"] == 1 and plan["ignored_no_close"] == 1, plan
# 3. hourly grouping: every request holds the closes of ONE hour block (closes in (H, H+3600]), one ticker per series per close, at most 44 tickers
jobs = C.build_jobs(plan)      # the default file size: cap <= 470 (the runner stops a run at 40 minutes, about 480 requests at 5 s; the Head, Nov 14)
assert C.MAX_PER_FILE == 420 and C.MAX_PER_FILE + C.RETRY_SLACK == 432      # 420 requests is 35 minutes at 5 s, leaving room under the runner's 40 minute stop for 12 retries with doubling pauses (Auditor B)
reqs = [r for j in jobs for r in j["requests"]]
assert all(len(r["params"]["market_tickers"].split(",")) <= 44 for r in reqs) and all(r["params"]["period_interval"] == 1 for r in reqs)
for r in reqs:
    tk = r["params"]["market_tickers"].split(","); cl = [plan["closes"][t] for t in tk]
    assert r["params"]["start_ts"] == min(cl) - 900 and r["params"]["end_ts"] == max(cl) and max(cl) - min(cl) <= 2700 and len({(c - 1) // 3600 for c in cl}) == 1, r
assert sorted(t for r in reqs for t in r["params"]["market_tickers"].split(",")) == sorted(plan["closes"]), "every kept ticker in exactly one request"
# 4. file limits and caps: at most 420 requests a file, cap = requests + 12 (the runner counts every request SENT, retries included), cap <= 432, ids unique, allowlist = the tickers
for j in jobs:
    assert len(j["requests"]) <= 420 and j["max_requests"] == len(j["requests"]) + 12 <= 432, (len(j["requests"]), j["max_requests"])
    allt = {t for r in j["requests"] for t in r["params"]["market_tickers"].split(",")}
    assert set(j["ticker_allowlist"]) == allt and j["pacing_seconds"] == 5.0 and j["owner"] == "DESK_A"
assert len({r["id"] for r in reqs}) == len(reqs) and len({j["job_id"] for j in jobs}) == len(jobs)
assert max(r["params"]["end_ts"] for r in reqs) <= C.END
# 5. the standing reader rule is in every job's notes
assert all("drop any candle ending after its market's close" in j["notes"] for j in jobs)
# 6. a small max_per_file splits into several files, none over the limit
small = C.build_jobs(plan, max_per_file=10); assert len(small) > 1 and all(len(j["requests"]) <= 10 for j in small) and sum(len(j["requests"]) for j in small) == len(reqs)
# 7. totals for the Head: requests, files, and hours at 5 s
tot = C.totals(jobs); assert tot["requests"] == len(reqs) and tot["files"] == len(jobs) and abs(tot["hours_at_5s"] - 5 * len(reqs) / 3600) < 1e-9
# 8. the builder reads only ticker and close_time: its source text names no result, price, size or volume key
src = open(os.path.join(here, "build_nc15_candles.py")).read().split("import sys", 1)[1]
for bad in ("yes_bid", "yes_ask", '"result"', "volume", "price", "open_interest"): assert bad not in src, bad
# 9. an incomplete or tampered lists run is refused before anything is built
dd = tempfile.mkdtemp(); bad = folder(dd, "bad", {"markets": markets}); m = json.load(open(bad + "/manifest.json")); m["status"] = "stopped_429"; json.dump(m, open(bad + "/manifest.json", "w"))
try: C.plan(bad); raise AssertionError("an incomplete lists run was accepted")
except SystemExit: pass
print("BUILD_NC15_CANDLES TEST OK (EVENT830 cut on 5 dates, hourly grouping, 44 tickers max, caps, standing reader rule, totals, reads only ticker and close_time)")
