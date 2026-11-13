#!/usr/bin/env python3
"""NHLOT price measurement, SECOND BUILD (History Miner, Nov 13, 2026), from the text only: IDEA_DESK_B_WAVE3.md (claude/idea-desk-b 5d1ead7d, sha256 71fac71b...), the six sections named by
nhlot/INPUT_LAYOUT.md, the later one right where they differ. Desk B's measure_prices.py, fixture_outputs/ and build_candles_job.py are NOT read. Zero tries, no outcome read, no result field.
Usage: python3 -I nhlot2.py <candle run folder> <games.json>"""
import gzip, hashlib, json, os, statistics, sys

LABEL = "hindsight window: detection uses the close time; upper bound, not a live rule"
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on these markets"
TOL = 1e-9
WINDOW_S = 45 * 60
FIRST5_S = 5 * 60
DECIDED_HI, DECIDED_LO = 0.93, 0.07           # 00:16Z: exactly 0.93 or 0.07 counts as decided
ML_LO, ML_HI = 0.30, 0.70                     # inclusive
MIN_QUOTED_STRIKES = 4
ASK_MAX, SPREAD_MAX = 0.43, 0.03
MIN_DET = 30
FIRE_LO, FIRE_HI = 0.12, 0.35                 # inclusive
SHARE_MIN = 0.30                              # exactly 30% is NOT closed
PRICE_LINES = (0.40, 0.43, 0.45, 0.47)


def refuse_heldout(p):
    for q in (os.path.abspath(p), os.path.realpath(p)):
        if any(c.upper().startswith("HELDOUT") for c in q.split(os.sep)):
            raise SystemExit("refused: %s is a held-out path" % p)


def load_candles(folder):
    """{ticker: {end_period_ts: (bid or None, ask or None)}} from the run's MANIFEST rows (not by file name). The run must be complete and every job request answered at 200;
    a stored file is checked against sha256 and bytes when the manifest carries them; every file must lie inside the run folder."""
    refuse_heldout(folder)
    root = os.path.realpath(folder)
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise SystemExit("refused: candle run status is %r" % m.get("status"))
    answered = set()
    out = {}
    for row in m.get("rows", []):
        if row.get("status") != 200:
            continue
        if not row.get("file") or row.get("truncated"):
            raise SystemExit("refused: a 200 row with no whole stored answer (%s)" % row.get("id"))
        p = os.path.join(folder, row["file"]); refuse_heldout(p)
        if os.path.commonpath([root, os.path.realpath(p)]) != root:
            raise SystemExit("refused: %s points outside the run folder" % row["file"])
        raw = gzip.open(p, "rb").read()
        if row.get("sha256") and hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise SystemExit("refused: %s does not match its sha256" % row["file"])
        if row.get("bytes") is not None and len(raw) != row["bytes"]:
            raise SystemExit("refused: %s does not match its bytes" % row["file"])
        answered.add(row["id"])
        body = json.loads(raw)
        for mk in body.get("markets") or []:
            t = mk.get("market_ticker")
            for c in mk.get("candlesticks") or []:
                out.setdefault(t, {})[int(c["end_period_ts"])] = (px(c.get("yes_bid")), px(c.get("yes_ask")))
    missing = [r["id"] for r in (m.get("job") or {}).get("requests", []) if r["id"] not in answered]
    if missing:
        raise SystemExit("refused: job requests with no 200 answer: %s" % missing[:5])
    return out


def px(node):
    if not isinstance(node, dict) or node.get("close_dollars") in (None, ""):
        return None
    try:
        return float(node["close_dollars"])
    except (TypeError, ValueError):
        return None


def at(cd, t, ts):
    return cd.get(t, {}).get(ts)


def detect(g, cd):
    """First minute (candle end) in the last 45 minutes before the close at which: at least 4 total strikes have a quote that minute, none undecided, at least one decided each way,
    and both moneyline mids (both sides present) within 0.30 to 0.70 inclusive. Returns the minute or None."""
    close = int(g["close_ts"])
    minutes = sorted({ts for t in list(g["ml"]) + list(g["total"]) for ts in cd.get(t, {}) if close - WINDOW_S < ts <= close})
    for ts in minutes:
        quoted = hi = lo = und = 0
        for t in g["total"]:
            q = at(cd, t, ts)
            if q is None or (q[0] is None and q[1] is None):
                continue
            quoted += 1
            b, a = q
            if b is not None and b >= DECIDED_HI - TOL:
                hi += 1
            elif a is not None and a <= DECIDED_LO + TOL:
                lo += 1
            else:
                und += 1
        if quoted < MIN_QUOTED_STRIKES or und or not hi or not lo:
            continue
        ok = True
        for t in g["ml"]:
            q = at(cd, t, ts)
            if q is None or q[0] is None or q[1] is None:
                ok = False; break
            mid = (q[0] + q[1]) / 2
            if not (ML_LO - TOL <= mid <= ML_HI + TOL):
                ok = False; break
        if ok:
            return ts
    return None


