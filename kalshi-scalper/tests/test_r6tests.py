"""Plain assert tests for the MAKER5 and L1Q1 scorer (src/scalper/r6tests.py) on a SYNTHETIC fixture only (no recorded
R6 row is used); run with: python tests/test_r6tests.py."""
import contextlib
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import r6tests as R
from scalper.quote2b import Poll

CLOSE = 1_800_000_000.0           # a quarter hour, exchange seconds
OPEN = CLOSE - 900


def poll(t, bid, ask, bsz=5.0, asz=3.0, depth=None):
    """YES bid `bid` (size bsz), YES ask `ask` (NO bid 1-ask, size asz); `depth` adds levels a cent apart."""
    yb, ybs, nb, nbs = [bid], [bsz], [round(1 - ask, 4)], [asz]
    for i, (db, da) in enumerate(depth or []):
        yb.append(round(bid - 0.01 * (i + 1), 4)); ybs.append(db)
        nb.append(round(1 - ask - 0.01 * (i + 1), 4)); nbs.append(da)
    return Poll(t, yb, ybs, nb, nbs)


def path(segs):
    """segs: [(until_t, bid, ask, bsz, asz)]; one poll every 2 s from OPEN."""
    out, t = [], OPEN
    for until, b, a, bs, as_ in segs:
        while t < until:
            out.append(poll(t, b, a, bs, as_))
            t += 2
    return out


assert (R.NEEDED, R.SIZES, R.TAKER, R.MAKER, R.Z_BAR) == (300, (1, 10), 0.07, 0.0175, 5.17)
assert (R.M5_POST, R.M5_FLAT, R.M5_FLAT_LATE, R.M5_STOP, R.Q_SIGNAL, R.Q_EXPIRE) == (720, 420, 402, 0.05, 360, 120)
assert R.READ_NOT_BEFORE == datetime(2026, 11, 6, tzinfo=timezone.utc).timestamp()
assert sum(R.TRIES.values()) == 18

# ---------------- MAKER5
P0 = CLOSE - 720                  # the posting poll (OPEN + 180 is on the 2 s grid)
flat = path([(CLOSE, 0.50, 0.52, 5, 3)])

# 1. no trades: one pair, never re-posted, nothing fills, P/L 0
pr = R.simulate_maker5(flat, [], CLOSE)
assert pr is not None and pr.b == 0.50 and pr.a == 0.52 and pr.fb == 0 and pr.fs == 0 and pr.end == "none"
assert R.maker5_pnl(pr, R.TAKER) == 0
# mid outside 0.20..0.80, or no NO bid, posts nothing
assert R.simulate_maker5(path([(CLOSE, 0.85, 0.87, 5, 3)]), [], CLOSE) is None
assert R.simulate_maker5([Poll(t, [0.5], [5], [], []) for t in range(int(OPEN), int(CLOSE), 2)], [], CLOSE) is None

# 2. queue: 5 ahead; 5 sold at our bid does not fill, 5.5 fills half; a taker BUY at our bid never counts; before live never counts
t = P0 + 10
for vol, want in ((5.0, 0.0), (5.5, 0.5), (6.0, 1.0)):
    assert abs(R.simulate_maker5(flat, [(t, 0.50, vol, -1)], CLOSE).fb - want) < 1e-9
assert R.simulate_maker5(flat, [(t, 0.50, 9, 1)], CLOSE).fb == 0
assert R.simulate_maker5(flat, [(P0 + 0.5, 0.50, 50, -1)], CLOSE).fb == 0

# 3. cancels never move us forward; the ask running THROUGH our bid fills at OUR price
moved = path([(P0 + 2, 0.50, 0.52, 5, 3), (CLOSE, 0.49, 0.51, 1, 1)])
assert R.simulate_maker5(moved, [(P0 + 20, 0.50, 1, -1)], CLOSE).fb == 0
thru = path([(P0 + 2, 0.50, 0.52, 5, 3), (CLOSE, 0.47, 0.49, 1, 1)])
pr = R.simulate_maker5(thru, [], CLOSE)
assert pr.fills and pr.fills[0][3] == 0.50

