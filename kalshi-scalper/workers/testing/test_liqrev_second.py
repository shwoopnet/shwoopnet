"""Test for liqrev_second.py: INVENTED rows only (LIQREV_SECOND_HAND_CASE.md). Run: python3 -B -W ignore test_liqrev_second.py"""
import calendar, csv, gzip, math, os, statistics as st, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liqrev_second as q

H = 1000.0          # H_sz, raw contracts of BTC-USDT-SWAP
D = lambda day, hour=12: calendar.timegm((2026, 11, day, hour, 0, 0))
def row(ts, side, sz, inst="BTC-USDT-SWAP", px=100000, pos="net"): return {"inst_id": inst, "ts_ms": int(ts * 1000), "side": side, "pos_side": pos, "sz": sz, "bk_px": px}
def poll(recv_s, yb, nb): return (int(round(recv_s * 1000)), yb, nb)
# --- pure pieces ---
assert q.EVIDENCE_N == 100 and q.MIN_BETS == 60 and q.MIN_TRIGGERED == 60          # the registered constants (the Head, 21:15Z: the evidence label threshold is 100)
assert q.contracts("BTC-USDT-SWAP", 600) == 600.0 and q.contracts("BTC-USDT-SWAP", "12.5") == 12.5 and q.contracts("BTC-USD-SWAP", 10000) is None          # Amendment 4: raw contracts of the USDT swap only; the USD swap is not used
for bad in ("ETH-USDT-SWAP", "BTC-USDC-SWAP", ""):
    try: q.contracts(bad, 1); assert 0
    except SystemExit as e: assert "R2" in str(e)
