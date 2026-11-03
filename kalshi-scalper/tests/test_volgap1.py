import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from statistics import NormalDist
from scalper import volgap1 as V

CLOSE = 1_800_000_000 - (1_800_000_000 % 3600)
LOOK = CLOSE - V.LOOK_S
ND = NormalDist()


def klines(per_min_vol, base=100.0):
    """alternating +/- moves of exactly per_min_vol in log terms: RMS of the 15 returns is per_min_vol."""
    out = {}
    ts = [LOOK - 60 - 60 * (15 - i) for i in range(16)]
    for i, t in enumerate(ts):
        out[t] = base * math.exp(per_min_vol * (i % 2))
    return out


def ladder(m, s, strikes, look_vol_ok=True):
    """candles for a lognormal ladder (log-median m, total std s) with a 1c spread, plus the fill candle one minute later."""
    cands, res = {}, {}
    for K in strikes:
        mid = 1 - ND.cdf((math.log(K) - m) / s)
        bid, ask = round(max(0.01, mid - 0.005), 3), round(min(0.99, mid + 0.005), 3)
        tk = f"T{K}"
        cands[tk] = [(LOOK, bid, ask, 5.0), (LOOK + 60, bid, ask, 5.0)]
        res[tk] = "yes" if mid > 0.5 else "no"
    return cands, res


def test_realised_per_min():
    assert abs(V.realised_per_min([100 * math.exp(0.001 * (i % 2)) for i in range(16)]) - 0.001) < 1e-9
    assert V.realised_per_min([100.0] * 16) is None
    assert V.realised_per_min([100.0] * 15) is None
    assert V.realised_per_min([100.0] * 15 + [None]) is None


def test_fit_recovers_a_lognormal_ladder():
    m, s = math.log(100.0), 0.01
    pts = []
    for k in [97, 98, 98.5, 99, 99.5, 100, 100.5, 101, 101.5, 102, 103]:
        pts.append((k, 1 - ND.cdf((math.log(k) - m) / s)))
    f = V.fit_ladder(pts)
    assert f is not None
    assert abs(f[0] - m) < 1e-6 and abs(f[1] - s) < 1e-6 and f[2] > 0.999999


def test_fit_refuses_thin_or_nonmonotone():
    assert V.fit_ladder([(99, 0.6), (100, 0.5), (101, 0.4)]) is None
    bad = [(90 + i, 0.5 + (0.1 if i % 2 else -0.1)) for i in range(10)]
    assert V.fit_ladder(bad) is None


def test_model_probability_is_monotone_and_half_at_the_median():
    m, s = math.log(100.0), 0.01
    assert abs(V.p_yes_model(100.0, m, s) - 0.5) < 1e-12
    assert V.p_yes_model(99.0, m, s) > V.p_yes_model(101.0, m, s)


def test_ratio_and_trigger_with_high_realised_vol():
    m, s = math.log(100.0), 0.01
    strikes = [98 + 0.25 * i for i in range(17)]            # 98 .. 102
    c, res = ladder(m, s, strikes)
    st = [(f"T{K}", K) for K in strikes]
    sr = s / math.sqrt(V.TAU_MIN) * 2.0                      # realised is twice implied
    h = V.decide_hour(CLOSE, st, c, klines(sr))
    assert h is not None and abs(h["ratio"] - 2.0) < 0.02
    assert h["best"] is not None and h["best"]["e"] >= V.EDGE
    p = h["best"]["price"]
    assert p is None or (V.TAIL[0] <= p <= V.TAIL[1])


def test_equal_vol_gives_no_model_trade():
    m, s = math.log(100.0), 0.01
    strikes = [98 + 0.25 * i for i in range(17)]
    c, _ = ladder(m, s, strikes)
    st = [(f"T{K}", K) for K in strikes]
    h = V.decide_hour(CLOSE, st, c, klines(s / math.sqrt(V.TAU_MIN)))
    assert abs(h["ratio"] - 1.0) < 0.02
    assert h["best"] is None                                   # a fair ladder offers no 8c edge after the fee


def test_hard_cap_blocks_a_fill_above_the_cap_or_slip():
    cs = [(LOOK, 0.20, 0.25, 1.0), (LOOK + 60, 0.30, 0.33, 1.0)]
    assert V.resolve_fill(cs, LOOK, "yes", 0.25) is None        # 0.33 above the 0.30 cap
    cs = [(LOOK, 0.20, 0.25, 1.0), (LOOK + 60, 0.24, 0.27, 1.0)]
    assert V.resolve_fill(cs, LOOK, "yes", 0.25) is not None and abs(V.resolve_fill(cs, LOOK, "yes", 0.25) - 0.27) < 1e-12
    cs = [(LOOK, 0.10, 0.12, 1.0), (LOOK + 60, 0.14, 0.16, 1.0)]
    assert V.resolve_fill(cs, LOOK, "yes", 0.12) is None        # 4c above the look price, slip limit 3c
    cs = [(LOOK, 0.10, 0.12, 1.0)]
    assert V.resolve_fill(cs, LOOK, "yes", 0.12) is None        # no fill candle
    cs = [(LOOK, 0.80, 0.82, 1.0), (LOOK + 60, 0.80, 0.82, 1.0)]
    assert V.resolve_fill(cs, LOOK, "no", 0.20) is not None and abs(V.resolve_fill(cs, LOOK, "no", 0.20) - 0.20) < 1e-12


def test_look_ignores_candles_after_the_look_and_stale_ones():
    cs = [(LOOK + 60, 0.4, 0.45, 1.0)]
    assert V.look_quote(cs, LOOK) is None
    cs = [(LOOK - 300, 0.4, 0.45, 1.0)]
    assert V.look_quote(cs, LOOK) is None
    cs = [(LOOK - 60, 0.4, 0.45, 1.0), (LOOK, 0.41, 0.46, 1.0)]
    assert V.look_quote(cs, LOOK)[0] == LOOK
    assert V.look_quote([(LOOK, 0.4, 0.50, 1.0)], LOOK) is None   # spread 10c


def test_pnl_uses_the_rounded_up_fee():
    from scalper import lag15 as L
    assert abs(L.pnl("yes", 0.10, "yes") - (100 - 10 - 0.7)) < 1e-9   # 0.07*10*.09 = 0.063 -> 7c / 10 = 0.7c
    assert abs(L.pnl("yes", 0.10, "no") - (-10 - 0.7)) < 1e-9


if __name__ == "__main__":
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith("test_"):
            f(); n += 1; print("ok", k)
    print(n, "tests passed")
