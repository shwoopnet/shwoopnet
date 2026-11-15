#!/usr/bin/env python3
"""Builds the kalshi-pull job that asks the settled result of every S3 paper fill ticker (development window). Reads ONLY quotes.csv.gz files (never results.csv.gz).
Usage: build_s3_results_job.py <combo-data checkout> <template job .json> <out .json>   Paper only; no order; no key."""
import csv, glob, gzip, json, os, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(0, os.path.join(here, ".."))
import importlib.util
spec = importlib.util.spec_from_file_location("s3_score", os.path.join(here, "s3_score.py")); s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
MAX_BATCH, MAX_REQ, SLACK = 100, 1000, 12

def main(root, template, out):
    snaps = []
    for q in sorted(glob.glob(os.path.join(root, "combo", "*", "*", "quotes.csv.gz"))):      # quotes only: no results file is ever opened
        rows = list(csv.DictReader(gzip.open(q, "rt", newline="")))
        if rows: snaps.append(rows)
    fl = s3.fills(snaps, s3.ts(s3.START_UTC), s3.ts(s3.HELDOUT_START_UTC))
    tickers = sorted({f["ticker"] for f in fl})
    if not tickers: sys.exit("REFUSED: no paper fill, nothing to ask")
    batches = [tickers[i:i + MAX_BATCH] for i in range(0, len(tickers), MAX_BATCH)]
    if len(batches) > MAX_REQ: sys.exit("REFUSED: more than %d requests" % MAX_REQ)
    job = json.load(open(template))
    job["job_id"] = "S3_RESULTS"
    job["registration"] = "kalshi-scalper/workers/S3_COMBO_HOUSE_SIDE_REGISTRATION.md"
    job["allowed_endpoints"] = [{"name": "markets_by_ticker", "method": "GET", "path_pattern": "/markets", "params_allowed": ["tickers", "status", "limit"]}]
    job["requests"] = [{"id": "r%03d" % (i + 1), "path": "/markets", "params": {"tickers": ",".join(b), "limit": 100}, "max_pages": 1} for i, b in enumerate(batches)]
    job["ticker_allowlist"] = tickers
    job["series_allowlist"] = sorted({t.split("-")[0] for t in tickers})
    job["max_requests"] = len(batches) + SLACK
    job["pacing_seconds"] = 5.0
    assert all(t in set(job["ticker_allowlist"]) for r in job["requests"] for t in r["params"]["tickers"].split(","))
    json.dump(job, open(out, "w"), indent=1)
    print("S3 paper fills %d | requests %d | cap %d" % (len(tickers), len(batches), job["max_requests"]))

if __name__ == "__main__":
    main(*sys.argv[1:4])
