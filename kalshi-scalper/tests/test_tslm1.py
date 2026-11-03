"""TSLM1 helpers on hand-built candles (candle = (bid, ask, volume, oi)). Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import tslm1  # noqa: E402

CT = 1_800_000_000


def mk(mids):
    """mids: {seconds before close: mid}; candle with a 2c spread."""
    return {CT - s: (m - .01, m + .01, 5.0, 1.0) for s, m in mids.items()}


def base(early_jump_at=None, late_jump_at=None):
    mids = {}
    m = 0.30
    for s in range(900, 100, -60):
        if s == early_jump_at:
            m += 0.10
        if s == late_jump_at:
            m += 0.10
        mids[s] = m
    return mk(mids)


def test_change_at_and_missing():
    cs = base()
    assert abs(tslm1.change_at(cs, CT - 600)) < 1e-9
    del cs[CT - 660]
    assert tslm1.change_at(cs, CT - 600) is None and tslm1.change_at(cs, CT - 660) is None
    cs = {CT - 60: (0.0, 1.5, 1, 1), CT - 120: (0.4, 0.5, 1, 1)}
    assert tslm1.change_at(cs, CT - 60) is None            # not a valid two sided quote


def test_thresholds_trailing_only():
    ends = list(range(0, 2000 * 60, 60)); vals = [0.01] * 2000
    ends_a = np_arr = None
    import numpy as np
    v = np.array(vals); v[1500] = 0.5
    assert tslm1.thresholds(ends, v, 100 * 60) is None                 # under MIN_TRAIL changes before that open
    p95, med = tslm1.thresholds(ends, v, 1900 * 60)
    assert abs(med - 0.01) < 1e-9 and abs(p95 - 0.01) < 1e-9
    p95b, _ = tslm1.thresholds(ends, v, 1400 * 60)                      # spike at index 1500 is in the future: not seen
    assert abs(p95b - 0.01) < 1e-9


def test_primary_shock_then_calm():
    cs = base(early_jump_at=600)               # +0.10 in the change ending 600 s before the close, flat afterwards
    p, l, ok = tslm1.classify(cs, CT, 0.05, 0.0)
    assert ok and p and not l
    cs = base(early_jump_at=600, late_jump_at=240)    # a second move inside the calm window kills the primary
    p, l, ok = tslm1.classify(cs, CT, 0.05, 0.0)
    assert ok and not p and not l
    p, l, ok = tslm1.classify(base(), CT, 0.05, 0.0)    # nothing big at all
    assert ok and not p and not l


def test_shock_outside_first_nine_minutes_does_not_count():
    cs = base(early_jump_at=300)              # change ending 300 s before the close is a last 3 minute change
    p, l, ok = tslm1.classify(cs, CT, 0.05, 0.0)
    assert ok and not p and l                 # calm first, then a late shock: the alternative


def test_calm_uses_median_strictly():
    cs = base(early_jump_at=600)
    for s in (300, 240, 180):                 # a 0.5c wiggle in the calm window with median 0.2c breaks calm
        pass
    cs[CT - 240] = (0.39, 0.41, 5.0, 1.0)      # mid 0.40 vs 0.40 before: still flat
    cs[CT - 180] = (0.395, 0.425, 5.0, 1.0)    # mid 0.41: change 0.01
    p, l, ok = tslm1.classify(cs, CT, 0.05, 0.005)
    assert ok and not p
    p, l, ok = tslm1.classify(cs, CT, 0.05, 0.0101)
    assert ok and p


def test_missing_calm_candle_is_not_eligible():
    cs = base(early_jump_at=600); del cs[CT - 240]
    assert tslm1.classify(cs, CT, 0.05, 0.0) == (False, False, False)


def test_late_needs_seven_early_changes():
    cs = base(late_jump_at=240)
    assert tslm1.classify(cs, CT, 0.05, 0.0)[1] is True
    for s in (840, 780, 720, 660):
        del cs[CT - s]
    assert tslm1.classify(cs, CT, 0.05, 0.0)[1] is False


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("ok  ", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
