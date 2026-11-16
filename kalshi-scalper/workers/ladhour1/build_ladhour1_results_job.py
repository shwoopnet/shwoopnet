#!/usr/bin/env python3
"""LADHOUR1 settled-list job generator (Desk B, Nov 16 2026; DRAFT, unrun, unsigned). Reads ONLY ticker then close_time from quote-data's ladder.csv.gz files for ONE series and writes a kalshi-pull job asking for exactly those tickers.
The page cap is SIZED FROM THE DATA: requests = ceil(kept/100), max_requests = requests + 12; the run refuses (exit 1) on 0 tickers or more than 1,100 requests. Expected figures: EXPECTED_ladhour1_nov16.md.
Usage: build_ladhour1_results_job.py <SERIES> <quote-data checkout> [out.json]   (the window comes from ladhour1_load.START and CUT, written by Main)"""
import os, sys, json, gzip, csv, io, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ladhour1_load as L
MAX_REQ = 1100
def collect(rows, series, cnt, keep):
    for r in rows:
        tk = r["ticker"]
        if not tk.startswith(series + "-"): cnt["ticker outside the wall (dropped)"] += 1; continue      # ticker FIRST
        t = L.iso(r["close_time"]) if isinstance(r["close_time"], str) else None
        if t is None: cnt["close_time unreadable (dropped)"] += 1; continue
        if not (L.START <= t < L.CUT): cnt["close_time outside the window (dropped)"] += 1; continue
        keep.add(tk)
def job(series, keep):
    tks = sorted(keep); chunks = [tks[i:i + 100] for i in range(0, len(tks), 100)]
    req = [{"id": "tk_%04d" % i, "path": "/markets", "params": {"tickers": ",".join(c), "limit": 100}} for i, c in enumerate(chunks)]
    return {"job_id": "LADHOUR1_RESULTS_" + series, "owner": "DESK_B", "status": "active", "registration": "kalshi-scalper/workers/specs/LADHOUR1_CARD.md",
            "purpose": "Results of the %s hourly ladder strikes the recorder stored (tickers from quote-data, ticker and close_time only), to score LADHOUR1." % series,
            "heldout": "FIXED window: only strikes whose recorded close_time lies in [start_utc, read date) are asked for, by ticker; nothing later.",
            "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["tickers", "limit"]}],
            "series_allowlist": [series], "ticker_allowlist": tks, "max_requests": len(req) + 12,
            "notes": "%d tickers, %d requests of up to 100 tickers; page cap = requests + 12, sized from the data." % (len(tks), len(req)),
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause; three in a row end the run"},
            "requests": req}
def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    series = a[0]
    if series not in L.SERIES: raise SystemExit("REFUSED: %s is not one of %s" % (series, L.SERIES))
    L.check_window(); cnt = collections.Counter(); keep = set()
    for d in L.dirs():
        dp = os.path.join(a[1], "quotes", d)
        if not os.path.isdir(dp): cnt["missing date directory"] += 1; continue
        for run in sorted(os.listdir(dp)):
            p = os.path.join(dp, run, "ladder.csv.gz")
            if os.path.exists(p): collect(({"ticker": r["ticker"], "close_time": r["close_time"]} for r in csv.DictReader(io.TextIOWrapper(gzip.open(p), encoding="utf-8", newline=""))), series, cnt, keep)
    j = job(series, keep)
    if not keep or len(j["requests"]) > MAX_REQ: print("REFUSED: %d tickers, %d requests (limit %d)" % (len(keep), len(j["requests"]), MAX_REQ)); sys.exit(1)
    out = a[2] if len(a) > 2 else "LADHOUR1_RESULTS_%s.json" % series
    json.dump(j, open(out, "w"), indent=1)
    print("%s: tickers kept %d | requests %d | max_requests %d | drops %s | sha256 %s" % (series, len(keep), len(j["requests"]), j["max_requests"], dict(cnt), hashlib.sha256(open(out, "rb").read()).hexdigest()))
if __name__ == "__main__": main()
