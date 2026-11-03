import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import hrseas1 as H


def ts(y, m, d, h):
    return int(datetime.datetime(y, m, d, h, tzinfo=datetime.timezone.utc).timestamp())


def test_fee():
    assert H.fee(0.5, 10) == 0.18 and H.fee(0.1, 10) == 0.07


def test_blocks():
    assert "ASIA_OPEN" in H.block_names(ts(2026, 9, 1, 1)) and "FUNDING" in H.block_names(ts(2026, 9, 1, 0))
    assert "US_OPEN" in H.block_names(ts(2026, 9, 1, 14)) and "WEEKEND" not in H.block_names(ts(2026, 9, 1, 14))
    assert "WEEKEND" in H.block_names(ts(2026, 9, 5, 14))   # a Saturday
    assert H.block_names(ts(2026, 9, 1, 11)) == []


def test_pick_tail_nearest_money_and_limit():
    look = [("a", 0.20, 0.25), ("b", 0.10, 0.12), ("c", 0.80, 0.85), ("d", 0.90, 0.95), ("e", 0.4, 0.45)]
    got = dict((s, t) for t, s in H.pick(look, "tail"))
    assert got["yes"] == "a"
    assert got["no"] == "c"   # 1-0.80 = 0.20 is the highest NO price under 0.30


def test_pick_fav():
    look = [("a", 0.88, 0.90), ("b", 0.95, 0.96), ("c", 0.05, 0.08)]
    got = dict((s, t) for t, s in H.pick(look, "fav"))
    assert got["yes"] == "a" and got["no"] == "c"   # NO price 0.95 is nearest 0.90 vs 0.92? c: 1-0.05=0.95; only c
    assert H.pick([("x", 0.4, 0.5)], "fav") == []


def test_fill_limit_and_pnl():
    assert H.fill_and_pnl("yes", (0.3, 0.35), "yes", "tail") is None     # above the hard limit
    p, pn, won = H.fill_and_pnl("yes", (0.1, 0.2), "yes", "tail")
    assert won and abs(pn - (10 - 2 - H.fee(0.2, 10))) < 1e-9
    p, pn, won = H.fill_and_pnl("no", (0.8, 0.9), "no", "tail")           # NO price 0.2
    assert abs(p - 0.2) < 1e-9 and won
    assert H.fill_and_pnl("yes", None, "yes", "tail") is None


def test_verdict_rules():
    good = {"n": 60, "pf": 1.6}
    assert H.verdict("b", "tail", good, good, 0.01, 0.02).startswith("NOT_ENOUGH_DATA")
    big = {"n": 90, "pf": 1.6}
    assert H.verdict("b", "tail", big, big, 0.01, 0.02).startswith("PASS")
    assert H.verdict("b", "tail", big, big, 0.01, -0.02) == "FALSIFIED"
    assert H.verdict("b", "tail", {"n": 90, "pf": 1.2}, big, 0.01, 0.02) == "FALSIFIED"


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("hrseas1 tests ok")
