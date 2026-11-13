import json, sys, random
START = "2026-11-05T16:18"
def rows(path):
    d = json.load(open(path))
    out = []
    for o in d["slotOrders"]:
        if o.get("strategy") != "OICORE" or o.get("status") != "filled": continue
        if not (o.get("count") or 0) > 0 or o.get("result") not in ("yes", "no"): continue
        if o["ts"][:16] <= START: continue
        paid = o["avgFill"] if o["side"] == "yes" else 1 - o["avgFill"]
        fee = o.get("avgFee") or 0
        pc = (1 - paid - fee) if o["result"] == o["side"] else -(paid + fee)
        out.append((o["price"], o["count"], pc, o["result"] == o["side"]))
    return out
def boot(g, n=10000):
    if not g: return None
    rng = random.Random(1); k = len(g); r = []
    for _ in range(n):
        s = [g[rng.randrange(k)] for _ in range(k)]
        r.append(100 * sum(c * p for _, c, p, _ in s) / sum(c for _, c, _, _ in s))
    r.sort(); return r[int(.05 * n)], r[int(.95 * n) - 1]
def rep(name, g):
    if not g: print(name, "fills 0"); return None
    con = sum(c for _, c, _, _ in g); net = sum(c * p for _, c, p, _ in g)
    ci = boot(g)
    print(f"{name}: fills {len(g)}, wins {sum(w for *_, w in g)}, net ${net:.2f}, "
          f"{100*net/con:+.2f}c/contract, 90% [{ci[0]:+.2f}, {ci[1]:+.2f}]")
    return net, 100 * net / con, ci
r = rows(sys.argv[1])
lo = [x for x in r if x[0] < 0.10]; hi = [x for x in r if x[0] >= 0.10]
a = rep("under 0.10", lo); rep("0.10+     ", hi)
if a: print(f"halving under-0.10 changes net by ${-a[0]/2:+.2f}")
n = len(lo); print(f"read point 40 fills: {n}/40")
if a and n >= 40:
    print("VERDICT:", "DROP idea" if a[1] > 3 else "SUPPORTS sending to owner" if a[1] < 0 and a[2][1] < 3 else "WAIT")
else: print("VERDICT: not at read point")
