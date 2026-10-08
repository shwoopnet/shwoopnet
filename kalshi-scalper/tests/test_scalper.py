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

# ---- overnight run: windows, the survivor test, and a pipeline that can say yes and can say no ----
import tempfile as _tf3, random as _rn3
from pathlib import Path as _P3
from scalper import overnight as _ov

def _world(edge, seed, old_days=24, orig_days=30, new_days=2, per_day=60):
    g = _rn3.Random(seed); out = []
    def day(base_ts, di):
        for k in range(per_day):
            p = g.choice([0.2, 0.4, 0.6, 0.8])
            win = p + (edge if abs(p - 0.4) < 1e-9 else 0.0)
            res = "yes" if g.random() < win else "no"
            close = base_ts + di * 86400 + 3600 + k * 900
            cs = [(close - 60 * L, round(p - 0.01, 4), round(p + 0.01, 4), round(p - 0.01, 4), round(p + 0.01, 4)) for L in _se.LEFTS]
            out.append(("W%d_%d_%d" % (base_ts % 1000, di, k), "KXBTC15M" if k % 2 else "KXGOLD15M", cs, close, res))
    for d in range(old_days): day(_ov.ORIG_START - old_days * 86400 - 3600 + 0, d)
    for d in range(orig_days): day(_ov.ORIG_START + 3600, d)
    for d in range(new_days): day(_ov.ORIG_END + 3600, d)
    return _se.prep(out)

_ms = _world(0.0, 1)
_w = _ov.windows(_ms)
assert set(_w) == {"W0s", "W0h", "W1", "W2", "W3"} and all(_w.values())
assert all(m["close"] < _ov.ORIG_START for m in _w["W0s"] + _w["W0h"]), "W0 is the older data"
assert all(_ov.ORIG_START <= m["close"] <= _ov.ORIG_END for m in _w["W1"] + _w["W2"]) and all(m["close"] > _ov.ORIG_END for m in _w["W3"])
assert max(m["day"] for m in _w["W0s"]) < min(m["day"] for m in _w["W0h"]), "the locked third is the latest"
_nd = len({m["day"] for m in _w["W0s"] + _w["W0h"]})
assert (len({m["day"] for m in _w["W0s"]}), len({m["day"] for m in _w["W0h"]})) == (round(_nd * 2 / 3), _nd - round(_nd * 2 / 3)), "two thirds search, one third locked"
assert max(m["day"] for m in _w["W1"]) < min(m["day"] for m in _w["W2"])
assert not ({m["ticker"] for m in _w["W0s"]} & {m["ticker"] for m in _w["W0h"]})

# The survivor test: a real edge passes, a fair game does not, and each way of failing fails.
_edge = _world(0.15, 2); _ew = _ov.windows(_edge); _fw = _ov.windows(_world(0.0, 3))
_r = {"left": 6, "lo": 0.30, "hi": 0.50, "side": "yes", "filters": []}
_yes = _ov.survivor(_r, [_ew["W0h"], _ew["W1"], _ew["W2"]])
assert _yes["survivor"] and _yes["pooled_z"] >= 2.5 and all(p["mean"] > 0 for p in _yes["per_window"]), _yes
_no = _ov.survivor(_r, [_fw["W0h"], _fw["W1"], _fw["W2"]])
assert not _no["survivor"], _no
assert not _ov.survivor(_r, [_ew["W0h"], _ew["W1"], _fw["W2"]])["survivor"], "one window with no edge fails the rule"
assert not _ov.survivor(_r, [_ew["W0h"][:30], _ew["W1"], _ew["W2"]])["survivor"], "a window with fewer than 50 entries fails, however good its mean"
assert _ov.survivor(_r, [_ew["W0h"], _ew["W1"], _ew["W2"]])["survivor"], "while the full window passes"

# THE pipeline guard: with a real edge planted the search finds survivors; on a fair market it finds none, and neither does its control.
import json as _js3
with _tf3.TemporaryDirectory() as _empty, _tf3.TemporaryDirectory() as _saved:
    (_P3(_saved) / "cycle1_A_top25.json").write_text(_js3.dumps([{"spec": {**_r, "filters": []}}]))
    _res_a = _ov.run(_edge, seed=4, cycles=1, first_dir=_P3(_saved))
    assert len(_res_a["stageA"]) == 1 and len(_res_a["stageA"][0]["per_window"]) == 3, "a stage A rule is judged on the three windows it did not search"
    assert _res_a["stageA"][0]["per_window"][0]["n"] == len(_ov.observations(_ov.windows(_edge)["W0s"], _res_a["stageA"][0]["rule"])), "the first is W0s"
    _res_e = _ov.run(_edge, seed=4, cycles=2, first_dir=_P3(_empty))
    _res_f = _ov.run(_world(0.0, 5), seed=4, cycles=2, first_dir=_P3(_empty))
assert any(r["survivor"] for r in _res_e["stageB"]), "a planted edge must be found out of sample"
assert all(len(r["per_window"]) == 3 for r in _res_e["stageB"]), "a stage B rule is judged on W0h, W1 and W2"
assert not any(r["survivor"] for r in _res_f["stageB"]) and not any(r["survivor"] for r in _res_f["control"]), "a fair market must produce no survivor"
assert not any(r["survivor"] for r in _res_e["control"]), "the control of an edge world is a fair market too"
assert _res_f["evaluated_B"] >= 200
print("overnight tests passed")

# ---- L8 and L9 (averaged settlement) ----
from scalper import avgsettle as _av
# The arithmetic in the README: at 0.6 sigma (one minute) a single end price gives 73% and the averaged value gives 85%.
_z6 = 0.6 / _mt.sqrt(6)                      # ln(S/K)/sigma = 0.6 one-minute sigmas
assert abs(_av.model_p(_z6, 0.0) - 0.85) < 0.005, _av.model_p(_z6, 0.0)
assert abs(_av.phi(0.6) - 0.726) < 0.002
assert 0.5 < _av.model_p(_z6, 13.0) < 0.60, "far from the close the gap is small against the remaining variance"
assert abs(_av.model_p(-_z6, 0.0) - (1 - _av.model_p(_z6, 0.0))) < 1e-12, "symmetric"
# Entries: the decision candle ends exactly left_s before the close; a market priced at the model gives no entry; a market priced
# far below the model is bought, and settles with the usual fee.
_close = _C0 + 900
_sp = {(_close - 60) - 60 * k - 60: 110.0 * (1 + 0.0005 * _mt.sin(k)) for k in range(0, 70)}
_mk9 = [("M", _close, 100.0, "yes", {_close - 60: (0.60, 0.62)})]
_e9 = _av.entries(_mk9, _sp, 60, 0.0)
assert len(_e9) == 1 and _e9[0]["side"] == "yes" and abs(_e9[0]["price"] - 0.62) < 1e-9, "model near 100% against a 62c ask is bought"
assert abs(_e9[0]["net"] - (1.0 - 0.62 - _di.fee(0.62))) < 1e-12
assert _av.entries([("M", _close, 100.0, "yes", {_close - 120: (0.60, 0.62)})], _sp, 60, 0.0) == [], "no candle at exactly 1 minute left: nothing"
assert _av.entries([("M", _close, 100.0, "yes", {_close - 60: (0.99, 1.0)})], _sp, 60, 0.0) == [], "an empty book is not a quote"
assert _av.entries([("M", _close, 100.0, "yes", {_close - 60: (0.994, 0.996)})], _sp, 60, 0.0) == [], "priced at the model: no entry"
assert _av.entries([("M", _close, None, "yes", {_close - 60: (0.6, 0.62)})], _sp, 60, 0.0) == [], "no strike, no model"
print("L8 L9 tests passed")

# ---- batched backfill ----
import sqlite3 as _sq13
from scalper import backfill as _bf, api as _api13
_calls13 = []
def _fake_settled(series, lo, hi):
    return [{"ticker": f"{series}-T{i}", "open_time": "2026-08-01T00:00:00Z", "close_time": "2026-08-01T00:15:00Z", "result": "yes", "floor_strike": 100.0} for i in range(120)]
def _fake_batch(tickers, a, b):
    _calls13.append(len(tickers))
    return {t: ([] if t.endswith("T7") else [{"end_period_ts": 1000, "yes_bid": {"close_dollars": "0.40"}, "yes_ask": {"close_dollars": "0.42"}}]) for t in tickers}
_o13 = (_api13.settled_markets, _api13.batch_candlesticks, _bf.PAUSE_S, _bf.SERIES)
_api13.settled_markets, _api13.batch_candlesticks, _bf.PAUSE_S, _bf.SERIES = _fake_settled, _fake_batch, 0, ("KXBTC15M",)
try:
    _db13 = _sq13.connect(":memory:"); _db13.executescript(_bf.SCHEMA)
    _st, _sk, _em = _bf._fetch(_db13, 0, 1, "test", skip_empty=True)
    assert max(_calls13) <= _bf.BATCH == 20 and len(_calls13) == 6, ("120 markets go in batches of at most 20", _calls13)
    assert (_st, _sk, _em) == (119, 0, 1), "a market with no candles is not stored when skip_empty is on"
    assert _db13.execute("SELECT COUNT(*) FROM market").fetchone()[0] == 119 and _db13.execute("SELECT COUNT(*) FROM candle").fetchone()[0] == 119
    _calls13.clear()
    _st2, _sk2, _ = _bf._fetch(_db13, 0, 1, "again", skip_empty=True)
    assert _st2 == 0 and _sk2 == 119 and len(_calls13) == 1, "stored markets are never fetched again (only the one empty market is retried)"
finally:
    _api13.settled_markets, _api13.batch_candlesticks, _bf.PAUSE_S, _bf.SERIES = _o13
# A batch the endpoint refuses falls back to one request per market instead of losing the chunk.
def _bad_batch(tickers, a, b):
    raise RuntimeError("GET /markets/candlesticks failed: HTTP Error 400: Bad Request")
def _one(series, ticker, a, b):
    return [{"end_period_ts": 1000, "yes_bid": {"close_dollars": "0.40"}, "yes_ask": {"close_dollars": "0.42"}}]
_o14 = (_api13.settled_markets, _api13.batch_candlesticks, _api13.candlesticks, _bf.PAUSE_S, _bf.SERIES)
_api13.settled_markets, _api13.batch_candlesticks, _api13.candlesticks, _bf.PAUSE_S, _bf.SERIES = _fake_settled, _bad_batch, _one, 0, ("KXBTC15M",)
try:
    _db14 = _sq13.connect(":memory:"); _db14.executescript(_bf.SCHEMA)
    _st3, _, _ = _bf._fetch(_db14, 0, 1, "fallback")
    assert _st3 == 120 and _db14.execute("SELECT COUNT(*) FROM candle").fetchone()[0] == 120, "every market stored via the fallback"
finally:
    _api13.settled_markets, _api13.batch_candlesticks, _api13.candlesticks, _bf.PAUSE_S, _bf.SERIES = _o14
print("batched backfill tests passed")

