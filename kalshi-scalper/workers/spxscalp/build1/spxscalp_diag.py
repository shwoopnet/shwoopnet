#!/usr/bin/env python3
"""SPXSCALP counts-only diagnostic (Desk B, Nov 15, 2026, on the Head's order). Imports build 1's loaders and entry scan unchanged.
Usage: spxscalp_diag.py --es ES.csv --candles DIR... --lists DIR... [--start 2026-11-05] [--end 2026-11-13]
Prints COUNTS ONLY: looks, looks with an ES move at or over the threshold, of those the two-sided ones, the candidate side's ask in 5c bands,
looks and windows in each arm's band, and the scorer's own entry count as a cross-check. No ES value, no per-bar or per-window line, no file written."""
import argparse, math, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxscalp as S

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--es", required=True); ap.add_argument("--candles", required=True, nargs="+")
    ap.add_argument("--lists", required=True, nargs="+"); ap.add_argument("--start", default="2026-11-05"); ap.add_argument("--end", default="2026-11-13")
    a = ap.parse_args(argv); drops = Counter()
    lo = S.iso_ts(a.start + "T00:00:00"); hi = S.iso_ts(a.end + "T00:00:00")
    if hi > S.iso_ts("2026-12-01T00:00:00"): sys.exit("STOP: window reaches the held-out date")
    es = S.load_es(a.es, drops); meta = {}
    for p in S.answer_files(a.lists, drops):
        for m in S.markets_of(p, drops):
            try: c = S.iso_ts(m["close_time"])
            except Exception: continue
            if lo <= c < hi: meta[m["ticker"]] = (c, m.get("result"))
    wins = []; seen = set()
    for p in S.answer_files(a.candles, drops):
        for m in S.markets_of(p, drops):
            tk = m.get("market_ticker", m.get("ticker"))
            if tk in seen: sys.exit("STOP: a market_ticker repeats across candle files (run overlap)")
            seen.add(tk)
            if tk not in meta: continue
            cand = {}
            for cs in m.get("candlesticks", []):
                try: ts_, bd, ak = int(cs["end_period_ts"]), float(cs["yes_bid"]["close_dollars"]), float(cs["yes_ask"]["close_dollars"])
                except Exception: continue
                if ts_ in cand: sys.exit("STOP: duplicate candle timestamp inside one market")
                cand[ts_] = (bd, ak)
            wins.append({"ticker": tk, "c": meta[tk][0], "result": meta[tk][1], "cand": cand})
    wins.sort(key=lambda w: (w["c"], w["ticker"]))
    nwin = len(wins); nstart = looks = es_present = moves = ts_n = nts_n = yes_n = no_n = 0
    hist = Counter(); inband = {b: 0 for b in S.BANDS}; winband = {b: 0 for b in S.BANDS}
    for w in wins:
        O = w["c"] - 900
        if O not in es: continue
        nstart += 1; thr = S.THR * es[O]; hit = {b: False for b in S.BANDS}
        for m in range(1, 6):
            t = O + 60 * m; looks += 1
            if t not in es: continue
            es_present += 1; mv = es[t] - es[O]
            side = "yes" if mv >= thr - S.EPS else ("no" if mv <= -thr + S.EPS else None)
            if side is None: continue
            moves += 1; yes_n += side == "yes"; no_n += side == "no"
            cd = w["cand"].get(t)
            if cd is None or not S.ts_ok(*cd): nts_n += 1; continue
            ts_n += 1; ask = S.side_prices(side, cd[0], cd[1])[1]
            hist[min(19, max(0, int(math.floor((ask + S.EPS) * 20))))] += 1
            for b, (l, h) in S.BANDS.items():
                if l - S.EPS <= ask <= h + S.EPS: inband[b] += 1; hit[b] = True
        for b in S.BANDS: winband[b] += hit[b]
    print("DIAGNOSTIC (counts only; build 1 scorer unchanged): windows with candles %d; windows with a start bar %d; looks %d; looks with an ES bar %d" % (nwin, nstart, looks, es_present))
    print("looks with an ES move at or over the threshold: %d (YES side %d, NO side %d); of those two-sided %d, not two-sided %d" % (moves, yes_n, no_n, ts_n, nts_n))
    print("candidate side ask, looks by 5c band: " + ", ".join("[%.2f,%.2f) %d" % (i / 20, (i + 1) / 20, hist[i]) for i in range(20) if hist[i]) if hist else "candidate side ask, looks by 5c band: none")
    for b in S.BANDS:
        n = len(S.run_band(es, wins, b, Counter()))
        print("%s band %.2f to %.2f: looks %d, windows with at least one in-band look %d; scorer entry scan entries_found %d" % (b, S.BANDS[b][0], S.BANDS[b][1], inband[b], winband[b], n))
    return 0

if __name__ == "__main__": sys.exit(main())
