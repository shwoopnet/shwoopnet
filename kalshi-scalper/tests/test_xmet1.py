"""Plain assert tests for src/scalper/xmet1.py, synthetic data only. Run: cd kalshi-scalper && PYTHONPATH=src python tests/test_xmet1.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import xmet1 as X

T = 100000
def cs(end_off_mid, vol=5):  # candle ending at T-off, bid/ask around mid with 0.02 spread
    return [(T - off, m - 0.01, m + 0.01, vol) for off, m in end_off_mid]

# mid and chg: only candles at or before the time, stale quote ignored
g = cs([(360, 0.50), (180, 0.56)])
assert abs(X.chg(g, T) - 0.06) < 1e-9
assert X.chg(cs([(180, 0.56)]), T) is None
assert X.chg(cs([(600, 0.50), (180, 0.56)]), T) is None                      # 600 is older than 120 s before T-360
assert X.mid_at(cs([(100, 0.9)]), T - 180) is None                            # a candle after the look is never used

# trailing SD needs 48 earlier windows, uses only earlier ones, floor 0.005
closes = [i * 900 for i in range(200)]
gc = {c: (0.02 if i % 2 else -0.02) for i, c in enumerate(closes)}
assert X.trailing_sd(gc, closes, 10) is None
sd = X.trailing_sd(gc, closes, 150)
assert abs(sd - 0.02) < 1e-9
gc2 = {c: 0.0 for c in closes}
assert X.trailing_sd(gc2, closes, 150) is None                                  # below SD_MIN

# decide: gold up buys YES only if the ask is in band; down buys NO at 1-bid
q = cs([(180, 0.30)], vol=20)
d = X.decide("KXSILVER15M", 1, q, T)
assert d["side"] == "yes" and abs(d["price"] - 0.31) < 1e-9
assert X.decide("KXSILVER15M", -1, q, T)["side"] is None                         # NO would cost 0.71, not cheap
dm = X.decide("KXSILVER15M", 1, q, T, against=True)                              # mirror: NO costs 0.71 -> nothing
assert dm["side"] is None
assert X.decide("KXSILVER15M", -1, q, T, against=True)["side"] == "yes"
assert X.decide("KXSILVER15M", 1, cs([(180, 0.30)], vol=3), T) is None           # volume rule
wide = [(T - 180, 0.20, 0.35, 50)]
assert X.decide("KXSILVER15M", 1, wide, T) is None                               # spread over 0.10
assert X.decide("KXSILVER15M", 1, cs([(180, 0.97)], vol=50), T)["side"] is None  # ask above 0.50
for s in X.NEVER:
    try:
        X.decide(s, 1, q, T); raise SystemExit("never-trade list failed " + s)
    except ValueError:
        pass

# pnl and payoff
assert abs(X.pnl("yes", 0.30, "yes") - (70 - 100 * X.fee(0.30))) < 1e-9
assert X.pnl("no", 0.30, "yes") < -30
assert abs(X.payoff([70, 70, -30, -30, -30]) - 70 / 30) < 1e-9

# build: a triggered gold window gives a metal trade, a flat one does not
markets, cands = {}, {}
for i in range(60):
    c = 900 * i + 10**6
    markets[f"G{i}"] = {"s": "KXGOLD15M", "close": c, "res": "yes", "vol": 1}
    up = (i == 59)
    base = 0.50 + (0.001 if i % 2 else -0.001)
    cands[f"G{i}"] = [(c - 360, base - .01, base + .01, 5), (c - 180, (base + (0.08 if up else (0.02 if i % 2 else -0.02))) - .01, (base + (0.08 if up else (0.02 if i % 2 else -0.02))) + .01, 5)]
c = 900 * 59 + 10**6
markets["S59"] = {"s": "KXSILVER15M", "close": c, "res": "yes", "vol": 1}
cands["S59"] = [(c - 180, 0.29, 0.31, 30)]
markets["S1"] = {"s": "KXSILVER15M", "close": 900 + 10**6, "res": "no", "vol": 1}
cands["S1"] = [(900 + 10**6 - 180, 0.29, 0.31, 30)]
rows, ng, nt = X.build(markets, cands)
r59 = [r for r in rows if r["close"] == c]
assert ng == 60 and len(r59) == 1 and r59[0]["H"]["side"] == "yes" and r59[0]["M"]["side"] is None, (ng, nt, rows)
print("test_xmet1: all passed")
