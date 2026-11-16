"""ENGINE1 held-out candle job generator (Desk A, Nov 16 2026). Makes the batched candle pull jobs from the LANDED ENGINE1_HELD_LISTS runs: ticker and close_time ONLY are read, a close outside its series' window (or in the EVENT830 cut) is dropped and counted before anything else (same walls as engine1_heldout_load.py), no result is opened.
REFUSES unless HELDOUT_PULL_RUNS.md carries a line with the mark "readable ONLY by Desk A's ENGINE1 held-out job generator", "engine1_heldout_make_candle_jobs.py", this file's own sha256 and every LISTS run named on the command line.
Per request: at most 44 tickers (sorted by close then ticker; all series mixed), start_ts = the earliest close of those tickers minus 21 minutes, end_ts = the LATEST close of those tickers (never later), period_interval 1. Jobs hold at most MAXREQ requests each (the runner stops a run at 40 minutes: 5 s pacing, about 480 requests), ids ENGINE1_HELD_CANDLES_01 and up.
  python3 -I engine1_heldout_make_candle_jobs.py <dir holding the pull run folders> <out dir> <LISTS run> [<LISTS run> ...]"""
import os, sys, json, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import engine1_heldout_load as L
MAXREQ = 440; PER_REQ = 44; LEAD = 21 * 60
MARK = "readable ONLY by Desk A's ENGINE1 held-out job generator"
def self_sha(): return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
def refuse_unless_allowed(runs):
    try: text = open(L.ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    for line in text.splitlines():
        ln = line.replace("\\", "/")
        if MARK in ln and "engine1_heldout_make_candle_jobs.py" in ln and self_sha() in ln and all(r in ln for r in runs): return
    raise SystemExit("REFUSED: no allow-list line names engine1_heldout_make_candle_jobs.py with this file's sha256 %s and the runs %s" % (self_sha(), runs))
def make(base, runs, check_allow=True):
    if check_allow: refuse_unless_allowed(runs)
    c = collections.Counter(); rows = {}
    for run in runs:
        for b in L.run_bodies(base, run):
            for m in (b["markets"] if isinstance(b, dict) and isinstance(b.get("markets"), list) else []):
                tk = m.get("ticker"); ct = m.get("close_time"); cl = L.iso(ct) if isinstance(ct, str) else None
                if not isinstance(tk, str) or cl is None: c["no ticker or close"] += 1; continue
                why = L.in_window(tk.split("-")[0], cl)
                if why: c["dropped: " + why] += 1; continue
                rows[tk] = cl
    order = sorted(rows.items(), key=lambda kv: (kv[1], kv[0])); reqs = []
    for k in range(0, len(order), PER_REQ):
        part = order[k:k + PER_REQ]; reqs.append((part[0][1], part[-1][1], [t for t, _ in part]))
    jobs = []
    for n in range(0, len(reqs), MAXREQ):
        part = reqs[n:n + MAXREQ]; jid = "ENGINE1_HELD_CANDLES_%02d" % (len(jobs) + 1)
        allow = sorted({t for _, _, ts in part for t in ts})
        jobs.append({"job_id": jid, "status": "active", "owner": "DESK_A", "registration": "kalshi-scalper/workers/ENGINE1_HELDOUT_READ_PLAN_NOV16.md",
            "purpose": "1 minute candles for the markets of ENGINE1's held-out read (closes %d to %d), batched at most 44 tickers a request, from the landed ENGINE1_HELD_LISTS runs only; each request runs from its earliest close minus 21 minutes to its latest close." % (part[0][0], part[-1][1]),
            "heldout": "Unread by ENGINE1, seen by earlier development cards. Closes outside each series' window (Auditor B, Nov 16: BTC, ETH, XRP, DOGE, GOLD before 2026-10-28T00:00Z; HYPE, SOL, NEAR, BNB, ZEC, WTI, SILVER before 2026-11-03T16:00Z; all from 2026-10-03T16:00Z) and WTI and Silver closes within 5 minutes of 13:30Z are never asked. The landed runs go into HELDOUT_PULL_RUNS.md (Main) and are readable only by the ENGINE1 held-out loader.",
            "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
            "series_allowlist": sorted(L.WINDOWS), "ticker_allowlist": allow, "max_requests": len(part) + 12,
            "requests": [{"id": "h%05d" % (n + i + 1), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(ts), "start_ts": lo - LEAD, "end_ts": hi, "period_interval": 1}} for i, (lo, hi, ts) in enumerate(part)],
            "notes": "Part %d, %d requests, cap %d (requests + 12 for retries). Pacing 5.0 s. Tickers and closes from the landed lists runs only. STANDING READER RULE: drop any candle ending after its market's close." % (len(jobs) + 1, len(part), len(part) + 12),
            "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0,
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}})
    return jobs, dict(c), len(rows)
if __name__ == "__main__":
    if len(sys.argv) < 4: sys.exit(__doc__)
    jobs, c, n = make(sys.argv[1], sys.argv[3:])
    for j in jobs: json.dump(j, open(os.path.join(sys.argv[2], j["job_id"] + ".json"), "w"), indent=1)
    print(json.dumps({"jobs": len(jobs), "markets": n, "dropped": c, "requests": sum(len(j["requests"]) for j in jobs), "generator_sha256": self_sha()}, indent=1))
