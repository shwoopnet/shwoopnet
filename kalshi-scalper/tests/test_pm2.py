"""Plain assert tests for PM2 (src/scalper/pm2.py); run with: python tests/test_pm2.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import l1b
from scalper import pm1
from scalper import pm2 as P

# Registered: the older days only (the same floor as L1B), the L1B download as the source, its own Polymarket file, the same 5 point rule as PM1's split.
assert P.FLOOR_TS == l1b.FLOOR_TS and P.SRC_DB.name == "l1b.sqlite" and P.PM2_DB.name == "pm2.sqlite" and P.PM2_DB != pm1.PM_DB
assert P.DISAGREE == 0.05 == pm1.DISAGREE and P.MIN_SKIPPED == 100 and P.Z_BAR == 2.1

# A window from the book's own days can never count: windows() drops anything on or after the floor, whatever the source holds.
orig = pm1.windows
pm1.windows = lambda src: [{"close_ts": P.FLOOR_TS - 1}, {"close_ts": P.FLOOR_TS}, {"close_ts": P.FLOOR_TS + 900}]
try:
    assert [w["close_ts"] for w in P.windows()] == [P.FLOOR_TS - 1]
finally:
    pm1.windows = orig

# Flagging: 5 points below Kalshi for the side bought is a skip (exactly 5 included); 4.9 is not; the NO side flips.
def ob(p_pm, side="yes"):
    return {"series": "KXBTC15M", "close_ts": 1, "day": "d", "bid": 0.89, "ask": 0.91, "p_k": 0.90, "p_pm": p_pm, "y": 1.0} if side == "yes" else \
           {"series": "KXBTC15M", "close_ts": 1, "day": "d", "bid": 0.05, "ask": 0.07, "p_k": 0.06, "p_pm": p_pm, "y": 0.0}
assert [e["skip"] for e in P.entries([ob(0.85), ob(0.851), ob(0.84), ob(0.95)])] == [True, False, True, False]
no_flags = [e["skip"] for e in P.entries([ob(0.12, "no"), ob(0.03, "no")])]
assert no_flags == [True, False], no_flags            # NO favourite at 94c: Polymarket "Up" 12c means NO at 88c, 6 points below; "Up" 3c means NO at 97c, above
assert P.entries([dict(ob(0.85), bid=0.40, ask=0.42)]) == [], "an entry outside the L1 band is not an L1 entry"

# Improvement: skipping the flagged losers helps; skipping random winners does not.
mk = lambda net, skip, s="KXBTC15M", day="d": {"series": s, "close_ts": 1, "day": day, "net": net, "skip": skip}
es = [mk(-0.9, True)] * 5 + [mk(0.05, False)] * 95
assert P.improvement(es, [e["skip"] for e in es]) > 0
assert P.improvement(es, [False] * 5 + [True] * 5 + [False] * 90) < P.improvement(es, [e["skip"] for e in es])

# Permutation null: flags the SAME number per series, and a flag set that is exactly the losers beats it.
two = [mk(-0.9, True, "KXBTC15M")] * 5 + [mk(0.05, False, "KXBTC15M")] * 45 + [mk(-0.9, True, "KXETH15M")] * 5 + [mk(0.05, False, "KXETH15M")] * 45
null = P.null_improvements(two, reps=50)
assert len(null) == 50 and max(null) < P.improvement(two, [e["skip"] for e in two])

# Verdicts.
def rows(n_days, per_day, skip_net, kept_net, skip_share=0.3):
    out = []
    for d in range(n_days):
        for i in range(per_day):
            skip = i < int(per_day * skip_share)
            out.append({"series": "KXBTC15M" if i % 2 else "KXETH15M", "close_ts": d, "day": f"2026-08-{d + 1:02d}", "net": (skip_net(d) if skip else kept_net(d)), "skip": skip})
    return out
assert P.verdict(rows(10, 5, lambda d: -0.5, lambda d: 0.05), [0.0])[0] == "NOT_ENOUGH_DATA"
good = rows(20, 20, lambda d: -0.4 if d % 2 else -0.1, lambda d: 0.03)
v, s = P.verdict(good, [0.001] * 20)
assert v == "NOT_YET_FALSIFIED" and s["z"] <= -P.Z_BAR and s["h1"] < 0 and s["h2"] < 0 and s["kept_mean"] > s["base"] and s["imp"] > s["p95"], (v, s)
good_imp = s["imp"]
# The improvement is exactly kept mean minus all-entries mean, and a random draw flags exactly the observed number per series.
assert abs(P.improvement(es, [e["skip"] for e in es]) - (0.05 - (5 * -0.9 + 95 * 0.05) / 100)) < 1e-12
import random
by = {"KXBTC15M": list(range(50)), "KXETH15M": list(range(50, 100))}
fl = P.random_flags(by, {"KXBTC15M": 5, "KXETH15M": 7}, 100, random.Random(1))
assert sum(fl[:50]) == 5 and sum(fl[50:]) == 7
# A skip that "helps" by less than the chance level is not a pass even when the null is negative: kept must beat the all-entries mean as well.
neg = P.verdict(good, [-5.0] * 20)
assert neg[0] == "NOT_YET_FALSIFIED" and neg[1]["imp"] > 0
worse = [dict(e, net=(-0.4 if e["skip"] else 0.03) * -1) for e in good]       # the skipped entries now WIN: skipping would have hurt
assert P.verdict(worse, [-5.0] * 20)[0] == "FALSIFIED"
# Skipping the better-looking group (skipped mean -0.1, kept mean -0.5) would have hurt even though the skipped mean is negative and the null is far below.
hurt = rows(20, 20, lambda d: -0.1 if d % 2 else -0.12, lambda d: -0.5, skip_share=0.7)
vh, sh = P.verdict(hurt, [-5.0] * 20)
assert sh["mean"] < 0 and sh["z"] <= -P.Z_BAR and sh["h1"] < 0 and sh["h2"] < 0 and sh["imp"] < 0 and sh["imp"] > sh["p95"] and vh == "FALSIFIED", (vh, sh)

# Each part bites alone.
v, s = P.verdict(good, [s["imp"] + 0.01] * 20); assert v == "FALSIFIED", "a chance subset that helps as much beats the claim"
v, s = P.verdict(rows(20, 20, lambda d: -1.0 if d < 10 else 0.1, lambda d: 0.03), [0.0] * 20); assert s["mean"] < 0 and s["z"] <= -P.Z_BAR and s["h2"] > 0 and v == "FALSIFIED", (v, s)
v, s = P.verdict(rows(20, 20, lambda d: 0.1 if d < 10 else -1.0, lambda d: 0.03), [0.0] * 20); assert s["mean"] < 0 and s["z"] <= -P.Z_BAR and s["h1"] > 0 and v == "FALSIFIED", (v, s)
v, s = P.verdict(rows(20, 20, lambda d: -0.6 if d % 2 else 0.5, lambda d: 0.03), [0.0] * 20); assert s["mean"] < 0 and s["z"] > -P.Z_BAR and s["h1"] < 0 and s["h2"] < 0 and v == "FALSIFIED", (v, s)
v, s = P.verdict(rows(20, 20, lambda d: 0.1, lambda d: 0.03), [0.0] * 20); assert v == "FALSIFIED" and s["mean"] > 0

code = "\n".join(l.split("#")[0] for l in Path(P.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("PM2 passed")
