#!/usr/bin/env python3
"""NC15 1 minute candle history: job builder (Idea Desk A, Nov 14, 2026, the Head's order). Offline, sends nothing, reads no price, size or result.
  python3 -I build_nc15_jobs.py lists  <out dir>                     writes NC15_LISTS.json (settled market lists per series, 10 day close ranges)
  python3 -I build_nc15_jobs.py probe  <git repo> <ref> <out dir>    writes NC15_PROBE.json: the hour (4 consecutive 15 minute closes) with the most recorded tickers on nc-data coverage files (columns close_time, series, ticker ONLY are read), as ONE batched request for the hour and ONE plain per-close request for its first close
Tickers are never typed: the probe's come from the NC15 recorder's coverage files, the candle jobs' (a later step, not here) come from the landed lists run. End date 2026-11-13T23:59Z; nothing later is asked."""
import sys, os, json, csv, gzip, io, subprocess, calendar, time, collections
SERIES = ["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M", "KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M"]
def ts(s): return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
LIST_START = ts("2026-06-01T00:00:00Z")      # before any of these series was listed (empty chunks cost one request each); the lists run answers the true start
END = ts("2026-11-13T23:59:00Z")             # nothing after this is asked (NC15DEPTH1's scoring window opens 2026-11-19T00:00Z)
CHUNK_S = 10 * 86400                          # 10 days x 96 windows = 960 markets, under the 1,000 limit of one page
REGISTRATION = "kalshi-scalper/workers/NC15_CANDLE_HISTORY_REGISTRATION.md"
HELDOUT = ("Development history, ending 2026-11-13T23:59:00Z; nothing after it is asked. NC15DEPTH1's pooled scoring window opens 2026-11-19T00:00Z, after this job's end. Many other cards hold out dates inside the range these series cover (per HELDOUT_REGISTRY.md, Auditor B's reading), so the landed runs WILL hold prices and results of those cards' held-out windows: the landed runs go into HELDOUT_PULL_RUNS.md (Main, in the landing PR); a reader may open them only through heldout_guard_v2 and must apply its own card's cutoff. Held-out guard copy HELDOUT_PULL_RUNS.md sha256 974f271366673c38f1a326335ed69db465aa2e15a327672b12a1e0f28640c126.")
STOP = {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}
def base(job_id, purpose, endpoints, tickers, max_requests, requests, notes):
    return {"job_id": job_id, "registration": REGISTRATION, "purpose": purpose, "heldout": HELDOUT, "allowed_endpoints": endpoints, "series_allowlist": list(SERIES), "ticker_allowlist": tickers,
            "max_requests": max_requests, "requests": requests, "notes": notes, "owner": "DESK_A", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 5.0, "status": "active", "stop_rules": STOP}
def chunks():
    out, lo = [], LIST_START
    while lo <= END:
        hi = min(lo + CHUNK_S - 1, END); out.append((lo, hi)); lo = hi + 1
    return out
def lists_job():
    ep = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "min_close_ts", "max_close_ts", "limit", "cursor"]}]
    reqs = []
    for s in SERIES:
        for i, (lo, hi) in enumerate(chunks(), 1):
            reqs.append({"id": "settled_%s_%02d" % (s, i), "path": "/markets", "params": {"series_ticker": s, "status": "settled", "min_close_ts": lo, "max_close_ts": hi, "limit": 1000}, "max_pages": 3})
    return base("NC15_LISTS", "Settled markets (tickers and close times; a reader never reads a result) of the 11 NC15 series from before their listing to 2026-11-13T23:59Z, in 10 day close ranges, as the input from which the hourly candle jobs are built.", ep, [], len(reqs), reqs,
                "%d series x %d ranges of 10 days (from %s). Pacing 5.0 s (12 requests a minute) on the Head's order of Nov 14, 2026. Candles are NOT requested here." % (len(SERIES), len(chunks()), "2026-06-01T00:00:00Z"))
def read_coverage(repo, ref):
    names = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", ref], capture_output=True, text=True, check=True).stdout.split()
    rows = {}
    for n in names:
        if n.startswith("nc15/") and n.endswith("/coverage.csv.gz"):
            raw = subprocess.run(["git", "-C", repo, "show", "%s:%s" % (ref, n)], capture_output=True, check=True).stdout
            for r in csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw)))):          # only these three columns are used
                if r.get("series") in SERIES and r.get("ticker") and r.get("close_time"): rows[r["ticker"]] = (ts(r["close_time"]), r["series"])
    return rows
def pick_hour(rows):
    """the 4 consecutive 15 minute closes with the most tickers; ties go to the earliest; closes on an hour boundary (minute 15, 30, 45, 00) start the quartet at :15"""
    by = collections.defaultdict(list)
    for t, (c, s) in rows.items(): by[c].append(t)
    best = None
    for c0 in sorted(by):
        if (c0 // 900) % 4 != 1: continue                  # first close of the quartet is at :15 of an hour
        quartet = [c0 + 900 * k for k in range(4)]
        n = sum(len(by.get(c, [])) for c in quartet)
        if all(c in by for c in quartet) and (best is None or n > best[0]): best = (n, quartet)
    if best is None: raise SystemExit("no complete hour on the coverage files")
    return best[1], {c: sorted(by[c]) for c in best[1]}
def probe_job(rows):
    quartet, bycl = pick_hour(rows)
    alltk = sorted(t for c in quartet for t in bycl[c]); first = quartet[0]
    ep = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    reqs = [{"id": "hour_batch", "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(alltk), "start_ts": first - 900, "end_ts": quartet[-1], "period_interval": 1}},
            {"id": "first_close_plain", "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(bycl[first]), "start_ts": first - 900, "end_ts": first, "period_interval": 1}}]
    return base("NC15_PROBE", "Two reads to learn the batch shape: the 1 minute candles of one hour (4 closes) for every recorded ticker in one batched request, and the first close's tickers alone as the plain request of the same window. Compared by shapes and timestamps only (does a ticker return only its own window, are minutes padded or missing); no price is read.", ep, alltk, 2, reqs,
                "Hour closes %s; %d tickers in the batch; tickers come from the NC15 recorder's coverage files (columns close_time, series and ticker only). Pacing 5.0 s." % (", ".join(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(c)) for c in quartet), len(alltk)))
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "lists": job, out = lists_job(), a[1]
    elif len(a) == 4 and a[0] == "probe": job, out = probe_job(read_coverage(a[1], a[2])), a[3]
    else: sys.exit(__doc__)
    os.makedirs(out, exist_ok=True); p = os.path.join(out, job["job_id"] + ".json")
    with open(p, "w") as f: json.dump(job, f, indent=1); f.write("\n")
    print("wrote", p, "| requests", len(job["requests"]))
