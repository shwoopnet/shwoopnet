"""BOOKS2: Kalshi total and spread ladders, far cheap strikes, vs a normal around the DraftKings close line. Held to settlement.

Registration: workers/BOOKS2_REGISTRATION.md.  Cheap side only: no favourite-side result is computed.
Frozen W3 (start from 2026-10-03T16:00Z) is never fetched or joined.
Usage: python -m scalper.books2 scores|markets|candles|score   (cache dir in BOOKS2_CACHE, outside the repo)
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "espn1.sqlite"
ODDS = Path(os.environ.get("BOOKS1_CACHE", "/tmp/books1"))
CACHE = Path(os.environ.get("BOOKS2_CACHE", "/tmp/books2"))
W3_START = int(datetime(2026, 10, 3, 16, tzinfo=timezone.utc).timestamp())
LO, HI, RATIO, C, LEAD, MAXQ = 0.03, 0.30, 3.0, 10, 120, 0.10
PRIOR_SD = {("T", "KXNCAAFGAME"): 14.0, ("T", "KXNFLGAME"): 10.0, ("T", "KXMLBGAME"): 3.2,
            ("S", "KXNCAAFGAME"): 16.0, ("S", "KXNFLGAME"): 13.0, ("S", "KXMLBGAME"): 3.3}
KSER = {"KXNCAAFGAME": ("KXNCAAFTOTAL", "KXNCAAFSPREAD"), "KXNFLGAME": ("KXNFLTOTAL", "KXNFLSPREAD"), "KXMLBGAME": ("KXMLBTOTAL", "KXMLBSPREAD")}
ESPN = {"KXNCAAFGAME": "football/college-football", "KXNFLGAME": "football/nfl", "KXMLBGAME": "baseball/mlb"}
UA = "research-bot BOOKS2 (kalshi research)"


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def net(win, ask, mult=1.0):
    return (1.0 if win else 0.0) - ask - mult * fee(ask) / C


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def valid(q):
    return q is not None and 0 <= q[0] < q[1] <= 1 and q[1] - q[0] <= MAXQ


def look(cands, start):
    """Last (bid, ask) of a candle ending at or before start - LEAD that is valid, else None."""
    ts = [t for t, q in cands.items() if t <= start - LEAD and valid(q)]
    return cands[max(ts)] if ts else None


def cheap_side(q):
    """('Y'|'N', ask) for the side with ask in [LO, HI], else None."""
    bid, ask = q
    if LO <= ask <= HI:
        return "Y", ask
    if LO <= 1 - bid <= HI:
        return "N", 1 - bid
    return None


def p_total_over(k, line, sd):
    return 1 - phi((k - line) / sd)


def p_margin_over(k, mu, sd):
    """P(margin > k) for margin ~ Normal(mu, sd); k in points, margin of the named team."""
    return 1 - phi((k - mu) / sd)


def side_prob(side, p_yes):
    return p_yes if side == "Y" else 1 - p_yes


def fit_sd(res):
    """RMS of residuals."""
    return math.sqrt(sum(r * r for r in res) / len(res)) if res else None


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf")


def pick_treated(rows, maxper=2):
    """rows of one game and family: dicts with ask, p. Eligible p >= RATIO*ask; two largest p/ask (ties lower ask)."""
    el = [r for r in rows if r["p"] >= RATIO * r["ask"]]
    el.sort(key=lambda r: (-r["p"] / r["ask"], r["ask"]))
    return el[:maxper]


def zstat(per):
    """t-like z of the mean of per-cluster sums (list of floats)."""
    n = len(per)
    if n < 3:
        return None
    m = sum(per) / n
    v = sum((x - m) ** 2 for x in per) / (n - 1)
    return m / math.sqrt(v / n) if v > 0 else None


# ---------------------------------------------------------------- data

def games():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    return c.execute("""select e.series,e.id,e.start_ts,m.event,e.home_id,e.away_id from match m
        join egame e on e.id=m.egame and e.series=m.series where e.start_ts<?""", (W3_START,)).fetchall()


def dk_lines(gid):
    """(overUnder, home_spread) from the cached odds item with both, else None."""
    try:
        d = json.load(open(ODDS / f"{gid}.json"))
    except Exception:
        return None
    for it in d.get("items", []):
        o, s = it.get("overUnder"), it.get("spread")
        if o and s is not None:
            return float(o), float(s)
    return None


def http(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(5):
        try:
            with urllib.request.urlopen(r, timeout=20) as f:
                return json.load(f)
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def fetch_scores():
    out = CACHE / "scores.json"
    have = json.load(open(out)) if out.exists() else {}
    gs = games()
    want = defaultdict(set)
    for s, gid, st, ev, h, a in gs:
        if dk_lines(gid):
            d = datetime.fromtimestamp(st - 6 * 3600, timezone.utc).date()  # US evening games belong to the previous US date
            for dd in (d, datetime.fromtimestamp(st, timezone.utc).date()):
                want[(s, dd.strftime("%Y%m%d"))].add(gid)
    for (s, ds), ids in sorted(want.items()):
        if all(g in have for g in ids):
            continue
        extra = "&groups=80" if s == "KXNCAAFGAME" else ""
        d = http(f"https://site.api.espn.com/apis/site/v2/sports/{ESPN[s]}/scoreboard?dates={ds}&limit=400{extra}")
        time.sleep(1.0)
        if not d:
            continue
        for ev in d.get("events", []):
            comp = ev["competitions"][0]
            sc = {c["homeAway"]: c.get("score") for c in comp["competitors"]}
            if comp["status"]["type"].get("completed") and sc.get("home") is not None and sc.get("away") is not None:
                have[ev["id"]] = [int(float(sc["home"])), int(float(sc["away"]))]
        json.dump(have, open(out, "w"))
    json.dump(have, open(out, "w"))
    print("scores for", len(have), "events")


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == "scores":
        fetch_scores()
    else:
        from . import books2_run
        getattr(books2_run, cmd)()
