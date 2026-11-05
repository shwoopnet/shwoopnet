import sys, math
sys.path.insert(0, "src")
from scalper import rainfact1 as r

assert r.fee(0.5) == math.ceil(0.07 * 10 * 0.25 * 100) / 100 / 10
# t_fact: hourly max, cumulative 0.01, only rows inside the day; a special repeating the hour does not double count
rows = [(1000, 0.0), (4600, 0.005), (4700, 0.005), (8200, 0.01)]
assert r.t_fact([(100, 0.0), (3700, 0.0)], 0, 10**6) is None
assert r.t_fact([(100, 0.01)], 0, 10**6) == 100
assert r.t_fact([(100, 0.01)], 200, 10**6) is None            # before the market day
assert r.t_fact([(7200, 0.004), (7300, 0.004), (7400, 0.004)], 0, 10**6) is None   # repeats do not add
assert r.t_fact([(7200, 0.004), (10800, 0.006)], 0, 10**6) == 10800
cs = [dict(end_ts=100, bid=None, ask=0.5), dict(end_ts=200, bid=0.4, ask=0.6), dict(end_ts=300, bid=0.9, ask=0.95)]
assert r.entry_candle(cs, 100)["end_ts"] == 200 and r.entry_candle(cs, 140)["end_ts"] == 300
assert r.entry_candle(cs, 250) is None
assert abs(r.net(0.9, True) - (0.1 - r.fee(0.9))) < 1e-12 and r.net(0.9, False) < -0.9
assert abs(r.tail_prob([0.5, 0.5], 2) - 0.25) < 1e-12 and abs(r.tail_prob([0.5, 0.5], 0) - 1) < 1e-12
try:
    r.guard([dict(ticker="X", close_ts=r.CUT)]); raise SystemExit("guard failed")
except RuntimeError:
    pass
# Amendment 1: an early close takes the neighbour's/Eastern reference's scheduled close
byk = {("X", 1): dict(close_ts=1 * 86400 + 5 * 3600)}
assert r.sched_close(dict(city="X", ticker="K-A-X", close_ts=2 * 86400 + 14 * 3600), byk, {}) == 2 * 86400 + 5 * 3600
assert r.sched_close(dict(city="X", ticker="K-A-X", close_ts=2 * 86400 + 4 * 3600), byk, {}) == 2 * 86400 + 4 * 3600
assert r.sched_close(dict(city="Y", ticker="K-A-Y", close_ts=2 * 86400 + 14 * 3600), {}, {"K-A": 2 * 86400 + 4 * 3600}) == 2 * 86400 + 4 * 3600
print("ok")
