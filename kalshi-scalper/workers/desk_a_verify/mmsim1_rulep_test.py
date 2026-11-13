"""Rule P hand cases on INVENTED books and trades (hand-computed). python3 -I mmsim1_rulep_test.py"""
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import mmsim1_rulep as M
ct = "2026-11-01T15:00:00Z"; T = M.parse_ms(ct)
def row(min_before, yb, ys, nb, ns): return {"poll_ts_local_ms": str(T - int(min_before * 60000)), "yes_bid_px_1": yb, "yes_bid_sz_1": ys, "no_bid_px_1": nb, "no_bid_sz_1": ns}
def tr(min_before, yes_price, cnt, taker): return {"created_time": M.dt.datetime.fromtimestamp((T - int(min_before * 60000)) / 1000, M.dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"), "yes_price_dollars": str(yes_price), "count_fp": str(cnt), "taker_outcome_side": taker, "trade_id": "t%s%s" % (min_before, yes_price)}
def run(rows, trades_, rule):
    b = {(ct, "KXA"): rows}; t = {"KXA": {x["trade_id"]: x for x in trades_}}
    return M.simulate(b, t, 0.0, rule)
post = row(50, "0.40", "100", "0.55", "100")
# A: a taker NO print at yes 0.39 (through our YES bid 0.40) and a book poll where the NO bid fell to 0.50: Rule P fills both legs at our prices, a pair paying 1 - 0.40 - 0.55 = 0.05; Rule Q fills nothing
rowsA = [post, row(30, "0.40", "100", "0.50", "100"), row(16, "0.40", "100", "0.50", "100")]; trA = [tr(40, 0.39, 5, "no")]
qa, pa = run(rowsA, trA, "Q"), run(rowsA, trA, "P")
assert qa[0][1] == 0.0 and qa[0][3:] == (0, 0, 0, 0), qa
assert abs(pa[0][1] - 0.05) < 1e-12 and pa[0][3:] == (1, 1, 1, 0), pa
# B: the quote moves AWAY in our favour (bids rise to 0.42 and 0.57): not a fill under P
rowsB = [post, row(30, "0.42", "100", "0.57", "100"), row(16, "0.42", "100", "0.57", "100")]
assert run(rowsB, [], "P")[0][3:] == (0, 0, 0, 0)
# C: a poll AT T-15 (not strictly before) with a lower bid is not a fill; strictly before is; a through print at or before T-15 counts, one after does not (the row list stops at T-15, the trade list too)
rowsC = [post, row(15, "0.30", "100", "0.55", "100")]
assert run(rowsC, [], "P")[0][3:] == (0, 0, 0, 0)
rowsC2 = [post, row(15.01, "0.30", "100", "0.55", "100"), row(15, "0.30", "100", "0.55", "100")]
r = run(rowsC2, [], "P"); assert r[0][3] == 1 and r[0][4] == 0, r         # YES leg filled by the book, NO leg not
assert run([post, row(16, "0.40", "100", "0.55", "100")], [tr(15, 0.39, 1, "no")], "P")[0][3] == 1     # a print exactly at T-15 counts (not after)
assert run([post, row(16, "0.40", "100", "0.55", "100")], [tr(14.9, 0.39, 1, "no")], "P")[0][3] == 0
# D: an ABSENT best bid (blank price) after the post fills the leg; a print at the same price (not through) does not
rowsD = [post, row(30, "", "", "0.55", "100"), row(16, "", "", "0.55", "100")]
assert run(rowsD, [], "P")[0][3] == 1
assert run([post, row(16, "0.40", "100", "0.55", "100")], [tr(30, 0.40, 1, "no")], "P")[0][3] == 0
# E: Rule Q is unchanged: the original queue fill (cum >= ahead + 1 at our price) still fills under both rules
rowsE = [post, row(16, "0.40", "100", "0.55", "100")]; trE = [tr(40, 0.40, 101, "no")]
assert run(rowsE, trE, "Q")[0][3] == 1 and run(rowsE, trE, "P")[0][3] == 1
# F5: blank or unparseable values never crash a run (a blank trade price, count or time, a blank poll time): those rows are skipped
rowsF = [post, {"poll_ts_local_ms": "", "yes_bid_px_1": "0.40", "yes_bid_sz_1": "100", "no_bid_px_1": "0.55", "no_bid_sz_1": "100"}, row(16, "0.40", "100", "0.55", "100")]
trF = [dict(tr(40, 0.39, 5, "no"), yes_price_dollars=""), dict(tr(39, 0.39, 5, "no"), count_fp=""), dict(tr(38, 0.39, 5, "no"), created_time=""), tr(37, 0.39, 5, "no")]
rf = run(rowsF, trF, "P"); assert rf[0][3] == 1, rf           # only the last, well-formed through print fills the YES leg; nothing crashed
# sizes: fee per order, unrounded or rounded UP to the cent, on 1 or 10 contracts (per-contract pnl). A pair at 0.40 + 0.55 with maker 0.0175: unrounded fee per leg 0.0175 x p x (1 - p)
def run2(rows, trades_, rule, coef, size, rounded):
    b = {(ct, "KXA"): rows}; t = {"KXA": {x["trade_id"]: x for x in trades_}}
    return M.simulate(b, t, coef, rule, size, rounded)
pa2 = run2(rowsA, trA, "P", 0.0175, 1, False)[0][1]; assert abs(pa2 - (0.05 - 0.0175 * 0.40 * 0.60 - 0.0175 * 0.55 * 0.45)) < 1e-12, pa2
pr1 = run2(rowsA, trA, "P", 0.0175, 1, True)[0][1]; assert abs(pr1 - (0.05 - 0.01 - 0.01)) < 1e-12, pr1          # 1 contract: each leg's fee 0.0042 and 0.0043 rounds UP to 0.01
pr10 = run2(rowsA, trA, "P", 0.0175, 10, True)[0][1]
import math
f10 = lambda p: math.ceil(0.0175 * 10 * p * (1 - p) * 100 - 1e-9) / 100 / 10
assert abs(pr10 - (0.05 - f10(0.40) - f10(0.55))) < 1e-12, pr10
# fractional-size share: stats rows say, per filled leg, how it was filled (q = queue, x = through print, b = book poll) and whether the triggering trade was fractional (None for a book fill)
st = []; M.simulate({(ct, "KXA"): rowsA}, {"KXA": {x["trade_id"]: x for x in trA}}, 0.0, "P", 1, False, st)
assert sorted((s["kind"], s["frac"]) for s in st) == [("b", None), ("x", False)], st
trFr = [tr(40, 0.39, 5.5, "no")]; st2 = []; M.simulate({(ct, "KXA"): rowsA}, {"KXA": {x["trade_id"]: x for x in trFr}}, 0.0, "P", 1, False, st2)
assert ("x", True) in [(s["kind"], s["frac"]) for s in st2], st2
print("MMSIM1 RULE P HAND CASES OK (through print, book poll, quote moving away, T-15 edge, absent bid, same-price print, Rule Q unchanged)")
