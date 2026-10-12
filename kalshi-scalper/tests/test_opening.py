"""Plain assert tests for OW1 (src/scalper/opening.py); run with: python tests/test_opening.py
Each states a consequence, not a mechanism."""
import inspect
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import opening as OW

DAY = 86400


def mk(i, close, bid, ask, res, series="KXBTC15M"):
    """One market whose only candle is the one that ends 600 s before the close, as scalps.load() returns them."""
    return ("T%d" % i, series, [(close - 600, bid, ask, bid, ask)], close, res)


def planted(n, per_day, ask, win_p, seed, start, prefix=0):
    """n markets after `start`, per_day to a UTC day, each a YES book at `ask` (bid one cent under) that wins with probability win_p. The ask drifts by a cent from day to day
    so the day clusters differ: a perfectly identical set has no spread to measure and could never pass a z bar, which would say nothing about the rule."""
    g = random.Random(seed)
    base = start - start % DAY + DAY          # the next UTC midnight, so a block of per_day markets is exactly one UTC day
    out = []
    for i in range(n):
        d, j = divmod(i, per_day)
        a = round(ask + (0.01 if d % 2 else 0.0), 4)
        close = base + d * DAY + (j + 1) * 900
        out.append(mk(prefix + i, close, round(a - 0.01, 4), a, "yes" if g.random() < win_p else "no"))
    return out


# The lanes are the registered ones, and they are the ones the paper recorder runs: the research number and the page's paper tally describe the same rule.
# The lanes are the registered ones. The paper recorder that used to write them was removed on Oct 12, 2026 (L1 is the only strategy); the offline research readout stays as history.
assert OW.LANES == {"F": (0.82, 0.87), "U": (0.20, 0.30)} and OW.LEFT_S == 600
print("OW1 lanes passed")

# One market never gets both lanes. A 5c wide book can put the YES ask at 84c (a favourite) and the NO price at 21c (an underdog): buying both is a guaranteed small loss.
_t = OW.OW1_START + 900
_both = OW.lane_entries([mk(1, _t, 0.79, 0.84, "yes")])
assert [e["ticker"] for e in _both["F"]] == ["T1"] and _both["U"] == [], "the favourite takes a market that fits both lanes"
_dog = OW.lane_entries([mk(2, _t, 0.24, 0.25, "no")])
assert _dog["F"] == [] and [e["side"] for e in _dog["U"]] == ["yes"], "a 25c YES side is only the underdog lane"
_no = OW.lane_entries([mk(3, _t, 0.74, 0.75, "no")])
assert _no["F"] == [] and [(e["side"], round(e["price"], 2)) for e in _no["U"]] == [("no", 0.26)], "a 75c favourite is only a 26c NO underdog, never an F entry"
print("OW1 one leg per market passed")

# Registration: a market that closed at or before OW1_START was looked at before the rules were fixed and never enters the forward numbers.
_old, _new = mk(10, OW.OW1_START, 0.84, 0.85, "yes"), mk(11, OW.OW1_START + 900, 0.84, 0.85, "yes")
assert [e["ticker"] for e in OW.lane_entries([_old, _new])["F"]] == ["T11"], "the close at exactly OW1_START is not forward"
assert [e["ticker"] for e in OW.exploratory_entries([_old, _new])["F"]] == ["T10"], "and it is reported as exploratory, separately"
print("OW1 registration boundary passed")

# Before the first read no verdict exists, however good the numbers look.
_edge = planted(400, 50, 0.85, 0.97, 1, OW.OW1_START)
assert all(v == {"first": None, "final": None} for v in OW.verdicts(_edge, OW.FIRST_READ - 1).values()), "no verdict before the registered date"
_early = OW.report(_edge, OW.FIRST_READ - 1)
assert not any(line.startswith("VERDICT") for line in _early.splitlines()), "the report prints numbers and no verdict before the date"
assert "information only" in _early
print("OW1 no verdict before the read date passed")

