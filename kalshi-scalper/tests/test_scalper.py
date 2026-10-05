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
dense = [(float(t),) for t in range(0, 901, 2)]
by = {("BTC", "m1"): dense, ("GOLD", "m1"): dense}
h = market_hours(by)
assert set(h) == {"BTC", "GOLD"} and all(abs(v - 0.25) < 1e-9 for v in h.values()), h
# A market recorded for 4 minutes, then nothing for 10, then 1 minute more, is
# 5 minutes of data, not the 15 that first-to-last would credit.
holey = [(float(t),) for t in range(0, 241, 2)] + [(float(t),) for t in range(840, 901, 2)]
assert abs(market_hours({("BTC", "m"): holey})["BTC"] - 300 / 3600) < 1e-9
print("market hours tests passed")

# ---- windows must not span recording gaps ----
from scalper.analyze import find_exit
ts_ = [float(t) for t in range(0, 61, 2)] + [1000.0, 1002.0]
# Normal: a 60s hold from t=0 exits at the snapshot at t=60.
assert ts_[find_exit(ts_, 0, 60)] == 60.0
# Entry at t=20: the next snapshot 60s later would be t=80, but the recorder
# was off until t=1000. That is not a 60 second hold and must be dropped,
# or a 16 minute move gets scored as a 60 second one and flatters the result.
assert find_exit(ts_, 10, 60) is None
# The end of the data is also a drop, never a guess.
assert find_exit(ts_, len(ts_) - 1, 10) is None
print("gap window tests passed")

# ---- candle backfill ----
from scalper.analyze import valid_quote, candle_windows
from scalper.backfill import parse_candle

# A real API candle, as served (dollar strings, nested yes_bid and yes_ask).
api_candle = {"end_period_ts": 1791209820, "open_interest_fp": "145952.68", "volume_fp": "135875.16",
              "price": {"close_dollars": "0.5100"},
              "yes_ask": {"open_dollars": "0.3600", "high_dollars": "0.6000", "low_dollars": "0.3000", "close_dollars": "0.5200"},
              "yes_bid": {"open_dollars": "0.3500", "high_dollars": "0.5900", "low_dollars": "0.2900", "close_dollars": "0.5100"}}
row = parse_candle(api_candle, "T", "S")
assert row[2] == 1791209820 and row[6] == 0.51 and row[10] == 0.52 and row[11] == 0.51
# A candle with no book fields parses to None values, never to zero (a fake free quote).
bare = parse_candle({"end_period_ts": 60, "price": {}}, "T", "S")
assert bare[6] is None and bare[10] is None
assert parse_candle({"price": {}}, "T", "S") is None

# An empty book at market open (bid 0.1c, ask $1) is not a tradable quote.
assert not valid_quote(0.001, 1.0)
assert not valid_quote(None, 0.5) and not valid_quote(0.5, None)
assert not valid_quote(0.40, 0.60)          # 20c wide: not a market
assert valid_quote(0.47, 0.49) and valid_quote(0.001, 0.01)  # a real far-from-50 book is fine

# Windows: entry at one close, exit exactly 60s later, never bridged.
cs = [(60 * k, 0.40 + 0.01 * k, 0.42 + 0.01 * k) for k in range(1, 6)]
recs, dropped = candle_windows("S", 900, cs)
assert len([r for r in recs if r[1] == 60]) == 4 and len([r for r in recs if r[1] == 120]) == 3
first = [r for r in recs if r[1] == 60][0]
assert abs(first[5] - 0.01) < 1e-9 and first[3] == 900 - 60 and first[4] > 0.02
# A missing minute must not be bridged: removing k=3 kills every window across it.
holey = [c for c in cs if c[0] != 180]
r2, _ = candle_windows("S", 900, holey)
assert all(not (r[6] < 180 < r[6] + r[1]) for r in r2 if r[1] == 60), "a 60s hold spans the missing minute"
assert len([r for r in r2 if r[1] == 60]) == 2
# Every hold ends exactly N seconds after it starts, on a candle that exists.
ends = {c[0] for c in holey}
assert all(int(r[6]) + r[1] in ends for r in r2)
# An unusable placeholder quote drops its windows and is counted, not scored.
junk = [(60, 0.001, 1.0)] + cs[1:]
r3, d3 = candle_windows("S", 900, junk)
assert d3 >= 1 and all(r[6] != 60 for r in r3)
print("candle backfill tests passed")

