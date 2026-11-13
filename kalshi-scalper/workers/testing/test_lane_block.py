"""Test for lane_block.py (tool 2): INVENTED signals only (SPXOI1_TOOLS_HAND_CASES.md traces T1 to T8). Run: python3 -B -W ignore test_lane_block.py"""
import calendar, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lane_block as lb

BASE = calendar.timegm((2026, 11, 13, 18, 0, 0))          # noon Central (CST), day 1 = 2026-11-13
DAY = 86400
def sg(i, kind, day=0, sec=0, ticker=None, side="yes", limit=20, status="filled"):
    """kind: 'W' win, 'L' loss, 'V' void, None open. Fill price .20: win +788c, loss -212c, void -12c."""
    res = {"W": side, "L": ("no" if side == "yes" else "yes"), "V": "void", None: None}[kind]
    return {"ticker": ticker or "KXINX15M-T%03d" % i, "side": side, "t": BASE + day * DAY + sec, "limit_cents": limit, "status": status, "fill": 0.20, "result": res}
P = lambda **kw: lb.Params(8, 50, **dict(dict(block_n=6, days_min=2, rarer_min=2, confirm_n=3), **kw))
NOW = BASE + 15 * DAY          # inside every first block's 21 days unless a test sets its own
def run(signals, prm=None, start=BASE - 1, now=NOW): return lb.read_place(signals, prm or P(), start, now)
def seq(kinds, per_day=3, day0=0, i0=0):
    return [sg(i0 + i, k, day0 + i // per_day, 60 * (i % per_day)) for i, k in enumerate(kinds)]

# --- cents and the bar arithmetic ---
assert lb.ok_ratio(13, 10) and not lb.ok_ratio(12, 10) and not lb.ok_ratio(0, 0) and lb.ok_ratio(5, 0) and lb.ok_even(10, 10) and not lb.ok_even(9, 10) and lb.ok_even(1, 0) and not lb.ok_even(0, 0)
assert lb.central_day(BASE) == "2026-11-13" and lb.central_day(BASE + 12 * 3600 - 1) == "2026-11-13" and lb.central_day(BASE + 12 * 3600) == "2026-11-14"          # Central midnight is 06:00Z in CST: BASE is noon Central
# --- T1: PASS then QUALIFIED ---
r = run(seq("WWLWLW") + seq("LWL", per_day=3, day0=2, i0=6))
b = r["blocks"][0]
assert b["n"] == 6 and b["W_cents"] == 3152 and b["L_cents"] == 424 and b["half1"] == {"W": 1576, "L": 212} and b["half2"] == {"W": 1576, "L": 212} and b["passed"] and b["days"] == 2 and b["wins"] == 4 and b["losses"] == 2
assert b["confirmation"]["W_cents"] == 788 and b["confirmation"]["L_cents"] == 424 and b["confirmation"]["state"] == "PASSED" and r["state"] == "QUALIFIED"
# confirmation LLL: FAILED (W = 0); the next block starts after it; its three signals never count toward a block
r = run(seq("WWLWLW") + seq("LLL", day0=2, i0=6))
assert r["blocks"][0]["confirmation"]["state"] == "FAILED" and r["state"].startswith("NO_OPEN_BLOCK") and len(r["blocks"]) == 1
more = seq("WWLWLW", per_day=3, day0=3, i0=9)
r = run(seq("WWLWLW") + seq("LLL", day0=2, i0=6) + more)
assert len(r["blocks"]) == 2 and r["blocks"][1]["start_index"] == 9 and r["blocks"][1]["n"] == 6 and r["blocks"][1]["passed"]          # a new block from the first counted signal after the confirmation
# the half test fails a block with a good total: W W W W (day 1) then L L at the end: first half W W W: fine; make the SECOND half all losses: 10 W >= 13 L overall but W2 < L2 fails
r = run(seq("WWWLLL")); bb = r["blocks"][0]
assert bb["n"] == 6 and bb["W_cents"] == 2364 and bb["L_cents"] == 636 and bb["half2"] == {"W": 0, "L": 636} and bb["passed"] is False and bb["state"].startswith("FAILED")          # 10 W = 23,640 >= 13 L = 8,268 but the second half is W = 0
r = run(seq("WLLLWLLL"), P(block_n=8)); rb = r["blocks"][0]
assert rb["n"] == 8 and rb["W_cents"] == 1576 and rb["L_cents"] == 1272 and rb["half1"] == {"W": 788, "L": 636} and rb["half2"] == {"W": 788, "L": 636} and rb["passed"] is False          # 10 W = 15,760 < 13 L = 16,536: only the ratio fails, both halves hold
assert r["state"].startswith("NO_OPEN_BLOCK")          # a failed block, no further signals: nothing open
r = run(seq("LLLWWWW"), P(block_n=7)); ro = r["blocks"][0]
assert ro["n"] == 7 and ro["half1"] == {"W": 0, "L": 636} and ro["half2"] == {"W": 3152, "L": 0} and ro["passed"] is False          # (e) halves by signal count: the first floor(7 / 2) = 3 signals, then the rest
# PF exactly 1.3 passes, 1.2999 fails: W = 13 k, L = 10 k in cents using signals of exact cents (invented results)
def fake(i, cents, day=0, sec=0):
    d = sg(i, "W", day, sec); d["_cents"] = cents; return d
# (the bar arithmetic itself is tested through ok_ratio above)
# --- T2 (a): fewer than 7 days: the block does not end at n = 6 on one day; it ends when the day count is reached ---
one_day = seq("WWLWLW", per_day=6)
assert run(one_day)["state"] == "GROWING" and run(one_day)["blocks"][0]["n_so_far"] == 6 and run(one_day)["blocks"][0]["days_so_far"] == 1
seven = one_day + [sg(6, "W", 1, 0)]
r = run(seven); assert r["blocks"][0]["n"] == 7 and r["blocks"][0]["days"] == 2 and r["blocks"][0]["start_index"] == 0
# --- T3 (r): an open result stops the search ---
r = run(seq("WWL") + [sg(3, None, 1, 0)] + seq("WLW", day0=1, i0=4))
assert r["blocks"][0]["state"].startswith("WAITING_FOR_RESULTS") and r["state"].startswith("WAITING_FOR_RESULTS") and "n_so_far" in r["blocks"][0] and r["blocks"][0]["n_so_far"] == 3
r2 = run(seq("WWL") + [sg(3, "W", 1, 0)] + seq("WLW", day0=1, i0=4)); assert r2["blocks"][0]["n"] == 6          # the same data with the result in: the block ends at the 6th
# --- T4 (b, k, q): expiry ---
t5 = [sg(i, k, 0, 60 * i) for i, k in enumerate("WWLWL")]          # five signals, all final, never reaching 6 in 21 days
assert run(t5, now=BASE + 21 * DAY - 1)["state"] == "GROWING"
assert run(t5, now=BASE + 21 * DAY)["state"] == "GROWING"          # 'passes': strictly after first + 21 x 24 h
r = run(t5, now=BASE + 21 * DAY + 1); assert r["blocks"][0]["state"].startswith("EXPIRED") and r["state"].startswith("NO_OPEN_BLOCK")
t5o = [sg(i, k, 0, 60 * i) for i, k in enumerate(["W", "W", "L", None, "L"])]
r = run(t5o, now=BASE + 30 * DAY); assert r["state"].startswith("WAITING_FOR_RESULTS") and "expiry not yet decided" in r["state"]          # (q)
# a signal past the window ends the block as EXPIRED and BEGINS the next block
late = t5 + [sg(9, "W", 22, 0)]
r = run(late, now=BASE + 22 * DAY + 5); assert r["blocks"][0]["state"].startswith("EXPIRED") and r["blocks"][1]["first_t"] == BASE + 22 * DAY and r["blocks"][1]["start_index"] == 5 and r["state"] == "GROWING"
# a signal exactly at first + 21 x 24 h is inside the window and can complete the block
edge = [sg(0, "W", 0, 0), sg(1, "W", 1, 0), sg(2, "L", 2, 0), sg(3, "W", 3, 0), sg(4, "L", 4, 0), sg(5, "W", 21, 0)]
assert run(edge)["blocks"][0]["n"] == 6 and run(edge)["blocks"][0]["state"].startswith("CLEARED")          # the 6th signal at exactly first + 21 x 24 h completes the block
edge2 = edge[:5] + [sg(5, "W", 21, 1)]
assert run(edge2)["blocks"][0]["state"].startswith("EXPIRED")          # one second later: too slow
# --- T5 (n): a void is in n and in L, not in the rarer count ---
rv = run(seq("WWVWLW")); bv = rv["blocks"][0]
assert bv["n"] == 6 and bv["W_cents"] == 3152 and bv["L_cents"] == 224 and bv["wins"] == 4 and bv["losses"] == 1 and bv["passed"]
assert run(seq("WVVVVV"))["state"] == "GROWING" and run(seq("WVVVVV"))["blocks"][0]["wins_so_far"] == 1          # one win: the block keeps growing
# --- T6 (l, p, m) ---
r = run(seq("WWLWLW"), start=BASE + DAY); assert r["counted_signals"] == 3 and r["excluded"]["decided before the start time (l)"] == 3
mixed = seq("WWL") + [sg(50, "W", 0, 500, status="miss"), sg(51, "W", 0, 501, status="not_fill_checked")] + seq("WLW", day0=1, i0=3)
rm = run(mixed); assert rm["excluded"]["miss (m)"] == 1 and rm["excluded"]["not fill-checked (m)"] == 1 and rm["blocks"][0]["n"] == 6          # they do not break the run and are not counted
cs, ex = lb.counted([sg(1, "W", 0, 0, ticker="B", side="yes"), sg(2, "W", 0, 0, ticker="A", side="no"), sg(3, "W", 0, 0, ticker="A", side="yes"), sg(4, "W", 0, -5, ticker="Z", side="yes")], P(), BASE - 100)
assert [(d["ticker"], d["side"]) for d in cs] == [("Z", "yes"), ("A", "yes"), ("A", "no"), ("B", "yes")]          # (p): time, ticker, side (yes before no)
# --- T7 (i): class from the registered band ---
p1, p2, p3, pf = lb.Params(8, 50), lb.Params(8, 51), lb.Params(51, 90), lb.Params(88, 95, favourites=True)
assert (p1.need_wins, p1.need_losses) == (True, False) and (p2.need_wins, p2.need_losses) == (True, True) and (p3.need_wins, p3.need_losses) == (False, True) and pf.block_n == 150 and p1.block_n == 60 and p1.days_min == 7 and p1.rarer_min == 10 and p1.confirm_n == 30
both = lb.Params(8, 51, block_n=6, days_min=2, rarer_min=2, confirm_n=3)
assert run(seq("WWWWWL"), both)["state"] == "GROWING" and run(seq("WWWWLL"), both)["blocks"][0]["n"] == 6          # crossing 50c needs 2 wins AND 2 losses
losses_only = lb.Params(51, 90, block_n=6, days_min=2, rarer_min=2, confirm_n=3)
assert run(seq("WWWWWL"), losses_only)["state"] == "GROWING" and run(seq("WWWWLL"), losses_only)["blocks"][0]["n"] == 6
fav = [sg(i, "W", i // 3, 60 * (i % 3), limit=88) for i in range(6)]
rf = run(fav); assert rf["counted_signals"] == 0 and rf["excluded"]["limit 88c or above, rule not in the favourites class (i, m)"] == 6          # skipped, not counted
favp = lb.Params(88, 95, favourites=True, days_min=2, rarer_min=2, confirm_n=3)
assert run(fav, favp)["counted_signals"] == 6 and favp.block_n == 150 and run(fav, favp)["state"] == "GROWING"
assert run([sg(i, "W", i // 3, 60 * (i % 3), limit=87) for i in range(6)])["counted_signals"] == 6          # 87c is not a favourite
# --- confirmation (j): not enough signals inside its 21 days, then expiry; open results; the next block starts after the expiry time ---
base_block = seq("WWLWLW")                      # block ends at signal 5, t = BASE + 2 DAY + 120
tl = BASE + 1 * DAY + 2 * 60 + 0
tl = max(d["t"] for d in [sg(0, "W", 1, 120)])          # the 6th signal: day 1 (0-based), sec 120
r = run(base_block + [sg(6, "L", 3, 0), sg(7, "W", 4, 0)], now=tl + 10 * DAY)
assert r["blocks"][0]["confirmation"]["state"].startswith("GROWING (2 of 3)") and r["state"].startswith("CONFIRMING")
r = run(base_block + [sg(6, "L", 3, 0), sg(7, "W", 4, 0)], now=tl + 21 * DAY + 1)
assert r["blocks"][0]["confirmation"]["state"].startswith("EXPIRED") and r["state"].startswith("NO_OPEN_BLOCK")
r = run(base_block + [sg(6, "L", 3, 0), sg(7, None, 4, 0)], now=tl + 30 * DAY); assert "WAITING_FOR_RESULTS" in r["state"] and "expiry not yet decided" in r["state"]          # (q) for a confirmation
r = run(base_block + [sg(6, "L", 3, 0), sg(7, "W", 4, 0), sg(8, "L", 5, 0)] , now=NOW); assert r["state"] == "QUALIFIED"
r = run(base_block + [sg(6, "L", 3, 0), sg(7, "W", 4, 0), sg(8, None, 5, 0)], now=NOW); assert "WAITING_FOR_RESULTS" in r["state"]          # a confirmation signal is open
# an expired confirmation: its late signal starts the next block (t)
r = run(base_block + [sg(6, "L", 3, 0), sg(7, "W", 4, 0)] + [sg(20, "W", 30, 0)], now=BASE + 30 * DAY)
assert r["blocks"][0]["confirmation"]["state"].startswith("EXPIRED") and r["blocks"][-1]["first_t"] == BASE + 30 * DAY and r["state"] == "GROWING"
# (t) after QUALIFIED no further block is read, however many signals follow
r = run(seq("WWLWLW") + seq("LWL", day0=2, i0=6) + seq("WWLWLW", day0=5, i0=9)); assert r["state"] == "QUALIFIED" and len(r["blocks"]) == 1
# a confirmation that is exactly W = L passes; L = 0 and W > 0 passes
assert run(seq("WWLWLW") + seq("WLW", day0=2, i0=6))["state"] == "QUALIFIED" and run(seq("WWLWLW") + seq("WWW", day0=2, i0=6))["state"] == "QUALIFIED"
assert run(seq("WWLWLW") + [sg(6, "L", 2, 0), sg(7, "L", 2, 60), sg(8, "V", 2, 120)])["blocks"][0]["confirmation"]["state"] == "FAILED"
# --- T8: the registered constants: 60 signals over 7 days at 9 a day, win rate 40 percent ---
pat = "WLLWL" * 20
sigs = [sg(i, pat[i % len(pat)], i // 9, 60 * (i % 9)) for i in range(63)]
reg = lb.Params(8, 50)
r = lb.read_place(sigs, reg, BASE - 1, NOW)
b8 = r["blocks"][0]
assert b8["n"] == 60 and b8["days"] == 7 and b8["wins"] == 24 and b8["losses"] == 36 and b8["W_cents"] == 24 * 788 and b8["L_cents"] == 36 * 212 and b8["passed"] and r["state"].startswith("CONFIRMING")          # ends at the 60th, not the 63rd
conf = [sg(100 + i, "W" if i % 2 == 0 else "L", 7 + i // 9, 60 * (i % 9)) for i in range(30)]
r = lb.read_place(sigs[:60] + conf, reg, BASE - 1, NOW); assert r["state"] == "QUALIFIED" and r["blocks"][0]["confirmation"]["W_cents"] == 15 * 788 and r["blocks"][0]["confirmation"]["L_cents"] == 15 * 212
r = lb.read_place(sigs[:59], reg, BASE - 1, NOW); assert r["state"] == "GROWING" and r["blocks"][0]["n_so_far"] == 59          # 59 signals: not read
# 60 signals on 6 days only (10 a day): not read until a 7th day
s6 = [sg(i, pat[i % len(pat)], i // 10, 60 * (i % 10)) for i in range(60)]
assert lb.read_place(s6, reg, BASE - 1, NOW)["blocks"][0]["days_so_far"] == 6 and lb.read_place(s6, reg, BASE - 1, NOW)["state"] == "GROWING"
assert lb.read_place(s6 + [sg(99, "W", 6, 0)], reg, BASE - 1, NOW)["blocks"][0]["n"] == 61
# rarer outcome: 60 signals over 7 days but only 9 wins keeps growing; the 10th win ends it
few = ["L"] * 60; 
for k_ in range(9): few[k_ * 6] = "W"
sf = [sg(i, few[i], i // 9, 60 * (i % 9)) for i in range(60)]
assert lb.read_place(sf, reg, BASE - 1, NOW)["state"] == "GROWING"
sf2 = sf + [sg(60, "W", 7, 0)]; assert lb.read_place(sf2, reg, BASE - 1, NOW)["blocks"][0]["n"] == 61 and lb.read_place(sf2, reg, BASE - 1, NOW)["blocks"][0]["wins"] == 10
print("test_lane_block: all checks passed")
