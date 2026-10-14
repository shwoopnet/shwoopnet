"""Plain assert tests for IDX1 (src/scalper/idx1.py); run with: python tests/test_idx1.py. Each states a consequence, not a mechanism."""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import idx1 as I

assert I.SYMBOLS == ("SPY", "QQQ") and I.SPLIT == date(2012, 1, 1) and I.COST == 0.0002 and I.STRESS_COST == 0.0004 and I.Z_BAR == 2.4 and I.MIN_ACTIVE == 150
assert I.TRIES == (("A_overnight", "SPY"), ("A_overnight", "QQQ"), ("B_turn_of_month", "SPY"), ("C_pre_holiday", "SPY"))

def cal(start, n, holidays=()):
    """n weekday sessions from `start`, skipping the given holiday dates."""
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5 and d not in holidays:
            out.append(d)
        d += timedelta(days=1)
    return out

def rows_of(dates, r, o):
    return [{"date": d, "r": r(i, d), "o": o(i, d)} for i, d in enumerate(dates)]

# Calendar: Tue 2024-12-31 is the last session of 2024, Jan 1 is a holiday, Jan 2 is the first session.
dates = cal(date(2024, 12, 24), 12, holidays={date(2024, 12, 25), date(2025, 1, 1)})
assert dates[0] == date(2024, 12, 24) and date(2025, 1, 1) not in dates
rows = rows_of(dates, lambda i, d: 0.01, lambda i, d: 0.004)
# A: the overnight return minus the cost EVERY day.
assert all(abs(x - (0.004 - 0.0002)) < 1e-12 for x in I.strategy_returns(rows, "A_overnight", 0.0002))
# B: only the first three sessions of a calendar month are held; the cost is taken once, on the third.
b = I.strategy_returns(rows, "B_turn_of_month", 0.0002)
jan = [i for i, x in enumerate(rows) if x["date"].month == 1][:4]
dec = [i for i, x in enumerate(rows) if x["date"].month == 12][:4]
assert [b[i] for i in dec[:3]] == [0.01, 0.01, 0.01 - 0.0002] and b[dec[3]] == 0.0
assert [b[i] for i in jan[:3]] == [0.01, 0.01, 0.01 - 0.0002] and b[jan[3]] == 0.0
# C: the pre-holiday session is the one whose NEXT session comes after a weekday with no trading: Dec 24 (Dec 25 closed) and Dec 31 (Jan 1 closed), not an ordinary Friday.
c = I.strategy_returns(rows, "C_pre_holiday", 0.0002)
held = [rows[i]["date"] for i, v in enumerate(c) if v != 0.0]
assert held == [date(2024, 12, 24), date(2024, 12, 31)] and all(abs(v - (0.01 - 0.0002)) < 1e-12 for v in c if v != 0.0)
assert I.active_periods(rows, "C_pre_holiday") == 2 and I.active_periods(rows, "A_overnight") == len(rows) and I.active_periods(rows, "B_turn_of_month") == 2
# A weekend alone is not a holiday.
fri = cal(date(2024, 3, 4), 10)
assert I.strategy_returns(rows_of(fri, lambda i, d: 0.01, lambda i, d: 0.0), "C_pre_holiday", 0.0) == [0.0] * 10

# Alpha: a rule that is always long and earns exactly the market has zero alpha; one that earns a constant extra every day has that constant, annualised, with beta 1.
long_dates = cal(date(2010, 1, 4), 600)
import random
rng = random.Random(3)
rs = [rng.gauss(0.0004, 0.01) for _ in long_dates]
mk = lambda extra: [{"date": d, "r": r, "o": r + extra} for d, r in zip(long_dates, rs)]
a0 = I.alpha(mk(0.0), "A_overnight", 0.0)
assert abs(a0["alpha_year"]) < 1e-9 and abs(a0["beta"] - 1.0) < 1e-9
a1 = I.alpha(mk(0.0005), "A_overnight", 0.0)
assert abs(a1["alpha_year"] - 0.0005 * 252) < 1e-9
assert abs(I.alpha(mk(0.0005), "A_overnight", 0.0002)["alpha_year"] - 0.0003 * 252) < 1e-9, "the cost comes straight off the alpha"

