"""VOLFAIR1 candle job generator (Desk A, Nov 16 2026). Makes the batched-candle pull jobs from the LANDED VOLFAIR1_LISTS run: ticker and close_time ONLY are read (the same wall as volfair1_load.py: closes outside [2026-06-01, 2026-09-21) are dropped and counted, nothing at or after 1789948800 is ever asked), no result and no strike is opened.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark "readable ONLY by Desk A's VOLFAIR1 job generator", "volfair1_make_candle_jobs.py", this file's own sha256 and the LISTS run name.
Per close (one hourly event) one request per at most 100 strikes: GET /markets/candlesticks market_tickers=..., start_ts = close - 56 min, end_ts = close - 14 min, period_interval 1 (the loader opens only the candles ending exactly 55 and 15 minutes before the close). Jobs hold at most MAXREQ requests each (the runner stops a run at 40 minutes: 5 s pacing, about 480 requests), ids VOLFAIR1_CANDLES_01 and up.
  python3 -I volfair1_make_candle_jobs.py <dir holding the pull run folders> <the LISTS run, e.g. VOLFAIR1_LISTS/2026-11-17T0100Z_123> <out dir for the job JSON files>"""
import os, sys, json, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import volfair1_load as L
MAXREQ = 440; PER_REQ = 100
MARK = "readable ONLY by Desk A's VOLFAIR1 job generator"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed(run):
    try: text = open(L.ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        if MARK in line and "volfair1_make_candle_jobs.py" in line and self_sha() in line and run in line.replace("\\", "/"): return
    raise SystemExit("REFUSED: no allow-list line names volfair1_make_candle_jobs.py with this file's sha256 %s and the run %s" % (self_sha(), run))
def make(base, run, check_allow=True):
    if check_allow: refuse_unless_allowed(run)
    c = collections.Counter(); by = collections.defaultdict(list)
    for b in L.run_bodies(base, run):
        for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
            tk = m.get("ticker"); ct = m.get("close_time"); cl = L.iso(ct) if isinstance(ct, str) else None
            if not isinstance(tk, str) or tk.split("-")[0] != L.SERIES or cl is None: c["unknown series or no close"] += 1; continue
            if cl >= L.VAL_TO: c["dropped: at or after 2026-09-21"] += 1; continue
            if cl < L.DEV_FROM: c["dropped: before 2026-06-01"] += 1; continue
            by[cl].append(tk)
    reqs = []
    for cl in sorted(by):
        tks = sorted(set(by[cl]))
        for k in range(0, len(tks), PER_REQ):
            reqs.append((cl, tks[k:k + PER_REQ]))
    jobs = []
    for n in range(0, len(reqs), MAXREQ):
        part = reqs[n:n + MAXREQ]; jid = "VOLFAIR1_CANDLES_%02d" % (len(jobs) + 1)
        allow = sorted({t for _, ts in part for t in ts})
        jobs.append({"job_id": jid, "status": "active", "owner": "DESK_A", "registration": "kalshi-scalper/workers/VOLFAIR1_REGISTRATION_NOV16.md",
            "purpose": "1 minute candles from 56 to 14 minutes before each KXBTCD hourly close (closes %d to %d), batched at most 100 strikes a request, from the landed VOLFAIR1_LISTS run only. The reader opens only the candles ending 55 and 15 minutes before the close." % (part[0][0], part[-1][0]),
            "heldout": "Closes at or after 2026-09-21T00:00Z (1789948800) are never asked (EVM1's held-out third H18, HRSEAS1's W3 H19). Development closes before 2026-09-01 are labelled development. The landed runs go into HELDOUT_PULL_RUNS.md (Main) and are readable only by the VOLFAIR1 loader.",
            "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
            "series_allowlist": [L.SERIES], "ticker_allowlist": allow, "max_requests": len(part) + 12,
            "requests": [{"id": "c%05d" % (n + i + 1), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(ts), "start_ts": cl - 56 * 60, "end_ts": cl - 14 * 60, "period_interval": 1}} for i, (cl, ts) in enumerate(part)],
            "notes": "Part %d, %d requests, cap %d (requests + 12 for retries). Pacing 5.0 s. Tickers and closes from the landed VOLFAIR1_LISTS run only. STANDING READER RULE: drop any candle ending after its market's close." % (len(jobs) + 1, len(part), len(part) + 12),
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}})
    return jobs, dict(c), len(by)
if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    jobs, c, closes = make(sys.argv[1], sys.argv[2])
    for j in jobs: json.dump(j, open(os.path.join(sys.argv[3], j["job_id"] + ".json"), "w"), indent=1)
    print(json.dumps({"jobs": len(jobs), "closes": closes, "dropped": c, "requests": sum(len(j["requests"]) for j in jobs), "generator_sha256": self_sha()}, indent=1))