# 4. completed cycle: spread 2c, verdict fee 2c + 2c at C = 1 -> -2c; zero maker fee +2c
pr = R.simulate_maker5(flat, [(t, 0.50, 6, -1), (t + 5, 0.52, 4, 1)], CLOSE)
assert pr.end == "cycle" and abs(pr.spread() - 0.02) < 1e-9
assert abs(R.maker5_pnl(pr, R.TAKER) + 0.02) < 1e-9 and abs(R.maker5_pnl(pr, 0.0) - 0.02) < 1e-9
assert abs(R.maker5_pnl(pr, R.TAKER, 1.2) - (0.02 - 1.2 * 0.04)) < 1e-9
# no re-pricing: after the cycle, further trades at the old prices fill nothing more
pr = R.simulate_maker5(flat, [(t, 0.50, 6, -1), (t + 5, 0.52, 4, 1), (t + 9, 0.50, 99, -1)], CLOSE)
assert pr.fb == 1 and pr.fs == 1

# 5. one-sided fill, no stop: flattened at the first poll at or after T-7 min, walking the book; nothing after T-7 counts
fl = path([(CLOSE - 600, 0.50, 0.52, 5, 3), (CLOSE, 0.47, 0.49, 0.4, 1)])
fl = [poll(p.t, p.bid, p.ask, p.ybs[0], p.nbs[0], depth=[(0.3, 1), (5, 5)]) if p.t >= CLOSE - 600 else p for p in fl]
pr = R.simulate_maker5(fl, [(t, 0.50, 7, -1), (CLOSE - 300, 0.52, 50, 1)], CLOSE)
assert pr.end == "flatten" and pr.fb == 1 and pr.fs == 1
assert pr.taker == [(0.47, 0.4, True), (0.46, 0.3, True), (0.45, 0.3, True)], pr.taker
assert pr.gross() < 0 and pr.spread() == 0
assert all(t_ <= CLOSE - R.M5_FLAT for t_, *_ in pr.fills), "flat before L1's 6.7 minute look"
# no poll between T-7 and T-6.7: worst case (a long sells at 0)
gap = [p for p in fl if not (CLOSE - 420 <= p.t <= CLOSE - 380)]
pr = R.simulate_maker5(gap, [(t, 0.50, 7, -1)], CLOSE)
assert pr.taker == [(0.0, 1, True)]

# 6. stop: mid 5c against a long -> cross at the NEXT poll
drop = path([(P0 + 30, 0.50, 0.52, 5, 3), (CLOSE, 0.44, 0.46, 2, 2)])
pr = R.simulate_maker5(drop, [(P0 + 10, 0.50, 7, -1)], CLOSE)
assert pr.end == "stop" and pr.taker[0][0] == 0.44
# C = 10 needs 10 more past the queue; fee rounded per order at 10
pr = R.simulate_maker5(flat, [(t, 0.50, 15, -1), (t + 5, 0.52, 13, 1)], CLOSE, size=10)
assert pr.fb == 10 and pr.fs == 10 and abs(pr.fees(R.TAKER) - 0.36) < 1e-9

# 7. markouts are signed: + = our way
up = path([(P0 + 20, 0.50, 0.52, 5, 3), (CLOSE, 0.53, 0.55, 5, 3)])
pr = R.simulate_maker5(up, [(P0 + 5, 0.50, 6, -1)], CLOSE)
m = R.maker5_markouts(pr, up, 30)
assert m and abs(m[0][0] - 0.04) < 1e-9

# ---------------- L1Q1
S_T = CLOSE - 360
fav = path([(CLOSE, 0.90, 0.92, 20, 4)])          # YES ask 0.92 in band; bid 0.90 with 20 ahead

# 8. signal side and plain L1
w = R.simulate_l1q1(fav, [], CLOSE, "yes")
assert w["side"] == "yes" and w["win"] and w["b"] == 0.90 and w["plain"] == [(0.92, 1)] and w["filled"] == 0
assert abs(R.l1q1_pnl(w, "plain", R.TAKER) - (1 - 0.92 - 0.01)) < 1e-9
assert R.l1q1_pnl(w, "a", R.TAKER) == 0
# variant b crosses at T-120 s if still in band
assert w["cross"] == [(0.92, 1)] and abs(R.l1q1_pnl(w, "b", R.TAKER) - (0.08 - 0.01)) < 1e-9
# NO side: YES bid 0.05 -> NO ask 0.95 in band; YES ask 0.07 -> no YES signal
nofav = path([(CLOSE, 0.05, 0.07, 3, 30)])
w = R.simulate_l1q1(nofav, [], CLOSE, "yes")
assert w["side"] == "no" and not w["win"] and abs(w["b"] - 0.93) < 1e-9 and abs(w["plain"][0][0] - 0.95) < 1e-9
assert abs(R.l1q1_pnl(w, "plain", R.TAKER) - (-0.95 - 0.01)) < 1e-9
# a NO fill comes from takers BUYING YES at 1 - our NO bid beyond the queue (30 NO contracts ahead)
w = R.simulate_l1q1(nofav, [(S_T + 5, 0.07, 30, 1)], CLOSE, "no")
assert w["filled"] == 0
w = R.simulate_l1q1(nofav, [(S_T + 5, 0.07, 31, 1)], CLOSE, "no")
assert w["filled"] == 1 and w["win"] and abs(R.l1q1_pnl(w, "a", R.TAKER) - (1 - 0.93 - 0.01)) < 1e-9
# no signal: neither in band
assert R.simulate_l1q1(path([(CLOSE, 0.50, 0.52, 5, 5)]), [], CLOSE, "yes") is None

