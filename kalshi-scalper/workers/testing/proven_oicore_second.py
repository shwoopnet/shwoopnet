#!/usr/bin/env python3
"""PROVEN-bar read for OICORE, SECOND BUILD (Testing Desk, Nov 13, 2026). Research only: reads a file it is given, sends nothing, places nothing.
Independent of Refinement's build 1 (not read). Hand case: PROVEN_OICORE_HAND_CASE.md (committed first). Test: test_proven_oicore_second.py (INVENTED rows only). No live figure is stored in any file; results go by message only.

TASK (Head of R&D, 19:20Z, the owner's priority): from the nightly report's slot rows for strategy OICORE (settled, filled), in fill order, split into 3 equal windows by fill count;
cash PF per window from avgFill and avgFee on the fill-booked cash basis (fillCost, functions/kalshiLiveLib.js), unrounded; PROVEN if at least 2 of 3 windows are at 1.3 or better, otherwise NOT YET with the figures.
RULING (Head, 19:22Z): the bar is 100 fills IN TOTAL; there is NO per-window n minimum; total n under 100 is NOT_ENOUGH_DATA; each window's n is printed beside its PF.

CASH BASIS (fillCost as read from origin/main): side price = avgFill for YES, 1 - avgFill for NO; cost = (side price + avgFee) x count; valid only if 0 < avgFill < 1, 0 <= avgFee < 1 and count > 0, else the row is EXCLUDED and counted
(fillCost would fall back to the limit booking maxCost, which the report row does not carry). Payout count x $1 when the result equals the side, else 0. A void = price refunded, fee kept (-(avgFee x count)).
A result of 'exit' (exitProceeds is not in the report row) is EXCLUDED and counted. Rows used: strategy exactly 'OICORE', count > 0, settledPnl present. Fill order = ascending ts (stable).
Windows: rows[i*n // 3 : (i+1)*n // 3]. A window counts when its PF >= 1.3 - 1e-9 (unrounded), whatever its n. Total rows used under 100: NOT_ENOUGH_DATA; else PROVEN if at least 2 of 3 windows count, otherwise NOT YET.
READ POINTS (Head, 19:23Z): one marker per read point, 100 and then 150 if the first says NOT YET. A read is made AT a point P and uses the FIRST P fills in fill order (my reading; rows beyond P are not read).
Fewer than P usable fills: NOT_ENOUGH_DATA, no marker, the point is not spent. A made read writes PROVEN_OICORE_READ_<P>.local (with its verdict) BEFORE any output. Point 100 refuses if its marker exists;
point 150 refuses unless the 100 marker exists with verdict NOT YET, and refuses if its own marker exists. Open (filled, unsettled) OICORE orders are counted and printed as open_filled_orders.
Usage: proven_oicore_second.py <report.json> <read point 100|150>      (the nightly report with ?orders=1 (a 'slotOrders' list), or a plain list of rows)
"""
import json, math, os, sys

STRATEGY = "OICORE"
BAR_PF = 1.3
MIN_TOTAL = 100
NEED_WINDOWS = 2
N_WINDOWS = 3
TOL = 1e-9
AMBIGUITIES = [
    "'By fill count' is by the NUMBER OF FILLED ORDERS (rows), not contracts (the Head's ruling 19:22Z); the 100-fill bar is a TOTAL, with no per-window minimum.",
    "Rows fillCost would book at the limit (unreadable avgFill or avgFee) cannot be reproduced from the report row (maxCost is not carried): they are excluded and counted, never guessed.",
    "A result of 'exit' (the exit watch sold some contracts) is excluded and counted: exitProceeds is not in the report row.",
    "A void is price refunded, fee kept (the standing void rule); fillCost's own cap 'cash <= worst case' cannot be applied without maxCost.",
    "Fill order is the row's ts (the order time), the only time the report row carries; ties keep input order.",
    "The report covers only the hours asked for (at most 90 days): the rows given are the rows read; this reader does not page.",
]


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def cash_result(row):
    """-> (net dollars, None) or (None, exclusion reason). The cash basis of fillCost."""
    if row.get("strategy") != STRATEGY:
        return None, "other strategy"
    count = _num(row.get("count"))
    if not (count is not None and count > 0):
        return None, "not filled"
    if row.get("settledPnl") is None or _num(row.get("settledPnl")) is None:
        return None, "not settled"
    res, side = row.get("result"), row.get("side")
    if res == "exit":
        return None, "exit (exitProceeds not in the row)"
    avg, fee = row.get("avgFill"), row.get("avgFee")
    a, f = _num(avg), _num(fee)
    if avg is None or avg == "" or a is None or not (0 < a < 1):
        return None, "avgFill unreadable"
    if fee is None or fee == "" or f is None or not (0 <= f < 1):
        return None, "avgFee unreadable"
    if side not in ("yes", "no"):
        return None, "side unreadable"
    sp = a if side == "yes" else 1.0 - a
    cost = (sp + f) * count
    if res == "void":
        return -(f * count), None
    if res not in ("yes", "no"):
        return None, "result not yes, no, void or exit"
    return (count if res == side else 0.0) - cost, None


