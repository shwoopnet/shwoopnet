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
# A NO entry at exactly 42c (YES bid 58c) is in the 40c band. In floating point
# 1 - 0.58 is 0.42000000000000004, which used to fail "<= 0.42" and skip the trade.
e42 = simulate([cd(60, 0.58, 0.60)], CLOSE, "no", B40)
assert e42 is not None and e42["side"] == "no" and e42["ask"] == 0.42
# Same at the 50c band's top edge, and a NO exit fires at exactly an 80c NO bid.
assert simulate([cd(60, 0.48, 0.54)], CLOSE, "no", BANDS["50c"])["ask"] == 0.52
assert simulate([cd(60, 0.58, 0.60), cd(120, 0.18, 0.20)], CLOSE, "yes", B40)["outcome"] == "target"
# Rounding must not widen a band: 43c and 37c on the NO side are still skipped.
assert simulate([cd(60, 0.57, 0.65)], CLOSE, "no", B40) is None
assert simulate([cd(60, 0.63, 0.70)], CLOSE, "no", B40) is None
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

# ---- H5: two sided market making ----
import random as _rd5, sqlite3 as _sq5, tempfile as _tf5, os as _os5
import scalper.marketmaker as _mm

# Quotes stop 5 minutes before close and need a usable two sided book.
_cs = [(1000, 0.40, 0.44), (1060, 0.0, 0.44), (1120, 0.40, 0.44), (1700, 0.40, 0.44), (1701, 0.40, 0.44)]
assert [q[0] for q in _mm.quote_minutes(_cs, 2000)] == [1000, 1120, 1700], "a dead quote is skipped, 300s or more must remain"
assert [q[0] for q in _mm.quote_minutes(_cs, 1999)] == [1000, 1120], "299s left is too late"

# A bid fills only when a taker SELLING yes prints strictly through it; an ask only for a taker buying through it.
_T = lambda ts, side, y: (ts, side, y, round(1 - y, 4))
assert _mm.fills_in([_T(10, "no", 0.39)], 0, 0.40, 0.44) == (True, False)
assert _mm.fills_in([_T(10, "no", 0.40)], 0, 0.40, 0.44) == (False, False), "a print AT our price does not fill us"
assert _mm.fills_in([_T(10, "no", 0.40)], 0, 0.40, 0.44, strict=False) == (True, False)
assert _mm.fills_in([_T(10, "yes", 0.39)], 0, 0.40, 0.44) == (False, False), "a taker BUYING at a low price does not hit a bid"
assert _mm.fills_in([_T(10, "yes", 0.45)], 0, 0.40, 0.44) == (False, True)
assert _mm.fills_in([_T(10, "yes", 0.44)], 0, 0.40, 0.44) == (False, False)
assert _mm.fills_in([_T(0, "no", 0.30), _T(61, "no", 0.30)], 0, 0.40, 0.44) == (False, False), "only the next minute counts, and not the current second"

# Inventory can never pass the cap, either way.
_q = [(1000 + 60 * i, 0.40, 0.44) for i in range(6)]
_down = [_T(1000 + 60 * i + 5, "no", 0.30) for i in range(6)]
_fl, _inv = _mm.walk(_q, _down, 2)
assert _inv == 2 and len(_fl) == 2, "a falling market buys only up to the cap"
_up = [_T(1000 + 60 * i + 5, "yes", 0.60) for i in range(6)]
assert _mm.walk(_q, _up, 2)[1] == -2

# A completed round trip captures the spread, and the fee is paid on both legs.
_c = [(1000, 0.40, 0.44), (1060, 0.40, 0.44), (1120, 0.40, 0.44)]
_tr = [_T(1010, "no", 0.39), _T(1070, "yes", 0.45)]
_r = _mm.simulate(_c, 5000, "yes", _tr)
assert _r["inv_end"] == 0 and abs(_r["rt_gross"] - 0.04) < 1e-9
assert abs(_r["pnl"] - (0.04 - _mm.fee(0.40) - _mm.fee(0.44))) < 1e-9, _r
assert abs(_r["pnl_nofee"] - 0.04) < 1e-9 and _r["pnl_stress"] < _r["pnl"] < _r["pnl_nofee"]
assert abs(_r["rt_gross"] + _r["leftover"] - _r["pnl_nofee"]) < 1e-9, "round trips plus leftover reconcile to the total before fees"
assert _mm.simulate(_c, 5000, "", _tr) is None and _mm.simulate([], 5000, "yes", _tr) is None

