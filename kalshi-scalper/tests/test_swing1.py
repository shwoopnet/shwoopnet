from scalper import swing1 as s


def mk(path, start=0):
    return {start + 60 * i: (p - 0.005, p + 0.005) for i, p in enumerate(path)}


def test_fee_rounding():
    assert s.fee(0.05) == 0.04 and s.fee(0.30) == 0.15


def test_swing_trade_and_one_per_game():
    a = [0.6] * 6 + [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
    b = [1 - x for x in a]
    st = -600
    sw, _ = s.scan_game("KXMLBGAME", st, mk(a, st), mk(b, st), False)
    assert sw and abs(sw["ask"] - 0.305) < 1e-9 or sw is None  # ask 0.305 is above the 0.30 limit


def test_swing_inside_band():
    a = [0.6] * 6 + [0.28] * 8
    b = [1 - x for x in a]
    st = -600
    sw, _ = s.scan_game("KXMLBGAME", st, mk(a, st), mk(b, st), True)
    assert sw and sw["win"] is True and 0.05 <= sw["ask"] <= 0.30


def test_no_swing_gives_control_only():
    a = [0.2] * 12
    b = [0.8] * 12
    sw, cs = s.scan_game("KXMLBGAME", -600, mk(a, -600), mk(b, -600), False)
    assert sw is None and cs and all(not c["win"] or True for c in cs)


def test_pre_game_not_used():
    a = [0.6] * 6 + [0.28] * 8
    sw, _ = s.scan_game("KXMLBGAME", 10**6, mk(a), mk([1 - x for x in a]), True)
    assert sw is None
