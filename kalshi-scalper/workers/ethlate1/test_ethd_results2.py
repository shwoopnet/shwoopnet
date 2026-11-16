#!/usr/bin/env python3
"""Hand case of build_ethd_results2_job.py on INVENTED rows (EXPECTED_ethd_results2_nov16.md)."""
import os, sys, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import build_ethd_results2_job as G
class BT(dict):
    def __getitem__(self, k):
        if k != "ticker": raise AssertionError("read %r on a wrong-series row" % (k,))
        return super().__getitem__(k)
rows = [{"ticker": "KXETHD-A1", "close_time": "2026-10-28T00:00:00Z"}, {"ticker": "KXETHD-A1", "close_time": "2026-10-28T00:00:00Z"}, {"ticker": "KXETHD-A2", "close_time": "2026-11-15T23:00:00Z"},
        {"ticker": "KXETHD-A3", "close_time": "2026-11-16T00:00:00Z"}, {"ticker": "KXETHD-A4", "close_time": "2026-10-27T23:00:00Z"}, BT(ticker="KXBTCD-B1", close_time="x"), {"ticker": "KXETHD-A5", "close_time": "garbage"}]
rows += [{"ticker": "KXETHD-N%03d" % i, "close_time": "2026-11-01T14:00:00Z"} for i in range(250)]
cnt = collections.Counter(); keep = set(); G.collect(rows, cnt, keep); j = G.job(keep)
ok = [("1 kept 252", len(keep) == 252 and "KXETHD-A1" in keep and "KXETHD-A2" in keep and "KXETHD-A3" not in keep),
      ("2 counts", cnt["ticker outside the wall (dropped)"] == 1 and cnt["close_time outside the window (dropped)"] == 2 and cnt["close_time unreadable (dropped)"] == 1),
      ("3 three requests of 100, 100, 52 and max_requests 15", [len(r["params"]["tickers"].split(",")) for r in j["requests"]] == [100, 100, 52] and j["max_requests"] == 15),
      ("4 requests carry only tickers and limit (no status, date, price or outcome), allowlist equals the kept set", set(j["ticker_allowlist"]) == keep and all(set(r["params"]) == {"tickers", "limit"} for r in j["requests"]) and j["series_allowlist"] == ["KXETHD"])]
for k, v in ok: print("PASS" if v else "FAIL", k)
sys.exit(0 if all(v for _, v in ok) else 1)
