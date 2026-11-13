"""Test for spxoi1.py (tool 1): INVENTED rows only (SPXOI1_TOOLS_HAND_CASES.md). Run: python3 -B -W ignore test_spxoi1.py"""
import calendar, math, os, sys, time
from email.utils import formatdate
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxoi1 as s
import liveshadow as ls

C = calendar.timegm((2026, 11, 13, 15, 0, 0))          # a close, exchange seconds
def poll(t, no=None, yes=None, close=C):          # a book with NO bids and no YES bids given gets a harmless far YES side (a missing side is no signal)
    if yes is None and no: yes = [(0.15, 20)]
    return {"t": float(t), "recv": float(t), "yes_bids": yes or [], "no_bids": no or [], "close": close}
# --- loader: exchange time from the rolling median offset, row by row ---
def row(recv_s, header_s, ticker="KXINX15M-A", no=None, yes=None, close="2026-11-13T15:00:00Z"):
    r = {"t_recv_ms": None if recv_s is None else recv_s * 1000, "server_date_header": None if header_s is None else formatdate(header_s, usegmt=True), "ticker": ticker, "close_time": close}
    for i, (p, z) in enumerate(no or [], 1): r["no_bid_px_%d" % i], r["no_bid_sz_%d" % i] = p, z
    for i, (p, z) in enumerate(yes or [], 1): r["yes_bid_px_%d" % i], r["yes_bid_sz_%d" % i] = p, z
    return r
