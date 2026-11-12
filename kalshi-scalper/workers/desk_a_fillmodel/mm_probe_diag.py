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
        cum = 0.0; ft = None; ffrac = None; through = 0.0
        for (cm, yp, cnt, sd) in trades.get(t, ()):
            if cm <= tp or cm > w1: continue
            if sd == hit and abs(yp - level) < 1e-6:
                cum += cnt
                if ft is None and cum >= q + 1:
                    ft = cm; ffrac = abs(cnt - round(cnt)) > 0.001
            # trades at a WORSE price for the seller (through our level): our order has price priority over them
            if sd == hit and ((side == "yes" and yp < level - 1e-6) or (side == "no" and yp > level + 1e-6)):
                through += cnt
        # did the best bid of our side leave our price before the fill / the end?
        last_at = max((s[0] for s in inwin if s[0] >= tp and s[ip] is not None and abs(s[ip] - p) < 1e-6), default=tp)
        rec = dict(ev=close_of[t], t=t, side=side, p=p, q=q, tp=tp, lead_min=(T - tp) / 60000, filled=ft is not None, ft=ft, wait=(ft - tp) / 1000 if ft else None,
                   ffrac=ffrac, cum=cum, through=through, at_touch_sec=(last_at - tp) / 1000)
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
F = [l for l in legs if l["filled"]]
print("strikes", len(strikes), "legs", len(legs), "filled legs", len(F), "leg fill rate %.3f" % (len(F) / len(legs)), "| pairs", sum(s["kind"] == "pair" for s in strikes), "singles", sum(s["kind"] == "single" for s in strikes), "total $ %.2f rounded $ %.2f" % (sum(s["pnl"] for s in strikes), sum(s["pnl_r"] for s in strikes)))
def q(v, ps=(10, 25, 50, 75, 90)):
    v = sorted(v); return [round(v[min(len(v) - 1, int(len(v) * p / 100))], 2) for p in ps]
