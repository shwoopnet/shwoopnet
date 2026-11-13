#!/usr/bin/env python3
"""PROVEN-bar read for OICORE, SECOND BUILD (Testing Desk, Nov 13, 2026). Research only: reads a file it is given, sends nothing, places nothing.
Independent of Refinement's build 1 (not read). Hand case: PROVEN_OICORE_HAND_CASE.md (committed first). Test: test_proven_oicore_second.py (INVENTED rows only). No live figure is stored in any file; results go by message only.

TASK (Head of R&D, 19:20Z, the owner's priority): from the nightly report's slot rows for strategy OICORE (settled, filled), in fill order, split into 3 equal windows by fill count;
cash PF per window from avgFill and avgFee on the fill-booked cash basis (fillCost, functions/kalshiLiveLib.js), unrounded; PROVEN if at least 2 of 3 windows are at 1.3 or better with n of 100 or more, otherwise NOT YET with the figures.

CASH BASIS (fillCost as read from origin/main): side price = avgFill for YES, 1 - avgFill for NO; cost = (side price + avgFee) x count; valid only if 0 < avgFill < 1, 0 <= avgFee < 1 and count > 0, else the row is EXCLUDED and counted
(fillCost would fall back to the limit booking maxCost, which the report row does not carry). Payout count x $1 when the result equals the side, else 0. A void = price refunded, fee kept (-(avgFee x count)).
A result of 'exit' (exitProceeds is not in the report row) is EXCLUDED and counted. Rows used: strategy exactly 'OICORE', count > 0, settledPnl present. Fill order = ascending ts (stable).
Windows: rows[i*n // 3 : (i+1)*n // 3]; n = the window's order count. A window counts when PF >= 1.3 - 1e-9 (PF unrounded) AND n >= 100. PROVEN if at least 2 of 3 windows count.
Usage: proven_oicore_second.py <report.json>      (the nightly report with ?orders=1 (a 'slotOrders' list), or a plain list of rows)
"""
import json, math, os, sys

STRATEGY = "OICORE"
BAR_PF = 1.3
MIN_N = 100
NEED_WINDOWS = 2
N_WINDOWS = 3
TOL = 1e-9
AMBIGUITIES = [
    "'By fill count' is read as by the NUMBER OF FILLED ORDERS (rows), not by contracts; n in 'n of 100 or more' is the window's order count.",
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
    return len(nets) >= MIN_N and p is not None and p >= BAR_PF - TOL


def read_rows(rows):
    used, ex = select(rows)
    nets = [x[1] for x in used]
    wins = split(nets)
    wf = []
    for w in wins:
        p = pf_of(w)
        wf.append({"n": len(w), "cash_pf_unrounded": p, "net": sum(w), "win_rate": (sum(1 for x in w if x > 0) / len(w) if w else None), "counts": window_ok(w)})
    ok = sum(1 for x in wf if x["counts"])
    verdict = "PROVEN" if ok >= NEED_WINDOWS else "NOT YET"
    return {"python": "%s at %s" % (sys.version.split()[0], sys.executable), "rule": "PROVEN if at least 2 of 3 windows have cash PF >= 1.3 (unrounded, 1e-9) with n >= 100; else NOT YET",
            "strategy": STRATEGY, "rows_given": len(rows), "rows_used": len(used), "excluded": ex, "windows": wf, "windows_counting": ok, "VERDICT": verdict, "ambiguities": AMBIGUITIES}


def read_file(path):
    d = json.load(open(path))
    rows = d.get("slotOrders") if isinstance(d, dict) else d
    if not isinstance(rows, list):
        raise SystemExit("STOP: no slotOrders list in %s" % path)
    return read_rows(rows)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 1:
        print(json.dumps(read_file(a[0]), indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