B = C - 400          # integer seconds: HTTP dates have whole-second resolution; offsets are set through the fractional receive time
# offsets (header + 0.5 - recv): 0.3, 0.5, 0.1 for rows at B + 0.2, B + 5.0, B + 10.4 -> medians 0.3, 0.4, 0.3
rows = [row(B + 0.2, B), row(B + 5.0, B + 5), row(B + 10.4, B + 10)]
out = s.load_rows(rows)["KXINX15M-A"]
assert [round(p["t"] - p["recv"], 6) for p in out] == [0.3, 0.4, 0.3], [p["t"] - p["recv"] for p in out]
assert out[0]["close"] == C and abs(out[0]["recv"] - (B + 0.2)) < 1e-9
# an unreadable header takes the median of the earlier readable ones and adds none: rows 0.3, (bad), 0.5 -> 0.3, 0.3, median(0.3, 0.5) = 0.4
rows2 = [row(B + 0.2, B), row(B + 5.0, None), row(B + 10.0, B + 10)]
assert [round(p["t"] - p["recv"], 6) for p in s.load_rows(rows2)["KXINX15M-A"]] == [0.3, 0.3, 0.4]
# a row with no readable header and no earlier one has no exchange time (skipped); a row with no receive time is dropped
rows3 = [row(B - 5, None), row(None, B), row(B + 0.2, B)]
assert len(s.load_rows(rows3)["KXINX15M-A"]) == 1
# rows of one receive instant keep the run's order (stable sort) and the offset sees up to the poll's own row: offsets 0.5 then 1.5 -> medians 0.5 then 1.0
rows4 = [row(B + 1.0, B + 1, ticker="KXINX15M-A"), row(B + 1.0, B + 2, ticker="KXINX15M-B")]
l4 = s.load_rows(rows4); assert round(l4["KXINX15M-A"][0]["t"] - l4["KXINX15M-A"][0]["recv"], 6) == 0.5 and round(l4["KXINX15M-B"][0]["t"] - l4["KXINX15M-B"][0]["recv"], 6) == 1.0
rows4r = [rows4[1], rows4[0]]          # the other run order: B's row is first (offset 1.5), A's row sees the median of both (1.0)
l4r = s.load_rows(rows4r); assert round(l4r["KXINX15M-B"][0]["t"] - l4r["KXINX15M-B"][0]["recv"], 6) == 1.5 and round(l4r["KXINX15M-A"][0]["t"] - l4r["KXINX15M-A"][0]["recv"], 6) == 1.0
# the window of 120 rows: offset 1.0 for the first 10 rows and 0.0 after: the last row's median over the LAST 120 is 0.0 (the first 10 fell out), the 10th row's is 1.0
many = [row(B + i + (-0.5 if i < 10 else 0.5), B + i) for i in range(130)]
lm = s.load_rows(many)["KXINX15M-A"]
assert round(lm[-1]["t"] - lm[-1]["recv"], 6) == 0.0 and round(lm[9]["t"] - lm[9]["recv"], 6) == 1.0
# the loader sorts by receive time whatever the run order is (stable): the rows reversed give the same offsets
assert [round(p["t"] - p["recv"], 6) for p in s.load_rows(list(reversed(rows)))["KXINX15M-A"]] == [0.3, 0.4, 0.3]
# only the LAST 120 readable rows count: 65 rows at offset 0.0 then 65 at 1.0: the last row's median over the last 120 (55 zeros, 65 ones) is 1.0, over all 130 it would be 0.5
win = [row(B + i + (0.5 if i < 65 else -0.5), B + i) for i in range(130)]
lw = s.load_rows(win)["KXINX15M-A"]; assert round(lw[-1]["t"] - lw[-1]["recv"], 6) == 1.0
# the REAL NC15 / R6 header (column names only, read from origin/nc-data nc15/2026-11-13/0846/book.csv.gz): an invented file with exactly these columns loads
import gzip, tempfile
HEADER = ("t_send_ms,t_recv_ms,server_date_header,ticker,series,close_time,yes_bid_px_1,yes_bid_px_2,yes_bid_px_3,yes_bid_px_4,yes_bid_px_5,yes_bid_sz_1,yes_bid_sz_2,yes_bid_sz_3,yes_bid_sz_4,yes_bid_sz_5,"
          "no_bid_px_1,no_bid_px_2,no_bid_px_3,no_bid_px_4,no_bid_px_5,no_bid_sz_1,no_bid_sz_2,no_bid_sz_3,no_bid_sz_4,no_bid_sz_5")
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "book.csv.gz")
    import csv as _csv
    def line(recv, hdr, no1, nsz):          # real Date headers contain a comma, so the file is written with the csv module (quoted), as the recorder's is
        return [int(recv * 1000 - 50), int(recv * 1000), formatdate(hdr, usegmt=True), "KXINX15M-INVENTED", "KXINX15M", "2026-11-13T15:00:00Z",
                0.15, "", "", "", "", 20, "", "", "", "", no1, 0.79, "", "", "", nsz, 12, "", "", ""]
    with gzip.open(f, "wt", newline="") as fh:
        w = _csv.writer(fh); fh.write(HEADER + "\n"); w.writerow(line(B + 0.2, B, 0.80, 6)); w.writerow(line(B + 5.0, B + 5, 0.80, 6))
    assert len(HEADER.split(",")) == 26 and len(line(B, B, 0.8, 6)) == 26
    real = s.load_nc15(f)["KXINX15M-INVENTED"]
    assert len(real) == 2 and real[0]["close"] == C and real[0]["no_bids"] == [(0.80, 6.0), (0.79, 12.0)] and real[0]["yes_bids"] == [(0.15, 20.0)], real
    assert abs(real[0]["t"] - real[0]["recv"] - 0.3) < 1e-6 and abs(real[1]["t"] - real[1]["recv"] - 0.4) < 1e-6          # median of the offsets 0.3 and 0.5
