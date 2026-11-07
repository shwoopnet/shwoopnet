import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import virt1 as V


def test_split_name():
    assert V.split_name("Chelsea (Zaroth)") == ("Chelsea", "Zaroth")
    assert V.split_name("Khaperskii Iurii") == (None, "Khaperskii Iurii")


def test_cheap_side_spread_guard():
    assert V.cheap_side(0.05, 0.08) == ("yes", 0.08)
    assert V.cheap_side(0.70, 0.72) == ("no", 0.30)
    assert V.cheap_side(0.01, 0.29) is None        # spread 0.28
    assert V.cheap_side(0.40, 0.45) is None


def test_draw_probs_sum_to_one():
    g = dict(sides=[("a", "t", "p"), ("b", "u", "q")], tie="t0")
    for e in (0.1, 0.5, 0.9):
        p = V.probs(g, e, 0.3)
        assert abs(sum(p.values()) - 1) < 1e-12 and min(p.values()) >= 0
    g2 = dict(sides=[("a", "t", "p"), ("b", "u", "q")], tie=None)
    assert V.probs(g2, 0.7, 0)["b"] - 0.3 < 1e-12


def test_rater_draw_and_ready():
    r = V.Rater(32)
    a, b = ("T", "pa"), ("U", "pb")
    for _ in range(8):
        r.update("KXESOCCERGAME", a, b, 1.0)
    assert r.ready("KXESOCCERGAME", a, b) and r.expect("KXESOCCERGAME", a, b) > .5
    before = r.rp[("KXESOCCERGAME", "pa")]
    r.update("KXESOCCERGAME", a, b, 0.5)             # a draw moves the favourite down
    assert r.rp[("KXESOCCERGAME", "pa")] < before


def test_one_per_event_and_verdict():
    rows = [("e1", 5, True, .1, 1, .4, True, "t", "yes"), ("e1", 5, True, .1, 1, .3, True, "u", "yes"), ("e2", -9, False, .1, 1, .05, False, "t", "yes")]
    assert [r[5] for r in V.one_per_event(rows)] == [.4]
    assert V.verdict(rows) == "NOT_ENOUGH_DATA"
