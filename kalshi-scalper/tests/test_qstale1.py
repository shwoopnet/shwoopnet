"""QSTALE1 helpers on hand-built candles (candle = (bid, ask, volume, oi)). Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import qstale1 as q  # noqa: E402

CT = 1_800_000_000


def cs_mid(mids, vols=(1, 1, 1), spread=0.02):
    """mids for the candles ending 360, 300, 240, 180 s before the close."""
    c = {}
    for k, (e, m) in enumerate(zip((360, 300, 240, 180), mids)):
        v = 0 if k == 0 else vols[k - 1]
        c[CT - e] = (m - spread / 2, m + spread / 2, float(v), 1.0)
    return c


def test_path_vol():
    p, v, lit = q.path_vol(cs_mid([0.40, 0.41, 0.42, 0.40]), CT)
    assert abs(p - 0.04) < 1e-9 and v is True and lit is False
    p, v, lit = q.path_vol(cs_mid([0.40, 0.405, 0.40, 0.405]), CT)
    assert lit is True and abs(p - 0.015) < 1e-9
    assert q.path_vol(cs_mid([0.40, 0.40, 0.40, 0.40], vols=(0, 0, 0)), CT)[1] is False


def test_missing_candle_not_eligible():
    c = cs_mid([0.4, 0.4, 0.4, 0.4]); del c[CT - 240]
    assert q.path_vol(c, CT) is None
    c = cs_mid([0.4, 0.4, 0.4, 0.4]); c[CT - 300] = (None, 0.4, 1.0, 1.0)
    assert q.path_vol(c, CT) is None


def test_trailing_q_strictly_before_look_and_min():
    ts = list(range(1000, 1000 + 400 * 60, 60)); sp = [0.01] * 399 + [0.05]
    import numpy as np
    look = ts[-1]                       # the last (wide) candle is the look itself and is excluded
    assert q.trailing_q(ts, np.array(sp), look) == 0.01
    assert q.trailing_q(ts[:100], np.array(sp[:100]), ts[99]) is None        # under 300 values


def test_cheap_trade_and_fill():
    c = {CT - 180: (0.70, 0.72, 1.0, 1.0), CT - 120: (0.68, 0.71, 1.0, 1.0)}
    t = q.cheap_trade(c, CT)                       # YES ask 0.72 out of band, NO ask 1-0.70=0.30 in band
    assert t["side"] == "no" and abs(t["sig_ask"] - 0.30) < 1e-9 and abs(t["fill"] - 0.32) < 1e-9
    c = {CT - 180: (0.30, 0.32, 1.0, 1.0), CT - 120: (0.30, 0.34, 1.0, 1.0)}
    t = q.cheap_trade(c, CT)
    assert t["side"] == "yes" and abs(t["fill"] - 0.34) < 1e-9
    assert q.cheap_trade({CT - 180: (0.30, 0.32, 1, 1)}, CT) is None          # no fill candle
    assert q.cheap_trade({CT - 180: (0.48, 0.52, 1, 1), CT - 120: (0.48, 0.52, 1, 1)}, CT) is None   # both asks 52c


def test_net10_and_worst_loss():
    assert abs(q.net10(0.30, False) - -(3.0 + 0.15)) < 1e-9        # fee ceil(0.07*10*.21*100)=15c
    assert abs(q.net10(0.30, True) - (7.0 - 0.15)) < 1e-9
    assert abs(q.net10(0.50, False) - -(5.0 + 0.18)) < 1e-9        # 10 contracts at the cap: $5.18


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1
    print(f"test_qstale1: {n} passed")
