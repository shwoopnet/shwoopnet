#!/usr/bin/env python3
"""WHEEL0 stage 2: builds the candle jobs from the stage 1 answers (WHEEL0_LISTS). Offline: it sends no request.
  python3 -I build_wheel0_candles.py <WHEEL0_LISTS run folder> <out dir>
Writes one job file a series (WHEEL0_CANDLES_XRP, _DOGE, _GOLD, _ETH) so no run comes near the runner's 200 MB cap.
Reads ONLY the ticker and the close time of each listed market. The result field is never read here, and no market is kept or dropped by its result.
Rules: closes from 2026-09-12T00:00Z to before 2026-11-13T00:00Z; Ethereum only before 2026-10-29T00:00Z (standing rule (h); a later Ethereum market is refused, not skipped);
1 minute candles; window = 900 s before the batch's first close to 120 s before its last close (the latest look is 180 s before a close, so the final minutes are not pulled);
batches packed so (window minutes x tickers) <= 9,000, the packing CFRTI_K_CANDLES proved. A folder under a HELDOUT_ name is refused."""
import gzip, json, os, sys, calendar, time, re
FROM = calendar.timegm(time.strptime("2026-09-12", "%Y-%m-%d"))
BEFORE = calendar.timegm(time.strptime("2026-11-13", "%Y-%m-%d"))
ETH_BEFORE = calendar.timegm(time.strptime("2026-10-29", "%Y-%m-%d"))
SERIES = {"KXXRP15M": ("XRP", BEFORE), "KXDOGE15M": ("DOGE", BEFORE), "KXGOLD15M": ("GOLD", BEFORE), "KXETH15M": ("ETH", ETH_BEFORE)}
LIMIT, LEAD_S, TAIL_S = 9000, 900, 120
REG = "kalshi-scalper/workers/forensics/wheel0/WHEEL0_REGISTRATION.md"


def refuse_heldout(path):
    if any(p.upper().startswith("HELDOUT_") for p in os.path.realpath(path).split(os.sep)) or any(p.upper().startswith("HELDOUT_") for p in os.path.abspath(path).split(os.sep)):
        raise SystemExit("refused: %s is a HELDOUT_ folder (standing rule (h))" % path)


def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None


def read_markets(folder):
    """-> {series: [(ticker, close)] in close order}, counts. Ticker and close time only."""
    refuse_heldout(folder)
    man = json.load(open(os.path.join(folder, "manifest.json"))); out = {s: {} for s in SERIES}; cnt = {"no_close_time": 0, "outside_dates": 0, "other_series": 0}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row or row.get("truncated"): continue
        body = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            if not isinstance(m, dict) or not m.get("ticker"): continue
            s = str(m["ticker"]).split("-")[0]
            if s not in SERIES: cnt["other_series"] += 1; continue
            c = iso_ts(m.get("close_time") or "")
            if c is None: cnt["no_close_time"] += 1; continue
            if s == "KXETH15M" and c >= ETH_BEFORE: raise SystemExit("refused: the lists hold an Ethereum market closing on or after 2026-10-29 (rule (h)); the list job is bounded, so this should not happen")
            if not (FROM <= c < SERIES[s][1]): cnt["outside_dates"] += 1; continue
            out[s][m["ticker"]] = c
    return {s: sorted(v.items(), key=lambda kv: (kv[1], kv[0])) for s, v in out.items()}, cnt


def pack(mk):
    reqs, cur = [], []
    def flush():
        reqs.append({"id": "b%04d" % len(reqs), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for t, _ in cur), "start_ts": cur[0][1] - LEAD_S, "end_ts": cur[-1][1] - TAIL_S, "period_interval": 1}})
    for t, c in mk:
        trial = cur + [(t, c)]
        if cur and ((trial[-1][1] - (trial[0][1] - LEAD_S)) / 60 * len(trial) > LIMIT or len(trial) > 100):
            flush(); cur = [(t, c)]
        else: cur = trial
    if cur: flush()
    return reqs


def job(series, mk):
    short, before = SERIES[series]; reqs = pack(mk)
    return {"job_id": "WHEEL0_CANDLES_" + short, "owner": "MAIN", "registration": REG,
            "purpose": "WHEEL0 stage 2 (the owner's ordered premise test of the rotation lane): 1 minute candles of the settled %s markets closing 2026-09-12 to before %s, from 15 minutes before each batch's first close to 2 minutes before its last." % (series, time.strftime("%Y-%m-%d", time.gmtime(before))),
            "heldout": "WHEEL0 has no held-out block (one read, 1 try). Rule (h): %s" % ("no Ethereum market closing on or after 2026-10-29T00:00Z is in the allowlist." if series == "KXETH15M" else "this series is held out by no card (Head of R&D, 2026-11-12 19:53Z)."),
            "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
            "series_allowlist": [series], "ticker_allowlist": sorted(t for t, _ in mk), "max_requests": len(reqs), "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
            "notes": "Written by the Forensics desk for the Head of R&D's order; owner is MAIN because the runner's owner list has no Forensics entry. Built by build_wheel0_candles.py from the WHEEL0_LISTS answers: every listed market, none dropped by result. %d markets, %d requests." % (len(mk), len(reqs)),
            "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"},
            "requests": reqs}


def main(folder, out):
    mk, cnt = read_markets(folder); os.makedirs(out, exist_ok=True); total = 0
    for s in SERIES:
        if not mk[s]: print("%s: no market listed, no job written" % s); continue
        j = job(s, mk[s]); total += len(j["requests"])
        json.dump(j, open(os.path.join(out, j["job_id"] + ".json"), "w"), indent=1); open(os.path.join(out, j["job_id"] + ".json"), "a").write("\n")
        print("%s: %d markets, closes %s to %s, %d requests" % (s, len(mk[s]), time.strftime("%Y-%m-%d %H:%M", time.gmtime(mk[s][0][1])), time.strftime("%Y-%m-%d %H:%M", time.gmtime(mk[s][-1][1])), len(j["requests"])))
    print("total requests %d | dropped: %s" % (total, json.dumps(cnt)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