# ---- rate limits are waited out, not fatal ----
import io, json as _json, urllib.error as _ue
import scalper.api as _api
_waits = []
_orig_sleep, _orig_open = _api.time.sleep, _api.urllib.request.urlopen
_calls = {"n": 0}
class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def _fake_open(url, timeout=0):
    _calls["n"] += 1
    if _calls["n"] <= 3:   # three 429s in a row, as a long pull can see
        raise _ue.HTTPError(url, 429, "Too Many Requests", {"Retry-After": "2"}, None)
    return _Resp(_json.dumps({"ok": True}).encode())
_api.time.sleep = lambda x: _waits.append(x)
_api.urllib.request.urlopen = _fake_open
try:
    # A 30 minute job must survive a burst of 429s and carry on...
    assert _api._get("/x") == {"ok": True}
    # ...waiting longer each time, never hammering.
    assert len(_waits) == 3 and _waits == sorted(_waits) and _waits[0] >= 5.0, _waits
    # A permanent failure still ends in an error, not an endless loop.
    _calls["n"] = -100
    _api.urllib.request.urlopen = lambda url, timeout=0: (_ for _ in ()).throw(_ue.HTTPError(url, 500, "x", {}, None))
    try:
        _api._get("/y", retries=2); raise SystemExit("should have failed")
    except RuntimeError:
        pass
finally:
    _api.time.sleep, _api.urllib.request.urlopen = _orig_sleep, _orig_open
print("rate limit tests passed")

# ---- calibration (hold to settlement) ----
from scalper.calibration import favourite, net_pnl, cluster_mean_z, judge, MIN_N, Z_BAR

# The favourite is bought at its ask. NO is bought at 1 minus the YES bid.
assert favourite(0.89, 0.90) == ("yes", 0.90)
b = favourite(0.08, 0.09)
assert b[0] == "no" and abs(b[1] - 0.92) < 1e-9
assert favourite(0.49, 0.51) is None             # a coin flip is not a favourite
assert favourite(0.97, 0.99) is None             # ask above the band: too little left to win
assert favourite(0.001, 1.0) is None             # an empty book is not a quote
# Profit per contract: a win pays $1 less the price and fee, a loss loses both.
fee = 0.07 * 0.90 * 0.10
assert abs(net_pnl("yes", 0.90, "yes") - (1 - 0.90 - fee)) < 1e-12
assert abs(net_pnl("yes", 0.90, "no") - (-0.90 - fee)) < 1e-12
assert net_pnl("no", 0.92, "no") > 0 > net_pnl("no", 0.92, "yes")
# A market that did not resolve yes or no is not scored at all.
assert net_pnl("yes", 0.90, "") is None and net_pnl("yes", 0.90, "void") is None
# Higher fees only ever lower profit.
assert net_pnl("yes", 0.90, "yes", 1.2) < net_pnl("yes", 0.90, "yes")

# Twenty outcomes from one day are closer to one observation than to twenty:
# the clustered error must be larger than the naive one when days differ.
obs = [("d1", 1.0)] * 20 + [("d2", -1.0)] * 20
mean, se, z = cluster_mean_z(obs)
naive = (sum((x - mean) ** 2 for _, x in obs) / (len(obs) - 1)) ** 0.5 / len(obs) ** 0.5
assert abs(mean) < 1e-12 and se > naive * 3, (se, naive)

def synth(n, edge, hi_edge=None, days=30, half_split=True):
    """n markets with a fixed net edge, spread over days; optionally a different
    edge in the second half. Alternates so the sample is not degenerate."""
    rows = []
    for i in range(n):
        day = i % days
        late = i >= n // 2
        e = (hi_edge if (late and hi_edge is not None) else edge)
        x = e + (0.05 if i % 2 else -0.05)
        rows.append((f"d{day}", float(i), x, x - 0.002))
    return rows

MID = 600.0
# A clean, consistent edge across both halves passes every criterion.
v, s = judge({10: synth(1200, 0.03)}, MID)
assert v == "NOT_YET_FALSIFIED" and s[0]["ok"], s
# No edge: falsified.
assert judge({10: synth(1200, 0.0)}, MID)[0] == "FALSIFIED"
# An edge in only one half must not qualify: with several entry times and
# several cells, one lucky half is exactly what chance produces.
assert judge({10: synth(1200, 0.03, hi_edge=-0.01)}, MID)[0] == "FALSIFIED"
# Too few markets never qualifies, however good they look.
assert judge({10: synth(MIN_N - 1, 0.20)}, MID)[0] == "FALSIFIED"
# An edge that disappears with 20% higher fees must not qualify.
rows = [(a, b, c, c - 0.05) for a, b, c, d in synth(1200, 0.03)]
assert judge({10: rows}, MID)[0] == "FALSIFIED"
# No verdict word may ever read as a go-ahead to trade.
import scalper.calibration as _c, re as _re2
_src = _re2.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_c.__file__).read())
assert not _re2.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _src)
print("calibration tests passed")
