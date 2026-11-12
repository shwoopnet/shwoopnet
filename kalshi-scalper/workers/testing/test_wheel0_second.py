"""Synthetic tests of wheel0_second.py (built from the registration text alone). No Kalshi data."""
import json, os, random, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wheel0_second as W

# ---- bands and edges (basis points) ----
assert W.band_of("cheap", 500) == "05-20" and W.band_of("cheap", 499) is None and W.band_of("cheap", 2000) == "20-35" and W.band_of("cheap", 3500) == "35-50" and W.band_of("cheap", 5000) == "35-50" and W.band_of("cheap", 5001) is None
assert W.band_of("fav", 5000) is None and W.band_of("fav", 5001) == "50-65" and W.band_of("fav", 6500) == "50-65" and W.band_of("fav", 6501) == "65-80" and W.band_of("fav", 8000) == "65-80" and W.band_of("fav", 8001) == "80-88" and W.band_of("fav", 8800) is None
assert W.third_of(8800) == "88-97" and W.third_of(9700) == "88-97" and W.third_of(9701) is None and W.third_of(8799) is None
# ---- fee: 10 contracts, rounded UP to the cent ----
assert W.fee10(0.5) == 0.18 and W.fee10(0.1) == 0.07 and W.fee10(0.2) == 0.12
# ---- look signals: the candle ending exactly at close - L; spread <= 4c; one-sided or equal asks are no signal ----
C0 = 1_790_000_000
def mk(t, close=C0, ser="KXXRP15M"): return {"series": ser, "ticker": t, "close": close}
def idx_of(rows): return {t: {ts: {"bid": b, "ask": a} for ts, (b, a) in d.items()} for t, d in rows.items()}
ix = idx_of({"T1": {C0 - 600: (0.17, 0.20), C0 - 360: (0.16, 0.21), C0 - 180: (0.50, 0.50)}})       # L600: yes ask .20 -> cheap 20-35 (edge), no ask .83 -> fav 80-88; L360: spread 5c: none; L180: bid>=ask: none
s = W.signals([mk("T1")], ix); assert sorted((x["L"], x["side"], x["band"]) for x in s) == [(600, "cheap", "20-35"), (600, "fav", "80-88")], s
assert W.signals([mk("T1")], idx_of({"T1": {C0 - 599: (0.17, 0.20)}})) == []          # the candle must END exactly at close - L
assert W.signals([mk("T1")], {"T1": {C0 - 600: {"bid": None, "ask": 0.2}}}) == []        # one-sided
assert W.signals([mk("T1")], idx_of({"T1": {C0 - 600: (0.49, 0.51)}})) == []             # equal asks (.51 and .51): no signal for either side
assert sorted(x["side"] for x in W.signals([mk("T1")], idx_of({"T1": {C0 - 600: (0.50, 0.52)}}))) == ["cheap", "fav"]
# ---- settle: win, loss, void (price refunded, fee kept, a loss) ----
sg = W.signals([mk("T1")], idx_of({"T1": {C0 - 600: (0.17, 0.20)}}))[0]; assert sg["yes"] and sg["band"] == "20-35"
w, l, v = W.settle(sg, "yes"), W.settle(sg, "no"), W.settle(sg, "")
assert abs(w["net"] - (10 * 0.8 - W.fee10(0.2))) < 1e-9 and abs(l["net"] - (-2.0 - W.fee10(0.2))) < 1e-9 and v["net"] == -W.fee10(0.2) and v["void"] and not v["win"]
# ---- the random drop: depends on seed, ticker, look and side only (never on the result) ----
assert W.drop_hash("T1", 600, "cheap") == W.drop_hash("T1", 600, "cheap") and W.drop_hash("T1", 600, "cheap") != W.drop_hash("T1", 360, "cheap") and 0 <= W.drop_hash("T9", 180, "fav") < 1
# ---- blocks ----
def O(i, win, side="cheap", net=None, series="KXXRP15M", band="20-35", L=600, third=False):
    return {"series": series, "ticker": "M%05d" % i, "close": C0 + 900 * i, "L": L, "side": side, "band": band, "third": third, "yes": True, "win": win, "net": (net if net is not None else (8.0 if win else -2.0)), "void": False}
