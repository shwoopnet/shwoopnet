import sys, math
sys.path.insert(0, "src")
from scalper import skew1 as s

# implied spot: YES mid 0.8, 0.6, 0.4, 0.2 at strikes 100..130 -> crosses 0.5 at 115
u = {100.0: (0.79, 0.81, 1), 110.0: (0.59, 0.61, 1), 120.0: (0.39, 0.41, 1), 130.0: (0.19, 0.21, 1)}
assert abs(s.implied_spot(u) - 115.0) < 1e-9
assert s.implied_spot({100.0: (0.1, 0.12, 1)}) is None
assert s.two_sided((0.1, 0.15, 0), 0.06) and not s.two_sided((0.1, 0.2, 0), 0.06) and not s.two_sided((0, 0.05, 0), 0.06)
# payoffs
td = {"side": "DN", "res": "no", "paid": 0.1, "close": 0}
tu = {"side": "UP", "res": "no", "paid": 0.1, "close": 0}
assert s.payoff(td) == 1 and s.payoff(tu) == 0
assert abs(s.net(tu) - (-1.0 - s.fee(0.1, 10))) < 1e-9
# build on a synthetic event set: 80 hourly events with a flat spot of 115 at look; DN strike 110 asks NO at 0.4 (too high), 100 at 0.2
ev = {}
base = 1_800_000_000 - (1_800_000_000 % 3600)
for i in range(80):
    c = base + 3600 * i
    q = {100.0: (0.79, 0.81, 1), 110.0: (0.59, 0.61, 1), 120.0: (0.39, 0.41, 1), 130.0: (0.19, 0.21, 1), 140.0: (0.09, 0.11, 1), 90.0: (0.89, 0.91, 1)}
    q2 = dict(q)
    # shift spot slightly so sigma > 0
    if i % 2:
        q = {k: (b + 0.01, a + 0.01, v) for k, (b, a, v) in q.items()}
    ev[c] = {"res": {k: "no" for k in q}, "q": {c - s.LOOK_LEAD: q, c - s.FILL_LEAD: q2}}
tr, fn = s.build(ev)
dn = [t for t in tr if t["side"] == "DN"]
up = [t for t in tr if t["side"] == "UP"]
assert dn and up, fn
# nearest-to-spot candidate with ask in [0.03,0.30]: DN buys NO at 1-bid: K=100 -> 1-0.79=.21 ok (110 has 1-.59=.41 too high); UP YES ask: 130 ->.21 (120 ask .41 too high)
assert all(t["k"] == 100.0 for t in dn) and all(t["k"] == 130.0 for t in up), (dn[0], up[0])
assert all(t["paid"] <= 0.30 for t in tr)
# frozen results are not read when score=False
tr2, _ = s.build(ev, score=False)
assert all(t["res"] is None for t in tr2)
# verdict: too few trades
assert s.verdict(dn[:10], up[:10], 0) == "NOT_ENOUGH_DATA"
print("test_skew1 ok")
