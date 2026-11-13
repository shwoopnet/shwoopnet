#!/usr/bin/env python3
"""Stage 2 of the candle refresh for V2's registered forward reads: builds candle job files from the V2READS_LISTS answers. Offline: it sends no request.
  python3 -I build_v2reads_candles.py <stage 1 run folder> <outdir>       writes V2READS_C1.json, V2READS_C2.json, ... (at most PER_JOB requests each) and prints the totals
Markets: every settled market of the 18 series with result yes/no, closes from 2026-10-12T00:00Z, per series in close-time order. Each request holds consecutive markets of ONE series with
(window minutes) x (tickers) <= 9,000 (the batched candle endpoint answers 400 above 10,000; V2 backfill.py), window = first open to last close, period_interval 1.
PER_JOB = 380 keeps one run under the 200 MB run cap (about 0.5 MB an answer; an estimate to check on the first job)."""
import gzip, json, os, sys, calendar, time, re
LIMIT, PER_JOB = 9000, 380
SER = ["KXBNB15M","KXBTC15M","KXCOPPER15M","KXDOGE15M","KXETH15M","KXEURUSD15M","KXGBPUSD15M","KXGOLD15M","KXHYPE15M","KXNATGAS15M","KXNEAR15M","KXPALLADIUM15M","KXPLATINUM15M","KXSILVER15M","KXUSDJPY15M","KXWTI15M","KXXRP15M","KXZEC15M"]
MIN_TS = 1760227200
def iso_ts(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def read_markets(folder):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "desk_a_verify")); import heldout_guard_v2 as heldout_guard; heldout_guard.refuse_heldout(folder, "build_v2reads_candles")      # standing rule (h)
    man = json.load(open(os.path.join(folder, "manifest.json"))); out = {}
    for row in man["rows"]:
        if row.get("status") != 200 or "file" not in row: continue
        body = json.load(gzip.open(os.path.join(folder, row["file"])))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            o, c = iso_ts(m.get("open_time") or ""), iso_ts(m.get("close_time") or "")
            s = (m.get("ticker") or "").split("-")[0]
            if s in SER and m.get("result") in ("yes", "no") and o and c and c >= MIN_TS: out[m["ticker"]] = (s, o, c)
    return out
def batches(mk):
    reqs = []
    for s in SER:
        items = sorted(((t, o, c) for t, (ss, o, c) in mk.items() if ss == s), key=lambda x: (x[2], x[0])); cur = []
        for it in items:
            trial = cur + [it]
            if cur and (max(x[2] for x in trial) - min(x[1] for x in trial)) / 60 * len(trial) > LIMIT:
                reqs.append(cur); cur = [it]
            else: cur = trial
        if cur: reqs.append(cur)
    return [dict(id="c%05d" % i, path="/markets/candlesticks", params={"market_tickers": ",".join(x[0] for x in b), "start_ts": min(x[1] for x in b), "end_ts": max(x[2] for x in b), "period_interval": 1}) for i, b in enumerate(reqs)]
def main(folder, outdir):
    mk = read_markets(folder); reqs = batches(mk); os.makedirs(outdir, exist_ok=True); n = 0
    for i in range(0, len(reqs), PER_JOB):
        chunk = reqs[i:i + PER_JOB]; n += 1
        tk = sorted({t for r in chunk for t in r["params"]["market_tickers"].split(",")})
        job = {"job_id": "V2READS_C%d" % n, "owner": "DESK_A", "registration": "kalshi-scalper/workers/DESK_A_V2_READS_INVENTORY.md",
               "purpose": "Stage 2 (part %d) of the candle refresh for V2's registered forward reads: 1 minute candles of the settled 15 minute markets listed by V2READS_LISTS." % n,
               "heldout": "none: registered forward reads", "allowed_endpoints": [{"name": "markets_candlesticks_batch", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
               "series_allowlist": SER, "ticker_allowlist": tk, "max_requests": len(chunk), "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
               "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out; three in a row end the run; no other address, no proxy, no retry around a refusal"}, "requests": chunk}
        json.dump(job, open(os.path.join(outdir, "V2READS_C%d.json" % n), "w"), indent=1)
    print("markets %d | candle requests %d | jobs %d (at most %d requests each)" % (len(mk), len(reqs), n, PER_JOB))
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