# Leftover inventory settles at 0 or 1: bought at 40c and yes loses is -40c less fee.
_r = _mm.simulate(_c, 5000, "no", [_T(1010, "no", 0.39)])
assert _r["inv_end"] == 1 and abs(_r["pnl_nofee"] + 0.40) < 1e-9 and _r["rt_gross"] == 0

# Outcome independent of fills (true value is the 50c mid, quotes 2c either side): before fees the strategy earns
# exactly the half spread on each fill and nothing more, and fees take it below that. No hidden source of profit.
_rg = _rd5.Random(5)
_res = []
for _ in range(3000):
    _cd = [(1000 + 60 * i, 0.48, 0.52) for i in range(8)]
    _t = [(1000 + 60 * i + _rg.randint(1, 59), _rg.choice(("yes", "no")), _p, round(1 - _p, 4))
          for i in range(8) for _p in [_rg.choice((0.45, 0.47, 0.50, 0.53, 0.55))] if _rg.random() < 0.8]
    _res.append(_mm.simulate(_cd, 5000, _rg.choice(("yes", "no")), _t))
_nf = sum(r["pnl_nofee"] for r in _res) / len(_res)
_pn = sum(r["pnl"] for r in _res) / len(_res)
_fills = sum(r["n_buy"] + r["n_sell"] for r in _res) / len(_res)
assert abs(_nf - 0.02 * _fills) < 0.04, (_nf, _fills)
assert _pn < _nf - 0.5 * _mm.fee(0.5) * _fills, "fees are charged on every fill"

# Adverse selection: a bid is only hit when the market is about to fall. Round trips look fine, the leftover loses it.
_ad = []
for _ in range(200):
    _won = _rg.random() < 0.5
    _tp5 = [_T(1010, "no", 0.30)] if not _won else [_T(1010, "yes", 0.60)]
    _ad.append(_mm.simulate([(1000, 0.40, 0.44), (1060, 0.40, 0.44)], 5000, "yes" if _won else "no", _tp5))
_lose = [r for r in _ad if r["n_buy"] == 1]
assert _lose and all(abs(r["pnl_nofee"] + 0.40) < 1e-9 for r in _lose), "informed selling: every bid fill settles at zero"
assert all(r["leftover"] < 0 for r in _lose)

# The sample is by position in time, never by result.
_ms = [(f"M{i}", "S", [], 100 + i, "yes" if i % 3 == 0 else "no") for i in range(20)]
_sm = _mm.sample(_ms)
assert [m[0] for m in _sm] == [f"M{i}" for i in range(0, 20, 4)]
assert [m[0] for m in _mm.sample([(m[0], m[1], m[2], m[3], "yes") for m in _ms])] == [m[0] for m in _sm], "results never pick the sample"

# Verdict: under 300 markets nothing is decided; a steady loser is FALSIFIED; no verdict word says to trade.
_days = [f"2026-09-{d:02d}" for d in range(1, 11)]
_rows = lambda n, f: [(_days[i % 10], i, f(i), f(i) - 0.001) for i in range(n)]
assert _mm.verdict(_rows(299, lambda i: 0.05), 150)[0] == "NOT_ENOUGH_DATA"
assert _mm.verdict(_rows(400, lambda i: -0.02 + (i % 5) * 0.001), 200)[0] == "FALSIFIED"
assert _mm.verdict(_rows(400, lambda i: 0.05 + (i % 7) * 0.002), 200)[0] == "NOT_YET_FALSIFIED"

# Fetch stores results only, and a rerun fetches nothing already stored.
_p5 = _os5.path.join(_tf5.mkdtemp(), "t.sqlite")
_d5 = _sq5.connect(_p5)
_d5.executescript("CREATE TABLE market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);"
                  "CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL, ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY (ticker, end_ts));")
for _i in range(8):
    _tk = f"K{_i}"
    _d5.execute("INSERT INTO market VALUES(?,?,?,?,?,?,?)", (_tk, "KXBTC15M", 0, 5000 + _i * 1000, "yes", None, 1))
    _d5.execute("INSERT INTO candle(ticker, series, end_ts, bid_c, ask_c) VALUES(?,?,?,?,?)", (_tk, "KXBTC15M", 1000 + _i * 1000, 0.40, 0.44))
