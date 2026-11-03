import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import usweep2 as u2, usweep1 as u1

DAY = 86400
T0 = 1_790_000_000 // DAY * DAY


def mk(series, i, life=3600, vol=500.0):
    close = T0 + (i % 30) * DAY + 3600 * 12
    return [f"{series}-{i}", close - life, close, None, vol, False]


def rec(series, n, **kw):
    return {"ticker": series, "freq": "daily", "cat": "X", "title": "t", "markets": [mk(series, i, **kw) for i in range(n)]}


def test_series_of():
    assert u2.series_of("KXNHLGAME-26OCT31EDMNYI") == "KXNHLGAME"
    assert u2.series_of("ABC") == "ABC"


def test_row_of():
    r = u2.row_of({"ticker": "A-1-X", "event_ticker": "A-1", "open_time": "2026-10-01T00:00:00Z", "close_time": "2026-10-01T01:00:00Z", "volume_fp": "12.5"})
    assert r[1] == "A" and r[3] - r[2] == 3600 and r[5] == 12.5 and r[4] is None


def test_candidates_screen():
    rows = [[f"S-{i}", "S", T0, T0 + (i % 3) * DAY + 100, None, 1.0, False] for i in range(20)] + [[f"R-{i}", "R", T0, T0 + 100, None, 1.0, False] for i in range(20)]
    c = u2.candidates(rows)
    assert "S" in c and "R" not in c      # R has 20 markets but one close date


def test_eligible_rule():
    assert u2.eligible(rec("A", 300), set())
    assert u2.eligible(rec("A", 299), set()) is None
    assert u2.eligible(rec("A", 300), {"A"}) is None            # USWEEP1 series excluded
    assert u2.eligible(rec("KXMVEX", 300), set()) is None
    assert u2.eligible(rec("A", 300, vol=5.0), set()) is None   # dead book
    r = rec("A", 300); r["freq"] = "fifteen_min"
    assert u2.eligible(r, set()) is None


def test_sample_deterministic_and_capped():
    r = rec("A", 300)
    a, b = u2.sampled(r), u2.sampled(dict(r, markets=list(reversed(r["markets"]))))
    assert len(a) == u2.SAMPLE_PER_SERIES and [m[0] for m in a] == [m[0] for m in b]


def test_frozen_third_not_in_dev():
    r = rec("A", 300)
    dev, dev_days = u2.dev_markets(r)
    allm = u2.sampled(r)
    _, frozen = u1.split_dates([u1.market_date(m) for m in allm])
    assert frozen and all(u1.market_date(m) not in set(frozen) for m in dev)
    assert len(dev) < len(allm)


def test_favourite_rule_is_dropped():
    assert set(u1.RULES) == {"tail", "fav"}      # usweep1 untouched
    r = {"class": "D"}
    t = 1_790_000_000 // 3600 * 3600
    m = ["X-1", t - 200000, t + 86400, None, 1.0, False]
    anc = u1.anchor_of(m)
    cs = [[anc - 1440 * 60 - 60, 0.05, 0.92, 1.0]]            # yes ask 0.92 is a favourite, no ask 0.95 is a favourite too: nothing to take
    out = u2.entries_for(r, [m], {"X-1": cs}, {"X-1": "yes"})
    assert all(rule == "tail" for (_, rule) in out) and not out


def test_tail_taken_and_no_favourite_cell():
    r = {"class": "D"}
    t = 1_790_000_000 // 3600 * 3600
    m = ["X-1", t - 200000, t + 86400, None, 1.0, False]
    anc = u1.anchor_of(m)
    cs = [[anc - 1440 * 60 - 60, 0.88, 0.92, 1.0]]            # yes ask 0.92 (favourite, ignored), no ask 0.12 (tail)
    out = u2.entries_for(r, [m], {"X-1": cs}, {"X-1": "no"})
    assert list(out) == [(1440, "tail")] and out[(1440, "tail")][0][1] == 0.12 and out[(1440, "tail")][0][2]
