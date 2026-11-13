#!/usr/bin/env python3 -I
"""OICORE proven-bar read (Head of R&D rules, Nov 13, 2026). Local file only, no network, no token.
Usage: python3 -I oicore_proven.py <nightly report json>   (the report's slotOrders list)
Rules: rows = OICORE orders with status filled and result yes or no; rows with result exit, or an unreadable avgFill or avgFee, are EXCLUDED and COUNTED.
n >= 100 rows (rows, not contracts), sorted by ts (fill order), split rows[i*n//3:(i+1)*n//3] into 3 windows.
Cash PF per window, unrounded, fill-booked basis: paid = avgFill for YES, 1 - avgFill for NO; win = count*(1 - paid) - avgFee*count, loss = -(count*paid) - avgFee*count.
PROVEN if at least 2 of 3 windows have PF >= 1.3 (1e-9 tolerance), else NOT YET. Run once at 100: a marker refuses a second read.
Under 100 rows: counts only, no read."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = os.path.join(HERE, "read_markers", "OICORE_PROVEN_READ_DONE")   # fixed path
BAR, TOL, NEED_N, NEED_WIN = 1.3, 1e-9, 100, 2

def num(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x:
        return None
    return float(x)

def cash(o):
    c, fill, fee = num(o.get("count")), num(o.get("avgFill")), num(o.get("avgFee"))
    if c is None or fill is None or fee is None or o.get("side") not in ("yes", "no"):
        return None
    paid = fill if o["side"] == "yes" else 1 - fill
    return c * (1 - paid) - fee * c if o.get("result") == o["side"] else -(c * paid) - fee * c

def pf(v):
    g = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return float("nan") if (g == 0 and l == 0) else (math.inf if l == 0 else g / l)

def run(report, marker=MARKER):
    rows, excl_exit, excl_unreadable = [], 0, 0
    for o in report.get("slotOrders", []):
        if o.get("strategy") != "OICORE" or o.get("status") != "filled":
            continue
        if o.get("result") == "exit":
            excl_exit += 1; continue
        if o.get("result") not in ("yes", "no"):
            continue   # not settled yet
        p = cash(o)
        if p is None:
            excl_unreadable += 1; continue
        rows.append((o["ts"], p))
    rows.sort(key=lambda r: r[0])
    n = len(rows)
    out = {"n": n, "excluded_exit": excl_exit, "excluded_unreadable": excl_unreadable}
    if n < NEED_N:
        out["verdict"] = "NO READ (%d of %d rows)" % (n, NEED_N); return out
    if os.path.exists(marker):
        out["verdict"] = "REFUSED: already read once (%s)" % marker; return out
    wins = []
    for i in range(3):
        w = [p for _, p in rows[i * n // 3:(i + 1) * n // 3]]
        wins.append({"rows": len(w), "net": sum(w), "pf": pf(w), "met": pf(w) >= BAR - TOL})
    out["windows"] = wins
    out["verdict"] = "PROVEN" if sum(w["met"] for w in wins) >= NEED_WIN else "NOT YET"
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    open(marker, "w").write("read done\n")
    return out

if __name__ == "__main__":
    print(json.dumps(run(json.load(open(sys.argv[1]))), indent=1, default=str))
