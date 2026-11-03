"""EVENT1 helpers on hand-built candles and calendars (candle = (bid, ask, volume, oi)). Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import event1  # noqa: E402

CT = 1_800_000_100 // 900 * 900


def cs(sig=(0.70, 0.74), fill=(0.71, 0.75), vol=5.0):
    return {CT - 180: (sig[0], sig[1], vol, 1.0), CT - 120: (fill[0], fill[1], vol, 1.0)}


def test_cheap_side_yes_first_and_fill_next_candle():
    why, t = event1.window_trade(cs(sig=(0.28, 0.32), fill=(0.34, 0.38)), CT)
    assert why == "trade" and t["side"] == "yes" and abs(t["fill"] - 0.38) < 1e-9


def test_no_side_when_yes_is_expensive():
    why, t = event1.window_trade(cs(), CT)          # YES ask 0.74; NO ask = 1 - 0.70 = 0.30; fill NO ask = 1 - 0.71 = 0.29
    assert why == "trade" and t["side"] == "no" and abs(t["fill"] - 0.29) < 1e-9


def test_hard_limit_at_050():
    why, t = event1.window_trade(cs(sig=(0.40, 0.46), fill=(0.46, 0.52)), CT)
    assert why == "limit" and t is None              # fill ask 0.52 is above the 0.50 limit: no trade, counted
    why, t = event1.window_trade(cs(sig=(0.40, 0.46), fill=(0.44, 0.50)), CT)
    assert why == "trade" and abs(t["fill"] - 0.50) < 1e-9   # exactly at the limit is allowed


def test_gaps_and_wide_spread_are_not_trades():
    c = cs(); del c[CT - 120]
    assert event1.window_trade(c, CT)[0] == "gap"
    c = cs(); del c[CT - 180]
    assert event1.window_trade(c, CT)[0] == "gap"
    assert event1.window_trade(cs(sig=(0.20, 0.34)), CT)[0] == "nocheap"        # spread 0.14 > 0.10
    assert event1.window_trade(cs(sig=(0.01, 0.99), fill=(0.01, 0.99)), CT)[0] == "nocheap"
    assert event1.window_trade(cs(sig=(0.00, 0.30)), CT)[0] == "gap"             # one sided


def test_fee_and_worst_loss():
    # 7% x C x p x (1-p) rounded up per order: C = 10 at 0.50 is 17.5c -> 18c; C = 5 is 8.75c -> 9c
    assert abs(event1.worst_loss_dollars(10) - 5.18) < 1e-9
    assert abs(event1.worst_loss_dollars(5) - 2.59) < 1e-9
    assert abs(event1.net_c(0.30, False) - (-30 - 100 * event1.gen6.fee(0.30, 10))) < 1e-9
    assert event1.net_c(0.30, True) > 0 > event1.net_c(0.30, False)


def test_event_window_membership():
    e = CT                                     # an event exactly at the close
    cal = event1.Cal([(e, "US_OPEN", "x")])
    assert cal.types_for(CT) == {"US_OPEN"}                    # window closing at the event
    assert cal.types_for(CT + 900) == set()                    # the window that opens at it is Try A's non-event window
    assert cal.types_for(CT - 900) == set()
    assert cal.types_open(CT + 900) == {"US_OPEN"}             # Try B: event in the first 5 minutes of the window
    assert cal.types_open(CT) == set()
    cal = event1.Cal([(CT - 299, "X", "x"), (CT - 300, "Y", "x"), (CT + 1, "Z", "x")])
    assert cal.types_for(CT) == {"X"}                          # c - 300 < e <= c: -299 in, -300 out, +1 out


def test_calendar_generated_rows():
    ev = event1.calendar()
    kinds = {}
    for ts, k, _ in ev:
        kinds[k] = kinds.get(k, 0) + 1
    for k in ("CPI", "JOBS", "FOMC", "US_OPEN", "US_CLOSE", "LONDON_OPEN", "TOKYO_OPEN", "HK_OPEN", "ISM_MFG", "ISM_SVC", "CONF_BOARD", "EIA", "CLAIMS"):
        assert kinds.get(k, 0) > 0, k
    assert all(ts % 900 == 0 for ts, k, _ in ev)               # every event is on a quarter hour
    from datetime import datetime, timezone
    opens = [ts for ts, k, _ in ev if k == "US_OPEN"]
    assert datetime.fromtimestamp(opens[0], timezone.utc).strftime("%H:%M") in ("13:30", "14:30")
    assert datetime(2026, 9, 7, 13, 30, tzinfo=timezone.utc).timestamp() not in opens   # Labor Day


def test_diff_vs_slot_removes_time_of_day():
    def mk(ct, win, day, sr="KXWTI15M"):
        return {"series": sr, "ct": ct, "day": day, "tr": {"fill": 0.30, "side": "yes", "zv": False}, "win": win}
    ctl = [mk(CT - 86400 * i, i % 3 == 0, f"d{i}") for i in range(1, 25)]       # same slot, 24 other days
    ev = [mk(CT, False, "e0"), mk(CT, False, "e1")]
    d, z, n, dropped = event1.diff_vs_slot(ev, ctl)
    assert n == 2 and dropped == 0 and d < 0
    d, z, n, dropped = event1.diff_vs_slot(ev, ctl[:5])                          # fewer than CTRL_MIN: dropped, not guessed
    assert n == 0 and dropped == 2


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn(); print("ok  ", name)
            except Exception as e:  # noqa: BLE001
                fails += 1; print("FAIL", name, repr(e))
    sys.exit(1 if fails else 0)
