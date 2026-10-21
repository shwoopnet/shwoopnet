"""Plain assert tests for SECT1 (src/scalper/sect1.py); run with: python tests/test_sect1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import sect1 as S

assert (S.SECTORS, S.CELLS, S.SKIP, S.TOP_N, S.COST_SIDE, S.STRESS, S.MIN_MONTHS, S.Z_BAR, S.PLACEBO_REPS) == (
    ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"], {"C1": 252, "C2": 126}, 21, 3, 0.0005, 1.2, 120, 2.6, 200), "the registered numbers"


def fake(n=900):
    dates = [f"{2010 + i // 252}-{(i % 252) // 21 + 1:02d}-{(i % 21) + 1:02d}" for i in range(n)]
    # sector k grows at rate 0.05 * (k + 1) per day so the ranking is known: XLY, XLV, XLU are the top three
    return {e: {d: 100.0 * (1 + 0.0005 * (k + 1)) ** i for i, d in enumerate(dates)} for k, e in enumerate(S.SECTORS)}, dates


bars, dates = fake()
rows = S.monthly_rows(bars, dates, 126)
assert all(r["picks"] == ["XLY", "XLV", "XLU"] for r in rows), "ranks by the known growth order"
# 1. Prices after a month's signal day cannot change that month's picks.
cut = dates.index(rows[5]["date"])
for e in S.SECTORS:
    for d in dates[cut + 1:]:
        bars[e][d] = 1.0 if e == "XLB" else bars[e][d]
assert [r["picks"] for r in S.monthly_rows(bars, dates, 126)[:6]] == [r["picks"] for r in rows[:6]], "no lookahead in the picks"
# 2. The latest 21 days are skipped: a spike in the final month before the signal does not change the ranking.
bars, dates = fake()
i = dates.index(rows[3]["date"])
bars["XLB"][dates[i]] = 1e9
assert S.monthly_rows(bars, dates, 126)[3]["picks"] == ["XLY", "XLV", "XLU"], "skip-month: the last day's price is not in the score"
# 3. Costs only on traded weight: a constant pick pays once, on entry.
bars, dates = fake()
rows = S.monthly_rows(bars, dates, 126)
s, b = S.series(rows, [r["picks"] for r in rows])
gross = [sum(r["ret"][e] for e in r["picks"]) / 3 for r in rows]
assert abs(s[0] - (gross[0] - S.COST_SIDE)) < 1e-12 and all(abs(p - q) < 1e-12 for p, q in zip(s[1:], gross[1:]))
print("test_sect1: ok")