assert not hasattr(q, "btc_size")
r1 = row(5, "sell", 600); assert len(q.dedupe([r1, dict(r1), row(5, "sell", 601)])) == 2          # R12: the key includes sz
assert len(q.dedupe([r1, dict(r1, t_recv_ms=999)])) == 1          # extra columns do not matter
try: q.liq_events([row(1, "long", 1)]); assert 0
except SystemExit as e: assert "R1" in str(e)
# L(t): ts == t - 180 s is in, ts == t is out
t0 = D(17)
ev = q.liq_events([row(t0 - 180, "sell", 100), row(t0, "sell", 100), row(t0 - 90, "sell", 200)])
assert abs(q.L_at(ev["sell"], t0) - 300.0) < 1e-12          # [t0 - 180, t0): the row AT t0 - 180 (100 contracts) is in and the row AT t0 is out; t0 - 90 (200 contracts) is in
assert abs(q.L_at(ev["sell"], t0 + 60) - 300.0) < 1e-12          # [t0 - 120, t0 + 60): the t0 - 180 row has left, the t0 row (100 contracts) has joined
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
assert q.trigger(q.liq_events([row(C - 700, "sell", 1000)]), C, 1000.0) == (C - 660, "sell")          # exactly H triggers
assert q.trigger(q.liq_events([row(C - 700, "sell", 999)]), C, 1000.0) is None
assert q.trigger(q.liq_events([row(C - 700, "sell", 1000), row(C - 700, "buy", 1000)]), C, 1000.0) == (C - 660, "both")
assert q.trigger(q.liq_events([row(C - 700, "sell", 600), row(C - 650, "sell", 400)]), C, 1000.0) == (C - 600, "sell")
assert q.trigger(q.liq_events([row(C - 400, "buy", 1100)]), C, 1000.0) == (C - 360, "buy")
assert q.trigger(q.liq_events([row(C - 170, "sell", 5000)]), C, 1000.0) is None          # a row after close - 180 is never seen (the last check is at close - 180: [close - 360, close - 180))
assert q.trigger(q.liq_events([row(C - 181, "sell", 5000)]), C, 1000.0) == (C - 180, "sell")          # the last minute, inclusive
assert q.trigger(q.liq_events([row(C - 721, "sell", 5000)]), C, 1000.0) == (C - 720, "sell")          # the first minute, inclusive
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
add("W11", W11, [row(W11 - 700, "sell", 10000, inst="BTC-USD-SWAP", px=100000)], [poll(W11 - 658, .45, .53)], "yes")          # a USD-swap row: ignored (Amendment 4), so no trigger
W14 = D(24, 14); market14 = {"ticker": "KXBTC15M-W14", "close": W14, "result": "yes"}; rows.append(row(W14 - 700, "sell", 1100)); polls["KXBTC15M-W14"] = [poll(W14 - 658, .45, .53)]          # only used in the continuing set below
add("W12", D(16), [row(D(16) - 700, "sell", 1100)], [poll(D(16) - 659, .35, .63)], "yes")
add("W13", D(30), [row(D(30) - 700, "sell", 1100)], [poll(D(30) - 659, .35, .63)], "yes")
add("OTHER", D(18), [], None, "yes"); markets[-1]["ticker"] = "KXETH15M-W1"          # another series: ignored
cov = [(0, W9 - 181), (W9 - 179, 4_000_000_000)]
NOW = q.READ_NOT_BEFORE
q.MIN_TRIGGERED, q.MIN_BETS, q.EVIDENCE_N = 3, 3, 3
o = q.dev_read(markets, rows, polls, cov, H, NOW)
c = o["counts"]
assert c == {"windows_listed": 14, "before_development_not_read": 1, "heldout_ignored": 1, "no_liq_coverage": 1, "no_trigger": 2, "both_sides": 1, "no_quote": 1, "one_sided_quote": 1, "band_or_spread_fail": 2, "bets": 4, "voids": 1, "usd_swap_rows_ignored": 1}, c
assert o["triggered_with_two_sided_quote"] == 6
f = lambda p: __import__("math").ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100
assert f(0.37) == 0.02 and f(0.38) == 0.02 and f(0.42) == 0.02 and f(0.51) == 0.02 and f(0.47) == 0.02
exp = {"W1": 1 - .37 - .02, "W2": -.38 - .02, "W4b": -.42 - .02, "W10": -.02}          # W2: a NO bet at .38 that loses (the result is yes); W11 (a USD-swap row) is no longer a bet
assert abs(o["all"]["net"] - sum(exp.values())) < 1e-9 and abs(o["all"]["net"] + 0.25) < 1e-9, o["all"]
gain, loss = 0.61, 0.40 + 0.44 + 0.02
assert abs(o["all"]["pf"] - gain / loss) < 1e-12 and abs(o["all"]["pf"] - 0.7093) < 5e-5
assert o["half1"]["n"] == 3 and abs(o["half1"]["pf"] - 0.61 / 0.84) < 1e-12 and abs(o["half1"]["pf"] - 0.7262) < 5e-5 and abs(o["half1"]["net"] + 0.23) < 1e-9 and o["half2"]["n"] == 1 and o["half2"]["pf"] == 0.0 and abs(o["half2"]["net"] + 0.02) < 1e-9
assert o["development_verdict"] == "CLOSED (cash PF under 1.0; half 1 PF under 1.2; half 2 PF under 1.2)", o["development_verdict"]
# 1c and 2c beside it (entry ask + .01 / + .02, fee rounded on that price)
a1, a2 = o["at_1c"], o["at_2c"]
assert abs(a1["all"]["net"] + 0.28) < 1e-9 and abs(a1["all"]["pf"] - 0.60 / 0.88) < 1e-12 and abs(a1["all"]["pf"] - 0.6818) < 5e-5 and abs(a1["half1"]["pf"] - 0.60 / 0.86) < 1e-12 and a1["half2"]["pf"] == 0.0
assert abs(a2["all"]["net"] + 0.31) < 1e-9 and abs(a2["all"]["pf"] - 0.59 / 0.90) < 1e-12 and abs(a2["all"]["pf"] - 0.6556) < 5e-5 and abs(a2["half1"]["pf"] - 0.59 / 0.88) < 1e-12 and abs(a2["half1"]["pf"] - 0.6705) < 5e-5 and a2["half2"]["pf"] == 0.0
assert o["haircut_label"] == "does not count: fails the haircut"
assert "z_by_central_day_cluster_z" not in o and o["z"].startswith("not computed in the development read") and "held-out window alone" in o["z"]          # Amendment 4 item 2: no z here
assert o["lines"] and all(ln.endswith("(upper bound, not fill-checked)") for ln in o["lines"]) and any("VERDICT at R8's fill" in ln for ln in o["lines"]) and any("does not count: fails the haircut" in ln for ln in o["lines"])
assert o["evidence_label"] == "n = 4 bets"
# kill lines and labels: the registered thresholds
q.MIN_TRIGGERED, q.MIN_BETS, q.EVIDENCE_N = 60, 60, 100
o2 = q.dev_read(markets, rows, polls, cov, H, NOW)
assert o2["evidence_label"] == "no evidence at n = 4" and "zero-try count: 6 triggered windows" in o2["development_verdict"] and "fewer than 60 bets (n = 4)" in o2["development_verdict"] and "half 1 PF under 1.2" in o2["development_verdict"]
q.MIN_TRIGGERED, q.MIN_BETS, q.EVIDENCE_N = 3, 3, 3
# Head's ruling (21:15Z): below 100 bets the evidence label reads 'no evidence at n = x', and the registered constant is 100; the verdict is the headline and both always print

