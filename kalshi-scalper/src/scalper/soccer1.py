"""SOCCER1: Kalshi soccer cheap side vs DraftKings (via ESPN core odds), de-vigged. Held to settlement.

Registration: workers/SOCCER1_REGISTRATION.md.  Cheap side only (ask 3c-30c): no favourite-side result is computed.
Frozen W3 (start from 2026-10-03T16:00Z) is never fetched or joined.  Cache outside the repo (SOCCER1_CACHE).
Usage: python -m scalper.soccer1 census|probe   (outcome-free steps); later steps are added after registration.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CACHE = Path(os.environ.get("SOCCER1_CACHE", "/tmp/soccer1"))
W3_START = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LO_TS = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp())
LO, HI, RATIO, C, LEAD, MAXQ = 0.03, 0.30, 3.0, 10, 120, 0.10
UA = "research-bot SOCCER1 (kalshi research)"
# kalshi series prefix -> espn league slug
LEAGUES = {"EPL": "eng.1", "LALIGA": "esp.1", "SERIEA": "ita.1", "BUNDESLIGA": "ger.1", "LIGUE1": "fra.1",
           "UCL": "uefa.champions", "UEL": "uefa.europa", "UECL": "uefa.europa.conf", "MLS": "usa.1",
           "EFLCHAMPIONSHIP": "eng.2", "EREDIVISIE": "ned.1", "LIGAPORTUGAL": "por.1", "LIGAMX": "mex.1"}
FAMS = ("GAME", "TOTAL", "BTTS", "SPREAD")


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def implied(american):
    a = float(american)
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


def devig3(h, d, a):
    """Proportional de-vig of a three-way moneyline (American odds)."""
    ps = [implied(h), implied(d), implied(a)]
    s = sum(ps)
    return [p / s for p in ps]


def devig2(over, under):
    po, pu = implied(over), implied(under)
    return po / (po + pu)


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= MAXQ


def look(cands, start):
    ts = [t for t, q in cands.items() if t <= start - LEAD and valid(q)]
    return cands[max(ts)] if ts else None


def cheap_side(q):
    bid, ask = q
    if LO <= ask <= HI:
        return "Y", ask
    if LO <= 1 - bid <= HI:
        return "N", 1 - bid
    return None


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def http(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(5):
        try:
            with urllib.request.urlopen(r, timeout=20) as f:
                return json.load(f)
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def census():
    """Listings and close times only: settled soccer markets closing before the frozen cut, by league and family. No results kept."""
    from . import api
    out = CACHE / "census.json"
    have = json.load(open(out)) if out.exists() else {}
    for pre in LEAGUES:
        for fam in FAMS:
            ser = f"KX{pre}{fam}"
            if ser in have:
                continue
            ev, n = {}, 0
            for m in api.settled_markets(ser, LO_TS, W3_START):
                n += 1
                ev.setdefault(m["event_ticker"], m.get("close_time"))
            have[ser] = dict(markets=n, events=ev)
            json.dump(have, open(out, "w"))
            print(ser, n, len(ev), flush=True)
            time.sleep(0.5)
    tot = defaultdict(int)
    for ser, v in have.items():
        pre = ser[2:].rsplit("GAME", 1)[0] if ser.endswith("GAME") else None
    for pre in LEAGUES:
        g = have.get(f"KX{pre}GAME", {})
        print(pre, "match events", len(g.get("events", {})), {f: have.get(f"KX{pre}{f}", {}).get("markets") for f in FAMS})


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    import sys
    globals()[sys.argv[1]]()