def select(rows):
    """-> (used [(ts, net)], exclusions {reason: n}) in fill order."""
    used, ex = [], {}
    for r in rows:
        net, why = cash_result(r)
        if why:
            ex[why] = ex.get(why, 0) + 1
        else:
            used.append((str(r.get("ts")), net))
    used.sort(key=lambda x: x[0])          # stable: ties keep input order
    return used, ex


def pf_of(nets):
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    if l > 0:
        return w / l
    return None if w == 0 else float("inf")


def split(nets, k=N_WINDOWS):
    n = len(nets)
    return [nets[i * n // k:(i + 1) * n // k] for i in range(k)]


def window_ok(nets):
    p = pf_of(nets)
    return p is not None and p >= BAR_PF - TOL          # no per-window n minimum (Head, 19:22Z)


def open_filled(rows):
    """Open OICORE orders: filled (count > 0) and not yet settled (settledPnl absent)."""
    n = 0
    for r in rows:
        c = _num(r.get("count"))
        if r.get("strategy") == STRATEGY and c is not None and c > 0 and (r.get("settledPnl") is None or _num(r.get("settledPnl")) is None):
            n += 1
    return n


def read_rows(rows, limit=None):
    used, ex = select(rows)
    if limit is not None and len(used) >= limit:
        used = used[:limit]          # the read point: the FIRST `limit` fills
    nets = [x[1] for x in used]
    wins = split(nets)
    wf = []
    for w in wins:
        p = pf_of(w)
        wf.append({"n": len(w), "cash_pf_unrounded": p, "net": sum(w), "win_rate": (sum(1 for x in w if x > 0) / len(w) if w else None), "counts": window_ok(w)})
    ok = sum(1 for x in wf if x["counts"])
    verdict = "NOT_ENOUGH_DATA" if len(used) < max(MIN_TOTAL, limit or 0) else ("PROVEN" if ok >= NEED_WINDOWS else "NOT YET")          # at a read point P: under P usable fills is not enough
    return {"python": "%s at %s" % (sys.version.split()[0], sys.executable), "rule": "100 fills in total (under 100: NOT_ENOUGH_DATA); PROVEN if at least 2 of 3 windows have cash PF >= 1.3 (unrounded, 1e-9), no per-window n minimum; else NOT YET",
            "strategy": STRATEGY, "rows_given": len(rows), "rows_used": len(used), "open_filled_orders": open_filled(rows), "excluded": ex,
            "excluded_unreadable_fill_or_fee": ex.get("avgFill unreadable", 0) + ex.get("avgFee unreadable", 0), "excluded_exit": ex.get("exit (exitProceeds not in the row)", 0),
            "windows": wf, "windows_counting": ok, "VERDICT": verdict, "ambiguities": AMBIGUITIES}


POINTS = (100, 150)
HERE = os.path.dirname(os.path.abspath(__file__))


def marker_path(point, marker_dir=None):
    return os.path.join(marker_dir or HERE, "PROVEN_OICORE_READ_%d.local" % point)


def read_point(rows, point, marker_dir=None, now=None):
    """One marker per read point. Refusals come before any data is looked at; NOT_ENOUGH_DATA writes no marker; a made read writes its marker BEFORE returning (the caller prints)."""
    import time
    if point not in POINTS:
        raise SystemExit("refused: read point %r; the read points are 100 and then 150" % (point,))
    m = marker_path(point, marker_dir)
    if os.path.exists(m):
        raise SystemExit("refused: the read point %d was already read (%s): %s" % (point, m, open(m).read().strip().splitlines()[-1]))
    if point == 150:
        m100 = marker_path(100, marker_dir)
        if not os.path.exists(m100):
            raise SystemExit("refused: read point 150 needs a read at point 100 first (no marker %s)" % m100)
        if "verdict: NOT YET" not in open(m100).read():
            raise SystemExit("refused: the point-100 read did not say NOT YET (%s); a PROVEN at 100 ends the question" % open(m100).read().strip().splitlines()[-1])
    out = read_rows(rows, limit=point)
    out["read_point"], out["rows_read"] = point, (point if out["rows_used"] >= point else 0)
    if out["VERDICT"] == "NOT_ENOUGH_DATA":
        return out          # fewer than P usable fills: not spent, no marker
    with open(m, "w") as fh:
        fh.write("READ POINT %d MADE at %s UTC\nverdict: %s\n" % (point, time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(time.time() if now is None else now)), out["VERDICT"]))
    return out


def read_file(path, point=None):
    d = json.load(open(path))
    rows = d.get("slotOrders") if isinstance(d, dict) else d
    if not isinstance(rows, list):
        raise SystemExit("STOP: no slotOrders list in %s" % path)
    return read_point(rows, point) if point is not None else read_rows(rows)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2:
        print(json.dumps(read_file(a[0], int(a[1])), indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
