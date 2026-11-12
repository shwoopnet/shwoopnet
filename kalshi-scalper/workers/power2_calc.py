"""POWER2: arithmetic only (numpy + math). No data files, no network. Inputs are published summary numbers.
Run: python3 -I workers/power2_calc.py"""
import math
import numpy as np
from math import erf, sqrt

def Phi(x): return 0.5 * (1 + erf(x / sqrt(2)))
def upper(x): return 1 - Phi(x)

print("== generic: n needed for z bar = sd*zbar/effect squared")
for sd in (0.40, 0.46, 0.50):
    for eff in (0.01, 0.015, 0.02, 0.03, 0.05):
        print(f"sd {sd:.2f} effect {eff*100:.1f}c: n for z4.39 = {(4.39*sd/eff)**2:,.0f}; z5.34 = {(5.34*sd/eff)**2:,.0f}")

print("\n== MMSIM1 (published: PF 1.28 at bound, mean 3.71c/event, sd 41.7c; L = gross loss/event)")
G_minus_L, pf = 3.71, 1.28
L = G_minus_L / (pf - 1); print("gross loss per event c", round(L, 2))
se300 = 2.41 / L   # 41.7/sqrt(300)/L
print("se(PF) n=300", round(se300, 3), "check P(PF>=1.5 | true 1.28) =", round(upper((1.5-1.28)/se300), 3), "(MMPOWER1: 0.11 D / 0.17 I)")
for label, mean in (("unshrunk", 3.71), ("shrunk 50%", 1.855)):
    tpf = 1 + mean / L
    for n in (172, 300, 428, 1600):
        se = 41.7 / sqrt(n) / L
        print(f"{label} truePF {tpf:.2f} n {n}: P(PF>=1.3) = {upper((1.3-tpf)/se):.2f}   P(PF<1.0) = {Phi((1.0-tpf)/se):.2f}")

print("\n== CFRTI1-BTC (n=50 held-out edge rows; dev w .33, mean +15.6c, PF 2.54)")
rng = np.random.default_rng(20261112)
fee = 0.01
p = 0.33 - 0.156 - fee
def sim(w, n, draws=100000):
    wins = rng.binomial(n, w, draws)
    gw = wins * (1 - p - fee); gl = (n - wins) * (p + fee)
    pfv = np.where(gl > 0, gw / np.maximum(gl, 1e-9), 9)
    mean = (gw - gl) / n
    return float(np.mean((pfv >= 1.3) & (mean > 0)))
for label, w in (("unshrunk w .33", .33), ("shrunk 50% of mean", p + fee + 0.078), ("pooled-5 PF 1.14", 0.1935), ("null mean 0", p + fee)):
    print(label, "w", round(w, 3), "P(pass) n50", round(sim(w, 50), 3), "n80", round(sim(w, 80), 3))

print("\n== NC15DEPTH1 (no dev estimate; assumed gross effect 3c, shrunk 50% = 1.5c; sd .40 cheap, .50 mid)")
perday = 816 * 0.7
for eff in (0.015, 0.03):
    for sd in (0.40, 0.50):
        need = (4.39 * sd / eff) ** 2
        print(f"effect {eff*100:.1f}c sd {sd}: cell windows for z4.39 {need:,.0f}; as one pooled cell of 1/4 of windows at {perday:.0f}/day = {need*4/perday:,.0f} days")
for days in (7, 30, 90):
    ncell = perday * days / 4
    for eff in (0.015, 0.03):
        z = eff / 0.45 * sqrt(ncell)
        print(f"days {days} pooled cell n {ncell:,.0f} effect {eff*100:.1f}c: power at z4.39 = {upper(4.39 - z):.2f}")
for days in (7,):
    ncell = 0.7*80*days/4
    print("single series cell (80 windows/day, 2x2) n", ncell, "z for 1.5c", round(0.015/0.45*sqrt(ncell), 2))

print("\n== MENTPERSIST1 (assumed: rule claims >=10c under b; true gross edge 5c after 50% shrink; ask .30)")
pr, f = 0.30, 0.02
w = pr + 0.05
mean = w * (1 - pr - f) - (1 - w) * (pr + f)
pf_true = w * (1 - pr - f) / ((1 - w) * (pr + f))
sd = sqrt(w * (1 - pr - f) ** 2 + (1 - w) * (pr + f) ** 2 - mean ** 2)
print("mean", round(mean, 4), "PF", round(pf_true, 2), "sd", round(sd, 3))
print("trades for z5.34", round((5.34 * sd / mean) ** 2), "z4.39", round((4.39 * sd / mean) ** 2))
tpr = 0.31 * 0.30
for reads in (1000, 1300, 1600, 2160):
    n = reads * tpr
    print(f"reads {reads} hours {reads/25:.0f} trades {n:.0f} z {mean/sd*sqrt(n):.2f} power z5.34 {upper(5.34-mean/sd*sqrt(n)):.3f}")
print("reads for 4,900 trades", round(4900 / tpr), "hours", round(4900 / tpr / 25))
print("reads to 60 trades (kill)", round(60 / tpr), "hours", round(60 / tpr / 25, 1))

print("\n== STALE1 (published: best cell n 74 PF 1.27 z 1.19; standardized effect z/sqrt(n))")
d = 1.19 / sqrt(74); print("standardized", round(d, 3), "shrunk", round(d / 2, 3))
print("events for z4.39 (shrunk)", round((4.39 / (d / 2)) ** 2), "unshrunk", round((4.39 / d) ** 2))
print("gap events per day: 265 over ~31 days =", round(265 / 31, 1), "-> days", round((4.39 / (d / 2)) ** 2 / (265 / 31)))

print("\n== EARLYCLOSE1 (published ECS H6 CHEAP n 458 PF .77 z -1.45; MID n 461 PF .86 z -1.02; best bin 0.20-0.25 n 63 win 33% vs 22.5%)")
for lab, win, price, n in (("bin .20-.25", .33, .225, 63),):
    es = (win - price) / sqrt(price * (1 - price))
    print(lab, "std effect", round(es, 3), "shrunk", round(es / 2, 3), "n for z4.39 shrunk", round((4.39 / (es / 2)) ** 2))

print("\n== TIECOND1 arm B (tie rate Wilson lower >= 6%, n>=300)")
def wl(k, n, z=1.96):
    ph = k / n; den = 1 + z*z/n
    return (ph + z*z/(2*n) - z*sqrt(ph*(1-ph)/n + z*z/(4*n*n))) / den
for rate in (0.026, 0.05, 0.08, 0.10):
    for n in (300, 420, 600):
        draws = rng.binomial(n, rate, 20000)
        pw = float(np.mean([wl(k, n) >= 0.06 for k in draws[:4000]]))
        print(f"true tie rate {rate} n {n}: P(lower>=6%) {pw:.2f}")

print("\n== AVG1: no calculation; pinned cut freezes the best development cell at n 28 (see POWER2_QUEUE.md)")
