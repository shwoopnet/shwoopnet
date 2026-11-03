"""EVENT830 evaluator on hand-built candles (candle = (bid, ask, volume, oi)). Research only. Plain runner."""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import event830 as e8, event1  # noqa: E402
from scalper.fwdeval import NoData  # noqa: E402

REL = e8._t("2026-11-05")
OFF = REL + 900                                   # a window that does not close at a release


def win(ct, sig=(0.28, 0.32), fill=(0.30, 0.34), series="KXSILVER15M"):
    return {"source": "candles", "series": series, "ticker": "T", "close_ts": ct, "result": "yes",
            "candles": {ct - 180: (sig[0], sig[1], 5.0, 1.0), ct - 120: (fill[0], fill[1], 5.0, 1.0)}}


def test_release_window_trades_cheap_side():
    tr = e8.forward_eval(win(REL), {})
    assert tr["side"] == "yes" and abs(tr["entry"] - 0.34) < 1e-9 and tr["exit"] is None and tr["t"] == REL - 120


def test_other_window_and_other_series_do_not_trade():
    assert e8.forward_eval(win(OFF), {}) is None
    assert e8.forward_eval(win(REL, series="KXBTC15M"), {}) is None


def test_hard_limit_and_gap():
    assert e8.forward_eval(win(REL, sig=(0.40, 0.46), fill=(0.46, 0.52)), {}) is None      # fill ask 0.52 above the 0.50 limit
    w = win(REL); del w["candles"][REL - 120]
    try:
        e8.forward_eval(w, {}); assert False
    except NoData:
        pass


def test_parity_with_event1_rule():
    for sig, fill in [((0.28, 0.32), (0.30, 0.34)), ((0.70, 0.74), (0.71, 0.75)), ((0.40, 0.46), (0.44, 0.50)), ((0.90, 0.95), (0.9, 0.95))]:
        w = win(REL, sig, fill)
        why, t = event1.window_trade(w["candles"], REL)
        r = e8.forward_eval(w, {})
        assert (t is None) == (r is None) and (t is None or (t["side"] == r["side"] and abs(t["fill"] - r["entry"]) < 1e-9))


def test_release_times_are_0830_new_york():
    for ct in e8.RELEASES:
        et = datetime.fromtimestamp(ct, e8.NY)
        assert (et.hour, et.minute) == (8, 30) and et.weekday() < 5 and ct > e8.FREEZE


def test_control_is_eastern_clock_and_excludes_releases():
    mon = e8._t("2026-11-09")                      # Monday 08:30 EST, no release
    assert e8.is_control(mon) and not e8.is_control(REL) and not e8.is_control(mon + 900) and not e8.is_control(e8._t("2026-11-07"))


def test_status_rules():
    base = {"n": 20, "pf": 2.0, "pf_x12": 1.9}
    assert e8.status(base, 3.0, 40 * 86400, 0).startswith("NOT_ENOUGH_DATA: 20 of 150") and "months to go" in e8.status(base, 3.0, 40 * 86400, 0)
    assert e8.status(dict(base, n=40, pf=0.9), 3.0, 1, 0).startswith("STOPPED_EARLY")
    assert e8.status(dict(base, n=150, pf=1.1), 3.0, 1, 0) == "FALSIFIED"
    assert e8.status(dict(base, n=150), -0.1, 1, 0) == "FALSIFIED"
    assert e8.status(dict(base, n=150), 1.0, 1, 0).startswith("NOT_YET_FALSIFIED")


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn(); print("ok  ", name)
            except Exception as e:  # noqa: BLE001
                fails += 1; print("FAIL", name, repr(e))
    sys.exit(1 if fails else 0)
