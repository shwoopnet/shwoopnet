import math, random
random.seed(20261112)
def q_for_pf(p, pf):
    f = 0.07*p*(1-p); c = p+f; r = pf*c/(1-c); return r/(1+r), c
def pf(ws, c):
    g = sum(ws)*(1-c); l = (len(ws)-sum(ws))*c
    return g/l if l > 0 else 99
def sim(p, true_pf, n, rule, reps=40000):
    q, c = q_for_pf(p, true_pf); hit = 0
    for _ in range(reps):
        w = [1 if random.random() < q else 0 for _ in range(n)]
        if rule(w, c): hit += 1
    return hit/reps
print("D. CFRTI1-BTC held-out read at n 50, price about 0.50: P(held-out PF >= 1.5)")
for t in (0.9, 1.0, 1.2, 1.5, 2.0, 2.5):
    print("  true PF %.1f: %.3f" % (t, sim(0.50, t, 50, lambda w, c: pf(w, c) >= 1.5)))
print("   and at n 130:", [round(sim(0.50, t, 130, lambda w, c: pf(w, c) >= 1.5), 3) for t in (1.0, 1.5, 2.0, 2.5)])
print("E. A cheap cell (price 0.10) showing PF >= 1.45 in BOTH thirds at n 56 each (the sports SPREAD lead)")
for t in (0.9, 1.0, 1.5):
    print("  true PF %.1f: %.3f" % (t, sim(0.10, t, 112, lambda w, c: pf(w[:56], c) >= 1.45 and pf(w[56:], c) >= 1.45)))
print("F. Wrong-fail chance for card 84 (train n 36 PF 0.58, validate n 44 PF 0.36): P(both at or below those) if the truth were PF 1.5")
for p in (0.20, 0.35, 0.50):
    print("  price %.2f: %.5f" % (p, sim(p, 1.5, 80, lambda w, c: pf(w[:36], c) <= 0.58 and pf(w[36:], c) <= 0.36, reps=200000)))
print("G. Wrong-fail chance for a held-out third reading PF <= 0.87 if the truth were PF 1.5, by n")
for n in (40, 80, 150):
    print("  n %d: price .20 %.4f  price .50 %.4f" % (n, sim(0.20, 1.5, n, lambda w, c: pf(w, c) <= 0.87), sim(0.50, 1.5, n, lambda w, c: pf(w, c) <= 0.87)))
print("H. A count bar: at least 3 of 40 city-days, 0 seen in the first 20. P(>=3 in the other 20) by true rate")
from math import comb
for r in (0.02, 0.05, 0.10, 0.15):
    print("  rate %.2f: %.4f ; and P(0 of 20 | rate) %.4f" % (r, 1-sum(comb(20, k)*r**k*(1-r)**(20-k) for k in range(3)), (1-r)**20))
print("I. Per-event maker test (MMSIM1 shape): mean +5.07c per event; n for z 5.34 and for a plain z 2, by sd per event")
for sd in (20, 30, 45, 60):
    print("  sd %dc: z5.34 needs %d events, z2 needs %d" % (sd, (5.34*sd/5.07)**2, (2*sd/5.07)**2))
