"""MMSIM1 development-only diagnostics for a 1-lot live probe note. Desk A, Nov 12 2026.
Held data only (quote-data:book, events closing before 2026-11-07T15:00:00Z). Zero API calls.
usage: python3 -I mm_probe_diag.py <data_root>"""
import sys, os, glob, gzip, csv, math, calendar, statistics as st, random
from datetime import datetime
from collections import defaultdict
DATA = sys.argv[1]; CUTOFF = "2026-11-07T15:00:00Z"; random.seed(20261112)
def iso_ms(s):
    s = s.strip().replace("Z", "")
    a, b = (s.split(".") + ["0"])[:2]; b = (b + "000000")[:6]
    return calendar.timegm(datetime.strptime(a, "%Y-%m-%dT%H:%M:%S").timetuple()) * 1000 + int(b) // 1000
def f(x):
    try: return float(x)
    except Exception: return None
snaps = defaultdict(list); close_of = {}
for path in sorted(glob.glob(os.path.join(DATA, "book", "*", "*", "book.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["close_time"] >= CUTOFF: continue
            t = r["ticker"]; close_of[t] = r["close_time"]
            snaps[t].append((int(r["poll_ts_local_ms"]), f(r["yes_bid_px_1"]), f(r["yes_bid_sz_1"]), f(r["no_bid_px_1"]), f(r["no_bid_sz_1"])))
for t in snaps: snaps[t].sort()
trades = defaultdict(list); seen = set()
for path in sorted(glob.glob(os.path.join(DATA, "book", "*", "*", "trades.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            t = r["ticker"]
            if t not in close_of or r["trade_id"] in seen: continue
            seen.add(r["trade_id"])
            trades[t].append((iso_ms(r["created_time"]), round(float(r["yes_price_dollars"]), 4), float(r["count_fp"]), r["taker_outcome_side"]))
for t in trades: trades[t].sort()
def fee(p, rounded):
    x = 0.07 * p * (1 - p)
    return math.ceil(x * 100 - 1e-9) / 100 if rounded else x
def side_bid(s, side): return s[1] if side == "yes" else s[3]
def side_mid(s, side):
    if not (s[1] and s[3]): return None
    m = (s[1] + 1 - s[3]) / 2
    return m if side == "yes" else 1 - m
legs = []; strikes = []
for t, ss in snaps.items():
    T = iso_ms(close_of[t]); w0, w1 = T - 50 * 60000, T - 15 * 60000
    inwin = [s for s in ss if w0 <= s[0] < w1]
    if not inwin: continue
    s0 = inwin[0]
    if not (s0[1] and s0[3] and s0[1] > 0 and s0[3] > 0): continue
    fl = [s for s in ss if s[0] <= w1][-1]
    L = {}
    for side, ip, isz in (("yes", 1, 2), ("no", 3, 4)):
        post = next((s for s in inwin if s[ip] is not None and s[ip] > 0 and s[isz] is not None), None)
        if post is None: continue
        p, q, tp = post[ip], post[isz], post[0]
        level, hit = (round(p, 4), "no") if side == "yes" else (round(1 - p, 4), "yes")
        cum = 0.0; ft = None; ffrac = None; through = 0.0; tt = None
        for (cm, yp, cnt, sd) in trades.get(t, ()):
            if cm <= tp or cm > w1: continue
            if sd == hit and abs(yp - level) < 1e-6:
                cum += cnt
                if ft is None and cum >= q + 1:
                    ft = cm; ffrac = abs(cnt - round(cnt)) > 0.001
            # trades at a WORSE price for the seller (through our level): our order has price priority over them
            if sd == hit and ((side == "yes" and yp < level - 1e-6) or (side == "no" and yp > level + 1e-6)):
                through += cnt
                if tt is None: tt = cm
        # did the best bid of our side leave our price before the fill / the end?
        last_at = max((s[0] for s in inwin if s[0] >= tp and s[ip] is not None and abs(s[ip] - p) < 1e-6), default=tp)
        bt = next((x[0] for x in inwin if x[0] > tp and (x[ip] is None or x[ip] < p - 1e-6)), None)
        nxt = None
        if tt is not None:
            sx = next((x for x in ss if x[0] >= tt + 3000), None)
            nxt = None if sx is None else (sx[ip] is None or sx[ip] < p - 1e-6)
        rec = dict(bt=bt, nxt=nxt, ev=close_of[t], t=t, side=side, p=p, q=q, tp=tp, lead_min=(T - tp) / 60000, filled=ft is not None, ft=ft, wait=(ft - tp) / 1000 if ft else None,
                   ffrac=ffrac, cum=cum, through=through, tt=tt, at_touch_sec=(last_at - tp) / 1000)
        if ft:
            def mid_at(ms):
                s = next((x for x in ss if x[0] >= ms), None)
                return side_mid(s, side) if s and s[0] <= w1 + 5000 else None
            m0 = side_mid(next((x for x in reversed(ss) if x[0] <= ft), post), side)
            rec.update(m0=m0, m60=mid_at(ft + 60000), m300=mid_at(ft + 300000), mfl=side_mid(fl, side), flbid=side_bid(fl, side))
        legs.append(rec); L[side] = rec
    if not L: continue
    y, n = L.get("yes"), L.get("no")
    yf, nf = bool(y and y["filled"]), bool(n and n["filled"])
    out = dict(ev=close_of[t], t=t, kind="none", pnl=0.0, pnl_r=0.0, cost=0.0)
    if yf and nf:
        out.update(kind="pair", pnl=1 - y["p"] - n["p"], pnl_r=1 - y["p"] - n["p"], cost=y["p"] + n["p"])
    elif yf or nf:
        l = y if yf else n; bid = l["flbid"] or 0.0
        out.update(kind="single", cost=l["p"], pnl=bid - fee(bid, False) - l["p"], pnl_r=bid - fee(bid, True) - l["p"] if bid > 0 else -l["p"], leg=l,
                   pnl_before_fee=bid - l["p"])
    strikes.append(out)


X = [l for l in legs if l["tt"] is not None and l["tt"] <= iso_ms(l["ev"]) - 15 * 60000]
print("legs with a tape trade through our price:", len(X), "| book's best bid below our price at the next snapshot 3 s later: %.3f" % (sum(bool(l["nxt"]) for l in X if l["nxt"] is not None) / sum(l["nxt"] is not None for l in X)))
print("legs whose level was emptied per the BOOK alone (best bid fell below our price before T-15): %.3f ; of those, tape also shows a through trade: %.3f" % (sum(l["bt"] is not None for l in legs) / len(legs), sum(l["tt"] is not None for l in legs if l["bt"] is not None) / max(1, sum(l["bt"] is not None for l in legs))))
def score(mode):
    ev = defaultdict(lambda: [0.0, 0.0]); kinds = defaultdict(int); bucket = defaultdict(list); nf = 0
    by = defaultdict(dict)
    for l in legs: by[l["t"]][l["side"]] = l
    for t, L in by.items():
        ss = snaps[t]; T = iso_ms(close_of[t]); fl = [x for x in ss if x[0] <= T - 15 * 60000][-1]
        def filled(l):
            if l is None: return None
            if mode == "queue": return "q" if l["filled"] else None
            if mode == "tape": return "q" if (l["filled"] and (l["tt"] is None or l["ft"] <= l["tt"])) else ("x" if l["tt"] is not None else None)
            if mode == "tape5": 
                tt = l["tt"] if (l["tt"] is not None and l["tt"] > l["tp"] + 5000) else None
                return "q" if l["filled"] else ("x" if tt is not None else None)
            if mode == "book": return "q" if l["filled"] else ("x" if l["bt"] is not None else None)
            if mode == "both": return "q" if l["filled"] else ("x" if (l["bt"] is not None and l["tt"] is not None) else None)
        y, n = L.get("yes"), L.get("no"); fy, fn = filled(y), filled(n)
        nf += bool(fy) + bool(fn)
        if fy and fn: p = pr = 1 - y["p"] - n["p"]; k = "pair"
        elif fy or fn:
            l = y if fy else n; bid = side_bid(fl, l["side"]) or 0.0
            p = bid - fee(bid, False) - l["p"]; pr = (bid - fee(bid, True) - l["p"]) if bid > 0 else -l["p"]; k = "single"
        else: p = pr = 0.0; k = "none"
        kinds[k] += 1; bucket[k].append(pr); e = ev[close_of[t]]; e[0] += p; e[1] += pr
    pp = [v[0] for k, v in sorted(ev.items())]; prr = [v[1] for k, v in sorted(ev.items())]
    def pf(v): g = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return g / b
    days = defaultdict(float)
    for k, v in sorted(ev.items()): days[k[:10]] += v[1]
    print("%-6s leg fill %.3f pairs %d singles %d none %d | PF %.2f (1-lot rounded %.2f) | mean/event %.1fc | total $%.2f | single mean %.1fc | positive days %d of %d" % (mode, nf / len(legs), kinds["pair"], kinds["single"], kinds["none"], pf(pp), pf(prr), 100 * st.mean(prr), sum(prr), 100 * st.mean(bucket["single"]), sum(v > 0 for v in days.values()), len(days)))
for m in ("queue", "tape", "tape5", "book", "both"): score(m)
# how far does the price run on singles under the book rule: flatten bid minus our price
def path(mode):
    ev = defaultdict(float); by = defaultdict(dict); fills = defaultdict(lambda: [0, 0])
    for l in legs: by[l["t"]][l["side"]] = l
    for t, L in by.items():
        ss = snaps[t]; T = iso_ms(close_of[t]); fl = [x for x in ss if x[0] <= T - 15 * 60000][-1]
        fz = lambda l: l is not None and (l["filled"] or (mode == "book" and l["bt"] is not None))
        y, n = L.get("yes"), L.get("no"); fy, fn = fz(y), fz(n)
        for l in (y, n):
            if l is not None: fills[close_of[t]][0] += 1; fills[close_of[t]][1] += fz(l)
        if fy and fn: pr = 1 - y["p"] - n["p"]
        elif fy or fn:
            l = y if fy else n; bid = side_bid(fl, l["side"]) or 0.0; pr = (bid - fee(bid, True) - l["p"]) if bid > 0 else -l["p"]
        else: pr = 0.0
        ev[close_of[t]] += pr
    ks = sorted(ev); return [ev[k] for k in ks], [fills[k] for k in ks]
import random
random.seed(20261112)
(qp, qf), (bp, bf) = path("queue"), path("book")
for name, pr in (("queue model true", qp), ("priority (book) model true", bp)):
    for stop in (3.0, 5.0, 6.0, 8.0):
        hit = []; 
        for _ in range(4000):
            c = pk = 0; h = None
            for i in range(96):
                c += random.choice(pr); pk = max(pk, c)
                if pk - c >= stop: h = i + 1; break
            hit.append(h)
        got = [h for h in hit if h is not None]
        print("%s: drawdown stop $%.0f | tripped within 24 events %.2f, 48 events %.2f, 96 events %.2f | median events to trip %s" % (name, stop, sum(h <= 24 for h in got) / 4000, sum(h <= 48 for h in got) / 4000, len(got) / 4000, sorted(got)[len(got) // 2] if got else None))
# fill-rate tripwire: after K events, is the pooled leg fill rate at or above 60%?
for K in (1, 2, 3):
    for name, ff in (("queue", qf), ("priority", bf)):
        c = 0
        for _ in range(4000):
            s = [random.choice(ff) for _ in range(K)]
            c += sum(x[1] for x in s) / sum(x[0] for x in s) >= 0.60
        print("fill-rate tripwire (>= 60%% of legs filled) after %d events, %s model true: fires %.3f" % (K, name, c / 4000))
print("single-event leg fill rate >= 0.6 share: queue %.3f priority %.3f ; mean fills per event: %.1f vs %.1f of %.1f legs" % (sum(x[1] / x[0] >= .6 for x in qf) / len(qf), sum(x[1] / x[0] >= .6 for x in bf) / len(bf), st.mean(x[1] for x in qf), st.mean(x[1] for x in bf), st.mean(x[0] for x in bf)))
print("priority model per event: mean %.1fc sd %.1fc worst $%.2f best $%.2f share losing %.2f ; per day mean $%.2f" % (100 * st.mean(bp), 100 * st.pstdev(bp), min(bp), max(bp), sum(x < 0 for x in bp) / len(bp), sum(bp) / 10))
