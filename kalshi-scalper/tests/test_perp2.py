"""Plain assert tests for PERP2 and PERP3 (src/scalper/perp2.py); run with: python tests/test_perp2.py. Each states a consequence, not a mechanism."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import perp2 as Q

assert (Q.SMA_N, Q.DOWN_DAYS, Q.STOP_ATR2, Q.EXIT_HI, Q.MAX_HOLD2, Q.ZWIN, Q.Z_ENTRY, Q.Z_STOP, Q.MAX_HOLD3, Q.Z_BAR2) == (100, 3, 2.0, 5, 20, 60, 2.0, 4.0, 30, 2.4), "the registered numbers"
assert Q.SPEC == {"PERP2": {"min_trades": 100, "min_years": 4}, "PERP3": {"min_trades": 40, "min_years": 4}}


def mk(closes, opens=None, spread=0.5):
    d0 = datetime(2020, 1, 1)
    out = []
    for i, c in enumerate(closes):
        o = opens[i] if opens else c
        out.append([(d0 + timedelta(days=i)).strftime("%Y-%m-%d"), o, max(o, c) + spread, min(o, c) - spread, c])
    return out


# PERP2: an uptrend of 120 days, then three down closes: the long is filled at the NEXT open, strictly after the signal day, and only while above the 100 day average.
rise = [100.0 + i * 0.5 for i in range(120)]
sig = rise + [rise[-1] - 0.5, rise[-1] - 1.0, rise[-1] - 1.5]      # three lower closes (still far above the average) -> signal at the third
exit_up = sig + [sig[-1] - 0.2, sig[-1] + 10.0, sig[-1] + 10.0]     # a close above the 5 day high -> exit at the next open
t = Q.dip_trades(mk(exit_up), "X")
assert len(t) == 1 and t[0]["side"] == 1 and t[0]["entry_i"] == 123, t
assert t[0]["exit_i"] > t[0]["entry_i"] and t[0]["exit_i"] == 125 and not t[0]["stopped"], t
# No signal below the 100 day average: a falling market with three down closes is not a dip in an uptrend.
fall = [200.0 - i * 0.5 for i in range(130)]
assert Q.dip_trades(mk(fall), "X") == [], "no entries in a downtrend"
# The stop is a resting order: a gap down through it fills at the open.
gap = mk(sig + [sig[-1], sig[-1]])
gap[-1][1] = 50.0
gap[-1][3] = 49.0
tg = Q.dip_trades(gap, "X")
assert tg and tg[0]["stopped"] and tg[0]["exit"] == 50.0, tg
# The time stop: held 20 bars at most (the exit is decided at the close of the 20th bar and filled at the next open).
flatter = sig + [sig[-1]] * 40
tt = Q.dip_trades(mk(flatter), "X")
assert tt and tt[0]["exit_i"] - tt[0]["entry_i"] <= 21, tt

# PERP3: a stretched ratio is faded: gold jumps against silver -> short gold / long silver at the NEXT open, exit when the ratio comes back through its mean.
import random
rng = random.Random(3)
base = [100.0 + rng.uniform(-2.0, 2.0) for _ in range(80)]
silver = mk([10.0] * 80)
gold = mk(base)
for i in (60, 61, 62):
    gold[i][4] = 105.0
    gold[i][1] = 105.0
    gold[i][2] = 105.5
    gold[i][3] = 104.5
for i in range(63, 80):
    gold[i][4] = 100.0
    gold[i][1] = 100.0
    gold[i][2] = 100.5
    gold[i][3] = 99.5
tp = Q.pair_trades(gold, silver)
assert tp and tp[0]["side"] == -1 and tp[0]["entry_i"] == 61 and tp[0]["exit_i"] > tp[0]["entry_i"], tp
assert tp[0]["gross"] > 0, "gold fell back against a flat silver, so short gold / long silver made money"
# Both legs pay: the pairs cost is double the single-leg cost.
assert abs(Q.net({"market": "GOLD/SILVER", "gross": 0.05, "days": 10}) - (0.05 - 2 * (0.0026 + 0.002))) < 1e-12
assert Q.verdict("PERP3", [], [])[0] == "NOT_ENOUGH_DATA"
print("ok test_perp2")
