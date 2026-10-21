"""Plain assert tests for RP1, CS1 and FA1 (src/scalper/fam4.py); run with: python tests/test_fam4.py."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import fam4 as F

assert (F.RP_ASSETS, F.RP_VOL_DAYS, F.RP_COST, F.CS_TARGET, F.CS_DAYS, F.CS_COST, F.FA_ASSETS, F.FA_COST, F.vm.Z_BAR, F.PLACEBO_REPS) == (
    ["SPY", "TLT", "GLD", "DBC"], 63, 0.0005, 0.40, 21, 0.0035, ["MTUM", "QUAL", "VLUE", "SIZE"], 0.0005, 2.9, 200), "the registered numbers"
dates = [f"{2007 + i // 252}-{(i % 252) // 21 + 1:02d}-{(i % 21) + 1:02d}" for i in range(3000)]
r = random.Random(7)
def path(sig):
    p = [100.0]
    for _ in range(2999):
        p.append(p[-1] * (1 + r.gauss(0.0003, sig)))
    return {d: v for d, v in zip(dates, p)}
bars = {"SPY": path(0.010), "TLT": path(0.006), "GLD": path(0.009), "DBC": path(0.012)}
rows = F.rp_rows(bars)
# 1. Weights sum to one and the lower-volatility asset gets the larger weight on average.
assert all(abs(sum(x["w"]) - 1) < 1e-12 for x in rows)
avg = [sum(x["w"][k] for x in rows) / len(rows) for k in range(4)]
assert avg[1] == max(avg) and avg[3] == min(avg), "inverse volatility ordering"
# 2. Weights use closes through the signal day only.
cut = dates.index(rows[10]["date"])
rr = random.Random(99)
b2 = {a: {d: (v if k <= cut else v * (1 + rr.gauss(0, 0.3))) for k, (d, v) in enumerate(sorted(bars[a].items()))} for a in bars}
assert [x["w"] for x in F.rp_rows(b2)[:11]] == [x["w"] for x in rows[:11]], "no lookahead"
# 3. Benchmark is 60/40 of the first two assets; cost is on traded weight (first month pays the whole entry).
s, b = F.rp_series([{"ret": [0.01, 0.02, 0.0, 0.0]}] * 2, [[0.25] * 4, [0.25] * 4])
assert abs(b[0] - (0.006 + 0.008)) < 1e-12 and abs(s[0] - (0.0075 - F.RP_COST)) < 1e-12 and abs(s[1] - 0.0075) < 1e-12
# 4. Bitcoin volatility uses 365 days a year.
flat = [100.0 * (1.01 if k % 2 else 0.99) ** 1 for k in range(60)]
assert abs(F.vol(flat, 40, 21, 365) / F.vol(flat, 40, 21, 252) - (365 / 252) ** 0.5) < 1e-9
print("test_fam4: ok")
