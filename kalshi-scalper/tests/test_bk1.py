"""Plain assert tests for BK1 (src/scalper/bk1.py); run with: python tests/test_bk1.py. Each states a consequence, not a mechanism."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import bk1 as B
from scalper import scalps

CLOSE = 1_800_000_000


def candle(left, bid, ask):
    return (CLOSE - left, bid, ask, bid, ask)


def market(series, res, **lefts):
    """lefts: s=(bid, ask) at the signal candle, e=(bid, ask) at the entry candle, x=(bid, ask) at the BK7 signal, y=(bid, ask) at the BK7 entry."""
    cs = {}
    for key, left in (("s", B.SIGNAL_LEFT), ("e", B.ENTRY_LEFT), ("x", B.BK7_SIGNAL_LEFT), ("y", B.BK7_ENTRY_LEFT)):
        if key in lefts:
            c = candle(left, *lefts[key])
            cs[c[0]] = c
    return ("T-" + series, series, list(cs.values()), CLOSE, res)


# 1. The entry is on a bar strictly later than the signal: changing the signal candle's ask must not change the price paid, changing the entry candle's must.
a = B.build([market(B.BTC, "yes", s=(0.55, 0.57), e=(0.60, 0.62))])
b = B.build([market(B.BTC, "yes", s=(0.55, 0.60), e=(0.60, 0.62))])
c = B.build([market(B.BTC, "yes", s=(0.55, 0.57), e=(0.70, 0.72))])
fav = lambda m: "yes" if m > 0.5 else "no"
ra, rb, rc = (B.single_rows(x, fav)[0] for x in (a, b, c))
assert abs(ra["net"] - (1 - 0.62 - scalps.fee(0.62))) < 1e-9, "paid the entry candle's ask, not the signal candle's"
assert abs(rb["net"] - ra["net"]) < 1e-9, "a different signal candle quote does not change the price paid"
assert abs(rc["net"] - (1 - 0.72 - scalps.fee(0.72))) < 1e-9, "a different entry candle changes the price paid"

# 2. The favorite and the underdog are opposite sides of the same market, and a coin-flip mid is skipped rather than guessed.
x = B.build([market(B.BTC, "no", s=(0.30, 0.32), e=(0.30, 0.32))])
f = B.single_rows(x, lambda m: None if abs(m - 0.5) < 1e-9 else ("yes" if m > 0.5 else "no"))[0]
u = B.single_rows(x, lambda m: None if abs(m - 0.5) < 1e-9 else ("no" if m > 0.5 else "yes"))[0]
assert f["net"] > 0 > u["net"], "a NO result pays the NO favorite and costs the YES underdog"
flat = B.build([market(B.BTC, "yes", s=(0.50, 0.50), e=(0.50, 0.51))])
assert B.single_rows(flat, lambda m: None if abs(m - 0.5) < 1e-9 else "yes") == []

# 3. The matched baseline: the YES pick and the NO pick in one market have exactly opposite contrasts (net minus the average of both sides), so a rule cannot look good by cost alone.
y = B.build([market(B.BTC, "yes", s=(0.55, 0.57), e=(0.50, 0.52))])
ry, rn = B.single_rows(y, lambda m: "yes")[0], B.single_rows(y, lambda m: "no")[0]
assert abs((ry["net"] - ry["base"]) + (rn["net"] - rn["base"])) < 1e-9 and ry["base"] == rn["base"]

# 4. A pair is two contracts: the net is the sum of both legs and a pair in which both legs lose by the cost shows about twice a single contract's cost.
p = B.build([market(B.BTC, "yes", s=(0.49, 0.51), e=(0.49, 0.51)), market(B.ETH, "no", s=(0.49, 0.51), e=(0.49, 0.51))])
pr = B.pair_rows(p, B.BTC, B.ETH)[0]
assert abs(pr["net"] - (1 - 0.51 - scalps.fee(0.51) + 1 - 0.51 - scalps.fee(0.51))) < 1e-9, "BTC YES wins and ETH NO wins: both legs paid"
assert B.pair_rows(B.build([market(B.BTC, "yes", s=(0.49, 0.51), e=(0.49, 0.51))]), B.BTC, B.ETH) == [], "no pair without both markets"

# 5. The divergence pair only trades when the two mids differ by 0.10 or more, with YES on the lower mid.
close = B.build([market(B.BTC, "yes", s=(0.49, 0.51), e=(0.49, 0.51)), market(B.ETH, "yes", s=(0.52, 0.54), e=(0.52, 0.54))])
assert B.pair_rows(close, B.BTC, B.ETH, diverge=B.DIVERGE) == [], "a 3c gap is not a divergence"
wide = B.build([market(B.BTC, "yes", s=(0.29, 0.31), e=(0.29, 0.31)), market(B.ETH, "no", s=(0.69, 0.71), e=(0.69, 0.71))])
assert B.pair_rows(wide, B.BTC, B.ETH, diverge=B.DIVERGE)[0]["net"] > 1.0, "YES on the cheaper (wins) and NO on the dearer (wins) pays both"

# 6. BK6 takes only entries with a spread of 1c or less.
n6 = B.build([market(B.BTC, "yes", e=(0.50, 0.51)), market(B.ETH, "yes", e=(0.48, 0.52))])
assert len(B.narrow_rows(n6)) == 1, "the 4c spread market is left out"

# 7. BK7 needs Bitcoin at an extreme and Ethereum's side still at 90c or less.
t7 = B.build([market(B.BTC, "yes", x=(0.96, 0.97)), market(B.ETH, "yes", y=(0.80, 0.82))])
assert len(B.lag_rows(t7)) == 1
dear = B.build([market(B.BTC, "yes", x=(0.96, 0.97)), market(B.ETH, "yes", y=(0.94, 0.95))])
assert B.lag_rows(dear) == [], "Ethereum already priced in: no entry"
mid_btc = B.build([market(B.BTC, "yes", x=(0.60, 0.62)), market(B.ETH, "yes", y=(0.80, 0.82))])
assert B.lag_rows(mid_btc) == [], "Bitcoin not at an extreme: no entry"
low = B.build([market(B.BTC, "no", x=(0.03, 0.04)), market(B.ETH, "no", y=(0.18, 0.20))])
assert B.lag_rows(low)[0]["net"] > 0, "Bitcoin at 4c means buy Ethereum NO, which wins here"

# 8. The verdict is only one of the three registered words, a small sample is NOT_ENOUGH_DATA, and passing needs every registered condition.
assert B.verdict(None) == "NOT_ENOUGH_DATA" and B.verdict({"n": 10, "days": 3}) == "NOT_ENOUGH_DATA"
good = {"n": 400, "days": 20, "mean": 0.01, "z": 2.5, "cmean": 0.01, "zc": 2.5, "h1": 0.01, "h2": 0.01, "stress": 0.005}
assert B.verdict(good) == "NOT_YET_FALSIFIED"
for key, bad in (("mean", -0.01), ("z", 1.0), ("cmean", -0.01), ("zc", 1.0), ("h1", -0.01), ("h2", -0.01), ("stress", -0.01)):
    assert B.verdict(dict(good, **{key: bad})) == "FALSIFIED", f"failing {key} alone must falsify"

# 8b. The registered BK1 is the favorite and BK2 the underdog, through the real grid (a NO favorite that wins pays BK1 and costs BK2).
g = B.all_rows(x)
assert g["BK1"][0]["net"] > 0 > g["BK2"][0]["net"], "BK1 buys the favorite and BK2 the underdog"

# 9. There is no promote verb in the code (comments stripped), and the grid is exactly the seven registered ideas.
code = "\n".join(l.split("#")[0] for l in Path(B.__file__).read_text().splitlines())
assert "promote" not in code.lower()
assert B.IDEAS == ("BK1", "BK2", "BK3", "BK4", "BK5", "BK6", "BK7") and set(B.all_rows({})) == set(B.IDEAS)
print("BK1 passed")
