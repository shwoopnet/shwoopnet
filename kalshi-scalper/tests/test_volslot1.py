"""VOLSLOT1 helpers on hand-built windows. Research only. Plain runner."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scalper import volslot1 as V  # noqa: E402

CT = 1_800_000_000 // 900 * 900


def test_hard_limit_097_and_band():
    cs = {CT - 180: (0.90, 0.92, 5, 1), CT - 120: (0.95, 0.97, 5, 1)}
    why, t = V.window_trade(cs, CT)
    assert why == "trade" and t["side"] == "yes" and abs(t["fill"] - 0.97) < 1e-9
    cs[CT - 120] = (0.96, 0.98, 5, 1)
    assert V.window_trade(cs, CT)[0] == "limit"
    cs[CT - 180] = (0.80, 0.82, 5, 1)
    assert V.window_trade(cs, CT)[0] == "nofav"


def test_no_side_favourite():
    cs = {CT - 180: (0.04, 0.06, 5, 1), CT - 120: (0.03, 0.05, 5, 1)}
    why, t = V.window_trade(cs, CT)
    assert why == "trade" and t["side"] == "no" and abs(t["fill"] - 0.97) < 1e-9


def test_path_move_needs_pairs_and_ignores_result():
    cs = {CT - 900 + 60 * i: (0.49 + 0.01 * (i % 2), 0.51 + 0.01 * (i % 2), 1, 1) for i in range(1, 15)}
    v = V.path_move(cs, CT)
    assert v is not None and abs(v - 0.01 * 11) < 1e-9     # candles up to CT-180 only: 12 candles, 11 steps
    assert V.path_move({CT - 840: (0.4, 0.6, 1, 1)}, CT) is None


def test_worst_loss():
    assert abs(V.worst_loss_dollars(10) - 9.73) < 1e-9


def test_slot_et():
    # 2026-10-20 16:00 UTC = 12:00 EDT Tuesday -> quarter 48, weekday
    from datetime import datetime, timezone
    ct = int(datetime(2026, 10, 20, 16, 0, tzinfo=timezone.utc).timestamp())
    assert V.slot_of(ct) == (48, True)


if __name__ == "__main__":
    n = 0
    for k, f in sorted(globals().items()):
        if k.startswith("test_"):
            f()
            n += 1
    print(n, "ok")
