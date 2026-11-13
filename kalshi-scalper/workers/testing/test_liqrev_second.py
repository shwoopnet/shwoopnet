"""Test for liqrev_second.py: INVENTED rows only (LIQREV_SECOND_HAND_CASE.md). Run: python3 -B -W ignore test_liqrev_second.py"""
import calendar, csv, gzip, math, os, statistics as st, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liqrev_second as q

H = 10.0
D = lambda day, hour=12: calendar.timegm((2026, 11, day, hour, 0, 0))
def row(ts, side, sz, inst="BTC-USDT-SWAP", px=100000, pos="net"): return {"inst_id": inst, "ts_ms": int(ts * 1000), "side": side, "pos_side": pos, "sz": sz, "bk_px": px}
def poll(recv_s, yb, nb): return (int(round(recv_s * 1000)), yb, nb)
# --- pure pieces ---
assert q.btc_size("BTC-USDT-SWAP", 600, None) == 6.0 and abs(q.btc_size("BTC-USD-SWAP", 10000, 100000) - 10.0) < 1e-12
for bad in ("ETH-USDT-SWAP", "BTC-USDC-SWAP", ""):
    try: q.btc_size(bad, 1, 1); assert 0
    except SystemExit as e: assert "R2" in str(e)
try: q.btc_size("BTC-USD-SWAP", 1, 0); assert 0
except SystemExit: pass
r1 = row(5, "sell", 600); assert len(q.dedupe([r1, dict(r1), row(5, "sell", 601)])) == 2          # R12: the key includes sz
assert len(q.dedupe([r1, dict(r1, t_recv_ms=999)])) == 1          # extra columns do not matter
try: q.liq_events([row(1, "long", 1)]); assert 0
except SystemExit as e: assert "R1" in str(e)
# L(t): ts == t - 180 s is in, ts == t is out
t0 = D(17)
ev = q.liq_events([row(t0 - 180, "sell", 100), row(t0, "sell", 100), row(t0 - 90, "sell", 200)])
assert abs(q.L_at(ev["sell"], t0) - 3.0) < 1e-12          # [t0 - 180, t0): the row AT t0 - 180 (1 BTC) is in and the row AT t0 is out; t0 - 90 (2 BTC) is in
assert abs(q.L_at(ev["sell"], t0 + 60) - 3.0) < 1e-12          # [t0 - 120, t0 + 60): the t0 - 180 row has left, the t0 row (1 BTC) has joined
# coverage (R15): [a, b) holds [close - 900, close - 180)
C = D(17)
assert q.covered([(C - 900, C - 180)], C) and not q.covered([(C - 899, C - 180)], C) and not q.covered([(C - 900, C - 181)], C) and not q.covered([], C)
assert q.covered([(0, 10), (C - 1000, C)], C) and not q.covered([(C - 1000, C - 500), (C - 500, C)], C)          # one interval must hold it all
# quote (R6): (t, t + 10 s]
pl = [poll(C - 600, .4, .5), poll(C - 590, .41, .5), poll(C - 589.9, .42, .5)]
assert q.first_quote(pl, C - 600)[1] == 0.41 and q.first_quote([poll(C - 600, .4, .5)], C - 600) is None and q.first_quote([poll(C - 589.9, .4, .5)], C - 600) is None and q.first_quote([], C) is None
assert q.usable(0.35, 0.63)["yes_ask"] > 0.36 and abs(q.usable(0.35, 0.63)["spread"] - 0.02) < 1e-12 and abs(q.usable(0.35, 0.63)["no_ask"] - 0.65) < 1e-12
assert q.usable(None, .5) is None and q.usable(.4, None) is None and q.usable(0.0, 0.5) is None and q.usable(.5, .5) is None and q.usable(.6, .5) is None and q.usable(.4, 0.0) is None          # 0 < yes bid < YES ask < 1
# trigger: first minute, tolerance, both sides
C = D(17)
assert q.trigger(q.liq_events([row(C - 700, "sell", 1000)]), C, 10.0) == (C - 660, "sell")          # exactly H triggers
assert q.trigger(q.liq_events([row(C - 700, "sell", 999)]), C, 10.0) is None
assert q.trigger(q.liq_events([row(C - 700, "sell", 1000), row(C - 700, "buy", 1000)]), C, 10.0) == (C - 660, "both")
assert q.trigger(q.liq_events([row(C - 700, "sell", 600), row(C - 650, "sell", 400)]), C, 10.0) == (C - 600, "sell")
assert q.trigger(q.liq_events([row(C - 400, "buy", 1100)]), C, 10.0) == (C - 360, "buy")
assert q.trigger(q.liq_events([row(C - 170, "sell", 5000)]), C, 10.0) is None          # a row after close - 180 is never seen (the last check is at close - 180: [close - 360, close - 180))
assert q.trigger(q.liq_events([row(C - 181, "sell", 5000)]), C, 10.0) == (C - 180, "sell")          # the last minute, inclusive
assert q.trigger(q.liq_events([row(C - 721, "sell", 5000)]), C, 10.0) == (C - 720, "sell")          # the first minute, inclusive
# --- the invented windows of the hand case ---
rows, polls, markets = [], {}, []
def add(name, close, side_rows, quote, result):
    tk = "KXBTC15M-%s" % name
    rows.extend(side_rows); markets.append({"ticker": tk, "close": close, "result": result})
    if quote is not None: polls[tk] = quote