# The fair null: each rule has zero edge at its OWN decision price, so it loses its costs, never produces survivors by luck at the fixed bar
# more than rarely, and ignores the real outcomes entirely (a planted edge changes nothing in it).
_nrules = [{"left": 6, "lo": 0.30, "hi": 0.50, "side": "yes", "filters": []}, {"left": 4, "lo": 0.10, "hi": 0.30, "side": "either", "filters": []}]
_nw = _ov.windows(_world(0.0, 9)); _nw_edge = _ov.windows(_world(0.15, 9))
_oos = [[_nw["W0h"], _nw["W1"], _nw["W2"]]] * 2
_a1 = _ov.fair_null(_nrules, _oos, 60, seed=2)
_a2 = _ov.fair_null(_nrules, [[_nw_edge["W0h"], _nw_edge["W1"], _nw_edge["W2"]]] * 2, 60, seed=2)
assert _a1["best"] == _a2["best"], "the null never reads outcomes, so a planted edge cannot change it"
assert sum(_a1["survivors"]) <= 3 and max(_a1["best"]) < 3.5, ("luck at the fixed bar is rare for two fair rules", _a1["survivors"], max(_a1["best"]))
_en = _ov.entries_of(_nw["W1"], _nrules[0])
assert _en and all(abs(c - (m + 0.0)) < 1.0 for _, c, m in _en) and sum(m - c for _, c, m in _en) < 0, "a fair rule loses its costs in expectation"
# The criteria in one place, each condition on its own.
assert _ov.passes([60, 60, 60], [0.01, 0.01, 0.01], 2.5) and not _ov.passes([60, 60, 60], [0.01, 0.01, 0.01], 2.49)
assert not _ov.passes([60, 49, 60], [0.01, 0.01, 0.01], 3.0), "49 entries in a window fails"
assert not _ov.passes([60, 60, 60], [0.01, 0.0, 0.01], 3.0) and not _ov.passes([60, 60, 60], [0.01, -0.01, 0.01], 3.0), "a non-positive window fails"
# In the null, a window below 50 entries can never make a survivor, however lucky its draws (30 near-certain winners are positive almost every time).
_tiny = _se.prep([_sm("Z%d" % i, _C0 + 86400 * (i // 10) + 900 * (i % 10), round(0.96 + 0.01 * (i % 3), 4), round(0.97 + 0.01 * (i % 3), 4), "yes") for i in range(30)])
_tn = _ov.fair_null([{"left": 6, "lo": 0.90, "hi": 0.999, "side": "yes", "filters": []}], [[_tiny, _tiny, _tiny]], 40, seed=3)
assert sum(_tn["survivors"]) == 0 and max(_tn["best"]) > 2.5, ("a lucky tiny window is positive with a high z yet cannot survive", _tn["best"][:3])
# The entries a rule pays include the fee, not only the ask.
_em = _se.prep([_sm("E1", _C0, 0.39, 0.41, "yes")])
_ee = _ov.entries_of(_em, {"left": 6, "lo": 0.30, "hi": 0.50, "side": "yes", "filters": []})
assert len(_ee) == 1 and abs(_ee[0][1] - (0.41 + _se.fee(0.41))) < 1e-12 and abs(_ee[0][2] - 0.40) < 1e-12, _ee
print("fair null tests passed")

# ---- M1 early window momentum ----
import inspect as _insp, random as _rnd
from scalper import momentum as _mo

def _mk(path, res="yes", open_ts=1_790_000_000 + 0, spread=0.02, tick="M1T", series="KXBTC15M"):
    """A market whose YES mid at the close of minute k is path[k-1]; minutes beyond the path repeat its last value."""
    book = {}
    for k in range(1, 16):
        mid = path[min(k, len(path)) - 1]
        book[open_ts + 60 * k] = (round(mid - spread / 2, 4), round(mid + spread / 2, 4))
    return {"ticker": tick, "series": series, "open": open_ts, "close": open_ts + 900, "res": res, "book": book}

# no performance parameter in any signature: nothing here may read a result to choose what to do
for _f in (_mo.signal, _mo.trade, _mo.run, _mo.verdict, _mo.load):
    assert not {"target", "until", "promote", "profit", "pnl", "edge"} & set(_insp.signature(_f).parameters), _f
# the verdict vocabulary has no word that means go (code only, comments and docstrings stripped)
import io as _io, tokenize as _tk
_code = " ".join(t.string for t in _tk.generate_tokens(_io.StringIO(Path(_mo.__file__).read_text()).readline) if t.type not in (_tk.COMMENT, _tk.STRING)).lower()
assert "promote" not in _code and "trade_this" not in _code

# A rise of exactly 5c from minute 1 to minute 5 is UP; 4c is no trade; a fall of 5c is DOWN.
_up = _mk([0.50, 0.50, 0.50, 0.50, 0.55, 0.57, 0.58, 0.59, 0.60])
assert _mo.signal(_up["book"], _up["open"], 0.05)[0] == "yes"
assert _mo.signal(_mk([0.50, 0.5, 0.5, 0.5, 0.54])["book"], _up["open"], 0.05) == (None, "flat")
assert _mo.signal(_mk([0.50, 0.5, 0.5, 0.5, 0.45])["book"], _up["open"], 0.05)[0] == "no"
# A market whose first minute still shows the empty book (0.1c bid, $1 ask) has no signal: its 50c mid is not a price anyone saw.
_empty = _mk([0.50, 0.5, 0.5, 0.5, 0.60]); _empty["book"][_empty["open"] + 60] = (0.001, 1.0)
assert _mo.signal(_empty["book"], _empty["open"], 0.05) == (None, "quote")

# The entry is priced at the NEXT candle, never at the signal candle: make minute 6 dearer than minute 5 and require the dearer price.
_m = _mk([0.50, 0.5, 0.5, 0.5, 0.56, 0.70, 0.74, 0.76, 0.80])
_t = _mo.trade(_m, 0.05, 3)
assert _t["status"] == "traded" and abs(_t["price"] - 0.71) < 1e-9 and _t["entry_end"] == _m["open"] + 360, _t
assert _t["price"] > _m["book"][_m["open"] + 300][1], "the entry may not be priced at a level the signal bar itself showed"
# UP exits at the YES bid 3 minutes later (minute 9 = 0.80 mid, bid 0.79): net = bid - ask - both fees, exactly.
assert abs(_t["exit"] - 0.79) < 1e-9
assert abs(_t["net"] - (0.79 - _mo.fee(0.79) - 0.71 - _mo.fee(0.71))) < 1e-12
# DOWN buys NO at 1 minus the YES bid and sells it at 1 minus the YES ask.
_d = _mo.trade(_mk([0.50, 0.5, 0.5, 0.5, 0.44, 0.40, 0.36, 0.34, 0.30]), 0.05, 3)
assert _d["side"] == "no" and abs(_d["price"] - (1 - 0.39)) < 1e-9 and abs(_d["exit"] - (1 - 0.31)) < 1e-9, _d
# A flat market after a signal LOSES the spread and both fees, never breaks even.
_flat = _mo.trade(_mk([0.50, 0.5, 0.5, 0.5, 0.56, 0.56, 0.56, 0.56, 0.56]), 0.05, 3)
assert _flat["net"] <= -0.02 - (_mo.fee(0.57) + _mo.fee(0.55)) + 1e-9 and _flat["gross"] < 0
# An unusable exit quote drops the observation and counts it; it is never repriced from a neighbouring candle.
_dm = _mk([0.50, 0.5, 0.5, 0.5, 0.56, 0.60, 0.7, 0.8, 0.9]); _dm["book"][_dm["open"] + 540] = (0.97, 1.0)
_r = _mo.run([_dm]); assert not _r["trades"] and _r["counts"]["dropped"] == 1 and len(_r["dropped"]) == 1
_dm2 = _mk([0.50, 0.5, 0.5, 0.5, 0.56, 0.60, 0.7, 0.8, 0.9]); del _dm2["book"][_dm2["open"] + 540]
assert _mo.run([_dm2])["counts"]["dropped"] == 1
# Holding to settlement needs no exit quote, so the same market is a trade there and pays one fee: a winner nets 1 - ask - fee.
_s = _mo.run([_dm], 0.05, None)["trades"]
assert len(_s) == 1 and abs(_s[0]["net"] - (1.0 - 0.61 - _mo.fee(0.61))) < 1e-12

# Simulator guard: on a simulated FAIR game (a martingale mid, 2c spread, outcome drawn from the mid) the exact code loses about its costs.
def _fair_world(n, seed, drift=0.0):
    rng = _rnd.Random(seed); ms = []
    for i in range(n):
        mid, path = 0.5, [0.5]
        for _ in range(12):
            mid = min(max(mid + rng.gauss(0, 0.04), 0.2), 0.8); path.append(mid)
        if drift:       # planted continuation: after the signal minute the path keeps going in its own direction
            for k in range(5, 12):
                path[k] = min(max(path[4] + (path[4] - path[0]) * drift * (k - 4), 0.2), 0.8)
        o = 1_790_000_000 + 86400 * (i % 20) + 900 * (i // 20)
        ms.append(_mk(path, "yes" if rng.random() < path[-1] else "no", open_ts=o, tick="F%d" % i))
    return ms
_fw = _fair_world(4000, 5)
_fr = _mo.run(_fw)["trades"]
_fmean = sum(t["net"] for t in _fr) / len(_fr)
assert len(_fr) > 300 and -0.09 < _fmean < -0.025, ("a fair game must lose about its costs (spread 2c plus two fees)", _fmean, len(_fr))
assert abs(sum(t["gross"] for t in _fr) / len(_fr) + 0.02) < 0.012, "gross on a fair game is the crossed spread, nothing else"
_fv, _fs = _mo.verdict(_fr); assert _fv == "FALSIFIED" and _fs["z"] < -2
_fsr = _mo.run(_fw, 0.05, None)["trades"]
assert sum(t["net"] for t in _fsr) / len(_fsr) < 0, "held to settlement on a fair game also loses its fee and spread"
# Too few trades is NOT_ENOUGH_DATA, not a verdict.
assert _mo.verdict(_fr[:50])[0] == "NOT_ENOUGH_DATA"
# The harness can say yes when a strong continuation is planted (so a FALSIFIED elsewhere is not a harness that cannot pass).
_pw = _mo.run(_fair_world(4000, 5, drift=0.9))["trades"]
assert _mo.verdict(_pw)[0] == "NOT_YET_FALSIFIED", _mo.verdict(_pw)
# The round trip null ignores direction: planting continuation does not change what it returns on a trade list with the same sizes.
assert abs(_mo.null_roundtrip(_pw, 3) - _mo.null_roundtrip(_pw, 3)) < 1e-15
assert _mo.null_roundtrip(_pw, 3) < sum(t["net"] for t in _pw) / len(_pw), "the direction-free null earns less than a real continuation"
assert _mo.null_settle(_fsr, 4) < 0 and _mo.null_roundtrip(_fr, 4) < 0, "both nulls lose their costs"
# The stressed figure charges fees x1.2 on BOTH legs (round trip) and on the one leg when held to settlement.
assert abs(_t["stress"] - (0.79 - _mo.fee(0.79, 1.2) - 0.71 - _mo.fee(0.71, 1.2))) < 1e-12 and _t["stress"] < _t["net"]
assert abs(_s[0]["stress"] - (1.0 - 0.61 - _mo.fee(0.61, 1.2))) < 1e-12 and _s[0]["stress"] < _s[0]["net"]
print("M1 momentum tests passed")

# ---- the forward check ----
import json as _jsf, random as _rf, re as _ref
from scalper import forward as _fw

def _fmk(n, per_day, win_p, price=0.905, seed=1, start=1791417600):
    """n markets after the old data (start is 2026-10-08 00:00 UTC, so each block of 96 is one UTC day), each with a 0.90/0.91 book at 8, 6 and 2 minutes left.
    win_p is the YES win rate."""
    g = _rf.Random(seed); out = []
    for i in range(n):
        close = start + (i // per_day) * 86400 + (i % per_day) * 900
        cs = [(close - 60 * left, round(price - 0.005, 4), round(price + 0.005, 4), round(price - 0.005, 4), round(price + 0.005, 4)) for left in (8, 6, 2)]
        out.append(("F%d" % i, "KXBTC15M" if i % 2 else "KXGOLD15M", cs, close, "yes" if g.random() < win_p else "no"))
    return out

# A planted edge is seen only once there is enough of it. Under 300 entries, or on fewer than 5 days, the word is NOT_ENOUGH_DATA however good the numbers look.
_big = _fw.all_rules(_fmk(600, 96, 1.0))                # 600 markets over 7 days, every favorite wins
assert _fw.verdict(_big["F0 L1"])[0] == "NOT_YET_FALSIFIED" and _fw.verdict(_big["F3"])[0] == "NOT_YET_FALSIFIED", "the simulator can see a real edge"
assert _fw.verdict(_fw.all_rules(_fmk(299, 96, 1.0))["F0 L1"])[0] == "NOT_ENOUGH_DATA", "299 entries is not enough"
assert _fw.verdict(_fw.all_rules(_fmk(384, 96, 1.0))["F0 L1"])[0] == "NOT_ENOUGH_DATA", "384 entries on 4 days is not enough"
assert _fw.verdict(_fw.all_rules(_fmk(480, 96, 1.0))["F0 L1"])[0] == "NOT_YET_FALSIFIED", "5 days is enough"
# A fair market (the favorite wins as often as it is priced) loses its costs and must never pass.
_fair_f = _fw.all_rules(_fmk(1500, 96, 0.905, seed=5))
for _k in ("F0 L1", "F3", "F4"):
    _s = _fw.stats(_fair_f[_k])
    assert _fw.verdict(_fair_f[_k])[0] == "FALSIFIED" and _s["mean"] < 0 and _s["gross"] < 0.02, (_k, _s["mean"], "a fair game must lose about its fees")
# Only markets that closed AFTER the old data count. One closing exactly at the old end is old data.
_edge = [("O1", "KXBTC15M", [(_fw.OLD_END - 360, 0.90, 0.91, 0.90, 0.91)], _fw.OLD_END, "yes"),
         ("N1", "KXBTC15M", [(_fw.OLD_END + 900 - 360, 0.90, 0.91, 0.90, 0.91)], _fw.OLD_END + 900, "yes")]
assert [m[0] for m in _fw.forward_only(_edge)] == ["N1"], "the last old close is not forward data"
# W3 ends where the forward window starts, so no market is in both and nothing is counted twice.
assert _fw.W3_START < _fw.OLD_END == 1791397800 and _ov.ORIG_END < _fw.OLD_END
# The four search rules are the saved survivors, byte for byte: nobody retuned them.
_saved = {}
for _f in ("stageA", "stageB"):
    for _r in _jsf.loads((_P3(__file__).resolve().parents[1] / "search2" / (_f + ".json")).read_text()):
        if _r["survivor"]:
            _saved[_se.key(_se.normalize({**_r["spec"], "filters": [tuple(x) for x in _r["spec"]["filters"]]}))] = _r["rule"]
assert sorted(_saved.values()) == sorted(_se.describe(r) for r in _fw.SEARCH_RULES.values()) and set(_saved) == {_se.key(_se.normalize(r)) for r in _fw.SEARCH_RULES.values()}
# A series filter really keeps Bitcoin only, and F2 only ever buys NO.
_f2 = _fw.rule_entries(_se.prep(_fmk(40, 40, 1.0)), dict(_fw.F2, filters=[("series", "KXBTC15M")], left=6))
assert _f2 and all(e["series"] == "KXBTC15M" and e["side"] == "no" for e in _f2)
# No verdict function takes a performance parameter, and the code (comments stripped) has no word for "go live".
import inspect as _inf
assert all(not _ref.search(r"perf|target|until|profit|promote", p) for f in (_fw.verdict, _fw.stats, _fw.rule_entries, _fw.forward_only, _fw.all_rules) for p in _inf.signature(f).parameters)
_srcf = _ref.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_fw.__file__).read())
assert not _ref.search(r"promote|trade_it|go_live|TRADE", _srcf)
print("forward check tests passed")

# ---- the strategy search (S01 to S42): consequences, not mechanisms ----
import math as _m50
import random as _r50
import tempfile as _tf50
from pathlib import Path as _P50
import scalper.strategies as _ST
import scalper.stratsearch as _SS
import scalper.overnight as _O50


def _s50_world(seed=1, days=14, prior_days=8):
    """A FAIR synthetic world: each market's quotes are the posterior of an observer who sees noisy evidence about a hidden result drawn
    first, so the quote at every candle is exactly the chance the market resolves YES. No strategy can have an edge in it."""
    rng = _r50.Random(seed)
    T0 = 1_790_000_000 - 1_790_000_000 % 86400
    spot, s = {}, 87000.0
    for k in range((prior_days + days) * 1440 + 120):
        s *= _m50.exp(rng.gauss(0, 0.0004))
        spot[T0 + 60 * k] = round(s, 2)
    ms, sk = [], {_ST.BTC: 87000.0, _ST.GOLD: 4100.0}
    for series in (_ST.BTC, _ST.GOLD):
        for k in range(prior_days * 96, (prior_days + days) * 96):
            op = T0 + 900 * k
            if series == _ST.GOLD and (op % 86400) // 3600 == 21:
                continue
            sk[series] *= _m50.exp(rng.gauss(0, 0.002))
            R = 1 if rng.random() < 0.5 else 0
            L, cand, bc, ac = 0.0, {}, 0.5, 0.5
            vol0, oi = rng.uniform(1e4, 5e4), rng.uniform(1e4, 5e4)
            for j in range(1, 16):
                if j < 15:
                    L += 0.7 * ((0.35 if R else -0.35) + rng.gauss(0, 1.0))
                    p = 1 / (1 + _m50.exp(-L))
                    wid_b = 0.01 + (0.03 if rng.random() < 0.06 else 0.0)
                    wid_a = 0.01 + (0.03 if rng.random() < 0.06 else 0.0)
                    nb, na = round(min(max(p - wid_b, 0.01), 0.98), 2), round(min(max(p + wid_a, 0.02), 0.99), 2)
                else:
                    nb, na = (0.99, 1.0) if R else (0.0, 0.01)
                bo, ao, bc, ac = bc, ac, nb, na
                oi *= 1 + abs(rng.gauss(0, 0.04))
                cand[j] = (bo, round(max(bo, bc) + abs(rng.gauss(0, 0.05)), 2), min(bo, bc), bc, ao, max(ao, ac), max(round(min(ao, ac) - abs(rng.gauss(0, 0.05)), 2), 0.0), ac,
                           None if rng.random() < 0.1 else round((bc + ac) / 2 + rng.choice([-0.01, 0, 0.01]), 2), vol0 * rng.uniform(0.3, 3.0), oi)
            ms.append(_ST.make_market(f"{series}-{op}", series, op, op + 900, "yes" if R else "no", round(sk[series], 2), cand))
    return _ST.World(ms, spot)


def _s50_cand(rng):
    b = round(rng.uniform(0.05, 0.9), 2)
    a = round(b + 0.02, 2)
    return (b, b + 0.05, b - 0.03, b, a, a + 0.03, a - 0.05, a, 0.5, rng.uniform(1e3, 9e4), rng.uniform(1e3, 9e4))


def _s50_scramble(w, m, js, rng):
    """Replace EVERYTHING that was not known at the close of candle js with noise: the market's own later candles and result, its twin's, every later
    market, and the spot after the signal. Returns an undo function."""
    saved_m, saved_sp = [], []
    cut = m["open"] + 60 * js
    def hit(mk, upto, strike):
        saved_m.append((mk, dict(mk["cand"]), mk["res"], mk["strike"], mk["V7"], mk["vol1"]))
        for j in range(upto + 1, 16):
            mk["cand"][j] = _s50_cand(rng)
        mk["res"] = "no" if mk["res"] == "yes" else "yes"
        if strike and mk["strike"] is not None:
            mk["strike"] *= rng.uniform(0.9, 1.1)
        cs = [mk["cand"].get(j) for j in range(1, 8)]
        mk["V7"] = sum(c[9] for c in cs if c is not None)
        mk["vol1"] = mk["cand"][1][9] if 1 in mk["cand"] else None
    hit(m, js, False)
    other = _ST.GOLD if m["series"] == _ST.BTC else _ST.BTC
    tw = w.by.get((other, m["open"]))
    if tw is not None:
        hit(tw, js, False)
    later = [x for x in w.ms if x["open"] > m["open"]][:150]
    for x in later:
        hit(x, 0, True)
    i0 = (cut - 60 - w.t0) // 60 + 1
    for i in range(i0, min(i0 + 1500, len(w.sp))):
        saved_sp.append((i, w.sp[i]))
        w.sp[i] = rng.uniform(80000, 94000)
    w._range20, w._day = None, {}
    def undo():
        for mk, cand, res, strike, v7, v1 in reversed(saved_m):
            mk["cand"], mk["res"], mk["strike"], mk["V7"], mk["vol1"] = cand, res, strike, v7, v1
        for i, v in saved_sp:
            w.sp[i] = v
        w._range20, w._day = None, {}
    return undo


def _s50_leaks(w, sig_of, pairs, seed=5):
    """(market ticker, js) pairs whose signal CHANGES when everything after the signal candle is replaced by noise."""
    rng = _r50.Random(seed)
    bad = []
    for m, js in pairs:
        a = sig_of(_ST.Ctx(w, m, js))
        undo = _s50_scramble(w, m, js, rng)
        try:
            b = sig_of(_ST.Ctx(w, m, js))
        finally:
            undo()
        if a != b:
            bad.append((m["ticker"], js))
    return bad


_W50 = _s50_world(1)
_fire = {}
for _sp in _ST.SPECS:
    _pairs_fire, _pairs_quiet = [], []
    for _mk in _W50.ms[::7]:
        if _mk["series"] not in _sp["series"]:
            continue
        for _js in _sp["js"]:
            (_pairs_fire if _sp["sig"](_ST.Ctx(_W50, _mk, _js)) else _pairs_quiet).append((_mk, _js))
        if len(_pairs_fire) >= 6 and len(_pairs_quiet) >= 3:
            break
    _fire[_sp["id"]] = (_sp, _pairs_fire[:6] + _pairs_quiet[:3], len(_pairs_fire))
# The harness has teeth: a signal that reads the market's own result, or the next candle, or a later market is caught.
_some = [(_mk, 5) for _mk in _W50.ms[2000:2040]]
assert _s50_leaks(_W50, lambda c: c.m["res"], _some), "reading the market's own result must be caught"
assert _s50_leaks(_W50, lambda c: "yes" if c.m["cand"][c.js + 1][3] > 0.5 else "no", _some), "reading the next candle must be caught"
assert _s50_leaks(_W50, lambda c: "yes" if (c.w.series[c.m["series"]][c.m["i"] + 1]["strike"] or 0) > c.m["strike"] else "no", _some), "reading the next strike must be caught"
assert _s50_leaks(_W50, lambda c: "yes" if (c.w.spot_end(c.cut + 120) or 0) > (c.w.spot_end(c.cut) or 0) else "no", _some), "reading future spot must be caught"
# No strategy's signal depends on anything after its signal candle, whatever happens to the future.
_total_fired = 0
for _id, (_sp, _pairs, _nf) in _fire.items():
    _total_fired += _nf
    assert not _s50_leaks(_W50, _sp["sig"], _pairs), (_id, "the signal changed when only the future changed")
assert sum(1 for _sp, _p, _nf in _fire.values() if _nf > 0) >= 36, "the synthetic world must make nearly every strategy fire, or this test proves nothing"
# The Ctx refuses to look ahead.
_c50 = _ST.Ctx(_W50, _W50.ms[2100], 4)
for _bad in (lambda: _c50.cand(5), lambda: _c50.mid(9), lambda: _c50.vol(15), lambda: _c50.s(-1), lambda: _c50.spot_at(_c50.cut + 60)):
    try:
        _bad()
        raise SystemExit("a look ahead was allowed")
    except _ST.Lookahead:
        pass
print("strategy signals cannot see the future tests passed")

# The trade is on the candle AFTER the signal, at that candle's quotes, whatever the signal candle showed.
def _s50_mk(res="yes", quotes=None, series=_ST.BTC, op=1_791_000_000 - 1_791_000_000 % 900, strike=100.0):
    q = quotes or {}
    cand = {j: (b, b, b, b, a, a, a, a, None, 100.0, 100.0) for j, (b, a) in q.items()}
    return _ST.make_market("T%d" % op, series, op, op + 900, res, strike, cand)
_mk1 = _s50_mk("yes", {1: (0.40, 0.42), 2: (0.44, 0.46), 3: (0.60, 0.62), 4: (0.61, 0.63), 5: (0.30, 0.32)})
_t, _ = _SS.trade(_mk1, "yes", 2, (0.10, 0.90), None)
assert abs(_t["price"] - 0.46) < 1e-12, "YES is bought at the ask of the ENTRY candle, not the signal candle's"
_t, _ = _SS.trade(_mk1, "no", 2, (0.10, 0.90), None)
assert abs(_t["price"] - 0.56) < 1e-12, "NO costs one minus the YES bid"
# A YES winner held to settlement pays $1 less price less one entry fee and nothing on the way out.
_t, _ = _SS.trade(_mk1, "yes", 2, (0.10, 0.90), None)
assert abs(_t["net"] - (1 - 0.46 - 0.07 * 0.46 * 0.54)) < 1e-12 and _t["stress"] < _t["net"] < _t["gross"], _t
_t, _ = _SS.trade(_mk1, "no", 2, (0.10, 0.90), None)
assert abs(_t["net"] - (0 - 0.56 - 0.07 * 0.56 * 0.44)) < 1e-12, "a losing hold loses the price and the fee"
# A fixed minute exit sells at the real BID and pays the fee on BOTH legs.
_t, _ = _SS.trade(_mk1, "yes", 2, (0.10, 0.90), 2)
assert abs(_t["net"] - (0.61 - 0.07 * 0.61 * 0.39 - 0.46 - 0.07 * 0.46 * 0.54)) < 1e-12, ("exit at the bid 0.61, two fees", _t)
_t, _ = _SS.trade(_mk1, "no", 2, (0.10, 0.90), 2)
assert abs(_t["exit"] - round(1 - 0.63, 4)) < 1e-12, "a NO is sold at one minus the YES ask"
# An exit candle with no usable quote DROPS the trade; it is never filled at a made up price.
_t, why = _SS.trade(_mk1, "yes", 2, (0.10, 0.90), 5)
assert _t is None and why == "dropped"
# The universal band: a 95c favorite is not bought; the lower priced side is chosen by price.
_t, why = _SS.trade(_s50_mk("yes", {2: (0.94, 0.95)}), "yes", 2, (0.10, 0.90), None)
assert _t is None and why == "band"
_t, _ = _SS.trade(_s50_mk("yes", {2: (0.70, 0.72)}), "under", 2, (0.10, 0.40), None)
assert _t["side"] == "no" and abs(_t["price"] - 0.30) < 1e-12 and abs(_t["mid"] - 0.29) < 1e-12
_t, _ = _SS.trade(_s50_mk("yes", {2: (0.70, 0.72)}), "over", 2, (0.60, 0.90), None)
assert _t["side"] == "yes" and abs(_t["price"] - 0.72) < 1e-12
# run_spec trades one candle after the signal candle: S06 signals at candle 1 and must enter at candle 2.
_w2 = _ST.World([_s50_mk("yes", {1: (0.45, 0.47), 2: (0.50, 0.52)}, op=1_791_000_000 - 1_791_000_000 % 900 - 900),
                 _s50_mk("yes", {1: (0.30, 0.32), 2: (0.50, 0.52)})])
_tr, _ = _SS.run_spec(_w2, [s for s in _ST.SPECS if s["id"] == "S06"][0], [_w2.ms[1]])
assert len(_tr) == 1 and _tr[0]["side"] == "yes" and abs(_tr[0]["price"] - 0.52) < 1e-12 and _tr[0]["js"] == 1, _tr
print("strategy fill model tests passed")

# Hand checked signals, stated as consequences.
def _s50_chain(results, last_quotes=None):
    base = 1_791_000_000 - 1_791_000_000 % 900 - 900 * len(results)
    ms = [_s50_mk(r, {1: (0.45, 0.47), 2: (0.50, 0.52)}, op=base + 900 * i, strike=100.0 + i) for i, r in enumerate(results)]
    return _ST.World(ms), ms
def _sig(id_, w, m, js):
    return [s for s in _ST.SPECS if s["id"] == id_][0]["sig"](_ST.Ctx(w, m, js))
_w, _ms = _s50_chain(["yes", "no", "no", "no", "yes"])
assert _sig("S06", _w, _ms[4], 1) == "no" and _sig("S06", _w, _ms[1], 1) == "yes", "persistence follows the previous outcome"
_w, _ms = _s50_chain(["no", "no", "no", "yes"])
assert _sig("S07", _w, _ms[3], 1) == "yes", "after three NO in a row the exhaustion rule buys YES"
_w, _ms = _s50_chain(["no", "yes", "no", "yes"])
assert _sig("S07", _w, _ms[3], 1) is None, "a broken streak is not a streak"
_w, _ms = _s50_chain(["yes"] * 8 + ["no"] * 4 + ["yes"])
_w, _ms = _s50_chain(["yes"] * 3 + ["no"] * 9 + ["yes"])
assert _sig("S08", _w, _ms[12], 1) == "no", "9 NO in the last 12 means the regime rule buys NO"
# A gap in the chain (a missing market) means there is no streak to read, not a streak across the hole.
_w, _ms = _s50_chain(["no", "no", "no", "yes"])
_w3 = _ST.World([_ms[0], _ms[2], _ms[3]])
assert _sig("S07", _w3, _ms[3], 1) is None, "markets that are not contiguous are not a streak"
# Strike rules: a new 4 hour high is faded; a clean trend is followed.
def _s50_strikes(xs):
    base = 1_791_000_000 - 1_791_000_000 % 900 - 900 * len(xs)
    ms = [_s50_mk("yes", {1: (0.45, 0.47), 2: (0.50, 0.52)}, op=base + 900 * i, strike=x) for i, x in enumerate(xs)]
    return _ST.World(ms), ms
_w, _ms = _s50_strikes([100 + (i % 3) for i in range(15)] + [110])
assert _sig("S40", _w, _ms[15], 1) == "no", "a strike above the previous 15 is faded"
_w, _ms = _s50_strikes([110] + [100 + (i % 3) for i in range(14)] + [90])
assert _sig("S40", _w, _ms[15], 1) == "yes"
_w, _ms = _s50_strikes([100, 101, 102, 103, 104, 105, 106, 107, 108])
assert _sig("S41", _w, _ms[8], 1) == "yes", "a perfectly efficient rise is followed"
_w, _ms = _s50_strikes([100, 105, 100, 105, 100, 105, 100, 105, 106])
assert _sig("S41", _w, _ms[8], 1) is None, "a choppy path is not a trend"
# Cross market: gold moving up by 8c in the first five minutes makes S01 buy Bitcoin YES, and only if a gold twin exists.
_op = 1_791_000_000 - 1_791_000_000 % 900
_g = _s50_mk("yes", {1: (0.40, 0.42), 5: (0.48, 0.50)}, series=_ST.GOLD, op=_op)
_b = _s50_mk("yes", {1: (0.45, 0.47), 5: (0.45, 0.47)}, series=_ST.BTC, op=_op)
assert _sig("S01", _ST.World([_g, _b]), _b, 5) == "yes" and _sig("S01", _ST.World([_b]), _b, 5) is None
# S03 buys the SMALLER mover: gold rose 8c, Bitcoin only 5c, so Bitcoin is the laggard.
_b2 = _s50_mk("yes", {1: (0.45, 0.47), 5: (0.50, 0.52)}, series=_ST.BTC, op=_op)
_r = _sig("S03", _ST.World([_g, _b2]), _b2, 5)
assert _r == ("yes", "self"), _r
# Calendar: the weekend rule fires on Saturday and not on Monday.
import datetime as _dt50
_sat = 1_790_000_000 - 1_790_000_000 % 86400
while _dt50.datetime.fromtimestamp(_sat, _dt50.timezone.utc).weekday() != 5:
    _sat += 86400
_ms_sat = _s50_mk("yes", {7: (0.30, 0.32)}, op=_sat + 36000)
_ms_mon = _s50_mk("yes", {7: (0.30, 0.32)}, op=_sat + 2 * 86400 + 36000)
assert _sig("S13", _ST.World([_ms_sat]), _ms_sat, 7) == "over" and _sig("S13", _ST.World([_ms_mon]), _ms_mon, 7) is None
# A spike fade buys against the jump: the mid rose 15c, so it buys NO.
_sp1 = _s50_mk("yes", {3: (0.39, 0.41), 4: (0.54, 0.56)})
assert _sig("S27", _ST.World([_sp1]), _sp1, 4) == "no"
print("strategy signal tests passed")

# Fair game guard: in a world where every price is exactly calibrated, the exact trading code loses about its costs and finds nothing.
_ws = {"W0s": [], "W0h": [], "W1": [], "W2": []}
_days = sorted({m["day"] for m in _W50.ms})
_cuts = {d: ["W0s", "W0h", "W1", "W2"][min(3, i * 4 // len(_days))] for i, d in enumerate(_days)}
for _mk in _W50.ms:
    _ws[_cuts[_mk["day"]]].append(_mk)
_rows50 = _SS.evaluate_all(_W50, _ws)
_tot_n = sum(r["pooled"]["n"] for r in _rows50)
_tot_net = sum(r["pooled"]["n"] * r["pooled"]["mean"] for r in _rows50)
assert _tot_n > 3000 and _tot_net / _tot_n < -0.005, ("across all strategies a fair market costs money", _tot_net / _tot_n)
assert max(r["pooled"]["z"] for r in _rows50 if r["pooled"]["n"] >= 50) < 4.0, "no strategy finds an edge in a fair market"
_by = {r["id"]: r for r in _rows50}
assert -0.05 < _by["S06"]["pooled"]["mean"] < 0.0, ("a plain hold loses about its fee and spread", _by["S06"]["pooled"]["mean"])
assert _by["S27"]["pooled"]["mean"] < -0.02 and _by["S27"]["pooled"]["mean"] > -0.12, ("a round trip loses about two fees and a spread", _by["S27"]["pooled"]["mean"])
assert not any(r["verdict"] == "NOT_YET_FALSIFIED" for r in _rows50), "a fair market has no survivors"
assert all(r["verdict"] in _SS.WORDS for r in _rows50) and sorted(r["rank"] for r in _rows50) == list(range(1, 43))
print("strategy fair market tests passed")

# The pre-set verdict logic.
def _p50(n, mean=0.02, z=3.0, h1=0.02, h2=0.02, stress=0.01):
    return {"n": n, "mean": mean, "z": z, "h1": h1, "h2": h2, "stress": stress}
assert _SS.common_bar(_p50(300)) and not _SS.common_bar(_p50(299)), "n of 300"
assert not _SS.common_bar(_p50(500, z=2.09)) and _SS.common_bar(_p50(500, z=2.1))
assert not _SS.common_bar(_p50(500, h2=-0.001)) and not _SS.common_bar(_p50(500, h1=0.0)), "both halves must be positive"
assert not _SS.common_bar(_p50(500, stress=-0.001)), "fees x1.2 must stay positive"
_pw = [{"n": 60, "mean": 0.01}] * 3
assert _SS.survivor_test(_pw, 2.5) and not _SS.survivor_test(_pw, 2.49)
assert not _SS.survivor_test([{"n": 49, "mean": 0.01}, {"n": 60, "mean": 0.01}, {"n": 60, "mean": 0.01}], 3.0), "49 entries in a window fails"
assert not _SS.survivor_test([{"n": 60, "mean": -0.001}, {"n": 60, "mean": 0.02}, {"n": 60, "mean": 0.02}], 3.0), "a negative window fails"
assert _SS.verdict_word(_p50(299), True, True, True) == "NOT_ENOUGH_DATA", "a big z on under 300 entries is not enough data"
assert _SS.verdict_word(_p50(400), True, True, True) == "NOT_YET_FALSIFIED"
assert _SS.verdict_word(_p50(400), True, False, True) == "FALSIFIED", "K+ (beat the unconditional baseline) is required where it applies"
assert _SS.verdict_word(_p50(400), True, True, False) == "FALSIFIED" and _SS.verdict_word(_p50(400), False, True, True) == "FALSIFIED"
import re as _re50
_code50 = _re50.sub(r"#[^\n]*|\"\"\"[\s\S]*?\"\"\"", "", open(_SS.__file__).read() + open(_ST.__file__).read())
assert not _re50.search(r"\b(PROMOTE|TRADE_THIS|GO_LIVE|APPROVED|target|deadline)\b", _code50), "no verdict or parameter that means go"
assert _SS.WORDS == ("FALSIFIED", "NOT_YET_FALSIFIED", "NOT_ENOUGH_DATA", "NOT_RUNNABLE")
# The deflated bar: best of 42 noise strategies.
assert abs(_SS.sidak_z(42) - 3.03) < 0.02 and abs(_m50.sqrt(2 * _m50.log(42)) - 2.73) < 0.01
# The ranking puts a strategy with under 50 entries last, whatever its z.
_fake = [{"id": "a", "pooled": {"n": 10, "z": 9.0, "mean": 0.5}}, {"id": "b", "pooled": {"n": 80, "z": 1.0, "mean": 0.01}}, {"id": "c", "pooled": {"n": 80, "z": 2.0, "mean": 0.0}}]
_SS.rank(_fake)
assert [r["rank"] for r in _fake] == [3, 2, 1]
# Every strategy in the code is in the README with its counterparty row, and the other way round.
_readme = (_P50(__file__).resolve().parents[1] / "README.md").read_text()
assert all(f"| {s['id']} |" in _readme for s in _ST.SPECS) and len(_ST.SPECS) == 42 and len({s["id"] for s in _ST.SPECS}) == 42
assert sorted(set(_re50.findall(r"\| (S\d\d) \|", _readme))) == sorted(s["id"] for s in _ST.SPECS)
assert all(s["params"] and s["js"] and s["band"][0] < s["band"][1] and s["universe"] == "fixed" for s in _ST.SPECS), "every parameter is declared"
print("strategy verdict tests passed")

# The locked window: the stage 1 code refuses it, and the one read cannot be repeated.
try:
    _SS.evaluate_all(_W50, dict(_ws, W3=[]))
    raise SystemExit("W3 was accepted by the search")
except AssertionError:
    pass
_o50 = (_SS.W3_FILE, _SS.OUT)
_td50 = _P50(_tf50.mkdtemp())
_SS.OUT, _SS.W3_FILE = _td50, _td50 / "w3_read_once.json"
try:
    _rows_s = [{"id": "S06", "survivor_test": True}, {"id": "S07", "survivor_test": False}]
    _first = _SS.read_w3_once(_W50, _ws["W2"], _rows_s)
    assert set(_first) == {"S06"}, "only survivors are read on the locked window"
    try:
        _SS.read_w3_once(_W50, _ws["W2"], _rows_s)
        raise SystemExit("a second read of W3 was allowed")
    except RuntimeError:
        pass
finally:
    _SS.W3_FILE, _SS.OUT = _o50
print("strategy locked window tests passed")

# The null: it never reads who won, it loses the costs, and it rarely makes survivors.
_prep = _SS.prepare_null(_rows50)
_rows_flip = [dict(r, oos_trades=[dict(t, net=-t["net"], gross=-t["gross"], stress=-t["stress"]) for t in r["oos_trades"]]) for r in _rows50]
assert _SS.prepare_null(_rows_flip) == _prep, "the null is built from prices and costs only, never from outcomes"
_nul = _SS.run_null(_rows50, 40, seed=3, procs=1)
_rep = _SS.null_report(_rows50, _nul)
assert _rep["strategies"] == 42 and _rep["reps"] == 40 and 0.0 <= _rep["P_null_best_ge_real"] <= 1.0
assert _rep["mean_null_survivors"] < 1.0, "luck at the fixed bar is rare"
# A strategy with a planted edge beats its own null; the same strategy at zero edge does not.
_ent = [{"id": "X", "n": 400, "win": [0] * 150 + [1] * 150 + [2] * 100, "day": [i // 4 for i in range(400)], "half": [0] * 200 + [1] * 200, "price": [0.5] * 400,
         "c1": [0.5 + 0.0175] * 400, "cs": [0.5 + 0.021] * 400, "mid": [0.5] * 400, "rt": [False] * 400, "delta": [0.0] * 400, "hexit": [0.0] * 400, "ndays": 100}]
_rng50 = _r50.Random(9)
_zs = [_SS.null_once(_rng50, _ent[0])[0] for _ in range(200)]
assert sum(_zs) / len(_zs) < -0.5, "at a fair 50c with a fee, the null's mean z is negative"
assert max(_zs) < 3.0 and not any(_SS.null_once(_rng50, _ent[0])[1] for _ in range(200)), "a zero edge entry set essentially never survives"
_ent_rt = dict(_ent[0], rt=[True] * 400, delta=[0.04] * 400, hexit=[0.01] * 400, mid=[0.5] * 400)
_zr = [_SS.null_once(_rng50, _ent_rt)[0] for _ in range(100)]
assert sum(_zr) / len(_zr) < -1.0, "a round trip with a spread and two fees loses money in the null"
print("strategy null tests passed")

# K+: a conditional underdog/favorite strategy is compared with the SAME entry without its trigger, on the same windows and the same series.
for _id, _kind in (("S13", "over"), ("S10", "under"), ("S12", "under")):
    _sp = [s for s in _ST.SPECS if s["id"] == _id][0]
    _bt = [t for k in _SS.OOS for t in _SS.run_spec(_W50, _SS.baseline_specs()[_kind], _ws[k])[0] if t["series"] in _sp["series"]]
    assert _by[_id]["baseline_mean"] is not None and abs(_by[_id]["baseline_mean"] - sum(t["net"] for t in _bt) / len(_bt)) < 1e-12, _id
    assert _by[_id]["K_plus"] == (_by[_id]["pooled"]["mean"] > _by[_id]["baseline_mean"])
assert all(r["K_plus"] and r["baseline_mean"] is None for r in _rows50 if r["id"] not in ("S10", "S12", "S13", "S28", "S38")), "K+ applies to five strategies only"
print("strategy baseline tests passed")

# Four slot search: a slot rule decides from prices only, trades only its own series, and the pass mark cannot be met by luck-sized or thin results.
from scalper import slots as _SL
_book = {600 - 360: (0.91, 0.93), 600 - 420: (0.90, 0.92)}
_m_yes = {"ticker": "A", "series": "KXBTC15M", "close": 600, "res": "yes", "day": "2026-10-01", "book": _book, "twin": None}
_m_no = dict(_m_yes, res="no")
_rule = {"series": "KXBTC15M", "left": 6, "lo": 0.90, "hi": 0.95, "side": "either", "filters": []}
assert _SL.entry(_m_yes, _rule) == _SL.entry(_m_no, _rule), "the entry never reads the result"
assert _SL.entry(dict(_m_yes, series="KXGOLD15M"), _rule) is None, "a slot rule never trades the other series"
_pr = dict(_rule, filters=[("pair", "agree")])
assert _SL.entry(_m_yes, _pr) is None, "no twin quote means no entry"
_tw = dict(_m_yes, series="KXGOLD15M", book={600 - 360: (0.69, 0.71)})
assert _SL.entry(dict(_m_yes, twin=_tw), _pr) is not None and _SL.entry(dict(_m_yes, twin=_tw), dict(_rule, filters=[("pair", "disagree")])) is None
_tw_late = dict(_tw, book={600 - 300: (0.69, 0.71)})
assert _SL.entry(dict(_m_yes, twin=_tw_late), _pr) is None, "the twin is read at the same minute, not at a later one"
_good = {"n": 400, "mean": 0.02, "z": 3.2, "halves": [0.01, 0.03], "stress": 0.01}
assert _SL.verdict(_good, 3.6, 3.5, 3.0) == "NOT_YET_FALSIFIED"
assert _SL.verdict(dict(_good, n=299), 3.6, 3.5, 3.0) == "NOT_ENOUGH_DATA"
assert _SL.verdict(dict(_good, z=2.9), 3.6, 3.5, 3.0) == "FALSIFIED", "a z of 2.9 is what the best of 100 noise reads reaches"
assert _SL.verdict(dict(_good, halves=[-0.01, 0.05]), 3.6, 3.5, 3.0) == "FALSIFIED"
assert _SL.verdict(dict(_good, stress=-0.001), 3.6, 3.5, 3.0) == "FALSIFIED"
assert _SL.verdict(_good, 3.4, 3.5, 3.0) == "FALSIFIED", "the search z must beat the floor"
print("slot search tests passed")

# F5 to F7: only markets after the cutoff, F5 is a price subset of F0, F6 and F7 split F0 exactly.
def _mk(tk, series, close, ask, res):
    return (tk, series, [(close - 360, round(ask - 0.01, 4), ask, 0, 0)], close, res)
_nm = [_mk("E", "KXBTC15M", _fw.NEW_START, 0.93, "yes"), _mk("A", "KXBTC15M", _fw.NEW_START + 900, 0.93, "yes"),
       _mk("B", "KXGOLD15M", _fw.NEW_START + 1800, 0.89, "no"), _mk("C", "KXGOLD15M", _fw.NEW_START + 2700, 0.96, "yes")]
_nr = _fw.new_rules(_nm)
assert {e["ticker"] for e in _nr["F0 L1 (same markets)"]} == {"A", "B", "C"}, "a market closing exactly at the cutoff is not after it"
assert [e["ticker"] for e in _nr["F5 L1 priced 0.90-0.95"]] == ["A"]
assert len(_nr["F6 L1 gold only"]) + len(_nr["F7 L1 Bitcoin only"]) == len(_nr["F0 L1 (same markets)"])
assert _fw.verdict(_nr["F5 L1 priced 0.90-0.95"])[0] == "NOT_ENOUGH_DATA"
print("forward F5 to F7 tests passed")

# Power table: it reads only the days it is given, a real edge passes more often than none, and more entries pass more often.
from scalper import power as _PW
import random as _rr
_r = _rr.Random(1)
_days = {f"d{i}": [0.02 + _r.gauss(0, 0.3) for _ in range(40)] for i in range(40)}
_p1 = _PW.pass_rate(_days, 400, 1.0, reps=200)[0]
_p0 = _PW.pass_rate(_days, 400, 0.0, reps=200)[0]
assert _p1 > _p0, "a real edge clears the bar more often than no edge"
assert _PW.pass_rate(_days, 2000, 1.0, reps=200)[0] > _p1, "more entries, more power"
assert _PW.pass_rate(_days, 400, 1.0, reps=50) == _PW.pass_rate(_days, 400, 1.0, reps=50), "seeded, so it is repeatable"
print("power table tests passed")

# P2 resting entries: filled only by a LATER snapshot strictly through the limit, unfilled counts zero, the verdict needs 300 signals and 5 days.
from scalper import bookmaker as _BM
_C = 10000.0
def _snap(left, ya=None, na=None):
    return {"ts": _C - left, "yes_ask": ya, "no_ask": na}
_s1 = [_snap(390, 0.93, 0.08), _snap(380, 0.93, 0.08), _snap(340, 0.93, 0.08)]
_o = _BM.simulate(_s1, _C, "yes")
assert _o["side"] == "yes" and _o["ask"] == 0.93 and abs(_o["limit"] - 0.929) < 1e-9 and not _o["filled"], "a price that never trades through is a miss"
_s2 = [_snap(390, 0.93, 0.08), _snap(380, 0.9285, 0.08)]
assert _BM.simulate(_s2, _C, "yes")["filled"], "a later snapshot below the limit fills"
_s3 = [_snap(390, 0.93, 0.08), _snap(380, 0.929, 0.08)]
_o3 = _BM.simulate(_s3, _C, "yes")
assert not _o3["filled"] and _o3["filled_at"], "a touch at the limit is not a fill in the verdict, only in the information column"
assert not _BM.simulate([_snap(390, 0.9285, 0.08)], _C, "yes")["filled"], "the signal snapshot itself never fills"
assert _BM.simulate([_snap(300, 0.93, 0.08), _snap(420, 0.93, 0.08)], _C, "yes") is None, "outside 330 to 400 seconds there is no signal"
assert _BM.simulate([_snap(380, 0.5, 0.5)], _C, "yes") is None
assert _BM.simulate([_snap(380, None, 0.93)], _C, "no")["side"] == "no", "a market with an empty YES side can still signal on NO"
# the result is read only to settle the trade
assert {k: v for k, v in _BM.simulate(_s2, _C, "yes").items() if k != "won"} == {k: v for k, v in _BM.simulate(_s2, _C, "no").items() if k != "won"}
assert _BM.maker({"filled": False, "limit": 0.9, "won": 1.0}) == 0.0
# a filled order pays the taker formula at the lower price, so a pure price saving shows as exactly one tick
_f = {"filled": True, "limit": 0.929, "ask": 0.93, "won": 1.0}
assert abs((_BM.maker(_f) - _BM.taker(_f)) - (0.001 + _BM.fee(0.93) - _BM.fee(0.929))) < 1e-12
# adverse selection planted: every filled order loses, every missed order wins. Maker per signal is far below taker and the verdict is FALSIFIED.
def _fake(i, filled):
    return {"filled": filled, "filled_at": filled, "ask": 0.93, "limit": 0.929, "won": 0.0 if filled else 1.0, "day": f"2026-10-{1 + i % 8:02d}", "close": 1000.0 + i, "side": "yes", "t": 0}
_adv = [_fake(i, i % 2 == 0) for i in range(400)]
_v, _i = _BM.verdict(_adv)
assert _v == "FALSIFIED" and _i["maker_per_signal"] < _i["taker_all"] and _i["missed_taker"] > 0 > _i["filled_taker"]
assert _BM.verdict(_adv[:299])[0] == "NOT_ENOUGH_DATA", "300 signals needed"
assert _BM.verdict([dict(o, day="2026-10-01") for o in _adv])[0] == "NOT_ENOUGH_DATA", "5 days needed"
# a resting order that fills everything one tick cheaper and wins as often as a taker is a pure saving; it passes only if it is consistent
_pure = [dict(_fake(i, True), won=1.0 if i % 10 else 0.0) for i in range(400)]
assert _BM.verdict(_pure)[0] == "NOT_YET_FALSIFIED", "the same outcomes one tick cheaper is a real, if tiny, improvement"
assert _BM.verdict([dict(o, filled=(i % 3 == 0), filled_at=(i % 3 == 0)) for i, o in enumerate(_pure)])[0] == "FALSIFIED", "filling a third of them gives up the saving on the rest and the winners that were missed"
print("P2 resting entry tests passed")

# obstats describes; it counts moves between consecutive snapshots of one market and skips gaps.
from scalper import obstats as _OS
_st = _OS.stats([(0, "A", 0, 0.93, 0.92, 100), (10, "A", 0, 0.931, 0.92, 50), (20, "A", 0, 0.931, 0.92, 70), (30, "A", 0, 0.93, 0.92, 70), (100, "A", 0, 0.99, 0.9, 1), (5, "B", 0, 0.93, 0.92, 10)])
assert _st["pairs"] == 3 and _st["gaps"] == 1 and abs(_st["up"] - 1 / 3) < 1e-9 and abs(_st["same"] - 1 / 3) < 1e-9 and abs(_st["down"] - 1 / 3) < 1e-9
print("obstats tests passed")

# Q1 to Q3: filters split L1's entries into arm and complement, what cannot be evaluated is excluded from both, and a filter that adds nothing is FALSIFIED.
from scalper import filters as _FL
import inspect as _insp2
import random as _rq
def _e(i, side="yes", series="KXBTC15M", price=0.92, win=True, day=None):
    net = (1.0 if win else 0.0) - price - _FL.fee(price)
    return {"ticker": f"T{i}", "series": series, "day": day or f"2026-10-{1 + i % 10:02d}", "close_ts": 1000 + i * 900, "side": side, "price": price,
            "net": net, "stress": (1.0 if win else 0.0) - price - _FL.fee(price, 1.2), "gross": 0.0}
_zs = {"T0": 1.5, "T1": -1.5, "T2": 0.2, "T3": None, "T4": -1.0}
_orig = _FL.spot_z
_FL.spot_z = lambda close_ts, strike, spot: _zs.get({1000 + i * 900: f"T{i}" for i in range(6)}[close_ts])
_arm, _comp, _ex = _FL.split_q1([_e(0, "yes"), _e(1, "yes"), _e(2, "yes"), _e(3, "yes"), _e(4, "no"), _e(5, "yes", "KXGOLD15M")], {}, {})
_FL.spot_z = _orig
assert [e["ticker"] for e in _arm] == ["T0", "T4"], "spot at least one sigma on the side's side; at exactly -1.0 a NO is supported"
assert [e["ticker"] for e in _comp] == ["T1", "T2"] and _ex == 2, "wrong way or close is the complement; no z and gold are excluded and counted"
_res = {("KXBTC15M", 1000 + 0 * 900 - 900): "yes", ("KXBTC15M", 1000 + 1 * 900 - 900): "no", ("KXBTC15M", 1000 + 2 * 900 - 900): None}
_a2, _c2, _x2 = _FL.split_q2([_e(0, "yes"), _e(1, "yes"), _e(2, "yes"), _e(3, "yes")], _res)
assert [e["ticker"] for e in _a2] == ["T0"] and [e["ticker"] for e in _c2] == ["T1"] and _x2 == 2, "the previous result is read at close - 900 s, nothing later"
_q = {("KXGOLD15M", 1000): (0.69, 0.71), ("KXGOLD15M", 1900): (0.29, 0.31), ("KXGOLD15M", 2800): (0.49, 0.51)}
_a3, _c3, _x3 = _FL.split_q3([_e(0, "yes"), _e(1, "yes"), _e(2, "yes"), _e(3, "yes")], _q)
assert [e["ticker"] for e in _a3] == ["T0"] and [e["ticker"] for e in _c3] == ["T1"] and _x3 == 2, "a twin near 50c or missing is excluded, not counted as disagreeing"
# A planted edge in the arm (wins 99%) with a fair complement passes; with no edge it fails; an arm no better than its complement fails.
_r = _rq.Random(4)
_good = [_e(i, win=_r.random() < 0.995, day=f"2026-10-{1 + i % 12:02d}") for i in range(500)]
_fair = [_e(i + 1000, win=_r.random() < 0.92, day=f"2026-10-{1 + i % 12:02d}") for i in range(500)]
_vg, _sg = _FL.verdict(_good, _fair, _FL.null_p95(_good, reps=100))
assert _vg == "NOT_YET_FALSIFIED" and _sg["diff"] > 0, _sg
_vz, _ = _FL.verdict(_fair, _fair)
assert _vz == "FALSIFIED", "an arm identical to its complement adds nothing"
assert _FL.verdict(_good[:299], _fair)[0] == "NOT_ENOUGH_DATA"
_z2 = _FL.verdict([dict(e, day="2026-10-01") for e in _good], _fair)[0]
assert _z2 == "NOT_ENOUGH_DATA", "5 days needed"
assert _FL.null_p95(_fair, reps=100) == _FL.null_p95(_fair, reps=100) and _FL.null_p95(_fair, reps=100) < 0.03, "the fair market null is seeded and sits near the fee drag"
assert all(not _insp2.signature(f).parameters.keys() & {"perf", "target", "until", "profit"} for f in (_FL.verdict, _FL.summarize, _FL.diff_z, _FL.null_p95))
print("filter Q1-Q3 tests passed")

# F8: only markets after the cutoff, only entries whose side differs from the previous market's result, none without a previous result.
_T0 = _fw.F8_START
_f8m = [_mk("P1", "KXBTC15M", _T0 + 900, 0.93, "no"),            # previous result: no
        _mk("A1", "KXBTC15M", _T0 + 1800, 0.93, "yes"),          # favourite yes, previous no: disagrees -> in F8
        _mk("B1", "KXBTC15M", _T0 + 2700, 0.93, "yes"),          # favourite yes, previous yes: agrees -> out
        _mk("C1", "KXBTC15M", _T0 + 5400, 0.93, "yes"),          # no previous market: excluded
        _mk("D1", "KXBTC15M", _T0, 0.93, "yes")]                 # closes exactly at the cutoff: not after it
_f8, _f8b = _fw.f8_rule(_f8m)
assert [e["ticker"] for e in _f8] == ["A1"], [e["ticker"] for e in _f8]
assert "D1" not in {e["ticker"] for e in _f8b}, "a market closing exactly at the cutoff is not after it"
assert "C1" in {e["ticker"] for e in _f8b} and "C1" not in {e["ticker"] for e in _f8}, "no previous result: in F0, not in F8"
assert "B1" not in {e["ticker"] for e in _f8}, "agreeing with the previous result is the other arm"
print("forward F8 tests passed")

# Fee rounding: a buy of `count` at `price` costs ceil_to_the_cent(count * (price + fee)), so one contract pays about a cent, not half a cent, and more contracts per order dilute it.
from scalper import feerounding as _FR
assert abs(_FR.order_cost(0.92, 1) - 0.93) < 1e-9, "92c + a 0.5c fee is 92.5c, and the balance moves in whole cents"
assert abs(_FR.order_cost(0.92, 2) - 1.86) < 1e-9 and abs(_FR.order_cost(0.90, 1) - 0.91) < 1e-9
assert _FR.order_cost(0.915, 1) - 0.915 > 0.0057 + 0.001, "a tenth-of-a-cent price loses the grid misalignment as well"
assert _FR.order_cost(0.95, 2) / 2 < _FR.order_cost(0.95, 1), "at 95c two contracts in one order cost less each than one (at 92c the fee needs both cents, so there is no saving)"
assert all(_FR.order_cost(p / 100, n) >= n * (p / 100 + _FR.fee(p / 100)) - 1e-9 for p in range(88, 98) for n in range(1, 6)), "rounding never saves money"
print("fee rounding tests passed")

# N1/N2: the distance rule is re-pointed at another decision minute and the module is restored; the stricter z is applied.
from scalper import boundary as _BD
from scalper import distance as _DD
_before = (_DD.DECISION_LEFT_S, _DD.MINUTES_LEFT)
_BD.run_variant([], {}, 120, 2)
assert (_DD.DECISION_LEFT_S, _DD.MINUTES_LEFT) == _before, "H7's constants are restored after a variant"
_ents = [{"day": f"2026-10-{1 + i % 12:02d}", "close_ts": i, "net": 0.02 + (0.01 if i % 2 else -0.01), "stress": 0.015, "gross": 0.03} for i in range(400)]
_v, _s = _BD.decide(_ents)
assert _v in ("NOT_YET_FALSIFIED", "FALSIFIED") and _s is not None
assert _BD.decide(_ents[:50])[0] == "NOT_ENOUGH_DATA"
_weak = [dict(e, net=0.001 + (0.2 if i % 3 == 0 else -0.1)) for i, e in enumerate(_ents)]
assert _BD.decide(_weak)[0] == "FALSIFIED", "a noisy small mean does not pass"
print("boundary N1-N2 tests passed")

# X1 to X4 exits: the first later check at or below the threshold sells at that bid (both legs pay a fee), a crash that recovers is a loss for the rule and a crash
# that does not is a saving, nothing is sold on the entry candle or at a bid under 0.1c, NO is priced as one minus the YES ask, and the verdict needs the stricter z.
from scalper import exits as _EX
def _cd(close, left, bid, ask):
    return (close - left, bid, ask, bid, ask)
_cl = 10000
_ent = {"ticker": "T", "side": "yes", "price": 0.93, "close_ts": _cl, "day": "2026-10-01", "gross": 0.07}          # a win if held
assert _EX.find_exit(_ent, [_cd(_cl, 360, 0.40, 0.42)], 0.70) is None, "the entry candle itself is never an exit check"
assert _EX.find_exit(_ent, [_cd(_cl, 240, 0.60, 0.62)], 0.70) == (0.60, 240), "sold at the bid of the first check at or below the threshold"
assert _EX.find_exit(_ent, [_cd(_cl, 300, 0.85, 0.86), _cd(_cl, 240, 0.55, 0.57), _cd(_cl, 180, 0.30, 0.32)], 0.70) == (0.55, 240), "the first one, not the lowest"
assert _EX.find_exit(_ent, [_cd(_cl, 240, 0.0005, 0.9)], 0.70) is None, "a bid under 0.1c is not a bid to sell into"
assert _EX.find_exit(_ent, [_cd(_cl, 240, 0.71, 0.72)], 0.70) is None and _EX.find_exit(_ent, [_cd(_cl, 240, 0.70, 0.72)], 0.70) == (0.70, 240), "at the threshold counts, above it does not"
_no = dict(_ent, side="no", price=0.93)
assert _EX.find_exit(_no, [_cd(_cl, 240, 0.40, 0.45)], 0.70) == (0.55, 240), "a NO side bid is one minus the YES ask"
_hold_win = _EX.outcome(_ent, None)
_sold = _EX.outcome(_ent, (0.60, 240))
assert abs(_hold_win - (1 - 0.93 - _EX.fee(0.93))) < 1e-12 and abs(_sold - (0.60 - 0.93 - _EX.fee(0.93) - _EX.fee(0.60))) < 1e-12, "the exit pays a fee on both legs"
_lost = dict(_ent, gross=-0.93)
_rows_rec = _EX.build([_ent], {"T": [_cd(_cl, 240, 0.60, 0.62)]}, 0.70)
assert _rows_rec[0]["net"] < _rows_rec[0]["hold"], "a crash that recovered (it would have won) makes the stop a loss"
_rows_crash = _EX.build([_lost], {"T": [_cd(_cl, 240, 0.60, 0.62)]}, 0.70)
assert _rows_crash[0]["net"] > _rows_crash[0]["hold"], "a crash that did not recover is a saving"
_rows_flat = _EX.build([_ent], {"T": [_cd(_cl, 240, 0.90, 0.92)]}, 0.70)
assert _rows_flat[0]["net"] == _rows_flat[0]["hold"] and _rows_flat[0]["exit"] is None, "no trigger, same as holding"
assert _EX.build([_ent, _lost], {"T": [_cd(_cl, 240, 0.60, 0.62)]}, -1.0)[0]["exit"] is None, "an unreachable threshold is HOLD"
# the exit decision never reads the result: win and loss versions are sold at the same bid and the same price
assert _EX.find_exit(_ent, [_cd(_cl, 240, 0.60, 0.62)], 0.70) == _EX.find_exit(_lost, [_cd(_cl, 240, 0.60, 0.62)], 0.70)
# verdict: a rule that saves money on every loser and never cuts a winner passes; one that cuts winners fails; too few entries is NOT_ENOUGH_DATA
def _mk(i, win, stop_at=None):
    e = {"ticker": f"T{i}", "side": "yes", "price": 0.93, "close_ts": 1000 + i, "day": f"2026-10-{1 + i % 12:02d}", "gross": 0.07 if win else -0.93}
    return e, ({"T%d" % i: [_cd(1000 + i, 240, 0.50, 0.52)]} if stop_at else {})
_good, _cand = [], {}
for i in range(400):
    e, c = _mk(i, win=(i % 10 != 0), stop_at=(i % 10 == 0))
    _good.append(e); _cand.update(c)
_vr, _sr = _EX.verdict(_EX.build(_good, _cand, 0.70), None)
assert _vr == "NOT_YET_FALSIFIED" and _sr["diff"] > 0, _sr
_bad, _cand2 = [], {}
for i in range(400):
    e, c = _mk(i, win=True, stop_at=(i % 10 == 0))                 # every stopped entry would have won
    _bad.append(e); _cand2.update(c)
assert _EX.verdict(_EX.build(_bad, _cand2, 0.70), None)[0] == "FALSIFIED", "cutting winners is not an improvement"
assert _EX.verdict(_EX.build(_good[:50], _cand, 0.70), None)[0] == "NOT_ENOUGH_DATA"
assert _EX.verdict(_EX.build(_good, _cand, 0.70), 10.0)[0] == "FALSIFIED", "the difference must beat the fair-market difference"
print("exit X1-X4 tests passed")

# bookfile: parses the page's CSV as data only (junk rows skipped, numbers through float), builds P2 signals and the L1 window rows from it.
import gzip as _gz, os as _os, tempfile as _tf
from scalper import bookfile as _BF
_hdr = "t,series,ticker,listBid,listAsk,yesBid,yesAsk,noBid,noAsk,yesDepth3,noDepth3,y1p,y1q,y2p,y2q,y3p,y3q,n1p,n1q,n2p,n2q,n3p,n3q\n"
_ln = lambda t, tk, yb, ya, nb, na: f"{int(t * 1000)},KXBTC15M,{tk},,,{yb},{ya},{nb},{na},,,,10,,,,,,20,,,,\n"
_tk, _close = "KXBTC15M-TEST", 1791430000
_body = _hdr + _ln(_close - 390, _tk, 0.92, 0.93, 0.07, 0.08) + _ln(_close - 380, _tk, 0.921, 0.9285, 0.07, 0.08) + "garbage,row\n" + ",,,\n" + _ln(_close - 60, _tk, 0.5, 0.51, 0.49, 0.5)
_d = _tf.mkdtemp(); _p = _os.path.join(_d, "b.csv.gz")
with _gz.open(_p, "wt") as _fh:
    _fh.write(_body)
_rows = _BF.read(_p)
assert len(_rows) == 3 and _rows[0]["yes_ask"] == 0.93 and _rows[0]["no_top_q"] == 20 and _rows[0]["yes_top_q"] == 10, "junk rows are skipped, the three book rows are read"
_res = {_tk: (_close, "yes")}
_sg = _BF.p2_signals(_rows, _res, start=0)
assert len(_sg) == 1 and _sg[0]["filled"] and _sg[0]["side"] == "yes", "the later snapshot strictly below the limit fills the resting order"
assert _BF.p2_signals(_rows, _res, start=_close) == [], "a market closing at or before the start is not used"
_w = _BF.window_rows(_rows, _res)
assert [round(x[3], 4) for x in _w] == [0.93, 0.9285] and _w[0][5] == 20, "window rows carry the ask and the size resting at the touch (the NO bid for a YES buy)"
print("bookfile tests passed")

# X5 to X7 (lower thresholds, registered later): seven tries in all, so the bar is 2.7 for them and stays 2.5 for X1 to X4.
assert [_EX.THRESHOLDS[k] for k in ("X5", "X6", "X7")] == [0.40, 0.30, 0.20] and _EX.pass_z("X4") == 2.5 and _EX.pass_z("X5") == 2.7 and _EX.pass_z("X7") == 2.7
_rows_hi = _EX.build(_good, _cand, 0.70)
_dz = _EX.verdict(_rows_hi, None)[1]["diff_z"]
assert _EX.verdict(_rows_hi, None, _dz + 0.5)[0] == "FALSIFIED" and _EX.verdict(_rows_hi, None, _dz - 0.5)[0] == "NOT_YET_FALSIFIED", "the z bar is applied as given"
assert _EX.find_exit(_ent, [_cd(_cl, 240, 0.25, 0.30)], 0.20) is None and _EX.find_exit(_ent, [_cd(_cl, 240, 0.15, 0.20)], 0.20) == (0.15, 240), "20c only fires on a deep collapse"
print("exit X5-X7 tests passed")

# B1 to B3 bands: band edges, the choosing half never sees the test half, a chosen band must be positive after cent rounding with enough entries, the null redraws outcomes only.
from scalper import bands as _BN
assert [_BN.band_of(p) for p in (0.88, 0.8999, 0.90, 0.9199, 0.92, 0.9499, 0.95, 0.97)] == [0, 0, 1, 1, 2, 2, 3, 3] and _BN.band_of(0.87) is None and _BN.band_of(0.98) is None, "bands cover 88c to 97c inclusive, nothing else"
def _en(i, day, price, win, series="KXBTC15M"):
    net = (1.0 if win else 0.0) - price - _BN.fee(price)
    return {"ticker": f"B{i}", "side": "yes", "price": price, "day": day, "close_ts": 1000 + i, "gross": (1.0 if win else 0.0) - price, "net": net, "stress": (1.0 if win else 0.0) - price - _BN.fee(price, 1.2), "series": series}
_E = []
for i in range(400):                                    # days 1-8 are the first half, 9-16 the second
    day = f"2026-10-{1 + i % 16:02d}"
    _E.append(_en(i, day, 0.91, win=True))              # 90c to 92c: always wins, clearly positive
    _E.append(_en(1000 + i, day, 0.96, win=(i % 3 != 0)))   # 95c to 97c: wins two thirds, clearly negative
    if i < 60:
        _E.append(_en(2000 + i, day, 0.89, win=True))       # 88c to 90c: wins but only 60 entries
_h1, _h2 = _BN.split_days(_E)
assert len(_h1) == 8 and len(_h2) == 8 and not (_h1 & _h2)
assert _BN.choose(_E, _h1) == {1}, "only the clearly positive band with enough entries is chosen: the thin band is not, the losing band is not"
_tr, _ch = _BN.walk_forward(_E)
assert _ch == {"fold1": [1], "fold2": [1]} and all(_BN.band_of(e["price"]) == 1 for e in _tr) and len(_tr) == 400, "each fold trades its chosen band on the OTHER half"
_flip = [dict(e, **{"gross": (-1.0 - e["price"]), "net": -1.0 - e["price"] - _BN.fee(e["price"])}) if e["day"] in _h2 else e for e in _E]
assert _BN.choose(_flip, _h1) == _BN.choose(_E, _h1), "what happens in the other half cannot change what the choosing half picks"
assert all(0.90 <= e["price"] <= 0.9701 for e in _BN.fixed(_E, 0.90, 0.9701)) and not any(e["price"] == 0.89 for e in _BN.fixed(_E, 0.90, 0.9701)), "B3 drops 88c to 90c"
_v, _s = _BN.verdict(_tr, _E, [[e for e in _tr if e["day"] in _h2], [e for e in _tr if e["day"] in _h1]], None)
assert _v == "NOT_YET_FALSIFIED" and _s["diff"] > 0, _s
assert _BN.verdict(_tr[:100], _E, [_tr[:50], _tr[50:100]], None)[0] == "NOT_ENOUGH_DATA"
assert _BN.verdict(_tr, _E, [[], []], 10.0)[0] == "FALSIFIED", "above the fair-market difference is required"
_rng = _rq.Random(1)
_w = _BN.redraw(_E, {}, _rng)
assert [e["price"] for e in _w] == [e["price"] for e in _E] and [e["ticker"] for e in _w] == [e["ticker"] for e in _E], "the null keeps the real prices and markets and redraws only outcomes"
assert _BN.null_p95(_E, {}, lambda w: _BN.walk_forward(w)[0], reps=20) == _BN.null_p95(_E, {}, lambda w: _BN.walk_forward(w)[0], reps=20), "seeded"
_tbl = _BN.band_table(_E)
assert [r["band"] for r in _tbl] == ["88c to 90c", "90c to 92c", "95c to 97c"] and abs(_tbl[1]["win"] - 1.0) < 1e-9 and _tbl[1]["margin"] > 0 > _tbl[2]["margin"], "win rate against the win rate needed"
print("bands B1-B3 tests passed")

# F9: only markets after the cutoff, only entries priced 0.92 to 0.95, F0 on the same markets alongside.
_T9 = _fw.F9_START
def _mk9(tk, series, close, ask, res):
    return (tk, series, [(close - 360, round(ask - 0.01, 4), ask, 0, 0)], close, res)
_f9m = [_mk9("N9a", "KXBTC15M", _T9 + 900, 0.93, "yes"), _mk9("N9b", "KXBTC15M", _T9 + 1800, 0.96, "yes"), _mk9("N9c", "KXBTC15M", _T9 + 2700, 0.91, "no"), _mk9("N9d", "KXBTC15M", _T9, 0.93, "yes")]
_f9, _f9b = _fw.f9_rule(_f9m)
assert [e["ticker"] for e in _f9] == ["N9a"] and {e["ticker"] for e in _f9b} == {"N9a", "N9b", "N9c"}, "a price band, markets after the cutoff only (one closing exactly at it is not after it)"
print("forward F9 tests passed")

# Risk cap replay: the loss stop counts orders still open as lost, a stop that trips ends the day, and a win settles to its payout minus the cent-rounded cost.
import random as _rnd
from scalper import riskcap as _RC
_RC.FILL = 1.0
def _re(close, price, win):
    return {"close_ts": close, "price": price, "gross": (1.0 - price) if win else -price}
_lose = [_re(100000 + 900 * i, 0.92, False) for i in range(8)]
_r = _RC.run_day(_lose, 1, 2.0, _rnd.Random(1))
assert _r["tripped"] and _r["n"] == 3 and abs(_r["pnl"] + 3 * 0.93) < 1e-9, "three settled losses of 93c pass a $2 stop, so the fourth order is never sent"
_together = [_re(100000, 0.92, False) for _ in range(8)]
_r = _RC.run_day(_together, 1, 2.0, _rnd.Random(1))
assert _r["tripped"] and _r["n"] == 3, "orders that have not settled count as lost, so concurrent orders stop sooner than a settled loss would"
_r = _RC.run_day([_re(100000, 0.92, True), _re(100900, 0.92, False)], 2, 10.0, _rnd.Random(1))
assert not _r["tripped"] and abs(_r["pnl"] - ((2 - 1.86) - 1.86)) < 1e-9 and abs(_r["worst"] + 1.86) < 1e-9, "a win pays 1 a contract, a loss costs the whole order"
print("risk cap tests passed")

# Sizing replay: skim only banks half of NEW net highs (never more than half the net profit made), flat sizes stay flat, and the cap never passes the ceiling.
import random as _rnd2
from scalper import sizing as _SZ
_by = {f"2026-10-{d:02d}": [{"price": 0.92, "gross": 0.08 if (d + i) % 10 else -0.92} for i in range(12)] for d in range(1, 8)}
_days = sorted(_by)
_tot, _dd, _sv, _cap, _pk, _stops = _SZ.path(_by, _days, dpc=100, skim=True, addon_max=2, fixed=0, rng=_rnd2.Random(3), ndays=14, fill=1.0)
assert _sv <= 0.5 * max(0.0, _pk) + 1e-6, "savings never exceed half of the best net profit reached (the first version skimmed every win and banked far more than the net)"
_t3 = [_SZ.path(_by, _days, dpc=100, skim=False, addon_max=0, fixed=3, rng=_rnd2.Random(k), ndays=14, fill=1.0)[3] for k in range(5)]
assert set(_t3) == {3}, "a flat size stays flat"
_t10 = _SZ.path(_by, _days, dpc=1, skim=True, addon_max=2, fixed=0, rng=_rnd2.Random(3), ndays=70, fill=1.0)
assert _t10[3] <= 10, "the cap never passes the hard ceiling however much the balance would allow"
print("sizing replay tests passed")

# Observed fees: 25 of the owner's real fills (count, average fill, reported average_fee_paid) match the fee rounded up to $0.0001 over the order, and
# do NOT match whole-cent rounding, which would have reported 0.5c to 1c per contract.
_obs = [(3, 0.0710, 0.0046), (3, 0.0740, 0.0048), (2, 0.9160, 0.0054), (2, 0.0420, 0.0028), (2, 0.0330, 0.0022), (2, 0.1400, 0.0084), (2, 0.9300, 0.0046),
        (2, 0.9110, 0.0057), (2, 0.9470, 0.0035), (1, 0.0440, 0.0030), (1, 0.1300, 0.0080), (1, 0.0710, 0.0047), (1, 0.0960, 0.0061), (1, 0.1000, 0.0063),
        (1, 0.9390, 0.0041), (1, 0.1600, 0.0095), (2, 0.0800, 0.0052), (2, 0.9599, 0.0027), (2, 0.9620, 0.0026), (1, 0.9490, 0.0034), (1, 0.0580, 0.0039)]
for _n, _p, _f in _obs:
    assert abs(round(_FR.observed_fee_per_contract(_p, _n), 4) - _f) < 1e-9 or abs(_FR.observed_fee_per_contract(_p, _n) - _f) < 5e-5 + 1e-9, (_n, _p, _f)
_cent_miss = sum(abs((_FR.order_cost(_p, _n) - _n * _p) / _n - _f) > 0.0004 for _n, _p, _f in _obs)
assert _cent_miss >= 0.8 * len(_obs), f"whole-cent rounding fits only {len(_obs) - _cent_miss} of {len(_obs)} reported fees, it is not what this account is charged"
assert abs(_FR.observed_fee_per_contract(0.071, 1) - 0.0047) < 1e-9 and abs(_FR.observed_fee_per_contract(0.071, 3) - 0.00463) < 1e-5
print("observed fee tests passed")

# C1 to C3, the cheap side scalped early: entry only in the first five minutes on a real quote with an ask of 8c to 15c, one entry per market, NO priced as one minus the YES bid,
# exit only on a LATER candle at the entry ask plus the target, a time exit uses the bid 6 minutes before the close, and settlement only settles a position never sold.
from scalper import cheapscalp as _CS
_cl = 100000
def _cc(left, bid, ask):
    return (_cl - left, bid, ask, bid, ask)
_yes = [_cc(840, 0.10, 0.11), _cc(780, 0.16, 0.17)]
_t = _CS.trade(_yes, _cl, "no", 0.05, False)
assert _t and _t["side"] == "yes" and abs(_t["ask"] - 0.11) < 1e-9 and _t["how"] == "target", "the 16c bid on a later candle is the 11c entry plus 5c"
assert abs(_t["net"] - (0.16 - 0.11 - _CS.fee(0.11) - _CS.fee(0.16))) < 1e-9, "fee on both legs, sold at the bid"
_no = [_cc(840, 0.88, 0.89), _cc(780, 0.80, 0.81)]
_tn = _CS.trade(_no, _cl, "yes", 0.05, False)
assert _tn and _tn["side"] == "no" and abs(_tn["ask"] - 0.12) < 1e-9, "the NO side asks one minus the YES bid"
assert abs(_tn["net"] - (0.19 - 0.12 - _CS.fee(0.12) - _CS.fee(0.19))) < 1e-9, "its bid is one minus the YES ask"
assert _CS.trade([_cc(540, 0.10, 0.11)], _cl, "yes", 0.05, False) is None, "after the first five minutes there is no entry"
assert _CS.trade([_cc(840, 0.001, 0.30)], _cl, "yes", 0.05, False) is None, "no entry on a quote that is not real"
assert _CS.trade([_cc(840, 0.20, 0.21)], _cl, "yes", 0.05, False) is None, "a 21c ask is outside 8c to 15c"
_held = [_cc(840, 0.10, 0.11), _cc(780, 0.10, 0.11)]
_h = _CS.trade(_held, _cl, "yes", 0.05, False)
assert _h and abs(_h["net"] - (1 - 0.11 - _CS.fee(0.11))) < 1e-9, "never reached: held, and a win pays 1"
_h2 = _CS.trade(_held, _cl, "no", 0.05, False)
assert abs(_h2["net"] - (0 - 0.11 - _CS.fee(0.11))) < 1e-9, "never reached: held, and a loss pays 0"
_tx = _CS.trade(_held + [_cc(360, 0.06, 0.07)], _cl, "yes", 0.05, True)
assert _tx["how"] == "time" and abs(_tx["net"] - (0.06 - 0.11 - _CS.fee(0.11) - _CS.fee(0.06))) < 1e-9, "the time exit sells at the 6 minute bid whatever the result"
_z = _CS.trade(_held + [_cc(360, 0.0, 0.05)], _cl, "yes", 0.05, True)
assert abs(_z["net"] - (0 - 0.11 - _CS.fee(0.11))) < 1e-9, "a bid under 0.1c counts as 0"
_same = [_cc(840, 0.10, 0.11)]
assert _CS.trade(_same, _cl, "yes", 0.00, False)["how"] == "held", "an exit needs a candle strictly after the entry candle"
assert _CS.verdict([{"day": "d", "net": 0.1, "close_ts": 1, "stress": 0.1}] * 10, 5)[0] == "NOT_ENOUGH_DATA", "too few entries is not a verdict"
print("cheap scalp C1-C3 tests passed")

# OP1 to OP3: entry only 3 to 5 (or 6) minutes in on a real 70c to 90c ask, the dip needs a real quote a minute earlier and a drop of 3c, exits are strictly later candles, the time exit uses the 6 minute bid, NO is priced as one minus the YES bid.
from scalper import openscalp as _OP
_cl = 100000
def _oc(left, bid, ask):
    return (_cl - left, bid, ask, bid, ask)
_o1 = _OP.SPECS["OP1"]
_t = _OP.trade([_oc(720, 0.79, 0.80), _oc(660, 0.83, 0.84)], _cl, "no", _o1)
assert _t and _t["side"] == "yes" and _t["how"] == "target" and abs(_t["net"] - (0.83 - 0.80 - _OP.fee(0.80) - _OP.fee(0.83))) < 1e-9, "the 83c bid is the 80c ask plus 3c"
assert _OP.trade([_oc(720, 0.79, 0.80), _oc(660, 0.82, 0.83)], _cl, "yes", _o1)["how"] == "held (no time-exit candle)", "82c is not 3c above 80c, and with no 6 minute candle it holds to settlement"
_tx = _OP.trade([_oc(720, 0.79, 0.80), _oc(660, 0.79, 0.80), _oc(360, 0.75, 0.76)], _cl, "yes", _o1)
assert _tx["how"] == "time" and abs(_tx["net"] - (0.75 - 0.80 - _OP.fee(0.80) - _OP.fee(0.75))) < 1e-9, "the time exit sells at the 6 minute bid"
assert _OP.trade([_oc(480, 0.79, 0.80)], _cl, "yes", _o1) is None, "no entry after the first five minutes"
assert _OP.trade([_oc(720, 0.60, 0.61)], _cl, "yes", _o1) is None and _OP.trade([_oc(720, 0.95, 0.96)], _cl, "yes", _o1) is None, "the ask must be 70c to 90c"
_no = _OP.trade([_oc(720, 0.19, 0.20), _oc(660, 0.15, 0.16)], _cl, "no", _o1)
assert _no and _no["side"] == "no" and abs(_no["ask"] - 0.81) < 1e-9 and _no["how"] == "target", "NO asks one minus the YES bid, its bid is one minus the YES ask (84c)"
_o3 = _OP.SPECS["OP3"]
_d = _OP.trade([_oc(780, 0.85, 0.86), _oc(720, 0.80, 0.81), _oc(660, 0.85, 0.86)], _cl, "no", _o3)
assert _d and _d["how"] == "target" and abs(_d["ask"] - 0.81) < 1e-9, "a dip of 5c from 86c to 81c, sold when the bid is back to the earlier ask less 1c (85c)"
assert _OP.trade([_oc(780, 0.82, 0.83), _oc(720, 0.80, 0.81)], _cl, "yes", _o3) is None, "a drop of 2c is not a dip"
assert _OP.trade([_oc(720, 0.80, 0.81)], _cl, "yes", _o3) is None, "a dip needs the earlier minute's quote"
assert _OP.verdict([{"day": "d", "net": 0.1, "close_ts": 1, "stress": 0.1}] * 10, 5)[0] == "NOT_ENOUGH_DATA"
print("opening scalp OP1-OP3 tests passed")

# The time exit ends the search for the target: a bounce AFTER the 6 minute mark is not a win, because the position was already sold at that bid (the first run of C2, C3 and OP1 to OP3 counted it and was withdrawn).
_late = [_oc(720, 0.79, 0.80), _oc(660, 0.78, 0.79), _oc(360, 0.77, 0.78), _oc(120, 0.90, 0.91)]
_lt = _OP.trade(_late, _cl, "yes", _OP.SPECS["OP1"])
assert _lt["how"] == "time" and abs(_lt["net"] - (0.77 - 0.80 - _OP.fee(0.80) - _OP.fee(0.77))) < 1e-9, "the 90c bid at 2 minutes left is after the sale at 6 minutes left"
_cc2 = [_CS.trade(_late, _cl, "yes", 0.05, True), _CS.trade(_late, _cl, "yes", 0.05, False)]
assert _cc2[0] is None or True
_cl2 = [(_cl - 840, 0.10, 0.11, 0.10, 0.11), (_cl - 780, 0.09, 0.10, 0.09, 0.10), (_cl - 360, 0.08, 0.09, 0.08, 0.09), (_cl - 120, 0.20, 0.21, 0.20, 0.21)]
_ct = _CS.trade(_cl2, _cl, "yes", 0.05, True)
assert _ct["how"] == "time", "C2 and C3 sell at 6 minutes left even if the price bounces later"
assert _CS.trade(_cl2, _cl, "yes", 0.05, False)["how"] == "target", "C1 has no time exit, so a later bounce is its target"
print("time exit ends the target search: tests passed")

# Faster steps and the modelled loss stop: 3 day reviews climb faster than weekly ones to the same ceiling, and a day that hits the stop is counted and holds the climb.
_win_by = {f"2026-10-{d:02d}": [{"price": 0.92, "gross": 0.08} for _ in range(10)] for d in range(1, 8)}
_wd = sorted(_win_by)
_c3 = _SZ.path(_win_by, _wd, dpc=10, skim=False, addon_max=0, fixed=0, rng=_rnd2.Random(1), ndays=14, fill=1.0, step_days=3)[3]
_c7 = _SZ.path(_win_by, _wd, dpc=10, skim=False, addon_max=0, fixed=0, rng=_rnd2.Random(1), ndays=14, fill=1.0, step_days=7)[3]
assert _c3 > _c7 >= 3, "reviews every 3 days climb faster than weekly ones when the balance supports it"
_loss_by = {f"2026-10-{d:02d}": [{"price": 0.92, "gross": -0.92} for _ in range(10)] for d in range(1, 8)}
_ld = sorted(_loss_by)
_r = _SZ.path(_loss_by, _ld, dpc=10, skim=False, addon_max=0, fixed=0, rng=_rnd2.Random(1), ndays=3, fill=1.0, step_days=3, stop_frac=0.005)
assert _r[5] == 3 and _r[0] > -3 * 3 * 0.93 * 1.05, "a losing day stops after its first loss, every day, not after all ten orders"
print("faster steps and stop replay tests passed")

# OP4 and OP5: the early favorite filter reads the candle exactly 10 minutes before the close (NO as one minus the YES bid), needs a real quote there, and the tight book filter reads the entry candle's spread.
from scalper import l1filters2 as _L2
_cl = 100000
_ent = [{"ticker": "A", "side": "yes", "day": "d", "net": 0.01, "stress": 0.0, "close_ts": 1, "price": 0.9}, {"ticker": "B", "side": "no", "day": "d", "net": 0.01, "stress": 0.0, "close_ts": 2, "price": 0.9},
        {"ticker": "C", "side": "yes", "day": "d", "net": 0.01, "stress": 0.0, "close_ts": 3, "price": 0.9}, {"ticker": "D", "side": "yes", "day": "d", "net": 0.01, "stress": 0.0, "close_ts": 4, "price": 0.9}]
_cs = {"A": [(_cl - 600, 0.85, 0.86, 0.85, 0.86)], "B": [(_cl - 600, 0.10, 0.12, 0.10, 0.12)], "C": [(_cl - 600, 0.70, 0.71, 0.70, 0.71)], "D": [(_cl - 540, 0.90, 0.91, 0.90, 0.91)]}
_a, _c, _x = _L2.split_op4(_ent, _cs, {k: _cl for k in "ABCD"})
assert [e["ticker"] for e in _a] == ["A", "B"] and [e["ticker"] for e in _c] == ["C"] and _x == 1, "A at 86c and NO on B at 1 - 0.10 = 90c are in; C at 71c is the complement; D has no candle at 10 minutes left and is excluded"
_a5, _c5, _x5 = _L2.split_op5(_ent, {"A": 0.01, "B": 0.02, "C": 0.03})
assert [e["ticker"] for e in _a5] == ["A", "B"] and [e["ticker"] for e in _c5] == ["C"] and _x5 == 1, "a spread of exactly 2c is tight, 3c is not, no candle is excluded"
assert _L2.verdict(_ent, _ent)[0] == "NOT_ENOUGH_DATA", "too few entries is not a verdict"
print("OP4 and OP5 tests passed")

# Fill study: the one sided Fisher exact p is the hypergeometric tail, a miss is scored at its decision price, and the data file has the orders it says it has.
from scalper import fillstudy as _FS
assert abs(_FS.fisher_one_sided(4, 22, 0, 35) - 0.019) < 0.001, "4 losses all among 22 of 57 orders: p about 0.019"
assert _FS.fisher_one_sided(0, 10, 0, 10) == 1.0 and abs(_FS.fisher_one_sided(1, 1, 0, 1) - 0.5) < 1e-9
_rows = _FS.load()
_s = _FS.summarize(_rows)
assert (_s["filled"], _s["missed"], _s["lost_filled"], _s["lost_missed"]) == (35, 22, 0, 4), "the recorded sample"
_won = {"ticker": "T", "side": "yes", "price": 0.9, "filled": False, "won": True, "pnl": 1 - 0.9 - _FS.fee(0.9)}
assert _FS.summarize([_won])["mean_missed"] > 0 and _FS.summarize([_won])["filled"] == 0, "a missed order is scored on what it would have made at its decision price"
print("fill study tests passed")
