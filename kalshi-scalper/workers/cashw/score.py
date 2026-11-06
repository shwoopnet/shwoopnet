#!/usr/bin/env python3 -I
"""CASHOPEN2, CASHCLOSE2, CASHGAP2, OVN5 scorer (index perps vs Yahoo 1 minute cash). Written and frozen BEFORE any rule outcome was computed.
Convention (tested on a known jump, corr 0.991 at shift 0 and about 0.02 at every other shift, registration file): Kalshi candle ending T carries the
quote AT T; Yahoo bar starting S has its close AT S+60, so cash(T) = close of the bar that starts at T-60; cash open of 09:30 = open of the bar starting 09:30.
Held-out dates are never read: the date cap is applied when the files are loaded (common.py)."""
import sys, os, math, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
DEV_CAP = dt.date(2026, 11, 3)          # Nov 4 and Nov 5 held out (last third of the 6 overlap dates)
OVN_CAP = dt.date(2026, 10, 30)         # OVN5: Nov 1 onward is OVN1's own held-out third, not read here
MEDSPREAD = {"KXUS500PERP": 0.95, "KXUSTECH100PERP": 1.09}
FEES = (5, 12, 24)

def trading_dates(C, cap):
    s = set()
    for t in C["SPY"]:
        d = dt.datetime.fromtimestamp(t, ET)
        if d.weekday() < 5 and d.date() <= cap and (d.hour, d.minute) == (10, 0): s.add(d.date())
    return sorted(s)
def prev_date(dates_all, d):
    p = [x for x in dates_all if x < d]; return p[-1] if p else None
def mid(q): return (q[0] + q[1]) / 2
def cashT(F, T): v = F.get(T - 60); return v[3] if v else None
def spread_bp(q): return 1e4 * (q[1] - q[0]) / mid(q)

def stats(rows, fee, label):
    """rows: (date, gross_mid_bps, net_at_fee_function)"""
    if not rows: return "%s: n 0" % label
    nets = [r["gross_x"] - 2 * fee for r in rows]            # gross_x = return after crossing at bid/ask, before fee
    w = sum(x for x in nets if x > 0); l = -sum(x for x in nets if x < 0)
    byd = {}
    for r, x in zip(rows, nets): byd.setdefault(r["date"], []).append(x)
    dm = [sum(v) / len(v) for v in byd.values()]
    z = (sum(dm) / len(dm)) / (math.sqrt(sum((a - sum(dm) / len(dm)) ** 2 for a in dm) / (len(dm) - 1)) / math.sqrt(len(dm))) if len(dm) > 2 else float("nan")
    return "%s fee %d: n %d on %d dates, gross-mid %+.1f, after crossing %+.1f, net %+.1f bps, PF %s, clustered z %s" % (
        label, fee, len(rows), len(byd), sum(r["gross_m"] for r in rows) / len(rows), sum(r["gross_x"] for r in rows) / len(rows),
        sum(nets) / len(nets), ("%.2f" % (w / l)) if l else "inf", ("%.2f" % z) if z == z else "n/a")

def report(name, trig, ctl, dates, bar_trades=100, bar_dates=30):
    print("=" * 8, name, "dev dates", [str(d) for d in dates])
    half = len(dates) // 2; d1 = set(dates[:half])
    for lab, rows in (("TRIGGER", trig), ("CONTROL", ctl)):
        for fee in FEES: print(stats(rows, fee, lab))
    for lab, rows in (("TRIGGER", trig),):
        for hn, hs in (("D1", [r for r in rows if r["date"] in d1]), ("D2", [r for r in rows if r["date"] not in d1])):
            print(stats(hs, 12, lab + " " + hn))
        if rows:
            be = sum(r["gross_x"] for r in rows) / len(rows) / 2
            print("break-even fee per side (after crossing): %+.2f bps" % be)
    nt = len(trig); nd = len(set(r["date"] for r in trig))
    print("VERDICT:", "NOT_ENOUGH_DATA (trades %d of %d, trigger dates %d, dev dates %d, bar %d dates)" % (nt, bar_trades, nd, len(dates), bar_dates) if nt < bar_trades or len(dates) < bar_dates else "bars met: apply FALSIFIED rules")
    for r in trig: print("  ", r["tag"])

def mk(date, pk, tag, s, p_in, p_out, entry_px, exit_px):
    gm = s * (mid(p_out) / mid(p_in) - 1) * 1e4
    gx = s * (exit_px / entry_px - 1) * 1e4
    return dict(date=date, gross_m=gm, gross_x=gx, tag=tag)

def px_in(q, s): return q[1] if s > 0 else q[0]       # buy at ask, sell at bid
def px_out(q, s): return q[0] if s > 0 else q[1]