W1, W2, W3, W4, W4b = D(17), D(18), D(19, 12), D(19, 13), D(19, 14)
add("W1", W1, [row(W1 - 700, "sell", 600), row(W1 - 650, "sell", 400)], [poll(W1 - 598, .35, .63)], "yes")
add("W2", W2, [row(W2 - 400, "buy", 1100)], [poll(W2 - 357, .62, .35)], "yes")
add("W3", W3, [row(W3 - 700, "sell", 1000), row(W3 - 700, "buy", 1000)], None, "yes")
add("W4", W4, [row(W4 - 700, "sell", 999)], None, "no")
add("W4b", W4b, [row(W4b - 700, "sell", 1000)], [poll(W4b - 659, .40, .58)], "no")
W5, W6, W7, W8, W9 = D(20, 12), D(20, 13), D(21, 12), D(21, 13), D(22)
add("W5", W5, [row(W5 - 400, "buy", 1100)], [poll(W5 - 349, .5, .5)], "yes")
add("W6", W6, [row(W6 - 700, "sell", 1100)], [poll(W6 - 659, None, .5)], "yes")
add("W7", W7, [row(W7 - 700, "sell", 1100)], [poll(W7 - 659, .12, .02), poll(W7 - 599, .35, .63)], "yes")          # the first quote fails the band; a later minute's good quote is NOT tried
add("W8", W8, [row(W8 - 700, "sell", 1100)], [poll(W8 - 659, .30, .65)], "yes")
add("W9", W9, [row(W9 - 700, "sell", 1100)], [poll(W9 - 659, .35, .63)], "yes")
W10, W11 = D(24, 12), D(24, 13)
add("W10", W10, [row(W10 - 700, "sell", 1100)], [poll(W10 - 659, .49, .49)], "void")
add("W11", W11, [row(W11 - 700, "sell", 10000, inst="BTC-USD-SWAP", px=100000)], [poll(W11 - 658, .45, .53)], "yes")
add("W12", D(16), [row(D(16) - 700, "sell", 1100)], [poll(D(16) - 659, .35, .63)], "yes")
add("W13", D(30), [row(D(30) - 700, "sell", 1100)], [poll(D(30) - 659, .35, .63)], "yes")
add("OTHER", D(18), [], None, "yes"); markets[-1]["ticker"] = "KXETH15M-W1"          # another series: ignored
cov = [(0, W9 - 181), (W9 - 179, 4_000_000_000)]
NOW = q.READ_NOT_BEFORE
q.MIN_TRIGGERED, q.MIN_BETS, q.EVIDENCE_N = 3, 3, 3
o = q.dev_read(markets, rows, polls, cov, H, NOW)
c = o["counts"]
assert c == {"windows_listed": 14, "before_development_not_read": 1, "heldout_ignored": 1, "no_liq_coverage": 1, "no_trigger": 1, "both_sides": 1, "no_quote": 1, "one_sided_quote": 1, "band_or_spread_fail": 2, "bets": 5, "voids": 1}, c
assert o["triggered_with_two_sided_quote"] == 7
f = lambda p: __import__("math").ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100
assert f(0.37) == 0.02 and f(0.38) == 0.02 and f(0.42) == 0.02 and f(0.51) == 0.02 and f(0.47) == 0.02
exp = {"W1": 1 - .37 - .02, "W2": -.38 - .02, "W4b": -.42 - .02, "W10": -.02, "W11": 1 - .47 - .02}          # W2: a NO bet at .38 that loses (the result is yes)
assert abs(o["all"]["net"] - sum(exp.values())) < 1e-9 and abs(o["all"]["net"] - 0.26) < 1e-9, o["all"]
gain, loss = 0.61 + 0.51, 0.40 + 0.44 + 0.02
assert abs(o["all"]["pf"] - gain / loss) < 1e-12 and abs(o["all"]["pf"] - 1.3023) < 5e-5
assert o["half1"]["n"] == 3 and abs(o["half1"]["pf"] - 0.61 / 0.84) < 1e-12 and abs(o["half1"]["pf"] - 0.7262) < 5e-5 and o["half2"]["n"] == 2 and abs(o["half2"]["pf"] - 0.51 / 0.02) < 1e-9
assert o["development_verdict"] == "CLOSED (half 1 PF under 1.2)", o["development_verdict"]
# z clustered by the Central day: days 17, 18, 19, 24 with mean nets .61, -.40, -.44, .245 (the 24th holds W10 and W11)
means = [0.61, -0.40, -0.44, (-0.02 + 0.51) / 2]
assert abs(o["z_by_central_day_cluster_z"]["z"] - (sum(means) / 4) / (st.stdev(means) / math.sqrt(4))) < 1e-9 and o["z_by_central_day_cluster_z"]["clusters"] == 4
assert o["evidence_label"] == "n = 5 bets"
# kill lines and labels: the registered thresholds
q.MIN_TRIGGERED, q.MIN_BETS, q.EVIDENCE_N = 60, 60, 30
o2 = q.dev_read(markets, rows, polls, cov, H, NOW)
assert o2["evidence_label"] == "no evidence at n = 5" and "zero-try count: 7 triggered windows" in o2["development_verdict"] and "fewer than 60 bets (n = 5)" in o2["development_verdict"] and "half 1 PF under 1.2" in o2["development_verdict"]
q.MIN_TRIGGERED, q.MIN_BETS, q.EVIDENCE_N = 3, 3, 3
# a continuing read: only the good windows (W1, W2 flipped to a win, W11): PF >= 1, halves >= 1.2
good = [dict(m, result=("no" if m["ticker"] == "KXBTC15M-W2" else m["result"])) for m in markets if m["ticker"] in ("KXBTC15M-W1", "KXBTC15M-W2", "KXBTC15M-W11", "KXBTC15M-W10")]
og = q.dev_read(good, rows, polls, cov, H, NOW)
assert og["counts"]["bets"] == 4 and og["development_verdict"] == "CONTINUE" and abs(og["all"]["pf"] - (0.61 + 0.60 + 0.51) / 0.02) < 1e-9, (og["development_verdict"], og["all"])
good2 = [dict(m, result="yes") for m in markets if m["ticker"] in ("KXBTC15M-W1", "KXBTC15M-W11", "KXBTC15M-W10")]
og2 = q.dev_read(good2, rows, polls, cov, H, NOW); assert og2["counts"]["bets"] == 3 and og2["development_verdict"] == "CONTINUE", (og2["development_verdict"], og2["half1"], og2["half2"])
# PF under 1.0: a lone loser
lone = [dict(m, result="no") for m in markets if m["ticker"] == "KXBTC15M-W1"]; q.MIN_TRIGGERED = q.MIN_BETS = 1
ol = q.dev_read(lone, rows, polls, cov, H, NOW); assert "cash PF under 1.0" in ol["development_verdict"]
q.MIN_TRIGGERED, q.MIN_BETS = 3, 3
# --- guards ---
for now in (q.READ_NOT_BEFORE - 1, 0):
    try: q.dev_read(markets, rows, polls, cov, H, now); assert 0
    except SystemExit as e: assert "refused" in str(e) and "2026-11-30" in str(e)
