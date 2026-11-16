#!/usr/bin/env python3
"""PERPSLANE4 INDEPENDENT SECOND BUILD (Forensics desk, Nov 16, 2026). Written from PERPSLANE4_DEFINITIONS.md, specs/PERPSLANE4.spec.json (sha256 02bd15fd...) and LANE4_HAND_CASE.md on claude/testing-desk (a5bc1912b) ONLY. The Testing Desk's plugin, loader and prints were not opened before this file was committed.
Declared readings (each can move a count): (R1) data start of a name = its first candle end; an entry or exit end at or before it is 'boundary'. (R2) A2 needs the underlyings u[name][ET date] = (official open, previous close); this build takes them as an argument and has none (no Databento read), so A2 prints 'no underlying' skips only. (R3) trade day = the ET date of the entry end; trading days = ET dates before the boundary on which at least one POOL name has a usable candle ending 09:31 ET. (R4) the gate and BH are per fee (0.0012 and 0.0005 a side) and each uses that fee's own nets; the day z uses the h 0.0002 net of that fee. (R5) the one-position check uses the previous TAKEN trade (one that passed marks, funding and boundary) of that rule and name. (R6) ET midday offset: EDT (UTC-4) for ET dates up to 2026-10-31, EST (UTC-5) from 2026-11-01 (the change is 2026-11-01T06:00Z).
usage: python3 -I perpslane4_b2.py --selftest | python3 -I perpslane4_b2.py <m_carried> <extract.sqlite> [<extract.sqlite> ...]"""
import sys, os, math, sqlite3, collections, calendar, datetime, itertools
BOUNDARY = 1794873600; H = (0.0002, 0.0005); FEES = (0.0012, 0.0005)
def et_offset(L):   # hours to add to ET local to get UTC, read at midday of ET date L
    return 4 if calendar.timegm((L.year, L.month, L.day, 16, 0, 0)) < calendar.timegm((2026, 11, 1, 6, 0, 0)) else 5
def et_end(L, hh, mm): return calendar.timegm((L.year, L.month, L.day, hh, mm, 0)) + et_offset(L) * 3600
def et_date(ts):
    for off in (4, 5):
        d = datetime.datetime.fromtimestamp(ts - off * 3600, datetime.timezone.utc).date()
        if et_offset(d) == off: return d
    return datetime.datetime.fromtimestamp(ts - 5 * 3600, datetime.timezone.utc).date()
def is_wd(d): return d.weekday() < 5
def next_wd(d):
    d = d + datetime.timedelta(days=1)
    while not is_wd(d): d += datetime.timedelta(days=1)
    return d
def prev_wd(d):
    d = d - datetime.timedelta(days=1)
    while not is_wd(d): d -= datetime.timedelta(days=1)
    return d
def usable(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1]
def mid(q): return (q[0] + q[1]) / 2
def fill(q, side, h): return q[1] * (1 + h) if side == "long" else q[0] * (1 - h)
def leave(q, side, h): return q[0] * (1 - h) if side == "long" else q[1] * (1 + h)
def gross(entry, exit_, side, h):
    f, x = fill(entry, side, h), leave(exit_, side, h)
    return x / f - 1 if side == "long" else (f - x) / f
class Name:
    def __init__(s, tk, cd, fd): s.tk, s.c, s.f = tk, cd, fd; s.ts = sorted(fd); s.start = min(cd) if cd else None
def booked(nm, e, x):
    p = nm.ts
    if not p or e < p[0] or x > p[-1] + 26 * 3600: return False, 0.0
    for a, b in zip(p, p[1:]):
        if b - a > 26 * 3600 and e < b and x > a: return False, 0.0
    return True, sum(nm.f[t] for t in p if e < t < x)
def build_rules():
    R = []
    for cl, sd in itertools.product(("weekend", "weeknight"), ("long", "short")): R.append(("A", cl, sd))
    for cl, thr, mode, ex in itertools.product(("Monday", "TueFri"), (40, 100), ("follow", "fade"), ("T30", "T60", "TC")): R.append(("A2", cl, thr, mode, ex))
    for n, thr, mode, ex in itertools.product((5, 15, 30), (20, 40), ("follow", "fade"), ("T30", "T60", "TC")): R.append(("B1", n, thr, mode, ex))
    for thr, mode, ex in itertools.product((20, 40), ("follow", "fade"), ("T1601", "TO")): R.append(("B2", thr, mode, ex))
    for sd in ("long", "short"): R.append(("B3", sd))
    for x, y, sr in itertools.product((60, 30, 15), (15, 30, 60), ("long", "short", "RECEIVE")): R.append(("C", x, y, sr))
    return R
