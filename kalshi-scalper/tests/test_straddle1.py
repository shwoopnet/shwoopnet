import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import straddle1 as S

DAYS = [dt.date(2026, 11, 2) + dt.timedelta(days=i) for i in range(30)]
DAYS = [d for d in DAYS if d.weekday() < 5]


def test_after_close_sells_same_day_close():
    d = dt.date(2026, 11, 5)
    assert S.exit_day(dt.datetime(2026, 11, 5, 16, 5), DAYS) == d
    assert S.entry_day(d, DAYS) == dt.date(2026, 11, 2)


def test_before_open_and_weekend_sell_prior_close():
    assert S.exit_day(dt.datetime(2026, 11, 5, 7, 0), DAYS) == dt.date(2026, 11, 4)
    assert S.exit_day(dt.datetime(2026, 11, 5, 11, 0), DAYS) == dt.date(2026, 11, 4)
    assert S.exit_day(dt.datetime(2026, 11, 7, 12, 0), DAYS) == dt.date(2026, 11, 6)  # Saturday -> Monday announcement


def test_eligibility_and_return():
    assert S.eligible(2.0, 2.04, 1.9, 1.94)
    assert not S.eligible(2.0, 2.2, 1.9, 2.1)
    assert not S.eligible(0, 0.1, 0.4, 0.5)
    r = S.event_return(2.04, 1.94, 2.2, 2.1)
    assert abs(r - ((4.3 - 3.98 - 0.0012) / 3.98)) < 1e-12
