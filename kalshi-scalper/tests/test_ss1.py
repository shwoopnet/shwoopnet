"""Plain assert tests for SS1 (src/scalper/ss1.py); run with: python tests/test_ss1.py. Each states a consequence, not a mechanism."""
import inspect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import ss1 as S
from scalper import scalps

CLOSE = 1_800_000_000


def candle(left, bid, ask):
    return (CLOSE - left, bid, ask, bid, ask)


# The grid is exactly the registered 216 cells, and nothing in it can be held past the cut-off or enter after the first four minutes.
assert len(S.CELLS) == 216 and len({(c["left"], c["band"], c["cond"], c["target"], c["stop"]) for c in S.CELLS}) == 216
assert S.ENTRY_LEFTS == (840, 780, 720, 660) and S.EXIT_LEFT_S == 480
live = (Path(__file__).resolve().parents[2] / "functions" / "kalshiLiveLib.js").read_text()
l1 = re.search(r"L1_WINDOW_MS = \[(\d+), (\d+)\]", live)
assert S.EXIT_LEFT_S > int(l1.group(2)) / 1000, "the last exit is before L1's earliest buy"
print("SS1 grid passed")

cell = dict(left=780, band=(0.20, 0.40), cond="none", target=0.03, stop=None)
# Target: ask 25c, a later closing bid of 28c sells there, with both fees.
t = S.trade([candle(780, 0.24, 0.25), candle(720, 0.26, 0.27), candle(660, 0.28, 0.29), candle(480, 0.10, 0.12)], CLOSE, cell)
assert t["how"] == "target" and t["exit_left"] == 660
assert abs(t["net"] - (0.28 - (0.25 + scalps.fee(0.25)) - scalps.fee(0.28))) < 1e-9
# Time exit at the 480 s candle, never later and never held to settlement; a missing 480 s candle is unresolvable, not settled.
t = S.trade([candle(780, 0.24, 0.25), candle(600, 0.20, 0.22), candle(480, 0.10, 0.12)], CLOSE, cell)
assert t["how"] == "time" and t["exit_left"] == 480
assert S.trade([candle(780, 0.24, 0.25), candle(600, 0.20, 0.22)], CLOSE, cell) == {"unresolvable": True}
# Stop: a closing bid 4c under the entry ask sells at that candle's bid.
stop_cell = dict(cell, stop=0.04)
t = S.trade([candle(780, 0.24, 0.25), candle(720, 0.20, 0.22), candle(480, 0.30, 0.31)], CLOSE, stop_cell)
assert t["how"] == "stop" and t["exit_left"] == 720
# A cell enters on its own minute only: a 25c ask on the 720 s candle is no entry for a 780 s cell, and there is no entry after the first four minutes at all. Only the closing bid ever counts.
assert S.trade([candle(720, 0.24, 0.25), candle(480, 0.5, 0.52)], CLOSE, cell) is None
assert S.find_entry([candle(660, 0.24, 0.25)], CLOSE, dict(cell, left=660))["left"] == 660
t = S.trade([candle(780, 0.24, 0.25), (CLOSE - 720, 0.2, 0.22, 0.60, 0.22), candle(480, 0.2, 0.22)], CLOSE, cell)
assert t["how"] == "time", "a 60c high inside a minute is not credited"
print("SS1 exits passed")

# Conditions: momentum needs the ask at least 3c above the previous candle's; dip needs it at least 3c below; a missing previous candle means no entry.
mom, dip = dict(cell, cond="momentum"), dict(cell, cond="dip")
assert S.find_entry([candle(840, 0.20, 0.22), candle(780, 0.24, 0.26)], CLOSE, mom)["left"] == 780
assert S.find_entry([candle(840, 0.23, 0.25), candle(780, 0.24, 0.26)], CLOSE, mom) is None
assert S.find_entry([candle(840, 0.28, 0.30), candle(780, 0.24, 0.26)], CLOSE, dip)["left"] == 780
assert S.find_entry([candle(780, 0.24, 0.26)], CLOSE, dip) is None
print("SS1 conditions passed")

# Selection uses the TRAINING rows only and picks the highest mean among cells with enough entries; the split is a function of the first date.
def rows(n, mean, days=10):
    return [{"day": "d%02d" % (i % days), "net": mean, "stress": mean, "how": "time", "close_ts": i} for i in range(n)]
a, b, c = dict(cell, target=0.03), dict(cell, target=0.05), dict(cell, target=0.08)
pick = S.select([(a, rows(400, -0.02)), (b, rows(400, -0.005)), (c, rows(100, 0.05))])
assert pick[0] == b, "the 100 entry cell with the best mean does not qualify"
assert S.select([(a, rows(100, 0.01))]) is None
mk = [("T", "KXBTC15M", [], 1_000_000, "yes"), ("U", "KXBTC15M", [], 1_000_000 + 40 * 86400, "yes")]
assert S.split_ts(mk) == 1_000_000 + 21 * 86400
# A frozen cell that loses on validation is FALSIFIED and too little data is never a pass.
assert S.verdict(rows(400, -0.01))[0] == "FALSIFIED" and S.verdict(rows(100, 0.05))[0] == "NOT_ENOUGH_DATA" and S.verdict([])[0] == "NOT_ENOUGH_DATA"
print("SS1 selection passed")

src = re.sub(r"#.*|\"\"\"[\s\S]*?\"\"\"", "", Path(S.__file__).read_text())
assert not re.search(r"promote|PROMOTE", src)
bad = {"target_pf", "min_pf", "pf", "edge", "threshold", "z_bar", "min_n"}
for name, fn in inspect.getmembers(S, inspect.isfunction):
    if fn.__module__ == S.__name__:
        assert not (set(inspect.signature(fn).parameters) & bad), name
print("SS1 tests passed")
