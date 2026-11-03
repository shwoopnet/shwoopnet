import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import idxfut1 as I

CLOSE = 1_800_000_000 - (1_800_000_000 % 3600)


def bars(L, step, base=100.0, n=100):
    """alternating +/-step log moves for the last n minutes before close; keys are bar starts."""
    out = {}
    for i in range(n):
        t = CLOSE - 60 * (n - i)
        out[t] = base * math.exp(step * (i % 2))
    return out


def test_ref_state_rms_and_scale():
    b = bars(30, 0.0002)
    yb = {CLOSE - I.SCALE_LEAD - 300: 1000.0}
    S, sig = I.ref_state(b, yb, CLOSE, 30)
    assert abs(sig - 0.0002) < 1e-6
    r0 = b[CLOSE - I.SCALE_LEAD - 60]
    assert abs(S - b[CLOSE - 30 * 60 - 60] * 1000.0 / r0) < 1e-9


def test_ref_state_needs_returns():
    b = {k: v for k, v in bars(30, 0.0002).items() if k % 120 == 0}
    assert I.ref_state(b, {CLOSE - I.SCALE_LEAD - 300: 1000.0}, CLOSE, 30) is None


def test_cands_and_ratio_rule():
    S, sig, L = 100.0, 0.0002, 30
    sd = sig * math.sqrt(L)
    k_far = 100.0 * math.exp(1.5 * sd)           # model p(above) = 1 - Phi(1.5) = 0.0668
    k_mid = 100.0 * math.exp(0.5 * sd)           # p = 0.3085
    qs = [("far", k_far, "no", 0.01, 0.03), ("mid", k_mid, "yes", 0.27, 0.29)]
    cs = I.cands_at(S, sig, L, qs)
    far = [c for c in cs if c["ticker"] == "far" and c["side"] == "yes"][0]
    assert abs(far["mp"] - 0.0668) < 1e-3 and far["price"] == 0.03
    mid_yes = [c for c in cs if c["ticker"] == "mid" and c["side"] == "yes"][0]
    assert mid_yes["won"] is True
    # far YES: 0.0668/0.03 = 2.2 (out); mid YES: 0.3085/0.29 = 1.06 (out); no treated pick
    assert I.pick_treated(cs) is None
    k_hi = 100.0 * math.exp(-1.0 * sd)           # p(above) = 0.8413; its NO side costs 0.04 -> 0.1587 / 0.04 = 4
    t = I.pick_treated(I.cands_at(S, sig, L, [("hi", k_hi, "yes", 0.96, 0.98)]))
    assert t is not None and t["side"] == "no" and t["price"] == 0.04 and t["mp"] >= 3 * t["price"]


def test_hard_limit_and_two_sided():
    cs = I.cands_at(100.0, 0.0002, 30, [("x", 100.0, "yes", 0.0, 0.2), ("y", 100.0, "yes", 0.5, 1.0), ("z", 100, "yes", 0.2, 0.35)])
    assert all(c["price"] <= 0.30 for c in cs)
    assert not any(c["ticker"] in ("x", "y") for c in cs)


def test_control_nearest_10c_and_fee():
    cs = [dict(price=0.05), dict(price=0.12), dict(price=0.25)]
    assert I.pick_control(cs)["price"] == 0.12
    # fee 7% * 10 * .1 * .9 = 0.063 -> 7c; a loss costs 1.00 + .07
    assert abs(I.pnl(dict(price=0.10, won=False)) - (-1.07)) < 1e-9
    assert abs(I.pnl(dict(price=0.10, won=True)) - (9.0 - 0.07)) < 1e-9


def test_windows_equal_thirds():
    days = [f"2026-09-{d:02d}" for d in range(1, 10)]
    w, a, b = I.split(days)
    assert [w(d) for d in days] == ["W1"] * 3 + ["W2"] * 3 + ["W3"] * 3


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("idxfut1 tests ok")