_d5.commit(); _d5.close()
_calls5 = []
def _ft(ticker, lo, hi):
    _calls5.append(ticker)
    return [(lo + 5, "no", 0.39, 0.61)]
_o = (_mm.DB, _mm.fetch_trades)
_mm.DB, _mm.fetch_trades = _p5, _ft
try:
    _mm.run_fetch(None)
    _rs = _sq5.connect(_p5).execute("SELECT ticker, n_buy, inv_end, n_trades FROM mm").fetchall()
    assert len(_rs) == 2 and all(r[1:] == (1, 1, 1) for r in _rs), _rs     # every 4th of 8, a raw tape is not stored
    _n5 = len(_calls5)
    _mm.run_fetch(None)
    assert len(_calls5) == _n5 == 2, "a rerun must not refetch stored markets"
finally:
    _mm.DB, _mm.fetch_trades = _o

import re as _re9
_c9 = _re9.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_mm.__file__).read())
assert not _re9.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _c9)
assert not _re9.search(r"place_order|/portfolio/", _c9), "research code never touches an order endpoint"
print("market making tests passed")

# ---- order-book recorder ----
import sqlite3 as _sq10, json as _js10, re as _re10
from scalper import recorder as _rc

_BOOK = {"orderbook_fp": {"yes_dollars": [["0.3000", "5"], ["0.4000", "10"]], "no_dollars": [["0.5000", "7"], ["0.5500", "3"]]}}
_b = _rc.parse_book(_BOOK)
# A yes ask is what the best no bid implies. Getting this wrong would price every quote 1 - x off.
assert _b["yes_bid"] == 0.40 and _b["no_bid"] == 0.55 and _b["yes_ask"] == 0.45 and _b["no_ask"] == 0.60, _b
# An empty side is unknown, never a free price of zero.
_e = _rc.parse_book({"orderbook_fp": {"yes_dollars": [], "no_dollars": [["0.5", "1"]]}})
assert _e["yes_bid"] is None and _e["no_ask"] is None and _e["yes_ask"] == 0.5, _e
assert _rc.parse_book({})["yes_bid"] is None, "a missing book must not crash or invent a price"

_paths10 = []
def _fake_get(path, p=None):
    _paths10.append(path)
    if path == "/markets":
        if p["series_ticker"] == "KXGOLD15M":
            raise RuntimeError("HTTP 429")
        return {"markets": [{"ticker": "KXBTC15M-T", "close_time": "x", "yes_bid_dollars": "0.38", "yes_ask_dollars": "0.42"}]}
    return _BOOK
_db10 = _sq10.connect(":memory:")
_db10.executescript(_rc.SCHEMA)
_n10 = _rc.cycle(_db10, _fake_get, now=lambda: 1.0)
# One series failing must not lose the other's rows, and the failure must be recorded, not swallowed.
assert _n10 == 1 and _db10.execute("SELECT count(*) FROM ob").fetchone()[0] == 1
assert _db10.execute("SELECT series, what FROM err").fetchall() == [("KXGOLD15M", "HTTP 429")]
_r10 = _db10.execute("SELECT list_yes_bid, list_yes_ask, yes_ask FROM ob").fetchone()
assert _r10 == (0.38, 0.42, 0.45), _r10     # the list price is kept beside the book so staleness can be measured
assert all(p == "/markets" or p.endswith("/orderbook") for p in _paths10), "only read endpoints"

_c10 = _re10.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_rc.__file__).read())
assert not _re10.search(r"place_order|/portfolio/|POST|\bdata=", _c10), "the recorder never touches an order path"
print("recorder tests passed")

# ---- H7: distance to the target ----
import math as _m7, random as _r7, re as _re7, sqlite3 as _sq7, tempfile as _tf7, os as _os7
import scalper.distance as _d7
from scalper.marketmaker import fee as _fee7

# Buckets: a value exactly on an edge goes UP, the extremes are open, and there are eight.
assert [_d7.bucket(z) for z in (-9, -2.0, -1.01, -1.0, -0.5, -0.01, 0.0, 0.5, 1.0, 1.99, 2.0, 9)] == [0, 1, 1, 2, 3, 3, 4, 5, 6, 6, 7, 7], "edges go up"
assert _d7.bucket(float("-inf")) == 0 and _d7.bucket(float("inf")) == 7 and len(_d7.EDGES) + 1 == 8
assert [_d7.bucket_label(i) for i in (0, 1, 4, 7)] == ["below -2", "-2 to -1", "0 to 0.5", "above 2"]

