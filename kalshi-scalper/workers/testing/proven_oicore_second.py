#!/usr/bin/env python3
"""PROVEN-bar read for OICORE, SECOND BUILD, EXTRACT-ONLY (Testing Desk, Nov 14, 2026). Research only: reads a file it is given, sends nothing, places nothing.
Independent of Refinement's build 1 (not read). Hand cases: PROVEN_OICORE_HAND_CASE.md and PROVEN_OICORE_HAND_CASE_ADDENDUM3.md (committed first). Test: test_proven_oicore_second.py (INVENTED rows only).
No live figure is stored in any file; results go by message only.

INPUT (Head, Nov 14, 00:30Z): ONLY Refinement's canonical extract (commit 6e63a0bd, oicore_extract.py 257b30c0): header ts,ticker,side,count,avgFill,avgFee,result; the first N settled OICORE rows by (ts, ticker);
%.6f; LF; no generatedAt; result yes or no only. Any deviation from that format STOPs naming the line. The sha256 of the raw file bytes is printed and written into the marker.
RULE (Head, 19:20Z to 19:23Z): rows in fill order (the extract's order), split into 3 windows by fill count, window i = rows[i*m // 3 : (i+1)*m // 3]; cash PF per window on the fill-booked cash basis, unrounded;
a window counts at PF >= 1.3 - 1e-9 whatever its n; PROVEN if at least 2 of 3 windows count, otherwise NOT YET with the figures; each window's n is printed beside its PF.
CASH BASIS (fillCost as read from origin/main): side price = avgFill for YES, 1 - avgFill for NO; cost = (side price + avgFee) x count; valid only if count > 0, 0 < avgFill < 1 and 0 <= avgFee < 1, else the row is EXCLUDED and counted
(fillCost would fall back to the limit booking, which the extract does not carry). Payout count x $1 when the result equals the side, else 0. A void is not in an extract.
READ POINTS (Head, 19:23Z): one marker per read point, 100 and then 150 if the first says NOT YET. A read at P needs exactly P rows (more than P STOPs); fewer than P usable fills is NOT_ENOUGH_DATA, no marker, the point is not spent.
A made read writes PROVEN_OICORE_READ_<P>.local (with its verdict and the extract's sha256) BEFORE any output. Point 100 refuses if its marker exists; point 150 refuses unless the 100 marker says NOT YET and refuses if its own exists; refusals come before the file is looked at.
Usage: proven_oicore_second.py <extract.csv> <read point 100|150>
"""
import hashlib, math, os, re, sys, time

BAR_PF = 1.3
NEED_WINDOWS = 2
N_WINDOWS = 3
TOL = 1e-9
COLS = "ts,ticker,side,count,avgFill,avgFee,result"
POINTS = (100, 150)
HERE = os.path.dirname(os.path.abspath(__file__))
AMBIGUITIES = [
    "'By fill count' is by the NUMBER OF FILLED ORDERS (rows), not contracts (the Head's ruling 19:22Z); the 100-fill bar is a TOTAL, with no per-window minimum.",
    "The extract holds exactly the first P rows by (ts, ticker): fill order is the extract's order (checked non-decreasing); a repeated (ts, ticker) is allowed and keeps its order.",
    "Rows with count <= 0, avgFill outside (0, 1) or avgFee outside [0, 1) cannot be booked as fillCost books them (it would use the limit): excluded and counted, never guessed; usable rows under P is NOT_ENOUGH_DATA.",
    "A void or exit row in the file STOPs: the extractor excludes them, so such a row means the file is not the canonical extract.",
    "The number format is checked strictly (avgFill and avgFee %.6f; count an integer or %.6f): the canonical extract carries nothing else.",
]
_FIXED = re.compile(r"^-?\d+\.\d{6}$")
_COUNT = re.compile(r"^\d+(\.\d{6})?$")


