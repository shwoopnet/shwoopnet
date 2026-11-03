import math, sys, os
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import count1 as c

def test_pmf_sums():
    assert abs(sum(c.nb_pmf(30, 10, 600)) - 1) < 1e-6
    assert c.nb_pmf(0, 10, 5)[0] == 1.0

def test_strike_semantics():
    pmf = [0.0] * 3 + [1.0]  # R = 3 surely
    assert c.bracket_prob({"strike_type": "between", "floor_strike": 10, "cap_strike": 13}, 10, pmf) == 1.0
    assert c.bracket_prob({"strike_type": "greater", "floor_strike": 13, "cap_strike": None}, 10, pmf) == 0.0
    assert c.bracket_prob({"strike_type": "greater_or_equal", "floor_strike": 13}, 10, pmf) == 1.0
    assert c.bracket_prob({"strike_type": "less", "cap_strike": 13}, 10, pmf) == 0.0

def test_dst_period():
    m = {"rules_primary": "x", "rules_secondary": "begins at 12:00:00 AM ET on Nov 1, 2026 and ends at 11:59:59 PM ET on Nov 1, 2026"}
    a, b = c.parse_period(m)
    assert (b - a) == timedelta(hours=25)  # DST ends 2026-11-01

def test_fee_and_cap():
    assert abs(c.fee(0.5) - 0.018) < 1e-9
    rows = [("a", .9, .2), ("b", .5, .1), ("c", .4, .1), ("d", .1, .2)]
    sel = c.select(rows)
    assert len(sel) == 2 and sel[0][0] == "b" and all(r[0] != "d" for r in sel)

def test_expected_sums_hours():
    prof = [1.0] * 24
    a = datetime(2026, 11, 2, 5, 0, tzinfo=timezone.utc)
    assert abs(c.expected(prof, a, a + timedelta(hours=5)) - 5.0) < 1e-9
