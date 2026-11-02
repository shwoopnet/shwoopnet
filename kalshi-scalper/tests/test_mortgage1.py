"""Plain assert tests for MORTGAGE1 (src/scalper/mortgage1.py); run with: python tests/test_mortgage1.py."""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import mortgage1 as M

# Synthetic world: PMMS change = 0.5 x the 10y change exactly, so a fit recovers b = 0.5 and no information after the release date enters.
pm, y = {}, {}
d0 = date(2010, 1, 7)
lvl, yl = 5.0, 3.5
for i in range(400):
    d = d0 + timedelta(days=7 * i)
    for j in range(7):
        y[d - timedelta(days=j)] = yl + 0.001 * j
    step = ((i * 37) % 11 - 5) / 100.0
    wk_y = y[d - timedelta(days=1)]
    pm[d] = lvl
    yl += step
    lvl += 0.5 * step
before = d0 + timedelta(days=7 * 300)
a, b, sd = M.fit(pm, y, before)
assert abs(b - 0.5) < 0.25 and sd < 0.2
# A fit never uses the release it is asked about: changing a later PMMS value leaves the fit unchanged.
pm2 = dict(pm); pm2[before + timedelta(days=7)] = 99.0
assert M.fit(pm2, y, before) == (a, b, sd)
# Too few weeks gives no fit.
assert M.fit(pm, y, d0 + timedelta(days=7 * 20)) is None
# Fair probability: centre above the strike by a lot is near 1, a print at the strike has the 0.005 rounding shift.
assert M.fair_above(6.0, 7.0, 0.05) > 0.99 and M.fair_above(8.0, 7.0, 0.05) < 0.01
assert abs(M.fair_above(7.0, 7.005, 0.05) - 0.5) < 1e-9
# Decision: needs a valid quote, the spread cut and the 8c gap; NO side pays 1 - bid.
assert M.decide(0.60, 0.40, 0.50) == ("yes", 0.50)
assert M.decide(0.30, 0.45, 0.50) == ("no", 0.55)
assert M.decide(0.55, 0.40, 0.50) is None            # gap 5c
assert M.decide(0.90, 0.40, 0.55) is None            # spread 15c
assert M.decide(0.90, None, 0.55) is None and M.decide(0.9, 0.0, 0.5) is None
assert M.decide(0.30, 0.45, 0.50, side_only_cheap=True) is None   # 55c side is not a long shot
assert M.decide(0.60, 0.40, 0.50, side_only_cheap=True) is None
# Windows are thirds by event order.
w = M.split3(list("abcdefghij"))
assert [w[c] for c in "abcdefghij"] == ["w1"] * 3 + ["w2"] * 3 + ["w3"] * 4
assert M.event_date("KX30YMORTW-26OCT29") == date(2026, 10, 29)
print("ok")