# z: the distance in units of typical movement over the 6 minutes left. A flat series has no sigma, so no z.
_rets = [0.001, -0.001] * 30
_cl = [100.0]
for _r in _rets:
    _cl.append(_cl[-1] * _m7.exp(_r))
_sd = _m7.sqrt(sum((r - sum(_rets) / 60) ** 2 for r in _rets) / 59)
assert abs(_d7.z_score(_cl, _cl[-1]) - 0.0) < 1e-12, "spot at the strike is z of zero"
assert abs(_d7.z_score(_cl, _cl[-1] / 1.01) - _m7.log(1.01) / (_sd * _m7.sqrt(6))) < 1e-9, "spot above its strike is positive and uses sigma times sqrt(6)"
assert _d7.z_score(_cl, _cl[-1] * 1.01) < 0, "spot below the strike is negative"
assert _d7.z_score([100.0] * 61, 99.0) is None, "no movement, no z"
assert _d7.z_score(_cl[:-1], 100.0) is None and _d7.z_score(_cl, 0) is None and _d7.z_score(_cl[:-1] + [None], 100.0) is None, "missing or bad data gives no z"

# The rule: buy YES only when the bucket's YES rate beats ask + fee + 2c, NO only when the NO rate beats its price likewise.
_p, _bid, _ask = 0.80, 0.68, 0.70
_dc = _d7.decide(_p, _bid, _ask)
assert _dc == ("yes", _ask), _dc
assert _p - _ask - _fee7(_ask) > 0.02 and _d7.decide(0.73, _bid, _ask) is None, "a bucket rate that only just beats the ask does not clear the fee and margin"
assert _d7.decide(0.20, 0.30, 0.32) == ("no", 0.70), "a low YES rate buys NO at 1 minus the bid"
assert _d7.decide(0.27, 0.30, 0.32) is None, "a NO rate that only just beats its price does not clear the fee and margin either"
assert _d7.decide(None, 0.5, 0.52) is None, "a thin bucket is never traded"
assert _d7.decide(0.50, 0.49, 0.51) is None, "a fair price is not traded"
# P and L: a won contract pays $1 less price and fee, a lost one loses price and fee; stress charges more fee.
assert abs(_d7.net("yes", 0.40, True) - (1 - 0.40 - _fee7(0.40))) < 1e-12 and abs(_d7.net("yes", 0.40, False) - (-0.40 - _fee7(0.40))) < 1e-12
assert abs(_d7.net("no", 0.30, False) - (1 - 0.30 - _fee7(0.30))) < 1e-12 and _d7.net("yes", 0.4, True, 1.2) < _d7.net("yes", 0.4, True)
assert abs(_d7.net("yes", 0.4, True, 0.0) - 0.60) < 1e-12

# Observations: one per market, at exactly 6 minutes left, with a usable quote and a full 61 minutes of spot.
_close = 1_800_000_000
_spot = {_close - 360 - 60 - 60 * k: 100.0 * (1 + 0.0005 * ((-1) ** k)) for k in range(0, 61)}
_good = ("T1", _close, 99.0, "yes", {_close - 360: (0.60, 0.64)})
assert len(_d7.observations([_good], _spot)) == 1
_o = _d7.observations([_good], _spot)[0]
assert _o["yes"] is True and _o["ask"] == 0.64 and _o["bid"] == 0.60 and _o["close_ts"] == _close
for _bad in (("T2", _close, 99.0, "yes", {_close - 300: (0.60, 0.64)}),      # no candle at 6 minutes left
             ("T3", _close, 99.0, "yes", {_close - 360: (0.01, 0.99)}),      # an empty book
             ("T4", _close, None, "yes", {_close - 360: (0.60, 0.64)}),      # no strike
             ("T5", _close, 99.0, "", {_close - 360: (0.60, 0.64)})):        # unresolved
    assert _d7.observations([_bad], _spot) == [], _bad[0]
assert _d7.observations([_good], {k: v for k, v in _spot.items() if k != _close - 360 - 60 - 60 * 30}) == [], "a missing spot minute drops the market"
assert _d7.observations([_good], {}) == []