# 9. queue for the resting bid; nothing after T-120 s fills it; cancels do not advance it
assert R.simulate_l1q1(fav, [(S_T + 5, 0.90, 20, -1)], CLOSE, "yes")["filled"] == 0
assert R.simulate_l1q1(fav, [(S_T + 5, 0.90, 21, -1)], CLOSE, "yes")["filled"] == 1
assert R.simulate_l1q1(fav, [(CLOSE - 100, 0.90, 99, -1)], CLOSE, "yes")["filled"] == 0
assert R.simulate_l1q1(fav, [(S_T + 0.5, 0.90, 99, -1)], CLOSE, "yes")["filled"] == 0, "before live"
thin = path([(S_T + 2, 0.90, 0.92, 20, 4), (CLOSE, 0.90, 0.92, 1, 4)])
assert R.simulate_l1q1(thin, [(S_T + 9, 0.90, 2, -1)], CLOSE, "yes")["filled"] == 0
# a print through our bid fills at OUR price; partial at C = 10
w = R.simulate_l1q1(fav, [(S_T + 5, 0.89, 1, -1)], CLOSE, "yes")
assert w["filled"] == 1 and w["b"] == 0.90
w = R.simulate_l1q1(fav, [(S_T + 5, 0.90, 24, -1)], CLOSE, "no", size=10)
assert abs(w["filled"] - 4) < 1e-9 and sum(q for _, q in w["cross"]) == 6
# the dip that fills us, then out of band at T-120: variant b does not cross
dip = path([(S_T + 10, 0.90, 0.92, 20, 4), (CLOSE, 0.80, 0.83, 5, 5)])
w = R.simulate_l1q1(dip, [], CLOSE, "no")
assert w["filled"] == 1 and w["cross"] == [] and abs(R.l1q1_pnl(w, "a", R.TAKER) - (-0.90 - 0.01)) < 1e-9

# 10. statistics, gates and refusals
rows = [(CLOSE + 900 * i, "KXGOLD15M", -0.02) for i in range(3)]
s = R.stats(rows)
assert s["n"] == 3 and s["pf"] == 0.0 and not R.bar(s, s)
R.RESULTS = {"maker5": Path("/nonexistent/maker5_result.txt"), "l1q1": Path("/nonexistent/l1q1_result.txt")}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    R.run("maker5", now=datetime(2026, 11, 5, 23, tzinfo=timezone.utc).timestamp())
assert "Refusing: the read date" in buf.getvalue()
row = lambda c: {"ticker": "X", "series": "KXBTC15M", "polls": "450", "ok_polls": "440", "max_gap_ms": "4000", "tape_pages": "3",
                 "note": "", "first_recv_ms": str(int((c - 899) * 1000)), "last_recv_ms": str(int((c - 1) * 1000)), "result": "yes"}
R.windows = lambda: {(CLOSE + 900 * i, "KXBTC15M"): ("r", row(CLOSE + 900 * i)) for i in range(299)}
for card in ("maker5", "l1q1"):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        R.run(card, now=datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp())
    assert "Refusing: 299 usable windows" in buf.getvalue(), buf.getvalue()
# usability is coverage only: a truncated tape, a late start or a missing result is not usable
assert R.usable("maker5", CLOSE, row(CLOSE)) and R.usable("l1q1", CLOSE, row(CLOSE))
assert not R.usable("maker5", CLOSE, dict(row(CLOSE), note="tape incomplete (HTTP 500)"))
assert not R.usable("maker5", CLOSE, dict(row(CLOSE), first_recv_ms=str(int((CLOSE - 600) * 1000))))
assert R.usable("l1q1", CLOSE, dict(row(CLOSE), first_recv_ms=str(int((CLOSE - 600) * 1000))))
assert not R.usable("l1q1", CLOSE, dict(row(CLOSE), result=""))

print("R6T (MAKER5, L1Q1) synthetic tests: all passed")
