"""HRSEAS1: hour-of-day / day-of-week seasonality of the cheap tail on the HOURLY Bitcoin ladder KXBTCD (research only).

Rule and bars: workers/HRSEAS1_REGISTRATION.md. Nothing here may change after the first outcome.
    python -m scalper.hrseas1 run     development window only (closes before cut2); the last third is never computed.
                                      Refuses a second run (data/hrseas1_score.json).
"""
from __future__ import annotations

import datetime
import json
import math
import os
import sqlite3
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data")
LAD = os.path.join(DATA, "conf2_lad.sqlite")
OUT = os.path.join(DATA, "hrseas1_score.json")
LEAD = 1500            # look: 25 minutes before the hourly close
LO, HI = 0.03, 0.30    # tail band at the look; hard fill limit HI
FLO, FHI = 0.85, 0.97  # favourite band (mirror); hard fill limit FHI
FTARGET = 0.90
MIN_N = 150
C = 10

# Blocks by the UTC hour of the CLOSE (fixed before any outcome). WEEKEND is by UTC weekday of the close.
BLOCKS = {
    "ASIA_OPEN": lambda h, wd: h in (0, 1, 2),
    "NIGHT_LULL": lambda h, wd: h in (3, 4, 5, 6),
    "LONDON_OPEN": lambda h, wd: h in (7, 8, 9),
    "US_OPEN": lambda h, wd: h in (13, 14, 15),
    "US_CLOSE": lambda h, wd: h in (19, 20, 21),
    "FUNDING": lambda h, wd: h in (0, 8, 16),
    "WEEKEND": lambda h, wd: wd in (5, 6),
}
MIRROR_BLOCKS = ("NIGHT_LULL", "WEEKEND")


def fee(p, c):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100.0


def block_names(close_ts):
    d = datetime.datetime.fromtimestamp(close_ts, datetime.timezone.utc)
    return [b for b, f in BLOCKS.items() if f(d.hour, d.weekday())]


def pick(look, kind):
    """look: list of (ticker, yes_bid, yes_ask) from the candle ending at the look.
    kind 'tail': per side the price nearest the money inside [LO, HI] (highest price). 'fav': per side the price nearest FTARGET inside [FLO, FHI].
    Returns list of (ticker, side). At most one per side."""
    out = []
    for side in ("yes", "no"):
        best = None
        for tk, b, a in look:
            if b is None or a is None or not (0 < a < 1) or not (0 < b < 1):
                continue
            p = a if side == "yes" else 1 - b
            if kind == "tail":
                if LO <= p <= HI and (best is None or p > best[0]):
                    best = (p, tk)
            else:
                if FLO <= p <= FHI and (best is None or abs(p - FTARGET) < abs(best[0] - FTARGET)):
                    best = (p, tk)
        if best:
            out.append((best[1], side))
    return out


def fill_and_pnl(side, fillq, result, kind):
    """fillq: (yes_bid, yes_ask) of the candle ENDING one minute after the look. Returns (price, pnl10, won) or None (no fill)."""
    if fillq is None or fillq[0] is None or fillq[1] is None:
        return None
    b, a = fillq
    if not (0 < a < 1 and 0 < b < 1):
        return None
    p = a if side == "yes" else 1 - b
    limit = HI if kind == "tail" else FHI
    if p > limit or p < 0.01:
        return None
    won = (result == "yes") == (side == "yes")
    return p, (C if won else 0.0) - C * p - fee(p, C), won


def load_events():
    db = sqlite3.connect(LAD)
    rows = db.execute("select ticker, close_ts, result from market where series='KXBTCD'").fetchall()
    ev = {}
    for tk, ct, res in rows:
        if res in ("yes", "no"):
            ev.setdefault(ct, []).append((tk, res))
    return db, ev


def q_at(db, tk, t):
    r = db.execute("select bid_c, ask_c from candle where ticker=? and end_ts=?", (tk, t)).fetchone()
    return (r[0], r[1]) if r else None


def trades_for_close(db, ct, mk):
    t = ct - LEAD
    out = []
    looks = []
    resmap = {}
    for tk, res in mk:
        q = q_at(db, tk, t)
        resmap[tk] = res
        if q and q[0] is not None and q[1] is not None:
            looks.append((tk, q[0], q[1]))
    if len(looks) < 4:   # a ladder that did not print is not a ladder
        return out
    for kind in ("tail", "fav"):
        for tk, side in pick(looks, kind):
            r = fill_and_pnl(side, q_at(db, tk, t + 60), resmap[tk], kind)
            if r:
                p, pn, won = r
                out.append({"close": ct, "kind": kind, "side": side, "price": p, "won": won,
                            "pnl10": pn, "pnl10x": pn - 0.2 * fee(p, C), "pnl1": (1.0 if won else 0.0) - p - fee(p, 1)})
    return out


def stats(tr):
    n = len(tr)
    if n == 0:
        return {"n": 0}
    g = sum(x["pnl10"] for x in tr if x["pnl10"] > 0)
    l = -sum(x["pnl10"] for x in tr if x["pnl10"] < 0)
    g2 = sum(x["pnl10x"] for x in tr if x["pnl10x"] > 0)
    l2 = -sum(x["pnl10x"] for x in tr if x["pnl10x"] < 0)
    return {"n": n, "win": sum(1 for x in tr if x["won"]) / n, "price": float(np.mean([x["price"] for x in tr])),
            "net": float(np.mean([x["pnl10"] for x in tr])) / C,
            "pf": g / l if l > 0 else float("inf"), "pfx": g2 / l2 if l2 > 0 else float("inf"),
            "closes": len({x["close"] for x in tr})}