# A planted edge is seen only once there is enough of it; a planted loser is FALSIFIED; too little data says so and nothing more.
_after = OW.FIRST_READ
assert OW.verdicts(_edge, _after)["F"]["first"] == "NOT_YET_FALSIFIED", "400 winning entries on 8 days pass the bar"
_loser = planted(400, 50, 0.25, 0.20, 2, OW.OW1_START)
assert OW.verdicts(_loser, _after)["U"]["first"] == "FALSIFIED", "an underdog that wins 20% at 25c loses and is FALSIFIED"
assert OW.verdicts(planted(299, 50, 0.85, 1.0, 3, OW.OW1_START), _after)["F"]["first"] == "NOT_ENOUGH_DATA", "299 entries is not enough"
assert OW.verdicts(planted(380, 95, 0.85, 0.97, 4, OW.OW1_START), _after)["F"]["first"] == "NOT_ENOUGH_DATA", "380 entries on 4 days is not enough"
assert OW.verdicts([], _after)["F"]["first"] == "NOT_ENOUGH_DATA", "no data is NOT_ENOUGH_DATA, never a pass"
print("OW1 verdict bar passed")

# The first read never changes after its date: markets closing later cannot rewrite it.
_late = planted(500, 50, 0.85, 1.0, 5, OW.FIRST_READ + 3600, prefix=1000)
assert OW.verdicts(_loser, _after)["U"]["first"] == "FALSIFIED"
assert OW.verdicts(_loser + _late, OW.FIRST_READ + 5 * DAY)["U"]["first"] == "FALSIFIED", "a verdict is not reopened by later winners"
print("OW1 first read is clipped passed")

# The final read exists only for a lane that was short of data at the first.
_short = planted(250, 50, 0.85, 0.97, 6, OW.OW1_START)                       # 250 entries in 5 days: not enough at the first read
_more = planted(250, 50, 0.85, 0.97, 7, OW.FIRST_READ + 3600, prefix=2000)    # and 250 more before the final read
_v = OW.verdicts(_short + _more, OW.FINAL_READ)
assert _v["F"]["first"] == "NOT_ENOUGH_DATA" and _v["F"]["final"] == "NOT_YET_FALSIFIED", "a lane short at the first read gets a second and final one"
_v2 = OW.verdicts(_loser + _more, OW.FINAL_READ)
assert _v2["U"]["first"] == "FALSIFIED" and _v2["U"]["final"] is None, "a lane with a first verdict never gets a second try"
assert OW.verdicts(_short + _more, OW.FINAL_READ - 1)["F"]["final"] is None, "and the final read waits for its date"
print("OW1 final read passed")

# The report separates what was seen before registration from what is forward.
_rep = OW.report(_edge + [mk(900, OW.OW1_START - 900, 0.84, 0.85, "yes")], OW.FIRST_READ)
assert "Exploratory" in _rep and "VERDICT F" in _rep and "VERDICT U" in _rep
print("OW1 report passed")

# The exploratory ladder is information only. A price on a bucket's edge belongs to exactly one bucket (the upper edge is the next bucket's lower edge), and it never prints a verdict.
from scalper import ladder as LD
_edge_mkt = mk(50, OW.OW1_START + 900, 0.29, 0.30, "yes")                       # YES ask exactly 30c, so the NO side is 71c
_by = {b: es for b, es in LD.table([_edge_mkt], 600)}
assert len(_by[(0.25, 0.30)]) == 0 and len(_by[(0.30, 0.35)]) == 1 and len(_by[(0.70, 0.78)]) == 1, "30c is in 30-35c, never in 25-30c; its other side, 71c, is in 70-78c"
_src = (Path(__file__).resolve().parents[1] / "src" / "scalper" / "ladder.py").read_text()
assert not re.search(r"FALSIFIED|NOT_ENOUGH_DATA", _src), "the ladder has no verdict word"
print("OW1 ladder passed")

# Nothing here can be tuned toward a result: no function takes a performance parameter.
_bad = {"target", "min_pf", "pf", "edge", "threshold", "z_bar", "min_n", "band", "bands"}
for _name, _fn in inspect.getmembers(OW, inspect.isfunction):
    if _fn.__module__ == OW.__name__:
        assert not (set(inspect.signature(_fn).parameters) & _bad), _name + " takes a parameter that could be tuned toward a result"
print("OW1 tests passed")
