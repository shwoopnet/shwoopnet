#!/usr/bin/env python3 -I
"""V1 (OICORE resting bid) and V2 (EVENT830 resting entry) scorer, registered Nov 13, 2026 (V1_OICORE_RESTING_BID_REGISTRATION.md, V2_EVENT830_RESTING_ENTRY_REGISTRATION.md).
Local files only: no network, no key. One read per block, a marker refuses a second run.

Usage:
  python3 -I v1_resting_score.py --version V1 --block dev|forward --book-root ROOT --signals SIGNALS.csv --out OUT_DIR [--depth1-recorded MARKER_FILE]
ROOT holds run folders each with book.csv.gz, trades.csv.gz and coverage.csv.gz (the recorder's layout: book15r6/<date>/<HHMM>/ for V1, nc15/... for V2).
SIGNALS.csv (one row per candidate window, built outside this scorer from public data): ticker,close_ts[,oi_rise]. V1: the OICORE trigger windows (OI rise of 86,300 or more); V2: the listed release windows' markets.
The scorer applies everything else of the registration: t0, side, band, parent taker replay, resting bid, fill rule, fees, measures, the 7g bar.
"""
import argparse
import csv
import glob
import gzip
import io
import math
import json
import os
import sys
import time
import calendar
import statistics

BLOCKS = {  # constants from the registrations (UTC close time bounds, inclusive)
    ("V1", "dev"): ("2026-10-29T22:15:00Z", "2026-11-13T23:59:59Z"),
    ("V1", "forward"): ("2026-11-14T00:00:00Z", "2026-12-31T23:59:59Z"),
    ("V2", "dev"): ("2026-11-12T00:00:00Z", "2026-12-04T23:59:59Z"),
    ("V2", "forward"): ("2026-12-10T00:00:00Z", "2026-12-23T23:59:59Z"),
}
READ_AFTER = {("V1", "forward"): "2027-01-01T00:00:00Z", ("V2", "forward"): "2026-12-24T00:00:00Z"}
BAND = (0.05, 0.50)
SPREAD_MAX = 0.10  # V2 only
T0_AFTER_S = 178   # V1: first row at or after close minus 178 s; V2: 180
CANCEL_S = 120
BAR_PF = 0.10
BAR_N = 60
DEPTH1_MARKER_PREFIX = "DEPTH1 READ MADE:"
NC15DEPTH1_HASH_PREFIX = "NC15DEPTH1 SCORER HASH:"  # first line of the file the Head names for V2 (to be confirmed by the Head)
V2_DEV_READ_AFTER = "2026-12-05T00:00:00Z"        # the V2 development block closes 2026-12-04T23:59:59Z
HERE = os.path.dirname(os.path.abspath(__file__))
MARKER_DIR = os.path.join(HERE, "read_markers")    # FIXED path: a new --out cannot reopen a block that was read
HELDOUT_LIST = os.path.join(os.path.dirname(HERE), "workers", "HELDOUT_PULL_RUNS.md")
LABELS = {
    "V1": "not blind on Bitcoin windows to Nov 13: DEPTH1, CFRTI-B and CFRTI1-BTC read them (DEPTH1 on 2026-11-14)",
    "V2": "not blind on EVENT830's forward windows",
}
MAKER_FEE_FRAC = 0.25  # primary; sensitivities 0 and 1


def epoch(iso):
    return calendar.timegm(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))


def fee(p):
    return 0.07 * p * (1 - p)


def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def created_ms(s):
    """created_time like 2026-11-03T11:57:02Z, ...02.5Z or ...02.123456Z to epoch ms; the fraction is read as a fraction (.5 is 500 ms)."""
    ms = epoch(s) * 1000
    if len(s) > 19 and s[19] == ".":
        digits = ""
        for ch in s[20:]:
            if not ch.isdigit():
                break
            digits += ch
        if digits:
            ms += int(round(float("0." + digits) * 1000))
    return ms


def check_marker_line(path, prefix):
    """The marker must exist and its first non-empty line must start with the prefix (as WHEEL0 does)."""
    try:
        for ln in open(path, encoding="utf-8").read().splitlines():
            if ln.strip():
                return ln.strip().startswith(prefix)
    except OSError:
        return False
    return False


