#!/usr/bin/env python3
"""EXITREPLAY1 gold hold: haircut recompute, build 1 (Idea Desk C, Nov 15, 2026; the Head of R&D's assignment of 14:31Z).

Independent of Forensics' exitreplay1.py: written from that file's printed rule, using the standard library only.
The rule and every constant are in HAND_CASE.md (committed first, d487b1a99).
Reads only R6's book15r6/*/*/coverage.csv.gz (close_time, series, ticker, max_gap_ms, result) and book.csv.gz (t_recv_ms, ticker,
yes_bid_px_1, no_bid_px_1), for KXGOLD15M windows closing from 2026-10-29T00:00Z to before CUT (S-HOLDVSSELL's held-out start).
A window at or after CUT is counted and never read (its book rows are not loaded). No network. Prints JSON.

Usage: python3 -I egh.py <root holding book15r6/>
"""
import csv
import gzip
import json
import math
import os
import sys
import calendar
import time

SERIES = "KXGOLD15M"
EPS = 1e-9
LOOK_S, LOOK_TOL_S = 360, 10
BAND = (0.88, 0.97)
MAX_GAP_MS = 15000
LABEL = "book replay, upper bound on queue; upper bound, not fill-checked"


def ms(iso):
    return calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")) * 1000


FROM_MS, CUT_MS = ms("2026-10-29T00:00:00Z"), ms("2026-11-07T20:24:00Z")


def fee(p):
    """Per order, rounded up to the cent, 1 contract."""
    return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def runs(root):
    base = os.path.join(root, "book15r6")
    out = []
    for day in sorted(os.listdir(base)):
        dp = os.path.join(base, day)
        if os.path.isdir(dp):
            out += [os.path.join(dp, r) for r in sorted(os.listdir(dp)) if os.path.isdir(os.path.join(dp, r))]
    return out


def pf(xs):
    w = sum(x for x in xs if x > EPS)
    l = -sum(x for x in xs if x < -EPS)
    if not xs:
        return None
    return "inf" if l == 0 else round(w / l, 4)


def main(root):
    wins = {}
    listed, cut = set(), set()
    rd = runs(root)
    for r in rd:
        f = os.path.join(r, "coverage.csv.gz")
        if not os.path.exists(f):
            continue
        with gzip.open(f, "rt", newline="") as fh:
            for c in csv.DictReader(fh):
                if c.get("series") != SERIES or not c.get("ticker"):
                    continue
                close = ms(c["close_time"])
                if not (FROM_MS <= close < ms("2026-11-09T00:00:00Z")):
                    continue
                t = c["ticker"]
                listed.add(t)
                if close >= CUT_MS:          # held out for S-HOLDVSSELL: counted, its result and gap never read
                    cut.add(t)
                    continue
                w = wins.setdefault(t, {"close": close, "gap": 0, "result": ""})
                w["gap"] = max(w["gap"], int(num(c.get("max_gap_ms")) or 0))
                res = (c.get("result") or "").strip().lower()
                if res in ("yes", "no") and not w["result"]:
                    w["result"] = res
    counts = {"listed": len(listed), "cut_dropped": len(cut), "dropped_no_result": 0, "dropped_gap": 0, "no_look": 0, "no_band": 0, "entries": 0}
    keep = {}
    for t, w in wins.items():
        if w["result"] not in ("yes", "no"):
            counts["dropped_no_result"] += 1
            continue
        if w["gap"] > MAX_GAP_MS:
            counts["dropped_gap"] += 1
            continue
        keep[t] = w
    rows = {t: {} for t in keep}
    for r in rd:
        f = os.path.join(r, "book.csv.gz")
        if not os.path.exists(f):
            continue
        with gzip.open(f, "rt", newline="") as fh:
            for b in csv.DictReader(fh):
                t = b.get("ticker")
                if t in rows:
                    ts = int(float(b["t_recv_ms"]))
                    rows[t].setdefault(ts, (num(b.get("yes_bid_px_1")), num(b.get("no_bid_px_1"))))
    entries = []
    for t, w in keep.items():
        T = w["close"]
        look = None
        for ts in sorted(rows[t]):
            yb, nb = rows[t][ts]
            if yb is None or nb is None or not (yb < 1 - nb - EPS) or ts >= T:
                continue
            if T - (LOOK_S + LOOK_TOL_S) * 1000 <= ts <= T - LOOK_S * 1000:
                look = (yb, nb)
        if look is None:
            counts["no_look"] += 1
            continue
        yb, nb = look
        ya, na = round(1 - nb, 6), round(1 - yb, 6)
        if BAND[0] - EPS <= ya <= BAND[1] + EPS:
            side, ask = "yes", ya
        elif BAND[0] - EPS <= na <= BAND[1] + EPS:
            side, ask = "no", na
        else:
            counts["no_band"] += 1
            continue
        won = w["result"] == side
        res = {}
        for k, h in (("raw", 0.0), ("1c", 0.01), ("2c", 0.02)):
            a = round(ask + h, 6)
            res[k] = round((1 - a - fee(a)) if won else -(a + fee(a)), 4)
        entries.append({"ticker": t, "close": T, "side": side, "ask": ask, "won": won, **res})
    counts["entries"] = len(entries)
    entries.sort(key=lambda e: (e["close"], e["ticker"]))
    n = len(entries)
    h = n // 2
    out = {"label": LABEL, "cut": "closes before 2026-11-07T20:24Z (S-HOLDVSSELL held-out start)", "counts": counts}
    for k in ("raw", "1c", "2c"):
        xs = [e[k] for e in entries]
        out[k] = {"n": n, "pf": pf(xs), "half1": pf(xs[:h]), "half2": pf(xs[h:]), "net": round(sum(xs), 4)}
    v = lambda x: float("inf") if x == "inf" else (x or 0.0)
    ok = v(out["1c"]["pf"]) >= 1.3 and v(out["1c"]["half1"]) >= 1.0 and v(out["1c"]["half2"]) >= 1.0 and v(out["2c"]["pf"]) >= 1.0
    out["bar"] = "meets the bar (counting only)" if ok else "does not count: fails the haircut"
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
