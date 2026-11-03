"""XOI1 helpers on hand-built candles (candle = (bid, ask, volume, oi)). Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import xoi1  # noqa: E402

CT = 1_800_000_000


def btc(level=100_000.0, doi=30_000.0, m0=0.50, m1=0.55):
    return {CT - 360: (m0 - .01, m0 + .01, 10.0, level), CT - 180: (m1 - .01, m1 + .01, 10.0, level + doi)}


def alt(sig=(0.78, 0.82), fill=(0.80, 0.84), vol=5.0):
    c = {CT - 120: (fill[0], fill[1], 3.0, 1.0), CT - 180: (sig[0], sig[1], vol, 1.0)}
    for j in range(1, 5):
        c[CT - 180 - 60 * j] = (0.5, 0.52, vol, 1.0)
    return c


def test_trigger_relative():
    assert xoi1.btc_trigger(btc(doi=30_000), CT) is True
    assert xoi1.btc_trigger(btc(doi=20_000), CT) is False       # 20% < 26.76%
    assert xoi1.btc_trigger(btc(doi=26_764.0), CT) is False and xoi1.btc_trigger(btc(doi=26_765.0), CT) is True
    c = btc(); c[CT - 360] = (0.4, 0.5, 1.0, None)
    assert xoi1.btc_trigger(c, CT) is None                       # missing oi: not eligible, not "no jump"
    c = btc(); del c[CT - 180]
    assert xoi1.btc_trigger(c, CT) is None


def test_cheap_side_and_fill():
    t = xoi1.alt_trade(alt(), CT)
    # YES ask 0.82 not cheap; NO ask = 1 - 0.78 = 0.22 is; fill at the -120 candle's NO ask = 1 - 0.80 = 0.20
    assert t["side"] == "no" and abs(t["fill"] - 0.20) < 1e-9 and abs(t["sig_ask"] - 0.22) < 1e-9
    t = xoi1.alt_trade(alt(sig=(0.28, 0.30), fill=(0.31, 0.33)), CT)
    assert t["side"] == "yes" and abs(t["fill"] - 0.33) < 1e-9     # YES first when it is the cheap side


def test_no_trade_cases():
    assert xoi1.alt_trade(alt(sig=(0.44, 0.46)), CT)["side"] == "yes"   # both sides near 50: YES first
    assert xoi1.alt_trade(alt(sig=(0.60, 0.62)), CT)["side"] == "no"     # NO ask 0.40
    assert xoi1.alt_trade(alt(sig=(0.01, 0.03), fill=(0.01, 0.03)), CT) is None   # YES ask 0.03 too cheap, NO ask 0.99
    assert xoi1.alt_trade(alt(sig=(0.96, 0.98), fill=(0.96, 0.98)), CT) is None   # NO ask 0.04 < 0.05, YES 0.98
    assert xoi1.alt_trade(alt(vol=1.0), CT) is None                 # 5 candles x 1 = 5 < 10 contracts
    assert xoi1.alt_trade(alt(vol=2.0), CT) is not None             # 10 contracts: eligible
    c = alt(); del c[CT - 120]
    assert xoi1.alt_trade(c, CT) is None                             # no fill candle


def test_fee_and_net():
    # win at 0.20: 10 * (1 - 0.20 - fee); fee = ceil(0.07*10*0.2*0.8*100)/100/10 = 0.12/10
    assert abs(xoi1.net10(0.20, True) - (10 * (0.80 - 0.012))) < 1e-9
    assert abs(xoi1.net10(0.20, False) - (-10 * (0.20 + 0.012))) < 1e-9


def test_direction_and_stats():
    assert abs(xoi1.btc_move(btc(m0=0.5, m1=0.6), CT) - 0.10) < 1e-9
    T = [{"fill": 0.20, "win": w, "day": "d%d" % (i % 3)} for i, w in enumerate([1, 0, 0, 0, 0, 1, 0, 0, 0, 0])]
    s = xoi1.stats(T)
    assert s["n"] == 10 and abs(s["win"] - 0.2) < 1e-9 and s["payoff"] > 3.5 and s["pf"] > 0


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("ok  ", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