# --- book helpers ---
yes_cheap = poll(C - 175, no=[(0.80, 6), (0.79, 6)], yes=[(0.18, 9)])          # YES ask .20 (6) and .21 (6); NO ask .82
assert abs(s.ask_of(yes_cheap, "yes") - 0.20) < 1e-12 and abs(s.ask_of(yes_cheap, "no") - 0.82) < 1e-12 and s.cheaper(yes_cheap)[0] == "yes"
assert s.cheaper(poll(0, no=[(0.50, 3)], yes=[(0.50, 3)]))[0] == "yes"          # tie to YES
assert s.cheaper(poll(0, no=[], yes=[(0.50, 3)])) is None and s.ask_of(poll(0), "yes") is None and s.cheaper(poll(0, no=[(0.5, 3)], yes=[])) is None          # a missing side: no cheaper side
assert abs(s.walked(yes_cheap, "yes") - 0.204) < 1e-12 and s.walked(poll(0, no=[(0.8, 5)]), "yes") is None
assert not s.offers(yes_cheap, "yes", 0.20) and s.offers(yes_cheap, "yes", 0.21)
# --- the rule: T is required; oi_rise exactly T passes, T - 1 does not ---
polls = [poll(C - 181, no=[(0.80, 20)]), poll(C - 180, no=[(0.40, 20)], yes=[(0.45, 20)]), poll(C - 175, no=[(0.80, 20)]), poll(C - 119, no=[(0.80, 20)])]
# poll 0 outside (181 s), poll 1: YES ask .60, NO ask .55: cheaper NO .55 outside the band; poll 2 (175 s): YES ask .20 inside: signal; poll 3 outside (119 s)
r = s.signal(polls, C, 1500, 1000, 500, 0.0); assert r[0] == "signal" and r[1] == 2 and r[2] == "yes" and abs(r[3] - 0.20) < 1e-12 and abs(r[4] - 0.20) < 1e-12, r
r = s.signal(polls, C, 1500, 1000, 500, 0.01); assert abs(r[4] - 0.21) < 1e-12
assert s.signal(polls, C, 1499, 1000, 500, 0.0) == ("no_trade", "oi rise under T") and s.signal(polls, C, 1500, 1000, 500 + 1e-10, 0.0)[0] == "signal"
assert s.signal(polls, C, None, 1000, 500, 0.0) == ("no_data", "no open interest") and s.signal(polls, C, 1500, None, 500, 0.0) == ("no_data", "no open interest")
assert s.signal([polls[0], polls[3]], C, 1500, 1000, 500, 0.0) == ("no_data", "no poll in window")
assert s.signal([polls[1]], C, 1500, 1000, 500, 0.0) == ("no_trade", "cheaper side outside 0.08 to 0.50")
# window edges: 180 s and 120 s count (1e-9); band edges .08 and .50 count, .07 and .51 do not
for dt, ok in ((-180, True), (-120, True), (-180.1, False), (-119.9, False)):
    assert (s.signal([poll(C + dt, no=[(0.80, 20)])], C, 2, 0, 1, 0.0)[0] == "signal") is ok, dt
for ask, ok in ((0.08, True), (0.50, True), (0.07, False), (0.51, False)):
    assert (s.signal([poll(C - 150, no=[(round(1 - ask, 6), 20)], yes=[(0.10, 5)])], C, 2, 0, 1, 0.0)[0] == "signal") is ok, ask
