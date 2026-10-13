"""Plain assert tests for GROWTH2 (src/scalper/growth2.py); run with: python tests/test_growth2.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import growth2 as G2

assert G2.LIVE == ("KXBTC15M", "KXGOLD15M", "KXETH15M") and G2.APPENDED == ("KXXRP15M", "KXDOGE15M")
mk = lambda s, n: {"series": s, "net": n}
es = [mk("KXXRP15M", 0.02), mk("KXXRP15M", 0.04), mk("KXDOGE15M", 0.00), mk("KXBTC15M", 0.01)]
# Shifting sets the appended series' mean to the target and leaves every other series, and the input list, untouched.
out = G2.shift_series(es, G2.APPENDED, 0.005)
assert abs(sum(e["net"] for e in out if e["series"] in G2.APPENDED) / 3 - 0.005) < 1e-12 and out[3]["net"] == 0.01 and es[0]["net"] == 0.02
# None leaves the measured numbers.
assert [e["net"] for e in G2.shift_series(es, G2.APPENDED, None)] == [e["net"] for e in es]
# Appended series must come AFTER the live three in the window order, or they would displace the live trades.
from scalper import growth as G
G.SERIES_ORDER = {"KXBTC15M": 0, "KXGOLD15M": 1, "KXETH15M": 2, "KXXRP15M": 3, "KXDOGE15M": 4}
day = [{"series": s, "close_ts": 1, "day": "d", "price": 0.92, "net": 0.0} for s in ("KXDOGE15M", "KXXRP15M", "KXETH15M", "KXBTC15M", "KXGOLD15M")]
assert [x["series"] for x in G.by_day(day)[0][0]] == ["KXBTC15M", "KXGOLD15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"]
code = "\n".join(l.split("#")[0] for l in Path(G2.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("GROWTH2 passed")