# The split is by close time: the first half estimates, the second half tests, and they never overlap.
_obs = [{"close_ts": 100 + i, "z": 0.0, "bid": 0.4, "ask": 0.42, "yes": True, "day": "d", "ticker": str(i)} for i in range(11)][::-1]
_obs = sorted(_obs, key=lambda o: o["close_ts"])
_e, _t = _d7.split(_obs)
assert len(_e) == 5 and len(_t) == 6 and max(o["close_ts"] for o in _e) < min(o["close_ts"] for o in _t)

# Estimation: thin buckets are not trusted, thick ones carry their rate.
_est = [{"z": 1.5, "yes": i < 15, "close_ts": i, "bid": 0.5, "ask": 0.52, "day": "d", "ticker": "x"} for i in range(20)] + \
       [{"z": -1.5, "yes": True, "close_ts": i, "bid": 0.5, "ask": 0.52, "day": "d", "ticker": "y"} for i in range(19)]
_tb = _d7.estimate(_est)
assert _tb[6] == {"n": 20, "p": 0.75} and _tb[1]["p"] is None and _tb[1]["n"] == 19, "19 markets is too few to trade"

# The descriptive table answers the owner's question in plain numbers and shows the price charged beside it.
_ds = {r["bucket"]: r for r in _d7.describe(_est)}
assert _ds["1 to 2"]["n"] == 20 and abs(_ds["1 to 2"]["yes_rate"] - 0.75) < 1e-12 and abs(_ds["1 to 2"]["mean_ask"] - 0.52) < 1e-12
assert _ds["above 2"]["n"] == 0 and _ds["above 2"]["yes_rate"] is None

# A fair market: outcomes drawn at the price the market charges. The distance rule must lose about the fees, not win.
_g = _r7.Random(11)
def _world(n, informed):
    out = []
    for i in range(n):
        z = _g.uniform(-3, 3)
        p_true = 1 / (1 + _m7.exp(-1.6 * z))
        ask = (p_true if not informed else 0.5) + 0.01
        yes = _g.random() < p_true
        out.append({"ticker": str(i), "close_ts": 1000 + i, "day": str(i // 40), "z": z, "bid": ask - 0.02, "ask": ask, "yes": yes})
    return out
_fair = _world(6000, informed=False)               # the price already reflects the distance
_fe, _ft = _d7.split(_fair)
_fentries = _d7.run(_ft, _d7.estimate(_fe))
assert _fentries and sum(e["net"] for e in _fentries) / len(_fentries) < 0.01, "no edge when the price already reflects the distance"
_blind = _world(6000, informed=True)               # the price ignores the distance, the outcomes do not
_be, _bt = _d7.split(_blind)
_bentries = _d7.run(_bt, _d7.estimate(_be))
assert _bentries and sum(e["net"] for e in _bentries) / len(_bentries) > 0.05, "an edge is found when the price really does ignore the distance"

# Verdict: under 300 entered markets nothing is decided; the words are the same three; none says to trade.
_rows = lambda n, f: [{"day": f"2026-09-{1 + i % 10:02d}", "close_ts": i, "net": f(i), "stress": f(i) - 0.001} for i in range(n)]
assert _d7.verdict(_rows(299, lambda i: 0.05))[0] == "NOT_ENOUGH_DATA"
assert _d7.verdict(_rows(400, lambda i: -0.02 + (i % 5) * 0.001))[0] == "FALSIFIED"
assert _d7.verdict(_rows(400, lambda i: 0.05 + (i % 7) * 0.002))[0] == "NOT_YET_FALSIFIED"

# describe cannot see the test half: it takes the estimation half only, and main hands it nothing else.
_src7 = _re7.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_d7.__file__).read())
assert "describe(est)" in _src7 and "describe(test)" not in _src7 and "describe(obs)" not in _src7
assert not _re7.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _src7)
assert not _re7.search(r"place_order|/portfolio/", _src7), "research code never touches an order endpoint"
print("distance tests passed")

# ---- L1, L2, L3 ----
import random as _rn
from scalper import lstrats as _ls
from scalper import distance as _di

# Band edges are inclusive, and a NO price of exactly 97c survives floating point (1 - 0.03 must count as 0.97).
assert _ls.favorite(0.87, 0.88, (0.88, 0.97)) == ("yes", 0.88)
assert _ls.favorite(0.96, 0.97, (0.88, 0.97)) == ("yes", 0.97)
assert _ls.favorite(0.97, 0.98, (0.88, 0.97)) is None, "98c is outside the L1 band"
assert _ls.favorite(0.03, 0.04, (0.88, 0.97)) == ("no", 0.97)
assert _ls.favorite(0.58, 0.60, (0.38, 0.42)) == ("no", 0.42), "1 - 0.58 is 0.42000000000000004 in floating point and must still be inside a band ending at 0.42"
assert _ls.favorite(0.001, 1.0, (0.88, 0.97)) is None, "an empty book is not a quote"
assert _ls.favorite(0.50, 0.52, (0.88, 0.97)) is None

