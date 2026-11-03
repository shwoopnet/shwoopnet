"""Synthetic tests for SNAPBACK1 (src/scalper/snapback1.py); run with: python tests/test_snapback1.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import snapback1 as S

assert (S.FEE_SIDE_BP, S.FUND_BP, S.STOP_ATR, S.TIME_STOP_MIN, S.COOLDOWN_MIN, S.Z_BAR, S.MIN_N) == (12.0, 1.0, 0.5, 360, 360, 5.27, 40), "registered numbers"
assert len(S.GRID) == 8


def series(n, base=100.0, wiggle=0.5, oi=1000.0):
    """flat minutes with a +-wiggle high/low band: every hour's true range is 2*wiggle"""
    t0 = 3600 * 1000
    o = [base] * n; h = [base + wiggle] * n; l = [base - wiggle] * n; c = [base] * n; oi_ = [oi] * n
    return t0, o, h, l, c, oi_


def drop(t0, o, h, l, c, oi, at, size, oidrop):
    """one minute (`at`) falls by `size` (a cascade candle); open interest falls by `oidrop` fraction from that minute on"""
    o[at] = 100.0; c[at] = 100.0 - size; h[at] = 100.0; l[at] = 100.0 - size
    for i in range(at, len(c)):
        oi[i] = 1000.0 * (1 - oidrop)


# 1. no move, no trade
t0, o, h, l, c, oi = series(24 * 60 * 3)
assert S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2) == []

# 2. a 10 point fall (ATR is about 1) with OI -10% triggers a LONG at the NEXT minute's open
t0, o, h, l, c, oi = series(24 * 60 * 3)
at = 40 * 60
drop(t0, o, h, l, c, oi, at, 10.0, 0.10)
for i in range(at + 1, len(c)):                       # price then holds at 90, flat band
    o[i] = 90.0; c[i] = 90.0; h[i] = 90.5; l[i] = 89.5
tr = S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2)
assert len(tr) == 1 and tr[0]["side"] == 1, tr
assert tr[0]["entry_ts"] == t0 + 60 * (at + 1) and tr[0]["entry"] == 90.0, "enters at the next minute's open"

# 3. OI NOT falling: no trade (the filter matters), and rising OI too
t0, o, h, l, c, oi = series(24 * 60 * 3)
drop(t0, o, h, l, c, oi, at, 10.0, -0.10)
assert S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2) == []
# OI falling 3%: passes x=2% but not x=5%
t0, o, h, l, c, oi = series(24 * 60 * 3)
drop(t0, o, h, l, c, oi, at, 10.0, 0.03)
assert len(S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2)) >= 1 and S.find_trades(t0, o, h, l, c, oi, 2, 0.05, 2) == []

# 4. exits: price rebounds past target -> target; falls on -> stop; flat -> time stop. Stop wins a same-minute tie.
def trade_with_after(after_h, after_l, after_c):
    t0, o, h, l, c, oi = series(24 * 60 * 3)
    drop(t0, o, h, l, c, oi, at, 10.0, 0.10)
    for i in range(at + 1, len(c)):
        o[i] = 90.0; c[i] = after_c; h[i] = after_h; l[i] = after_l
    return S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2)[0]

a = None
t = trade_with_after(200.0, 89.9, 90.0)            # high of 200 on the first minute, low barely under entry: target
assert t["reason"] == "target" and t["gross_bp"] > 0, t
t = trade_with_after(90.1, 1.0, 90.0)              # deep low: stop
assert t["reason"] == "stop" and t["gross_bp"] < 0, t
t = trade_with_after(200.0, 1.0, 90.0)             # both in the same minute: STOP
assert t["reason"] == "stop", t
t = trade_with_after(90.1, 89.9, 90.0)             # nothing: time stop after 360 minutes
assert t["reason"] == "time" and t["exit_ts"] - t["entry_ts"] == 360 * 60, t
# fees: a flat time-stop trade nets about -24 bp minus funding
assert abs(t["gross_bp"]) < 1e-9 and -24 - 3 <= t["net_bp"] <= -24, t

# 5. cooldown: after a trade, a second trigger within 6 hours is skipped
t0, o, h, l, c, oi = series(24 * 60 * 3)
drop(t0, o, h, l, c, oi, at, 10.0, 0.10)
for i in range(at + 1, len(c)):
    o[i] = 90.0; c[i] = 90.0; h[i] = 90.5; l[i] = 89.5
tr = S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2)
assert len(tr) == 1, "one cascade, one trade"
# last_entry_ts blocks late entries (frozen third)
assert S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2, last_entry_ts=t0 + 60 * at) == []

# 6. a rise is faded SHORT
t0, o, h, l, c, oi = series(24 * 60 * 3)
o[at] = 100.0; c[at] = 110.0; h[at] = 110.0; l[at] = 100.0
for i in range(at, len(c)):
    oi[i] = 900.0
for i in range(at + 1, len(c)):
    o[i] = 110.0; c[i] = 110.0; h[i] = 110.5; l[i] = 109.5; oi[i] = 900.0
tr = S.find_trades(t0, o, h, l, c, oi, 2, 0.02, 2)
assert len(tr) == 1 and tr[0]["side"] == -1

# 7. grid_from_candles forward fills a missing/no-trade minute and keeps OI
cs = [{"end_period_ts": 7200 + 60 * i, "open_interest": "5.00",
       "price": {"open": "10", "high": "11", "low": "9", "close": "10.5"}} for i in range(3)]
cs.append({"end_period_ts": 7200 + 60 * 4, "open_interest": "6.00", "price": {"open": None, "high": None, "low": None, "close": None}})
t0_, o_, h_, l_, c_, oi_ = S.grid_from_candles(cs)
assert t0_ == 7140 and len(c_) == 5 and c_[3] == 10.5 and o_[3] == 10.5 and oi_[3] == 5.0 and oi_[4] == 6.0

# 8. stats and verdict
tr = [{"net_bp": v, "move_atr": v / 100.0} for v in (50, -20, 30, -10)]
s = S.stats(tr)
assert s["n"] == 4 and abs(s["win"] - 0.5) < 1e-9 and abs(s["pf"] - 80 / 30) < 1e-9 and abs(s["exp_bp"] - 12.5) < 1e-9 and s["worst_bp"] == -20
assert S.verdict(s, s, {"n": 10, "exp_bp": 1, "pf": 9, "z": 9}) == "NOT_ENOUGH_DATA"
good = {"n": 50, "exp_bp": 5, "pf": 2.0, "z": 6.0}
assert S.verdict(good, good, good) == "SURVIVES_DEVELOPMENT"
assert S.verdict(good, dict(good, exp_bp=-1), good) == "FALSIFIED"
assert S.verdict(good, dict(good, pf=1.4), good) == "FALSIFIED"
assert S.verdict(good, good, dict(good, z=3.0)) == "FALSIFIED"

# 9. funding counted across a funding time: a trade entered just before 08:00 UTC pays one
assert (8 * 3600 + 60) // S.FUND_PERIOD - (8 * 3600 - 60) // S.FUND_PERIOD == 1
print("test_snapback1: ok")