assert q.evidence_label(99, 100) == "no evidence at n = 99" and q.evidence_label(100, 100) == "n = 100 bets" and q.evidence_label(0, 100) == "no evidence at n = 0"
assert "development_verdict" in o2 and "evidence_label" in o2 and list(o2).index("development_verdict") < list(o2).index("evidence_label")
# a continuing read: W1 win, W2 flipped to a win (result no), W10 void, W14 win (+0.51): PF 86, half 1 no losses, half 2 .51 / .02 = 25.5
good = [dict(m, result=("no" if m["ticker"] == "KXBTC15M-W2" else m["result"])) for m in markets if m["ticker"] in ("KXBTC15M-W1", "KXBTC15M-W2", "KXBTC15M-W10")] + [market14]
og = q.dev_read(good, rows, polls, cov, H, NOW)
assert og["counts"]["bets"] == 4 and og["development_verdict"] == "CONTINUE" and abs(og["all"]["pf"] - 1.72 / 0.02) < 1e-9 and og["half1"]["pf"] == float("inf") and abs(og["half2"]["pf"] - 0.51 / 0.02) < 1e-9, (og["development_verdict"], og["all"])
assert abs(og["at_1c"]["all"]["pf"] - 1.69 / 0.02) < 1e-9 and abs(og["at_1c"]["half2"]["pf"] - 0.50 / 0.02) < 1e-9 and abs(og["at_2c"]["all"]["pf"] - 1.66 / 0.02) < 1e-9 and og["haircut_label"] == "passes the haircut", (og["at_1c"], og["at_2c"], og["haircut_label"])
# PF under 1.0: a lone loser
lone = [dict(m, result="no") for m in markets if m["ticker"] == "KXBTC15M-W1"]; q.MIN_TRIGGERED = q.MIN_BETS = 1
ol = q.dev_read(lone, rows, polls, cov, H, NOW); assert "cash PF under 1.0" in ol["development_verdict"]
q.MIN_TRIGGERED, q.MIN_BETS = 3, 3
# --- survivors turned into cases ---
E0 = 1000
assert abs(q.run_offset([(E0 * 1000 - 200, E0), (E0 * 1000 - 400, E0), (E0 * 1000 - 1500, E0)]) - 0.9) < 1e-9          # samples .7, .9, 2.0: the MEDIAN .9 (the mean would be 1.2)
# the haircut label on synthetic stats: every condition matters
mk_at = lambda a1, h1, h2, a2: {"1c": {"all": {"pf": a1}, "half1": {"pf": h1}, "half2": {"pf": h2}}, "2c": {"all": {"pf": a2}}}
assert q.haircut_passes(mk_at(1.3, 1.0, 1.0, 1.0)) and q.haircut_passes(mk_at(1.3 - 5e-10, 1.0 - 5e-10, float("inf"), 1.0 - 5e-10))
assert not q.haircut_passes(mk_at(1.2999, 1.0, 1.0, 1.0)) and not q.haircut_passes(mk_at(1.3, 0.9999, 1.0, 1.0)) and not q.haircut_passes(mk_at(1.3, 1.0, 0.9999, 1.0)) and not q.haircut_passes(mk_at(1.3, 1.0, 1.0, 0.9999))
assert not q.haircut_passes(mk_at(1.3, None, 1.0, 1.0)) and not q.haircut_passes(mk_at(1.3, 1.0, None, 1.0)) and not q.haircut_passes(mk_at(None, 1.0, 1.0, 1.0)) and not q.haircut_passes(mk_at(1.3, 1.0, 1.0, None))
# the haircut never changes the verdict: bets that pass R8 (PF 1.2, both halves 1.2) but fail 1c and 2c: CONTINUE, labelled 'does not count: fails the haircut'
def crafted():
    bets = []
    for half in (1, 2):
        for i in range(6): bets.append({"ticker": "t", "close": 0, "net": 0.20, "win": True, "void": False, "half": half, "day": "d", "ask": 0.78, "res": "yes", "bet": "yes"})
        for i in range(5): bets.append({"ticker": "t", "close": 0, "net": -0.20, "win": False, "void": False, "half": half, "day": "d", "ask": 0.18, "res": "no", "bet": "yes"})
    return bets
