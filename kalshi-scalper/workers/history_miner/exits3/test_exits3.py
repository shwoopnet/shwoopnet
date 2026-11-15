"""Invented windows for exits3.py: the hand case of EXITS3_HAND_CASE_NOV15.md. Run: python3 -I test_exits3.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exits3 as X

CL = 10_000
A = lambda x, y: abs(x - y) < 1e-12


def q(bid, ask, oi=None):
    return (bid, ask, 1.0, oi)


# E1: YES e 0.20; mark -60 bid 0.45
c1 = {CL - 120: q(0.18, 0.20), CL - 60: q(0.45, 0.47)}
k, b = X.exit_mark(c1, CL - 120, CL, "yes", 0.20, "T")
assert k == CL - 60 and b == 0.45
assert A(X.net(0.20, 0.0, b, "yes", "yes"), 0.220) and A(X.net(0.20, 0.01, b, "yes", "yes"), 0.200)
assert X.exit_mark(c1, CL - 120, CL, "yes", 0.20, "S") == (None, "held") and A(X.net(0.20, 0.0, None, "yes", "yes"), 0.788)
assert X.exit_mark(c1, CL - 120, CL, "yes", 0.20, "M") == (None, "M n/a, held")
# E2: NO e 0.30 (yes_bid 0.70); mark -60 yes_ask 0.90 -> NO bid 0.10
c2 = {CL - 120: q(0.70, 0.72), CL - 60: q(0.88, 0.90)}
k, b = X.exit_mark(c2, CL - 120, CL, "no", 0.30, "S")
assert k == CL - 60 and A(b, 0.10) and A(X.net(0.30, 0.0, b, "yes", "no"), -0.222)
assert X.exit_mark(c2, CL - 120, CL, "no", 0.30, "T")[0] is None and A(X.net(0.30, 0.0, None, "yes", "no"), -0.315)
# E3: all held, result no
c3 = {CL - 120: q(0.28, 0.30), CL - 60: q(0.40, 0.42)}
for v in ("T", "S", "M", "hold"):
    assert X.exit_mark(c3, CL - 120, CL, "yes", 0.30, v)[0] is None
assert A(X.net(0.30, 0.0, None, "no", "yes"), -0.315)
# E4: S triggered at a 0.00 bid, never sold
c4 = {CL - 120: q(0.38, 0.40), CL - 60: q(0.0, 0.05)}
assert X.exit_mark(c4, CL - 120, CL, "yes", 0.40, "S") == (None, "triggered, not sold") and A(X.net(0.40, 0.0, None, "yes", "yes"), 0.583)
# E5: entry at -600
c5 = {CL - 600: q(0.48, 0.50), CL - 540: q(0.52, 0.54), CL - 180: q(0.61, 0.63), CL - 60: q(0.95, 0.97)}
kT, bT = X.exit_mark(c5, CL - 600, CL, "yes", 0.50, "T"); kM, bM = X.exit_mark(c5, CL - 600, CL, "yes", 0.50, "M")
assert kT == CL - 60 and kM == CL - 180 and X.exit_mark(c5, CL - 600, CL, "yes", 0.50, "S")[0] is None
assert A(X.net(0.50, 0.0, bT, "yes", "yes"), 0.428) and A(X.net(0.50, 0.0, bM, "yes", "yes"), 0.075)
# E6: void
assert A(X.net(0.30, 0.0, None, "void", "yes"), -0.015)
print("engine: ok")


def win(level, sig, side_ask_sig=0.20, fill=0.22, fill_missing=False, both_out=False):
    s = q(0.40, 0.55, sig) if both_out else q(0.18, side_ask_sig, sig)
    c = {CL - 360: q(0.75, 0.77, level), CL - 180: s}
    if not fill_missing:
        c[CL - 120] = q(0.20, fill, sig)
    return c


for lv, sg, core, rel in ((300000, 400000, True, True), (400000, 490000, True, False), (200000, 280000, False, True)):
    assert bool(X.ENTRY["OICORE"](win(lv, sg), CL)) == core and bool(X.ENTRY["OIREL"](win(lv, sg), CL)) == rel, (lv, sg)
r = X.ENTRY["OICORE"](win(300000, 400000), CL)
assert r == {"side": "yes", "e": 0.22, "entry_end": CL - 120}, r
assert not X.ENTRY["OICORE"](win(300000, 400000, both_out=True), CL) and not X.ENTRY["OIREL"](win(300000, 400000, both_out=True), CL)
assert not X.ENTRY["OICORE"](win(300000, 400000, fill_missing=True), CL) and not X.ENTRY["OIREL"](win(300000, 400000, fill_missing=True), CL)
one = win(300000, 400000); one[CL - 180] = q(0.0, 0.20, 400000)
assert X.ENTRY["OICORE"](one, CL) == "not two-sided"
one = win(300000, 400000); one[CL - 120] = q(0.22, 0.22, 400000)
assert X.ENTRY["OIREL"](one, CL) == "not two-sided"
print("entries: ok")

s = X.summary([{"net": v, "day": "d%d" % i} for i, v in enumerate((0.2, -0.1, 0.3, -0.3))])
assert A(s["pf"], 1.25) and A(s["pf_half1"], 2.0) and A(s["pf_half2"], 1.0), s
print("summary: ok")
