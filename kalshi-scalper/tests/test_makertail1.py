"""Plain assert tests for src/scalper/makertail1.py on a SYNTHETIC book and tape only; run: python tests/test_makertail1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import makertail1 as M

C = 1_800_000_000.0


def poll(t, yb, ybs, nb, nbs):
    return M.Poll(t, [yb] if yb is not None else [], [ybs] if yb is not None else [], [nb] if nb is not None else [], [nbs] if nb is not None else [])


def look_polls(yb=0.08, ybs=10.0, nb=0.88, nbs=50.0):
    return [poll(C - M.LOOK_S - 6 + 3 * i, yb, ybs, nb, nbs) for i in range(6)]


# orders: only the YES side (bid 8c) is in the 1c to 15c band; the NO bid 88c is not
os_ = M.make_orders("T", C, look_polls())
assert len(os_) == 1 and os_[0].side == "yes" and os_[0].price == 0.08 and os_[0].q0 == 10.0
assert abs(os_[0].ask - 0.12) < 1e-9 and os_[0].ask_size == 50.0          # ask = 1 - NO bid
# both sides in band -> two orders; out of band (16c) -> none; no look poll -> none
assert len(M.make_orders("T", C, look_polls(0.05, 5, 0.10, 5))) == 2
assert M.make_orders("T", C, look_polls(0.16, 5, 0.50, 5)) == []
assert M.make_orders("T", C, [poll(C - M.LOOK_S - 200, 0.08, 5, 0.5, 5)]) == []

o = os_[0]
t0 = o.look_t + 1
tr = lambda dt, yp, c, s: (t0 + dt, yp, c, s)
# queue ahead 10: prints of 6 + 4 at 0.08 are not enough (needs strictly more than 10); a third print fills
assert not M.filled(o, [tr(5, 0.08, 6, "no"), tr(9, 0.08, 4, "no")], "pess")
assert M.filled(o, [tr(5, 0.08, 6, "no"), tr(9, 0.08, 4, "no"), tr(12, 0.08, 1, "no")], "pess")
# optimistic: the first print at the price fills; the middle bound (ahead 5) needs more than 5
assert M.filled(o, [tr(5, 0.08, 1, "no")], "opt") and not M.filled(o, [tr(5, 0.08, 1, "no")], "mid")
assert M.filled(o, [tr(5, 0.08, 5.5, "no")], "mid")
# a print through the price (0.07) fills even the pessimistic order
assert M.filled(o, [tr(5, 0.07, 1, "no")], "pess")
# wrong taker side, a higher price, before the order is live, after the cancel: no fill
assert not M.filled(o, [tr(5, 0.08, 99, "yes"), tr(5, 0.09, 99, "no"), (t0 - 0.5, 0.08, 99, "no"), (C - 30, 0.08, 99, "no")], "opt")
# NO order: bid 8c on NO is a YES price of 0.92; a taker "yes" at 0.92 hits it, at 0.93 goes through
no = M.make_orders("T", C, look_polls(0.50, 5, 0.08, 4.0))[0]
assert no.side == "no" and no.price == 0.08
n0 = no.look_t + 1
assert not M.filled(no, [(n0 + 5, 0.92, 3, "yes")], "pess") and M.filled(no, [(n0 + 5, 0.92, 2, "yes")], "pess") is False
assert M.filled(no, [(n0 + 5, 0.92, 3, "yes"), (n0 + 6, 0.92, 2, "yes")], "pess")
assert M.filled(no, [(n0 + 5, 0.93, 0.1, "yes")], "pess")
# tape gap: a hole over 90 s inside the order's life marks it; pess and mid then count it as not filled
o.gap = M.tape_gap(o, [t0 + i * 30 for i in range(0, 5)])
assert o.gap
assert not M.filled(o, [tr(5, 0.07, 1, "no")], "pess") and M.filled(o, [tr(5, 0.07, 1, "no")], "opt")
assert not M.tape_gap(o, [o.look_t + 1 + 30 * i for i in range(0, 50)])
# fees and summaries
assert abs(M.taker_fee_per_contract(0.10) - 0.007) < 1e-9 and abs(M.taker_fee_per_contract(0.12) - 0.008) < 1e-9


def mk(price, won, fill, close=C, gap=False):
    x = M.Order("T", close, "yes", price, 5.0, close - M.LOOK_S, price + 0.02, 20.0)
    x.won, x.gap, x.fill = won, gap, {"pess": fill, "opt": fill, "mid": fill}
    return x


orders = [mk(0.10, True, True), mk(0.10, False, True), mk(0.10, False, False), mk(0.10, False, True, gap=True)]
s = M.summarise(orders, "pess")
assert s["orders"] == 4 and s["fills"] == 3 and abs(s["fill_rate"] - 0.75) < 1e-9
assert abs(s["per_fill"] - (90 - 10 - 10) / 3) < 1e-9 and abs(s["per_order"] - (90 - 10 - 10 + 0) / 4) < 1e-9
assert abs(s["pf"] - 90 / 20) < 1e-9
assert M.summarise(orders, "opt")["orders"] == 3          # a tape-gap order is excluded from the optimistic bound
t = M.taker_summary([mk(0.10, True, True)])
assert abs(t["per_order"] - (100 * (1 - 0.12 - 0.008))) < 1e-6
assert M.taker_summary([mk(0.10, True, True)], 1.2)["per_order"] < t["per_order"]
# verdict words
many = [mk(0.10, False, True) for _ in range(160)]
assert M.verdict(M.summarise(orders, "pess"), s, s) == "NOT_ENOUGH_DATA"
assert M.verdict(M.summarise(many, "pess"), M.summarise(many, "pess"), M.summarise(many, "pess")) == "FALSIFIED"
good = [mk(0.10, True, True) for _ in range(40)] + [mk(0.10, False, True) for _ in range(120)]
g = M.summarise(good, "pess")
assert g["per_order"] > 0 and g["pf"] >= 1.5 and M.verdict(g, g, g) == "NOT_YET_FALSIFIED"
assert M.verdict(g, g, M.summarise(many, "pess")) == "FALSIFIED"
print("ok")
