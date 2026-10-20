"""Plain assert tests for TP1 (src/scalper/tp1.py); run with: python tests/test_tp1.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import tp1 as T
from scalper.scalps import fee

# Registered: 99c, the single-try z bar, checks at 300..60 s.
assert T.TP == 0.99 and T.PASS_Z == 2.5 and T.CHECK_LEFT_S == (300, 240, 180, 120, 60) if hasattr(T, "CHECK_LEFT_S") else True

CLOSE = 10_000
entry = {"ticker": "T", "side": "yes", "close_ts": CLOSE, "price": 0.93, "gross": 0.07, "day": "d1", "series": "KXBTC15M"}   # a winner: gross = won - price
c = lambda left, bid, ask: (CLOSE - left, bid, ask)

# It sells at the FIRST check at or above 99c, at that bid, and never looks at the entry candle (360 s) or the result.
assert T.find_tp(entry, [c(360, 0.995, 0.999), c(300, 0.97, 0.98), c(240, 0.99, 1.0), c(180, 0.998, 1.0)]) == (0.99, 240)
assert T.find_tp(entry, [c(300, 0.98, 0.99), c(60, 0.989, 0.99)]) is None, "98.9c is below the line"
# A NO position reads one minus the YES ask.
no = dict(entry, side="no")
assert T.find_tp(no, [c(120, 0.001, 0.005)]) == (0.995, 120)

# Selling at 99c gives up the last cent on a winner and pays a sell fee: the rule costs money when the favourite was going to win anyway.
rows = T.build([entry], {"T": [c(240, 0.99, 1.0)]})
r = rows[0]
assert abs(r["hold"] - (1.0 - 0.93 - fee(0.93))) < 1e-9
assert abs(r["net"] - (0.99 - 0.93 - fee(0.93) - fee(0.99))) < 1e-9 and r["net"] < r["hold"], "on a winner the cash-out is worse than holding"

# On a flip (touched 99c, then lost) the cash-out is far better than holding: that is the whole case for the rule.
loser = dict(entry, gross=-0.93)
rl = T.build([loser], {"T": [c(240, 0.99, 1.0)]})[0]
assert rl["hold"] < -0.9 and rl["net"] > 0.0 and rl["exit"] is not None
assert T.flip_rate([r, rl]) == (2, 1), "two reached the line, one of them then lost"

# Verdicts: a cash-out that loses 1c a day-cluster is FALSIFIED; one that wins in every day, both halves and under stress passes; too few entries is NOT_ENOUGH_DATA.
def mk(n_days, per, diff):
    out = []
    for d in range(n_days):
        for i in range(per):
            out.append({"day": f"d{d:02d}", "net": 0.05 + diff + 0.001 * (i % 3) + 0.002 * ((d % 3) - 1), "hold": 0.05, "stress": 0.04 + diff, "hold_stress": 0.04})
    return out
assert T.verdict(mk(10, 5, 0.01), 0.0)[0] == "NOT_ENOUGH_DATA"
assert T.verdict(mk(10, 60, -0.011), 0.0)[0] == "FALSIFIED"
assert T.verdict(mk(10, 60, 0.011), 0.0)[0] == "NOT_YET_FALSIFIED"
assert T.verdict(mk(10, 60, 0.011), 0.02)[0] == "FALSIFIED", "a difference below what the rule costs in a fair market is not an edge"
weak = mk(10, 60, 0.011)
for x in weak:
    x["stress"] = x["hold_stress"] - 0.001
assert T.verdict(weak, 0.0)[0] == "FALSIFIED", "positive only at the base fee is not enough"
print("ok")
