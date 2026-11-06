#!/usr/bin/env python3
"""LL1, XS1, RO1 scorer (registered in workers/LEAD_COMMON.md etc. before it was run). Held-out dates are never loaded.
Usage: python3 -I lead.py REPO_DIR"""
import sys, math, statistics as st
sys.path.insert(0, sys.argv[1] + "/workers/fundcarry")
import fundcarry as f
f.AMEND1 = True
seen = f.load(sys.argv[1])
times = sorted(set(k[0] for k in seen)); T = {t: f.ts(t) for t in times}
Q = {t: {} for t in times}
for (t, k), r in seen.items():
    q = f.quote(r)
    if q: Q[t][k] = q
sp = {}
for t in times:
    for k, q in Q[t].items(): sp.setdefault(k, []).append((q["a"] - q["b"]) / q["m"] * 1e4)
U = sorted(k for k, v in sp.items() if len(v) >= 10 and st.median(v) <= 5.0)
print("universe", U); print("median spread bp", {k: round(st.median(sp[k]), 2) for k in U})
FEE, FUND = 0.0012, 0.0002
D1_END = "2026-10-26"
def lr(t0, t1, k): return math.log(Q[t1][k]["m"] / Q[t0][k]["m"])
def ok(a, b): return 2 * 3600 <= T[b] - T[a] <= 8 * 3600
def leg(t1, t2, k, s, fee):   # s=+1 long
    e, x = Q[t1][k], Q[t2][k]
    g = (x["b"] / e["a"] - 1) if s > 0 else (1 - x["a"] / e["b"])
    return g - 2 * fee - FUND * (T[t2] - T[t1]) / 86400
def mid_gross(t1, t2, k, s): return s * (Q[t2][k]["m"] / Q[t1][k]["m"] - 1)
def report(name, trades):
    # trades: (date, net, net_stress, net_ctrl, gross)
    n = len(trades); days = {}
    for d, a, b, c, g in trades: days.setdefault(d, []).append(a)
    print("==", name, "trades", n, "day clusters", len(days))
    if n == 0: return
    def pf(v):
        w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0); return w / l if l > 0 else float("inf")
    for lab, sel in (("all", lambda d: True), ("D1", lambda d: d <= D1_END), ("D2", lambda d: d > D1_END)):
        v = [a for d, a, b, c, g in trades if sel(d)]
        if v: print(" ", lab, "n", len(v), "net bp %.1f" % (st.mean(v) * 1e4), "PF %.2f" % pf(v))
    print("  gross(mid) bp %.1f" % (st.mean(g for *_, g in trades) * 1e4), "stress net bp %.1f" % (st.mean(b for _, _, b, _, _ in trades) * 1e4),
          "control net bp %.1f" % (st.mean(c for _, _, _, c, _ in trades) * 1e4), "hit %.2f" % (sum(1 for t in trades if t[1] > 0) / n))
    ds = [sum(v) / len(v) for v in days.values()]
    if len(ds) >= 3 and st.stdev(ds) > 0: print("  day z %.2f" % (st.mean(ds) / (st.stdev(ds) / math.sqrt(len(ds)))))
    print("  breakeven fee/side bp %.1f" % (((st.mean(g for *_, g in trades) - st.mean([FUND * 0] )) ) / 2 * 1e4))
def mk(t1, t2, k, s):
    return (t1[:10], leg(t1, t2, k, s, FEE), leg(t1, t2, k, s, FEE * 1.2), leg(t1, t2, k, -s, FEE), mid_gross(t1, t2, k, s))
# LL1
tr, skip = [], 0
for i in range(len(times) - 2):
    t0, t1, t2 = times[i:i + 3]
    if not (ok(t0, t1) and ok(t1, t2)): skip += 1; continue
    try: s = (lr(t0, t1, "KXBTCPERP") + lr(t0, t1, "KXETHPERP")) / 2
    except KeyError: skip += 1; continue
    if abs(s) < 0.005: continue
    for k in ("KXUSTECH100PERP", "KXUS500PERP"):
        if k in U and k in Q[t1] and k in Q[t2]: tr.append(mk(t1, t2, k, 1 if s > 0 else -1))
print("LL1 skipped", skip); report("LL1", tr)
# info corr
xs, ys = [], []
for i in range(len(times) - 2):
    t0, t1, t2 = times[i:i + 3]
    if ok(t0, t1) and ok(t1, t2):
        try: xs.append((lr(t0, t1, "KXBTCPERP") + lr(t0, t1, "KXETHPERP")) / 2); ys.append(lr(t1, t2, "KXUSTECH100PERP"))
        except KeyError: pass
if len(xs) > 3: print("  info corr(BTC/ETH prev, Tech100 next) %.2f over %d" % (st.correlation(xs, ys), len(xs)))
# RO1
tr, skip = [], 0
for i in range(len(times) - 2):
    t0, t1, t2 = times[i:i + 3]
    if not (ok(t0, t1) and ok(t1, t2)): skip += 1; continue
    try: s = lr(t0, t1, "KXUSTECH100PERP")
    except KeyError: skip += 1; continue
    if s <= -0.005 and "KXGOLDPERP" in U and "KXGOLDPERP" in Q[t1] and "KXGOLDPERP" in Q[t2]: tr.append(mk(t1, t2, "KXGOLDPERP", 1))
print("RO1 skipped", skip); report("RO1", tr)
# XS1
tr, skipd = [], 0
for d in sorted(set(t[:10] for t in times)):
    c = [t for t in times if t[:10] == d and t[11:13] >= "14"]
    if not c: skipd += 1; continue
    t = c[0]
    def near(target):
        b = min(times, key=lambda u: abs(T[u] - target)); return b if abs(T[b] - target) <= 3 * 3600 else None
    a, x = near(T[t] - 86400), near(T[t] + 86400)
    if not a or not x or x == t or a == t: skipd += 1; continue
    names = [k for k in U if k in Q[a] and k in Q[t] and k in Q[x]]
    if len(names) < 6: skipd += 1; continue
    names.sort(key=lambda k: lr(a, t, k))
    lo, hi = names[:2], names[-2:]
    def book(fee, sgn):
        return sum(0.5 * leg(t, x, k, sgn, fee) for k in hi) + sum(0.5 * leg(t, x, k, -sgn, fee) for k in lo)
    g = sum(0.5 * mid_gross(t, x, k, 1) for k in hi) + sum(0.5 * mid_gross(t, x, k, -1) for k in lo)
    tr.append((d, book(FEE, 1), book(FEE * 1.2, 1), book(FEE, -1), g))
print("XS1 skipped dates", skipd); report("XS1", tr)