# cheap template: 60 signals with only 9 wins is not yet a block; it runs on until the 10th win
seq = [O(i, i % 7 == 0 and i < 70) for i in range(120)]
b = W.blocks(seq); assert b and b[0]["end"] + 1 >= 60 and sum(1 for o in b[0]["orders"] if o["win"]) == 10 and len(b[0]["orders"]) == b[0]["end"] - b[0]["start"] + 1
# a tail that never completes is not a block; the next block starts at the next signal; no overlap
seq2 = [O(i, i % 5 == 0) for i in range(60)] + [O(100 + i, i % 5 == 0) for i in range(30)]
b2 = W.blocks(seq2); assert len(b2) == 1 and b2[0]["end"] == 59 and len(b2[0]["orders"]) == 60
seq3 = [O(i, i % 5 == 0) for i in range(180)]; b3 = W.blocks(seq3); assert [x["start"] for x in b3] == [0, 60, 120] and [x["end"] for x in b3] == [59, 119, 179]
# favourite template: the rarer outcome is the LOSS
fseq = [O(i, i % 9 != 0, side="fav", net=None) for i in range(200)]; fb = W.blocks(fseq); assert sum(1 for o in fb[0]["orders"] if not o["win"]) == 10 and len(fb[0]["orders"]) >= 60
# third line: at least 150 and to the 10th loss
tseq = [O(i, i % 20 != 0, side="fav", band="88-97", third=True) for i in range(400)]; tb = W.blocks(tseq, True); assert len(tb[0]["orders"]) >= 150 and sum(1 for o in tb[0]["orders"] if not o["win"]) == 10
# HOT: PF >= 1.3 overall AND >= 1.0 in each half (first floor(n/2), then the rest)
good = [O(i, i % 5 == 0, net=(3.0 if i % 5 == 0 else -0.5)) for i in range(60)]; assert W.blocks(good)[0]["hot"]                 # wins pay 3 vs losses 0.5, 12 wins: PF = 36/24 = 1.5 in total and in each half
front = [O(i, i < 12, net=(8.0 if i < 12 else -0.6)) for i in range(60)]; bf = W.blocks(front)[0]; assert not bf["hot"]       # all wins first: second half has no wins: PF 0 in the second half, not HOT despite overall PF >= 1.3
assert W.pf([4, -2, -2]) == 1.0 and W.pf([5]) == float("inf") and W.pf([]) is None
# ---- pairing: each block with the next block of the same template and market ----
prs = W.pairs(seq3); assert len(prs) == 2 and prs[0][0] is not prs[0][1]
other = [O(1000 + i, i % 5 == 0, series="KXDOGE15M") for i in range(120)]; assert len(W.pairs(seq3 + other)) == 3                    # a second market pairs on its own
# ---- D and verdict thresholds ----
assert W.verdict(1.15, 0.1, 30, 0.05, 0.05) == "PREMISE SUPPORTED" and W.verdict(1.15, 0.1, 30, 0.051, 0.01) .startswith("no evidence") and W.verdict(1.15, 0.1, 29, 0.0, 0.0) == "no evidence at n = 29 HOT pairs"
assert W.verdict(0.99, 0.1, 30, 0.0, 0.0) == "PREMISE NOT SUPPORTED" and W.verdict(1.2, 0.0, 30, 0.0, 0.0) == "PREMISE NOT SUPPORTED" and W.verdict(1.14, 0.1, 30, 0.0, 0.0).startswith("no evidence") and W.verdict(1.2, -0.1, 99, 0.0, 0.0) == "PREMISE NOT SUPPORTED"
# ---- rule (h): Bitcoin and Ethereum markets closing on or after 2026-10-29T00:00Z are dropped at the reader, on the close time ----
cut = W.BTC_ETH_CUT; ms = [dict(mk("B1", cut - 1, "KXBTC15M"), result="yes"), dict(mk("B2", cut, "KXBTC15M"), result="yes"), dict(mk("E1", cut + 5, "KXETH15M"), result="no"), dict(mk("X1", cut + 5, "KXXRP15M"), result="yes")]
ixh = idx_of({t: {c - 600: (0.17, 0.20)} for t, c in (("B1", cut - 1), ("B2", cut), ("E1", cut + 5), ("X1", cut + 5))})
dt = {g: [{"L": L, "side": sd, "band": bd, "fill_share": 1.0} for L in W.LOOKS for sd, bds in (("cheap", ("05-20", "20-35", "35-50")), ("fav", ("50-65", "65-80", "80-88", "88-97"))) for bd in bds] for g in ("gold_xrp_doge", "xrp_doge")}
lk = {"05-20": .09, "20-35": .06}
r = W.full_read(ms, ixh, dt, lk, boot_draws=50, null_runs=5); assert r["counts_first"]["markets"] == 2, r["counts_first"]          # B1 (before the cut) and X1 stay; B2 and E1 are gone
# ---- a fair-coin world: never SUPPORTED, D near 0 ----
random.seed(3); fair = []; ixf = {}; chance = {}
for i in range(2500):
    t = "F%05d" % i; c = C0 + 900 * i; ser = "KXXRP15M"; ask = 0.12 + random.random() * 0.3
    fair.append({"series": ser, "ticker": t, "close": c, "result": "yes" if random.random() < ask - 0.01 else "no"}); ixf[t] = {c - 600: {"bid": ask - 0.03, "ask": ask}}
