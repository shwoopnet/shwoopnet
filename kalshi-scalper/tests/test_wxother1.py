"""Plain assert tests for src/scalper/wxother1.py; run with: python tests/test_wxother1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import wxother1 as W

# covered families are filtered out of the candidate list; the remaining ones are labelled
ss = [{"ticker": t} for t in ("KXHIGHCHI", "KXLOWTNYC", "KXRAIND", "KXRAINDNYC", "KXRAIN", "KXHIGHNYD", "KXNYCSNOWM", "KXRAINNYCM", "KXAVGTKPHX", "KXTORNADO", "KXEMERGENCYLA", "KXVAILOPEN", "KXTEMPNYCH", "KXLOWDEN")]
c = W.candidates(ss)
assert "KXHIGHCHI" not in c and "KXLOWTNYC" not in c and "KXRAIND" not in c and "KXRAINDNYC" not in c and "KXRAIN" not in c and "KXLOWDEN" not in c
assert "KXEMERGENCYLA" not in c and "KXVAILOPEN" not in c
assert W.family("KXNYCSNOWM") == "snowfall" and W.family("KXRAINNYCM") == "rain totals (month/week)" and W.family("KXAVGTKPHX") == "weekly temperature"
assert W.family("KXTEMPNYCH") == "hourly directional temperature" and W.family("KXTORNADO") == "tornadoes" and W.family("KXHIGHNYD") == "hourly directional temperature"
assert "KXHIGHNYD" in c and "KXSEAICE" in c      # hourly directional is kept in the census (to be labelled DUPLICATE of WXNEW1), extras added
# cap: per event at most 2 markets with volume
rows = [("e1", "2026-01-01T00:00:00Z", 30.0, "a"), ("e1", "2026-01-01T00:00:00Z", 50.0, "b"), ("e1", "2026-01-01T00:00:00Z", 90.0, "c"), ("e2", "2026-01-02T00:00:00Z", 5.0, "d")]
k = W.cap(rows)
assert k["events"] == 2 and k["traded_events"] == 1 and k["upper_bound"] == 2
assert W.verdict(149, 500) == "NOT_RUNNABLE" and W.verdict(150, 149) == "NOT_RUNNABLE" and W.verdict(150, 150) == "RUNNABLE"
# fee: 10 contracts at 0.10 -> 0.07*10*0.1*0.9 = 0.063 -> 0.07 -> 0.007 each
assert abs(W.fee(0.10) - 0.007) < 1e-12
# model: forecast 70, bias 0, sd 2: P(>70)=0.5, P(>74) small
assert abs(W.prob_above(70, 0, 2, 70) - 0.5) < 1e-9 and W.prob_above(70, 0, 2, 74) < 0.03
b, sd = W.fit_error([(70, 71), (60, 59), (50, 51), (40, 41)])
assert abs(b - 0.5) < 1e-9 and sd > 0.1
# pick: cheap side only, ratio >= 3, max 2 per event, favourite side (ask > 0.30) never picked
q = [("m1", 0.10, 0.92), ("m2", 0.20, 0.82), ("m3", 0.05, 0.97), ("m4", 0.40, 0.62)]
mp = {"m1": 0.40, "m2": 0.50, "m3": 0.20, "m4": 0.9}
r = W.pick(q, mp)
assert [x[0] for x in r] == ["m3", "m1"] and all(x[2] <= 0.30 for x in r)       # ratios 4.0, 4.0 -> m3/m1 by order; m2 is 2.5x so not taken
assert all(x[1] == "yes" for x in r)
assert W.pick([("m5", 0.95, 0.04)], {"m5": 0.5}) == [("m5", "no", 0.04)]        # the cheap side is the NO side here
assert W.pick([("m6", 0.95, 0.04)], {"m6": 0.97}) == []                         # P(no) 0.03 < 3 x 0.04: nothing, and the 0.95 side is never considered
print("ok")
