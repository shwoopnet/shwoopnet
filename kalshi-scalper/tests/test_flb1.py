"""Plain assert tests for FLB1 (src/scalper/flb1.py); run with: python tests/test_flb1.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import flb1 as F
from scalper.scalps import STRESS, fee

assert F.LEADS_H == (24, 72, 168) and F.BAND == (0.88, 0.97) and F.EXCLUDED_CATEGORIES == ("Sports", "Financials", "Crypto") and F.FLB_DB.name == "flb1.sqlite"
assert F.MIN_ENTRIES == 300 and F.MIN_EVENTS == 60 and F.Z_BAR == 2.1 and F.MIN_LIFETIME_S == 3 * 86400 and F.DAYS == 60

# The entry hour is never later than the lead before the close: an entry after that would use information the rule does not allow.
H, C = 3600, 1_790_000_000 + 1234
for lead in F.LEADS_H:
    e = F.entry_end(C, lead)
    assert e <= C - lead * H and e % H == 0 and C - lead * H - e < H
assert F.entry_end(1_790_000_000 - 1_790_000_000 % H + 72 * H, 72) == 1_790_000_000 - 1_790_000_000 % H, "exactly on a boundary the candle ending then is used"

# Eligibility uses category, lifetime and result only: sports, financials and crypto are out; a 2 day market is out; an unresolved market is out. Price never enters.
D = 86400
assert F.eligible("Politics", 0, 3 * D, "yes") and F.eligible("Mentions", 0, 10 * D, "no")
assert not F.eligible("Sports", 0, 10 * D, "yes") and not F.eligible("Financials", 0, 10 * D, "yes") and not F.eligible("Crypto", 0, 10 * D, "yes")
assert not F.eligible("Politics", 0, 3 * D - 1, "yes") and not F.eligible("Politics", 0, 10 * D, "") and not F.eligible("Politics", None, 10 * D, "yes") and not F.eligible("Politics", 0, None, "yes")

# Entry choice: YES at its ask, NO at 1 minus the YES bid, both in the band; a bad quote or a price out of the band is never taken. The loss costs the price plus fee.
s, p, mid, net, stress = F.take_entry(0.90, 0.92, "yes")
assert s == "yes" and p == 0.92 and abs(mid - 0.91) < 1e-12 and abs(net - (1 - 0.92 - fee(0.92))) < 1e-12 and stress < net
s, p, mid, net, _ = F.take_entry(0.05, 0.07, "no")
assert s == "no" and abs(p - 0.95) < 1e-12 and abs(mid - 0.94) < 1e-12 and abs(net - (1 - 0.95 - fee(0.95))) < 1e-12
assert F.take_entry(0.05, 0.07, "yes")[3] < -0.9, "a NO favourite that loses costs its price"
assert F.take_entry(0.40, 0.42, "yes") is None and F.take_entry(0.0, 0.92, "yes") is None and F.take_entry(0.98, 0.99, "yes") is None and F.take_entry(0.93, 0.92, "yes") is None

# Chunking: at most 100 per request and a 48 h span; nothing lost.
ms = [{"ticker": f"T{i}", "close_ts": 1_800_000_000 + i * 60} for i in range(250)]
assert [len(c) for c in F.chunk_markets(ms)] == [100, 100, 50]
sp = [{"ticker": f"S{i}", "close_ts": 1_800_000_000 + i * 3600} for i in range(100)]
assert all(c[-1]["close_ts"] - c[0]["close_ts"] <= F.MAX_SPAN_S for c in F.chunk_markets(sp)) and sum(len(c) for c in F.chunk_markets(sp)) == 100

# Simulation: only the candle at exactly the entry hour counts (never a neighbour); the lead is part of the key.
m = {"ticker": "A", "event": "E1", "category": "Politics", "close_ts": C, "result": "yes"}
e24 = F.entry_end(C, 24)
out = F.simulate([m], {("A", 24): (e24, 0.90, 0.92, 5.0)}, 24)
assert len(out) == 1 and out[0]["won"] == 1.0 and out[0]["event"] == "E1"
assert F.simulate([m], {("A", 24): (e24 - H, 0.90, 0.92, 5.0)}, 24) == [] and F.simulate([m], {("A", 24): (e24, 0.90, 0.92, 5.0)}, 72) == []
assert F.simulate([dict(m, result="no")], {("A", 24): (e24, 0.90, 0.92, 5.0)}, 24)[0]["won"] == 0.0

# Verdicts. The cluster is the EVENT: many markets of one event are one bet. Too few events is not a verdict.
def mk(n_events, per, net_of, price=0.92):
    return [{"event": f"E{i}", "close_ts": i, "net": net_of(i), "stress": net_of(i) - 0.002, "price": price, "mid": price - 0.01, "won": 1.0} for i in range(n_events) for _ in range(per)]
assert F.verdict(mk(40, 10, lambda i: 0.02), [-0.05])[0] == "NOT_ENOUGH_DATA" and F.verdict(mk(100, 2, lambda i: 0.02), [-0.05])[0] == "NOT_ENOUGH_DATA"
v, s = F.verdict(mk(100, 5, lambda i: 0.02 if i % 2 else 0.002), [-0.05]); assert v == "NOT_YET_FALSIFIED" and s["z"] >= F.Z_BAR and s["mean"] > 0 and not s["audit"], (v, s)
v, s2 = F.verdict(mk(100, 5, lambda i: 0.02 if i % 2 else 0.002), [s["mean"] + 0.01]); assert v == "FALSIFIED", "a placebo that does as well beats the claim"
v, s = F.verdict(mk(100, 5, lambda i: 0.09 if i % 2 else 0.01), [-0.05]); assert s["audit"] and v == "NOT_YET_FALSIFIED"
v, s = F.verdict(mk(100, 5, lambda i: 0.06 if i < 50 else -0.01), [-0.05]); assert s["h1"] > 0 > s["h2"] and s["z"] >= F.Z_BAR and v == "FALSIFIED", (v, s)
v, s = F.verdict(mk(100, 5, lambda i: -0.01 if i < 50 else 0.06), [-0.05]); assert s["h2"] > 0 > s["h1"] and s["z"] >= F.Z_BAR and v == "FALSIFIED", (v, s)
rows = [dict(r, stress=r["net"] - 0.1) for r in mk(100, 5, lambda i: 0.02 if i % 2 else 0.002)]
v, s = F.verdict(rows, [-0.05]); assert s["stress"] < 0 < s["mean"] and s["z"] >= F.Z_BAR and v == "FALSIFIED", (v, s)
v, s = F.verdict(mk(100, 5, lambda i: 0.4 if i % 2 else -0.3), [-0.05]); assert s["mean"] > 0 and s["z"] < F.Z_BAR and s["h1"] > 0 and s["h2"] > 0 and v == "FALSIFIED", (v, s)
# Clustering by event, not by row: 5 identical rows per event leave a bigger standard error than 5x the events would.
a = F.verdict(mk(100, 5, lambda i: 0.05 if i % 2 else -0.03), [-0.05])[1]["mde"]
b = F.verdict(mk(500, 1, lambda i: 0.05 if i % 2 else -0.03), [-0.05])[1]["mde"]
assert a > b * 1.5, (a, b)

code = "\n".join(l.split("#")[0] for l in Path(F.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("FLB1 passed")
