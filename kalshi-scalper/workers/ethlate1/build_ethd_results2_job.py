#!/usr/bin/env python3
"""ETHD_RESULTS2 job generator (Desk B, Nov 16, 2026). Reads ONLY ticker then close_time from quote-data's ladder.csv.gz files (date directories 2026-10-27 to 2026-11-15) and writes a kalshi-pull job asking for exactly those KXETHD strikes by ticker.
No price, size, status, strike or outcome is parsed. Expected figures: EXPECTED_ethd_results2_nov16.md.   Usage: build_ethd_results2_job.py <quote-data checkout> [out.json]"""
import os, sys, csv, gzip, io, json, hashlib, calendar, time, collections
START = 1793145600; CUT = 1794787200          # 2026-10-28T00:00Z, 2026-11-16T00:00Z
DIRS = tuple("2026-10-%02d" % d for d in (27, 28, 29, 30, 31)) + tuple("2026-11-%02d" % d for d in range(1, 16))
def iso(s):
    try: return calendar.timegm(time.strptime(s.replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception: return None
def collect(rows, cnt, keep):
    for r in rows:
        tk = r["ticker"]
        if not tk.startswith("KXETHD-"): cnt["ticker outside the wall (dropped)"] += 1; continue      # ticker FIRST
        t = iso(r["close_time"]) if isinstance(r["close_time"], str) else None
        if t is None: cnt["close_time unreadable (dropped)"] += 1; continue
        if not (START <= t < CUT): cnt["close_time outside the window (dropped)"] += 1; continue
        keep.add(tk)
def job(keep):
    tks = sorted(keep); chunks = [tks[i:i + 100] for i in range(0, len(tks), 100)]
    req = [{"id": "tk_%04d" % i, "path": "/markets", "params": {"tickers": ",".join(c), "limit": 100}} for i, c in enumerate(chunks)]
    return {"job_id": "ETHD_RESULTS2", "owner": "DESK_B", "status": "active", "registration": "kalshi-scalper/workers/specs/ETHLATE1_CARD.md",
            "purpose": "Results of the hourly Ethereum ladder strikes the recorder stored (tickers from quote-data, ticker and close_time only), closes 2026-10-28 to 2026-11-15, to score ETHLATE1; replaces ETHD_RESULTS, which hit its page cap.",
            "heldout": "FIXED window: only strikes whose recorded close_time is from 2026-10-28T00:00:00Z to before 2026-11-16T00:00:00Z are asked for, by ticker; nothing from Nov 16 on. KXETHD has no row in HOLDS.json for these closes (Auditor B, Nov 16); the reader of this run is ETHLATE1's loader only.",
            "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["tickers", "limit"]}],
            "series_allowlist": ["KXETHD"], "ticker_allowlist": tks, "max_requests": len(req) + 12,
            "notes": "%d tickers, %d requests of up to 100 tickers; no status or date parameter (a settled market is returned by ticker)." % (len(tks), len(req)),
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": req}
def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    cnt = collections.Counter(); keep = set()
    for d in DIRS:
        dp = os.path.join(a[0], "quotes", d)
        if not os.path.isdir(dp): cnt["missing date directory"] += 1; continue
        for run in sorted(os.listdir(dp)):
            p = os.path.join(dp, run, "ladder.csv.gz")
            if os.path.exists(p):
                rows = ({"ticker": r["ticker"], "close_time": r["close_time"]} for r in csv.DictReader(io.TextIOWrapper(gzip.open(p), encoding="utf-8", newline="")))
                collect(rows, cnt, keep)
    j = job(keep); out = a[1] if len(a) > 1 else "ETHD_RESULTS2.json"
    json.dump(j, open(out, "w"), indent=1)
    print("tickers kept %d | requests %d | max_requests %d | drops %s | sha256 %s" % (len(keep), len(j["requests"]), j["max_requests"], dict(cnt), hashlib.sha256(open(out, "rb").read()).hexdigest()))
if __name__ == "__main__": main()
