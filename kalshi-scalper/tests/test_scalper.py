"""Plain assert tests; run with: python tests/test_scalper.py
Each states a consequence, not a mechanism."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper.fees import taker_fee, round_trip_cost




# A scalp exiting early pays fees twice, so it must cost more than the same
# trade held to settlement (one fee). If this ever flips, the model is wrong.
assert round_trip_cost(0.50, 0.50) >= 2 * taker_fee(0.50) - 1e-9
# Fees are cheapest at the extremes and dearest at 50c: that is where scalps are viable.
assert taker_fee(0.95, 100) < taker_fee(0.50, 100)
# Crossing a 2c spread at 50c can never be break-even on a flat market.
assert round_trip_cost(0.51, 0.49) > 0.02
print("fee tests passed")

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
# ---- H4: the same rule from a 30c entry ----
from scalper.bandscan import H4_BAND, INFO_BANDS, rows_for as _h4_rows
# The band is exactly what the README fixed, and H2's own bands (and so the paper bot's) are untouched.
assert H4_BAND == ("30c", (0.28, 0.32)) and set(BANDS) == {"40c", "50c"} and BANDS["40c"] == (0.38, 0.42)
assert INFO_BANDS["40c"] == BANDS["40c"] and INFO_BANDS["50c"] == BANDS["50c"]
# From 30c the NO side is bought at 1 minus the YES bid: a YES bid of 0.69 is a NO ask of 0.31.
t30 = simulate([cd(60, 0.28, 0.30), cd(120, 0.80, 0.81)], CLOSE, "no", H4_BAND[1])
assert t30["side"] == "yes" and t30["outcome"] == "target" and abs(t30["net"] - (0.80 - sfee(0.80) - 0.30 - sfee(0.30))) < 1e-12
n30 = simulate([cd(60, 0.69, 0.71), cd(120, 0.18, 0.20)], CLOSE, "yes", H4_BAND[1])
assert n30["side"] == "no" and abs(n30["ask"] - 0.31) < 1e-9
# Outside 28c to 32c there is no entry, so a 40c market is not a 30c trade.
assert simulate([cd(60, 0.39, 0.40)], CLOSE, "yes", H4_BAND[1]) is None
# THE test that matters, for this band: in a FAIR game it must lose about the costs, never win.
rng30 = _random.Random(11)
def fair_market30():
    p, cs = 0.5, []
    for k in range(1, 15):
        p = min(0.98, max(0.02, p + rng30.choice((-0.05, 0.05))))   # 5c steps land exactly on 30c
        cs.append(cd(60 * k, round(p - 0.01, 4), round(p + 0.01, 4)))
    return cs, ("yes" if rng30.random() < p else "no")
v30 = []
for _ in range(30000):
    cs, res = fair_market30()
    r = simulate(cs, CLOSE, res, H4_BAND[1])
    if r:
        v30.append(r["net"])
m30 = sum(v30) / len(v30)
assert len(v30) > 3000 and -0.10 < m30 < -0.01, (m30, len(v30))
# A rigged market that really does continue from 30c (it reaches 80c more often than a fair game) must show a profit,
# so a pass is possible and the test is not one that always says no.
def trend_market():
    return [cd(60, 0.29, 0.30), cd(120, 0.80, 0.81)], "yes"
r = [simulate(*((lambda cs, res: (cs, CLOSE, res, H4_BAND[1]))(*trend_market()))) for _ in range(5)]
assert all(x and x["net"] > 0.4 for x in r)
import scalper.bandscan as _bs, re as _re8
assert not _re8.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _re8.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_bs.__file__).read()))
print("scalp tests passed")

# ---- spot lag study (exploratory) ----
import math as _m
import random as _rd
from scalper.leadlag import ols_clustered, build_rows, report, verdict, decile_move, usable as _usable
from scalper.spot import parse_rows

# Coinbase lists newest first with the close in column 4; we keep (start, close), oldest first.
assert parse_rows([[120, 1, 2, 3, 40.5, 9], [60, 1, 2, 3, 30.0, 9], ["bad"]]) == [(60, 30.0), (120, 40.5)]

# The estimator must recover a known relationship, or every number below is noise.
_rd.seed(7)
_rows = []
for _d in range(20):
    for _ in range(30):
        _x = [1.0, _rd.gauss(0, 1), _rd.gauss(0, 1)]
        _rows.append((str(_d), _x, 2.0 + 3.0 * _x[1] - 1.0 * _x[2] + _rd.gauss(0, 0.1)))
_b, _s = ols_clustered(_rows)
assert abs(_b[0] - 2) < 0.05 and abs(_b[1] - 3) < 0.05 and abs(_b[2] + 1) < 0.05, _b
assert all(0 < s < 0.1 for s in _s), _s

GAIN = 30.0   # dollars of Kalshi mid per unit log return: a 0.06% move is 1.8c, well inside the 35c to 65c clamp

def _world(lag_share, n_markets=240, seed=11):
    """Synthetic Bitcoin and Kalshi where Kalshi's minute move is a known blend of this
    minute's spot move and last minute's. lag_share = 0 is a market with no lag."""
    rng = _rd.Random(seed)
    spot, markets = {}, {}
    t0, price = 1_700_000_000 - 1_700_000_000 % 60, 60000.0
    rets = {}
    for i in range(n_markets * 15 + 40):
        r = rng.gauss(0, 0.0006)
        price *= _m.exp(r)
        spot[t0 + i * 60] = price          # candle STARTING at t0+i*60, closes a minute later
        rets[t0 + (i + 1) * 60] = r        # the return that ENDS at that instant
    for m in range(n_markets):
        open_ts = t0 + (m * 15 + 20) * 60
        close_ts = open_ts + 900
        mid, cs = 0.5, []
        for k in range(1, 16):
            end = open_ts + k * 60
            cs.append((end, mid - 0.01, mid + 0.01))
            mid += GAIN * ((1 - lag_share) * rets[end + 60] + lag_share * rets[end]) + rng.gauss(0, 0.002)
            mid = min(max(mid, 0.35), 0.65)
        markets[f"M{m}"] = (open_ts, close_ts, cs)
    return markets, spot

# No lag in the world: the lag coefficient must come out near zero and the bar must say no.
_mk, _sp = _world(0.0)
_rows2, _drop = build_rows(_mk, _sp)
_rep = report(_rows2)
assert _rep["beta"][1] > 0 and abs(_rep["beta"][2]) < 0.15 * _rep["beta"][1], _rep["beta"]
assert verdict(_rep, 0.0)[0] is False
# A full minute of lag in the world: it must be found, in the right slot, in both halves.
_mk, _sp = _world(1.0)
_rows3, _ = build_rows(_mk, _sp)
_rep3 = report(_rows3)
assert _rep3["beta"][2] > 0.6 * GAIN and abs(_rep3["beta"][1]) < 0.1 * GAIN, _rep3["beta"]
assert all(hb[2] / hs[2] > 3 for hb, hs in _rep3["halves"])
# A quarter blend is found as a third of the contemporaneous effect (0.25 / 0.75): the ratio is what the bar reads.
_mk, _sp = _world(0.25)
_rep4 = report(build_rows(_mk, _sp)[0])
assert 0.27 < _rep4["beta"][2] / _rep4["beta"][1] < 0.40, _rep4["beta"]
# A minute with no spot price is dropped, never bridged across.
_mk, _sp = _world(0.0, n_markets=20)
_full, _ = build_rows(_mk, _sp)
for _k in list(_sp)[40:60]:
    del _sp[_k]
_cut, _dropped = build_rows(_mk, _sp)
assert _dropped > 0 and len(_cut) < len(_full)
# The signal must be known at the time: a spot move only AFTER the quote cannot be the lag term.
assert _usable(0.49, 0.51) and not _usable(0.001, 0.999) and not _usable(0.40, 0.55)
# The decile read is in dollars per contract in the direction of the spot move.
_mv, _n = decile_move([("d", 0, [], 0.05, 0.01), ("d", 0, [], -0.05, -0.01)] * 20)
assert abs(_mv - 0.05) < 1e-12 and _n >= 1
# No output of the study may read as a go-ahead to trade.
import scalper.leadlag as _ll, re as _re5
_c = _re5.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_ll.__file__).read())
assert not _re5.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _c)
print("spot lag tests passed")

# ---- H3: resting orders ----
import random as _rd2
from scalper.makers import plan, filled, net as _net, orders_for, verdict as _mverdict, mean as _mmean, BANDS as _MB
from scalper.tape import parse_ts, parse_trade

# The order is the FIRST usable minute with 5+ minutes left, YES bid before NO bid, one per band.
_cs = [(100, 0.001, 0.999), (160, 0.30, 0.34), (220, 0.40, 0.42), (280, 0.39, 0.41)]
assert plan(_cs, 100 + 900, (0.38, 0.42)) == (220, "yes", 0.40, 0.42), "an unusable quote and an out of band minute are skipped"
assert plan(_cs, 220 + 200, (0.38, 0.42)) is None, "under 5 minutes left: no order"
_no = [(100, 0.56, 0.58)]   # YES bid 0.56 is out of band, NO bid is 1 - 0.58 = 0.42
assert plan(_no, 100 + 900, (0.38, 0.42)) == (100, "no", 0.42, 0.44)

# A resting bid is filled only when the tape prints strictly THROUGH it, on our side, after it, inside the window.
_o = (1000, "yes", 0.40, 0.42)
assert filled(_o, [(1030, "no", 0.39, 0.61)])
assert not filled(_o, [(1030, "no", 0.40, 0.60)]), "a print AT our price does not count: our queue place is unknown"
assert filled(_o, [(1030, "no", 0.40, 0.60)], strict=False), "but it does in the optimistic count"
assert not filled(_o, [(1030, "yes", 0.39, 0.61)]), "a taker buying YES hits the asks, not our bid"
assert not filled(_o, [(1000, "no", 0.30, 0.70)]), "a print at the order minute is not after the order"
assert not filled(_o, [(1121, "no", 0.30, 0.70)]) and filled(_o, [(1121, "no", 0.30, 0.70)], window=300)
_on = (1000, "no", 0.42, 0.44)
assert filled(_on, [(1030, "yes", 0.60, 0.41)]) and not filled(_on, [(1030, "no", 0.60, 0.41)])

# Tape timestamps carry any number of fraction digits.
assert abs(parse_ts("2026-10-05T09:59:59.95576Z") - parse_ts("2026-10-05T09:59:59Z") - 0.95576) < 1e-6
assert parse_trade({"trade_id": "x", "ticker": "T", "created_time": "2026-10-05T09:59:59.5Z", "taker_side": "no",
                    "yes_price_dollars": "0.9990", "no_price_dollars": "0.0010", "count_fp": "75.00"})[3:] == ("no", 0.999, 0.001, 75.0)
assert parse_trade({"ticker": "T"}) is None

def _h3_world(p_win, fill_when, n=1200, seed=3, days=20, edge_first_half_only=False):
    """Synthetic markets: a 40c bid, ask 42c, one order each. fill_when(won) says whether the tape
    prints through our bid. p_win is the true chance the side wins."""
    rng = _rd2.Random(seed)
    markets, results = [], {}
    base = 1_790_000_000 - 1_790_000_000 % 86400
    for i in range(n):
        d = i * days // n
        close_ts = base + d * 86400 + (i % 90) * 900 + 900
        end = close_ts - 780
        pw = p_win(d) if callable(p_win) else p_win
        won = rng.random() < pw
        t = f"T{i}"
        markets.append((t, "KXBTC15M", [(end, 0.40, 0.42)], close_ts, "yes" if won else "no"))
        tape = [(end + 30, "no", 0.39, 0.61)] if fill_when(won, rng) else []
        o = plan([(end, 0.40, 0.42)], close_ts, _MB["40c"])
        # exactly what tape.py stores for the order: flags computed from the window's trades
        results[(t, end)] = (filled(o, tape), filled(o, tape, strict=False), filled(o, tape, 300), o[1], o[2])
    return markets, results

# A FAIR game (the side wins as often as its price says, fills unrelated to the outcome) must lose about the
# fee less the half spread it earns, never make money: the simulator invents no edge.
_m, _r = _h3_world(0.41, lambda won, r: r.random() < 0.4, n=6000)
_rows = orders_for(_m, _r)["40c"]
_fm = _mmean([r["net"] for r in _rows if r["fill"]])
assert _fm < 0 and abs(_fm - (0.41 - 0.40 - 0.07 * 0.4 * 0.6)) < 0.02, _fm
assert abs(sum(r["fill"] for r in _rows) / len(_rows) - 0.4) < 0.03

# ADVERSE SELECTION: fills happen when the side is about to lose. Filled orders lose, the missed ones would
# have won: that gap is the selection check the verdict is printed beside.
_m, _r = _h3_world(0.41, lambda won, r: (not won) and r.random() < 0.8, n=4000)
_rows = orders_for(_m, _r)["40c"]
_filled = _mmean([r["net"] for r in _rows if r["fill"]]); _missed = _mmean([r["net"] for r in _rows if not r["fill"]])
assert _filled < -0.4 and _missed > _filled + 0.3, (_filled, _missed)

# An order whose tape window was never fetched is not an order with no fills: it is left out.
_m, _r = _h3_world(0.41, lambda won, r: True, n=100)
assert len(orders_for(_m, {})["40c"]) == 0 and len(orders_for(_m, _r)["40c"]) == 100
# A window recorded for a different side or price than today's plan is not this order's window.
_k = next(iter(_r)); _bad = dict(_r); _bad[_k] = _r[_k][:3] + ("no", _r[_k][4])
assert len(orders_for(_m, _bad)["40c"]) == 99

# The kill criteria: too few fills is NOT_ENOUGH_DATA, a real edge in both halves passes, one lucky half does not.
_m, _r = _h3_world(0.41, lambda won, r: r.random() < 0.4, n=500)
assert _mverdict(orders_for(_m, _r), 1_790_000_000 + 10 * 86400)[0] == "NOT_ENOUGH_DATA"
_mid = 1_790_000_000 - 1_790_000_000 % 86400 + 10 * 86400
_m, _r = _h3_world(0.62, lambda won, r: r.random() < 0.5, n=3000)
assert _mverdict(orders_for(_m, _r), _mid)[0] == "NOT_YET_FALSIFIED"
_m, _r = _h3_world(lambda d: 0.65 if d < 10 else 0.30, lambda won, r: r.random() < 0.5, n=3000)
assert _mverdict(orders_for(_m, _r), _mid)[0] == "FALSIFIED", "an edge in only one half of the period must not pass"

# The fetcher stores the right flags, one row per order, and a rerun fetches nothing already done.
import sqlite3 as _sq, tempfile as _tf2, os as _os
import scalper.tape as _tp
_tmp = _os.path.join(_tf2.mkdtemp(), "t.sqlite")
_d = _sq.connect(_tmp)
_d.executescript("CREATE TABLE market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);"
                 "CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY (ticker, end_ts));")
for _i, _t in enumerate(("A", "B")):
    _d.execute("INSERT INTO market VALUES(?,?,?,?,?,?,?)", (_t, "KXBTC15M", 0, 5000 + _i * 10000, "yes", None, 1))
    _d.execute("INSERT INTO candle(ticker, series, end_ts, bid_c, ask_c) VALUES(?,?,?,?,?)", (_t, "KXBTC15M", 4000 + _i * 10000 - 3000, 0.40, 0.42))
_d.commit(); _d.close()
_calls = []
def _fake(ticker, end_ts):
    _calls.append(ticker)
    # A fills through a YES bid of 0.40 at 30s; B prints only AT 0.40 (not through) at 30s and through at 200s
    return [("1", ticker, end_ts + 30, "no", 0.39 if ticker == "A" else 0.40, 0.6, 5.0)] + ([("2", ticker, end_ts + 200, "no", 0.35, 0.65, 5.0)] if ticker == "B" else [])
_orig_db, _orig_fetch = _tp.DB, _tp.fetch_window
_tp.DB, _tp.fetch_window = _tmp, _fake
try:
    _tp.run(None)
    _got = {r[0]: r[1:] for r in _sq.connect(_tmp).execute("SELECT ticker, fill, fill_opt, fill5, side, price, n_trades FROM fills")}
    assert _got["A"] == (1, 1, 1, "yes", 0.40, 1), _got
    assert _got["B"] == (0, 1, 1, "yes", 0.40, 2), _got      # not through in 2 min, an AT-price print counts only optimistically, through by 5 min
    _n = len(_calls)
    _tp.run(None)
    assert len(_calls) == _n == 2, "a rerun must not fetch an order that is already stored"
finally:
    _tp.DB, _tp.fetch_window = _orig_db, _orig_fetch

# No output of the study may read as a go-ahead to trade.
import scalper.makers as _mk, re as _re6
_c2 = _re6.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_mk.__file__).read())
assert not _re6.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _c2)
print("resting order tests passed")

# ---- Kalshi demo trading ----
try:
    import cryptography  # noqa: F401
    _HAVE_CRYPTO = True
except ImportError:
    _HAVE_CRYPTO = False
    print("demo trading tests skipped: pip3 install cryptography to run them")

if _HAVE_CRYPTO:
    import base64 as _b64, io as _io, json as _json, os as _os2, tempfile as _tf3, urllib.request as _ur, urllib.error as _ue, contextlib as _cl
    from cryptography.hazmat.primitives import hashes as _h, serialization as _ser
    from cryptography.hazmat.primitives.asymmetric import padding as _pad, rsa as _rsa
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey as _Ed
    from cryptography.exceptions import InvalidSignature as _Bad
    import scalper.demo as _dm

    _rk = _rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _pss = _pad.PSS(mgf=_pad.MGF1(_h.SHA256()), salt_length=_pad.PSS.DIGEST_LENGTH)

    # The signature must verify against the public key over timestamp + METHOD + path, query stripped.
    _sig = _b64.b64decode(_dm.sign_request(_rk, "1703123456789", "GET", "/trade-api/v2/portfolio/balance?limit=5"))
    _rk.public_key().verify(_sig, b"1703123456789GET/trade-api/v2/portfolio/balance", _pss, _h.SHA256())
    for _wrong in (b"1703123456789POST/trade-api/v2/portfolio/balance", b"1703123456790GET/trade-api/v2/portfolio/balance",
                   b"1703123456789GET/portfolio/balance", b"1703123456789GET/trade-api/v2/portfolio/balance?limit=5"):
        try:
            _rk.public_key().verify(_sig, _wrong, _pss, _h.SHA256())
            raise AssertionError("a signature over a different message must not verify: %r" % _wrong)
        except _Bad:
            pass
    _ek = _Ed.generate()
    _ek.public_key().verify(_b64.b64decode(_dm.sign_request(_ek, "1", "GET", "/x")), b"1GET/x")

    # Demo only: no other host is ever contacted, whatever the base is set to.
    for _bad in ("https://external-api.kalshi.com/trade-api/v2/x", "https://api.elections.kalshi.com/trade-api/v2/x",
                 "http://external-api.demo.kalshi.co/trade-api/v2/x", "https://external-api.demo.kalshi.co.evil.com/x",
                 "https://evil.com/external-api.demo.kalshi.co"):
        try:
            _dm.assert_demo(_bad); raise AssertionError("must refuse " + _bad)
        except _dm.NotDemo:
            pass
    _dm.assert_demo("https://demo-api.kalshi.co/trade-api/v2/x")
    _real, _hit = _dm.DEMO_BASE, []
    _dm.DEMO_BASE = "https://external-api.kalshi.com/trade-api/v2"
    try:
        _dm.request("GET", "/portfolio/balance", opener=lambda *a, **k: _hit.append(1))
        raise AssertionError("a request to the real exchange must never be sent")
    except _dm.NotDemo:
        assert not _hit, "refused before anything was sent"
    finally:
        _dm.DEMO_BASE = _real

    # An order is tiny and shaped as the docs say: strings for count and price, a resting bid.
    _b = _dm.order_body("KXBTC15M-X", 1, 0.01, "cid1", 2)
    assert _b == {"ticker": "KXBTC15M-X", "side": "bid", "count": "1", "price": "0.01", "time_in_force": "good_till_canceled",
                  "self_trade_prevention_type": "taker_at_cross", "client_order_id": "cid1", "exchange_index": 2}, _b
    assert "exchange_index" not in _dm.order_body("T", 1, 0.01, "c")
    for _c, _p in ((0, 0.01), (6, 0.01), (1, 0.0), (1, 0.06), (1, 0.5)):
        try:
            _dm.order_body("T", _c, _p, "c"); raise AssertionError("must refuse count %s price %s" % (_c, _p))
        except ValueError:
            pass

    class _Resp:
        def __init__(self, status, body): self.status, self._b = status, _json.dumps(body).encode()
        def read(self): return self._b
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _server(dup_second=None):
        """A fake demo exchange. Records every request. dup_second: what the second identical create does."""
        seen, creates = [], []
        def opener(req, timeout=None):
            u = req.full_url; m = req.get_method(); body = _json.loads(req.data) if req.data else None
            seen.append((m, u, dict(req.header_items()), body))
            if m == "GET" and "/markets" in u:
                return _Resp(200, {"markets": [{"ticker": "KXBTC15M-TEST", "close_time": "2099-01-01T00:00:00Z", "exchange_index": 2}]})
            if m == "GET" and u.endswith("/portfolio/balance"):
                return _Resp(200, {"balance": 10000000, "balance_dollars": "100000.00",
                                   "balance_breakdown": [{"balance": "0.0000", "exchange_index": 0}, {"balance": "200.0000", "exchange_index": 2}]})
            if m == "POST":
                creates.append(body)
                if len(creates) == 2 and dup_second == "refuse":
                    raise _ue.HTTPError(u, 409, "conflict", {}, _io.BytesIO(b'{"error":"duplicate client_order_id"}'))
                oid = "ord-1" if (len(creates) == 1 or dup_second == "same") else "ord-2"
                return _Resp(201, {"order_id": oid, "client_order_id": body["client_order_id"], "fill_count": "0.00", "remaining_count": "1.00"})
            if m == "DELETE":
                return _Resp(200, {"order_id": u.rsplit("/", 1)[1].split("?")[0], "reduced_by": "1.00"})
            raise AssertionError("unexpected request " + m + " " + u)
        return opener, seen, creates

    _d = _tf3.mkdtemp(); _pem = _os2.path.join(_d, "k.pem")
    open(_pem, "wb").write(_rk.private_bytes(_ser.Encoding.PEM, _ser.PrivateFormat.PKCS8, _ser.NoEncryption()))
    _os2.environ["KALSHI_DEMO_KEY_ID"] = "key-id-123"; _os2.environ["KALSHI_DEMO_KEY_FILE"] = _pem
    _pem_body = open(_pem).read().split("\n")[1]
    _orig_open = _ur.urlopen

    def _run(cmd, opener):
        _ur.urlopen = opener
        out = _io.StringIO()
        try:
            with _cl.redirect_stdout(out):
                cmd()
        finally:
            _ur.urlopen = _orig_open
        return out.getvalue()

    # A signed read signs the FULL path from the API root, with the query left out, and prints no secret.
    _op, _seen, _ = _server()
    _out = _run(_dm.cmd_balance, _op)
    _m, _u, _hd, _ = _seen[0]
    _hd = {k.lower(): v for k, v in _hd.items()}
    assert _m == "GET" and _u == "https://external-api.demo.kalshi.co/trade-api/v2/portfolio/balance" and _hd["kalshi-access-key"] == "key-id-123"
    _rk.public_key().verify(_b64.b64decode(_hd["kalshi-access-signature"]),
                            (_hd["kalshi-access-timestamp"] + "GET/trade-api/v2/portfolio/balance").encode(), _pss, _h.SHA256())
    assert "100000.00" in _out and _pem_body not in _out and _hd["kalshi-access-signature"] not in _out and "BEGIN" not in _out

    # The duplicate test sends the identical order twice, cancels what exists by ticker and shard, and says which of
    # the three things happened. Each outcome must be told apart.
    for _mode, _expect in (("same", "SAME order"), ("refuse", "REFUSED"), ("two", "does NOT protect")):
        _op, _seen, _cr = _server(_mode)
        _out = _run(_dm.cmd_dup, _op)
        assert len(_cr) == 2 and _cr[0] == _cr[1] and _cr[0]["client_order_id"].startswith("dup-"), "the same body twice"
        assert _expect in _out, (_mode, _out)
        _dels = [s for s in _seen if s[0] == "DELETE"]
        assert len(_dels) == (2 if _mode == "two" else 1)
        assert all("market_ticker=KXBTC15M-TEST" in d[1] and "exchange_index=2" in d[1] for d in _dels), "cancels name the market and shard"
    assert "neither" in _dm.classify_dup([])
    # The picker takes a market on a funded shard and refuses one on an unfunded shard, and needs 2+ minutes left.
    _op, _seen, _ = _server()
    assert _dm.pick_market({2}, opener=_op)["ticker"] == "KXBTC15M-TEST"
    try:
        _dm.pick_market({0}, opener=_op); raise AssertionError("a market on an unfunded shard must not be picked")
    except RuntimeError as _e:
        assert "unfunded" in str(_e)

    # Moving demo funds between shards: whole cents, capped, never to the same shard, signed, and demo only.
    assert _dm.transfer_body(50, 2) == {"source": "event_contract", "destination": "event_contract", "amount": 500000,   # $50 at the measured 10,000 units a dollar
                                        "source_exchange_shard": 0, "destination_exchange_shard": 2}
    assert _dm.transfer_body(0.01, 2)["amount"] == 100 and _dm.transfer_body(49.5, 2)["amount"] == 495000
    for _args in ((0, 2), (-5, 2), (101, 2), (50, 0), (50.005, 2)):
        try:
            _dm.transfer_body(*_args); raise AssertionError("must refuse a transfer of %s" % (_args,))
        except ValueError:
            pass
    _sent = []
    def _opener(req, timeout=None):
        _sent.append((req.get_method(), req.full_url, _json.loads(req.data) if req.data else None, dict(req.header_items())))
        if req.get_method() == "POST":
            return _Resp(200, {"transfer_id": "tr-1"})
        if "/portfolio/balance" in req.full_url:
            return _Resp(200, {"balance_breakdown": [{"balance": "150.0000", "exchange_index": 0}, {"balance": "50.0000", "exchange_index": 2}]})
        return _Resp(200, {"markets": [{"ticker": "T", "exchange_index": 2}]})
    _out = _run(lambda: _dm.cmd_move(["50", "2"]), _opener)
    _post = [x for x in _sent if x[0] == "POST"][0]
    assert _post[1] == "https://external-api.demo.kalshi.co/trade-api/v2/portfolio/intra_exchange_instance_transfer" and _post[2]["amount"] == 500000
    _ph = {k.lower(): v for k, v in _post[3].items()}
    _rk.public_key().verify(_b64.b64decode(_ph["kalshi-access-signature"]),
                            (_ph["kalshi-access-timestamp"] + "POST/trade-api/v2/portfolio/intra_exchange_instance_transfer").encode(), _pss, _h.SHA256())
    assert "tr-1" in _out and "shard 2" in _out and _pem_body not in _out

    # The recommended demo host returned 503 while the other kept trading: a transient failure fails over to the second
    # host, with the same signed body; a real answer (even a 4xx) is returned from the first and never repeated.
    def _two_hosts(first, second):
        seen = []
        def op(req, timeout=None):
            seen.append((req.full_url.split("/")[2], req.get_method(), req.data))
            kind = first if len(seen) == 1 else second
            if kind == "ok":
                return _Resp(200, {"ok": True})
            raise _ue.HTTPError(req.full_url, kind, "x", {}, _io.BytesIO(b'{"error":"x"}'))
        return op, seen
    _op, _s = _two_hosts(503, "ok")
    _st, _d = _dm.request("POST", "/portfolio/events/orders", key_id="k", key=_rk, body={"client_order_id": "c1"}, opener=_op)
    assert _st == 200 and [h for h, _, _ in _s] == ["external-api.demo.kalshi.co", "demo-api.kalshi.co"], _s
    assert _s[0][2] == _s[1][2] and b"c1" in _s[0][2], "the same body goes to both"
    _op, _s = _two_hosts(400, "ok")
    assert _dm.request("GET", "/x", opener=_op)[0] == 400 and len(_s) == 1, "a 4xx is an answer, not a reason to try another host"
    _op, _s = _two_hosts(503, 503)
    assert _dm.request("GET", "/x", opener=_op)[0] == 503 and len(_s) == 2, "both down: the last answer is reported"
    assert all(h in _dm.DEMO_HOSTS for h in ("external-api.demo.kalshi.co", "demo-api.kalshi.co"))
    assert _dm.DEMO_ALT_BASE.split("/")[2] in _dm.DEMO_HOSTS

    # One order: placed tiny, then cancelled.
    _op, _seen, _cr = _server()
    _run(_dm.cmd_order, _op)
    assert len(_cr) == 1 and _cr[0]["count"] == "1" and float(_cr[0]["price"]) <= 0.05
    assert [s[0] for s in _seen].count("DELETE") == 1
    # The key never leaves the machine: nothing in the module writes it anywhere but into the signature.
    import re as _re7
    _src = _re7.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_dm.__file__).read())
    assert not _re7.search(r"print\([^)]*(private|pem|key\b)", _src), "no print of key material"
    assert not _re7.search(r"kalshi\.com/trade-api", _src.replace("demo.kalshi.co", "")), "no production host in the code"
    # A private key dropped into the repo must not be committable by accident.
    _gi = open(_os2.path.join(_os2.path.dirname(__file__), "..", "..", ".gitignore")).read()
    assert "*.pem" in _gi and "*.key" in _gi, "private keys are gitignored"
    print("demo trading tests passed")
