"""Plain assert tests for TREE1 and PAT1 (src/scalper/tree1.py); run with: python tests/test_tree1.py. Each states a consequence, not a mechanism."""
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import tree1 as T

assert (T.Z_BAR, T.DIFF_Z_BAR, T.MIN_KEPT, T.BURN_DAYS, T.DEPTH, T.MIN_LEAF, T.PAT_LEN, T.PAT_K, T.PAT_SKIP_LOSSES, T.PLACEBO_REPS) == (2.5, 2.0, 300, 14, 2, 250, 9, 200, 24, 100), "the registered numbers"
assert len(T.FEATURES) == 13


def candles(close_ts, base=0.93, n=16):
    """16 one minute candles ending at close-900 ... close, a quiet favourite at `base`."""
    return [(close_ts - 900 + 60 * i, base - 0.01, base + 0.01, base, base) for i in range(n)]


# 1. A feature can only use candles that END at or before the decision candle: changing every later candle cannot change a feature or a pattern.
close = 1_790_000_000 - (1_790_000_000 % 900)
t = close - 360
a = candles(close)
b = [c if c[0] <= t else (c[0], 0.05, 0.06, 0.07, 0.05) for c in a]
assert T.row_features(a, t, "yes", 0.94, close, "KXBTC15M") == T.row_features(b, t, "yes", 0.94, close, "KXBTC15M"), "nothing after the decision candle reaches a feature"
f, p = T.row_features(a, t, "yes", 0.94, close, "KXBTC15M")
assert f is not None and len(f) == len(T.FEATURES) and p is not None and len(p) == T.PAT_LEN
# A missing candle excludes the row from that learner; it is never filled.
holes = [c for c in a if c[0] != t - 120]
f2, p2 = T.row_features(holes, t, "yes", 0.94, close, "KXBTC15M")
assert f2 is None and p2 is None
# The NO side is the mirror: a quiet YES favourite at 0.93 is a NO side near 0.07, so its price feature is whatever the caller bought at, and its mids are 1 minus the YES mids.
fn, pn = T.row_features(a, t, "no", 0.07, close, "KXETH15M")
assert fn is not None and fn[-2] == 1.0 and fn[-3] == 0.0, "series flags"


# 2. A planted rule is found: when a wide spread always precedes the loss, the tree skips wide spread entries and nothing else, out of sample.
def synth(days=30, per=120, planted=True, seed=1):
    rng = random.Random(seed)
    rows = []
    for d in range(days):
        for k in range(per):
            spread = rng.choice([0.01, 0.02, 0.06])
            lose = (rng.random() < (0.8 if spread == 0.06 else 0.01)) if planted else rng.random() < 0.01
            net = -0.93 if lose else 0.05
            feats = [0.93, spread, 0.0, 0.0, 0.0, 0.02, 0.9, 0.0, float(rng.randrange(24)), float(rng.randrange(7)), 1.0, 0.0, 0.0]
            rows.append({"day": f"2026-09-{d + 1:02d}" if d < 30 else f"2026-10-{d - 29:02d}", "close_ts": d * 86400 + k * 900, "net": net,
                         "stress": net, "gross": net, "price": 0.93, "feats": feats, "pat": [0.0] * 8 + [spread], "series": "KXBTC15M"})
    return rows


rows = synth()
cuts = T.cut_points(rows)
y = [r["net"] for r in rows]
dec = T.tree_walk(rows, y, cuts)
assert dec, "out of sample decisions exist after the burn-in"
assert all(rows[i]["day"] > sorted({r["day"] for r in rows})[T.BURN_DAYS - 1] for i in dec), "the first 14 days are training only"
skipped_wide = sum(1 for i, s in dec.items() if s and rows[i]["feats"][1] >= 0.06)
skipped_other = sum(1 for i, s in dec.items() if s and rows[i]["feats"][1] < 0.06)
assert skipped_wide > 100 and skipped_other == 0, (skipped_wide, skipped_other)
assert T.gain(dec, y) > 0.1, "skipping the planted losers raises the mean net of what is kept"

# 3. With no signal the tree does not invent one: it either skips nothing or skips without any gain beating chance (placebo is the judge, not the tree).
flat = synth(planted=False)
fy = [r["net"] for r in flat]
fdec = T.tree_walk(flat, fy, T.cut_points(flat))
assert sum(1 for s in fdec.values() if s) <= 0.35 * len(fdec), "no wild skipping on noise"

# 4. No peeking: changing a LATER day's outcomes cannot change an EARLIER day's decision (the walk-forward uses strictly earlier days).
y2 = list(y)
last = sorted({r["day"] for r in rows})[-1]
for i, r in enumerate(rows):
    if r["day"] == last:
        y2[i] = -0.93
dec2 = T.tree_walk(rows, y2, cuts)
assert all(dec[i] == dec2[i] for i in dec if rows[i]["day"] != last), "an earlier day's decision does not depend on a later day's result"

# 5. The placebo shuffles outcomes inside each day only: every day keeps its own multiset of outcomes, so day level luck is preserved.
z = T.shuffled_within_day(rows, y, random.Random(5))
for day in {r["day"] for r in rows}:
    assert sorted(y[i] for i, r in enumerate(rows) if r["day"] == day) == sorted(z[i] for i, r in enumerate(rows) if r["day"] == day)
assert z != y

# 6. PAT1 skips a pattern whose nearest neighbours lost: wide-spread patterns (the last number) lose 80%, so they are skipped; a clean pattern is not.
nb = T.neighbours(rows)
pdec = T.pat_walk(nb, y)
sk = sum(1 for i, s in pdec.items() if s and rows[i]["feats"][1] >= 0.06)
bad = sum(1 for i, s in pdec.items() if s and rows[i]["feats"][1] < 0.06)
assert sk > 100 and bad == 0, (sk, bad)

# 7. Too few kept entries is NOT_ENOUGH_DATA, never a pass: a rule cannot win by keeping 40 lucky entries.
v, s = T.judge(rows, {i: (i % 2 == 0) for i in list(dec)[:60]}, 0.0, "x")
assert v == "NOT_ENOUGH_DATA"
# A pass needs the placebo: with no placebo value there is no NOT_YET_FALSIFIED, however good the numbers.
v2, _ = T.judge(rows, dec, None, "x")
assert v2 != "NOT_YET_FALSIFIED"

# 8. The code has no promote verb (comments stripped), and a second run is refused while the result file exists.
src = Path(T.__file__).read_text()
code = re.sub(r'"""[\s\S]*?"""', "", src)
code = re.sub(r"#.*", "", code)
for word in ("promote", "--target", "--until"):
    assert word not in code.lower()
assert "Refusing to run again" in src and T.RESULT.name == "tree1_result.txt"
print("test_tree1: ok")
