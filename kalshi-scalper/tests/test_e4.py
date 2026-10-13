"""Plain assert tests for E4 (src/scalper/e4.py); run with: python tests/test_e4.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import e4 as E
from scalper import lstrats as L

# The three registered series and windows, no more: another series would be an unregistered try. History goes to its own file.
assert E.SERIES_DAYS == {"KXINXU": 40, "KXBTCD": 14, "KXETHD": 14}
assert E.LADDER_DB.name == "ladders.sqlite"
# The rule is L1's, unchanged, and the entry candle (360 s before the close) is always inside the fetched window, with a minute either side.
assert L.L1 == {"left_s": 360, "band": (0.88, 0.97)}
assert E.WINDOW_BEFORE_S > L.L1["left_s"] > E.WINDOW_AFTER_S
assert E.CHUNK == 100

# Settled markets group by close time; one with no result or no readable close is dropped, never guessed.
listed = [{"ticker": "A", "close_time": "2026-10-13T20:00:00Z", "result": "yes"}, {"ticker": "B", "close_time": "2026-10-13T20:00:00Z", "result": "no"},
          {"ticker": "C", "close_time": "2026-10-13T21:00:00Z", "result": ""}, {"ticker": "D", "close_time": "bad", "result": "yes"},
          {"ticker": "E", "close_time": "2026-10-13T21:00:00Z", "result": "yes"}]
g = E.group_by_close(listed)
assert sorted(len(v) for v in g.values()) == [1, 2] and {m["ticker"] for v in g.values() for m in v} == {"A", "B", "E"}
assert [len(c) for c in E.chunks(list(range(250)), 100)] == [100, 100, 50]


def entry(ticker, close_ts, price, net, series="KXBTCD", day="2026-10-13"):
    return {"ticker": ticker, "series": series, "close_ts": close_ts, "price": price, "net": net, "day": day}


# One entry per hour takes the price nearest 92.5c, ties to the lower strike, and never more than one per series and hour.
es = [entry("t1", 100, 0.90, 0.05), entry("t2", 100, 0.93, 0.04), entry("t3", 100, 0.96, 0.02), entry("t4", 200, 0.92, -0.9, series="KXETHD"), entry("t5", 200, 0.93, 0.0)]
pick = E.one_per_hour(es, {"t1": 1, "t2": 2, "t3": 3, "t4": 4, "t5": 5})
assert sorted(e["ticker"] for e in pick) == ["t2", "t4", "t5"], "one per (series, hour)"
tie = [entry("a", 100, 0.915, 0.0), entry("b", 100, 0.935, 0.0)]
assert E.one_per_hour(tie, {"a": 50, "b": 10})[0]["ticker"] == "b", "a tie goes to the lower strike"

# The worst hour is the sum over that hour's entries: a ladder that loses five strikes at once is one big loss, not five small ones.
h = [entry(f"x{i}", 1000, 0.92, -0.92) for i in range(5)] + [entry(f"y{i}", 2000, 0.92, 0.07) for i in range(5)]
hs = E.hour_stats(h)
assert abs(hs["worst_hour"] - (-4.6)) < 1e-9 and hs["worst_n"] == 5 and hs["hours"] == 2 and hs["per_hour"] == 5

# Entries inside one hour share an outcome, so the hour clustered z is smaller than treating each entry as independent would give.
import math
from scalper.calibration import cluster_mean_z
obs = [(str(1000 + k), -0.9 if k % 4 == 0 else 0.06) for k in range(40) for _ in range(5)]
_, _, z_hour = cluster_mean_z(obs)
_, _, z_naive = cluster_mean_z([(str(i), v) for i, (_, v) in enumerate(obs)])
assert abs(z_hour) < abs(z_naive), "clustering by hour is more careful than counting each entry"

# The minimum detectable edge is exactly the pass bar's z times the day clustered standard error: the edge a test of this size could just barely see.
days = [entry(f"d{i}", 3000 + i, 0.92, -0.9 if i % 6 == 0 else 0.06, day=f"2026-10-{10 + i % 4}") for i in range(20)]
_, se, _ = cluster_mean_z([(e["day"], e["net"]) for e in days])
assert se > 0, "the fixture must have a nonzero standard error or this check proves nothing"
assert abs(E.hour_stats(days)["mde"] - E.Z_BAR * se) < 1e-12 and E.Z_BAR == 2.1

# The power rule: FALSIFIED with a wide minimum detectable edge is labelled "not shown", never "absent".
assert E.MDE_FLAG == 0.010
code = "\n".join(l.split("#")[0] for l in Path(E.__file__).read_text().splitlines())
assert "promote" not in code.lower() and "NOT SHOWN" in code
print("E4 passed")
