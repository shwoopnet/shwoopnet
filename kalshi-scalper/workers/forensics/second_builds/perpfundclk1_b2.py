#!/usr/bin/env python3
"""PERPFUNDCLK1 INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from Desk C's card PERPFUNDCLK1_CARD.md (commit 9e2d14cb) ONLY: no spec file and no definitions file exist, so every reading below is mine and is DECLARED. Desk C's plugin and prints were not opened.
Declared readings: (R1) the fill is at the quote of the candle NAMED (the one ending at T - offset, T + 1 min, ...), with the haircut on that quote (long: ask x (1 + h) in, bid x (1 - h) out; short: bid x (1 - h) in, ask x (1 + h) out); the card's phrase 'entry at the next candle's ask' is read as 'the ask of the entry candle' (as in PERPSLANE4). (R2) T = a print's own timestamp when it falls at 21:00:00Z; a name with ANY print not at 21:00:00Z is left out and counted. (R3) the previous rate = the rate of the latest print of that name strictly before T; a zero rate or none = no trade. (R4) the second threshold M = the median of the nonzero |previous rate| over every (name, T) of the development window, all names pooled, computed from funding rows only; rule: |previous rate| >= M. (R5) both legs usable (0 < bid < ask) or 'no mark'; one position at a time is moot (one trade a name a day per cell). (R6) net = gross - 2 x 0.0012 (12 bp a leg); arm C also net += -side x rate summed over prints with entry < ts < exit (side +1 long, -1 short). (R7) trading days = distinct dates of T with at least one of the nine names having a usable candle ending T - 60 min; trades a day = n / trading days, also printed per day with a trade. (R8) halves = the first floor(n/2) trades by (entry end, name) and the rest; PF with no losses = infinity; day z on the 0.0002 net by UTC date of T, p one sided; BH at 5% over m_total (cells with n >= 48 only, the rest count in m but have no p). (R9) development cut 1794787199 (everything with ts or candle end <= it).
usage: python3 -I perpfundclk1_b2.py <m_carried> <extract.sqlite> | python3 -I perpfundclk1_b2.py --selftest"""
import sys, math, sqlite3, collections, datetime, calendar
CUT = 1794787199; NAMES = ["KXNVDAPERP", "KXMUPERP", "KXSPCXPERP", "KXCOSTPERP", "KXTSLAPERP", "KXPLTRPERP", "KXMETAPERP", "KXAAPLPERP", "KXGOOGLPERP"]
H = (0.0002, 0.0005); FEE = 0.0012
def usable(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1]
def fillin(q, side, h): return q[1] * (1 + h) if side == 1 else q[0] * (1 - h)
def fillout(q, side, h): return q[0] * (1 - h) if side == 1 else q[1] * (1 + h)
def gross(qi, qo, side, h):
    a, b = fillin(qi, side, h), fillout(qo, side, h)
    return b / a - 1 if side == 1 else (a - b) / a
def pf(v):
    gw = sum(x for x in v if x > 0); ls = -sum(x for x in v if x < 0)
    return float("inf") if ls == 0 and gw > 0 else (gw / ls if ls else 0.0)
def zp(rows):
    d = collections.defaultdict(float)
    for r in rows: d[r["date"]] += r["net"]
    k = len(d)
    if k < 2: return None, None
    s = list(d.values()); mu = sum(s) / k; sd = math.sqrt(sum((a - mu) ** 2 for a in s) / (k - 1))
    if sd == 0: return None, None
    z = mu / (sd / math.sqrt(k)); return z, 0.5 * math.erfc(z / math.sqrt(2))
def bh(ps, m):
    o = sorted(range(len(ps)), key=lambda i: (ps[i], i)); k = 0
    for r, i in enumerate(o, 1):
        if ps[i] <= 0.05 * r / m: k = r
    return k
CELLS = [("A", off, thr) for off in (60, 30) for thr in (1, 2)] + [("C", off, thr) for off in (60, 30) for thr in (1, 2)] + [("B", 0, thr) for thr in (1, 2)]
def events(cd, fd):
    """-> (names kept, names left out, list of (name, T, prev_rate)) and the median M"""
    keep, out, ev = [], [], []
    for n in NAMES:
        p = sorted(t for t in fd.get(n, {}) if t <= CUT)
        if not p or any(t % 86400 != 75600 for t in p): out.append(n); continue
        keep.append(n)
        for i, t in enumerate(p):
            if i == 0: continue
            ev.append((n, t, fd[n][p[i - 1]]))
    return keep, out, ev
def run_cell(cell, cd, fd, ev, M):
    arm, off, thr = cell; tr = []; skips = collections.Counter()
    for (n, T, prev) in ev:
        if prev == 0: skips["zero previous rate"] += 1; continue
        if thr == 2 and not abs(prev) >= M: skips["below threshold"] += 1; continue
        payer = 1 if prev > 0 else -1                     # +1 longs pay
        if arm == "B": side = payer; e, x = T + 60, T + 31 * 60
        elif arm == "A": side = -payer; e, x = T - off * 60, T - 5 * 60
        else: side = -payer; e, x = T - off * 60, T + 31 * 60
        qe, qx = cd[n].get(e), cd[n].get(x)
        if not (usable(qe) and usable(qx)): skips["no mark"] += 1; continue
        f = sum(r for t, r in fd[n].items() if e < t < x) if arm == "C" else 0.0
        row = {"name": n, "e": e, "date": datetime.datetime.fromtimestamp(T, datetime.timezone.utc).date()}
        for h in H: row[h] = gross(qe, qx, side, h) - 2 * FEE - side * f
        row["gross0"] = gross(qe, qx, side, 0.0); row["net"] = row[H[0]]; row["span"] = int(arm == "C"); tr.append(row)
    tr.sort(key=lambda r: (r["e"], r["name"])); return tr, skips