def dirside(up, mode): return ("long" if up else "short") if mode == "follow" else ("short" if up else "long")
def candidates(rule, nm, days, u=None):
    """yield (entry_end, exit_end, side, day, entry_q, exit_q, reason_or_None) in entry order; reason 'no mark' or 'no underlying' for an event that fires but cannot be priced."""
    c = nm.c; kind = rule[0]; out = []
    def q(L, hh, mm): return c.get(et_end(L, hh, mm))
    for L in days:
        if kind == "A":
            _, cl, sd = rule
            if (L.weekday() == 4) != (cl == "weekend"): continue
            e, x = et_end(L, 16, 0), et_end(next_wd(L), 9, 31); qe, qx = c.get(e), c.get(x)
            out.append((e, x, sd, L, qe, qx, None if usable(qe) and usable(qx) else "no mark"))
        elif kind == "A2":
            _, cl, thr, mode, ex = rule
            if (L.weekday() == 0) != (cl == "Monday"): continue
            uu = (u or {}).get(nm.tk, {}).get(L)
            if uu is None: out.append((et_end(L, 9, 31), et_end(L, 9, 31), "long", L, None, None, "no underlying")); continue
            p0 = q(L, 9, 25); pl = prev_wd(L)
            while et_end(pl, 16, 0) not in c and (L - pl).days < 10: pl = prev_wd(pl)
            qp = q(pl, 16, 0); qE = q(L, 9, 31)
            if not usable(p0) or not usable(qp) or not usable(qE): out.append((et_end(L, 9, 31), et_end(L, 9, 31), "long", L, None, None, "no mark")); continue
            g = (uu[0] / uu[1] - 1) - (mid(p0) / mid(qp) - 1); half = ((qE[1] - qE[0]) / 2) / mid(qE)
            if not (round(abs(g), 9) > round(2 * half, 9) and round(abs(g) * 10000, 9) >= thr): continue
            e = et_end(L, 9, 31); x = {"T30": e + 1800, "T60": e + 3600, "TC": et_end(L, 16, 0)}[ex]; qx = c.get(x)
            out.append((e, x, dirside(g > 0, mode), L, qE, qx, None if usable(qx) else "no mark"))
        elif kind == "B1":
            _, n, thr, mode, ex = rule
            eO, eN = et_end(L, 9, 31), et_end(L, 9, 31) + n * 60; qO, qN = c.get(eO), c.get(eN)
            if not (usable(qO) and usable(qN)): continue
            m = mid(qN) / mid(qO) - 1
            if not round(abs(m) * 10000, 9) >= thr: continue
            x = {"T30": eN + 1800, "T60": eN + 3600, "TC": et_end(L, 16, 0)}[ex]; qx = c.get(x)
            out.append((eN, x, dirside(m > 0, mode), L, qN, qx, None if usable(qx) else "no mark"))
        elif kind == "B2":
            _, thr, mode, ex = rule
            q0, q1 = q(L, 15, 0), q(L, 15, 30)
            if not (usable(q0) and usable(q1)): continue
            m = mid(q1) / mid(q0) - 1
            if not round(abs(m) * 10000, 9) >= thr: continue
            x = et_end(L, 16, 1) if ex == "T1601" else et_end(next_wd(L), 9, 31); qx = c.get(x)
            out.append((et_end(L, 15, 30), x, dirside(m > 0, mode), L, q1, qx, None if usable(qx) else "no mark"))
        elif kind == "B3":
            e, x = et_end(L, 15, 30), et_end(L, 16, 1); qe, qx = c.get(e), c.get(x)
            out.append((e, x, rule[1], L, qe, qx, None if usable(qe) and usable(qx) else "no mark"))
    return out
def candidates_c(rule, nm):
    _, xm, ym, sr = rule; out = []
    for T in nm.ts:
        e, x = T - xm * 60, T + ym * 60
        if sr == "RECEIVE":
            prior = [t for t in nm.ts if t < e]
            if not prior: continue
            r = nm.f[prior[-1]]
            if r == 0: continue
            side = "short" if r > 0 else "long"
        else: side = sr
        qe, qx = nm.c.get(e), nm.c.get(x)
        out.append((e, x, side, et_date(e), qe, qx, None if usable(qe) and usable(qx) else "no mark"))
    return out
