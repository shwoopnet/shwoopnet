import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import cric1 as C


def mk(date, a, b, win, xi_a=("a1",), xi_b=("b1",), toss=None):
    return dict(id=date + a + b, date=date, pool="T20", gender="male", teams=(a, b), xi=(list(xi_a), list(xi_b)), toss=toss, winner=win, ev="")


def test_walk_forward_same_day_not_used():
    ms = [mk("2025-01-01", "A", "B", "A"), mk("2025-01-01", "A", "B", "B"), mk("2025-01-02", "A", "B", "A")]
    e = C.Engine(1.0, 0.5, 0.0)
    rec = C.walk(ms, e, lambda m: True)
    assert abs(rec[0][2] - 0.5) < 1e-12 and abs(rec[1][2] - 0.5) < 1e-12   # both of day 1 saw fresh ratings
    assert rec[2][2] != 0.5


def test_toss_sign_and_symmetry():
    e = C.Engine(1.0, 0.0, 0.1)
    m = mk("2025-01-01", "A", "B", None, toss="A")
    assert e.predict(m) > 0.5
    m["toss"] = "B"
    assert e.predict(m) < 0.5


def test_fee_and_net():
    assert C.fee(0.10) == 0.07  # 0.07*10*0.1*0.9 = 0.063 rounds up to 0.07
    w, w12 = C.net_cents(0.10, True)
    assert abs(w - ((10 * 0.9 - 0.07) / 10 * 100)) < 1e-9
    l, _ = C.net_cents(0.10, False)
    assert l < -10


def test_look_window_and_stale():
    start = 100000
    cs = [(start - 1700, 0.4, 0.5), (start - 2000, 0.3, 0.35), (start - 20000, 0.3, 0.35)]
    q = C.look(cs, start)
    assert q == (2000, 0.3, 0.35)
    assert C.look([(start - 20000, 0.3, 0.35)], start) is None


def test_event_start_is_eastern():
    day, st = C.event_start("KXT20MATCH-26JUN070930NOREAG")
    assert st == 1780839000  # 2026-06-07 09:30 EDT = 13:30Z
    assert C.event_start("KXT20MATCH-26FEB12NAMIND")[1] is None
