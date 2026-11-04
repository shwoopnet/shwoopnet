import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import nflftd1 as n  # noqa: E402


def test_fee_net():
    assert n.fee(0.10) == math.ceil(0.07 * 10 * 0.09 * 100) / 100 / 10 * 1.0 or abs(n.fee(0.10) - 0.0063) < 1e-9
    assert n.net(False, 0.10) < -0.10
    assert abs(n.net(True, 0.10) - (0.9 - n.fee(0.10))) < 1e-12


def test_split_thirds():
    fit, test = n.split_thirds([str(i) for i in range(9)])
    assert len(fit) == 6 and test == ["6", "7", "8"]


def test_pick_two():
    rows = [dict(ticker=f"T{i}", ratio=r, ask=a) for i, (r, a) in enumerate([(5, .05), (4, .06), (3.5, .07), (2.9, .05), (9, .35)])]
    t = n.pick_two(rows, True)
    assert [r["ticker"] for r in t] == ["T0", "T1"]
    assert all(r["ask"] <= 0.30 for r in t)
    assert len(n.pick_two(rows, False)) == 2