def main():
    Cdev = cash(DEV_CAP)                      # held-out dates are never loaded
    dates = trading_dates(Cdev, DEV_CAP)
    allc = [dt.date(2026, 10, 28)] + dates   # calendar for 'previous trading day' (Oct 28 has perp candles, no Yahoo bars)
    P = {tk: perp(tk, DEV_CAP) for tk in PERPS}
    # ---- CASHOPEN2
    trig, ctl = [], []
    for tk, etf in PERPS.items():
        F = Cdev[etf]
        for d in dates:
            o = F.get(ets(d, 9, 30)); q0 = P[tk].get(ets(d, 9, 30))
            if not o or not q0: continue
            for hh, mm in ((9, 31), (9, 33)):
                Ts = ets(d, hh, mm); q1 = P[tk].get(Ts); q2 = P[tk].get(Ts + 120); c1 = cashT(F, Ts)
                if not (q1 and q2 and c1): continue
                g = (c1 / o[0] - 1) * 1e4 - (mid(q1) / mid(q0) - 1) * 1e4
                s = 1 if g > 0 else -1
                r = mk(d, tk, "%s %s %02d:%02d g %+.1f bp" % (tk[2:-4], d, hh, mm, g), s, q1, q2, px_in(q1, s), px_out(q2, s))
                (trig if abs(g) >= 10 else ctl).append(r)
    report("CASHOPEN2", trig, ctl, dates)
    # ---- CASHCLOSE2
    trig, ctl = [], []; skipped = 0
    for tk, etf in PERPS.items():
        F = Cdev[etf]
        for d in dates:
            pd_ = prev_date(allc, d)
            pc = cashT(F, ets(pd_, 16, 0)) if pd_ else None; c1 = cashT(F, ets(d, 15, 40))
            q1 = P[tk].get(ets(d, 15, 40)); q2 = P[tk].get(ets(d, 16, 0))
            if not (pc and c1 and q1 and q2): skipped += 1; continue
            dd = (c1 / pc - 1) * 1e4; s = 1 if dd > 0 else -1
            trig.append(mk(d, tk, "%s %s d %+.1f bp" % (tk[2:-4], d, dd), s, q1, q2, px_in(q1, s), px_out(q2, s)))
            ctl.append(mk(d, tk, "ctl", 1, q1, q2, px_in(q1, 1), px_out(q2, 1)))
    print("CASHCLOSE2 skipped perp-days (no prior cash close or missing candle):", skipped)
    report("CASHCLOSE2 (trigger = momentum, control = always long)", trig, ctl, dates)
    # ---- CASHGAP2
    trig, ctl = [], []; agree = []
    for tk, etf in PERPS.items():
        F = Cdev[etf]
        for d in dates:
            pd_ = prev_date(allc, d)
            pc = cashT(F, ets(pd_, 16, 0)) if pd_ else None; o = F.get(ets(d, 9, 30))
            q1 = P[tk].get(ets(d, 9, 30)); q2 = P[tk].get(ets(d, 9, 40))
            if not (pc and o and q1 and q2): continue
            gap = (o[0] / pc - 1) * 1e4; s = -1 if gap > 0 else 1
            r = mk(d, tk, "%s %s gap %+.1f bp" % (tk[2:-4], d, gap), s, q1, q2, px_in(q1, s), px_out(q2, s))
            (trig if abs(gap) >= 30 else ctl).append(r)
            agree.append((gap, (mid(q2) / mid(q1) - 1) * 1e4))
    report("CASHGAP2 (fade; control = same fade, |gap| < 30 bp)", trig, ctl, dates)
    if agree:
        same = sum(1 for g, r in agree if g * r > 0)
        print("information: perp 09:30 to 09:40 return has the gap sign on %d of %d perp-dates (nonzero)" % (same, len(agree)))
        for g, r in agree: print("   gap %+.1f bp  perp 10 min return %+.1f bp" % (g, r))
    # ---- OVN5
    trig, ctl = [], []; info = []; ovd = trading_dates(cash(OVN_CAP), OVN_CAP)
    Pov = {tk: perp(tk, OVN_CAP) for tk in PERPS}; Cov = cash(OVN_CAP)
    for tk, etf in PERPS.items():
        for d in ovd:
            pd_ = prev_date(allc, d)
            qa = Pov[tk].get(ets(d, 8, 55)); qc = Pov[tk].get(ets(pd_, 16, 0)); qx = Pov[tk].get(ets(d, 10, 0))
            if not (qa and qc and qx): continue
            gp = (mid(qa) / mid(qc) - 1) * 1e4; sp = spread_bp(qa)
            F = Cov[etf]; pc = cashT(F, ets(pd_, 16, 0)); o = F.get(ets(d, 9, 30))
            gc = (o[0] / pc - 1) * 1e4 if (pc and o) else None
            info.append((tk[2:-4], str(d), round(gp, 1), None if gc is None else round(gc, 1), round(sp, 2)))
            if abs(gp) >= 30 and abs(gp) >= 5 * sp and sp <= 3 * MEDSPREAD[tk]:
                s = -1 if gp > 0 else 1
                trig.append(mk(d, tk, "%s %s g_p %+.1f bp" % (tk[2:-4], d, gp), s, qa, qx, px_in(qa, s), px_out(qx, s)))
                ctl.append(mk(d, tk, "ctl", -s, qa, qx, px_in(qa, -s), px_out(qx, -s)))
    report("OVN5 (fade; control = continuation)", trig, ctl, ovd)
    print("information (index, date, perp overnight gap bp, ETF cash gap bp, entry spread bp):")
    for i in info: print("  ", i)
main()