def run_rule(rule, names, days_by, u=None):
    """returns trades {(h,fee)->list of (entry_end, name, day, net)} plus counts"""
    trades = {(h, fee): [] for h in H for fee in FEES}; cnt = collections.Counter(); unb = collections.Counter()
    for nm in names:
        last_exit = None
        cands = candidates_c(rule, nm) if rule[0] == "C" else candidates(rule, nm, days_by[nm.tk], u)
        for (e, x, side, L, qe, qx, why) in sorted(cands, key=lambda t: t[0]):
            if last_exit is not None and e < last_exit: cnt["cooldown"] += 1; continue
            if why: cnt[why] += 1; continue
            ok, f = booked(nm, e, x)
            if not ok: unb[nm.tk] += 1; cnt["funding unbooked"] += 1; continue
            if nm.start is not None and e <= nm.start or e >= BOUNDARY or x >= BOUNDARY: cnt["boundary"] += 1; continue
            last_exit = x
            for h in H:
                g = gross(qe, qx, side, h); fl = f if side == "long" else -f
                for fee in FEES: trades[(h, fee)].append((e, nm.tk, L, g - 2 * fee - fl))
    return trades, cnt, unb
def pf(v):
    gw = sum(x for x in v if x > 0); ls = -sum(x for x in v if x < 0)
    return float("inf") if ls == 0 and gw > 0 else (gw / ls if ls else 0.0)
def zp(v):
    d = collections.defaultdict(float)
    for (e, tk, L, net) in v: d[L] += net
    k = len(d)
    if k < 2: return None, None
    s = list(d.values()); mu = sum(s) / k; sd = math.sqrt(sum((a - mu) ** 2 for a in s) / (k - 1))
    if sd == 0: return None, None
    z = mu / (sd / math.sqrt(k)); return z, 0.5 * math.erfc(z / math.sqrt(2))
def evaluate(tr, trading_days):
    r = {}
    for fee in FEES:
        a = sorted(tr[(H[0], fee)], key=lambda t: (t[0], t[1])); b = sorted(tr[(H[1], fee)], key=lambda t: (t[0], t[1])); n = len(a)
        def halves_ok(s, thr): 
            h = len(s) // 2; v = [t[3] for t in s]; return pf(v) >= thr and (not s or (pf(v[:h]) >= 1.0 and pf(v[h:]) >= 1.0))
        days = len({t[2] for t in a}); z, p = zp(a)
        p1 = pf([t[3] for t in a]); p2 = pf([t[3] for t in b]); perday = n / trading_days if trading_days else 0.0
        gate = n >= 100 and days >= 10 and perday >= 3 and p1 >= 1.3 and halves_ok(a, 1.3) and p2 >= 1.0 and halves_ok(b, 1.0) if n else False
        r[fee] = {"n": n, "days": days, "perday": perday, "pf2": p1, "pf5": p2, "z": z, "p": p, "gate": gate}
    return r
def bh(ps, m):
    o = sorted(range(len(ps)), key=lambda i: (ps[i], i)); k = 0
    for r, i in enumerate(o, 1):
        if ps[i] <= 0.05 * r / m: k = r
    return k
