"""Plain assert tests for VOL1 (src/scalper/vol1.py); run with: python tests/test_vol1.py. Each states a consequence, not a mechanism."""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import fwd1
from scalper import vol1 as V

# Registered: Bitcoin and Ethereum, the README's thresholds, FWD1's data file, the single forward read.
assert V.SERIES == ("KXBTC15M", "KXETH15M") and V.THRESHOLDS == {"KXBTC15M": 132_766.0, "KXETH15M": 5_751.0} and A.ALT_DB.name == "fwd1.sqlite"
assert V.MIN_SKIPPED == 150 and V.MIN_DAYS == 10
# Strictly above the threshold is skipped; at it is kept; an unknown volume is kept.
assert V.is_skipped("KXBTC15M", 132_766.1) and not V.is_skipped("KXBTC15M", 132_766.0) and V.is_skipped("KXETH15M", 6_000) and not V.is_skipped("KXETH15M", 5_751) and not V.is_skipped("KXBTC15M", None)

# Only forward Bitcoin and Ethereum entries are read, each flagged by ITS OWN entry candle's volume.
S = fwd1.START_TS
raw = [{"series": "KXBTC15M", "ticker": "A", "close_ts": S + 900, "day": "d1", "net": 0.01}, {"series": "KXETH15M", "ticker": "B", "close_ts": S + 1800, "day": "d1", "net": -0.9},
       {"series": "KXGOLD15M", "ticker": "C", "close_ts": S + 900, "day": "d1", "net": 0.01}, {"series": "KXBTC15M", "ticker": "D", "close_ts": S - 5, "day": "d0", "net": 0.01}]
vol = {("A", S + 900 - 360): 200_000.0, ("B", S + 1800 - 360): 1_000.0, ("D", S - 5 - 360): 999_999.0}
es = V.entries(raw, vol)
assert [(e["series"], e["skip"]) for e in es] == [("KXBTC15M", True), ("KXETH15M", False)], "gold and days before the start never count"

# The single read is refused before the registered date.
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    V.run(now_ts=fwd1.EARLIEST_READ_TS - 1)
assert "Too early" in buf.getvalue()

# Verdicts.
def rows(n_days, per_day, skip_net, kept_net, skip_share=1 / 3):
    out = []
    for d in range(n_days):
        for i in range(per_day):
            skip = i < int(per_day * skip_share)
            out.append({"series": "KXBTC15M" if i % 2 else "KXETH15M", "close_ts": d, "day": f"2026-11-{d + 1:02d}", "net": (skip_net(d) if skip else kept_net(d)), "skip": skip})
    return out
assert V.verdict(rows(20, 6, lambda d: -0.3, lambda d: 0.05), [0.0])[0] == "NOT_ENOUGH_DATA"                      # 40 skipped
assert V.verdict(rows(8, 60, lambda d: -0.3, lambda d: 0.05), [0.0])[0] == "NOT_ENOUGH_DATA"                       # 8 days
good = rows(20, 30, lambda d: -0.2 if d % 2 else -0.05, lambda d: 0.03)
v, s = V.verdict(good, [0.001] * 20)
assert v == "NOT_YET_FALSIFIED" and s["skipped_mean"] < 0 < s["kept_mean"] and s["imp"] > s["p95"], (v, s)
# Each part bites alone.
assert V.verdict(good, [s["imp"] + 0.01] * 20)[0] == "FALSIFIED", "a chance subset that helps as much beats the claim"
v, s2 = V.verdict(rows(20, 30, lambda d: 0.02, lambda d: 0.05), [-5.0] * 20); assert s2["skipped_mean"] > 0 and s2["skipped_mean"] < s2["kept_mean"] and v == "FALSIFIED", (v, s2)
v, s2 = V.verdict(rows(20, 30, lambda d: -0.3 if d < 10 else 0.10, lambda d: 0.03 if d < 10 else 0.0), [-5.0] * 20); assert s2["skipped_mean"] < 0 and s2["gaps"][1][0] > s2["gaps"][1][1] and v == "FALSIFIED", (v, s2)
v, s2 = V.verdict(rows(20, 30, lambda d: 0.10 if d < 10 else -0.5, lambda d: 0.0 if d < 10 else 0.03), [-5.0] * 20); assert s2["skipped_mean"] < 0 and s2["gaps"][0][0] > s2["gaps"][0][1] and v == "FALSIFIED", (v, s2)
v, s2 = V.verdict(rows(20, 30, lambda d: -0.3, lambda d: -0.5), [-5.0] * 20); assert s2["skipped_mean"] < 0 and s2["skipped_mean"] > s2["kept_mean"] and v == "FALSIFIED", (v, s2)

code = "\n".join(l.split("#")[0] for l in Path(V.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("VOL1 passed")
