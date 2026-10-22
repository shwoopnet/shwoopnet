import sys
sys.path.insert(0, "src")
from scalper import losscl1 as T

e = lambda s, t, g: {"series": s, "close_ts": t, "gross": g}
rows = [e("A", 0, -1.0), e("A", 2000, 0.1), e("A", 5000, 0.1), e("B", 1900, -1.0)]
rl, nrl = T.classify(rows)
# A@2000: A@0 closed 2000 s earlier (inside 1800..3600) and lost -> RL. A@5000: A@2000 closed 3000 s earlier, won -> NOT_RL. A@0 and B@1900 have no earlier entry -> dropped.
assert [r["close_ts"] for r in rl] == [2000] and [r["close_ts"] for r in nrl] == [5000], (rl, nrl)
rl2, nrl2 = T.classify(rows, True)
# market-wide: B@1900 sees A@0 (1900 s earlier, lost) -> RL; A@2000 sees A@0 -> RL; A@5000 sees B@1900 (3100 s earlier, lost) -> RL; B@1900 is too recent (100 s) for A@2000 but A@0 covers it
assert [r["close_ts"] for r in rl2] == [1900, 2000, 5000] and nrl2 == [], (rl2, nrl2)
print("ok")
