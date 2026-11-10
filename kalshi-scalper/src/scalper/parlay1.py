"""PARLAY1 census (workers/PARLAY1_PROTOCOL.md): open Kalshi multi-leg combos, price vs product of leg mids. Read-only, no outcome."""
import sys, json, math, collections
sys.path.insert(0, "src/scalper")
import hist15 as h
SERIES = ["KXMVECROSSCATEGORY", "KXMVESPORTSMULTIGAMEEXTENDED", "KXMVENFLMULTIGAME", "KXMVENBAMULTIGAMEEXTENDED", "KXMVENFLSINGLEGAME"]
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
combos = []
for s in SERIES:
    cur = None; got = 0
    while got < 300:
        p = {"status": "open", "limit": 100, "series_ticker": s}
        if cur: p["cursor"] = cur
        d = h.get("/markets", p)
        if not d: break
        for m in d.get("markets", []):
            cs = m.get("custom_strike") or {}
            ml = [x for x in (cs.get("Associated Markets") or "").split(",") if x]
            sd = [x for x in (cs.get("Associated Market Sides") or "").split(",") if x]
            if len(ml) >= 5 and len(ml) == len(sd):
                combos.append(dict(t=m["ticker"], s=s, legs=ml, sides=sd, bid=float(m.get("yes_bid_dollars") or 0), ask=float(m.get("yes_ask_dollars") or 0)))
        got += len(d.get("markets", [])); cur = d.get("cursor")
        if not cur or not d.get("markets"): break
print("combos with 5+ legs:", len(combos), collections.Counter(c["s"] for c in combos))
need = sorted({l for c in combos for l in c["legs"]})
print("distinct legs", len(need))
q = {}
for i in range(0, len(need), 100):
    d = h.get("/markets", {"tickers": ",".join(need[i:i + 100]), "limit": 100})
    for m in (d or {}).get("markets", []):
        b, a = float(m.get("yes_bid_dollars") or 0), float(m.get("yes_ask_dollars") or 0)
        if a > 0 and b > 0: q[m["ticker"]] = (b + a) / 2
print("legs with a two-sided quote", len(q))
rows = []
for c in combos:
    if not all(l in q for l in c["legs"]): continue
    fair = 1.0
    for l, sd in zip(c["legs"], c["sides"]): fair *= q[l] if sd == "yes" else 1 - q[l]
    if c["ask"] <= 0: continue
    rows.append((fair - c["ask"] - fee(c["ask"]), c, fair))
print("combos with all legs quoted and a combo ask:", len(rows))
rows.sort(key=lambda r: -r[0])
for e, c, fair in rows[:8]:
    teams = {l.split("-")[1] for l in c["legs"]}
    print("%s legs %d ask %.3f bid %.3f fair(indep) %.4f edge %+.3f dates/games %d" % (c["t"][-14:], len(c["legs"]), c["ask"], c["bid"], fair, e, len(teams)))
cheap = [r for r in rows if 0.03 <= r[1]["ask"] <= 0.30]
print("combos with ask 3c to 30c:", len(cheap), "of which edge > 0 by the independence fair value:", sum(1 for r in cheap if r[0] > 0))
if rows:
    ratios = [r[1]["ask"] / r[2] for r in rows if r[2] > 0]; ratios.sort()
    print("combo ask / independent fair, median %.2f (n %d)" % (ratios[len(ratios)//2], len(ratios)))
