#!/usr/bin/env python3
"""ONE job file for the INPLAYJUMP pilot AND the tennis screen validation pull (Head, Nov 12 19:46Z): the 5-request cost pilot (one batch per family on its first development days) plus Desk B's validation (10 md5-first matches per tennis family,
full minute candles from the open plus hourly candles). Offline: sends nothing. No result read, development matches only, every window bounded by the lists (which end before the held-out cut). The lists folder is the only placeholder.
  python3 -I build_inplayjump_pilotval.py <INPLAYJUMP_SERIES.json> <lists run folder> <outdir>"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_inplayjump_pilot as P, build_inplayjump_validation as V, build_inplayjump_candles as B
def main(series_path, folder, outdir):
    import heldout_guard; heldout_guard.refuse_heldout(folder, "pilotval builder")
    import tempfile, io, contextlib
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2, contextlib.redirect_stdout(io.StringIO()) as o:
        P.main(series_path, folder, t1); V.main(series_path, folder, t2)
        a = json.load(open(os.path.join(t1, "INPLAYJUMP_PILOT.json"))); b = json.load(open(os.path.join(t2, "INPLAYJUMP_VAL1.json")))
    reqs = []
    for i, r in enumerate(a["requests"]): reqs.append(dict(r, id="p%02d" % i))
    for i, r in enumerate(b["requests"]): reqs.append(dict(r, id="v%02d" % i))
    job = dict(a, job_id="INPLAYJUMP_PILOTVAL", purpose="INPLAYJUMP pilot (cost and tradeability, one batch per family) plus tennis screen validation (10 md5-first matches per tennis family: minute and hourly candles). No result read; development matches only.",
               requests=reqs, max_requests=len(reqs), ticker_allowlist=sorted(set(a["ticker_allowlist"]) | set(b["ticker_allowlist"])), series_allowlist=sorted(set(a["series_allowlist"]) | set(b["series_allowlist"])))
    os.makedirs(outdir, exist_ok=True); json.dump(job, open(os.path.join(outdir, "INPLAYJUMP_PILOTVAL.json"), "w"), indent=1)
    print("pilot %d + validation %d = %d requests | tickers %d" % (len(a["requests"]), len(b["requests"]), len(reqs), len(job["ticker_allowlist"])))
if __name__ == "__main__": main(*sys.argv[1:4])
