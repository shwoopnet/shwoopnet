import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import esportm1 as E


def mk(series, ev, a, b, close):
    return {f"{ev}-{a}": dict(ticker=f"{ev}-{a}", event_ticker=ev, close_time=close, yes_sub_title=a, series=series, src="live"),
            f"{ev}-{b}": dict(ticker=f"{ev}-{b}", event_ticker=ev, close_time=close, yes_sub_title=b, series=series, src="live")}


def test_parse_start_is_eastern():
    st = E.parse_start("KXLOLGAME-26SEP031330DV1LDS")
    assert st == 1788456600 or abs(st - 1788456600) < 4 * 3600  # 13:30 EDT = 17:30Z
    from datetime import datetime, timezone
    assert datetime.fromtimestamp(st, timezone.utc).hour == 17
    assert E.parse_start("KXLOLGAME-garbage") is None


def test_elo_and_ready():
    e = E.Elo(24)
    assert abs(e.prob("a", "b") - .5) < 1e-12
    for _ in range(8):
        e.update("a", "b")
    assert e.ready("a", "b") and e.prob("a", "b") > .5 and not e.ready("a", "c")


def test_fee_cheap_side_and_net():
    assert E.cheap_side(0.05, 0.08) == ("yes", 0.08)
    assert E.cheap_side(0.70, 0.75)[0] == "no"       # NO ask = 1 - 0.70 = 0.30 is the cheap side
    assert E.cheap_side(0.40, 0.45) is None
    assert E.treated(0.30, 0.10) and not E.treated(0.29, 0.10) and not E.treated(0.9, 0.31)
    assert E.net_cents(0.10, True) > 80 and E.net_cents(0.10, False) < -10


def test_qualified_uses_only_matches_closed_before_look():
    ms = {}
    for i in range(9):
        ms |= mk("KXCS2GAME", f"KXCS2GAME-26SEP{i+1:02d}1000AAABBB", "AAA", "BBB", f"2026-09-{i+1:02d}T15:00:00Z")
    # a tenth event whose look is BEFORE the ninth match closed: team not ready by close order at that look
    ms |= mk("KXCS2GAME", "KXCS2GAME-26SEP101000AAABBB", "AAA", "BBB", "2026-09-10T15:00:00Z")
    ms |= mk("KXCS2GAME", "KXCS2GAME-26SEP021100AAABBB", "AAA", "BBB", "2026-09-02T16:00:00Z")
    g = E.group(ms)
    q = E.qualified(g)
    assert "KXCS2GAME-26SEP101000AAABBB" in q and "KXCS2GAME-26SEP021100AAABBB" not in q


def test_frozen_cut_excluded():
    ms = {}
    for i in range(9):
        ms |= mk("KXLOLGAME", f"KXLOLGAME-26SEP{i+1:02d}1000XXXYYY", "XXX", "YYY", f"2026-09-{i+1:02d}T15:00:00Z")
    ms |= mk("KXLOLGAME", "KXLOLGAME-26OCT051000XXXYYY", "XXX", "YYY", "2026-10-05T15:00:00Z")
    assert "KXLOLGAME-26OCT051000XXXYYY" not in E.qualified(E.group(ms))


def test_md5_order_is_stable():
    assert E.md5_key("a") == E.md5_key("a") != E.md5_key("b")


def test_verdict():
    rows = [("e", 5.0, True, .1, i % 2 * 200, .3, True, 1) for i in range(160)]
    assert E.verdict(rows, 100, 5.0) == "NOT_YET_FALSIFIED"
    assert E.verdict(rows[:10], 100, 5.0) == "NOT_ENOUGH_DATA"
    bad = [("e", -3.0, False, .1, i % 2 * 200, .3, True, 1) for i in range(160)]
    assert E.verdict(bad, 100, -3.0) == "FALSIFIED"