def _mk(ticker, close, bid, ask, res, left=360, series="KXBTC15M", extra=()):
    cs = [(close - left, bid, ask, bid, ask)] + list(extra)
    return (ticker, series, cs, close, res)

# One observation per market, taken from the candle that ends EXACTLY left_s before the close: a nearby minute is never substituted.
_C = 1_790_000_000 - (1_790_000_000 % 900)
_m = [_mk("A", _C, 0.89, 0.90, "yes"),
      _mk("B", _C + 900, 0.89, 0.90, "yes", left=420),      # the quote is a minute too early: no observation
      _mk("C", _C + 1800, 0.89, 0.90, "")]                  # unresolved: no observation
_r = _ls.hold_rule(_m, **_ls.L1)
assert [o["ticker"] for o in _r] == ["A"], _r
assert abs(_r[0]["net"] - (1.0 - 0.90 - _ls.fee(0.90))) < 1e-12, "a win nets 1 - price - entry fee"
_l = _ls.hold_rule([_mk("D", _C, 0.89, 0.90, "no")], **_ls.L1)
assert abs(_l[0]["net"] - (-0.90 - _ls.fee(0.90))) < 1e-12, "a loss costs the whole price plus the fee"
assert _l[0]["stress"] < _l[0]["net"], "higher fees must cost more"

# THE simulator guard: in a FAIR game (the true win rate equals the midpoint) holding favorites must LOSE about its costs,
# the half spread plus the fee. A profit here would mean the simulator invents an edge.
_g = _rn.Random(7)
_fair = []
for _i in range(4000):
    _p = _g.choice([0.90, 0.92, 0.94])
    _res = "yes" if _g.random() < _p else "no"
    _fair.append(_mk(f"F{_i}", _C + 900 * _i, round(_p - 0.01, 4), round(_p + 0.01, 4), _res))
_fr = _ls.hold_rule(_fair, **_ls.L1)
_mean = sum(o["net"] for o in _fr) / len(_fr)
assert len(_fr) > 3000 and -0.035 < _mean < -0.005, _mean
assert _ls.verdict(_fr)[0] == "FALSIFIED", "a fair game must never pass"
assert _ls.verdict(_fr[:100])[0] == "NOT_ENOUGH_DATA"

# A rule that truly beats its price (favorite wins 5 points more than priced) passes: the verdict can say yes.
_edge = []
for _i in range(1500):
    _res = "yes" if _g.random() < 0.97 else "no"
    _edge.append(_mk(f"E{_i}", _C + 900 * _i, 0.89, 0.90, _res))
assert _ls.verdict(_ls.hold_rule(_edge, **_ls.L1))[0] == "NOT_YET_FALSIFIED"

# L2: a fixture where spot sits far above the target, so H7 buys YES at the ask once its estimation half has seen YES win.
import math as _mt
_N = 120
_spot = {_C - 4020 + 60 * i: 110.0 * (1 + 0.0005 * _mt.sin(i)) for i in range((_N * 15) + 200)}
def _l2m(i, later_bid, same_minute_bid=0.40, result="yes"):
    close = _C + 900 * (i + 5)
    q = {close - 360: (same_minute_bid, same_minute_bid + 0.01)}
    if later_bid is not None:
        q[close - 300] = (later_bid, later_bid + 0.01)
    return ("T%d" % i, close, 100.0, result, q)
