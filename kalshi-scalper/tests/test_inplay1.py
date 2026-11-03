import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scalper import inplay1 as s


def q(a, w=0.01):
    return (a - w, a)


def test_fee():
    assert s.fee(0.05) == 0.04 and s.fee(0.30) == 0.15


def test_trade_when_ratio_met():
    L = 3600
    rows = [(0, 0.5, 0.0), (L - 300, 0.40, 0.0)]  # home 0.40, away 0.60
    ca, cb = {L: q(0.12)}, {L: q(0.90)}
    t, c = s.scan_game(0, rows, ca, cb, True)
    assert t and abs(t["ask"] - 0.12) < 1e-9 and t["win"] is True and len(c) == 1


def test_no_trade_below_ratio():
    L = 3600
    rows = [(L - 300, 0.30, 0.0)]
    t, c = s.scan_game(0, rows, {L: q(0.12)}, {L: q(0.90)}, False)
    assert t is None and len(c) == 1  # 0.30 < 3 * 0.12


def test_stale_or_future_row_ignored():
    L = 3600
    t, c = s.scan_game(0, [(L - 100, 0.9, 0.0)], {L: q(0.10)}, {L: q(0.9)}, True)
    assert t is None and not c  # row after L-D is not visible


def test_away_probability_and_tie():
    L = 5400
    rows = [(L - 250, 0.8, 0.05)]  # away 0.15
    t, _ = s.scan_game(0, rows, {L: q(0.9)}, {L: q(0.04)}, False)
    assert t and t["win"] is True and abs(t["pe"] - 0.15) < 1e-9


def test_one_per_game_earliest_look():
    rows = [(3000, 0.5, 0), (5000, 0.5, 0)]
    ca = {3600: q(0.1), 5400: q(0.1)}
    t, c = s.scan_game(0, rows, ca, {}, True)
    assert t["k"] == 3600 and len(c) == 2


def test_band_and_pf():
    assert s.band(0.03) == 0 and s.band(0.30) == 4
    assert s.pf([1, -1]) == 1.0


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("ok")
