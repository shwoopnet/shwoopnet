#!/usr/bin/env python3
"""Hand case of build_ladhour1_results_job.py on INVENTED rows (EXPECTED_ladhour1_nov16.md)."""
import os, sys, collections, calendar, time
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ladhour1_load as L, build_ladhour1_results_job as G
L.START = calendar.timegm(time.strptime("2026-11-20", "%Y-%m-%d")); L.CUT = L.START + 86400
class BT(dict):
    def __getitem__(self, k):
        if k != "ticker": raise AssertionError("read %r on a wrong-series row" % (k,))
        return super().__getitem__(k)
ct = "2026-11-20T14:00:00Z"
rows = [{"ticker": "KXWTIH-N%03d" % i, "close_time": ct} for i in range(250)] + [{"ticker": "KXWTIH-N000", "close_time": ct}] * 4
rows += [BT(ticker="KXINXU-X1")] * 3 + [{"ticker": "KXWTIH-O1", "close_time": "2026-11-21T00:00:00Z"}, {"ticker": "KXWTIH-O2", "close_time": "2026-11-19T23:00:00Z"}, {"ticker": "KXWTIH-U1", "close_time": "bad"}]
cnt = collections.Counter(); keep = set(); G.collect(rows, "KXWTIH", cnt, keep); j = G.job("KXWTIH", keep)
ok = [("1 kept 250, duplicates once", len(keep) == 250),
      ("2 counts", cnt["ticker outside the wall (dropped)"] == 3 and cnt["close_time outside the window (dropped)"] == 2 and cnt["close_time unreadable (dropped)"] == 1),
      ("3 requests 100, 100, 50 and max_requests 15 (requests + 12)", [len(r["params"]["tickers"].split(",")) for r in j["requests"]] == [100, 100, 50] and j["max_requests"] == 15),
      ("4 only tickers and limit, allowlist equals kept, one series", set(j["ticker_allowlist"]) == keep and all(set(r["params"]) == {"tickers", "limit"} for r in j["requests"]) and j["series_allowlist"] == ["KXWTIH"] and j["job_id"] == "LADHOUR1_RESULTS_KXWTIH")]
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
