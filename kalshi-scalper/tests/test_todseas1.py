"""TODSEAS1 helpers on hand-built windows. Research only. Plain runner."""
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import todseas1 as T  # noqa: E402

ET, LON = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")


def ts(tz, y, m, d, hh, mm):
    return int(datetime(y, m, d, hh, mm, tzinfo=tz).timestamp())


def test_slot_clock_follows_zone_rules():
    # Tue 2026-10-20 (UK summer time, US summer time): 07:00 London = 06:00 UTC; Tue 2026-10-27 (UK back, US not yet): 07:00 London = 07:00 UTC
    assert T.slot_of("KXSILVER15M", ts(LON, 2026, 10, 20, 7, 0)) == "S6"
    assert T.slot_of("KXSILVER15M", ts(LON, 2026, 10, 27, 7, 0)) == "S6"
    assert T.slot_of("KXSILVER15M", ts(LON, 2026, 10, 27, 7, 0) + 3600) is None
    assert T.slot_of("KXSILVER15M", ts(ET, 2026, 11, 3, 12, 0)) == "S9"


def test_weekday_and_series_limits():
    assert T.slot_of("KXSILVER15M", ts(ET, 2026, 10, 15, 17, 0)) == "S1"       # Thursday
    assert T.slot_of("KXSILVER15M", ts(ET, 2026, 10, 16, 17, 0)) is None       # Friday: no S1 (P03 covers Fridays)
    assert T.slot_of("KXEURUSD15M", ts(ET, 2026, 10, 15, 17, 0)) == "S3"
    assert T.slot_of("KXEURUSD15M", ts(ET, 2026, 10, 15, 18, 15)) is None      # S2 is commodities only
    assert T.slot_of("KXSILVER15M", ts(ET, 2026, 10, 18, 18, 15)) is None      # Sunday reopen belongs to P10
    assert T.slot_of("KXSILVER15M", ts(ET, 2026, 10, 19, 18, 15)) == "S2"


def test_hard_limit_030():
    ct = 1_800_000_000 // 900 * 900
    cs = {ct - 180: (0.20, 0.24, 5, 1), ct - 120: (0.26, 0.30, 5, 1)}
    why, t = T.window_trade(cs, ct)
    assert why == "trade" and abs(t["fill"] - 0.30) < 1e-9
    cs[ct - 120] = (0.27, 0.31, 5, 1)
    why, t = T.window_trade(cs, ct)
    assert why == "limit" and t is None
    cs = {ct - 180: (0.40, 0.44, 5, 1), ct - 120: (0.40, 0.44, 5, 1)}            # YES ask 0.44, NO ask 0.60: nothing cheap enough
    assert T.window_trade(cs, ct)[0] == "nocheap"


def test_worst_loss():
    assert abs(T.worst_loss_dollars(10) - 3.15) < 1e-9


def test_halt_hour():
    assert T.in_halt_hour(ts(ET, 2026, 10, 15, 17, 30)) and T.in_halt_hour(ts(ET, 2026, 10, 15, 18, 0))
    assert not T.in_halt_hour(ts(ET, 2026, 10, 15, 17, 0)) and not T.in_halt_hour(ts(ET, 2026, 10, 15, 18, 15))


def test_control_uses_neighbours_only_and_excludes_halt_hour():
    ct = ts(ET, 2026, 10, 15, 17, 0)
    mk = lambda c, win: {"series": "KXSILVER15M", "ct": c, "tr": {"fill": 0.2, "side": "yes"}, "win": win, "slot": None, "ev": False, "day": "d"}
    pool = {("KXSILVER15M", ct + 1800): mk(ct + 1800, True), ("KXSILVER15M", ct - 1800): mk(ct - 1800, False),
            ("KXSILVER15M", ct + 7200): mk(ct + 7200, True)}
    t = {"series": "KXSILVER15M", "ct": ct}
    cm = T.control_mean(t, pool, {}, "S1")        # +1800 is inside the halt hour (17:30 ET), so only -1800 (a loss) counts
    assert abs(cm - T.net_c(0.2, False)) < 1e-9
    cm = T.control_mean(t, pool, {}, "S9")        # not a halt slot: both neighbours count
    assert abs(cm - (T.net_c(0.2, True) + T.net_c(0.2, False)) / 2) < 1e-9
    assert T.control_mean(t, {}, {}, "S9") is None


def test_verdict_rules():
    good = lambda n, pfv, d: {"n": n, "pf": pfv, "pf_x12": pfv, "diff_c": d, "mean_c": 1.0}
    assert T.verdict({"W1": good(60, 2, 1), "W2": good(80, 2, 1)}) == "NOT_ENOUGH_DATA"            # 140 < 150
    assert T.verdict({"W1": good(100, 2, 1), "W2": good(80, 1.2, 1)}) == "FALSIFIED"
    assert T.verdict({"W1": good(100, 2, 1), "W2": good(80, 2, -1)}) == "FALSIFIED"
    assert T.verdict({"W1": good(100, 2, 1), "W2": good(80, 2, 1)}) == "PASSES_W1_W2"
    assert T.verdict({"W1": good(10, 2, 1), "W2": good(200, 2, 1)}) == "NOT_ENOUGH_DATA"            # one window under 30


if __name__ == "__main__":
    names = [n for n in dir() if n.startswith("test_")]
    for n in names:
        globals()[n]()
    print(f"{len(names)} tests ok")
