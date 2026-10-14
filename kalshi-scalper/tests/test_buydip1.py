"""Plain assert tests for BUYDIP1 (src/scalper/buydip1.py); run with: python tests/test_buydip1.py. Each states a consequence, not a mechanism."""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import buydip1 as B

assert B.SYMBOLS == ("SCHD", "SPY", "QQQ") and B.RULES == ("DIP10", "MA200") and B.CONTRIBUTION == 500.0 and B.MONTHS == 60 and B.DIP == 0.10 and B.HIGH_DAYS == 252 and B.MA_DAYS == 200
assert B.MAX_WAIT_MONTHS == 6 and B.MIN_STARTS == 24 and B.MIN_SHARE == 0.60 and B.INFO_SYMBOL == "JEPQ"

def series(n_months, f, days_per_month=21, start=date(2015, 1, 1)):
    """Synthetic daily prices: month m, day k has price f(index). Dates advance 1 per trading day, 21 trading days a month on a fixed calendar."""
    out, d = [], start
    for m in range(n_months):
        for k in range(days_per_month):
            out.append((date(start.year + (start.month - 1 + m) // 12, (start.month - 1 + m) % 12 + 1, 1) + timedelta(days=k), f(len(out))))
    return out

flat = series(40, lambda i: 100.0)
ms = B.month_starts(flat)
assert len(ms) == 40 and ms[0] == 0 and ms[1] == 21
# Flat prices: every rule ends exactly where DCA does (R = 1), and DCA's end value is the contributions.
assert abs(B.simulate(flat, 0, 12, "DCA")["end"] - 12 * 500.0) < 1e-9
for rule in B.RULES:
    assert abs(B.simulate(flat, 0, 12, rule)["end"] - 6000.0) < 1e-9, rule
# A steadily rising market: waiting costs money, so a rule that waits never beats DCA (R at or below 1).
rising = series(90, lambda i: 100.0 * 1.002 ** i)
assert all(r["R"] <= 1.0 + 1e-12 for r in B.ratios(rising, "DIP10", 24)) and all(r["R"] <= 1.0 + 1e-12 for r in B.ratios(rising, "MA200", 24))
# Signals use only the past: changing prices AFTER day i never changes the signal at i.
px = [100.0] * 300
px2 = px[:299] + [1.0]
assert B.signal("DIP10", px, 250) == B.signal("DIP10", px2, 250) and B.signal("MA200", px, 250) == B.signal("MA200", px2, 250)
# DIP10 fires at exactly 10% below the trailing high, not at 9.9%; needs a full 252 days of history.
base = [100.0] * 300
assert not B.signal("DIP10", base[:299] + [90.1], 299) and B.signal("DIP10", base[:299] + [90.0], 299) and not B.signal("DIP10", base[:100] + [50.0], 100), "no signal before 252 days of history"
# MA200: below its 200 day average fires; equal to it does not.
assert B.signal("MA200", [100.0] * 199 + [99.9], 199) and not B.signal("MA200", [100.0] * 200, 199) and not B.signal("MA200", [50.0] * 50, 49)
# The six month fallback: with no dip at all, a contribution that has waited 6 months is spent, so the rule is never left in cash forever.
r = B.simulate(rising, 0, 12, "DIP10")
assert r["cash_days"] > 0 and r["end"] > 0
# The fallback is the registered 6 months: a shorter or no fallback changes how long cash sits, and the module constant is what the rule reads.
base_days = B.simulate(rising, 0, 24, "DIP10")["cash_days"]
B.MAX_WAIT_MONTHS = 3
try:
    short_days = B.simulate(rising, 0, 24, "DIP10")["cash_days"]
    B.MAX_WAIT_MONTHS = 999
    never_days = B.simulate(rising, 0, 24, "DIP10")["cash_days"]
finally:
    B.MAX_WAIT_MONTHS = 6
assert short_days < base_days < never_days
sim_long = B.simulate(rising, 0, 24, "MA200")
assert sim_long["end"] > 24 * 500.0 * 0.99
# A V-shaped market (long drift, a 30% crash, a recovery) rewards waiting: the dip rule beats DCA there.
def vshape(i):
    return 100.0 if i < 300 else (max(70.0, 100.0 - (i - 300)) if i < 600 else 70.0 + 0.2 * (i - 600))
vm = series(60, vshape)
assert B.simulate(vm, 12, 10, "DIP10")["end"] > B.simulate(vm, 12, 10, "DCA")["end"], "a window that ends in the crash rewards the dip rule"
# ... and one that runs through the recovery punishes it: it sat in cash while the price climbed back.
assert B.simulate(vm, 12, 24, "DIP10")["end"] < B.simulate(vm, 12, 24, "DCA")["end"]
# Cash earning interest raises a waiting rule's end value and never DCA's immediate-buy value.
assert B.simulate(vm, 12, 24, "DIP10", 0.04)["end"] > B.simulate(vm, 12, 24, "DIP10", 0.0)["end"]
assert abs(B.simulate(vm, 12, 24, "DCA", 0.04)["end"] - B.simulate(vm, 12, 24, "DCA", 0.0)["end"]) < 1e-6
# Windows need a full window of data: 40 months of data gives 16 start months of 24, and a 60 month window on it gives none.
assert len(B.ratios(flat, "DIP10", 24)) == 16 and B.ratios(flat, "DIP10", 60) == []

# Verdicts.
rows = lambda f, n=40: [{"start": s, "R": f(s), "cash_share": 0.2} for s in range(n)]
assert B.verdict(rows(lambda s: 1.1, 10))[0] == "NOT_ENOUGH_DATA"
v, d = B.verdict(rows(lambda s: 1.02)); assert v == "NOT_YET_FALSIFIED" and d["audit"]
assert B.verdict(rows(lambda s: 0.98))[0] == "FALSIFIED"
assert B.verdict(rows(lambda s: 1.05 if s < 20 else 0.97))[0] == "FALSIFIED", "second half below 1"
assert B.verdict(rows(lambda s: 0.97 if s < 20 else 1.05))[0] == "FALSIFIED", "first half below 1"
assert B.verdict(rows(lambda s: 1.2 if s % 5 == 0 else 0.99))[0] == "FALSIFIED", "median below 1 and R above 1 only 20% of the time"
assert B.verdict(rows(lambda s: 1.01 if s % 5 else 0.99))[0] == "NOT_YET_FALSIFIED"
assert B.verdict(rows(lambda s: 1.01 if s % 2 else 0.99))[0] == "FALSIFIED", "R above 1 only half the time is under the 60% bar"
v, d = B.verdict(rows(lambda s: 1.01 if s % 20 < 11 else 0.5)); assert d["median"] > 1.0 and d["share"] == 0.55 and d["h1"] > 1.0 and d["h2"] > 1.0 and v == "FALSIFIED", "median above 1 but R above 1 in only 55%"
v, d = B.verdict(rows(lambda s: 1.05 if s < 20 or s % 5 == 0 else 0.97)); assert d["median"] > 1.0 and d["share"] >= 0.6 and d["h1"] > 1.0 and d["h2"] <= 1.0 and v == "FALSIFIED", (v, d)
v, d = B.verdict(rows(lambda s: 1.05 if s >= 20 or s % 5 == 0 else 0.97)); assert d["median"] > 1.0 and d["share"] >= 0.6 and d["h2"] > 1.0 and d["h1"] <= 1.0 and v == "FALSIFIED", (v, d)
code = "\n".join(l.split("#")[0] for l in Path(B.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("BUYDIP1 passed")