rf = W.full_read(fair, ixf, dt, lk, boot_draws=300, null_runs=20); assert rf["verdict"] != "PREMISE SUPPORTED" and rf["counts_first"]["hot_pairs"] >= 0, rf["verdict"]
assert rf["counts_first"]["signals"] > 0 and rf["primary"]["p_bootstrap"] is not None
# ---- the outcome is not needed to form signals: signals() takes no result; the drop takes none either ----
import inspect
assert "result" not in inspect.signature(W.signals).parameters and "result" not in inspect.signature(W.drop_hash).parameters
# ---- the guarded reader ----
import time
with tempfile.TemporaryDirectory() as d:
    pre = os.path.join(d, "PRE.md"); open(pre, "w").write("Status: DEPTH1's read has not been made.\n")
    out = os.path.join(d, "out.json")
    for now, text, why in ((W.NOT_BEFORE - 1, "DEPTH1 READ MADE: yes\n", "before the date"), (W.NOT_BEFORE, "nothing\n", "no marker line"), (W.NOT_BEFORE, " DEPTH1 READ MADE: indented\n", "marker not at the start of a line")):
        open(pre, "w").write(text)
        try: W.precondition(pre, now); raise AssertionError(why)
        except SystemExit: pass
    open(pre, "w").write("DEPTH1 READ MADE: 2026-11-14 test\n"); W.precondition(pre, W.NOT_BEFORE)
    hd = os.path.join(d, "HELDOUT_Z"); os.makedirs(hd)
    try: W.read_all([hd], [], pre, "x", "y", out, W.NOT_BEFORE); raise AssertionError("HELDOUT_ must be refused")
    except SystemExit as e: assert "HELDOUT_" in str(e)
    open(out, "w").write("{}")
    try: W.read_all([], [], pre, "x", "y", out, W.NOT_BEFORE); raise AssertionError("second read must be refused")
    except SystemExit as e: assert "once" in str(e)
# ---- book read: look poll within 10 s, the first LATER poll within 4 s must still offer 10 at or under the limit; the average walked ----
def poll(t, yb, nb): return {"t": t, "yes_bids": yb, "no_bids": nb}
Bm = [{"series": "KXGOLD15M", "ticker": "G1", "close": C0}]
look = C0 - 600
pl = [poll(look + 2, [(0.17, 50)], [(0.80, 50)]), poll(look + 5, [(0.17, 50)], [(0.80, 4), (0.79, 50)])]              # yes ask .20; second poll: 4 at .20 then 6 more at .21 (limit .21): average .2060
bo = W.book_orders(Bm, {"G1": pl}); y = [o for o in bo if o["yes"]]; assert len(y) == 1 and abs(y[0]["paid"] - (4 * 0.20 + 6 * 0.21) / 10) < 1e-9, bo
assert W.book_orders(Bm, {"G1": [pl[0], poll(look + 9, [(0.17, 50)], [(0.80, 50)])]}) == []                                 # the later poll is 7 s after the look poll: no trade
assert W.book_orders(Bm, {"G1": [poll(look + 11, [(0.17, 50)], [(0.80, 50)]), poll(look + 12, [(0.17, 50)], [(0.80, 50)])]}) == []   # look poll arrives after 10 s: no look
assert not [o for o in W.book_orders(Bm, {"G1": [pl[0], poll(look + 5, [(0.17, 50)], [(0.80, 4), (0.79, 3)])]}) if o["yes"]]                         # not enough size at or under the limit
assert W.book_orders([{"series": "KXBTC15M", "ticker": "B", "close": C0}], {"B": pl}) == []                                  # no Bitcoin or Ethereum book row is ever kept
print("wheel0_second synthetic tests passed")