print("queue ahead at post (contracts) p10/25/50/75/90:", q([l["q"] for l in legs]))
print("post price p10/25/50/75/90:", q([l["p"] for l in legs]))
print("wait to fill (s) p10/25/50/75/90:", q([l["wait"] for l in F]), "| share of fills inside 60 s %.2f, inside 5 min %.2f" % (sum(l["wait"] <= 60 for l in F) / len(F), sum(l["wait"] <= 300 for l in F) / len(F)))
qs = sorted(l["q"] for l in legs); t1, t2 = qs[len(qs) // 3], qs[2 * len(qs) // 3]
for name, sel in (("queue low third (<=%d)" % t1, lambda l: l["q"] <= t1), ("mid", lambda l: t1 < l["q"] <= t2), ("high third (>%d)" % t2, lambda l: l["q"] > t2)):
    g = [l for l in legs if sel(l)]; print("  fill rate,", name, "%.3f n %d" % (sum(l["filled"] for l in g) / len(g), len(g)))
for lo, hi in ((0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)):
    g = [l for l in legs if lo <= l["p"] < hi]
    if g: print("  fill rate, post price %.1f-%.1f: %.3f n %d" % (lo, hi, sum(l["filled"] for l in g) / len(g), len(g)))
print("fill-rule sensitivity (leg fill rate if the volume needed at our price is k x the visible queue):")
for k in (0.25, 0.5, 1, 1.5, 2, 3):
    print("  k %.2f: %.3f" % (k, sum(l["cum"] >= k * l["q"] + 1 for l in legs) / len(legs)), end="")
print()
print("  with price priority (also filled if any taker trade printed THROUGH our price): %.3f" % (sum((l["cum"] >= l["q"] + 1) or l["through"] > 0 for l in legs) / len(legs)))
print("  share of unfilled legs where some volume traded at our price: %.2f ; where volume traded through: %.2f" % (sum(l["cum"] > 0 for l in legs if not l["filled"]) / sum(not l["filled"] for l in legs), sum(l["through"] > 0 for l in legs if not l["filled"]) / sum(not l["filled"] for l in legs)))
print("fractional filler share of filled legs: %.3f" % (sum(bool(l["ffrac"]) for l in F) / len(F)))
S1 = [s for s in strikes if s["kind"] == "single"]; P2 = [s for s in strikes if s["kind"] == "pair"]
print("filled strikes %d: one-sided share %.3f" % (len(S1) + len(P2), len(S1) / (len(S1) + len(P2))))
for name, key in (("single unrounded", "pnl"), ("single 1-lot rounded fee", "pnl_r"), ("single before exit fee", "pnl_before_fee")):
    v = [100 * s[key] for s in S1]; print("  %s: mean %.2fc sd %.2fc median %.2f p5 %.1f p95 %.1f min %.1f max %.1f share>0 %.2f" % (name, st.mean(v), st.pstdev(v), st.median(v), q(v, (5,))[0], q(v, (95,))[0], min(v), max(v), sum(x > 0 for x in v) / len(v)))
v = [100 * s["pnl"] for s in P2]; print("  pair: mean %.2fc sd %.2f min %.1f max %.1f" % (st.mean(v), st.pstdev(v), min(v), max(v)))
# adverse selection on filled legs: move of our side's mid after the fill
for h in ("m60", "m300", "mfl"):
    v = [100 * (l[h] - l["m0"]) for l in F if l.get(h) is not None and l.get("m0") is not None]
    v1 = [100 * (l[h] - l["p"]) for l in F if l.get(h) is not None]
    print("  our side's mid, %s minus mid at fill: mean %+.2fc (n %d) sd %.1f ; minus our price: mean %+.2fc" % (h, st.mean(v), len(v), st.pstdev(v), st.mean(v1)))
for name, sel in (("filled by fractional", lambda l: l["ffrac"]), ("filled by whole", lambda l: not l["ffrac"]), ("filled inside 60 s", lambda l: l["wait"] <= 60), ("filled after 5 min", lambda l: l["wait"] > 300)):
    v = [100 * (l["m300"] - l["p"]) for l in F if sel(l) and l.get("m300") is not None]
    print("  mid 5 min after fill minus our price, %s: %+.2fc n %d" % (name, st.mean(v), len(v)))
# per event
ev = defaultdict(lambda: dict(p=0.0, pr=0.0, cost=0.0, fills=0, legs=0, singles=0))
for s in strikes:
    e = ev[s["ev"]]; e["p"] += s["pnl"]; e["pr"] += s["pnl_r"]; e["cost"] += s["cost"]; e["singles"] += s["kind"] == "single"
for l in legs:
    ev[l["ev"]]["legs"] += 1; ev[l["ev"]]["fills"] += l["filled"]
E = [ev[k] for k in sorted(ev)]
pp = [e["p"] for e in E]; pr = [e["pr"] for e in E]
def pf(v): g = sum(x for x in v if x > 0); b = -sum(x for x in v if x < 0); return g / b
print("events %d | PF unrounded %.2f rounded %.2f | mean %.2fc / %.2fc | sd %.1fc / %.1fc | worst event $%.2f / $%.2f | best $%.2f | losing events %.2f" % (len(E), pf(pp), pf(pr), 100 * st.mean(pp), 100 * st.mean(pr), 100 * st.pstdev(pp), 100 * st.pstdev(pr), min(pp), min(pr), max(pp), sum(x < 0 for x in pr) / len(pr)))
print("  per event: legs %.1f fills %.2f (sd %.2f) singles %.2f | fill-cost outlay mean $%.2f max $%.2f | resting collateral if all legs rest: mean $%.2f" % (st.mean(e["legs"] for e in E), st.mean(e["fills"] for e in E), st.pstdev([e["fills"] for e in E]), st.mean(e["singles"] for e in E), st.mean(e["cost"] for e in E), max(e["cost"] for e in E), sum(l["p"] for l in legs) / len(E)))
fr = [e["fills"] / e["legs"] for e in E]; print("  event-level fill rate: mean %.3f sd %.3f ; design effect vs independent legs %.2f" % (st.mean(fr), st.pstdev(fr), st.pvariance(fr) / (st.mean(fr) * (1 - st.mean(fr)) / st.mean(e["legs"] for e in E))))
cum = 0; peak = 0; dd = 0; run = 0; worst_run = 0
for x in pr:
    cum += x; peak = max(peak, cum); dd = max(dd, peak - cum); run = run + 1 if x < 0 else 0; worst_run = max(worst_run, run)
print("  1-lot rounded path: total $%.2f, max drawdown $%.2f, longest run of losing events %d" % (cum, dd, worst_run))
days = defaultdict(float)
for k in sorted(ev): days[k[:10]] += ev[k]["pr"]
print("  by day (rounded):", {d: round(v, 2) for d, v in days.items()})
# bootstrap: chance that N events of the 1-lot rounded path show a drawdown beyond X, and a net below Y
for N in (24, 48, 96, 168):
    dds = []; nets = []
    for _ in range(4000):
        c = pk = d = 0
        for _ in range(N):
            c += random.choice(pr); pk = max(pk, c); d = max(d, pk - c)
        dds.append(d); nets.append(c)
    dds.sort(); nets.sort()
    print("  resampled %d events: net p5 $%.2f median $%.2f p95 $%.2f | drawdown median $%.2f p95 $%.2f p99 $%.2f | P(net<0) %.2f" % (N, nets[200], nets[2000], nets[3800], dds[2000], dds[3800], dds[3960], sum(x < 0 for x in nets) / 4000))
# same with the mean shifted to zero (no edge) and to minus 3c per event
for shift, name in ((-st.mean(pr), "zero-edge"), (-st.mean(pr) - 0.03, "minus 3c an event")):
    for N in (48, 96, 168):
        dds = []; nets = []
        for _ in range(4000):
            c = pk = d = 0
            for _ in range(N):
                c += random.choice(pr) + shift; pk = max(pk, c); d = max(d, pk - c)
            dds.append(d); nets.append(c)
        dds.sort(); nets.sort()
        print("  %s, %d events: net p5 $%.2f median $%.2f | drawdown p50 $%.2f p95 $%.2f" % (name, N, nets[200], nets[2000], dds[2000], dds[3800]))
