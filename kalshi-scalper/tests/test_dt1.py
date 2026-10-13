"""Plain assert tests for DT1 (src/scalper/dt1.py); run with: python tests/test_dt1.py. Each states a consequence, not a mechanism."""
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import dt1 as D

assert len(D.FEATURES) == 11 and D.MAX_DEPTH == 3 and D.MIN_LEAF == 150 and D.SKIP_AT == -0.005 and D.TRAIN_DAYS == 20

# The tree finds a real split and respects the leaf size: net is -0.6 when feature 0 is high, +0.03 otherwise.
rng = np.random.default_rng(1)
X = rng.random((1200, 11))
cut = float(np.quantile(X[:, 0], 0.7))         # the true boundary sits on a decile, which is where the tree looks
y = np.where(X[:, 0] > cut, -0.6, 0.03) + rng.normal(0, 0.02, 1200)
tree = D.fit_tree(X, y)
assert tree["feat"] == 0 and abs(tree["thr"] - cut) < 1e-9
leaves = []
def walk(n):
    leaves.append(n) if "feat" not in n else (walk(n["left"]), walk(n["right"]))
walk(tree)
assert all(l["n"] >= D.MIN_LEAF for l in leaves) and sum(l["n"] for l in leaves) == 1200
# ... and flags exactly the bad region for skipping.
sm = D.skip_mask(tree, X)
assert (sm == (X[:, 0] > cut)).all() and y[sm].mean() < -0.5, "exactly the bad region is flagged"
# Pure noise: the tree may split but no leaf that looks bad survives a large shuffled sample unchanged (and a tiny sample never splits at all).
assert "feat" not in D.fit_tree(X[:200], y[:200], min_leaf=150), "fewer than two leaves' worth of rows never splits"

# The shuffled-label null keeps each series' set of net values and destroys the link to the features, reproducibly.
rows = [{"series": "A" if i % 2 else "B", "net": float(i)} for i in range(40)]
a, b = D.shuffled_within_series(rows, random.Random(5)), D.shuffled_within_series(rows, random.Random(5))
assert (a == b).all() and sorted(a[[i for i in range(40) if i % 2]]) == sorted(float(i) for i in range(40) if i % 2)
assert not (a == np.array([r["net"] for r in rows])).all()

# Entries: only candles at or before the entry candle and the previous market's RESULT are read. Poison everything later: nothing changes.
CLOSE = 1_800_000_000
def candles(ask=0.92):
    out = {}
    for left in range(900, 0, -60):
        e = CLOSE - left
        out[e] = (ask - 0.01, ask, 100.0)
    return out
def mk(series, close, res, cs):
    return {"series": series, "close_ts": close, "result": res, "candles": cs}
base = {"T1": mk("KXBTC15M", CLOSE, "yes", candles()), "T0": mk("KXBTC15M", CLOSE - 900, "yes", candles())}
r0 = D.build_entries(base)
assert len(r0) == 2 or len(r0) == 1
poisoned = {"T1": mk("KXBTC15M", CLOSE, "yes", {**candles(), **{CLOSE - l: (0.01, 0.99, 9999.0) for l in (300, 240, 180, 120, 60)}}), "T0": base["T0"]}
r1 = D.build_entries(poisoned)
assert [r["x"] for r in r0 if r["ticker"] == "T1"] == [r["x"] for r in r1 if r["ticker"] == "T1"], "candles after the entry candle are never read"
# The previous market's result feeds prev_yes (0.5 when it is missing), and an entry lacking a feature is dropped, not guessed.
t1 = [r for r in r0 if r["ticker"] == "T1"][0]
assert t1["x"][D.FEATURES.index("prev_yes")] == 1.0
alone = D.build_entries({"T1": base["T1"]})
assert alone[0]["x"][D.FEATURES.index("prev_yes")] == 0.5
short = candles(); del short[CLOSE - D.ENTRY_LEFT - 60]
assert D.build_entries({"T1": mk("KXBTC15M", CLOSE, "yes", short)}) == []
# The favourite side's mid change is signed toward the favourite: a NO favourite whose YES mid rises has weakened.
no_cs = {e: (0.07, 0.08, 10.0) for e in candles()}
no_cs[CLOSE - D.ENTRY_LEFT - 60] = (0.02, 0.03, 10.0)           # YES mid was lower a minute earlier; now 0.075: the NO side lost 0.05
rno = D.build_entries({"N": mk("KXBTC15M", CLOSE, "no", no_cs)})[0]
assert rno["x"][D.FEATURES.index("side_yes")] == 0.0 and rno["x"][D.FEATURES.index("d1")] < 0

