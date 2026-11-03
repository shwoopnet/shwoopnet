"""SPIKE1 helpers on hand-built candles. Research only. Plain runner."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import spike1  # noqa: E402

CT = 1_790_000_100
CT = CT - CT % 900


def q(m, half=0.01):
    return (round(m - half, 4), round(m + half, 4), 1.0)


def win(ct, mids):
    """mids: {seconds_before_close: yes_mid}"""
    return {"tk": f"W{ct}", "ct": ct, "cs": {ct - s: q(m) for s, m in mids.items()}, "res": None}


def quiet(ct, base=0.50, step=0.01):
    return win(ct, {s: base + (step if (s // 60) % 2 else 0) for s in range(840, 59, -60)})


def by(*ws):
    return {w["ct"]: w for w in ws}


def test_mid_rejects_wide_crossed_and_settled():
    assert abs(spike1.mid((0.40, 0.42, 1.0)) - 0.41) < 1e-9
    assert spike1.mid((0.40, 0.60, 1.0)) is None            # spread 0.20
    assert spike1.mid((0.42, 0.40, 1.0)) is None
    assert spike1.mid((0.999, 1.0, 1.0)) is None
    assert spike1.mid(None) is None


def test_trailing_sd_floor_and_minimum_changes():
    prev = [quiet(CT - 900 * j) for j in range(1, 5)]
    sd = spike1.trailing_sd(by(*prev), CT)
    assert abs(sd - spike1.SD_FLOOR) < 1e-9                              # +-1c alternation has rms 0.01 = the floor
    assert spike1.trailing_sd(by(*prev[:2]), CT) is None      # 2 windows: 26 changes < 40
    assert spike1.trailing_sd({}, CT) is None


def test_trailing_sd_ignores_the_settlement_candle_and_the_current_window():
    prev = [quiet(CT - 900 * j) for j in range(1, 5)]
    for w in prev:
        w["cs"][w["ct"]] = (0.999, 1.0, 1.0)                  # settlement candle: must not enter
    cur = quiet(CT, 0.5, 0.2)                                 # huge moves in the current window: must not enter
    assert abs(spike1.trailing_sd(by(*prev, cur), CT) - spike1.SD_FLOOR) < 1e-9


def test_spike_z_units():
    cs = {CT - 600: q(0.50), CT - 480: q(0.50), CT - 540: q(0.50)}
    cs[CT - 480] = q(0.70)
    z, d = spike1.spike_z(cs, CT, 480, 0.02)
    assert abs(d - 0.20) < 1e-9 and abs(z - 0.20 / (0.02 * math.sqrt(2))) < 1e-9
    assert spike1.spike_z(cs, CT, 300, 0.02) is None          # missing candle


def test_up_spike_to_high_mid_is_reversal_on_no():
    prev = [quiet(CT - 900 * j) for j in range(1, 5)]
    mids = {s: 0.50 for s in range(840, 59, -60)}
    mids[480] = 0.80                                          # signal: 0.50 -> 0.80 over 2 minutes
    mids[420] = 0.80
    cur = win(CT, mids)
    trig, ctrl, ok = spike1.window_events(cur, by(*prev, cur))
    assert ok and trig["look"] == 480 and trig["side"] == "no" and trig["kind"] == "rev"
    assert abs(trig["fill"] - (1 - 0.79)) < 1e-6              # NO ask = 1 - YES bid of the NEXT candle


def test_down_spike_to_low_mid_is_reversal_on_yes():
    prev = [quiet(CT - 900 * j) for j in range(1, 5)]
    mids = {s: 0.50 for s in range(840, 59, -60)}
    mids[480] = 0.20
    mids[420] = 0.20
    cur = win(CT, mids)
    trig, _, _ = spike1.window_events(cur, by(*prev, cur))
    assert trig["side"] == "yes" and trig["kind"] == "rev" and abs(trig["fill"] - 0.21) < 1e-6


def test_up_spike_that_ends_low_is_continuation():
    prev = [quiet(CT - 900 * j, 0.10) for j in range(1, 5)]
    mids = {s: 0.08 for s in range(840, 59, -60)}
    mids[480] = 0.22
    mids[420] = 0.22
    cur = win(CT, mids)
    trig, _, _ = spike1.window_events(cur, by(*prev, cur))
    assert trig is not None and trig["side"] == "yes" and trig["kind"] == "cont"


def test_no_trade_when_cheap_side_is_missing_or_limit_exceeded():
    prev = [quiet(CT - 900 * j) for j in range(1, 5)]
    mids = {s: 0.50 for s in range(840, 59, -60)}
    mids[480] = 0.62                                          # spike to 0.62: neither side is under 0.30
    mids[420] = 0.62
    cur = win(CT, mids)
    trig, _, _ = spike1.window_events(cur, by(*prev, cur))
    assert trig is None
    mids2 = {s: 0.50 for s in range(840, 59, -60)}
    mids2[480] = 0.75
    mids2[420] = 0.55                                         # next candle: NO ask jumps to 0.46 > limit
    cur2 = win(CT, mids2)
    trig2, _, _ = spike1.window_events(cur2, by(*prev, cur2))
    assert trig2 is None or trig2["look"] != 480


def test_no_spike_window_gives_control_looks_only():
    prev = [quiet(CT - 900 * j, 0.15) for j in range(1, 5)]
    cur = win(CT, {s: 0.15 for s in range(840, 59, -60)})
    trig, ctrl, ok = spike1.window_events(cur, by(*prev, cur))
    assert ok and trig is None and len(ctrl) == len(spike1.LOOKS)
    assert all(t["side"] == "yes" for t in ctrl)


def test_fee_is_event1_cost():
    assert abs(spike1.net_c(0.2, True) - 100 * (0.8 - spike1.event1.gen6.fee(0.2, 10))) < 1e-9


def test_cont_leg_is_the_other_side_with_limit():
    prev = [quiet(CT - 900 * j) for j in range(1, 5)]
    mids = {s: 0.50 for s in range(840, 59, -60)}
    mids[480] = 0.80
    mids[420] = 0.80
    cur = win(CT, mids)
    trig, _, _ = spike1.window_events(cur, by(*prev, cur))
    b = spike1.cont_leg(cur, trig)
    assert b["side"] == "yes" and abs(b["fill"] - 0.81) < 1e-6
    cur["cs"][CT - 420] = (0.985, 0.995, 1.0)
    assert spike1.cont_leg(cur, trig) is None                  # 0.995 > 0.97 limit


def test_verdict_floors_and_kills():
    def h(n, pf, ab, ac, x12):
        return {"A": {"n": n, "pf": pf}, "A_minus_B": (ab, 0, 1, 0), "A_minus_ctrl": (ac, 0, 1, 0), "A_x12": {"pf": x12}}
    ok = h(200, 2.0, 1.0, 1.0, 1.8)
    assert spike1.verdict(ok, ok, 400)[0] == "PASS_SCREEN"
    assert spike1.verdict(ok, h(30, 2.0, 1, 1, 1.8), 230)[0] == "NOT_ENOUGH_DATA"
    assert spike1.verdict(ok, ok, 149)[0] == "NOT_ENOUGH_DATA"
    assert spike1.verdict(ok, h(200, 1.4, 1, 1, 1.8), 400)[0] == "FALSIFIED"
    assert spike1.verdict(ok, h(200, 2.0, -1, 1, 1.8), 400)[0] == "FALSIFIED"
    assert spike1.verdict(ok, h(200, 2.0, 1, -1, 1.8), 400)[0] == "FALSIFIED"


def test_diff_vs_ctrl_cell_and_fallback():
    def t(h, win, fill=0.2, look=480):
        return {"series": "S", "hour": h, "third": 1, "day": "d", "win": win, "tr": {"fill": fill, "look": look}}
    ctrl = [t(5, False) for _ in range(5)]
    m, z, used, dropped = spike1.diff_vs_ctrl([t(5, True), t(5, True)], ctrl)
    assert used == 2 and dropped == 0 and m > 0
    m2, z2, used2, dropped2 = spike1.diff_vs_ctrl([t(7, True)], ctrl)       # hour 7: neighbours 6 and 8 are empty
    assert used2 == 0 and dropped2 == 1
    ctrl2 = [t(4, False) for _ in range(3)] + [t(6, False) for _ in range(3)]
    _, _, used3, _ = spike1.diff_vs_ctrl([t(5, True), t(5, False)], ctrl2)  # empty cell, neighbours give 6
    assert used3 == 2


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("ok  ", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
