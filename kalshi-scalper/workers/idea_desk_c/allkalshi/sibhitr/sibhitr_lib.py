#!/usr/bin/env python3
"""SIBHIT-R shared code (Idea Desk C, Nov 16, 2026). Card: SIBHITR_CARD.md (with Amendments 1 and 2).
The clock, base, pace share, clock check and S_MED are SIBHIT's, imported unchanged from ../sibhit/sibhit_lib.py.
Only the list source, the window and the side differ: FAST (s >= S_MED) buys NO, SLOW buys YES."""
import gzip, json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sibhit"))
import sibhit_lib as B

SERIES = "KXNBAPTS"
WIN = (1772323200, 1776124800)          # close_time from 2026-03-01T00:00Z to before 2026-04-14T00:00Z (Amendment 1)
LIST_JOB, LIST_ID = "SIBHITR_LISTS_A", "hist_KXNBAPTS"
CANDLE_JOB = "SIBHITR_CANDLES"
S_MED, BAND, EPS, LOOKBACK_S = B.S_MED, B.BAND, B.EPS, B.LOOKBACK_S
import hashlib
SEED, N_READ = "SIBHITR-2026-11-16", 40   # Amendment 2 (the Head, Nov 16 15:26Z): first 40 games by md5 are read; the rest are SIBHIT-R's held-out
_games_all = B.games                     # SIBHIT's own function: base, share, clock check, arm (HIGH = fast, LOW = slow)


def order(g):
    return sorted(g, key=lambda e: (hashlib.md5((SEED + e).encode("ascii")).hexdigest(), e))


def games(rows, part="read"):
    """part 'read': the first N_READ games by md5; 'heldout': the rest (pulled only after a pass)."""
    g = _games_all(rows)
    o = order(g)
    keep = o[:N_READ] if part == "read" else o[N_READ:]
    return {e: g[e] for e in keep}


def bodies(root, job, rid=None):
    base = os.path.join(root, "pull", job)
    for run in sorted(os.listdir(base)):
        with open(os.path.join(base, run, "manifest.json")) as fh:
            man = json.load(fh)
        for r in man["rows"]:
            fn = r.get("file")
            if not fn or os.path.basename(fn) != fn or (rid and r.get("id") != rid):
                continue
            with gzip.open(os.path.join(base, run, fn), "rt") as fh:
                b = json.load(fh)
            if isinstance(b, dict):
                yield r, b


def truncated(root):
    """True when the window may be incomplete: the last stored page still has a cursor AND its earliest close_time is not before the
    window start. The historical list comes newest first by close time, so a last page reaching before WIN[0] covers the whole window
    (Amendment 5, Nov 16, time fields only)."""
    last = {}
    for r, b in bodies(root, LIST_JOB, LIST_ID):
        if "markets" in b:
            closes = [B.iso(m.get("close_time")) for m in b.get("markets") or []]
            closes = [c for c in closes if c is not None]
            last[(r.get("page") or 0)] = (b.get("cursor") or "", min(closes) if closes else None)
    if not last:
        return True
    cur, earliest = last[max(last)]
    if not cur:
        return False
    return earliest is None or earliest >= WIN[0]


def list_rows(root):
    """(ticker, event, close, occurrence) for window markets. close_time is tested FIRST; nothing else is parsed for a market outside."""
    out = []
    for _r, b in bodies(root, LIST_JOB, LIST_ID):
        for m in b.get("markets") or []:
            c = B.iso(m.get("close_time"))
            if c is None or not (WIN[0] <= c < WIN[1]):
                continue
            t = m.get("ticker") or ""
            o = B.iso(m.get("occurrence_datetime"))
            if t.split("-")[0] != SERIES or o is None:
                continue
            out.append((t, m.get("event_ticker") or "", c, o))
    return out


def fee(p):
    return math.ceil(round(0.07 * p * (1 - p) * 100, 9)) / 100