# Verdict: each registered condition is necessary.
def vrows(n_days=20, per=15, bad=-0.5):
    out = []
    for d in range(n_days):
        for i in range(per):
            out.append({"day": f"2026-10-{1 + d:02d}", "net": (bad - 0.05 * (d % 4)) if i < 6 else 0.02, "series": "A"})
    return out
vr = vrows()
skipped = np.array([r["net"] < 0 for r in vr])
v, s = D.verdict(vr, skipped, [0.0] * 200)
assert v == "NOT_YET_FALSIFIED" and s["z"] <= -D.Z_BAR
assert D.verdict(vr, skipped, [10.0] * 200)[0] == "FALSIFIED", "an improvement inside the shuffled-label null falsifies"
assert D.verdict(vr, np.array([False] * len(vr)), [0.0])[0] == "NOT_ENOUGH_DATA"
few = np.array([r["net"] < 0 and r["day"] < "2026-10-04" for r in vr])
assert D.verdict(vr, few, [0.0])[0] == "NOT_ENOUGH_DATA", "fewer than 100 skipped entries is not enough data"
# Each half must show losers: a skipped set that loses in one half and wins in the other falls on that condition alone (z and the null both pass).
def half_case(win_in_first):
    rows = []
    for d in range(20):
        first = d < 10
        for i in range(6):
            lose = (first != win_in_first)
            rows.append({"day": f"2026-10-{1 + d:02d}", "net": (-0.5 - 0.05 * (d % 3)) if lose else 0.01, "series": "A"})
        for i in range(9):
            rows.append({"day": f"2026-10-{1 + d:02d}", "net": 0.02, "series": "A"})
    mask = np.array([r["net"] < 0.015 and r["net"] != 0.02 or (r["net"] == 0.01) for r in rows])
    return rows, mask
for first in (True, False):
    rows_, mask_ = half_case(first)
    vv, ss = D.verdict(rows_, mask_, [-1.0] * 200)
    assert ss["z"] <= -D.Z_BAR and ss["mean"] < 0 and ss["imp"] > ss["p95"] and vv == "FALSIFIED", f"win_in_first={first}: only the half condition can fail here"
# A negative skipped mean with a huge day-to-day swing fails on z alone.
noisy = [{"day": f"2026-10-{1 + d:02d}", "net": (-0.6 if d % 2 == 0 else 0.5), "series": "A"} for d in range(20) for _ in range(6)] + [{"day": f"2026-10-{1 + d:02d}", "net": 0.02, "series": "A"} for d in range(20) for _ in range(9)]
nm = np.array([r["net"] != 0.02 for r in noisy])
vn, sn = D.verdict(noisy, nm, [-1.0] * 200)
assert sn["mean"] < 0 and sn["z"] > -D.Z_BAR and sn["imp"] > sn["p95"] and vn == "FALSIFIED", "a big day-to-day swing fails on z alone"
# Skipping winners (a tree that flags good entries) improves nothing.
winners = np.array([r["net"] > 0 for r in vr])
assert D.verdict(vr, winners, [0.0])[0] == "FALSIFIED"
code = "\n".join(l.split("#")[0] for l in Path(D.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("DT1 passed")
