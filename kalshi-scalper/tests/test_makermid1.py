"""Plain assert tests for src/scalper/makermid1.py on a SYNTHETIC book and tape only; run: python tests/test_makermid1.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scalper import makermid1 as M
from scalper import makertail1 as T

C = 1_800_000_000.0


def poll(t, yb, ybs, nb, nbs):
    return T.Poll(t, [yb] if yb is not None else [], [ybs] if yb is not None else [], [nb] if nb is not None else [], [nbs] if nb is not None else [])


def look_polls(yb=0.30, ybs=10.0, nb=0.65, nbs=50.0):
    return [poll(C - T.LOOK_S - 6 + 3 * i, yb, ybs, nb, nbs) for i in range(6)]


# band: YES 30c in; the NO bid 65c is the favourite side and is never an order
o = M.make_orders("T", C, look_polls())
assert len(o) == 1 and o[0].side == "yes" and o[0].price == 0.30 and o[0].q0 == 10.0
assert abs(o[0].ask - 0.35) < 1e-9
assert T.BAND == (0.01, 0.15)                                  # makertail1's band is restored after the call
# edges: 16c and 40c in, 15c and 41c out; both sides in band gives two orders
assert len(M.make_orders("T", C, look_polls(0.16, 5, 0.40, 5))) == 2
assert M.make_orders("T", C, look_polls(0.15, 5, 0.41, 5)) == []
assert M.make_orders("T", C, look_polls(0.60, 5, 0.70, 5)) == []
# an ask above 40c is dropped from the taker column: YES bid 30c, NO bid 0.50 -> ask 0.50
x = M.make_orders("T", C, look_polls(0.30, 5, 0.50, 5))[0]
assert x.ask is None and M.taker_summary([x])["orders"] == 0
# fill times: queue 10, prints 6+4 do not fill, a third does; through-print fills at its time
x = M.make_orders("T", C, look_polls())[0]
t0 = x.look_t + 1
tr = [(t0 + 5, 0.30, 6, "no"), (t0 + 9, 0.30, 4, "no"), (t0 + 12, 0.30, 1, "no")]
assert M.fill_time(x, tr, "pess") == t0 + 12 and M.fill_time(x, tr, "opt") == t0 + 5 and M.fill_time(x, tr[:2], "pess") is None
assert M.fill_time(x, [(t0 + 7, 0.29, 1, "no")], "pess") == t0 + 7
assert M.fill_time(x, [(t0 + 5, 0.30, 99, "yes"), (C - 30, 0.30, 99, "no")], "opt") is None
# NO order: bid 30c on NO is yes price 0.70
n = M.make_orders("T", C, look_polls(0.55, 5, 0.30, 4.0))[0]
assert n.side == "no" and n.price == 0.30
assert M.fill_time(n, [(n.look_t + 5, 0.70, 5, "yes")], "pess") == n.look_t + 5 and M.fill_time(n, [(n.look_t + 5, 0.70, 4, "yes")], "pess") is None
# MR2 guard: bid falls to 28c (2c drop) at a poll after live -> cancel there; falls to 29c -> no cancel; empty side -> cancel
base = look_polls()
x = M.make_orders("T", C, base + [poll(t0 + 20, 0.28, 10, 0.65, 50)])[0]
assert x.cancel_t == t0 + 20
assert M.make_orders("T", C, base + [poll(t0 + 20, 0.29, 10, 0.65, 50)])[0].cancel_t is None
assert M.make_orders("T", C, base + [poll(t0 + 20, None, 0, 0.65, 50)])[0].cancel_t == t0 + 20
# a poll at or before the live time does not cancel
assert M.cancel_time(x, [poll(x.look_t + 1, 0.10, 1, 0.9, 1)]) is None
# guarded fill: fill at t0+12 is before the cancel at t0+20 (kept); a fill at t0+25 is after (dropped); no cancel keeps every fill
x.won, x.gap = True, False
M.score_fills(x, [(t0 + 5, 0.29, 1, "no")])
assert x.fill["pess"] and x.fill["pess_g"]
M.score_fills(x, [(t0 + 25, 0.29, 1, "no")])
assert x.fill["pess"] and not x.fill["pess_g"] and not x.fill["opt_g"]
v = M.guard_view([x])[0]
assert v.fill["pess"] is False and x.fill["pess"] is True        # the view is a copy; the original is unchanged
# summaries use makertail1's arithmetic: win at 30c nets +70c, a loss -30c
def mk(price, won, fill):
    y = T.Order("T", C, "yes", price, 5.0, C - T.LOOK_S, price + 0.02, 20.0)
    y.won, y.gap, y.fill = won, False, {"pess": fill, "opt": fill, "mid": fill, "pess_g": False, "opt_g": fill, "mid_g": False}
    return y
os_ = [mk(0.30, True, True), mk(0.30, False, True), mk(0.30, False, False)]
s = T.summarise(os_, "pess")
assert abs(s["per_order"] - (70 - 30) / 3) < 1e-9 and s["fills"] == 2
assert T.summarise(M.guard_view(os_), "pess")["fills"] == 0
assert T.summarise(M.guard_view(os_), "opt")["fills"] == 2
# buckets only show 16c to 40c
assert [b.split(":")[0].strip() for b in M.buckets(os_, "pess")] == ["bid 16-25c", "bid 26-33c", "bid 34-40c"]
print("ok")
