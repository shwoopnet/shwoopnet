#!/usr/bin/env python3
"""Data inventory counter (Forensics desk, Nov 14, 2026; the Head's overnight item 3). COUNTS ONLY: first and last time, rows, the two-sided share (rule 18) and gaps over 30 minutes of each recorded source.
It reads, per row, only the time column, the series or ticker column and the best bid and ask columns needed for rule 18; it never reads a result, a trade price or size, volume or open interest, and it prints no price.
HELD OUT: rows of a window whose close_time is on or after a cut are NOT counted (a cut is a date given on the command line per source, from the registry: see DATA_INVENTORY_TABLE_NOV14.md); the number of such rows skipped is printed.
Rule 18 (two-sided): 0 < yes_bid < yes_ask < 1 in whole cents. For a book row the YES ask is 1 minus the best NO bid, so two-sided means yes_bid_px_1 > 0, no_bid_px_1 > 0 and yes_bid_px_1 + no_bid_px_1 < 1.
For a quote row, yes_bid and yes_ask. For a perpetual (prices not on 0 to 1): bid > 0, ask > 0 and bid < ask.
usage: python3 -I inventory_counts.py <kind> <root> [cut ISO date, e.g. 2026-11-05T00:00:00Z]
  kind: book (a folder of <date>/<HHMM>/book.csv.gz with t_recv_ms, series, close_time, yes_bid_px_1, no_bid_px_1), bookl (ladder book: poll_ts_local_ms, ticker), quotes (quotes.csv.gz: t_recv_ms, ticker, yes_bid, yes_ask),
        polrec (t_recv_ms, series, yes_bid, yes_ask), ingame (obs.csv.gz: t_recv_ms, kind, yes_bid, yes_ask), combo (t_recv_ms, ticker, yes_bid, yes_ask), dailyq (daily, ref, wxens: poll_ts, series, yes_bid, yes_ask), perps30 (ts_utc, ticker, bid, ask), kalshi1m (end_period_ts, ticker, bid_close, ask_close)"""
import sys, os, csv, gzip, collections, re
from datetime import datetime, timezone

GAP_S = 30 * 60


def iso(s):
    try: return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except Exception: return None


def cents(s):
    try:
        if s is None or s == "": return None
        v = float(s)
        return None if v != v else int(round(v * 100))
    except ValueError: return None


def files(root, name_re):
    out = []
    for d, _, fs in os.walk(root):
        for f in fs:
            if re.search(name_re, f): out.append(os.path.join(d, f))
    return sorted(out)


def opener(p): return gzip.open(p, "rt", newline="") if p.endswith(".gz") else open(p, newline="")


class Acc:
    def __init__(self): self.n = 0; self.two = 0; self.first = None; self.last = None; self.skipped = 0; self.files = set(); self.spans = []   # per file (min, max, internal gaps)


