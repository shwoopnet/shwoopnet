"""Plain assert tests for E5 (src/scalper/e5.py); run with: python tests/test_e5.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import altseries as A
from scalper import e5 as E
from scalper.scalps import fee, STRESS

# The eight registered series, no more; the split is E3's cut; its own file.
assert E.SERIES == ("KXSILVER15M", "KXWTI15M", "KXNATGAS15M", "KXCOPPER15M", "KXPLATINUM15M", "KXPALLADIUM15M", "KXZEC15M", "KXNEAR15M") and len(set(E.SERIES)) == 8
assert E.SPLIT_TS == 1_788_465_600 and A.ALT_DB.name == "alts3.sqlite" and E.DAYS == 69
# fetch() points the shared fetcher at these series.
seen = {}
orig = A.fetch
A.fetch = lambda days: seen.update(series=A.ALTS, days=days)
try:
    E.fetch()
finally:
    A.fetch = orig
assert seen == {"series": E.SERIES, "days": 69}

# Split: on or after the cut is discovery, before is holdout, nothing is in both.
mk = lambda c: {"close_ts": c}
d, h = E.split([mk(E.SPLIT_TS - 1), mk(E.SPLIT_TS), mk(E.SPLIT_TS + 5)])
assert [e["close_ts"] for e in d] == [E.SPLIT_TS, E.SPLIT_TS + 5] and [e["close_ts"] for e in h] == [E.SPLIT_TS - 1]

# A window of entries: net per entry from the day, price fixed; nets chosen to give or deny each part of the bar.
def window(n_days, per, net_of, start=0):
    out = []
    for d_ in range(n_days):
        for i in range(per):
            n = net_of(d_)
            out.append({"day": f"2026-09-{d_ + 1:02d}", "close_ts": start + d_ * 86400 + i, "net": n, "stress": n - 0.002, "gross": n + 0.93 + fee(0.93) - 0.93 + 0.0, "price": 0.93})
    return out

good = lambda start: window(12, 30, lambda d_: 0.03 if d_ % 2 else 0.01, start)
bad = lambda start: window(12, 30, lambda d_: -0.02, start)
few = lambda start: window(12, 10, lambda d_: 0.03 if d_ % 2 else 0.01, start)

# Too little data in discovery is not a verdict.
assert E.series_verdict(few(0), good(0))[0] == "NOT_ENOUGH_DATA" and E.series_verdict([], [])[0] == "NOT_ENOUGH_DATA"
# Plenty of entries on too few days (4 days, 500 entries) is not a verdict either.
assert E.series_verdict(window(4, 125, lambda d_: 0.03 if d_ % 2 else 0.01), good(0))[0] == "NOT_ENOUGH_DATA"
# Failing Stage 1 is FALSIFIED and the holdout is NOT read (stage2 stays None) however good it looks.
v, d = E.series_verdict(bad(0), good(0))
assert v == "FALSIFIED" and d["stage2"] is None
# Passing Stage 1 and the holdout: NOT_YET_FALSIFIED.
v, d = E.series_verdict(good(0), good(0))
assert v == "NOT_YET_FALSIFIED" and d["stage1"] == "NOT_YET_FALSIFIED" and d["stage2"] == "NOT_YET_FALSIFIED", (v, d)
# Passing Stage 1 and failing the holdout: FALSIFIED. Passing Stage 1 with a holdout too small to read: NOT_ENOUGH_DATA, not a pass.
v, d = E.series_verdict(good(0), bad(0)); assert v == "FALSIFIED" and d["stage2"] == "FALSIFIED"
v, d = E.series_verdict(good(0), few(0)); assert v == "NOT_ENOUGH_DATA" and d["stage2"] == "NOT_ENOUGH_DATA"

code = "\n".join(l.split("#")[0] for l in Path(E.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("E5 passed")
