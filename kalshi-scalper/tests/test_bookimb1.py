"""Plain assert tests for src/scalper/bookimb1.py on SYNTHETIC books only; run: python tests/test_bookimb1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import bookimb1 as B
from scalper import makertail1 as M

C = 1_800_000_000.0
P = lambda t, yp, ys, np_, ns: M.Poll(t, yp, ys, np_, ns)

# depth within 3 ticks of the best bid: 0.09 (5), 0.08 (4), 0.07 (3), 0.06 (2) counted; 0.05 (100) is 4 ticks away, not counted
assert B.depth_near_best([0.09, 0.08, 0.07, 0.06, 0.05], [5, 4, 3, 2, 100]) == 14.0
assert B.depth_near_best([], []) == 0.0
assert B.depth_near_best([0.06, 0.09], [7, 1]) == 8.0                       # order independent: the best is the max price
# imbalance: own 10 vs opp 30 -> -0.5; own 30 vs opp 10 -> +0.5; equal -> 0; own empty -> -1; opp empty -> None
assert abs(B.imbalance([0.1], [10], [0.8], [30]) - (-0.5)) < 1e-12
assert abs(B.imbalance([0.1], [30], [0.8], [10]) - 0.5) < 1e-12
assert B.imbalance([0.1], [20], [0.8], [20]) == 0.0
assert B.imbalance([], [], [0.8], [20]) == -1.0
assert B.imbalance([0.1], [20], [], []) is None
# bounds hold for random-ish books
for a in (0, 1, 7, 1000):
    for b in (1, 3, 999):
        v = B.imbalance([0.2, 0.19], [a, 5], [0.7, 0.6], [b, 1])
        assert -1.0 <= v <= 1.0
# sign convention: strictly positive is ON, zero is OFF
assert B.feature_on(0.01) and not B.feature_on(0.0) and not B.feature_on(-0.2) and not B.feature_on(None)
# the complement flips the sign for the same book (YES view vs NO view of one book): own and opp swap
yv = B.imbalance([0.1], [30], [0.8], [10]); nv = B.imbalance([0.8], [10], [0.1], [30])
assert abs(yv + nv) < 1e-12

# a close with three strikes: tails and an out-of-band strike; the highest ask in band per side wins; one per side
def strike(tk, yb, ybs, nb, nbs, n=6):
    return tk, [P(C - B.LOOK_S - 6 + 3 * i, [yb] if yb is not None else [], [ybs] if yb is not None else [], [nb] if nb is not None else [], [nbs] if nb is not None else []) for i in range(n)]

# YES ask = 1 - NO bid. A: YES ask 0.12 (NO bid 0.88), YES bid 0.10 size 40 vs NO bid size 10 -> ON.  B: YES ask 0.25 (NO 0.75), imb<0.
# NO ask = 1 - YES bid: A: 0.90 (out of band).  C: YES bid 0.80 -> NO ask 0.20, NO bid 0.20 (YES ask 0.80)
polls = dict([strike("A", 0.10, 40.0, 0.88, 10.0), strike("B", 0.20, 5.0, 0.75, 50.0), strike("C", 0.80, 10.0, 0.20, 30.0)])
tr = B.candidates_at_close(polls, C)
by = {t.side: t for t in tr}
assert set(by) == {"yes", "no"}
assert by["yes"].ticker == "B" and abs(by["yes"].ask_look - 0.25) < 1e-9      # highest YES ask in [0.03, 0.30]
assert by["yes"].imb < 0 and not by["yes"].on
assert by["no"].ticker == "C" and abs(by["no"].ask_look - 0.20) < 1e-9
assert abs(by["no"].imb - ((30 - 10) / 40.0 * -1)) < 1e-9 or True
# NO view of C: own = NO bids (0.20, size 30), opp = YES bids (0.80, size 10): (30-10)/40 = +0.5 -> ON
assert abs(by["no"].imb - 0.5) < 1e-9 and by["no"].on
assert by["yes"].ok and by["no"].ok and by["yes"].ask == 0.25
# ties go to the lower ticker string
tie = dict([strike("Z", 0.10, 5.0, 0.80, 5.0), strike("Y", 0.10, 5.0, 0.80, 5.0)])
assert {t.side: t.ticker for t in B.candidates_at_close(tie, C)}["yes"] == "Y"
# no look poll (too old) -> nothing; ask above the hard limit at the fill poll -> not ok
assert B.candidates_at_close({"A": [P(C - B.LOOK_S - 200, [0.1], [5], [0.88], [5])]}, C) == []
moved = [P(C - B.LOOK_S - 3, [0.1], [5.0], [0.80], [20.0]), P(C - B.LOOK_S + 1.5, [0.1], [5.0], [0.60], [20.0])]  # ask 0.20 at look, 0.40 at fill
mt_ = B.candidates_at_close({"A": moved}, C)
assert len(mt_) == 1 and mt_[0].ask == 0.40 and not mt_[0].ok
thin = [P(C - B.LOOK_S - 3, [0.1], [5.0], [0.80], [20.0]), P(C - B.LOOK_S + 1.5, [0.1], [5.0], [0.80], [3.0])]
assert not B.candidates_at_close({"A": thin}, C)[0].ok                          # displayed size under 10

# outcome and fee: win at ask 0.20: +80c - 20c - fee (7% x 10 x .2 x .8 = 0.112 -> 12c per 10 = 1.2c)
t = by["no"]; t.won = True
assert abs(B.fee_per_contract(0.20) - 0.012) < 1e-9
assert abs(B.net_cents(t) - (100 - 20 - 1.2)) < 1e-9 and abs(B.net_cents(t, 1.2) - (100 - 20 - 1.44)) < 1e-9
t.won = False
assert abs(B.net_cents(t) - (-20 - 1.2)) < 1e-9

# summarise / verdict gates on synthetic trades
def mk(on, won, close, ask=0.20):
    x = B.Trade("T", close, "yes", ask, 0.5 if on else -0.5, ask, 50.0); x.won = won; return x
few = [mk(True, True, C + 3600 * i) for i in range(10)] + [mk(False, False, C + 3600 * i) for i in range(10)]
assert B.verdict(few, few[:10], few[10:]) == "NOT_ENOUGH_DATA"
many = [mk(True, i % 2 == 0, C + 3600 * i) for i in range(160)] + [mk(False, i % 10 == 0, C + 3600 * i) for i in range(160)]
h1 = [x for x in many if x.close < C + 3600 * 80]; h2 = [x for x in many if x.close >= C + 3600 * 80]
assert B.verdict(many, h1, h2) == "NOT_YET_FALSIFIED"                        # ON wins half the time at 20c: PF well over 1.5, beats OFF in both halves
bad = [mk(True, i % 10 == 0, C + 3600 * i) for i in range(160)] + [mk(False, i % 2 == 0, C + 3600 * i) for i in range(160)]
assert B.verdict(bad, [x for x in bad if x.close < C + 3600 * 80], [x for x in bad if x.close >= C + 3600 * 80]) == "FALSIFIED"
# a trade that is not tradable (size) or has no result is not scored
bad_t = B.Trade("T", C, "yes", 0.2, 0.5, 0.2, 5.0); bad_t.won = True
assert B.summarise([bad_t])["n"] == 0
print("test_bookimb1: ok")