cb = crafted(); cc = {"bets": 22, "band_or_spread_fail": 0, "usd_swap_rows_ignored": 0}
sv_ = (q.MIN_TRIGGERED, q.MIN_BETS); q.MIN_TRIGGERED, q.MIN_BETS = 3, 3
try: of = q.finish(cb, cc, 1000.0)
finally: q.MIN_TRIGGERED, q.MIN_BETS = sv_
assert of["development_verdict"] == "CONTINUE" and abs(of["all"]["pf"] - 1.2) < 1e-9 and abs(of["at_1c"]["all"]["pf"] - 1.14 / 1.05) < 1e-9 and abs(of["at_2c"]["all"]["pf"] - 1.08 / 1.10) < 1e-9 and of["haircut_label"] == "does not count: fails the haircut", (of["development_verdict"], of["all"], of["at_1c"]["all"], of["at_2c"]["all"])
# the half bar is 1.2: a half at 1.0625 closes it even when everything else is fine
W15 = D(24, 15); m15 = {"ticker": "KXBTC15M-W15", "close": W15, "result": "no"}; rows.append(row(W15 - 700, "sell", 1100)); polls["KXBTC15M-W15"] = [poll(W15 - 658, .42, .56)]
oh = q.dev_read(good + [m15], rows, polls, cov, H, NOW)
assert oh["counts"]["bets"] == 5 and abs(oh["half2"]["pf"] - 0.51 / 0.48) < 1e-9 and oh["development_verdict"] == "CLOSED (half 2 PF under 1.2)", (oh["development_verdict"], oh["half2"])
# --- guards ---
for now in (q.READ_NOT_BEFORE - 1, 0):
    try: q.dev_read(markets, rows, polls, cov, H, now); assert 0
    except SystemExit as e: assert "refused" in str(e) and "2026-11-30" in str(e)
for badH in (None, 0, -1, "10", True):
    try: q.dev_read(markets, rows, polls, cov, badH, NOW); assert 0
    except SystemExit as e: assert "H_sz is a required input" in str(e)
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
# the R6 loader reads the real header; an empty cell is None (never a shifted level); the poll time is t_recv_ms plus the FILE's offset (Amendment 4 item 3)
import email.utils
HDR = ("t_send_ms,t_recv_ms,server_date_header,ticker,series,close_time,yes_bid_px_1,yes_bid_px_2,yes_bid_px_3,yes_bid_px_4,yes_bid_px_5,yes_bid_sz_1,yes_bid_sz_2,yes_bid_sz_3,yes_bid_sz_4,yes_bid_sz_5,"
       "no_bid_px_1,no_bid_px_2,no_bid_px_3,no_bid_px_4,no_bid_px_5,no_bid_sz_1,no_bid_sz_2,no_bid_sz_3,no_bid_sz_4,no_bid_sz_5")
