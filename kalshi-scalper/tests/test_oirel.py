"""OIREL evaluator (FALS5 check 2 forward candidate): the relative jump rule on hand-built windows. Research only."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import oirel  # noqa: E402
from scalper.fwdeval import NoData  # noqa: E402

CLOSE = 1_800_000_000


def window(level=100_000.0, doi=30_000.0, sig=(0.80, 0.82, 500.0), fill=(0.17, 0.19, 400.0), series="KXBTC15M", drop=()):
    c = {CLOSE - 360: (0.70, 0.72, 300.0, level),
         CLOSE - 180: (sig[0], sig[1], sig[2], level + doi),
         CLOSE - 120: (fill[0], fill[1], fill[2], level + doi + 10)}
    for d in drop:
        c.pop(CLOSE - d)
    return {"series": series, "ticker": "KXBTC15M-TEST", "close_ts": CLOSE, "result": "no", "candles": c}


def test_fires_above_relative_threshold_no_side_fill_from_next_candle():
    # YES ask 0.82 is not cheap; NO ask = 1 - 0.80 = 0.20 is: NO side, filled at the -120 candle's NO ask 1 - 0.17 = 0.83
    tr = oirel.decide(window(level=100_000, doi=30_000))
    assert tr["side"] == "no" and abs(tr["entry"] - 0.83) < 1e-9 and tr["exit"] is None and tr["t"] == CLOSE - 120
    assert tr["zero_volume"] is False


def test_yes_first_when_both_cheap():
    tr = oirel.decide(window(sig=(0.30, 0.32, 10.0), fill=(0.33, 0.35, 10.0)))
    assert tr["side"] == "yes" and abs(tr["entry"] - 0.35) < 1e-9


def test_strictly_above_and_scales_with_level():
    thr = oirel.RTHR
    assert oirel.decide(window(level=100_000, doi=100_000 * thr)) is None          # equal is not above
    assert oirel.decide(window(level=100_000, doi=100_000 * thr + 1)) is not None
    # the same absolute jump is a signal at a low level and not at a high one
    assert oirel.decide(window(level=200_000, doi=60_000)) is not None
    assert oirel.decide(window(level=400_000, doi=60_000)) is None


def test_no_cheap_side_is_no_trade():
    # YES ask 0.52 and NO ask 1 - 0.48 = 0.52: neither side is in 5c to 50c
    assert oirel.decide(window(sig=(0.48, 0.52, 10.0))) is None


def test_missing_or_zero_oi_is_nodata_not_no_trade():
    for d in (360, 180):
        try:
            oirel.decide(window(drop=(d,)))
            assert False, "expected NoData"
        except NoData:
            pass
    try:
        oirel.decide(window(level=0.0, doi=50_000))
        assert False, "expected NoData"
    except NoData:
        pass
    try:
        oirel.decide(window(drop=(120,)))
        assert False, "expected NoData for a missing fill candle"
    except NoData:
        pass


def test_series_and_params():
    assert oirel.forward_eval(window(series="KXETH15M"), {"series": "KXBTC15M"}) is None
    assert oirel.forward_eval(window(), {"series": "KXBTC15M"}) is not None
    assert oirel.forward_eval(window(level=100_000, doi=30_000), {"series": "KXBTC15M", "rthr": 0.5}) is None


def test_zero_volume_flag():
    tr = oirel.decide(window(sig=(0.80, 0.82, 0.0)))
    assert tr["zero_volume"] is True


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