def refuse_heldout(paths, list_file):
    """Standing held-out guard (the logic of hm_guard / deskb_guard): a part starting HELDOUT_, or equal to a run folder named in the list, is refused; an unreadable list refuses everything."""
    try:
        lines = open(list_file, "rb").read().decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return "REFUSED: %s cannot be read, so no run can be shown to be clean" % list_file
    if not any(ln.startswith("| Run folder") for ln in lines):
        return "REFUSED: %s has no table header" % list_file
    import re
    runs = set()
    for ln in lines:
        m = re.match(r"^\|\s*`([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)`\s*\|", ln)
        if m:
            runs.add(m.group(2))
    for p in paths:
        for q in (os.path.abspath(p), os.path.realpath(p)):
            parts = q.split(os.sep)
            if any(x.upper().startswith("HELDOUT_") for x in parts):
                return "REFUSED: %s lies in or resolves into a HELDOUT_ folder" % p
            hit = runs.intersection(parts)
            if hit:
                return "REFUSED: %s is, or lies inside, the landed run %s, listed as held-out material" % (p, sorted(hit)[0])
    return None


def read_csv_gz(path):
    with gzip.open(path, "rt", newline="") as f:
        return list(csv.DictReader(f))


def load_run_folders(root):
    book, trades, cover = {}, {}, {}
    for d in sorted(glob.glob(os.path.join(root, "**", "book.csv.gz"), recursive=True)):
        base = os.path.dirname(d)
        for r in read_csv_gz(d):
            book.setdefault(r["ticker"], []).append(r)
        p = os.path.join(base, "trades.csv.gz")
        if os.path.exists(p):
            for r in read_csv_gz(p):
                trades.setdefault(r["ticker"], []).append(r)
        p = os.path.join(base, "coverage.csv.gz")
        if os.path.exists(p):
            for r in read_csv_gz(p):
                old = cover.get(r["ticker"])
                if old is None or (old.get("result") not in ("yes", "no")):
                    cover[r["ticker"]] = r        # a yes or no row is never replaced by an empty one
    for k in book:
        book[k].sort(key=lambda r: int(float(r["t_recv_ms"])))
    return book, trades, cover


def sides(row):
    """(yes_bid, no_bid) best bids as dollars or None; yes_ask = 1 - no_bid, no_ask = 1 - yes_bid."""
    yb, nb = fl(row.get("yes_bid_px_1")), fl(row.get("no_bid_px_1"))
    return yb, nb


def one_window(version, tk, ct, book, trades, cover):
    """Returns dict with keys: status, and when a signal: side, p_ask, p_bid, filled, win."""
    rows = book.get(tk) or []
    if not rows:
        return {"status": "no_book"}
    t0ms = (ct - (180 if version == "V2" else T0_AFTER_S)) * 1000
    cancel_ms = (ct - CANCEL_S) * 1000
    t0 = next((r for r in rows if int(float(r["t_recv_ms"])) >= t0ms), None)
    if t0 is None or int(float(t0["t_recv_ms"])) - t0ms > 10000:
        return {"status": "no_t0_row"}
    yb, nb = sides(t0)
    ya = None if nb is None else 1 - nb
    na = None if yb is None else 1 - yb
    if ya is None and na is None:
        return {"status": "no_quote"}
    if version == "V2" and (ya is None or yb is None or ya - yb > SPREAD_MAX + 1e-9):
        return {"status": "spread_wide"}
    # the cheaper side is the one with the lower own ask; a side whose ask does not exist (no opposite bid) is not a candidate
    if na is None or (ya is not None and ya <= na):
        side, p_ask = "yes", ya
    else:
        side, p_ask = "no", na
    if not (BAND[0] - 1e-9 <= p_ask <= BAND[1] + 1e-9):
        return {"status": "out_of_band"}
    res = (cover.get(tk) or {}).get("result")
    if res not in ("yes", "no"):
        return {"status": "no_result"}
    p_bid = yb if side == "yes" else nb
    out = {"status": "signal", "side": side, "p_ask": p_ask, "p_bid": p_bid, "win": res == side, "filled": False, "ct": ct}
    if p_bid is None or p_bid <= 0:
        out["no_order"] = True
        return out
    t0_ms = int(float(t0["t_recv_ms"]))
    # (b) a later book row, before the cancel row, shows the side's ask at or below our price
    for r in rows:
        ms = int(float(r["t_recv_ms"]))
        if ms <= t0_ms:
            continue
        if ms >= cancel_ms:
            break
        yb2, nb2 = sides(r)
        ask2 = (1 - nb2) if side == "yes" and nb2 is not None else ((1 - yb2) if side == "no" and yb2 is not None else None)
        if ask2 is not None and ask2 <= p_bid + 1e-9:
            out["filled"] = True
            return out
    # (a) a public trade strictly through our price after t0 and before the cancel
    cancel_row = next((r for r in rows if int(float(r["t_recv_ms"])) >= cancel_ms), None)
    end_ms = int(float(cancel_row["t_recv_ms"])) if cancel_row else cancel_ms
    for tr in trades.get(tk) or []:
        try:
            tms = created_ms(tr["created_time"])
        except (ValueError, KeyError):
            continue
        if not (t0_ms < tms < end_ms):
            continue
        yp = fl(tr.get("yes_price_dollars"))
        tk_side = tr.get("taker_outcome_side")
        if yp is None:
            continue
        if side == "yes" and tk_side == "no" and yp < p_bid - 1e-9:
            out["filled"] = True
            return out
        if side == "no" and tk_side == "yes" and yp > (1 - p_bid) + 1e-9:
            out["filled"] = True
            return out
    return out