# the first poll that passes the band is the signal (an earlier poll outside the band is skipped), one signal per market
assert s.signal([poll(C - 178, no=[(0.40, 20)], yes=[(0.45, 20)]), poll(C - 170, no=[(0.80, 20)]), poll(C - 160, no=[(0.85, 20)])], C, 2, 0, 1, 0.0)[1] == 1
# --- fill check: the NEXT poll within 6 s ---
sp = [poll(C - 175, no=[(0.80, 6), (0.79, 6)]), poll(C - 170, no=[(0.80, 6), (0.79, 6)])]
assert s.fill_check(sp, 0, "yes", 0.21)[0] == "filled" and abs(s.fill_check(sp, 0, "yes", 0.21)[1] - 0.204) < 1e-12
assert s.fill_check(sp, 0, "yes", 0.20)[0] == "miss"                                                        # only 6 at or under .20
assert s.fill_check([sp[0], poll(C - 175 + 6.0, no=[(0.80, 12)])], 0, "yes", 0.21)[0] == "filled"          # exactly 6 s counts
assert s.fill_check([sp[0], poll(C - 175 + 6.1, no=[(0.80, 12)])], 0, "yes", 0.21)[0] == "not_fill_checked"
assert s.fill_check([sp[0]], 0, "yes", 0.21)[0] == "not_fill_checked"
worse = [sp[0], poll(C - 170, no=[(0.78, 10)])]          # second poll walks .22 at limit .22: the HIGHER walked price is the fill
fw = s.fill_check(worse, 0, "yes", 0.22); assert fw[0] == "filled" and abs(fw[1] - 0.22) < 1e-9
assert s.fill_check([sp[0], poll(C - 170, no=[(0.80, 4)])], 0, "yes", 0.21)[0] == "miss"          # the second poll offers only 4
# --- fee and cents (g) ---
assert s.fee_up_order(0.50) == 0.18 and s.fee_up_order(0.15) == 0.09 and s.fee_up_order(0.90) == 0.07 and s.fee_up_order(0.20) == 0.12
assert s.cash_cents(0.20, "yes", "yes") == 788 and s.cash_cents(0.20, "yes", "no") == -212 and s.cash_cents(0.20, "no", "no") == 788 and s.cash_cents(0.20, "yes", "void") == -12
assert s.cash_cents(0.204, "yes", "yes") == 784          # 10 x .796 - .12 = 7.84
assert s.cash_cents(0.2045, "yes", "yes") == 783 and s.cash_cents(0.2045, "yes", "no") == -217          # 783.5 floors to 783 and -216.5 floors to -217 (the worse result, lane (g)); rounding would give 784 and -216
assert math.floor(100 * 6.754 + 1e-6) == 675 and math.floor(100 * -6.754 + 1e-6) == -676          # the (g) rounding toward the worse result
# --- the shadow dict and liveshadow.compare ---
polls_t = {"KXINX15M-A": [poll(C - 175, no=[(0.80, 20)], close=C)], "KXINX15M-B": [poll(C - 175, no=[(0.80, 20)], close=C)], "KXINX15M-C": [poll(C - 300, no=[(0.80, 20)], close=C)],
           "KXINX15M-D": [poll(C - 175, no=[(0.40, 20)], yes=[(0.45, 20)], close=C)], "KXINX15M-E": [poll(C - 175, close=None)]}
oi = lambda a, b: [{"ts": C - 360, "oi": a}, {"ts": C - 180, "oi": b}]
cs = {"KXINX15M-A": oi(1000, 1600), "KXINX15M-B": oi(1000, 1100), "KXINX15M-C": oi(1000, 1600), "KXINX15M-D": oi(1000, 1600)}
sh = s.spxoi1_shadow(polls_t, cs, 500, 0.0)
assert sh["KXINX15M-A"][:3] == ("trade", "yes", sh["KXINX15M-A"][2]) and abs(sh["KXINX15M-A"][2] - 0.20) < 1e-12 and sh["KXINX15M-A"][3]["limit"] == sh["KXINX15M-A"][2]
assert sh["KXINX15M-B"] == ("no_trade", "oi rise under T") and sh["KXINX15M-C"] == ("no_data", "no poll in window") and sh["KXINX15M-D"] == ("no_trade", "cheaper side outside 0.08 to 0.50") and sh["KXINX15M-E"] == ("no_data", "no close time")
live = [{"ticker": "KXINX15M-A", "side": "yes", "count": 10, "orderedCount": 10, "fill": 0.21, "sentAtMs": (C - 174) * 1000}]
cmp_ = ls.compare(live, list(polls_t), sh, {"KXINX15M-A": [poll(C - 175, no=[(0.80, 20)])]})
assert cmp_["agree"] == 1 and cmp_["codes"]["AGREE"] == 1 and abs(cmp_["fill_gap"]["mean_cents"] - 1.0) < 1e-9, cmp_
# T has no default anywhere
import inspect
assert inspect.signature(s.signal).parameters["T"].default is inspect.Parameter.empty and inspect.signature(s.signal).parameters["limit_add"].default is inspect.Parameter.empty
assert inspect.signature(s.spxoi1_shadow).parameters["T"].default is inspect.Parameter.empty
print("test_spxoi1: all checks passed")