def selftest():
    q1, q2 = (100.0, 100.2), (100.5, 100.7)
    assert abs(gross(q1, q2, 1, 0.0002) - ((100.5 * 0.9998) / (100.2 * 1.0002) - 1)) < 1e-12
    assert abs(gross(q1, q2, -1, 0.0002) - ((100.0 * 0.9998 - 100.7 * 1.0002) / (100.0 * 0.9998))) < 1e-12
    T = 1794690000 - 1794690000 % 86400 + 75600
    cd = {"KXNVDAPERP": {T - 3600: q1, T - 300: q2, T + 60: q1, T + 1860: q2}}
    fd = {"KXNVDAPERP": {T - 86400: 0.0004, T: 0.0003, T + 86400: 0.0}}
    keep, out, ev = events(cd, fd); assert "KXNVDAPERP" in keep and len(ev) == 2 and ev[0][2] == 0.0004
    trA, _ = run_cell(("A", 60, 1), cd, fd, ev, 0.0); assert len(trA) == 1 and trA[0]["name"] == "KXNVDAPERP" and abs(trA[0][H[0]] - (gross(q1, q2, -1, 0.0002) - 0.0024)) < 1e-12   # prev rate > 0: longs pay, the A trade is a SHORT
    del cd["KXNVDAPERP"][T + 1860]; assert len(run_cell(("C", 60, 1), cd, fd, ev, 0.0)[0]) == 0   # no candle at T + 31 min: no mark
    cd["KXNVDAPERP"][T + 1860] = q2; trC, _ = run_cell(("C", 60, 1), cd, fd, ev, 0.0); assert len(trC) == 1 and abs(trC[0][H[0]] - (gross(q1, q2, -1, 0.0002) - 0.0024 + 0.0003)) < 1e-12   # a short receives the print inside the hold
    trB, _ = run_cell(("B", 0, 1), cd, fd, ev, 0.0); assert len(trB) == 1 and abs(trB[0][H[0]] - (gross(q1, q2, 1, 0.0002) - 0.0024)) < 1e-12   # with the payer: long
    fd2 = {"KXNVDAPERP": {T - 86400: 0.0004, T + 30: 0.1}}; assert "KXNVDAPERP" in events(cd, fd2)[1]   # a print not at 21:00:00Z leaves the name out
    assert pf([1, -1]) == 1.0 and pf([1]) == float("inf") and pf([-1]) == 0.0
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    mcar = int(a[0]); db = sqlite3.connect("file:%s?mode=ro" % a[1], uri=True); cd = {n: {} for n in NAMES}; fd = {n: {} for n in NAMES}
    for t, e, b, k in db.execute("select ticker, end_ts, yes_bid, yes_ask from candle where end_ts <= %d" % CUT):
        if t in cd: cd[t].setdefault(e, (b, k))
    for t, ts, r in db.execute("select ticker, ts, rate from funding where ts <= %d" % CUT):
        if t in fd: fd[t].setdefault(ts, float(r))
    keep, out, ev = events(cd, fd)
    nz = [abs(p) for (_, _, p) in ev if p != 0]; M = sorted(nz)[len(nz) // 2] if len(nz) % 2 else (sorted(nz)[len(nz) // 2 - 1] + sorted(nz)[len(nz) // 2]) / 2 if nz else float("inf")
    perN = collections.Counter(n for (n, _, p) in ev if p != 0)
    print("FUNDING ROWS ONLY (no price read): names kept %d left out %s; events (name, T with a previous rate) %d; nonzero previous rate %d; per name %s; median nonzero |prev| M = %.12g" % (len(keep), out, len(ev), len(nz), dict(perN), M), flush=True)
    tdays = {datetime.datetime.fromtimestamp(T, datetime.timezone.utc).date() for (n, T, p) in ev if usable(cd[n].get(T - 3600))}
    m_total = mcar + 10; res = []
    for cell in CELLS:
        tr, sk = run_cell(cell, cd, fd, ev, M); n = len(tr); v = [r[H[0]] for r in tr]; w = [r[H[1]] for r in tr]; hf = n // 2
        days = len({r["date"] for r in tr}); z, p = zp(tr) if n else (None, None); gm = sum(r["gross0"] for r in tr) / n * 1e4 if n else None
        gate = n >= 100 and days >= 10 and pf(v) >= 1.3 and pf(v[:hf]) >= 1.0 and pf(v[hf:]) >= 1.0 and pf(w) >= 1.0
        res.append((cell, n, days, n / len(tdays) if tdays else 0.0, pf(v) if n else None, pf(w) if n else None, gm, z, p, gate, dict(sk)))
    ps = [r[8] for r in res if r[1] >= 48 and r[8] is not None]; k = bh(ps, m_total) if ps else 0
    print("trading days with a usable T-60 candle %d; cells 10; m_total %d" % (len(tdays), m_total))
    for r in res: print("%s off %d thr %d | n %d days %d per_day %.4f | PF gate %s stress %s | gross mean bp %s | z %s p %s | gate %s | skips %s" % (r[0][0], r[0][1], r[0][2], r[1], r[2], r[3], "%.6f" % r[4] if r[4] is not None else "-", "%.6f" % r[5] if r[5] is not None else "-", "%.4f" % r[6] if r[6] is not None else "-", "%.6f" % r[7] if r[7] is not None else "-", "%.6e" % r[8] if r[8] is not None else "-", r[9], r[10]))
    print("gate passes", sum(1 for r in res if r[9]), "BH survivors", k)
if __name__ == "__main__": main(sys.argv[1:])
