#!/usr/bin/env python3
"""Builds the OICAND_CANDLES kalshi-pull job (open interest candles for Desk A's twelve OICORE wheel places) from the answers of the OICAND_LISTS run.
Reads ONLY ticker and close_time from the settled lists (no result, price or volume). Usage: [OICAND_MAXREQ=1000] oi_candles_job.py <lists run folder> <out directory>  (writes OICAND_CANDLES_1.json, _2.json, ...)
Rules (fixed here): the last 20 weekdays (Monday to Friday by the UTC date of the close) present in the lists; one request per distinct close time, the tickers of every
series that has a market with that close batched in market_tickers; period_interval 1; start_ts = close - 420 s, end_ts = close - 120 s (covers the candles ending
close - 360 s and close - 180 s and the entry minutes, and leaves the last two minutes unread); a ticker of EVENT830's 8 series closing at 13:30Z on its past forward dates
(2026-11-05, 11-06, 11-10, 11-12, 11-13) is dropped even if listed; nothing closing after 2026-11-13T02:35:00Z. Standard library only."""
import gzip, hashlib, json, os, sys
from datetime import datetime, timezone

END = "2026-11-13T02:35:00Z"
EV830 = {"KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"}
CUT_DATES = {"2026-11-05", "2026-11-06", "2026-11-10", "2026-11-12", "2026-11-13"}
DAYS = 20

def ep(s):
    return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())

def read(run):
    man = json.load(open(os.path.join(run, "manifest.json")))
    out = []
    for row in man.get("rows", []):
        if row.get("status") != 200 or not str(row.get("id", "")).startswith("settled_"):
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in (body.get("markets", []) if isinstance(body, dict) else []):
            out.append((m["ticker"], m["close_time"]))          # times only
    return out

def build(markets):
    keep = []
    for tk, ct in markets:
        s = tk.split("-")[0]
        if ct > END:
            continue
        if s in EV830 and ct[11:16] == "13:30" and ct[:10] in CUT_DATES:
            continue
        if datetime.strptime(ct[:10], "%Y-%m-%d").weekday() > 4:
            continue                                            # weekdays only (UTC date of the close)
        keep.append((tk, ct))
    days = sorted({ct[:10] for _, ct in keep})[-DAYS:]
    keep = [(tk, ct) for tk, ct in keep if ct[:10] in days]
    by = {}
    for tk, ct in keep:
        by.setdefault(ct, set()).add(tk)
    reqs = []
    for i, ct in enumerate(sorted(by)):
        c = ep(ct)
        reqs.append({"id": "c%04d" % (i + 1), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(sorted(by[ct])), "start_ts": c - 420, "end_ts": c - 120, "period_interval": 1}})
    return days, reqs, sorted({tk for tk, _ in keep})

def main():
    days, reqs, tickers = build(read(sys.argv[1]))
    maxreq = int(os.environ.get("OICAND_MAXREQ", "1000"))
    tpl = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "OICAND_CANDLES_template.json")))
    os.makedirs(sys.argv[2], exist_ok=True)
    chunks = [reqs[i:i + maxreq] for i in range(0, len(reqs), maxreq)] or [[]]
    for k, ch in enumerate(chunks, 1):
        job = json.loads(json.dumps(tpl))
        job["job_id"] = "OICAND_CANDLES_%d" % k
        job["requests"] = ch
        job["ticker_allowlist"] = sorted({t for r in ch for t in r["params"]["market_tickers"].split(",")})
        job["max_requests"] = len(ch)
        job["notes"] += " Part %d of %d of the same candle pull, at most %d requests each (about 27 KB a request unpacked)." % (k, len(chunks), maxreq)
        path = os.path.join(sys.argv[2], "OICAND_CANDLES_%d.json" % k)
        json.dump(job, open(path, "w"), indent=1)
        print("part %d of %d: %s | %d requests | %d tickers | sha256 %s" % (k, len(chunks), os.path.basename(path), len(ch), len(job["ticker_allowlist"]), hashlib.sha256(open(path, "rb").read()).hexdigest()))
    print("days %d (%s to %s) | closes %d | tickers %d | requests %d | files %d" % (len(days), days[0], days[-1], len(reqs), len(tickers), len(reqs), len(chunks)))

if __name__ == "__main__":
    main()