def buyable(q):
    return q is not None and q[0] is not None and q[1] is not None and q[1] <= ASK_MAX + TOL and (q[1] - q[0]) <= SPREAD_MAX + TOL


def ot_state(q):
    if q is None or (q[0] is None and q[1] is None):
        return "no quote"
    if q[0] is not None and q[0] >= DECIDED_HI - TOL:
        return "says overtime"
    if q[1] is not None and q[1] <= DECIDED_LO + TOL:
        return "says no overtime"
    return "undecided"


def quart(xs):
    """Quartiles by linear interpolation at (n - 1) p on the sorted list (statistics.quantiles 'inclusive')."""
    return statistics.quantiles(xs, n=4, method="inclusive") if len(xs) >= 2 else [xs[0]] * 3


def measure(folder, games_path):
    refuse_heldout(games_path)
    games = json.load(open(games_path))
    cd = load_candles(folder)
    with_ml = [g for g in games if all(cd.get(t) for t in g["ml"])]
    dets, xcheck = [], {"detected": {}, "not_detected": {}}
    for g in with_ml:
        ts = detect(g, cd)
        close = int(g["close_ts"])
        if ts is None:
            last = max([x for x in cd.get(g["ot"], {}) if close - WINDOW_S < x <= close], default=None)
            st = ot_state(at(cd, g["ot"], last) if last is not None else None)
            xcheck["not_detected"][st] = xcheck["not_detected"].get(st, 0) + 1
            continue
        st = ot_state(at(cd, g["ot"], ts))
        xcheck["detected"][st] = xcheck["detected"].get(st, 0) + 1
        asks = sorted((at(cd, t, ts)[1], t) for t in g["ml"])
        cheap = asks[0][1]                                     # equal asks: the ticker that sorts first
        dets.append({"game": g["game"], "ts": ts, "before_close_min": (close - ts) / 60.0, "ask": asks[0][0], "cheap": cheap,
                     "first5": ts <= close - WINDOW_S + FIRST5_S,
                     "buyable": buyable(at(cd, cheap, ts + 60)), "best_of_two": buyable(at(cd, cheap, ts)) or buyable(at(cd, cheap, ts + 60))})
    n, ng = len(dets), len(with_ml)
    rate = n / ng if ng else None
    asks = sorted(d["ask"] for d in dets)
    out = {"label": LABEL, "freshness": FRESH,
           "games": len(games), "games_with_moneyline_candles": ng, "detections": n, "fire_rate": round(rate, 4) if rate is not None else None,
           "cross_check": xcheck,
           "cheaper_ask": {"median": round(statistics.median(asks), 4), "quartiles": [round(x, 4) for x in quart(asks)], "lowest": min(asks),
                           "at_or_under": {"%dc" % round(L * 100): sum(1 for a in asks if a <= L + TOL) for L in PRICE_LINES}} if asks else None,
           "detection_minutes_before_close": {"median": statistics.median([d["before_close_min"] for d in dets]), "min": min(d["before_close_min"] for d in dets),
                                              "max": max(d["before_close_min"] for d in dets)} if dets else None,
           "detections_in_first_5_minutes": sum(d["first5"] for d in dets)}
    fire_ok = rate is not None and FIRE_LO - TOL <= rate <= FIRE_HI + TOL
    if n >= MIN_DET and fire_ok:
        share = sum(d["buyable"] for d in dets) / n
        out["buyable_share_registered"] = round(share, 4)
        out["best_of_two_share_optimistic"] = round(sum(d["best_of_two"] for d in dets) / n, 4)
    if n < MIN_DET:
        out["verdict"] = "NOT_ENOUGH_DATA (%d detections, under 30)" % n
    elif not fire_ok:
        out["verdict"] = "CLOSED: the rule fires %s (%.4f of games)" % ("too rarely" if rate < FIRE_LO - TOL else "too often", rate)
    elif share < SHARE_MIN - TOL:
        out["verdict"] = "CLOSED on the price share (%.4f buyable, under 0.30)" % share
    else:
        out["verdict"] = "survives the price measurement (%.4f buyable)" % share
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2:
        print(__doc__); sys.exit(0)
    print(json.dumps(measure(a[0], a[1]), indent=1))
