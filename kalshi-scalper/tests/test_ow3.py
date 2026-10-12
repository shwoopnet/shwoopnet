"""Plain assert tests for OW3, OW4 and OW7 (src/scalper/ow3.py); run with: python tests/test_ow3.py. Each states a consequence, not a mechanism."""
import inspect
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import ow3 as W

DAY = 86400


def rows(n, per_day, mean, seed, start=1_700_000_000, extra=None):
    """n entries over n/per_day days whose net is mean plus noise."""
    g = random.Random(seed)
    out = []
    for i in range(n):
        d, j = divmod(i, per_day)
        out.append(dict({"day": "d%03d" % d, "close_ts": start + d * DAY + j * 900, "net": mean + g.gauss(0, 0.2), "stress": mean - 0.01 + g.gauss(0, 0.2)}, **(extra or {})))
    return out


# A planted difference is seen, a null is not.
a, b = rows(600, 20, 0.03, 1), rows(600, 20, 0.0, 2)
d, se, z = W.contrast(a, b)
assert d > 0.02 and z > 2.5, (d, z)
d0, se0, z0 = W.contrast(rows(600, 20, 0.0, 3), rows(600, 20, 0.0, 4))
assert abs(z0) < 2.5, "no planted difference: no z"
print("OW3 contrast passed")

# Entries from one day share that day's luck, so a day-level shock widens the clustered standard error beyond the one that treats every entry as independent.
g = random.Random(5)
shock = {"d%03d" % d: g.gauss(0, 0.08) for d in range(30)}
sa = [dict(r, net=r["net"] + shock[r["day"]]) for r in rows(600, 20, 0.0, 5)]
sb = rows(600, 20, 0.0, 6)
naive = (sum((r["net"] - sum(x["net"] for x in sa) / 600) ** 2 for r in sa) / 600 ** 2 + sum((r["net"] - sum(x["net"] for x in sb) / 600) ** 2 for r in sb) / 600 ** 2) ** 0.5
assert W.contrast(sa, sb)[1] > 1.5 * naive, "a shared day shock must widen the standard error"
print("OW3 clustering passed")

# Too little data is NOT_ENOUGH_DATA, never a pass; a planted difference that is positive in both halves passes; one that flips in a half does not.
mid = 1_700_000_000 + 15 * DAY
assert W.verdict(a[:100], b[:100], mid)[0] == "NOT_ENOUGH_DATA"
assert W.verdict(a, b, mid)[0] == "NOT_YET_FALSIFIED"
flip = [dict(r, net=r["net"] - 0.06) if r["close_ts"] >= mid else r for r in a]
assert W.verdict(flip, b, mid)[0] == "FALSIFIED", "a difference that is negative in the second half fails"
assert W.verdict(a, [dict(r, net=r["net"] + 0.03) for r in b], mid)[0] == "FALSIFIED", "no difference, no pass"
print("OW3 verdict passed")

# OW3 must not win by price alone: NO entries sit at higher prices (so net is higher) and the residual contrast removes it.
g = random.Random(7)
fake = []
for i in range(2000):
    side = "no" if i % 2 else "yes"
    price = 0.93 if side == "no" else 0.84
    fake.append({"day": "d%03d" % (i // 70), "close_ts": 1_700_000_000 + (i // 70) * DAY + (i % 70) * 900, "side": side, "price": price, "left": 600, "net": (price - 0.9) * 0.5 + g.gauss(0, 0.2), "stress": 0.0})
W.residualise(fake)
a3 = [dict(r, net=r["res"]) for r in fake if r["side"] == "no"]
b3 = [dict(r, net=r["res"]) for r in fake if r["side"] == "yes"]
assert abs(W.contrast(a3, b3)[0]) < 1e-9, "same bucket never shared: residuals are zero, so price alone shows nothing"
print("OW3 price matching passed")

# OW4: the weekday US-hours window is 13:30 to 20:00 UTC, Monday to Friday.
import datetime as dt
ts = lambda y, m, d, h, mi: int(dt.datetime(y, m, d, h, mi, tzinfo=dt.timezone.utc).timestamp())
assert W.is_us_hours(ts(2026, 10, 12, 13, 30)) and W.is_us_hours(ts(2026, 10, 12, 19, 45))
assert not W.is_us_hours(ts(2026, 10, 12, 13, 15)) and not W.is_us_hours(ts(2026, 10, 12, 20, 0))
assert not W.is_us_hours(ts(2026, 10, 10, 15, 0)), "a Saturday is never US hours"
print("OW4 hours passed")

# OW7: the feature is open-interest change over summed volume, and a missing candle leaves the market out instead of being filled in.
C = 1_800_000_000
full = {C - 600: (100, 5), C - 540: (105, 10), C - 480: (110, 10), C - 420: (115, 10), C - 360: (130, 10)}
assert abs(W.oi_feature(full, C) - (130 - 100) / 40.0) < 1e-9
assert W.oi_feature({k: v for k, v in full.items() if k != C - 480}, C) is None
assert W.oi_feature({**full, C - 420: (115, None)}, C) is None
assert W.oi_feature({**full, C - 360: (None, 10)}, C) is None
# The forward read uses the OLD boundary: a feature of 0.2395 or less is arm B whatever the new sample looks like.
fm = [("T%d" % i, "KXBTC15M", [(C + i * 900 - 360, 0.9, 0.91, 0.9, 0.91)], C + i * 900, "yes") for i in range(6)]
raw7 = {"T0": 0.10, "T1": 0.20, "T2": 0.2395, "T3": 0.24, "T4": 0.50, "T5": 0.90}
fa, fb, fn = W.ow7_arms(fm, raw7, W.OW7_FIXED_CUT)
assert sorted(r["ticker"] for r in fb) == ["T0", "T1", "T2"] and sorted(r["ticker"] for r in fa) == ["T3", "T4", "T5"], "the boundary is fixed, not refit"
a7, b7, n = W.ow7_arms([], {})
assert a7 == [] and b7 == [] and n == 0
print("OW7 feature passed")

# Nothing here can be tuned toward a result, and the only verdict words are the three.
src = re.sub(r"#.*|\"\"\"[\s\S]*?\"\"\"", "", Path(W.__file__).read_text())
assert not re.search(r"promote|PROMOTE", src)
bad = {"target", "min_pf", "pf", "edge", "threshold", "z_bar", "min_n", "band", "bands"}
for name, fn in inspect.getmembers(W, inspect.isfunction):
    if fn.__module__ == W.__name__:
        assert not (set(inspect.signature(fn).parameters) & bad), name
print("OW3 tests passed")
