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

# ---- path situations (exploratory) ----
from scalper.situations import first_trigger, wilson, summarise

# A side hits T on its MID. YES at 72/74c is a 73% YES; NO is the mirror.
t = first_trigger([(0.72, 0.74)], 0.70)
assert t[0] == "yes" and abs(t[1] - 0.73) < 1e-9 and t[2] == 0.74
t = first_trigger([(0.26, 0.28)], 0.70)              # YES mid 27c, so NO is 73%
assert t[0] == "no" and abs(t[1] - 0.73) < 1e-9 and abs(t[2] - 0.74) < 1e-9   # NO is bought at 1 - yes_bid
assert first_trigger([(0.49, 0.51)], 0.70) is None
# The FIRST checkpoint that qualifies is the event, even if a later one flips side.
assert first_trigger([(0.49, 0.51), (0.72, 0.74), (0.20, 0.22)], 0.70)[0] == "yes"
# An unusable quote (empty opening book, no candle) is skipped, never read as a trigger.
assert first_trigger([(0.001, 1.0), None, (0.72, 0.74)], 0.70)[0] == "yes"
assert first_trigger([(0.001, 1.0), None], 0.70) is None
# Exactly at the threshold counts; just under it does not.
assert first_trigger([(0.695, 0.705)], 0.70) is not None and first_trigger([(0.69, 0.70)], 0.70) is None

# The consequence that matters: a side priced at 70% that wins 70% of the time is
# CALIBRATED, not an edge. The gap must be zero there, however the flip rate looks.
ev = [("yes", 0.70, 0.71, i < 70, 0.0, "d%d" % (i % 10), float(i)) for i in range(100)]
s = summarise(ev)
assert abs(s["flip"] - 0.30) < 1e-9 and abs(s["gap"]) < 1e-9, s
# A flip rate of 30% against a price of 80% is a real shortfall of 10 points.
ev = [("yes", 0.80, 0.81, i < 70, 0.0, "d%d" % (i % 10), float(i)) for i in range(100)]
assert abs(summarise(ev)["gap"] + 0.10) < 1e-9
# The interval must widen when there are few events.
assert (lambda a, b: (a[1] - a[0]) > (b[1] - b[0]))(wilson(7, 10), wilson(700, 1000))
assert wilson(0, 0) == (0.0, 1.0)
lo, hi = wilson(98, 100)
assert 0.9 < lo < 0.98 < hi <= 1.0   # near 100% the interval stays inside [0,1]
print("situations tests passed")

# ---- 40c/50c to 80c scalps (hypothesis H2) ----
import random as _random
from scalper.scalps import simulate, judge as scalp_judge, fee as sfee, BANDS, MIN_N as SMIN

def cd(end, bid, ask, bh=None, al=None):
    """(end, bid_c, ask_c, bid_h, ask_l)"""
    return (end, bid, ask, bid if bh is None else bh, ask if al is None else al)

CLOSE = 900
B40 = BANDS["40c"]
# Entry at the ask of 40c, exit when the bid closes at 80c: the 80c is received,
# and the fee is paid on BOTH legs.
t = simulate([cd(60, 0.39, 0.40), cd(120, 0.80, 0.81)], CLOSE, "no", B40)
assert t["outcome"] == "target" and t["side"] == "yes"
assert abs(t["net"] - (0.80 - sfee(0.80) - 0.40 - sfee(0.40))) < 1e-12
# Never reaches 80c: held to settlement, a win pays $1 and a loss pays nothing.
nope = [cd(60, 0.39, 0.40), cd(120, 0.50, 0.51), cd(180, 0.45, 0.46)]
assert abs(simulate(nope, CLOSE, "yes", B40)["net"] - (1 - 0.40 - sfee(0.40))) < 1e-12
assert abs(simulate(nope, CLOSE, "no", B40)["net"] - (-0.40 - sfee(0.40))) < 1e-12
# The NO side is bought at 1 minus the YES bid and sold when the YES ask falls to 20c.
n = simulate([cd(60, 0.59, 0.61), cd(120, 0.18, 0.20)], CLOSE, "yes", B40)
assert n["side"] == "no" and abs(n["ask"] - 0.41) < 1e-9 and n["outcome"] == "target"
# No entry: outside the band, under 5 minutes left, or an unusable quote.
assert simulate([cd(60, 0.55, 0.57)], CLOSE, "yes", B40) is None
assert simulate([cd(CLOSE - 240, 0.39, 0.40)], CLOSE, "yes", B40) is None
assert simulate([cd(60, 0.001, 1.0)], CLOSE, "yes", B40) is None
# A market that did not resolve yes or no is not scored.
assert simulate(nope, CLOSE, "", B40) is None
# No lookahead: the entry minute's own high must never trigger the exit.
spike = [cd(60, 0.39, 0.40, bh=0.90), cd(120, 0.30, 0.31)]
assert simulate(spike, CLOSE, "no", B40, touch="high")["outcome"] == "loss"
# A stop exits at the closing bid, slippage included, never at the stop price.
st = simulate([cd(60, 0.39, 0.40), cd(120, 0.12, 0.13)], CLOSE, "no", B40, stop=0.20)
assert st["outcome"] == "stop" and abs(st["net"] - (0.12 - sfee(0.12) - 0.40 - sfee(0.40))) < 1e-12
# Fees only ever lower profit.
assert simulate([cd(60, 0.39, 0.40), cd(120, 0.80, 0.81)], CLOSE, "no", B40, fee_mult=1.2)["net"] < t["net"]

