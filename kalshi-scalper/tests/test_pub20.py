"""PUB20 helpers on hand-built data. Research only. Plain runner."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import pub20  # noqa: E402

CT = 1_790_000_100  # a multiple of 900? adjusted below
CT = CT - CT % 900


def test_fee_is_event1_cost():
    # 50c, 10 contracts: 7% x 10 x .25 = 0.175 -> 18c rounded up -> 1.8c a contract; win nets 100*(1-.5-.018)
    assert abs(pub20.net_c(0.5, True) - 48.2) < 1e-6
    assert abs(pub20.net_c(0.5, False) + 51.8) < 1e-6


def test_nr7_needs_seven_contiguous_and_strictly_smallest():
    ms = {CT - 900 * j: (0.001 if j == 0 else 0.01 * (j + 1)) for j in range(7)}
    assert pub20.nr7_flag(ms, CT)
    ms2 = dict(ms); ms2[CT - 900 * 3] = 0.001            # tie with the newest: not strictly smaller
    assert not pub20.nr7_flag(ms2, CT)
    ms3 = dict(ms); del ms3[CT - 900 * 4]                # a gap
    assert not pub20.nr7_flag(ms3, CT)


def test_volexp_threshold():
    cts = [CT - 900 * j for j in range(120, -1, -1)]
    ms = {c: 0.01 for c in cts}
    assert not pub20.volexp_flag(ms, cts, CT)
    for j in range(4):
        ms[CT - 900 * j] = 0.02
    assert pub20.volexp_flag(ms, cts, CT)               # 2x the median, bar is 1.5x
    short = cts[-40:]
    assert not pub20.volexp_flag({c: ms[c] for c in short}, short, CT)   # fewer than 48 trailing moves


def test_month_end_dates_are_the_last_two_business_days():
    import datetime as dt
    for d in pub20.MONTH_ENDS:
        y, m, dd = map(int, d.split("-"))
        assert dt.date(y, m, dd).weekday() < 5
    assert "2026-08-28" in pub20.MONTH_ENDS and "2026-08-31" in pub20.MONTH_ENDS and "2026-08-30" not in pub20.MONTH_ENDS


def test_fix_windows_follow_local_clock():
    import datetime as dt
    from zoneinfo import ZoneInfo
    # 2026-09-15 16:00 London (BST, UTC+1) = 15:00 UTC, a Tuesday
    ct = int(dt.datetime(2026, 9, 15, 15, 0, tzinfo=dt.timezone.utc).timestamp())
    assert pub20.fix_name("KXEURUSD15M", ct) == "LON16"
    assert pub20.fix_name("KXSILVER15M", ct) is None
    # 2026-11-03 16:00 London (GMT) = 16:00 UTC
    ct = int(dt.datetime(2026, 11, 3, 16, 0, tzinfo=dt.timezone.utc).timestamp())
    assert pub20.fix_name("KXGBPUSD15M", ct) == "LON16"
    # 10:00 New York in EDT = 14:00 UTC
    ct = int(dt.datetime(2026, 9, 15, 14, 0, tzinfo=dt.timezone.utc).timestamp())
    assert pub20.fix_name("KXUSDJPY15M", ct) == "NY10"
    # Saturday: never
    ct = int(dt.datetime(2026, 9, 19, 14, 0, tzinfo=dt.timezone.utc).timestamp())
    assert pub20.fix_name("KXUSDJPY15M", ct) is None


def test_reopen_ignores_a_one_hour_break():
    wins = [{"ct": CT + 900 * j} for j in range(10)]
    wins += [{"ct": CT + 900 * 10 + 3600 + 900 * j} for j in range(8)]          # 60 minute break: no gap
    ev = pub20.reopen_events({"S": wins})["S"]
    assert ev == {}
    far = CT + 900 * 10 + 7200                                                    # 2 hour gap between close and next open
    wins2 = [{"ct": CT + 900 * j} for j in range(10)] + [{"ct": far + 900 * j} for j in range(8)]
    ev2 = pub20.reopen_events({"S": wins2})["S"]
    assert sorted(ev2.values()) == [0, 1, 2, 3]


def test_directional_band_and_spread():
    cs = {CT - 180: (0.40, 0.46, 1.0, None), CT - 120: (0.41, 0.47, 1.0, None)}
    assert pub20.directional(cs, CT, "yes", 0.2, 0.8)["fill"] == 0.47
    assert abs(pub20.directional(cs, CT, "no", 0.2, 0.8)["fill"] - 0.59) < 1e-9
    assert pub20.directional(cs, CT, "yes", 0.5, 0.8) is None
    cs[CT - 180] = (0.40, 0.55, 1.0, None)           # spread 0.15
    assert pub20.directional(cs, CT, "yes", 0.2, 0.8) is None


def test_smile_fit_recovers_a_smooth_ladder():
    Ks = [100 + 5 * i for i in range(11)]
    ps = [pub20.PHI(-(K - 125) / 20) for K in Ks]
    for i in range(11):
        assert abs(pub20.fit_leave_one_out(Ks, ps, i) - ps[i]) < 0.02
    ps2 = list(ps); ps2[5] += 0.10                    # one strike off by 10c
    assert pub20.fit_leave_one_out(Ks, ps2, 5) < ps2[5] - 0.07


def p(n, pfv, ex):
    return {"stats": {"n": n, "pf": pfv}, "excess": ex}


def test_verdict_rules():
    ok = p(100, 2.0, 1.0)
    assert pub20.verdict(ok, ok, ok, 200) == "NOT_YET_FALSIFIED"
    assert pub20.verdict(ok, ok, p(100, 1.2, 1.0), 200) == "FALSIFIED"
    assert pub20.verdict(ok, p(100, 1.4, 1.0), None, 200) == "FALSIFIED"
    assert pub20.verdict(ok, p(100, 2.0, -0.1), None, 200) == "FALSIFIED"
    assert pub20.verdict(ok, ok, ok, 149) == "NOT_ENOUGH_DATA"
    assert pub20.verdict(ok, ok, None, 200) == "FALSIFIED"      # W3 only reached when both pass; unread is not a pass


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("ok  ", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