def net(p, win, slip=0.0, frac=1.0):
    c = p + slip
    f = frac * fee(c)
    return (1 - c - f) if win else -(c + f)


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return (g / l) if l > 0 else (float("inf") if g > 0 else float("nan"))


def evaluate(sig, days, block="dev"):
    """sig: signal dicts (status signal) in close order. Returns the report lines and the bar."""
    sig = sorted(sig, key=lambda s: s["ct"])
    n = len(sig)
    filled = [s for s in sig if s["filled"]]
    unfilled = [s for s in sig if not s["filled"]]
    out = []
    out.append("signals %d, orders placed %d, filled %d (fill rate %.1f%%), no order (no bid) %d" % (
        n, sum(1 for s in sig if not s.get("no_order")), len(filled), 100.0 * len(filled) / n if n else 0, sum(1 for s in sig if s.get("no_order"))))
    res = {}
    for slip in (0.0, 0.01):
        par_all = [net(s["p_ask"], s["win"], slip) for s in sig]
        par_unf = [net(s["p_ask"], s["win"], slip) for s in unfilled]
        for frac in (MAKER_FEE_FRAC, 0.0, 1.0):
            ver = [net(s["p_bid"], s["win"], 0.0, frac) for s in filled]
            res[(slip, frac)] = (ver, par_all, par_unf)
    ver, par_all, par_unf = res[(0.01, MAKER_FEE_FRAC)]
    weeks = max(math.ceil(days / 7.0 - 1e-9), 1)
    def line(tag, v, p, pu):
        out.append("%s: version PF %.2f (n %d, mean %+.2fc) | parent PF all signals %.2f (n %d, mean %+.2fc) | parent PF on unfilled %.2f (n %d) | net per contract-week version %+.3f parent %+.3f" % (
            tag, pf(v), len(v), 100 * (sum(v) / len(v) if v else 0), pf(p), len(p), 100 * (sum(p) / len(p) if p else 0), pf(pu), len(pu), sum(v) / weeks, sum(p) / weeks))
    line("PRIMARY (parent +1c, maker fee 25%)", ver, par_all, par_unf)
    for (slip, frac), (v, p, pu) in sorted(res.items()):
        if (slip, frac) != (0.01, MAKER_FEE_FRAC):
            line("sens parent +%dc maker fee %d%%" % (round(slip * 100), round(frac * 100)), v, p, pu)
    # halves by close time of the SIGNALS (median)
    half = n // 2
    def part(ss):
        f = [s for s in ss if s["filled"]]
        v = [net(s["p_bid"], s["win"], 0.0, MAKER_FEE_FRAC) for s in f]
        p = [net(s["p_ask"], s["win"], 0.01) for s in ss]
        return pf(v), pf(p), len(f)
    h1, h2 = part(sig[:half]), part(sig[half:])
    out.append("first half: version PF %.2f parent PF %.2f (filled %d) | second half: version PF %.2f parent PF %.2f (filled %d)" % (h1[0], h1[1], h1[2], h2[0], h2[1], h2[2]))
    c1 = pf(ver) - pf(par_all) >= BAR_PF
    par0 = res[(0.0, MAKER_FEE_FRAC)][1]
    c2_1 = sum(ver) / weeks >= sum(par_all) / weeks - 1e-12
    c2_0 = sum(ver) / weeks >= sum(par0) / weeks - 1e-12   # the stricter parent (+0c) governs: live fills are at or below the ask seen
    c2 = c2_0 and c2_1
    d1, d2 = h1[0] - h1[1], h2[0] - h2[1]
    c3 = d2 >= d1 - 1e-12
    c4 = len(filled) >= BAR_N
    miss = pf(par_unf) - pf(ver) >= BAR_PF if unfilled and filled else False
    out.append("7g BAR: (1) PF beats parent by 0.10: %s | (2) net per contract-week not lower (vs parent +0c: %s, vs +1c: %s; +0c governs): %s | (3) second half not worse (version minus parent, second half vs first): %s | (4) at least %d filled: %s" % (
        "met" if c1 else "not met", "met" if c2_0 else "not met", "met" if c2_1 else "not met", "met" if c2 else "not met", "met" if c3 else "not met", BAR_N, "met" if c4 else "not met (NOT_ENOUGH_DATA)"))
    falsified = (not c2) or miss
    out.append("adverse selection check (parent PF on missed windows, no-bid windows included, exceeds the version's PF on its fills by 0.10 or more): %s" % ("YES" if miss else "no"))
    out.append("FALSIFIED on development if (2) fails OR the missed windows' parent PF exceeds the version PF by 0.10 or more: (2) fails: %s | adverse selection: %s => %s" % ("yes" if not c2 else "no", "yes" if miss else "no", "FALSIFIED" if falsified else "not falsified"))
    if falsified and block == "dev":
        verdict = "FALSIFIED on development (filled %d%s)" % (len(filled), "" if c4 else ", below the 60 of bar (4)")
    elif not c4:
        verdict = "NOT_ENOUGH_DATA"
    else:
        verdict = "PASS the 7g bar (this block)" if (c1 and c2 and c3) else "does not meet the 7g bar"
    out.append("VERDICT (this block): " + verdict)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, choices=["V1", "V2"])
    ap.add_argument("--block", required=True, choices=["dev", "forward"])
    ap.add_argument("--book-root", required=True)
    ap.add_argument("--signals", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth1-recorded", default=None)
    ap.add_argument("--nc15depth1-hash", default=None, help="V2: file whose first line starts 'NC15DEPTH1 SCORER HASH:'")
    ap.add_argument("--heldout-list", default=None, help="the standing HELDOUT_PULL_RUNS.md (default: kalshi-scalper/workers/ beside this folder; an unreadable list refuses everything)")
    ap.add_argument("--now", default=None, help="test only: ISO time used in place of the clock for the read-after guard")
    a = ap.parse_args(argv)
    lo, hi = (epoch(x) for x in BLOCKS[(a.version, a.block)])
    marker = os.path.join(MARKER_DIR, "%s_%s_READ_DONE" % (a.version, a.block))   # fixed path, not under --out
    if os.path.exists(marker):
        print("already read: %s exists; refusing a second run" % marker)
        return 2
    msg = refuse_heldout([a.book_root, a.signals, a.out], a.heldout_list or HELDOUT_LIST)
    if msg:
        print(msg)
        return 2
    if a.version == "V1" and a.block == "dev" and not (a.depth1_recorded and check_marker_line(a.depth1_recorded, DEPTH1_MARKER_PREFIX)):
        print("refused: V1 development is not scored before DEPTH1's read is recorded (pass --depth1-recorded with the marker file the Head names; its first line must start %r)" % DEPTH1_MARKER_PREFIX)
        return 2
    ra = READ_AFTER.get((a.version, a.block))
    if a.version == "V2" and a.block == "dev":
        ra = V2_DEV_READ_AFTER
    now = epoch(a.now) if a.now else time.time()
    if ra and now < epoch(ra):
        print("refused: the %s %s block is read on or after %s" % (a.version, a.block, ra))
        return 2
    if a.version == "V2" and not (a.nc15depth1_hash and check_marker_line(a.nc15depth1_hash, NC15DEPTH1_HASH_PREFIX)):
        print("refused: V2 is not scored before NC15DEPTH1's scorer hash is on record (pass --nc15depth1-hash with the file the Head names; its first line must start %r)" % NC15DEPTH1_HASH_PREFIX)
        return 2
    book, trades, cover = load_run_folders(a.book_root)
    sigs, counts = [], {}
    with open(a.signals, newline="") as f:
        for r in csv.DictReader(f):
            ct = int(float(r["close_ts"]))
            if not (lo <= ct <= hi):
                continue
            w = one_window(a.version, r["ticker"], ct, book, trades, cover)
            counts[w["status"]] = counts.get(w["status"], 0) + 1
            if w["status"] == "signal":
                sigs.append(w)
    days = (hi - lo + 1) / 86400.0
    print("%s %s block (%s to %s, constants of the registration); candidate windows by status: %s" % (a.version, a.block, BLOCKS[(a.version, a.block)][0], BLOCKS[(a.version, a.block)][1], json.dumps(counts, sort_keys=True)))
    if a.version == "V2" or a.block == "dev":
        print("LABEL: " + LABELS[a.version])
    for l in evaluate(sigs, days, a.block):
        print(l)
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(MARKER_DIR, exist_ok=True)
    open(marker, "w").write("read done\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
