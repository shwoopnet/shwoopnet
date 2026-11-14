#!/usr/bin/env python3
"""ESLEAD1 scorer, build 1 (Desk B). Card: ESLEAD1_CARD_NOV13.md (Amendments 1 to 4).

PRINT LINE (licensed ES data): this script prints AGGREGATES ONLY: counts of drops by reason, the pair count and the pooled Pearson
correlation per lag, and the prediction line. It prints no ES bar value, no per-bar line and no per-window line, and it writes NO
file derived from the ES bars (it writes nothing at all). stdlib only.

Usage: eslead1.py --es ES.csv --candles DIR --lists DIR [--min-pairs 30] [--start 2026-11-05] [--end 2026-11-13]
  ES.csv: Databento 1 minute bars, header ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume; ts_event is the bar START.
  DIR (candles): JSON or JSON.GZ files holding {"markets":[{"market_ticker":..,"candlesticks":[{end_period_ts, yes_bid{close_dollars}, yes_ask{close_dollars}}]}]}
  DIR (lists): JSON or JSON.GZ files holding {"markets":[{"ticker":..,"close_time":ISO}]}
"""
import argparse, csv, gzip, json, math, os, sys
from collections import Counter
from datetime import datetime, timezone

def iso_ts(s):
    s = s.strip()
    if s.endswith("Z"): s = s[:-1]
    if "." in s:
        a, b = s.split("."); s = a + "." + b[:6]
        return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp())
    return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())

def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f: return json.load(f)

def files(d): return sorted(os.path.join(d, n) for n in os.listdir(d) if n.endswith(".json") or n.endswith(".json.gz"))


def answer_files(dirs, drops):
    """Answer files of each run folder. With a manifest.json: only rows with status 200 and not truncated, each file checked against its sha256 (of the DECOMPRESSED body for a .gz file, as the runner writes it)
    (a mismatch stops the run); other rows are counted by reason. Without a manifest (made-up fixtures): every *.json or *.json.gz file."""
    import hashlib
    out = []
    for d in dirs:
        mp = os.path.join(d, "manifest.json")
        if os.path.exists(mp):
            for r in json.load(open(mp)).get("rows", []):
                if r.get("status") != 200: drops["manifest_row_not_200"] += 1; continue
                if r.get("truncated"): drops["manifest_row_truncated"] += 1; continue
                fp = os.path.join(d, os.path.basename(r.get("file") or ""))
                if not r.get("file") or not os.path.exists(fp): drops["manifest_row_file_missing"] += 1; continue
                if hashlib.sha256((gzip.open if fp.endswith(".gz") else open)(fp, "rb").read()).hexdigest() != r.get("sha256"): sys.exit("STOP: sha256 mismatch in a run folder")
                out.append(fp)
        else:
            out.extend(files(d))
    return out

def markets_of(path, drops):
    doc = jload(path)
    if not isinstance(doc, dict) or not isinstance(doc.get("markets"), list): drops["answer_without_markets_list"] += 1; return []
    return doc["markets"]

def load_es(path, drops):
    rows = []; bad = 0; total = 0
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            total += 1
            try: rows.append((iso_ts(r["ts_event"]), int(r["instrument_id"]), float(r["close"])))
            except Exception: bad += 1
    if not rows: sys.exit("STOP: no ES rows kept")
    cnt = Counter(i for _, i, _ in rows).most_common()
    if len(cnt) > 1 and cnt[0][1] == cnt[1][1]: sys.exit("STOP: instrument tie")
    inst = cnt[0][0]; es = {}
    for t, i, c in rows:
        if i != inst: drops["es_other_instrument"] += 1; continue
        es[t + 60] = c                      # bar START + 60 s = the minute END at which the close is the price
    drops["es_unparseable_rows"] += bad
    if (bad + drops["es_other_instrument"]) / max(total, 1) > 0.05: sys.exit("STOP: more than 5% of ES rows skipped")
    return es

def two_sided(b, a): return b is not None and a is not None and 0 < b < a < 1

