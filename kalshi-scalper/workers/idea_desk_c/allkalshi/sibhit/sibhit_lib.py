#!/usr/bin/env python3
"""SIBHIT: shared code for the design count, the stage B job builder and the scorer (Idea Desk C, Nov 15, 2026). Standard library only, no network.

Card: SIBHIT_CARD.md. A KXNBAPTS rung closes the moment it is hit, so the number of rungs of one game already closed is a live pace count.
At T = occurrence - 60 min: share s = rungs closed after occurrence - 180 min and strictly before T - 240 s / rungs still open at occurrence - 180 min.
HIGH (s >= S_MED): buy YES on every rung still open after T with YES ask 0.30 to 0.70. LOW (s < S_MED): buy NO on every open rung with NO ask 0.30 to 0.70.
Held to settlement. S_MED is the median of s over the 120 development games, computed from close times alone before any price was pulled.
"""
import calendar, gzip, json, math, os, time

SERIES = "KXNBAPTS"
DEV = ("2026-10-21T00:00:00", "2026-11-06T00:00:00")     # close_time window; Nov 6 to 13 is PROPUNDER's reserve, never pulled
A_MIN, T_MIN = 180, 60
COUNT_LEAD_S = 240                                       # the count uses closes strictly before T - 240 s, the start of the earliest allowed entry candle (Head, Nov 15)
S_MED = 0.07362240289069558                              # median over 120 dev games of the strict count (time fields only, Nov 15 ~21:30Z; was 0.0818 with closes <= T)
BAND = (0.30, 0.70)
MIN_BASE = 10
LOOKBACK_S = 180                                         # candle at T, else the latest ending in [T - 180 s, T]
EPS = 1e-9


def iso(s):
    s = (s or "").split(".")[0].rstrip("Z")
    try:
        return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def list_rows(root):
    """Stage A list answers: (ticker, event, close, occurrence) for KXNBAPTS in the dev window. Time fields only."""
    lo, hi = iso(DEV[0]), iso(DEV[1])
    out = []
    base = os.path.join(root, "pull", "KXNBAPTS_LISTS_A")
    for run in sorted(os.listdir(base)):
        man = json.load(open(os.path.join(base, run, "manifest.json")))
        for r in man["rows"]:
            fn = r.get("file")
            if not fn or r.get("id") != "dev_KXNBAPTS":
                continue
            with gzip.open(os.path.join(base, run, fn), "rt") as fh:
                for m in json.load(fh).get("markets") or []:
                    t = m.get("ticker") or ""
                    c, o = iso(m.get("close_time")), iso(m.get("occurrence_datetime"))
                    if t.split("-")[0] != SERIES or c is None or o is None or not (lo <= c < hi):
                        continue
                    out.append((t, m.get("event_ticker") or "", c, o))
    return out


def games(rows):
    """event -> dict(T, s, arm, open tickers). Time fields only."""
    ev = {}
    for t, e, c, o in rows:
        ev.setdefault(e, []).append((t, c, o))
    out = {}
    for e, L in sorted(ev.items()):
        occ = min(o for _, _, o in L)
        A, T = occ - A_MIN * 60, occ - T_MIN * 60
        base = [x for x in L if x[1] > A]
        if len(base) < MIN_BASE:
            continue
        hits = sum(1 for x in base if x[1] < T - COUNT_LEAD_S)
        s = hits / len(base)
        out[e] = {"T": T, "s": s, "arm": "HIGH" if s >= S_MED - EPS else "LOW", "open": sorted(x[0] for x in base if x[1] > T),
                  "close": {x[0]: x[1] for x in base}}
    return out


def fee(p):
    return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100
