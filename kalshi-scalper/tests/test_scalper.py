"""Plain assert tests; run with: python tests/test_scalper.py
Each states a consequence, not a mechanism."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper.fees import taker_fee, round_trip_cost
from scalper.risk import Limits, State, Order, check_order, KILL_FILE

LIM = Limits(bankroll=1000.0)


def good(**kw):
    base = dict(underlying="BTC", price=0.50, contracts=10, my_prob=0.60, spread=0.01)
    base.update(kw)
    return Order(**base)


# A scalp exiting early pays fees twice, so it must cost more than the same
# trade held to settlement (one fee). If this ever flips, the model is wrong.
assert round_trip_cost(0.50, 0.50) >= 2 * taker_fee(0.50) - 1e-9
# Fees are cheapest at the extremes and dearest at 50c: that is where scalps are viable.
assert taker_fee(0.95, 100) < taker_fee(0.50, 100)
# Crossing a 2c spread at 50c can never be break-even on a flat market.
assert round_trip_cost(0.51, 0.49) > 0.02

# A normal, edged, small order is allowed.
ok, why = check_order(good(contracts=10), LIM, State())
assert ok, why
# One trade must never risk more than the per-trade cap (1% of $1000 = $10).
ok, why = check_order(good(contracts=40), LIM, State())
assert not ok and any("per-trade" in w for w in why)
# Many BTC strikes are one bet: a second BTC order is refused when BTC exposure is full.
ok, why = check_order(good(contracts=10), LIM, State(open_risk_by_underlying={"BTC": 28.0}))
assert not ok and any("correlated" in w for w in why)
# After the daily loss limit, no new risk is taken, even on a great-looking trade.
ok, why = check_order(good(), LIM, State(realized_pnl_today=-25.0))
assert not ok and any("daily loss" in w for w in why)
# No edge after fees means no trade. Buying at your own probability loses to the fee.
ok, why = check_order(good(price=0.50, my_prob=0.51), LIM, State())
assert not ok and any("edge" in w for w in why)
# Garbage input fails closed rather than slipping through.
ok, _ = check_order(good(price=1.5), LIM, State())
assert not ok
# The kill switch overrides everything.
KILL_FILE.write_text("stop")
try:
    ok, why = check_order(good(), LIM, State())
    assert not ok and "kill" in why[0]
finally:
    KILL_FILE.unlink()
print("all tests passed")

# ---- paper engine ----
from scalper.paper import run

# snapshot: (ts, yes_bid, bid_sz, yes_ask, ask_sz)
flat = {"M": [(t, 0.49, 100, 0.51, 100) for t in range(0, 200, 2)]}
always = lambda h: ("yes", 0.6)
tr = run(flat, always, hold_s=10)
# A flat market must LOSE money to spread and fees. If a flat book ever shows a
# profit, fills are being priced at the mid and every result is fiction.
assert tr and all(t.net < 0 for t in tr)
# The fill must come from a later snapshot than the signal (no lookahead).
seen = []
def spy(h):
    seen.append(len(h)); return ("yes", 0.6) if len(h) == 1 else None
tr = run({"M": [(0, .49, 9, .51, 9), (2, .60, 9, .62, 9), (20, .60, 9, .62, 9)]}, spy, hold_s=5)
assert tr and tr[0].entry == 0.62      # filled at the NEXT snapshot's ask, not 0.51
# Size is capped by what is displayed at the touch.
tr = run({"M": [(0, .49, 3, .51, 3), (2, .49, 3, .51, 3), (30, .49, 3, .51, 3)]}, spy, hold_s=5, contracts=50)
assert tr and tr[0].contracts == 3
print("paper engine tests passed")

# ---- status and service ----
from scalper.status import find_gaps
from scalper.service import build_plist, LABEL

# A laptop that sleeps for 40 minutes must show up as a gap. Silence that looks
# like "nothing happened" would let a 60 second move be computed across a hole.
ts = [0, 2, 4, 6, 2406, 2408]
assert find_gaps(ts) == [(6, 2406)]
assert find_gaps([0, 2, 4, 6, 8]) == []
# The background job must restart itself and run the recorder, not something else.
pl = build_plist()
assert pl["Label"] == LABEL and pl["KeepAlive"] is True and pl["RunAtLoad"] is True
assert pl["ProgramArguments"][-2:] == ["scalper.recorder", "2"]
print("status and service tests passed")

# ---- analyze ----
from scalper.analyze import needed_accuracy
# A coin flip must never look profitable: with any cost at all, break-even
# needs better than 50% of calls right.
assert needed_accuracy(0.04, 0.10) > 0.5
# Free trading would break even at 50%.
assert abs(needed_accuracy(0.0, 0.10) - 0.5) < 1e-12
# Hand check: 4.4c cost against a 9.34c average move needs about 73.6% right.
assert abs(needed_accuracy(0.0440, 0.0934) - 0.7355) < 0.001
# When the cost exceeds twice the move, no predictor can break even.
assert needed_accuracy(0.0423, 0.0207) > 1.0
print("analyze tests passed")

# ---- pre-registered verdict ----
from scalper.analyze import verdict, RULE_MIN_HOURS

def rec(series, mid, cost, move, ts, secs=400.0):
    return (series, 60, mid, secs, cost, move, ts)

def block(n, cost, move, t0, t1, mid=0.5):
    return [rec("S", mid, cost, move, t0 + (t1 - t0) * i / n) for i in range(n)]

H = RULE_MIN_HOURS + 1
# Too little data never produces a conclusion either way.
assert verdict(block(2000, 0.05, 0.10, 0, 1000), 5.0)[0] == "NOT_ENOUGH_DATA"
# Costly, small-move data is a clean negative: a directional scalp has no room.
assert verdict(block(2000, 0.05, 0.10, 0, 1000), H)[0] == "FALSIFIED"
# A bucket that beats the bar in BOTH halves earns only "not yet falsified".
good = block(1000, 0.02, 0.20, 0, 1000)            # needs 55% throughout
assert verdict(good, H)[0] == "NOT_YET_FALSIFIED"
# One lucky half must not qualify: 18 buckets will always throw up a fluke.
lucky = block(500, 0.02, 0.20, 0, 499) + block(500, 0.05, 0.10, 500, 1000)
assert verdict(lucky, H)[0] == "FALSIFIED"
# A promising bucket with too few samples must not qualify.
assert verdict(block(300, 0.02, 0.20, 0, 1000), H)[0] == "FALSIFIED"
# No verdict may ever read as a go-ahead to trade.
import scalper.analyze as _a, re as _re
_code = _re.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_a.__file__).read())
assert not _re.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _code)
print("verdict tests passed")

# ---- market hours are per series ----
from scalper.analyze import market_hours
# Two series recorded over the same 15 minute window are 0.25h EACH, not 0.5h.
# Summing them is what made "72 hours" fire after about 36 hours of recording.
by = {("BTC", "m1"): [(0.0,), (900.0,)], ("GOLD", "m1"): [(0.0,), (900.0,)]}
h = market_hours(by)
assert h == {"BTC": 0.25, "GOLD": 0.25}, h
assert min(h.values()) == 0.25
print("market hours tests passed")
