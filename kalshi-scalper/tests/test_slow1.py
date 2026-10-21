"""Plain assert tests for SLOW1 (src/scalper/slow1.py); run with: python tests/test_slow1.py. Each states a consequence, not a mechanism."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import slow1 as S

assert (S.ETFS, S.START, S.CELLS, S.COST_SIDE, S.STRESS, S.MIN_MONTHS, S.Z_BAR, S.PLACEBO_REPS, S.NW_LAGS) == (
    ["SPY", "QQQ", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "UUP"], "2007-03-01", {"S1": 252, "S2": 126, "S3": 63}, 0.0005, 1.2, 120, 2.5, 200, 3), "the registered numbers"


def fake(n=900):
    dates = [f"{2010 + i // 252}-{(i % 252) // 21 + 1:02d}-{(i % 21) + 1:02d}" for i in range(n)]
    return {e: {d: 100.0 + i * 0.1 for i, d in enumerate(dates)} for e in S.ETFS}, dates


# 1. A month's flag cannot change when prices AFTER its signal day change.
bars, dates = fake()
rows = S.monthly_rows(bars, dates, 63)
cut = dates.index(rows[5]["date"])
for e in S.ETFS:
    for d in dates[cut + 1:]:
        bars[e][d] = 0.5
rows2 = S.monthly_rows(bars, dates, 63)
assert [r["flag"] for r in rows2[:6]] == [r["flag"] for r in rows[:6]], "no lookahead in the flag"
# the return is taken from the NEXT day's close, not the signal day's close
bars, dates = fake()
r0 = S.monthly_rows(bars, dates, 63)[0]
i = dates.index(r0["date"])
assert abs(r0["ret"]["SPY"] - (bars["SPY"][dates[S.month_ends(dates)[S.month_ends(dates).index(i) + 1] + 1]] / bars["SPY"][dates[i + 1]] - 1)) < 1e-12, "entry at the day after the signal"

# 2. Regression recovers a known alpha and beta.
rng = random.Random(3)
x = [rng.gauss(0.01, 0.04) for _ in range(300)]
y = [0.002 + 0.5 * v + rng.gauss(0, 0.002) for v in x]
a, b, z = S.ols_nw(y, x)
assert abs(a - 0.002) < 3e-4 and abs(b - 0.5) < 0.02 and z > 5

# 3. Always invested equals the benchmark apart from the one-off entry cost.
rows = S.monthly_rows(*fake(), 63)
s, bm = S.strategy_series(rows, [{e: True for e in S.ETFS} for _ in rows])
assert abs(s[0] - (bm[0] - S.COST_SIDE)) < 1e-12 and all(abs(p - q) < 1e-12 for p, q in zip(s[1:], bm[1:])), "cost only on traded weight"
# 4. Never invested earns exactly zero.
s0, _ = S.strategy_series(rows, [{e: False for e in S.ETFS} for _ in rows])
assert all(v == 0.0 for v in s0)
print("test_slow1: ok")
