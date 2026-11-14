#!/usr/bin/env python3 -I
"""OICORE proven-bar read (Head of R&D rules, Nov 13, 2026). Local file only, no network, no token.
Usage: python3 -I oicore_proven.py --extract <canonical extract csv> <100|150>   (the real read, see oicore_extract.py)\n       python3 -I oicore_proven.py <nightly report json>   (dry run: counts only below 100 rows; not used for the read)
Rules: rows = OICORE orders with status filled and result yes or no; rows with result exit, or an unreadable avgFill or avgFee, are EXCLUDED and COUNTED.
n >= 100 rows (rows, not contracts), sorted by ts (fill order); the read point uses EXACTLY the first 100 (or first 150) rows and splits them rows[i*m//3:(i+1)*m//3] with m = 100 or 150.
Cash PF per window, unrounded, fill-booked basis: paid = avgFill for YES, 1 - avgFill for NO; win = count*(1 - paid) - avgFee*count, loss = -(count*paid) - avgFee*count.
PROVEN if at least 2 of 3 windows have PF >= 1.3 (1e-9 tolerance), else NOT YET. Read points: 100 rows, then 150 rows only if the 100 read said NOT YET; each read once (a marker per read point), no other read in between.
Open (filled, unsettled) orders are counted and printed. Under 100 rows: counts only, no read."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MARKER_DIR = os.path.join(HERE, "read_markers")   # fixed path; one marker per read point: OICORE_PROVEN_READ_100_DONE, OICORE_PROVEN_READ_150_DONE
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

def run(report, marker_dir=MARKER_DIR):
    rows, excl_exit, excl_unreadable, n_open = [], 0, 0, 0
    for o in report.get("slotOrders", []):
        if o.get("strategy") != "OICORE" or o.get("status") != "filled":
            continue
        if o.get("result") == "exit":
            excl_exit += 1; continue
        if o.get("result") not in ("yes", "no"):
            n_open += 1; continue   # filled but not settled yet: counted and printed
        p = cash(o)
        if p is None:
            excl_unreadable += 1; continue
        rows.append((o["ts"], p))
    rows.sort(key=lambda r: r[0])
    n = len(rows)
    out = {"n": n, "excluded_exit": excl_exit, "excluded_unreadable": excl_unreadable, "open_unsettled": n_open}
    m100 = os.path.join(marker_dir, "OICORE_PROVEN_READ_100_DONE"); m150 = os.path.join(marker_dir, "OICORE_PROVEN_READ_150_DONE")
    if n < NEED_N:
        out["verdict"] = "NO READ (%d of %d rows)" % (n, NEED_N); return out
    if os.path.exists(m150):
        out["verdict"] = "REFUSED: both read points are used (%s)" % m150; return out
    if not os.path.exists(m100):
        point, marker = 100, m100
    else:
        first = open(m100).read().split()[0] if open(m100).read().strip() else ""
        if first == "PROVEN":
            out["verdict"] = "REFUSED: the 100 read said PROVEN, no 150 read"; return out
        if n < 150:
            out["verdict"] = "NO READ (the 100 read is done; the 150 read needs 150 rows, have %d)" % n; return out
        point, marker = 150, m150
    out["read_point"] = point
    used = rows[:point]   # EXACTLY the first 100 (or 150) counted rows by ts, never "all rows present": no choice about when to look
    out["rows_used"] = len(used); m = len(used)
    out["first_ts"], out["last_ts"] = used[0][0], used[-1][0]
    wins = []
    for i in range(3):
        w = [p for _, p in used[i * m // 3:(i + 1) * m // 3]]
        wins.append({"rows": len(w), "net": sum(w), "pf": pf(w), "met": pf(w) >= BAR - TOL})
    out["windows"] = wins
    out["verdict"] = "PROVEN" if sum(w["met"] for w in wins) >= NEED_WIN else "NOT YET"
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    open(marker, "w").write(out["verdict"] + "\n")
    return out

def run_extract(text, point, marker_dir=MARKER_DIR):
    """The real read: scores a canonical extract (oicore_extract.py) only; the extract must hold exactly `point` rows."""
    lines = text.rstrip("\n").split("\n")
    out = {"read_point": point}
    if lines[0] != "ts,ticker,side,count,avgFill,avgFee,result" or len(lines) - 1 != point or point not in (100, 150):
        out["verdict"] = "REFUSED: not a canonical extract of exactly %d rows" % point; return out
    m100 = os.path.join(marker_dir, "OICORE_PROVEN_READ_100_DONE"); m150 = os.path.join(marker_dir, "OICORE_PROVEN_READ_150_DONE")
    marker = m100 if point == 100 else m150
    if os.path.exists(marker):
        out["verdict"] = "REFUSED: read point %d already used" % point; return out
    if point == 150:
        if not os.path.exists(m100) or open(m100).read().split()[0] != "NOT":
            out["verdict"] = "REFUSED: the 150 read needs a 100 read that said NOT YET"; return out
    rows = []
    for ln in lines[1:]:
        ts, tk, side, cnt, fill, fee, res = ln.split(",")
        p = cash({"count": float(cnt), "avgFill": float(fill), "avgFee": float(fee), "side": side, "result": res})
        rows.append((ts, p))
    rows.sort(key=lambda r: r[0])
    out["rows_used"] = len(rows); out["first_ts"], out["last_ts"] = rows[0][0], rows[-1][0]
    m = len(rows); wins = []
    for i in range(3):
        w = [p for _, p in rows[i * m // 3:(i + 1) * m // 3]]
        wins.append({"rows": len(w), "net": sum(w), "pf": pf(w), "met": pf(w) >= BAR - TOL})
    out["windows"] = wins
    out["verdict"] = "PROVEN" if sum(w["met"] for w in wins) >= NEED_WIN else "NOT YET"
    os.makedirs(marker_dir, exist_ok=True)
    open(marker, "w").write(out["verdict"] + "\n")
    return out

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--extract":
        print(json.dumps(run_extract(open(sys.argv[2]).read(), int(sys.argv[3])), indent=1, default=str))
    else:
        print(json.dumps(run(json.load(open(sys.argv[1]))), indent=1, default=str))
