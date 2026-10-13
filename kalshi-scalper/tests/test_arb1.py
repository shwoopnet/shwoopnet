"""Plain assert tests for ARB1 (src/scalper/arb1.py); run with: python tests/test_arb1.py. Each states a consequence, not a mechanism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import arb1 as A

assert A.ARB_DB.name == "arb1.sqlite" and A.MIN_LOCK == 0.01 and A.MIN_CAPACITY == 10.0 and A.SIZE_CAP == 50.0 and A.PERSIST_S == 900 and A.MIN_EVENTS == 3 and A.MIN_PER_DAY == 1.0 and A.MIN_SCANS == 8


def ev(bids, sizes=None, exclusive=True, status="active", name="E"):
    sizes = sizes or [100.0] * len(bids)
    return {"event_ticker": name, "series_ticker": "S", "mutually_exclusive": exclusive,
            "markets": [{"status": status, "yes_bid_dollars": f"{b:.4f}", "yes_bid_size_fp": f"{z:.2f}"} for b, z in zip(bids, sizes)]}


# Only events marked mutually exclusive are ever read: for any other event a sum of bids over 1 is not an arithmetic fact.
assert A.event_row(ev([0.6, 0.6], exclusive=False)) is None
# A locked set: two legs bid 60c each, fees on both, so the lock is 1.20 - 1 - 2 fee(0.6).
r = A.event_row(ev([0.6, 0.6]))
assert abs(r["lock"] - (0.2 - 2 * 0.07 * 0.6 * 0.4)) < 1e-12 and abs(r["sum_bid"] - 1.2) < 1e-12 and r["legs"] == 2 and A.is_opportunity(r)
# The fee is subtracted, not ignored: bids summing to 1.02 across two legs leave a NEGATIVE lock.
r2 = A.event_row(ev([0.51, 0.51]))
assert r2["lock"] < 0 and not A.is_opportunity(r2), r2
# Legs with no bid are not bought: they are left out of the set, never counted at zero or made to fail the event.
r3 = A.event_row(ev([0.6, 0.6, 0.0]))
assert r3["legs"] == 2 and abs(r3["sum_bid"] - 1.2) < 1e-12
# One usable leg is not a set; a closed leg is not usable; bids are at most 99c.
assert A.event_row(ev([0.9, 0.0])) is None and A.event_row(ev([0.6, 0.6], status="closed")) is None
# A leg already bid at $1.00 is settled, not a quote: it is left out, not counted as a lock.
assert A.event_row(ev([1.0, 0.6])) is None and A.event_row(ev([1.0, 0.6, 0.6]))["legs"] == 2
# Capacity is the smallest leg size: the set can only be as big as its thinnest leg. Under 10 contracts it is not an opportunity.
r4 = A.event_row(ev([0.6, 0.6], sizes=[500.0, 9.0]))
assert r4["capacity"] == 9.0 and not A.is_opportunity(r4)
assert A.is_opportunity(A.event_row(ev([0.6, 0.6], sizes=[500.0, 10.0])))
# Cent rounding of the fee can only cost more, never less, than the unrounded model.
assert all(A.fee_rounded(p, c) >= A.fee(p) - 1e-12 for p in (0.05, 0.3, 0.6, 0.95) for c in (1, 10, 50))
assert r["lock_rounded"] <= r["lock"] + 1e-12

# Persistence: an opportunity in one scan only, or in two scans under 15 minutes apart, is a flicker and does not count.
def sc(ts, *rows): return {"ts": ts, "rows": [A.event_row(ev(b, name=n, sizes=[100.0] * len(b))) for n, b in rows]}
opp = ("X", [0.6, 0.6])
assert A.persistent([sc(0, opp), sc(899, opp)]) == {} and A.persistent([sc(0, opp)]) == {}
p = A.persistent([sc(0, opp), sc(900, opp)])
assert list(p) == ["X"] and abs(p["X"] - A.event_row(ev([0.6, 0.6]))["lock"] * 50.0) < 1e-9, "value is lock x min(capacity, 50) in the first opportunity scan"
# The value is taken in the FIRST opportunity scan, not a later, bigger one.
big = {"ts": 1000, "rows": [A.event_row(ev([0.6, 0.6], name="X", sizes=[500.0, 500.0]))]}
first = sc(0, opp)
assert abs(A.persistent([first, big])["X"] - A.event_row(ev([0.6, 0.6]))["lock"] * 50.0) < 1e-9
small = {"ts": 0, "rows": [A.event_row(ev([0.6, 0.6], name="X", sizes=[10.0, 10.0]))]}
assert abs(A.persistent([small, sc(1000, opp)])["X"] - A.event_row(ev([0.6, 0.6]))["lock"] * 10.0) < 1e-9
# An event that is an opportunity in scan 1 and again in scan 3 but not in scan 2 still counts (two scans at least 15 minutes apart).
assert "X" in A.persistent([sc(0, opp), sc(1000, ("X", [0.4, 0.4])), sc(2000, opp)])

# Verdicts. Fewer than 8 scans is not a verdict.
def scans(n, evs, gap=1200, size=100.0):
    return [{"ts": i * gap, "rows": [A.event_row(ev(b, name=nm, sizes=[size] * len(b))) for nm, b in evs]} for i in range(n)]
assert A.verdict(scans(7, [("X", [0.6, 0.6])]))[0] == "NOT_ENOUGH_DATA"
three = [("A", [0.6, 0.6]), ("B", [0.6, 0.6]), ("C", [0.6, 0.6])]
v, s = A.verdict(scans(12, three))
assert v == "NOT_YET_FALSIFIED" and s["persistent"] == 3 and s["per_day"] >= 1.0, (v, s)
# Two persistent events are not three.
assert A.verdict(scans(12, three[:2]))[0] == "FALSIFIED"
# Three persistent events worth too little per day fail the money bar: a 1.5c lock on 10 sets is 15c an event, and over a 22 hour span that is well under $1 a day.
tiny = [(n, [0.525, 0.525]) for n in "ABC"]
v, s = A.verdict(scans(12, tiny, gap=7200, size=10.0))
assert s["persistent"] == 3 and s["per_day"] < 1.0 and v == "FALSIFIED", (v, s)
assert A.verdict(scans(12, tiny, gap=1200, size=10.0))[0] == "NOT_YET_FALSIFIED", "the same events over the short registered span clear the generous scale-up"
# No opportunities at all.
assert A.verdict(scans(12, [("A", [0.3, 0.3])]))[0] == "FALSIFIED"

code = "\n".join(l.split("#")[0] for l in Path(A.__file__).read_text().splitlines())
assert "promote" not in code.lower()
print("ARB1 passed")