def parse_extract(path):
    """-> {'rows': [dict(ts, ticker, side, count, fill, fee, result)], 'sha256': str}. Any deviation from the canonical format STOPs naming the line."""
    raw = open(path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit("STOP: the file is not utf-8 text (not the canonical extract)")
    if "\r" in text:
        raise SystemExit("STOP: a CR in the file: the canonical extract is LF only")
    if text and not text.endswith("\n"):
        raise SystemExit("STOP: the file does not end with a final LF (not the canonical extract)")
    lines = text.split("\n")[:-1] if text else []
    if not lines or lines[0] != COLS:
        raise SystemExit("STOP: line 1 is not the header %s" % COLS)
    rows, prev = [], None
    for n, ln in enumerate(lines[1:], start=2):
        f = ln.split(",")
        if len(f) != 7:
            raise SystemExit("STOP: line %d has %d fields, not 7" % (n, len(f)))
        ts, tk, side, cnt, fill, fee, res = f
        if not ts or not tk:
            raise SystemExit("STOP: line %d has an empty ts or ticker" % n)
        if side not in ("yes", "no"):
            raise SystemExit("STOP: line %d side %r is not yes or no" % (n, side))
        if res not in ("yes", "no"):
            raise SystemExit("STOP: line %d result %r is not yes or no (the extractor excludes exit, void and open rows)" % (n, res))
        if not _COUNT.match(cnt):
            raise SystemExit("STOP: line %d count %r is not an integer or %%.6f" % (n, cnt))
        if not _FIXED.match(fill):
            raise SystemExit("STOP: line %d avgFill %r is not %%.6f" % (n, fill))
        if not _FIXED.match(fee):
            raise SystemExit("STOP: line %d avgFee %r is not %%.6f" % (n, fee))
        if prev is not None and (ts, tk) < prev:
            raise SystemExit("STOP: line %d is before its predecessor in (ts, ticker) order" % n)
        prev = (ts, tk)
        rows.append({"ts": ts, "ticker": tk, "side": side, "count": float(cnt), "fill": float(fill), "fee": float(fee), "result": res})
    return {"rows": rows, "sha256": sha}


def cash_net(row):
    """-> (net dollars, None) or (None, exclusion reason). The cash basis of fillCost."""
    c, a, f = row["count"], row["fill"], row["fee"]
    if not (c > 0):
        return None, "count not positive"
    if not (0 < a < 1):
        return None, "avgFill unreadable"
    if not (0 <= f < 1):
        return None, "avgFee unreadable"
    sp = a if row["side"] == "yes" else 1.0 - a
    return (c if row["result"] == row["side"] else 0.0) - (sp + f) * c, None


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
    pf = pf_of(nets)
    return pf is not None and pf >= BAR_PF - TOL          # no per-window n minimum (Head, 19:22Z)


def score_rows(rows, point):
    """The figures for the rows of an extract read at point P. More than P rows STOPs; fewer usable fills than P is NOT_ENOUGH_DATA."""
    if len(rows) > point:
        raise SystemExit("STOP: %d rows in the extract, more than the read point %d (not the canonical extract for this point)" % (len(rows), point))
    nets, ex = [], {}
    for r in rows:
        net, why = cash_net(r)
        if why:
            ex[why] = ex.get(why, 0) + 1
        else:
            nets.append(net)
    wins = split(nets)
    wf = []
    for w in wins:
        pf = pf_of(w)
        wf.append({"n": len(w), "cash_pf_unrounded": pf, "net": sum(w), "win_rate": (sum(1 for x in w if x > 0) / len(w) if w else None), "counts": window_ok(w)})
    ok = sum(1 for x in wf if x["counts"])
    verdict = "NOT_ENOUGH_DATA" if len(nets) < point else ("PROVEN" if ok >= NEED_WINDOWS else "NOT YET")
    return {"python": "%s at %s" % (sys.version.split()[0], sys.executable), "rule": "extract of exactly P rows; 3 windows rows[i*m//3:(i+1)*m//3]; PROVEN if at least 2 of 3 windows have cash PF >= 1.3 (unrounded, 1e-9), no per-window n minimum; else NOT YET; under P usable fills NOT_ENOUGH_DATA",
            "rows_in_extract": len(rows), "rows_usable": len(nets), "excluded": ex, "excluded_unusable": sum(ex.values()), "windows": wf, "windows_counting": ok, "VERDICT": verdict, "ambiguities": AMBIGUITIES}


def marker_path(point, marker_dir=None):
    return os.path.join(marker_dir or HERE, "PROVEN_OICORE_READ_%d.local" % point)


def read_point(path, point, marker_dir=None, now=None):
    """One marker per read point. Refusals come before the file is looked at; NOT_ENOUGH_DATA writes no marker; a made read writes its marker BEFORE returning (the caller prints)."""
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
    ex = parse_extract(path)
    out = score_rows(ex["rows"], point)
    out["extract_sha256"], out["read_point"] = ex["sha256"], point
    if out["VERDICT"] == "NOT_ENOUGH_DATA":
        return out          # fewer than P usable fills: not spent, no marker
    with open(m, "w") as fh:
        fh.write("READ POINT %d MADE at %s UTC\nextract sha256: %s\nverdict: %s\n" % (point, time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(time.time() if now is None else now)), ex["sha256"], out["VERDICT"]))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2:
        import json as _j
        print(_j.dumps(read_point(a[0], int(a[1])), indent=2, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
