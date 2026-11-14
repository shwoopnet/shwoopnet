#!/usr/bin/env python3
"""Builds a kalshi-pull candle job for KXINX15M from a LISTS run: every ticker is exactly as listed, never rebuilt from a minute.
Reads only `ticker` and `close_time` of each listed market (no price, result or other field). Writes one job file. stdlib only.
Usage: build_spxoi1_candle_job.py --lists RUNDIR [RUNDIR..] --template JOB.json --out OUT.json [--from 2026-11-05] [--to 2026-11-14]"""
import argparse, calendar, gzip, hashlib, json, os, sys
from datetime import datetime

def ts(s):
    return calendar.timegm(datetime.strptime(s.strip().rstrip("Z").split(".")[0], "%Y-%m-%dT%H:%M:%S").timetuple())

def answer_files(dirs):
    out = []
    for d in dirs:
        mp = os.path.join(d, "manifest.json")
        if os.path.exists(mp):
            for r in json.load(open(mp)).get("rows", []):
                if r.get("status") != 200 or r.get("truncated"): continue
                fp = os.path.join(d, os.path.basename(r.get("file") or ""))
                if not os.path.exists(fp): continue
                b = (gzip.open if fp.endswith(".gz") else open)(fp, "rb").read()
                if hashlib.sha256(b).hexdigest() != r.get("sha256"): sys.exit("STOP: sha256 mismatch")
                out.append(fp)
        else:
            out += sorted(os.path.join(d, n) for n in os.listdir(d) if n.endswith(".json") or n.endswith(".json.gz"))
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--lists", nargs="+", required=True); ap.add_argument("--template", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--from", dest="lo", default="2026-11-05"); ap.add_argument("--to", dest="hi", default="2026-11-14")
    a = ap.parse_args(argv); lo = ts(a.lo + "T00:00:00"); hi = ts(a.hi + "T00:00:00")
    if hi > ts("2026-12-01T00:00:00"): sys.exit("STOP: the range reaches the held-out date")
    seen = {}; 
    for p in answer_files(a.lists):
        doc = json.load((gzip.open if p.endswith(".gz") else open)(p, "rt"))
        for m in (doc.get("markets") or []) if isinstance(doc, dict) else []:
            tk = m.get("ticker")
            if not isinstance(tk, str) or not tk.startswith("KXINX15M-"): continue
            if tk in seen: sys.exit("STOP: a listed ticker repeats across files")
            c = ts(m["close_time"])
            if lo <= c < hi: seen[tk] = c
    if not seen: sys.exit("STOP: no market kept")
    job = json.load(open(a.template)); reqs = []
    for i, (tk, c) in enumerate(sorted(seen.items(), key=lambda kv: (kv[1], kv[0])), 1):
        reqs.append({"id": "c%03d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": tk, "start_ts": c - 1800, "end_ts": c - 120, "period_interval": 1}})
    assert all(r["params"]["market_tickers"] in seen for r in reqs)      # every ticker is a listed ticker
    job["requests"] = reqs; job["max_requests"] = len(reqs)
    json.dump(job, open(a.out, "w"), indent=1); print("requests: %d" % len(reqs)); return 0

if __name__ == "__main__": sys.exit(main())