_l2 = [_l2m(i, None) for i in range(_N // 2)] + [_l2m(_N // 2, 0.85), _l2m(_N // 2 + 1, 0.50), _l2m(_N // 2 + 2, None, same_minute_bid=0.85)] \
      + [_l2m(i, None) for i in range(_N // 2 + 3, _N)]
# The decision minute's own 85c bid must not trigger the exit (strictly later); only a LATER close at 80c or more does.
_x = {e["ticker"]: e for e in _ls.l2_rule(_l2, _spot)}
_exp = lambda m: _ls.EXIT - _ls.fee(_ls.EXIT, m) - 0.41 - _ls.fee(0.41, m)
assert "T%d" % (_N // 2) in _x and _x["T%d" % (_N // 2)]["exited"], "a later close at 85c sells at 80c"
assert abs(_x["T%d" % (_N // 2)]["net"] - (_ls.EXIT - _ls.fee(_ls.EXIT) - 0.41 - _ls.fee(0.41))) < 1e-12, "the exit is priced at 80c, not at the 85c bid"
assert not _x["T%d" % (_N // 2 + 1)]["exited"] and abs(_x["T%d" % (_N // 2 + 1)]["net"] - _ls.net("yes", 0.41, True)) < 1e-12, "no 80c touch means hold to settlement"
assert "T%d" % (_N // 2 + 2) not in _x or not _x["T%d" % (_N // 2 + 2)]["exited"], "the decision minute itself never exits"

print("L1 L2 L3 tests passed")

import re as _re11
_c11 = _re11.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_ls.__file__).read())
assert not _re11.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _c11)
assert not _re11.search(r"place_order|/portfolio/", _c11), "research code never touches an order endpoint"

# ---- automated rule search ----
import random as _rs
from scalper import search as _se
from scalper import lstrats as _l2s

def _sm(ticker, close, bid, ask, res, series="KXBTC15M", extra=()):
    cs = [(close - 360, bid, ask, bid, ask)] + list(extra)
    return (ticker, series, cs, close, res)

_C0 = 1_790_000_000 - (1_790_000_000 % 900)
_rule = lambda **k: {"left": 6, "lo": 0.88, "hi": 0.97, "side": "either", "filters": [], **k}

# A search rule that is L1 must give exactly L1's numbers: the generic evaluator cannot disagree with the audited one.
_mk = [_sm("A", _C0, 0.89, 0.90, "yes"), _sm("B", _C0 + 900, 0.03, 0.04, "no"), _sm("C", _C0 + 1800, 0.50, 0.52, "yes"),
       _sm("D", _C0 + 2700, 0.89, 0.90, "")]
_p = _se.prep(_mk)
_got = sorted(_se.observe(m, _rule()) [1] for m in _p if _se.observe(m, _rule()))
_ref = sorted(o["net"] for o in _l2s.hold_rule(_mk, **_l2s.L1))
assert len(_got) == 2 and all(abs(a - b) < 1e-12 for a, b in zip(_got, _ref)), (_got, _ref)

# The decision candle must be exactly the one asked for, a side selector must restrict the side, and band edges are inclusive.
assert _se.observe(_p[0], _rule(left=5)) is None, "no candle at 5 minutes: nothing is substituted"
assert _se.observe(_p[0], _rule(side="no")) is None and _se.observe(_p[0], _rule(side="yes")) is not None
assert _se.observe(_p[0], _rule(lo=0.90, hi=0.97)) is not None and _se.observe(_p[0], _rule(lo=0.91, hi=0.97)) is None

# Filters: spread, series and the market's own move toward or away from the side.
assert _se.observe(_p[0], _rule(filters=[("spread", 0.01)])) is not None
assert _se.observe(_p[0], _rule(filters=[("spread", 0.01)])) is not None and _se.observe(_se.prep([_sm("W", _C0, 0.86, 0.90, "yes")])[0], _rule(filters=[("spread", 0.02)])) is None
assert _se.observe(_p[0], _rule(filters=[("series", "KXGOLD15M")])) is None
_mv = _se.prep([_sm("M", _C0, 0.89, 0.90, "yes", extra=[(_C0 - 360 - 180, 0.84, 0.85, 0.84, 0.85)])])[0]       # YES mid rose 5c over the last 3 minutes
assert _se.observe(_mv, _rule(filters=[("move", "toward", 0.05, 3)])) is not None, "a YES buy after a 5c rise moved toward the side"
assert _se.observe(_mv, _rule(filters=[("move", "away", 0.05, 3)])) is None
assert _se.observe(_mv, _rule(filters=[("move", "toward", 0.05, 5)])) is None, "no candle 5 minutes back: the filter cannot be evaluated, so no entry"
_mv2 = _se.prep([_sm("N", _C0, 0.89, 0.90, "yes", extra=[(_C0 - 360 - 180, 0.001, 1.0, 0.001, 1.0)])])[0]      # an empty book 3 minutes back is not a price
assert _se.observe(_mv2, _rule(filters=[("move", "toward", 0.05, 3)])) is None, "an unusable earlier quote cannot define a move"

# Add or remove ONE filter, and nothing else changes.
_g = _rs.Random(3)
for _ in range(300):
    _r0 = _se.normalize(_se.random_rule(_g)); _r1 = _se.normalize(_se.mutate(_r0, _g))
    _a, _b = {tuple(f) for f in _r0["filters"]}, {tuple(f) for f in _r1["filters"]}
    assert abs(len(_a) - len(_b)) == 1 and (_a <= _b or _b <= _a), (_r0, _r1)     # exactly one filter added or removed
    assert {k: v for k, v in _r0.items() if k != "filters"} == {k: v for k, v in _r1.items() if k != "filters"}
    assert len({f[0] for f in _r1["filters"]}) == len(_r1["filters"]) <= 3

# The holdout is the later half of the DAYS and never overlaps the search window.
_days = [_sm(f"X{i}", _C0 + 86400 * (i // 4) + 900 * (i % 4), 0.89, 0.90, "yes") for i in range(40)]
_s, _h = _se.split_days(_se.prep(_days))
assert _s and _h and max(m["day"] for m in _s) < min(m["day"] for m in _h)
assert (len({m["day"] for m in _s}), len({m["day"] for m in _h})) == (5, 5), "half the days each"
assert "holdout" not in _se.run_search.__code__.co_varnames and "hold" not in _se.run_search.__code__.co_varnames

# THE selection guard. On a FAIR game, the best of 150 rules found in the search window looks good, and the same rules lose on fresh data.
_gf = _rs.Random(11)
def _fair(n, base):
    out = []
    for i in range(n):
        p = _gf.choice([0.15, 0.35, 0.5, 0.65, 0.85, 0.93])
        res = "yes" if _gf.random() < p else "no"
        close = base + 900 * i
        cs = [(close - 60 * L, round(p - 0.01, 4), round(p + 0.01, 4), round(p - 0.01, 4), round(p + 0.01, 4)) for L in _se.LEFTS]
        out.append(("F%d_%d" % (base, i), "KXBTC15M" if i % 2 else "KXGOLD15M", cs, close, res))
    return out
_fs = _se.prep(_fair(1600, _C0)); _fh = _se.prep(_fair(1600, _C0 + 86400 * 20))
_res = _se.run_search(_fs, seed=5, cycles=1)
_best = _res["rounds"][-1]["top"][0]
_hold = [_se.score(_fh, r["rule"]) for r in _res["rounds"][-1]["top"]]
_hm = sum(h["mean"] for h in _hold) / len(_hold)
assert _res["evaluated"] > 100 and _best["z"] >= _res["rounds"][-1]["top"][-1]["z"], "ranked best first"
assert _best["z"] < 2.5, ("a fair game with costs must not produce a significant winner", _best["z"])
assert _hm < 0.005, ("and it does not survive fresh data", _hm)

# The control is a FAIR market: outcomes are drawn from each market's own last price, so a rule's win rate matches its price.
_cm = _se.prep([_sm("Q%d" % i, _C0 + 900 * i, 0.79, 0.81, "yes", extra=[(_C0 + 900 * i - 60, 0.79, 0.81, 0.79, 0.81)]) for i in range(4000)])
_cn = _se.fair_market(_cm, 3)
_yr = sum(1 for m in _cn if m["res"] == "yes") / len(_cn)
assert len(_cn) == 4000 and abs(_yr - 0.80) < 0.02, ("outcomes follow the price", _yr)
assert [m["ticker"] for m in _cn] == [m["ticker"] for m in _cm], "same markets, same order"
# Buying the 5c longshot in the control does NOT win half the time (the failure of the shuffle control).
_lg = _se.prep([_sm("L%d" % i, _C0 + 900 * i, 0.04, 0.06, "no", extra=[(_C0 + 900 * i - 60, 0.04, 0.06, 0.04, 0.06)]) for i in range(4000)])
_ln = _se.fair_market(_lg, 4)
assert sum(1 for m in _ln if m["res"] == "yes") / len(_ln) < 0.09, "a 5c contract wins about 5% of the time in a fair market"
print("search tests passed")

import re as _re12
_c12 = _re12.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_se.__file__).read())
assert not _re12.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED)\b", _c12)
assert not _re12.search(r"place_order|/portfolio/", _c12)
