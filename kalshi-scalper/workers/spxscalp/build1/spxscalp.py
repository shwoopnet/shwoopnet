#!/usr/bin/env python3
"""SPXSCALP scorer, build 1 (Desk B). Card: SPXSCALP_CARD_DRAFT_NOV13.md (Amendments 1 to 5), commit 6d35a82b.

PRINT LINE (licensed ES data): prints AGGREGATES ONLY (entries, net sum, profit factor, halves, labels, drop counts, spread median and p90).
No ES bar value, no per-bar line, no per-window line. It writes NO file at all (so none derived from the ES bars). stdlib only.

Usage: spxscalp.py --es ES.csv --candles DIR --lists DIR [--min-entries 100] [--start 2026-11-05] [--end 2026-11-13]
Inputs as in eslead1.py; the lists files must also carry "result" (yes|no|void) for each market.
"""
import argparse, csv, gzip, json, math, os, sys
from collections import Counter
from datetime import datetime, timezone

THR = 0.0005; EPS = 1e-9
BANDS = {"B25": (0.20, 0.25), "B30": (0.20, 0.30)}

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
    """Answer files of each run folder. With a manifest.json: only rows with status 200 and not truncated, each file checked against its sha256
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
                if hashlib.sha256(open(fp, "rb").read()).hexdigest() != r.get("sha256"): sys.exit("STOP: sha256 mismatch in a run folder")
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
    inst = cnt[0][0]; es = {}; other = 0
    for t, i, c in rows:
        if i != inst: other += 1; continue
        es[t + 60] = c
    drops["es_other_instrument"] += other; drops["es_unparseable_rows"] += bad
    if (bad + other) / max(total, 1) > 0.05: sys.exit("STOP: more than 5% of ES rows skipped")
    return es

def fee(p, c=1):
    p = min(max(p, 0.0), 1.0)
    return math.ceil(round(0.07 * p * (1 - p) * c * 100, 9)) / 100

def ts_ok(b, a): return b is not None and a is not None and 0 < b < a < 1

def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    if l <= EPS: return float("inf") if w > EPS else None
    return w / l

def fpf(x): return "n/a" if x is None else ("no losses" if x == float("inf") else "%.4f" % x)

def side_prices(side, bid, ask):
    # YES side: bid = yes bid, ask = yes ask. NO side: bid = 1 - yes ask, ask = 1 - yes bid.
    return (bid, ask) if side == "yes" else (1 - ask, 1 - bid)

def run_band(es, wins, band, drops):
    lo, hi = BANDS[band]; entries = []
    for w in wins:
        c, O, cand = w["c"], w["c"] - 900, w["cand"]
        if O not in es: drops["window_no_start_bar"] += 1; continue
        thr = THR * es[O]; entry = None
        for m in range(1, 6):
            t = O + 60 * m
            if t not in es: drops["look_es_missing"] += 1; continue
            mv = es[t] - es[O]
            side = "yes" if mv >= thr - EPS else ("no" if mv <= -thr + EPS else None)
            if side is None: continue
            cd = cand.get(t)
            if cd is None or not ts_ok(*cd): drops["look_not_two_sided"] += 1; continue
            _, ask = side_prices(side, cd[0], cd[1])
            if lo - EPS <= ask <= hi + EPS: entry = (t, side, ask); break
        if entry: entries.append((w, entry))
    return entries

def exit_px(w, side, t_from, c, pick):
    """First two-sided candle after t_from through c-300 satisfying pick(bid), else None. Returns (t, bid)."""
    for t in sorted(w["cand"]):
        if t_from < t <= c - 300:
            cd = w["cand"][t]
            if ts_ok(*cd):
                bid, _ = side_prices(side, cd[0], cd[1])
                if pick(bid): return t, bid
    return None

def time_exit(w, side, c):
    for t in sorted(w["cand"]):
        if c - 300 <= t <= c:
            cd = w["cand"][t]
            if ts_ok(*cd): return t, side_prices(side, cd[0], cd[1])[0]
    return None

def settle(side, result, fill):
    if result == "void": return fill            # refund the price; the fee is kept by the caller
    win = (result == "yes") == (side == "yes")
    return 1.0 if win else 0.0

def score(entries, s, arm, drops):
    """Returns list of (close, ticker, net, last_exit_t_or_None)."""
    out = []
    for w, (te, side, ask) in entries:
        c = w["c"]; fill = ask + s; res = w["result"]
        if res not in ("yes", "no", "void"): sys.exit("STOP: result other than yes, no or void on an entered window")
        if arm == "HOLD":
            net = settle(side, res, fill) - fill - fee(fill); out.append((c, w["ticker"], net, None)); continue
        tgt = 2 * fill
        def leg(pick):
            hit = exit_px(w, side, te, c, pick)
            if hit: return hit[0], hit[1] - s
            tx = time_exit(w, side, c)
            if tx:
                if tx[0] != c - 300: drops["exit_moved_to_next_two_sided"] += 1
                return tx[0], tx[1] - s
            drops["exit_settled"] += 1
            return None, None
        legs = [("t", lambda b: b >= tgt - EPS)]
        if arm == "HALF2X": legs.append(("e", lambda b: b >= 0.80 - EPS))
        net = 0.0; last = None; nc = len(legs)
        for _, pick in legs:
            t, px = leg(pick)
            if t is None:
                net += settle(side, res, fill) - fill
            else:
                net += px - fill - fee(px); last = t if last is None else max(last, t)
        net -= fee(fill, nc)
        out.append((c, w["ticker"], net, last))
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--es", required=True); ap.add_argument("--candles", required=True, nargs="+")
    ap.add_argument("--lists", required=True, nargs="+"); ap.add_argument("--min-entries", type=int, default=100)
    ap.add_argument("--start", default="2026-11-05"); ap.add_argument("--end", default="2026-11-13")
    a = ap.parse_args(argv); drops = Counter()
    lo = iso_ts(a.start + "T00:00:00"); hi = iso_ts(a.end + "T00:00:00")
    if hi > iso_ts("2026-12-01T00:00:00"): sys.exit("STOP: window reaches the held-out date")
    es = load_es(a.es, drops); meta = {}
    for p in answer_files(a.lists, drops):
        for m in markets_of(p, drops):
            try: c = iso_ts(m["close_time"])
            except Exception: drops["list_unparseable_close"] += 1; continue
            if lo <= c < hi: meta[m["ticker"]] = (c, m.get("result"))
    wins = []; seen = set()
    for p in answer_files(a.candles, drops):
        for m in markets_of(p, drops):
            tk = m.get("market_ticker", m.get("ticker"))
            if tk in seen: sys.exit("STOP: a market_ticker repeats across candle files (run overlap)")
            seen.add(tk)
            if tk not in meta: continue
            cand = {}
            for cs in m.get("candlesticks", []):
                try: ts_, bd, ak = int(cs["end_period_ts"]), float(cs["yes_bid"]["close_dollars"]), float(cs["yes_ask"]["close_dollars"])
                except Exception: drops["candle_missing_side"] += 1; continue
                if ts_ in cand: sys.exit("STOP: duplicate candle timestamp inside one market")
                cand[ts_] = (bd, ak)
            wins.append({"ticker": tk, "c": meta[tk][0], "result": meta[tk][1], "cand": cand})
    wins.sort(key=lambda w: (w["c"], w["ticker"]))
    print("windows with candles: %d" % len(wins))
    # C1: spread on the five looks of windows with a start bar
    spreads = []; nl = 0; nts = 0
    for w in wins:
        O = w["c"] - 900
        if O not in es: continue
        for m in range(1, 6):
            cd = w["cand"].get(O + 60 * m); nl += 1
            if cd is not None and ts_ok(*cd): nts += 1; spreads.append(round((cd[1] - cd[0]) * 100, 6))
    spreads.sort()
    def nr(q): return spreads[max(0, math.ceil(q * len(spreads)) - 1)] if spreads else None
    print("C1 looks: %d, two-sided: %d, YES spread median %s c, p90 %s c (nearest rank)" % (nl, nts, nr(0.5), nr(0.9)))
    for band in ("B25", "B30"):
        bd = Counter(); entries = run_band(es, wins, band, bd)
        for arm in ("HEADLINE", "HALF2X", "HOLD"):
            res = {}
            for s, tag in ((0.01, "1c"), (0.02, "2c")):
                ad = Counter(); res[tag] = score(entries, s, arm, ad)
                if tag == "1c": armdrops = ad
            n = len(res["1c"]); primary = "1c"
            if any(x[3] is not None and x[3] > x[0] - 120 for x in res["1c"]): primary = "2c"
            line = []
            for tag in ("1c", "2c"):
                v = [x[2] for x in sorted(res[tag])]; h = len(v) // 2
                print("%s %s %s: n=%d, net=%.2f, PF=%s, half1 PF=%s, half2 PF=%s" % (band, arm, tag, n, sum(v), fpf(pf(v)), fpf(pf(v[:h])), fpf(pf(v[h:]))))
            v1 = [x[2] for x in sorted(res["1c"])]; v2 = [x[2] for x in sorted(res["2c"])]; h = n // 2
            p1, p2, a1, b1 = pf(v1), pf(v2), pf(v1[:h]), pf(v1[h:])
            ge = lambda x, y: x is not None and x >= y - EPS
            lt = lambda x, y: x is not None and x < y - EPS
            if n < a.min_entries: label = "FALSIFIED (fewer than %d entries)" % a.min_entries
            elif lt(a1, 1.0) or lt(b1, 1.0) or lt(p2, 1.0): label = "FALSIFIED"
            elif ge(p1, 1.3) and ge(a1, 1.0) and ge(b1, 1.0) and ge(p2, 1.0): label = "counts"
            else: label = "no evidence"
            print("%s %s drops (1c read): %s" % (band, arm, ", ".join("%s=%d" % kv for kv in sorted(armdrops.items())) or "none"))
            print("%s %s label: %s (primary read %s); upper bound, not fill-checked; fee mode per-order rounded; void refunds the price and keeps the fee" % (band, arm, label, primary))
        print("%s entry-scan drops: %s" % (band, ", ".join("%s=%d" % kv for kv in sorted(bd.items())) or "none"))
    print("global drops: " + (", ".join("%s=%d" % kv for kv in sorted(drops.items())) or "none"))
    return 0

if __name__ == "__main__": sys.exit(main())
