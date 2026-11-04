import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import pytest
from scalper import stressday1 as s

DAY = 86400
T0 = 1788480000  # 2026-09-04


def row(i, cat="Financials", look="T1440", ask=0.1, t=None):
    return {"cat": cat, "series": "X", "look": look, "t": t if t is not None else T0 + i * DAY, "event": f"E{i}", "ask": ask, "won": 1, "net": 9}


def test_outcomes_dropped_and_filters():
    r = s.entry_rows([row(0), row(1, cat="Sports"), row(2, look="A1h"), row(3, t=s.FROZEN_FROM + 5)])
    assert len(r) == 1 and "won" not in r[0] and "net" not in r[0]


def test_favourite_side_refused():
    with pytest.raises(AssertionError):
        s.entry_rows([row(0, ask=0.5)])


def test_vix_change_uses_only_prior_sessions():
    v = [("2026-09-01", 10.0), ("2026-09-02", 11.0), ("2026-09-03", 99.0)]
    assert s.vix_change(v, "2026-09-03") == pytest.approx(0.1)
    assert s.vix_change(v, "2026-09-02") is None


def test_census_not_enough_days():
    v = [(s.day_of(T0 + i * DAY), 10 + (i % 3)) for i in range(-3, 40)]
    res = s.census([row(i) for i in range(12)], v, set())
    assert res["days"] == 12 and res["verdict"] == "NOT_ENOUGH_DATA"