# THE test that matters. In a FAIR game (a martingale price, the result drawn with
# probability equal to the price) this strategy has zero expected profit before
# costs, so after a 2c spread and fees it must LOSE about the costs. A profit here
# would mean the simulator invents an edge (an optimistic fill, a lookahead).
rng = _random.Random(7)
def fair_market():
    p, cs = 0.5, []
    for k in range(1, 15):
        if 0.02 < p < 0.98:
            p = min(0.98, max(0.02, p + rng.choice((-0.06, 0.06))))
        cs.append(cd(60 * k, round(p - 0.01, 4), round(p + 0.01, 4)))
    return cs, ("yes" if rng.random() < p else "no")
nets = {"40c": [], "50c": []}
for _ in range(20000):
    cs, res = fair_market()
    for b in nets:
        r = simulate(cs, CLOSE, res, BANDS[b])
        if r:
            nets[b].append(r["net"])
for b, v in nets.items():
    m = sum(v) / len(v)
    assert -0.10 < m < -0.01, (b, m, len(v))   # loses roughly the costs, never wins
# Verdict logic, as for H1: a clean edge passes, one lucky half or too few markets does not.
def rows(n, edge, edge2=None):
    return {"40c": [("d%d" % (i % 30), float(i), (edge2 if (edge2 is not None and i >= n // 2) else edge) + (0.1 if i % 2 else -0.1),
                     (edge2 if (edge2 is not None and i >= n // 2) else edge) - 0.003 + (0.1 if i % 2 else -0.1)) for i in range(n)]}
assert scalp_judge(rows(1200, 0.04), 600.0)[0] == "NOT_YET_FALSIFIED"
assert scalp_judge(rows(1200, 0.0), 600.0)[0] == "FALSIFIED"
assert scalp_judge(rows(1200, 0.04, edge2=-0.02), 600.0)[0] == "FALSIFIED"
assert scalp_judge(rows(SMIN - 1, 0.30), 600.0)[0] == "FALSIFIED"
import scalper.scalps as _sc, re as _re3
_s = _re3.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_sc.__file__).read())
assert not _re3.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _s)
print("scalp tests passed")

# ---- the paper bot ----
import tempfile as _tf
from datetime import datetime as _dt, timezone as _tz
from pathlib import Path as _P
from scalper.limits import tier_state
from scalper.bot import PaperBot, size_for, position_id

NOON = _dt(2026, 10, 5, 12, 0, 0).timestamp()      # local noon, so a local-day boundary never interferes
def at(h, m=0): return _dt(2026, 10, 5, h, m, 0).timestamp()
def iso(ts): return _dt.fromtimestamp(ts, _tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- limits: the SAME cases as the web page's tests (kalshiMonitorGates G13 to G17) ---
cl = lambda pnl, t: (t, pnl)
t = tier_state([], 300, at(12))
assert t["mode"] == "ok" and t["cap"] == 3 and t["soft_limit"] == 9 and t["hard_limit"] == 15
two = [cl(-5, at(9)), cl(-5, at(10))]
assert tier_state(two, 300, at(11, 59))["mode"] == "break" and tier_state(two, 300, at(11, 59))["cap"] == 0
after = tier_state(two, 300, at(12, 1))
assert after["mode"] == "half" and after["cap"] == 1.5
# a later win does not end the break early
assert tier_state(two + [cl(8, at(10, 30))], 300, at(11)) ["mode"] == "break"
# the hard stop is sticky, even after a recovery
assert tier_state([cl(-16, at(9)), cl(20, at(9, 30))], 300, at(14))["mode"] == "done"
# yesterday's loss does not carry over
assert tier_state([cl(-20, at(12) - 86400)], 300, at(12))["mode"] == "ok"
# no bankroll means no trading, never an unlimited cap
assert tier_state([], 0, at(12))["mode"] == "done" and tier_state([], "", at(12))["mode"] == "done"

# --- sizing: cost INCLUDING the fee must fit the cap ---
assert size_for(0.40, 3.0, None) == 7              # 7 x 40c = $2.80 + 12c fee = $2.92; 8 would be $3.35
assert size_for(0.42, 3.0, None) == 6             # 7 x 42c = $2.94 fits, but the 12c fee makes $3.06: the fee counts
assert size_for(0.40, 3.0, 3) == 3                 # never more than the touch can fill
assert size_for(0.40, 0.30, None) == 0             # a cap too small for one contract means no trade
assert size_for(1.2, 3.0, None) == 0 and size_for(0.4, 0, None) == 0

# --- a scripted Kalshi ---
class FakeApi:
    def __init__(self): self.mk, self.result, self.active, self.fail, self.fail_series = {}, {}, True, False, set()
    def exchange_status(self):
        if self.fail: raise RuntimeError("exchange down")
        return {"trading_active": self.active}
    def markets(self, series, status="open", limit=20):
        if self.fail or series in self.fail_series: raise RuntimeError("markets down")
        return [m for m in self.mk.get(series, [])]
    def market(self, ticker):
        self.market_calls = getattr(self, "market_calls", 0) + 1
        return {"result": self.result.get(ticker, "")}
    def put(self, ticker, bid, ask, close_ts, series="KXBTC15M", ask_sz=100, bid_sz=100, status="active"):
        self.mk[series] = [m for m in self.mk.get(series, []) if m["ticker"] != ticker] + [{
            "ticker": ticker, "status": status, "close_time": iso(close_ts),
            "yes_bid_dollars": f"{bid:.4f}", "yes_ask_dollars": f"{ask:.4f}",
            "yes_ask_size_fp": str(ask_sz), "yes_bid_size_fp": str(bid_sz)}]

def make(bankroll=300.0, start=NOON):
    d = _P(_tf.mkdtemp())
    clock = {"t": start}
    api = FakeApi()
    bot = PaperBot(api, d / "bot.sqlite", bankroll, lambda: clock["t"], d / "KILL")
    return bot, api, clock, d

CLOSE = NOON + 900                                   # a market 15 minutes from now
# It refuses to be anything but a paper bot.
try:
    PaperBot(FakeApi(), _P(_tf.mkdtemp()) / "x.sqlite", mode="live"); raise SystemExit("live mode must be refused")
except ValueError:
    pass

# Entry at the ask in the 40c band, sized from the $3 cap, then the 80c exit on a LATER tick.
bot, api, clock, d = make()
api.put("M1", 0.39, 0.40, CLOSE)
bot.tick()
p = bot.db.execute("SELECT side,band,contracts,entry,status FROM position").fetchall()
assert p == [("yes", "40c", 7, 0.40, "open")], p
clock["t"] += 5; api.put("M1", 0.81, 0.82, CLOSE); bot.tick()
r = bot.db.execute("SELECT status,exit,pnl FROM position").fetchone()
want = round(0.80 * 7 - taker_fee(0.80, 7) - 0.40 * 7 - taker_fee(0.40, 7), 2)
assert r == ("closed", 0.8, want), (r, want)
# After a closed trade the same market is never re-entered (the id is taken).
clock["t"] += 5; api.put("M1", 0.39, 0.40, CLOSE); bot.tick()
assert bot.db.execute("SELECT COUNT(*) FROM position").fetchone()[0] == 1
# ...and the closed trade must be untouched, not quietly reopened by a replace.
assert bot.db.execute("SELECT status,pnl FROM position").fetchone() == ("closed", want)
assert bot.db.execute("SELECT COUNT(*) FROM event WHERE kind='entry'").fetchone()[0] == 1

# THE incident, in miniature: two copies of the bot, or a restart, must not enter
# the same market twice. The key is derived from the market, not generated per call.
bot, api, clock, d = make()
api.put("M2", 0.39, 0.40, CLOSE)
bot.tick(); bot.tick()
bot2 = PaperBot(api, d / "bot.sqlite", 300.0, lambda: clock["t"], d / "KILL")   # a second process, same database
bot2.tick()
assert bot.db.execute("SELECT COUNT(*) FROM position").fetchone()[0] == 1
assert bot.db.execute("SELECT COUNT(*) FROM event WHERE kind='entry'").fetchone()[0] == 1, "a second process must not log a second entry"
assert position_id("M2") == "h2-M2"

# Never exit at the very timestamp of the entry, even if the quote then jumps
# (a restart at the same instant must not turn into a free instant profit).
bot, api, clock, d = make()
api.put("M7", 0.39, 0.40, CLOSE); bot.tick()
api.put("M7", 0.85, 0.86, CLOSE); bot.tick()                 # same clock value
assert bot.db.execute("SELECT status FROM position").fetchone()[0] == "open"
clock["t"] += 5; bot.tick()
assert bot.db.execute("SELECT status FROM position").fetchone()[0] == "closed"

# The NO side is bought at 1 minus the YES bid.
bot, api, clock, d = make()
api.put("M3", 0.59, 0.61, CLOSE)
bot.tick()
s = bot.db.execute("SELECT side,entry FROM position").fetchone()
assert s[0] == "no" and abs(s[1] - 0.41) < 1e-9
# ...and is sold when the YES ask falls to 20c (NO bid 80c).
clock["t"] += 5; api.put("M3", 0.18, 0.20, CLOSE); bot.tick()
assert bot.db.execute("SELECT status FROM position").fetchone()[0] == "closed"

# Held to settlement: a loss costs the entry plus the fee, a win pays $1 a contract.
bot, api, clock, d = make()
api.put("M4", 0.39, 0.40, CLOSE); bot.tick()
clock["t"] = CLOSE + 60; api.mk = {}; api.result["M4"] = "no"; bot.tick()
assert bot.db.execute("SELECT status,pnl FROM position").fetchone() == ("closed", round(-0.40 * 7 - taker_fee(0.40, 7), 2))
bot, api, clock, d = make()
api.put("M5", 0.39, 0.40, CLOSE); bot.tick()
clock["t"] = CLOSE + 60; api.mk = {}; api.result["M5"] = "yes"; bot.tick()
assert bot.db.execute("SELECT pnl FROM position").fetchone()[0] == round(7 - 0.40 * 7 - taker_fee(0.40, 7), 2)
# Before the market closes the bot must not even ask for a result: a position is
# not settled early, and asking for every open position on every tick wastes the
# request budget.
bot, api, clock, d = make()
api.put("M8", 0.39, 0.40, CLOSE); bot.tick()
clock["t"] += 5; bot.tick(); clock["t"] += 5; bot.tick()
assert getattr(api, "market_calls", 0) == 0, "no result lookups before the close"
# A result that is not final yet leaves the position open, to be asked again.
bot, api, clock, d = make()
api.put("M6", 0.39, 0.40, CLOSE); bot.tick()
clock["t"] = CLOSE + 60; api.mk = {}; bot.tick()
assert bot.db.execute("SELECT status FROM position").fetchone()[0] == "open"

# --- the safety rules ---
def entered(bot): return bot.db.execute("SELECT COUNT(*) FROM position").fetchone()[0]
bot, api, clock, d = make(); (d / "KILL").write_text("stop"); api.put("A", 0.39, 0.40, CLOSE); bot.tick()
assert entered(bot) == 0, "the kill switch must stop new entries"
# ...but it must NOT freeze a position that is already open: that is the dangerous act.
bot, api, clock, d = make(); api.put("B", 0.39, 0.40, CLOSE); bot.tick()
(d / "KILL").write_text("stop"); clock["t"] += 5; api.put("B", 0.81, 0.82, CLOSE); bot.tick()
assert bot.db.execute("SELECT status FROM position").fetchone()[0] == "closed", "exits must carry on under the kill switch"
bot, api, clock, d = make(); api.active = False; api.put("A", 0.39, 0.40, CLOSE); bot.tick()
assert entered(bot) == 0, "an inactive exchange means no entry"
bot, api, clock, d = make(); api.fail = True; bot.tick()          # prices unreadable: no crash, no entry
assert entered(bot) == 0 and bot.db.execute("SELECT COUNT(*) FROM event WHERE kind='error'").fetchone()[0] == 1
bot, api, clock, d = make(); api.fail_series = {"KXGOLD15M"}; api.put("A", 0.39, 0.40, CLOSE); bot.tick()
assert entered(bot) == 0, "a partly unreadable feed must fail closed, even for the part that was readable"
bot, api, clock, d = make(bankroll=0); api.put("A", 0.39, 0.40, CLOSE); bot.tick()
assert entered(bot) == 0, "no bankroll must fail closed"
bot, api, clock, d = make(); api.put("A", 0.39, 0.40, NOON + 240); bot.tick()
assert entered(bot) == 0, "under 5 minutes left is no entry"
bot, api, clock, d = make(); api.put("A", 0.30, 0.55, CLOSE); api.put("B", 0.45, 0.46, CLOSE, status="finalized"); bot.tick()
assert entered(bot) == 0, "a wide book and a closed market are not entries"
bot, api, clock, d = make(); api.put("A", 0.39, 0.40, CLOSE, ask_sz=2); bot.tick()
assert bot.db.execute("SELECT contracts FROM position").fetchone()[0] == 2, "never more than the touch shows"
# A hard stop: after enough losses today the bot takes no new entry, and reports why once.
bot, api, clock, d = make()
for i in range(3):
    bot.db.execute("INSERT INTO position VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (f"x{i}", f"X{i}", "S", "yes", "40c", 7, .4, .12, at(9), at(9, 15), "closed", 0, None, at(9, 15), -6.0, at(9, 15) + i, "paper"))
bot.db.commit()
api.put("A", 0.39, 0.40, CLOSE); bot.tick(); bot.tick()
assert entered(bot) == 3 and bot.db.execute("SELECT COUNT(*) FROM event WHERE kind='block'").fetchone()[0] == 1
assert bot.summary()["limits"]["mode"] == "done"
# The outside watchdog: pinged at most once a minute, only on a healthy tick, and a
# failing ping must never stop or change a tick.
pings = []
bot, api, clock, d = make(); bot.pinger = lambda: pings.append(clock["t"])
api.put("P", 0.39, 0.40, CLOSE)
for _ in range(5):
    bot.tick(); clock["t"] += 5
assert len(pings) == 1, "one ping a minute, not one per tick"
clock["t"] += 60; bot.tick()
assert len(pings) == 2
api.fail = True; clock["t"] += 120; bot.tick()
assert len(pings) == 2, "silence on an unhealthy tick is what makes the watchdog alarm"
api.fail = False; bot.pinger = lambda: (_ for _ in ()).throw(RuntimeError("watchdog down")); clock["t"] += 120
bot.tick()                                         # must not raise
assert entered(bot) >= 1
# The owner's starting capital is $100: $1 a trade, a break at -$3, done at -$5.
from scalper.bot import DEFAULT_BANKROLL
assert DEFAULT_BANKROLL == 100.0
t100 = tier_state([], DEFAULT_BANKROLL, at(12))
assert (t100["cap"], t100["soft_limit"], t100["hard_limit"]) == (1.0, 3.0, 5.0)
# No verdict or order code: this file must contain no way to place an order.
import scalper.bot as _b, re as _re4
_code = _re4.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_b.__file__).read())
assert not _re4.search(r"/orders|create_order|place_order|private_key|api_key", _code, _re4.I)
print("paper bot tests passed")

# ---- bot status ----
from scalper.botstatus import report, health
assert health(None) == "NEVER RAN" and health(5) == "OK" and health(60) == "STALE" and health(500) == "DOWN"
bot, api, clock, d = make(bankroll=100.0)
api.put("S1", 0.39, 0.40, CLOSE); bot.tick()
rep = report(d / "bot.sqlite", now=clock["t"] + 3)
assert "Bot: OK" in rep and "PAPER" in rep and "Bankroll $100.00" in rep and "$1.00 a trade" in rep
assert "Open positions: 1" in rep and "S1" in rep, rep
# A bot that has stopped must read as DOWN, not as a stale "everything fine".
assert "Bot: DOWN" in report(d / "bot.sqlite", now=clock["t"] + 600)
assert "No bot database" in report(d / "missing.sqlite")
print("bot status tests passed")

# ---- the bot as a background job ----
from scalper.service import build_plist as _bp, JOBS
pb = _bp("bot")
assert pb["Label"] == "com.shwoop.kalshi-bot" and pb["KeepAlive"] is True and pb["RunAtLoad"] is True
assert pb["ProgramArguments"][-3:] == ["scalper.bot", "--bankroll", "100"], pb["ProgramArguments"]
# The two jobs must never share a label, or installing one would replace the other.
assert JOBS["bot"][0] != JOBS["recorder"][0] and _bp()["Label"] == "com.shwoop.kalshi-recorder"
# Nothing the service runs may be anything but the paper bot: no live flag exists.
assert not any("live" in a.lower() for a in pb["ProgramArguments"])
print("bot service tests passed")
