"""Plain assert tests for the QUOTE2B scorer (src/scalper/quote2b.py) on a SYNTHETIC fixture only (no recorded
book or trade row is used); run with: python tests/test_quote2b.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import quote2b as Q

CLOSE = 1_800_000_000.0          # a top of the hour, in exchange seconds
B0 = CLOSE - 50 * 60             # first boundary


def poll(t, bid, ask, bsz=5.0, asz=3.0, depth=None):
    """A poll with YES bid `bid` (size bsz) and YES ask `ask` (NO bid 1-ask, size asz); `depth` adds levels."""
    yb, ybs, nb, nbs = [bid], [bsz], [round(1 - ask, 4)], [asz]
    for i, (db, da) in enumerate(depth or []):
        yb.append(round(bid - 0.01 * (i + 1), 4)); ybs.append(db)
        nb.append(round(1 - ask - 0.01 * (i + 1), 4)); nbs.append(da)
    return Q.Poll(t, yb, ybs, nb, nbs)


def steady(bid=0.50, ask=0.52, until=CLOSE, bsz=5.0, asz=3.0, depth=None):
    return [poll(B0 + i * 3, bid, ask, bsz, asz, depth) for i in range(int((until - B0) / 3))]


assert (Q.NEEDED, Q.SIZES, Q.TAKER, Q.Z_BAR, Q.MAX_ACTIVE, Q.FLAT_AT, Q.POST_FROM, Q.POST_TO) == (300, (1, 10), 0.07, 5.17, 3, 600, 3000, 900)
assert Q.READ_NOT_BEFORE == datetime(2026, 11, 12, tzinfo=timezone.utc).timestamp()

# 1. nothing trades and the quote never crosses: pairs are posted but nothing fills; P/L 0
h = Q.simulate_hour({1: (steady(), [])}, CLOSE)
assert h["pairs"] and all(p.fb == 0 and p.fs == 0 for p in h["pairs"]) and Q.hour_pnl(h, Q.TAKER) == 0
assert len(h["pairs"]) == 36, "one fresh pair per posting boundary T-50..T-15 while flat"

# 2. queue: 5 ahead on the bid; taker sells of 5 at our bid do not fill us; 5.5 fills half; a taker BUY at the bid price never counts
t = B0 + 10
for vol, want in ((5.0, 0.0), (5.5, 0.5), (6.0, 1.0)):
    h = Q.simulate_hour({1: (steady(), [(t, 0.50, vol, -1)])}, CLOSE)
    assert abs(h["pairs"][0].fb - want) < 1e-9, (vol, h["pairs"][0].fb)
h = Q.simulate_hour({1: (steady(), [(t, 0.50, 9, 1)])}, CLOSE)
assert h["pairs"][0].fb == 0
# trades before the order is live (posting poll + 1 s) do not count
h = Q.simulate_hour({1: (steady(), [(B0 + 0.5, 0.50, 50, -1)])}, CLOSE)
assert h["pairs"][0].fb == 0

# 3. the quote moving away (size ahead cancelled, price moved) is not a fill and does not move us up
moved = [poll(B0, 0.50, 0.52)] + [poll(B0 + 3 + i * 3, 0.48, 0.51, 1, 1) for i in range(1200)]
h = Q.simulate_hour({1: (moved, [(B0 + 20, 0.50, 1, -1)])}, CLOSE)
assert h["pairs"][0].fb == 0, "one contract at our bid after the 5 ahead were cancelled still does not reach us"
# ... but the ask running down THROUGH our bid is a fill at OUR price
thru = [poll(B0, 0.50, 0.52)] + [poll(B0 + 3 + i * 3, 0.40, 0.43, 1, 1) for i in range(1200)]
h = Q.simulate_hour({1: (thru, [])}, CLOSE)
p = h["pairs"][0]
assert p.fb == 1 and p.fills[0][3] == 0.50
# and a print strictly through our bid fills the remainder too
h = Q.simulate_hour({1: (steady(), [(t, 0.49, 1, -1)])}, CLOSE)
assert h["pairs"][0].fb == 1

# 4. a completed cycle earns the spread; the verdict fee is the taker formula rounded up per order
tr = [(t, 0.50, 6, -1), (t + 5, 0.52, 4, 1)]       # fills our buy (6 > 5 ahead) then our sell (4 > 3 ahead)
h = Q.simulate_hour({1: (steady(), tr)}, CLOSE)
p = h["pairs"][0]
assert p.fb == 1 and p.fs == 1 and p.end == "cycle"
assert abs(p.gross() - 0.02) < 1e-9 and abs(p.spread() - 0.02) < 1e-9
assert abs(p.fees(Q.TAKER) - 0.04) < 1e-9, "2c + 2c at 1 contract"
assert abs(Q.hour_pnl(h, Q.TAKER) + 0.02) < 1e-9 and abs(Q.hour_pnl(h, 0.0) - 0.02) < 1e-9
h10 = Q.simulate_hour({1: (steady(), [(t, 0.50, 15, -1), (t + 5, 0.52, 13, 1)])}, CLOSE, size=10)
p = h10["pairs"][0]
assert p.fb == 10 and p.fs == 10 and abs(p.fees(Q.TAKER) - 0.36) < 1e-9, "17.5c -> 18c, 17.47c -> 18c"

# 5. one-sided fill, no stop: the inventory is flattened at T-10 min by crossing, walking the book, taker fee
path = steady(until=CLOSE - 1200) + [poll(CLOSE - 1200 + i * 3, 0.47, 0.49, 0.4, 1, depth=[(0.3, 1), (5, 5)]) for i in range(400)]
h = Q.simulate_hour({1: (path, [(t, 0.50, 7, -1)])}, CLOSE, size=1)
p = h["pairs"][0]
assert p.end == "flatten" and p.fb == 1 and p.fs == 1
assert p.taker == [(0.47, 0.4, True), (0.46, 0.3, True), (0.45, 0.3, True)], p.taker
assert abs(p.gross() - (-0.50 + 0.47 * 0.4 + 0.46 * 0.3 + 0.45 * 0.3)) < 1e-9
assert p.spread() == 0 and p.gross() < 0
# while long, the sell stays resting at its ORIGINAL price (no chasing) and no new pair is posted on that strike
assert len(h["pairs"]) == 1

# 6. stop: mid 5c against a long -> cross at the NEXT poll; the strike quotes no more this hour
drop = steady(until=B0 + 30) + [poll(B0 + 30 + i * 3, 0.44, 0.46, 2, 2) for i in range(1000)]
h = Q.simulate_hour({1: (drop, [(t, 0.50, 7, -1)])}, CLOSE)
p = h["pairs"][0]
assert p.end == "stop" and len(h["pairs"]) == 1 and p.taker[0][0] == 0.44

# 7. at most 3 strikes active; nearest 0.50 first
st = {k: (steady(bid=b, ask=b + 0.02), []) for k, b in ((1, 0.30), (2, 0.45), (3, 0.49), (4, 0.55), (5, 0.70))}
h = Q.simulate_hour(st, CLOSE)
first = sorted(p.strike for p in h["pairs"] if abs(p.live - (B0 + 1)) < 1e-6)
assert first == [2, 3, 4], first
# mid outside 0.20..0.80 is never quoted
h = Q.simulate_hour({1: (steady(bid=0.85, ask=0.87), [])}, CLOSE)
assert not h["pairs"]

# 8. markouts are signed: + = our way
up = steady(until=B0 + 15) + [poll(B0 + 15 + i * 3, 0.53, 0.55) for i in range(1000)]
h = Q.simulate_hour({1: (up, [(B0 + 5, 0.50, 6, -1)])}, CLOSE)
m = Q.markouts(h, 30)
assert m and abs(m[0][0] - 0.04) < 1e-9

# 9. statistics and gates
rows = [(CLOSE + i * 3600, Q.simulate_hour({1: (steady(), [(t, 0.50, 6, -1), (t + 5, 0.52, 4, 1)])}, CLOSE)) for i in range(3)]
s = Q.summarise(rows, Q.TAKER)
assert s["n"] == 3 and s["pf"] == 0.0 and not Q.passes(s, Q.summarise(rows, Q.TAKER, 1.2))

# 10. refusals: before the read date, and below 300 closes
Q.RESULT = Path("/nonexistent/quote2b_result.txt")
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    Q.run(now=datetime(2026, 11, 11, 23, tzinfo=timezone.utc).timestamp())
assert "Refusing: the read date" in buf.getvalue()
Q.closes = lambda: {CLOSE + i * 3600: ("r", {"tickers": "7", "polls": "100", "ok_polls": "100", "first_ms": str(int((CLOSE + i * 3600 - 3300) * 1000)),
                                             "last_ms": str(int((CLOSE + i * 3600) * 1000))}) for i in range(299)}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    Q.run(now=datetime(2026, 11, 13, tzinfo=timezone.utc).timestamp())
assert "Refusing: 299 usable hourly closes" in buf.getvalue(), buf.getvalue()
assert Q.ready_date(299, CLOSE).timestamp() == max(Q.READ_NOT_BEFORE, CLOSE + 3600)

print("QUOTE2B synthetic tests: all passed")
