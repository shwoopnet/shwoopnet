import math
from datetime import datetime, timedelta, timezone

from scalper import equake1 as e

UTC = timezone.utc
T0 = datetime(2026, 9, 10, tzinfo=UTC)


def cat(n_per_day=20, days=800):
    out = []
    for d in range(days):
        for k in range(n_per_day):
            # magnitude ladder so the mean gives b near 1
            m = 4.5 + (-math.log10(1 - (k + 0.5) / n_per_day)) / 1.0
            out.append((T0 - timedelta(days=days - d, hours=-k % 20), round(m, 1)))
    return out


def test_fit_uses_only_past():
    ev = cat()
    lam, b = e.fit(ev, T0)
    assert 15 < lam < 25 and 0.5 < b < 1.5
    ev2 = ev + [(T0 + timedelta(hours=1), 9.0)] * 200
    assert e.fit(ev2, T0) == e.fit(ev, T0)


def test_fair_monotone_and_bounds():
    lam, b = 20.0, 1.0
    assert e.fair(lam, b, 5.0) > e.fair(lam, b, 6.0) > e.fair(lam, b, 7.0) > 0
    assert e.fair(lam, b, 4.5) < 1.0
    assert e.fair(0.0, b, 5.0) == 0.0


def test_decide_edge_after_fee_and_spread():
    assert e.decide(0.5, 0.30, 0.34)[0] == "yes"
    assert e.decide(0.5, 0.30, 0.45) is None  # spread over 10c
    assert e.decide(0.2, 0.60, 0.64)[0] == "no"
    assert e.decide(0.50, 0.46, 0.50) is None  # edge too small


def test_first_quote_no_lookahead():
    t0 = T0
    cs = [dict(end_period_ts=int(t0.timestamp()) - 60, yes_bid=dict(close_dollars="0.1"), yes_ask=dict(close_dollars="0.2")),
          dict(end_period_ts=int(t0.timestamp()) + 60, yes_bid=dict(close="0.3"), yes_ask=dict(close="0.4")),
          dict(end_period_ts=int(t0.timestamp()) + 7200, yes_bid=dict(close="0.5"), yes_ask=dict(close="0.6"))]
    assert e.first_quote(cs, t0, 1800) == (0.3, 0.4)
    assert e.first_quote(cs[:1] + cs[2:], t0, 1800) is None


def test_split_and_end_to_end():
    days = [T0 + timedelta(days=i) for i in range(9)]
    w = e.split_days(days)
    assert [w[d] for d in days] == ["disc"] * 3 + ["val"] * 3 + ["hold"] * 3
    ev = cat()
    ms, cd = [], {}
    for d in days:
        for k in (5.2, 6.0):
            t = f"KXBIGGESTQUAKE-{d:%d}{list(e.MONTHS)[d.month-1]}{d:%y}-{k}"
            ms.append(dict(ticker=t, floor_strike=k, result="no"))
            cd[t] = [dict(end_period_ts=int(d.timestamp()) + 60, yes_bid=dict(close_dollars="0.80"), yes_ask=dict(close_dollars="0.84"))]
    tr, bm, bk, n = e.score(ms, ev, cd, "A")
    assert n > 0 and len(bm) == n
    v = e.verdict(tr, bm, bk, "A")[0]
    assert v in ("NOT_ENOUGH_DATA", "FALSIFIED")
    assert all(t["p"] < 0 for t in tr if t["side"] == "yes")  # result "no" loses every YES buy
