#!/usr/bin/env python3
"""Stage 2 of INPLAYJUMP: candle job files from the INPLAYJUMP_LISTS answers. Offline: sends nothing.
  python3 -I build_inplayjump_candles.py <INPLAYJUMP_SERIES.json> <stage 1 run folder> <outdir>
Per family: development matches only (market closes inside the family's development window; the Tie contract is never pulled: it is never the jumper and never bought), contracts of consecutive matches batched so that
tickers <= 100 and (window minutes x tickers) <= 9,000 (the batched endpoint answers 400 above about 10,000 candles); window = first close minus the family's candle lead to last close; period_interval 1.
At most 380 requests a job file (the 200 MB run cap). Prints the request count per family."""
import gzip, json, os, sys, calendar, time, re, collections
def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def main(series_path, folder, outdir):
    S = json.load(open(series_path)); man = json.load(open(os.path.join(folder, "manifest.json"))); mk = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        b = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            c = iso_ts(m.get("close_time") or "")
            if m.get("ticker") and c and m.get("result") in ("yes", "no"): mk[m["ticker"]] = (m["ticker"].split("-")[0], m.get("event_ticker", ""), c)
    reqs, per = [], collections.Counter(); alltk = set()
    for f in S["families_ranked_by_events"]:
        lo, hi, lead = iso_ts(f["development"]["closes_from"]), iso_ts(f["development"]["closes_before"]), f["candle_minutes_before_close"]
        items = sorted(((t, c) for t, (s, e, c) in mk.items() if s in f["series"] and lo <= c < hi and not t.endswith("-TIE")), key=lambda x: (x[1], x[0]))
        cur = []
        def flush(cur=None):
            reqs.append(dict(id="c%05d" % len(reqs), path="/markets/candlesticks", params={"market_tickers": ",".join(t for t, _ in cur), "start_ts": cur[0][1] - lead * 60, "end_ts": cur[-1][1], "period_interval": 1})); per[f["family"]] += 1
        for it in items:
            trial = cur + [it]
            if cur and (len(trial) > 100 or ((trial[-1][1] - trial[0][1]) / 60 + lead) * len(trial) > 9000): flush(cur); cur = [it]
            else: cur = trial
        if cur: flush(cur)
        alltk.update(t for t, _ in items)
    os.makedirs(outdir, exist_ok=True); n = 0
    for i in range(0, len(reqs), 380):
        ch = reqs[i:i + 380]; n += 1
        tk = sorted({t for r in ch for t in r["params"]["market_tickers"].split(",")}); sers = sorted({t.split("-")[0] for t in tk})
        job = {"job_id": "INPLAYJUMP_C%d" % n, "owner": "DESK_A", "registration": "kalshi-scalper/workers/inplayjump/INPLAYJUMP_REGISTRATION.md", "purpose": "INPLAYJUMP stage 2 (part %d): 1 minute candles of the development-window match contracts listed by INPLAYJUMP_LISTS." % n,
               "heldout": "none: development windows only", "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
               "series_allowlist": sers, "ticker_allowlist": tk, "max_requests": len(ch), "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
               "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"}, "requests": ch}
        json.dump(job, open(os.path.join(outdir, "INPLAYJUMP_C%d.json" % n), "w"), indent=1)
    print("contracts %d | candle requests %d | jobs %d | per family %s" % (len(alltk), len(reqs), n, dict(per)))
if __name__ == "__main__": main(*sys.argv[1:4])
