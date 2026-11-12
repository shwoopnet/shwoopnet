#!/usr/bin/env python3
"""INPLAYJUMP tennis screen VALIDATION job (Desk B, Amendment 6; pending the Head's go). Offline: sends nothing.
  python3 -I build_inplayjump_validation.py <INPLAYJUMP_SERIES.json> <lists run folder> <outdir>
For each tennis family: the 10 development matches whose EVENT tickers come first in md5 order (hashlib.md5 of the event ticker, hex digest, ascending; the Tie never; the result field not read), FULL minute candles from the market's open to the close for every contract of those matches
plus their HOURLY candles from the open to the close. The engine is later run both ways on them (screened against full); any mismatch in bets, in-play set or placebo, or a 2c step found inside an hour the screen would have skipped, voids the screen for that family.
Contracts are packed with tickers <= 100 and (window minutes x tickers) <= 9,000 per request. Prints the request count per family and kind."""
import json, os, sys, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_inplayjump_candles as B
def main(series_path, folder, outdir):
    if os.path.basename(os.path.normpath(folder)).startswith("HELDOUT_"): sys.exit("REFUSED: held-out folder (standing rule h)")
    S = json.load(open(series_path)); mk = B.read_lists(folder); reqs, per = [], collections.Counter()
    for f, items in B.families(S, mk, False):
        ev = collections.defaultdict(list)
        for t, m in items: ev[m["event"]].append((t, m))
        pick = sorted(ev, key=lambda e: hashlib.md5(e.encode()).hexdigest())[:10]
        its = sorted(((t, m["open"] or m["close"] - 20 * 3600, m["close"]) for e in pick for t, m in ev[e]), key=lambda x: (x[1], x[0]))
        B.pack(its, None, reqs, per, f["family"] + " minute", 1, 1)
        B.pack(its, None, reqs, per, f["family"] + " hourly", 60, 60)
    n = B.write(reqs, outdir, "INPLAYJUMP_VAL", "INPLAYJUMP tennis screen validation: 10 md5-first matches per tennis family, full minute and hourly candles from the open to the close")
    print("validation requests %d | jobs %d | per family and kind %s" % (len(reqs), n, dict(per)))
if __name__ == "__main__": main(*sys.argv[1:4])