for badH in (None, 0, -1, "10"):
    try: q.dev_read(markets, rows, polls, cov, badH, NOW); assert 0
    except SystemExit as e: assert "H is a required input" in str(e)
try: q.dev_read(markets + [dict(markets[0])], rows, polls, cov, H, NOW); assert 0
except SystemExit as e: assert "duplicate window KXBTC15M-W1" in str(e)
for bad in ("scalar", "", None):
    try: q.dev_read([dict(markets[0], result=bad)], rows, polls, cov, H, NOW); assert 0
    except SystemExit as e: assert "KXBTC15M-W1" in str(e)
try: q.dev_read(markets, rows + [row(W1 - 700, "sell", 1, inst="ETH-USDT-SWAP")], polls, cov, H, NOW); assert 0
except SystemExit as e: assert "R2" in str(e)
# an odd result on a window OUTSIDE development is not read (counted only)
odd_out = [dict(markets[0], ticker="KXBTC15M-OLD", close=D(10), result="scalar")]; assert q.dev_read(odd_out, rows, polls, cov, H, NOW)["counts"]["before_development_not_read"] == 1
# development edges: close exactly 2026-11-17T00:00Z is in, exactly 2026-11-30T00:00Z is out; the half split at 2026-11-23T12:00Z
Cb = q.DEV_FROM; add("EDGE_IN", Cb, [row(Cb - 700, "sell", 1100)], [poll(Cb - 659, .35, .63)], "yes")
Ce = q.DEV_TO; add("EDGE_OUT", Ce, [row(Ce - 700, "sell", 1100)], [poll(Ce - 659, .35, .63)], "yes")
Cs = q.HALF_SPLIT; add("SPLIT", Cs, [row(Cs - 700, "sell", 1100)], [poll(Cs - 659, .35, .63)], "yes")
oe = q.dev_read([m for m in markets if m["ticker"] in ("KXBTC15M-EDGE_IN", "KXBTC15M-EDGE_OUT", "KXBTC15M-SPLIT")], rows, polls, [(0, 4_000_000_000)], H, NOW)
assert oe["counts"]["bets"] == 2 and oe["counts"]["heldout_ignored"] == 1 and oe["half1"]["n"] == 1 and oe["half2"]["n"] == 1          # the split instant belongs to half 2
# band and spread edges (inclusive, 1e-9): ask .80 with spread .04 passes; .81, .19 and spread .05 fail; ask .20 passes; spread exactly .04 passes
edge_rows, edge_polls, edge_mk = [], {}, []
for i, (name, yb, nb, ok) in enumerate((("A80", .76, .20, True), ("A81", .78, .19, False), ("A20", .18, .80, True), ("A19", .17, .81, False), ("S05", .45, .50, False), ("S04", .46, .50, True))):
    Ce_ = D(25 + i // 3, 12 + i % 3)
    edge_rows.append(row(Ce_ - 700, "sell", 1100)); edge_polls["KXBTC15M-" + name] = [poll(Ce_ - 659, yb, nb)]; edge_mk.append({"ticker": "KXBTC15M-" + name, "close": Ce_, "result": "yes"})
oe2 = q.dev_read(edge_mk, edge_rows, edge_polls, [(0, 4_000_000_000)], H, NOW)
assert oe2["counts"]["bets"] == 3 and oe2["counts"]["band_or_spread_fail"] == 3, oe2["counts"]
# the R6 loader reads the real header; an empty cell is None, never a shifted level
HDR = ("t_send_ms,t_recv_ms,server_date_header,ticker,series,close_time,yes_bid_px_1,yes_bid_px_2,yes_bid_px_3,yes_bid_px_4,yes_bid_px_5,yes_bid_sz_1,yes_bid_sz_2,yes_bid_sz_3,yes_bid_sz_4,yes_bid_sz_5,"
       "no_bid_px_1,no_bid_px_2,no_bid_px_3,no_bid_px_4,no_bid_px_5,no_bid_sz_1,no_bid_sz_2,no_bid_sz_3,no_bid_sz_4,no_bid_sz_5")
with tempfile.TemporaryDirectory() as d:
    fp = os.path.join(d, "book.csv.gz")
    with gzip.open(fp, "wt", newline="") as fh:
        fh.write(HDR + "\n"); w = csv.writer(fh)
        w.writerow([1, 5000, "x", "KXBTC15M-A", "KXBTC15M", "c", "", 0.30, "", "", "", "", 5, "", "", "", 0.60, "", "", "", "", 7, "", "", "", ""])
        w.writerow([1, 6000, "x", "KXBTC15M-A", "KXBTC15M", "c", 0.31, "", "", "", "", 9, "", "", "", "", 0.60, "", "", "", "", 7, "", "", "", ""])
    got = q.load_r6_top(fp)["KXBTC15M-A"]; assert got == [(5000, None, 0.60), (6000, 0.31, 0.60)], got
# the result of the whole: no key text leaks ticker detail beyond counts
assert "KXBTC15M" not in repr({k_: v for k_, v in o.items() if k_ not in ("ambiguities",)})
print("test_liqrev_second: all checks passed")
