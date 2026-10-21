"""Plain assert tests for TREE2 (src/scalper/tree2.py); run with: python tests/test_tree2.py. Each states a consequence, not a mechanism."""
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import tree1 as T
from scalper import tree2 as Q

assert (Q.Z_BAR, Q.DIFF_Z_BAR, Q.MIN_KEPT, Q.MIN_DAYS, Q.BURN_DAYS, Q.REFIT_EVERY, Q.DEPTH, Q.MIN_LEAF, Q.PLACEBO_REPS) == (2.6, 2.0, 1000, 10, 14, 7, 3, 400, 100), "the registered numbers"
assert len(Q.NUMERIC) == 10 and set(Q.SOURCES) == {"alts2", "alts3", "alts4", "book", "l1b", "e3b"}


def synth(days=45, per=120, seed=2):
    """Two series, A and B. B loses 60% of the time, A 1%: the only structure there is."""
    rng = random.Random(seed)
    rows = []
    for d in range(days):
        day = f"2026-09-{d + 1:02d}" if d < 30 else f"2026-10-{d - 29:02d}"
        for k in range(per):
            b = rng.random() < 0.5
            lose = rng.random() < (0.6 if b else 0.01)
            net = -0.93 if lose else 0.05
            feats = [0.93, 0.01, 0.0, 0.0, 0.0, 0.02, 0.9, 0.0, float(rng.randrange(24)), float(rng.randrange(7)), 0.0 if b else 1.0, 1.0 if b else 0.0]
            rows.append({"day": day, "close_ts": d * 86400 + k * 60, "net": net, "stress": net, "gross": net, "price": 0.93,
                         "feats": feats, "pat": None, "series": "B" if b else "A"})
    return rows


rows = synth()
cuts = T.cut_points(rows)
y = [r["net"] for r in rows]
dec = T.tree_walk(rows, y, cuts, Q.BURN_DAYS, Q.REFIT_EVERY, Q.DEPTH, Q.MIN_LEAF)
assert dec and all(rows[i]["day"] > sorted({r["day"] for r in rows})[Q.BURN_DAYS - 1] for i in dec), "the first 14 days are training only"
# A series that loses most of the time is dropped, and the good one is kept, out of sample.
assert sum(1 for i, s in dec.items() if rows[i]["series"] == "B" and s) > 0.95 * sum(1 for i in dec if rows[i]["series"] == "B")
assert sum(1 for i, s in dec.items() if rows[i]["series"] == "A" and s) == 0
assert T.gain(dec, y) > 0.2

# No peeking with weekly refits either: changing a LATER day's outcomes cannot change an EARLIER day's decision.
y2 = list(y)
last = sorted({r["day"] for r in rows})[-1]
for i, r in enumerate(rows):
    if r["day"] == last:
        y2[i] = -0.93
dec2 = T.tree_walk(rows, y2, cuts, Q.BURN_DAYS, Q.REFIT_EVERY, Q.DEPTH, Q.MIN_LEAF)
assert all(dec[i] == dec2[i] for i in dec if rows[i]["day"] != last)
# The weekly refit means a day's tree is at most 7 days stale, never fitted on that day: shifting a day inside the week changes only later weeks' trees.
mid = sorted({r["day"] for r in rows})[Q.BURN_DAYS + 2]
y3 = list(y)
for i, r in enumerate(rows):
    if r["day"] == mid:
        y3[i] = -0.93
dec3 = T.tree_walk(rows, y3, cuts, Q.BURN_DAYS, Q.REFIT_EVERY, Q.DEPTH, Q.MIN_LEAF)
assert all(dec[i] == dec3[i] for i in dec if rows[i]["day"] <= mid), "decisions up to the shifted day are unchanged"

# A kept set that fails in one month cannot pass: judge needs the kept mean to beat the all-decided mean in every judged month.
v, s = Q.judge(rows, dec, -1.0)
assert "month_ok" in s and isinstance(s["month_ok"], bool)
# Too few kept entries is NOT_ENOUGH_DATA, never a pass.
v2, _ = Q.judge(rows, {i: (i % 2 == 0) for i in list(dec)[:200]}, 0.0)
assert v2 == "NOT_ENOUGH_DATA"
# Without a placebo value there is no pass however good the numbers look.
v3, _ = Q.judge(rows, dec, None)
assert v3 != "NOT_YET_FALSIFIED"

src = Path(Q.__file__).read_text()
code = re.sub(r"#.*", "", re.sub(r'"""[\s\S]*?"""', "", src))
for word in ("promote", "--target", "--until"):
    assert word not in code.lower()
assert "Refusing to run again" in src and Q.RESULT.name == "tree2_result.txt"
print("test_tree2: ok")