def selftest():
    D = datetime.date; L = D(2026, 10, 9)   # a Friday, EDT
    assert et_end(L, 16, 0) == calendar.timegm((2026, 10, 9, 20, 0, 0)) and et_end(D(2026, 11, 2), 9, 31) == calendar.timegm((2026, 11, 2, 14, 31, 0)) and next_wd(L) == D(2026, 10, 12)
    assert et_date(calendar.timegm((2026, 10, 10, 3, 59, 0))) == D(2026, 10, 9) and et_date(calendar.timegm((2026, 11, 1, 6, 0, 0))) == D(2026, 11, 1)
    # hand case A: Friday 16:00 candle bid 100.60 ask 100.70, Monday 09:31 bid 100.90 ask 101.00
    g = gross((100.60, 100.70), (100.90, 101.00), "long", 0.0002)
    assert abs(fill((100.60, 100.70), "long", 0.0002) - 100.72014) < 1e-9 and abs(leave((100.90, 101.00), "long", 0.0002) - 100.87982) < 1e-9 and abs(g - 0.0015854) < 1e-7
    # B1 N=15: O mid 100.00 (99.99, 100.01), E mid 100.30 (100.29, 100.31): m = +0.0030; follow long fill 100.33062, exit bid 100.60 -> 100.57988, gross 0.0024844; fade short fill 100.26994, exit ask 100.61 -> 100.63012, gross -0.0035922
    assert round(abs(mid((100.29, 100.31)) / mid((99.99, 100.01)) - 1) * 10000, 9) == 30.0
    # NOTE: the hand case writes the long fill as 100.33062, but 100.31 x 1.0002 = 100.330062, so its gross 0.0024844 should read 0.00248996 (the fade case and A and C check out)
    assert abs(fill((100.29, 100.31), "long", 0.0002) - 100.330062) < 1e-9 and abs(gross((100.29, 100.31), (100.60, 100.62), "long", 0.0002) - 0.0024899616) < 1e-9 and abs(gross((100.29, 100.31), (100.60, 100.61), "short", 0.0002) - (-0.0035922)) < 2e-7
    # C: short, entry bid 100.00, exit ask 100.20: gross -0.0024007; print rate 0.0003 received: net taker = -0.0024007 - 0.0024 + 0.0003
    gs = gross((100.00, 100.10), (100.10, 100.20), "short", 0.0002); assert abs(gs - (-0.24004 / 99.98)) < 1e-12 and abs(gs - (-0.0024007)) < 5e-7   # the hand case rounds to -0.0024007
    nm = Name("T", {}, {1000: 0.0004, 80000: 0.0003, 160000: 0.0002}); ok, f = booked(nm, 500, 81000)
    assert ok is False                                   # e (99000) is before the first print: unbooked
    ok, f = booked(nm, 1001, 80500); assert ok and abs(f - 0.0003) < 1e-12
    assert booked(Name("T", {}, {1000: 0.0004, 100000: 0.0003}), 1001, 100500)[0] is False   # a gap of more than 26 h between neighbours spanned by the position
    assert abs((gs - 2 * 0.0012 - (-f)) - (-0.0045007)) < 5e-7
    assert booked(Name("T", {}, {}), 1, 2)[0] is False and booked(nm, 1001, 160000 + 26 * 3600 + 1)[0] is False
    assert len(build_rules()) == 101
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    mcar = int(a[0]); cd = collections.defaultdict(dict); fd = collections.defaultdict(dict); uu = collections.defaultdict(dict)
    for path in a[1:]:
        db = sqlite3.connect("file:%s?mode=ro" % path, uri=True); tabs = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
        if "candle" in tabs:
            for tk, e, b, k in db.execute("select ticker, end_ts, yes_bid, yes_ask from candle"): cd[tk].setdefault(e, (b, k))
        if "underlying" in tabs:     # underlying(ticker, et_date 'YYYY-MM-DD', u_open, u_prev): the official open of the ET date and the previous trading day's official close, for A2 only
            for tk, ds, uo, up in db.execute("select ticker, et_date, u_open, u_prev from underlying"): uu[tk].setdefault(datetime.date.fromisoformat(ds), (float(uo), float(up)))
        if "funding" in tabs:
            for tk, ts, r in db.execute("select ticker, ts, rate from funding"): fd[tk].setdefault(ts, float(r))
    pool = []
    for tk in sorted(cd):
        dates = {et_date(e) for e in cd[tk]}
        if len(dates) >= 5 and len(fd.get(tk, {})) >= 2: pool.append(Name(tk, cd[tk], fd[tk]))
    alldays = sorted({et_date(e) for nm in pool for e in nm.c if e < BOUNDARY and is_wd(et_date(e))})
    days_by = {nm.tk: [d for d in alldays] for nm in pool}
    trading_days = len({et_date(e) for nm in pool for e in nm.c if e < BOUNDARY and is_wd(et_date(e)) and e == et_end(et_date(e), 9, 31) and usable(nm.c[e])})
    print("names in the pool", len(pool), "of", len(cd), "with candles; ET weekdays", len(alldays), "trading days", trading_days, "rules", len(build_rules()), "m_total", mcar + 101, flush=True)
    res = []; skips = collections.Counter(); unb = collections.Counter()
    for rule in build_rules():
        tr, cnt, ub = run_rule(rule, pool, days_by, uu); skips.update(cnt); unb.update(ub); res.append((rule, evaluate(tr, trading_days)))
    print("skips", dict(skips), "funding-unbooked names", len(unb))
    for fee in FEES:
        ps = [r[fee]["p"] for _, r in res if r[fee]["p"] is not None]; k = bh(ps, mcar + 101)
        print("fee", fee, "rules with n>0", sum(1 for _, r in res if r[fee]["n"]), "gate passes", sum(1 for _, r in res if r[fee]["gate"]), "p defined", len(ps), "BH survivors", k)
    out = os.environ.get("OUTLIST")
    if out:
        with open(out, "w") as fh:
            for rule, r in res:
                for fee in FEES: q = r[fee]; fh.write("%s fee %.4f n %d days %d perday %.6f pf2 %.12f pf5 %.12f z %s p %s gate %s\n" % ("|".join(str(x) for x in rule), fee, q["n"], q["days"], q["perday"], q["pf2"], q["pf5"], "%.12f" % q["z"] if q["z"] is not None else "-", "%.12e" % q["p"] if q["p"] is not None else "-", q["gate"]))
if __name__ == "__main__": main(sys.argv[1:])
