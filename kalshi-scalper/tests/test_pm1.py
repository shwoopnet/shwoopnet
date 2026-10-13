"""Plain assert tests for PM1 (src/scalper/pm1.py); run with: python tests/test_pm1.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import pm1 as P

# Registered: Bitcoin and Ethereum only, a 50/50 blend, the 180 s freshness rule, its own file, the read-only public API.
assert P.ASSETS == {"KXBTC15M": "btc", "KXETH15M": "eth"} and P.BLEND == 0.5 and P.MAX_AGE_S == 180 and P.ENTRY_LEFT_S == 360 and P.PM_DB.name == "pm1.sqlite"
assert P.MIN_OBS == 500 and P.MIN_DAYS == 10 and P.Z_BAR == 2.1 and P.AUDIT_GAIN == 0.002 and P.DISAGREE == 0.05
# Polymarket names a window by its START, which is the Kalshi close minus 900 seconds.
assert P.slug("btc", 1_791_850_500) == "btc-updown-15m-1791849600"

# A price AFTER the entry second is never read (that would be the outcome leaking in); one older than 180 s is stale; the latest eligible point wins.
cut = 10_000
assert P.last_point([(cut + 1, 0.9)], cut) is None
assert P.last_point([(cut - 181, 0.9)], cut) is None
assert P.last_point([(cut - 180, 0.9)], cut) == 0.9
assert P.last_point([(cut - 120, 0.4), (cut - 30, 0.6), (cut + 5, 0.99)], cut) == 0.6
assert P.last_point([], cut) is None

# The paired difference: when Polymarket is right where Kalshi is wrong the blend wins (positive); when Polymarket is more wrong, it loses (negative); equal prices give zero.
assert P.paired_d(0.5, 0.9, 1.0) > 0 and P.paired_d(0.9, 0.5, 1.0) < 0 and P.paired_d(0.7, 0.7, 1.0) == 0.0
assert abs(P.paired_d(0.6, 0.8, 1.0) - ((0.4) ** 2 - (0.3) ** 2)) < 1e-12

# Observations: a window with no recent Polymarket point has none; the outcome comes from Kalshi's result.
C = 1_791_850_500
w = {"ticker": "T", "series": "KXBTC15M", "close_ts": C, "yes": True, "bid": 0.89, "ask": 0.91}
s = P.slug("btc", C)
o = P.observations([w], {s: [(C - 360 - 60, 0.80)]})
assert len(o) == 1 and abs(o[0]["p_k"] - 0.90) < 1e-12 and o[0]["p_pm"] == 0.80 and o[0]["y"] == 1.0
assert P.observations([w], {}) == [] and P.observations([w], {s: [(C - 360 + 1, 0.8)]}) == [] and P.observations([w], {s: [(C - 360 - 400, 0.8)]}) == []
assert P.observations([dict(w, yes=False)], {s: [(C - 360, 0.8)]})[0]["y"] == 0.0

# Verdicts.
def rows(day_d, n_days=12, per=50):
    return [{"day": f"2026-09-{d + 1:02d}", "d": day_d(d)} for d in range(n_days) for _ in range(per)]
assert P.verdict(rows(lambda d: 0.01, per=10))[0] == "NOT_ENOUGH_DATA" and P.verdict(rows(lambda d: 0.01, n_days=5, per=200))[0] == "NOT_ENOUGH_DATA"
v, s = P.verdict(rows(lambda d: 0.002 if d % 2 else 0.001)); assert v == "NOT_YET_FALSIFIED" and s["z"] >= P.Z_BAR and not s["audit"], (v, s)
v, s = P.verdict(rows(lambda d: 0.01 if d % 2 else 0.004)); assert v == "NOT_YET_FALSIFIED" and s["audit"], "a gain over 0.002 triggers the audit note"
v, s = P.verdict(rows(lambda d: 0.01 if d < 6 else -0.001)); assert s["h1"] > 0 > s["h2"] and s["z"] >= P.Z_BAR and v == "FALSIFIED", (v, s)
v, s = P.verdict(rows(lambda d: -0.001 if d < 6 else 0.01)); assert s["h2"] > 0 > s["h1"] and s["z"] >= P.Z_BAR and v == "FALSIFIED", (v, s)
v, s = P.verdict(rows(lambda d: 0.03 if d % 2 else -0.01)); assert s["mean"] > 0 and s["z"] < P.Z_BAR and s["h1"] > 0 and s["h2"] > 0 and v == "FALSIFIED", (v, s)
assert P.verdict(rows(lambda d: -0.01))[0] == "FALSIFIED"

# Disagreement split: Polymarket 5 points or more BELOW Kalshi for the side bought is "disagrees"; for a NO entry the sides flip.
base = {"bid": 0.89, "ask": 0.91, "p_k": 0.90, "y": 1.0}
g = P.disagreement_split([dict(base, p_pm=0.84), dict(base, p_pm=0.86), dict(base, p_pm=0.95)])
assert len(g["disagrees"]) == 1 and len(g["agrees"]) == 2
no = {"bid": 0.05, "ask": 0.07, "p_k": 0.06, "y": 0.0}          # a NO favourite: Kalshi's YES mid 6c, so NO is 94c; Polymarket "Up" 12c means NO is 88c, 6 points below
g = P.disagreement_split([dict(no, p_pm=0.12), dict(no, p_pm=0.03)])
assert len(g["disagrees"]) == 1 and len(g["agrees"]) == 1

code = "\n".join(l.split("#")[0] for l in Path(P.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("PM1 passed")
