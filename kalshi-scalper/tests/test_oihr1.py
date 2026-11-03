"""OIHR1 helpers on hand-built ladders. Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import oihr1 as o  # noqa: E402


def ladder(oi_back=100.0, oi_look=120.0, mids_back=(0.97, 0.9, 0.7, 0.5, 0.3, 0.1, 0.04), mids_look=(0.98, 0.95, 0.8, 0.6, 0.35, 0.12, 0.05)):
    ev = {}
    for i, (mb, ml) in enumerate(zip(mids_back, mids_look)):
        k = 100.0 + i
        ev[k] = {o.BACK: (mb - .01, mb + .01, oi_back), o.LOOK: (ml - .01, ml + .01, oi_look),
                 o.FILL: (ml - .01, ml + .01, oi_look)}
    ev[103.0][o.FILL] = (0.59, 0.61, 1)
    return ev


def test_stat():
    assert abs(o.oi_stat(ladder()) - 0.2) < 1e-9
    assert o.oi_stat({k: v for k, v in list(ladder().items())[:3]}) is None      # under 6 strikes
    ev = ladder(); ev[100.0][o.BACK] = (0.8, 0.9, None)
    assert abs(o.oi_stat(ev) - 0.2) < 1e-9 and len(ev) == 7


def test_p90():
    assert o.p90(list(range(1, 11))) == 9 and o.p90(list(range(1, 21))) == 18


def test_centre_lean():
    ev = ladder()
    cb, cl = o.centre(ev, o.BACK), o.centre(ev, o.LOOK)
    assert abs(cb - 103.0) < 1e-9 and 103.0 < cl < 104.0          # mids rose: centre moved up the strike axis
    assert o.lean(ev) == "up"


def test_pick_A_B_and_limit():
    ev = ladder()
    # lean up, centre between 103 and 104: YES on strikes above it. 104 mid .35 (ask .36, over 0.30), 105 ask .13, 106 ask .06 -> 105
    k, side, fill = o.pick(ev, "A")
    assert k == 105.0 and side == "yes" and abs(fill - 0.13) < 1e-9
    # hard limit: fill ask above 0.30 -> None
    ev[105.0][o.FILL] = (0.40, 0.45, 1)
    assert o.pick(ev, "A") is None
    # B: cheaper side of each strike; 104 YES ask .13, 100 NO ask .06, 101 NO ask .21 ... highest within limit is 0.29? (strike 103 YES .36 not in range)
    ev = ladder()
    b = o.pick(ev, "B")
    assert b is not None and b[2] <= 0.30


def test_fee_and_net():
    assert abs(o.net_cents(0.20, True) - (100 - 20 - 0.0 - o.gen6.fee(0.20, 10) * 100)) < 1e-9
    assert o.net_cents(0.20, False) < -20


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("ok")