# Verdicts on a long synthetic history: discovery and holdout both earn a constant extra overnight.
dates = cal(date(1995, 1, 2), 8000)
rs = [rng.gauss(0.0004, 0.01) for _ in dates]
def build(extra_disc, extra_hold):
    return [{"date": d, "r": r, "o": r + (extra_disc if d < I.SPLIT else extra_hold)} for d, r in zip(dates, rs)]
v, d = I.verdict(build(0.0006, 0.0006), "A_overnight")
assert v == "NOT_YET_FALSIFIED" and d["holdout"]["z"] >= I.Z_BAR and d["h1"] > 0 and d["h2"] > 0 and d["stress"]["alpha_year"] > 0 and d["discovery"]["alpha_year"] > 0, (v, d)
# Each requirement bites alone.
v, d = I.verdict(build(0.0006, 0.0001), "A_overnight"); assert d["holdout"]["alpha_year"] < 0.05 and v == "FALSIFIED", (v, d)           # the effect is gone after costs in the holdout
v, d = I.verdict(build(-0.0006, 0.0006), "A_overnight"); assert d["holdout"]["z"] >= I.Z_BAR and d["discovery"]["alpha_year"] < 0 and v == "FALSIFIED", (v, d)   # never existed in discovery
v, d = I.verdict(build(0.0006, 0.00027), "A_overnight"); assert d["holdout"]["alpha_year"] > 0 and d["stress"]["alpha_year"] < 0 and v == "FALSIFIED", (v, d)   # dies at the stress cost
v, d = I.verdict(build(0.0006, 0.00005), "A_overnight"); assert v == "FALSIFIED"
# A noisy holdout whose alpha is positive at both costs and in both halves but under the 2.4 bar is not a pass: the z requirement bites by itself.
noise = random.Random(11)
noisy = [{"date": d, "r": r, "o": r + 0.00045 + noise.gauss(0, 0.01)} for d, r in zip(dates, rs)]
v, d = I.verdict(noisy, "A_overnight")
assert d["holdout"]["alpha_year"] > 0 and d["stress"]["alpha_year"] > 0 and d["h1"] > 0 and d["h2"] > 0 and d["discovery"]["alpha_year"] > 0 and d["holdout"]["z"] < I.Z_BAR and v == "FALSIFIED", (v, d)
# A holdout whose alpha comes from one half only fails on the other half, however large the total.
mid = I.SPLIT.replace(year=2019)
first_only = [{"date": d, "r": r, "o": r + (0.0014 if d < mid else 0.0)} for d, r in zip(dates, rs)]
second_only = [{"date": d, "r": r, "o": r + (0.0014 if d >= mid or d < I.SPLIT else 0.0)} for d, r in zip(dates, rs)]
v1, d1 = I.verdict(first_only, "A_overnight"); assert d1["holdout"]["z"] >= I.Z_BAR and d1["h1"] > 0 > d1["h2"] and v1 == "FALSIFIED", (v1, d1)
v2, d2 = I.verdict(second_only, "A_overnight"); assert d2["holdout"]["z"] >= I.Z_BAR and d2["h2"] > 0 > d2["h1"] and v2 == "FALSIFIED", (v2, d2)
# Too few active periods in the holdout.
assert I.verdict([x for x in build(0.0006, 0.0006) if x["date"] < date(2012, 6, 1)], "A_overnight")[0] == "NOT_ENOUGH_DATA"
assert I.verdict(build(0.0006, 0.0006)[:100], "A_overnight")[0] == "NOT_ENOUGH_DATA"
code = "\n".join(l.split("#")[0] for l in Path(I.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("IDX1 passed")
