"""Plain assert tests for SS2 (src/scalper/ss2.py); run with: python tests/test_ss2.py. Each states a consequence, not a mechanism."""
import inspect
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import ss2 as S
from scalper import scalps

CLOSE = 1_800_000_000


def candle(left, bid, ask):
    return (CLOSE - left, bid, ask, bid, ask)


def by(*cs):
    return {c[0]: c for c in cs}


# The grid is exactly the registered 1,760 cells.
assert len(S.CELLS) == 1760 and len({(c["series"], c["left"], c["band"], c["cond"], c["exit"], c["target"]) for c in S.CELLS}) == 1760
assert sum(1 for c in S.CELLS if c["exit"] == "hold") == 800 and all(c["left"] in S.SCALP_LEFTS for c in S.CELLS if c["exit"] == "scalp")
live = (Path(__file__).resolve().parents[2] / "functions" / "kalshiLiveLib.js").read_text()
l1 = re.search(r"L1_WINDOW_MS = \[(\d+), (\d+)\]", live)
assert S.EXIT_LEFT_S > int(l1.group(2)) / 1000, "a scalp is always sold before L1's earliest buy"
print("SS2 grid passed")

hold = dict(series="ALL", left=360, band=(0.88, 0.97), cond="none", exit="hold", target=None)
# Hold: the fee is paid once, on the entry, and settlement pays no fee. A win nets 1 - ask - fee, a loss -ask - fee.
c2 = CLOSE + 900
rows = S.rows_for(hold, [("T", "KXBTC15M", by(candle(360, 0.90, 0.92)), CLOSE, "yes"), ("U", "KXBTC15M", by((c2 - 360, 0.90, 0.92, 0.90, 0.92)), c2, "no")])
assert abs(rows[0]["net"] - (1 - 0.92 - scalps.fee(0.92))) < 1e-9 and abs(rows[1]["net"] - (0 - 0.92 - scalps.fee(0.92))) < 1e-9
# Series filter: a Bitcoin cell never takes a gold market.
btc = dict(hold, series="KXBTC15M")
assert S.rows_for(btc, [("G", "KXGOLD15M", by(candle(360, 0.90, 0.92)), CLOSE, "yes")]) == []
# Conditions.
assert S.find_entry(by(candle(360, 0.90, 0.91)), CLOSE, dict(hold, cond="wide")) is None and S.find_entry(by(candle(360, 0.89, 0.93)), CLOSE, dict(hold, cond="wide")) is not None
assert S.find_entry(by(candle(360, 0.90, 0.91)), CLOSE, dict(hold, cond="tight")) is not None and S.find_entry(by(candle(360, 0.89, 0.93)), CLOSE, dict(hold, cond="tight")) is None
mom = dict(hold, cond="momentum")
assert S.find_entry(by(candle(420, 0.86, 0.88), candle(360, 0.90, 0.92)), CLOSE, mom) is not None and S.find_entry(by(candle(360, 0.90, 0.92)), CLOSE, mom) is None
# A scalp is sold at its target or at the 480 s candle, never later; a missing 480 s candle leaves it out.
sc = dict(series="ALL", left=720, band=(0.20, 0.40), cond="none", exit="scalp", target=0.03)
r = S.rows_for(sc, [("T", "KXBTC15M", by(candle(720, 0.24, 0.25), candle(660, 0.29, 0.30), candle(480, 0.10, 0.12)), CLOSE, "yes")])
assert abs(r[0]["net"] - (0.29 - (0.25 + scalps.fee(0.25)) - scalps.fee(0.29))) < 1e-9
assert S.rows_for(sc, [("T", "KXBTC15M", by(candle(720, 0.24, 0.25), candle(600, 0.20, 0.22)), CLOSE, "yes")]) == []
print("SS2 entries and exits passed")

# Selection uses training rows only, needs enough entries, and takes the highest mean; the split is a function of the first date.
def mk(n, mean, days=10):
    return [{"day": "d%02d" % (i % days), "net": mean, "stress": mean, "close_ts": i, "ask": 0.9, "bid": 0.89, "mid": 0.895, "win": 1.0} for i in range(n)]
a, b, c = dict(hold, left=360), dict(hold, left=480), dict(hold, left=600)
pk = S.select([(a, mk(200, -0.02)), (b, mk(200, -0.005)), (c, mk(60, 0.05))])
assert [p[1] for p in pk][0] == b and len(pk) == 2, "the 60 entry cell with the best mean does not qualify"
assert S.split_ts([("T", "x", {}, 1_000_000, "yes"), ("U", "x", {}, 1_000_000 + 40 * 86400, "yes")]) == 1_000_000 + 24 * 86400
assert S.verdict(mk(400, -0.01))[0] == "FALSIFIED" and S.verdict(mk(100, 0.05))[0] == "NOT_ENOUGH_DATA" and S.verdict([])[0] == "NOT_ENOUGH_DATA"
# The placebo changes outcomes only: entries, prices and fees are kept, and a fair market has no edge on average.
rng = random.Random(1)
pr = S.placebo_rows([{"day": "d", "close_ts": 1, "net": 0, "stress": 0, "ask": 0.92, "bid": 0.91, "mid": 0.915, "win": 1.0}] * 20000, rng)
assert all(p["ask"] == 0.92 for p in pr)
mean = sum(p["net"] for p in pr) / len(pr)
assert abs(mean - (0.915 - 0.92 - scalps.fee(0.92))) < 0.01, "fair-priced outcomes earn about minus the spread and fee"
print("SS2 selection and placebo passed")

src = re.sub(r"#.*|\"\"\"[\s\S]*?\"\"\"", "", Path(S.__file__).read_text())
assert not re.search(r"promote|PROMOTE", src)
bad = {"target_pf", "min_pf", "pf", "edge", "threshold", "z_bar", "min_n"}
for name, fn in inspect.getmembers(S, inspect.isfunction):
    if fn.__module__ == S.__name__:
        assert not (set(inspect.signature(fn).parameters) & bad), name
print("SS2 tests passed")