def main(a):
    if len(a) < 2: print(__doc__); return 2
    kind, root = a[0], a[1]; cut = iso(a[2]) if len(a) > 2 else None
    for p in (os.path.abspath(root), os.path.realpath(root)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)): raise SystemExit("REFUSED: HELDOUT_ path")
    acc = collections.defaultdict(Acc)
    if kind == "book": fl = files(root, r"^book\.csv\.gz$"); tcol, kcol, bid, nob = "t_recv_ms", "series", "yes_bid_px_1", "no_bid_px_1"
    elif kind == "bookl": fl = files(root, r"^book\.csv\.gz$"); tcol, kcol, bid, nob = "poll_ts_local_ms", "ticker", "yes_bid_px_1", "no_bid_px_1"
    elif kind == "quotes": fl = files(root, r"^quotes\.csv\.gz$"); tcol, kcol, bid, nob = "t_recv_ms", "ticker", "yes_bid", "yes_ask"
    elif kind == "polrec": fl = files(root, r"^quotes\.csv\.gz$"); tcol, kcol, bid, nob = "t_recv_ms", "series", "yes_bid", "yes_ask"
    elif kind == "combo": fl = files(root, r"^quotes\.csv\.gz$"); tcol, kcol, bid, nob = "t_recv_ms", "exchange_index", "yes_bid", "yes_ask"
    elif kind == "ingame": fl = files(root, r"^obs\.csv\.gz$"); tcol, kcol, bid, nob = "t_recv_ms", "kind", "yes_bid", "yes_ask"
    elif kind == "dailyq": fl = files(root, r"\.csv\.gz$"); tcol, kcol, bid, nob = "poll_ts", "series", "yes_bid", "yes_ask"
    elif kind == "perps30": fl = files(root, r"\.csv(\.gz)?$"); tcol, kcol, bid, nob = "ts_utc", "asset_class", "bid", "ask"
    elif kind == "kalshi1m": fl = files(root, r"\.csv\.gz$"); tcol, kcol, bid, nob = "end_period_ts", "ticker", "bid_close", "ask_close"
    else: raise SystemExit("unknown kind")
    for p in fl:
        r = csv.reader(opener(p)); h = next(r, None)
        if not h or tcol not in h: continue
        it, ik, ib, ia = h.index(tcol), (h.index(kcol) if kcol in h else None), h.index(bid), h.index(nob)
        ic = h.index("close_time") if "close_time" in h else None
        last_by = {}; fmin = {}; fmax = {}; fgaps = collections.defaultdict(list)
        for row in r:
            if cut is not None and ic is not None:
                ct = iso(row[ic])
                if ct is not None and ct >= cut: acc[row[ik] if ik is not None else "all"].skipped += 1; continue
            try:
                t = float(row[it]) / (1000.0 if kind in ("book", "bookl", "quotes", "polrec", "combo", "ingame") else 1.0) if re.match(r"^\d+(\.\d+)?$", row[it]) else iso(row[it])
            except ValueError: t = None
            if t is None: continue
            k = row[ik] if ik is not None else "all"
            if kind in ("bookl", "quotes"): k = k.split("-")[0]          # the series, so a gap is a stop of the whole series' recording
            if kind == "quotes" and cut is not None and t >= cut: acc[k].skipped += 1; continue
            if kind == "bookl" and cut is not None and ic is not None: pass
            A = acc[k]; A.n += 1; A.files.add(p)
            vb, va = cents(row[ib]), cents(row[ia])
            if kind in ("book", "bookl"): two = vb is not None and va is not None and vb > 0 and va > 0 and vb + va < 100
            elif kind in ("perps30", "kalshi1m"):
                fb, fa = (float(row[ib]) if row[ib] not in ("", None) else 0.0), (float(row[ia]) if row[ia] not in ("", None) else 0.0)
                two = fb > 0 and fa > 0 and fb < fa
            else: two = vb is not None and va is not None and 0 < vb < va < 100
            if two: A.two += 1
            if k in last_by and t - last_by[k] > GAP_S: fgaps[k].append(t - last_by[k])
            last_by[k] = t; fmin[k] = min(fmin.get(k, t), t); fmax[k] = max(fmax.get(k, t), t)
        for k in fmin: acc[k].spans.append((fmin[k], fmax[k], fgaps[k]))
    print("kind", kind, "| files read", len(fl), "| cut", a[2] if len(a) > 2 else "none")
    for k in sorted(acc, key=str):
        A = acc[k]
        if not A.spans: print("%-16s rows 0 skipped_by_cut %d" % (k, A.skipped)); continue
        spans = sorted(A.spans); gaps = []; end = None
        for s, e, g in spans:
            gaps += g
            if end is not None and s - end > GAP_S: gaps.append(s - end)
            end = e if end is None else max(end, e)
        first = datetime.fromtimestamp(spans[0][0], timezone.utc).strftime("%Y-%m-%dT%H:%MZ"); last = datetime.fromtimestamp(end, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        print("%-16s files %3d rows %9d first %s last %s two_sided %9d (%.1f%%) gaps_over_30min %d longest %.1f h skipped_by_cut %d" % (
            k, len(A.files), A.n, first, last, A.two, 100.0 * A.two / A.n if A.n else 0.0, len(gaps), (max(gaps) / 3600.0 if gaps else 0.0), A.skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
