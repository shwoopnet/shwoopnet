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