def corr(pairs):
    n = len(pairs); mx = sum(a for a, _ in pairs) / n; my = sum(b for _, b in pairs) / n
    sxx = sum((a - mx) ** 2 for a, _ in pairs); syy = sum((b - my) ** 2 for _, b in pairs)
    if sxx <= 0 or syy <= 0: return None
    return sum((a - mx) * (b - my) for a, b in pairs) / math.sqrt(sxx * syy)

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--es", required=True); ap.add_argument("--candles", required=True, nargs="+")
    ap.add_argument("--lists", required=True, nargs="+"); ap.add_argument("--min-pairs", type=int, default=30)
    ap.add_argument("--start", default="2026-11-05"); ap.add_argument("--end", default="2026-11-13")
    a = ap.parse_args(argv); drops = Counter()
    lo = iso_ts(a.start + "T00:00:00"); hi = iso_ts(a.end + "T00:00:00")
    if hi > iso_ts("2026-12-01T00:00:00"): sys.exit("STOP: window reaches the held-out date")
    es = load_es(a.es, drops)
    closes = {}
    for p in answer_files(a.lists, drops):
        for m in markets_of(p, drops):
            try: c = iso_ts(m["close_time"])
            except Exception: drops["list_unparseable_close"] += 1; continue
            if lo <= c < hi: closes[m["ticker"]] = c
    pooled = {k: [] for k in range(-3, 4)}; nwin = 0
    seen = set()
    for p in answer_files(a.candles, drops):
        for m in markets_of(p, drops):
            tk = m.get("market_ticker", m.get("ticker"))
            if tk in seen: sys.exit("STOP: a market_ticker repeats across candle files (run overlap); not counted twice")
            seen.add(tk); c = closes.get(tk)
            if c is None: continue
            mid = {}
            tseen = set()
            for cs in m.get("candlesticks", []):
                try:
                    t = int(cs["end_period_ts"]); b = float(cs["yes_bid"]["close_dollars"]); ak = float(cs["yes_ask"]["close_dollars"])
                except Exception: drops["candle_missing_side"] += 1; continue
                if t in tseen: sys.exit("STOP: duplicate candle timestamp inside one market")
                tseen.add(t)
                if two_sided(b, ak): mid[t] = (b + ak) / 2
                else: drops["candle_not_two_sided"] += 1
            nwin += 1; O = c - 900
            # T = whole-minute ends in [O+60, c] that have BOTH a two-sided Kalshi mid and an ES bar (computed once per window).
            T = {t for t in range(O + 60, c + 1, 60) if t in mid and t in es}
            drops["minute_not_in_both"] += (c - O) // 60 - len(T)
            dA = {t: mid[t] - mid[t - 60] for t in T if t - 60 in mid}            # lookback from the whole Kalshi series
            dB = {t: math.log(es[t] / es[t - 60]) for t in T if t - 60 in es}     # lookback from the whole ES series
            for k in range(-3, 4):
                for t in dA:
                    if (t - 60 * k) in dB: pooled[k].append((dA[t], dB[t - 60 * k]))
                    else: drops["pair_outside_window_or_missing_es"] += 1
    cells = {}; npairs = {}
    for k in range(-3, 4):
        npairs[k] = len(pooled[k])
        cells[k] = None if npairs[k] < a.min_pairs else corr(pooled[k])
    line = ", ".join("%+d: %s" % (k, ("n/a" if cells[k] is None else "%.3f" % cells[k])) for k in range(-3, 4))
    print("lead/lag, 1 minute change correlation Kalshi mid vs ES at lags -3..+3: " + line)
    print("pairs per lag: " + ", ".join("%+d: %d" % (k, npairs[k]) for k in range(-3, 4)))
    print("windows with candles: %d" % nwin)
    print("drops by reason: " + (", ".join("%s=%d" % kv for kv in sorted(drops.items())) or "none"))
    if cells[0] is None: pred = 'untestable at n = %d' % npairs[0]
    else:
        ok = npairs[0] >= a.min_pairs and all(cells[k] is None or cells[k] <= cells[0] for k in range(-3, 4) if k != 0)
        # "no lag from +1 to +3 exceeds it" and lag 0 is the largest: both read against the seven cells
        ok = ok and all(cells[k] is None or cells[k] <= cells[0] for k in (1, 2, 3))
        pred = "pass (peak at lag 0, no lead)" if ok else "fail (a lag other than 0 is larger)"
    print("prediction: " + pred + "; upper bound, not fill-checked")
    return 0

if __name__ == "__main__": sys.exit(main())