hd = lambda ts_: email.utils.formatdate(ts_, usegmt=True)
def book(path, rows_):
    with gzip.open(path, "wt", newline="") as fh:
        fh.write(HDR + "\n"); w = csv.writer(fh)
        for tk, recv_ms, hdr, yb, nb in rows_:
            w.writerow([1, recv_ms, hdr, tk, "KXBTC15M", "c", "" if yb is None else yb, "", "", "", "", "", "", "", "", "", "" if nb is None else nb, "", "", "", "", "", "", "", "", ""])
assert q.header_s(hd(1000)) == 1000 and q.header_s("x") is None and q.header_s("") is None
assert abs(q.run_offset([(1000 * 1000 - 200, 1000), (1000 * 1000 - 400, 1000), (1000 * 1000 - 600, 1000)]) - 0.9) < 1e-9          # samples .7, .9, 1.1: the median
assert abs(q.run_offset([(1000 * 1000 - 200, 1000), (1000 * 1000 - 600, 1000)]) - 0.9) < 1e-9          # an even count: the mean of the two middle values
assert abs(q.run_offset([(1000 * 1000 - 200, 1000), (5, None), (1000 * 1000 - 600, 1000)]) - 0.9) < 1e-9          # an unreadable header is left out of the median
try: q.run_offset([(5, None), (6, None)]); assert 0
except SystemExit as e: assert "no poll of the run carries a readable Date header" in str(e)
with tempfile.TemporaryDirectory() as d:
    tt = D(17, 12)          # a trigger minute (whole seconds)
    fp = os.path.join(d, "book.csv.gz")
    book(fp, [("KXBTC15M-A", tt * 1000 - 400, hd(tt), 0.31, 0.60), ("KXBTC15M-A", (tt + 9.6) * 1000, hd(tt + 10), 0.32, 0.60), ("KXBTC15M-A", (tt + 19.8) * 1000, hd(tt + 20), None, 0.60), ("KXBTC15M-A", (tt + 29.4) * 1000, hd(tt + 30), 0.33, None), ("KXBTC15M-B", tt * 1000 + 7000, "x", 0.5, 0.4)])
    got = q.load_r6_top(fp)
    A_ = got["KXBTC15M-A"]; assert [p_[0] for p_ in A_] == [tt * 1000 + 500, tt * 1000 + 10500, tt * 1000 + 20700, tt * 1000 + 30300], A_          # offset 0.9 s added to each raw receive time
    assert [(p_[1], p_[2]) for p_ in A_] == [(0.31, 0.60), (0.32, 0.60), (None, 0.60), (0.33, None)]          # an empty cell stays None, never a shifted level
    assert got["KXBTC15M-B"] == [(tt * 1000 + 7900, 0.5, 0.4)]          # the row with the unreadable header is kept, with the file's offset
    raw_polls = [(tt * 1000 - 400, 0.31, 0.60), (int((tt + 9.6) * 1000), 0.32, 0.60)]
    assert q.first_quote(raw_polls, tt)[1] == 0.32          # WITHOUT the offset the raw clock picks the wrong poll
    assert q.first_quote(A_, tt)[1] == 0.31          # with it the poll received 0.4 s before the minute is at t + 0.5 s and IS the quote; the poll at raw t + 9.6 is at t + 10.5 and is out of the span
    fp2 = os.path.join(d, "book2.csv.gz"); book(fp2, [("KXBTC15M-A", tt * 1000 - 0, hd(tt), 0.4, 0.5)])
    assert q.load_r6_top(fp2)["KXBTC15M-A"] == [(tt * 1000 + 500, 0.4, 0.5)]          # this file's own offset: (tt + 0.5) - tt = 0.5 s (two files, two offsets)
    fp3 = os.path.join(d, "book3.csv.gz"); book(fp3, [("KXBTC15M-A", 5000, "x", 0.4, 0.5)])
    try: q.load_r6_top(fp3); assert 0
    except SystemExit as e: assert "readable Date header" in str(e)
# the result of the whole: no key text leaks ticker detail beyond counts
assert "KXBTC15M" not in repr({k_: v for k_, v in o.items() if k_ not in ("ambiguities",)})
print("test_liqrev_second: all checks passed")