def boot_diff(a, b, rng, n=2000):
    ga, gb = {}, {}
    for x in a:
        ga.setdefault(x["close"], []).append(x["pnl10"])
    for x in b:
        gb.setdefault(x["close"], []).append(x["pnl10"])
    if not ga or not gb:
        return None
    va = np.array([np.mean(v) for v in ga.values()]); vb = np.array([np.mean(v) for v in gb.values()])
    d = [rng.choice(va, len(va)).mean() - rng.choice(vb, len(vb)).mean() for _ in range(n)]
    return float(va.mean() - vb.mean()) / C, float(np.percentile(d, 5)) / C, float(np.percentile(d, 95)) / C


def verdict(block, kind, sA, sB, dA, dB):
    """sA/sB: stats of the block in half 1/2; dA/dB: block-minus-control net per contract in half 1/2 (None if unavailable)."""
    n = sA.get("n", 0) + sB.get("n", 0)
    kill = (sA.get("n", 0) == 0 or sB.get("n", 0) == 0 or sA["pf"] < 1.5 or sB["pf"] < 1.5
            or dA is None or dB is None or not (dA > 0 and dB > 0))
    if n < MIN_N:
        return "NOT_ENOUGH_DATA (n=%d under %d)%s" % (n, MIN_N, "; kill rule already fires" if kill else "")
    return "FALSIFIED" if kill else "PASS_DEVELOPMENT (needs W3)"


def run():
    if os.path.exists(OUT):
        raise SystemExit("already scored once (%s); no second run" % OUT)
    db, ev = load_events()
    closes = sorted(ev)
    T0, T1 = closes[0], closes[-1]
    cut1 = T0 + (T1 - T0) // 3
    cut2 = T0 + 2 * (T1 - T0) // 3
    dev = [x for x in closes if x < cut2]          # closes at or after cut2 are never touched
    rows = []
    for ct in dev:
        for t in trades_for_close(db, ct, ev[ct]):
            t["half"] = 1 if ct < cut1 else 2
            t["blocks"] = block_names(ct)
            rows.append(t)
    rng = np.random.default_rng(12345)
    lines = ["HRSEAS1 development read: closes %d..%d (dev n=%d of %d), cut1 %d cut2 %d; closes >= cut2 NOT computed" % (T0, T1, len(dev), len(closes), cut1, cut2)]
    res = {"cut1": cut1, "cut2": cut2, "dev_closes": len(dev)}
    for kind in ("tail", "fav"):
        base = [x for x in rows if x["kind"] == kind]
        lines.append("BASELINE %s all hours: %s" % (kind, stats(base)))
        for h in (1, 2):
            lines.append("  baseline h%d: %s" % (h, stats([x for x in base if x["half"] == h])))
        for b in BLOCKS:
            if kind == "fav" and b not in MIRROR_BLOCKS:
                continue
            inb = [x for x in base if b in x["blocks"]]
            ctl = [x for x in base if b not in x["blocks"]]
            sh, dd = {}, {}
            for h in (1, 2):
                a = [x for x in inb if x["half"] == h]; c = [x for x in ctl if x["half"] == h]
                sh[h] = stats(a)
                bd = boot_diff(a, c, rng)
                dd[h] = bd[0] if bd else None
                lines.append("  [%s %s h%d] %s | control %s | diff %s" % (kind, b, h, sh[h], stats(c), bd))
            allb = stats(inb)
            v = verdict(b, kind, sh[1], sh[2], dd[1], dd[2])
            lines.append("  [%s %s] ALL %s -> %s" % (kind, b, allb, v))
            res["%s/%s" % (kind, b)] = {"all": allb, "h1": sh[1], "h2": sh[2], "diff1": dd[1], "diff2": dd[2], "verdict": v}
    out = "\n".join(lines)
    print(out)
    with open(OUT, "w") as f:
        json.dump(res, f, default=str)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()


W3_OUT = os.path.join(DATA, "hrseas1_w3.json")


def run_w3():
    """Registered section 8: only a slot that PASSED development is read on the frozen last third, once. Only fav/WEEKEND passed."""
    if os.path.exists(W3_OUT):
        raise SystemExit("W3 already read once")
    with open(OUT) as f:
        dev = json.load(f)
    passed = [k for k, v in dev.items() if isinstance(v, dict) and str(v.get("verdict", "")).startswith("PASS")]
    assert passed == ["fav/WEEKEND"], passed
    db, ev = load_events()
    closes = [x for x in sorted(ev) if x >= dev["cut2"]]
    rows = []
    for ct in closes:
        for t in trades_for_close(db, ct, ev[ct]):
            t["blocks"] = block_names(ct)
            rows.append(t)
    fav = [x for x in rows if x["kind"] == "fav"]
    inb = [x for x in fav if "WEEKEND" in x["blocks"]]
    ctl = [x for x in fav if "WEEKEND" not in x["blocks"]]
    rng = np.random.default_rng(12345)
    res = {"closes": len(closes), "weekend": stats(inb), "control": stats(ctl), "diff": boot_diff(inb, ctl, rng)}
    print(json.dumps(res, default=str))
    with open(W3_OUT, "w") as f:
        json.dump(res, f, default=str)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "w3":
    run_w3()
