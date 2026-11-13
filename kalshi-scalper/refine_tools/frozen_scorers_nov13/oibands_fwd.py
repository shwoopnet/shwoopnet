import json, sys, random
from math import comb
if len(sys.argv) < 3:
    sys.exit("usage: oibands_fwd.py report.json start_ts")
START = sys.argv[2].rstrip("Z")[:16]
A_READ, B_READ = 40, 20

def rows(path):
    d = json.load(open(path)); out = []
    for o in d["slotOrders"]:
        if o.get("strategy") != "OICORE" or o.get("status") != "filled": continue
        if not (o.get("count") or 0) > 0 or o.get("result") not in ("yes", "no"): continue
        if o["ts"][:16] <= START: continue
        paid = o["avgFill"] if o["side"] == "yes" else 1 - o["avgFill"]
        fee = o.get("avgFee") or 0
        win = o["result"] == o["side"]
        pc = (1 - paid) - fee if win else -paid - fee
        out.append((paid, o["count"], pc, win))
    return out

def cdf(k, n, p):
    return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(k+1))

def cp(k, n, a=0.10):
    # exact Clopper-Pearson, two-sided 90 percent, by bisection
    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            m = (lo+hi)/2
            if f(m): lo = m
            else: hi = m
        return lo
    lower = 0.0 if k == 0 else solve(lambda p: 1 - cdf(k-1, n, p) < a/2)
    upper = 1.0 if k == n else solve(lambda p: cdf(k, n, p) > a/2)
    return lower, upper

def boot(g, n=10000):
    rng = random.Random(1); k = len(g); r = []
    for _ in range(n):
        s = [g[rng.randrange(k)] for _ in range(k)]
        r.append(100*sum(c*p for _, c, p, _ in s)/sum(c for _, c, _, _ in s))
    r.sort(); return r[int(.05*n)], r[int(.95*n)-1]

def rep(name, g):
    if not g:
        print(f"{name}: fills 0"); return None
    con = sum(c for _, c, _, _ in g); net = sum(c*p for _, c, p, _ in g)
    w = sum(x[3] for x in g); n = len(g)
    wl, wu = cp(w, n); bl, bu = boot(g)
    npc = 100*net/con
    print(f"{name}: fills {n}, wins {w}, win rate {100*w/n:.1f}% 90% [{100*wl:.1f}, {100*wu:.1f}], "
          f"net ${net:.2f}, {npc:+.2f}c/contract 90% [{bl:+.2f}, {bu:+.2f}]")
    return dict(n=n, npc=npc, bu=bu, wu=wu)

r = rows(sys.argv[1])
print(f"S-OIBANDS1 forward window: OICORE filled+settled, ts after {START}Z; paid price basis")
A = [x for x in r if x[0] <= 0.07]
B = [x for x in r if x[0] > 0.20]
M = [x for x in r if 0.07 < x[0] <= 0.20]
a = rep("A paid<=0.07   ", A); rep("M 0.07-0.20 (ref)", M); b = rep("B paid>0.20    ", B)
print(f"read points: A {len(A)}/{A_READ}, B {len(B)}/{B_READ}")
if a and a["n"] >= A_READ:
    print("A VERDICT:", "does not earn its risk (flag, information only)" if a["npc"] <= 0 and a["bu"] < 1 else "no read, extend")
else: print("A VERDICT: not at read point")
if b and b["n"] >= B_READ:
    print("B VERDICT:", "does not earn its risk (flag, information only)" if b["npc"] < 0 and 100*b["wu"] < 45 else "no read, extend")
else: print("B VERDICT: not at read point")
