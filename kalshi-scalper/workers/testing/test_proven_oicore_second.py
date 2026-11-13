"""Test for proven_oicore_second.py: INVENTED rows only (PROVEN_OICORE_HAND_CASE.md). Run: python3 -B -W ignore test_proven_oicore_second.py"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proven_oicore_second as p

def mk(i, wins, side=None, **kw):
    """One invented OICORE row: count 10, fee .02, side price .20 for either side; win pays 10."""
    side = side or ("yes" if i % 2 == 0 else "no")
    res = side if wins else ("no" if side == "yes" else "yes")
    row = {"ts": "2026-11-13T00:%02d:%02dZ" % (i // 60, i % 60) if i < 3600 else "2026-11-13T%02d:%02d:00Z" % (i // 3600, (i % 3600) // 60), "strategy": "OICORE", "ticker": "KXBTC15M-T%d" % i, "side": side, "count": 10,
           "avgFill": 0.20 if side == "yes" else 0.80, "avgFee": 0.02, "status": "settled", "result": res, "settledPnl": 7.8 if wins else -2.2}
    row.update(kw); return row
def window(start, n, w):          # n rows from index `start`, w of them wins (the first w)
    return [mk(start + j, j < w) for j in range(n)]
A = window(0, 100, 30) + window(100, 100, 25) + window(200, 100, 28)
o = p.read_rows(A)
assert o["rows_used"] == 300 and o["excluded"] == {} and [w["n"] for w in o["windows"]] == [100, 100, 100]
exp = [234 / 154, 195 / 165, 218.4 / 158.4]
for w, e in zip(o["windows"], exp): assert abs(w["cash_pf_unrounded"] - e) < 1e-9, (w, e)
assert abs(exp[0] - 1.5195) < 5e-5 and abs(exp[1] - 1.1818) < 5e-5 and abs(exp[2] - 1.3788) < 5e-5
assert [w["counts"] for w in o["windows"]] == [True, False, True] and o["windows_counting"] == 2 and o["VERDICT"] == "PROVEN" and all("n" in w and "cash_pf_unrounded" in w for w in o["windows"])
assert abs(o["windows"][0]["net"] - (30 * 7.8 - 70 * 2.2)) < 1e-9 and abs(o["windows"][0]["win_rate"] - 0.3) < 1e-12
# Set B: window 3 at 25 wins -> one of three -> NOT YET
B = window(0, 100, 30) + window(100, 100, 25) + window(200, 100, 25)
assert p.read_rows(B)["VERDICT"] == "NOT YET" and p.read_rows(B)["windows_counting"] == 1
# Set C: 299 rows, windows 99, 100, 100 (Head 19:22Z: no per-window n minimum): the 99-row window at PF 1.5415 COUNTS, so 2 of 3 and PROVEN
C = window(0, 99, 30) + window(99, 100, 30) + window(199, 100, 25)
oc = p.read_rows(C)
assert [w["n"] for w in oc["windows"]] == [99, 100, 100] and abs(oc["windows"][0]["cash_pf_unrounded"] - 234 / 151.8) < 1e-9 and [w["counts"] for w in oc["windows"]] == [True, True, False] and oc["VERDICT"] == "PROVEN" and oc["windows_counting"] == 2
# total n under 100 is NOT_ENOUGH_DATA whatever the windows show; 100 in all is read
nine = [mk(i, True) for i in range(99)]; on = p.read_rows(nine)
assert on["VERDICT"] == "NOT_ENOUGH_DATA" and [w["n"] for w in on["windows"]] == [33, 33, 33] and all(w["cash_pf_unrounded"] == float("inf") for w in on["windows"]) and on["rows_used"] == 99
assert p.read_rows([mk(i, True) for i in range(100)])["VERDICT"] == "PROVEN" and p.read_rows([mk(i, i % 5 == 0) for i in range(100)])["VERDICT"] in ("PROVEN", "NOT YET")
# NOT YET is only with total n >= 100: 100 rows, 20 wins each window-ish: PF 7.8 x 20 / (2.2 x 80) = 0.886 in every window
ny = p.read_rows([mk(i, i % 5 == 0) for i in range(100)]); assert ny["VERDICT"] == "NOT YET" and ny["windows_counting"] == 0 and ny["rows_used"] == 100
# a small window counts when its PF is 1.3 or better (no per-window minimum)
assert p.window_ok([1.0] * 5 + [-0.5] * 2) and abs(p.pf_of([1.0] * 5 + [-0.5] * 2) - 5.0) < 1e-12
# Set D: the same rows in REVERSED input order give the same windows (the reader sorts by ts)
assert p.read_rows(list(reversed(A)))["windows"] == o["windows"] and p.read_rows(list(reversed(A)))["VERDICT"] == "PROVEN"
# ties in ts keep input order (stable): two rows with one ts, wins first
tie = [mk(0, True, ts="T"), mk(1, False, ts="T")]
near = lambda xs, ys: all(abs(x - y) < 1e-9 for x, y in zip(xs, ys)) and len(xs) == len(ys)
assert near([x[1] for x in p.select(tie)[0]], [7.8, -2.2]) and near([x[1] for x in p.select(list(reversed(tie)))[0]], [-2.2, 7.8])
# exclusions, each counted in its own bucket, none changes a figure
extra = [mk(900, True, settledPnl=None), mk(901, True, count=0), mk(902, True, strategy="L2X"), mk(903, True, result="exit"), mk(904, True, avgFill=1.2), mk(905, True, avgFee=1.5), mk(906, True, avgFill=None)]
oe = p.read_rows(A + extra)
assert oe["rows_given"] == 307 and oe["rows_used"] == 300 and oe["windows"] == o["windows"] and oe["excluded"] == {"not settled": 1, "not filled": 1, "other strategy": 1, "exit (exitProceeds not in the row)": 1, "avgFill unreadable": 2, "avgFee unreadable": 1}, oe["excluded"]
assert oe["excluded_unreadable_fill_or_fee"] == 3 and oe["excluded_exit"] == 1 and o["excluded_unreadable_fill_or_fee"] == 0 and o["excluded_exit"] == 0          # always printed, zero included
# void: price refunded, fee kept: -(0.02 x 10) = -0.20
assert abs(p.cash_result(mk(0, True, result="void"))[0] + 0.20) < 1e-12
# the cash basis itself: YES win +7.8, NO win +7.8 (side price 1 - .80), YES loss -2.2, NO loss -2.2; settledPnl is not used for the figure
assert abs(p.cash_result(mk(0, True, side="yes"))[0] - 7.8) < 1e-12 and abs(p.cash_result(mk(0, True, side="no"))[0] - 7.8) < 1e-12
assert abs(p.cash_result(mk(0, False, side="yes"))[0] + 2.2) < 1e-12 and abs(p.cash_result(mk(0, False, side="no"))[0] + 2.2) < 1e-12
assert abs(p.cash_result(mk(0, True, settledPnl=12345.0))[0] - 7.8) < 1e-12
# a NO order read with the YES price as if it were its own would differ: avgFill .80 on a NO side costs .20, not .80
assert abs(p.cash_result(mk(0, True, side="no", avgFill=0.60, avgFee=0.0))[0] - (10 - 4.0)) < 1e-12          # cost (1 - .60 + 0) x 10 = 4
# bar boundary: exactly 1.3 counts (inside 1e-9), 1.2999 does not, n 99 does not, no-loss window is infinity and counts at n >= 100
assert p.window_ok([1.3] * 65 + [-1.0] * 65)
assert not hasattr(p, "MIN_N") or p.MIN_N == 100          # MIN_N is now the TOTAL n of the verdict, not a per-window minimum
assert p.MIN_TOTAL == 100 and not hasattr(p, "MIN_N")
assert abs(p.pf_of([1.3] * 65 + [-1.0] * 65) - 1.3) < 1e-9
assert not p.window_ok([1.2999] * 65 + [-1.0] * 65) and not p.window_ok([1.3] * 49 + [-1.0] * 50) and p.window_ok([1.0] * 100) and not p.window_ok([]) and not p.window_ok([-1.0]) and p.pf_of([1.0] * 100) == float("inf") and p.pf_of([-1.0, 1.0]) == 1.0 and p.pf_of([]) is None
# the 2-of-3 rule: exactly two windows suffice, one does not; n >= 100 per window
rows_pf = lambda w: window(0, 100, w)
three = [mk(i, j < 30) for i, j in zip(range(300), [k % 100 for k in range(300)])]          # all three windows 30 wins
assert p.read_rows(three)["VERDICT"] == "PROVEN" and p.read_rows(three)["windows_counting"] == 3
# unsettled-only and empty inputs: NOT YET, no division by zero
assert p.read_rows([])["VERDICT"] == "NOT_ENOUGH_DATA" and p.read_rows([])["windows"][0]["cash_pf_unrounded"] is None and p.read_rows([])["rows_used"] == 0
# split sizes follow i*n//3
assert [len(x) for x in p.split(list(range(10)))] == [3, 3, 4] and [len(x) for x in p.split(list(range(299)))] == [99, 100, 100]
# the file entry point takes a report dict (slotOrders) or a plain list; the output carries the interpreter line and no row-level detail
with tempfile.TemporaryDirectory() as t:
    f = os.path.join(t, "r.json"); json.dump({"slotOrders": A}, open(f, "w")); r1 = p.read_file(f)
    g = os.path.join(t, "l.json"); json.dump(A, open(g, "w")); r2 = p.read_file(g)
    assert r1 == r2 and r1["VERDICT"] == "PROVEN" and r1["python"].startswith(sys.version.split()[0]) and "KXBTC15M-T" not in json.dumps(r1)
    h = os.path.join(t, "bad.json"); json.dump({"x": 1}, open(h, "w"))
    try: p.read_file(h); assert 0
    except SystemExit as e: assert "STOP" in str(e)
print("test_proven_oicore_second: all checks passed")
