"""Test for place_report.py: INVENTED rows only (OICORE_ADAPTER_AND_PLACE_REPORT_HAND_CASES.md item 2). Run: python3 -B -W ignore test_place_report.py"""
import calendar, os, sys, tempfile, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import place_report as pr
import lane_block as lb

T = lambda d, h, m: calendar.timegm((2026, 11, d, h, m, 0))
def poll(t, close, yes, no): return {"t": float(t), "recv": float(t), "yes_bids": yes, "no_bids": no, "close": close}
def win(tk, close, yes, no, nxt_dt=5.0, nxt_no=None, early=None):
    """signal poll exactly at D = close - 600; the next poll nxt_dt s later with the same book unless nxt_no is given; `early` adds an earlier poll with another book."""
    D = close - 600
    ps = []
    if early: ps.append(poll(D - 8, close, *early))
    ps.append(poll(D, close, yes, no))
    ps.append(poll(D + nxt_dt, close, yes, no if nxt_no is None else nxt_no))
    return tk, ps
# book sizes (YES bids, NO bids): imb5 = (YES - NO) / (YES + NO); a YES buy meets the NO bids (ask = 1 - best NO bid), a NO buy meets the YES bids
W = dict([
    win("KXAAA15M-W1", T(13, 18, 15), [(0.40, 30), (0.39, 10)], [(0.70, 10)], early=([(0.40, 5)], [(0.70, 50)])),          # +0.60, YES ask .30, filled -> COUNTED (the earlier poll at D - 8 is another book: the last poll at or before D wins)
    win("KXAAA15M-W2", T(13, 18, 30), [(0.40, 35)], [(0.70, 15)]),                                                        # +0.40: not in the cell
    win("KXAAA15M-W3", T(13, 18, 45), [(0.05, 10)], [(0.40, 40)]),                                                        # -0.60, NO ask .95: outside the band
    win("KXAAA15M-W4", T(14, 18, 15), [(0.75, 15)], [(0.30, 85)], nxt_dt=8.0),                                            # -0.70, NO ask .25, next poll 8 s later: not fill-checked
    win("KXAAA15M-W5", T(14, 18, 30), [(0.40, 90)], [(0.80, 10)], nxt_no=[(0.80, 4)]),                                    # +0.80, YES ask .20, the next poll offers only 4: miss
    win("KXAAA15M-W6", T(14, 18, 45), [(0.40, 31)], [(0.12, 9)]),                                                         # +0.55, YES ask .88, limit .89 >= 88c: skipped
    win("KXAAA15M-W7", T(14, 19, 0), [(0.40, 190)], [(0.60, 10)]),                                                        # +0.90, YES ask .40, filled -> COUNTED
    win("KXAAA15M-W8", T(15, 18, 0), [(0.40, 190)], [(0.60, 10)]),                                                        # closes on day 3: held out
    win("KXZZZ15M-X1", T(13, 18, 15), [(0.40, 190)], [(0.60, 10)]),                                                       # another series: ignored
])
S = lambda **kw: dict(dict(name="depth-AAA", kind="depth", series="KXAAA15M", start_ts=T(13, 0, 0), heldout_first=T(15, 0, 0), log="NC15"), **kw)
r = pr.report_place(S(), W, {})
assert r["per_day"]["2026-11-13"] == {"windows_examined": 3, "signals_counted": 1, "misses": 0, "not_fill_checked": 0, "skipped_88c": 0}, r["per_day"]
assert r["per_day"]["2026-11-14"] == {"windows_examined": 4, "signals_counted": 1, "misses": 1, "not_fill_checked": 1, "skipped_88c": 1}, r["per_day"]
assert r["held_out_windows_not_read"] == 1 and r["days_with_data"] == 2 and r["signals_counted"] == 2 and abs(r["signals_per_day"] - 1.0) < 1e-12 and r["days_to_a_60_signal_block"] == 60 and set(r["per_day"]) == {"2026-11-13", "2026-11-14"}
assert r["windows_without_a_signal_poll"] == 0
# outcomes and prices never appear: the output keys are counts, days and rates
def keys(x, acc):
    if isinstance(x, dict):
        for k_, v in x.items(): acc.add(k_); keys(v, acc)
    elif isinstance(x, list):
        for v in x: keys(v, acc)
    return acc
ks = keys(r, set()); assert not any(w in " ".join(ks).lower() for w in ("price", "ask", "result", "outcome", "pnl", "cents", "fill_price", "limit")) and "KXAAA15M-W1" not in json.dumps(r)
# the start time (l): a start at day 2 00:00 Central drops day 1 (signals AND data days)
r2 = pr.report_place(S(start_ts=T(14, 6, 0)), W, {})          # Central midnight of Nov 14 is 06:00Z
assert set(r2["per_day"]) == {"2026-11-14"} and r2["signals_counted"] == 1 and r2["days_with_data"] == 1 and r2["days_to_a_60_signal_block"] == 60
# no held-out date: the day-3 window is examined and counted
r3 = pr.report_place(S(heldout_first=None), W, {}); assert r3["held_out_windows_not_read"] == 0 and r3["signals_counted"] == 3 and "2026-11-15" in r3["per_day"] and r3["days_with_data"] == 3
# a high rate still needs 7 days: 10 signals a day gives 7 days, not 6
assert max(pr.BLOCK_DAYS, int(__import__("math").ceil(60 / 10.0))) == 7
fast = {}
for dd in range(13, 20):
    for j in range(10):
        tk, ps = win("KXAAA15M-F%d%d" % (dd, j), T(dd, 18, 0) + 900 * j, [(0.40, 190)], [(0.60, 10)]); fast[tk] = ps
rf = pr.report_place(S(heldout_first=None), fast, {}); assert rf["signals_counted"] == 70 and rf["days_with_data"] == 7 and abs(rf["signals_per_day"] - 10.0) < 1e-12 and rf["days_to_a_60_signal_block"] == 7
slow = {}
for dd in range(13, 20):
    tk, ps = win("KXAAA15M-S%d" % dd, T(dd, 18, 0), [(0.40, 190)], [(0.60, 10)]); slow[tk] = ps
rs = pr.report_place(S(heldout_first=None), slow, {}); assert rs["signals_per_day"] == 1.0 and rs["days_to_a_60_signal_block"] == 60
# the five levels are SUMMED: three YES levels of 10 against one NO level of 10 is (30 - 10) / 40 = .50, in the cell; the top level alone would give 0
assert pr.depth_signal([poll(T(13, 18, 0) - 600, T(13, 18, 0), [(0.40, 10), (0.39, 10), (0.38, 10)], [(0.70, 10)])], T(13, 18, 0))[0] == "signal"
assert pr.depth_signal([poll(T(13, 18, 0) - 600, T(13, 18, 0), [(0.40, 25)], [(0.70, 5), (0.69, 5), (0.68, 5), (0.67, 5), (0.66, 5), (0.65, 500)])], T(13, 18, 0))[1] == "not in the cell"          # only five levels count: (25 - 25) / 50 = 0; a sixth level of 500 is ignored
# a rate of 0.6 a day: 60 / 0.6 is 100.00000000000001 in floats but the block takes 100 days, not 101
five = {}
for dd, sigk in zip(range(13, 18), (True, False, True, False, True)):
    tk, ps = win("KXAAA15M-R%d" % dd, T(dd, 18, 0), [(0.40, 190)], [(0.60, 10)] if sigk else [(0.70, 120)]); five[tk] = ps          # a quiet day: not in the cell
rr = pr.report_place(S(heldout_first=None), five, {}); assert rr["days_with_data"] == 5 and rr["signals_counted"] == 3 and abs(rr["signals_per_day"] - 0.6) < 1e-12 and rr["days_to_a_60_signal_block"] == 100, rr
# 3 signals in 11 days: 60 / (3 / 11) is 220.00000000000003 in floats; the block takes 220 days, not 221
eleven = {}
for dd in range(13, 24):
    tk, ps = win("KXAAA15M-Q%d" % dd, T(dd, 18, 0), [(0.40, 190)], [(0.60, 10)] if dd in (13, 17, 21) else [(0.70, 120)]); eleven[tk] = ps
re_ = pr.report_place(S(heldout_first=None), eleven, {}); assert re_["days_with_data"] == 11 and re_["signals_counted"] == 3 and re_["days_to_a_60_signal_block"] == 220, re_
# depth edges: |imb5| exactly .50 is in the cell; the band .10 and .90 are inclusive; D and the 10 s age
assert pr.depth_signal([poll(T(13, 18, 0) - 600, T(13, 18, 0), [(0.40, 30)], [(0.70, 10)])], T(13, 18, 0))[0] == "signal"          # (30 - 10) / 40 = .50
assert pr.depth_signal([poll(T(13, 18, 0) - 600, T(13, 18, 0), [(0.40, 29)], [(0.70, 10)])], T(13, 18, 0))[1] == "not in the cell"          # (29 - 10) / 39 = .487
assert pr.depth_signal([poll(T(13, 18, 0) - 600, T(13, 18, 0), [(0.40, 25)], [(0.70, 10)])], T(13, 18, 0))[1] == "not in the cell"          # (25 - 10) / 35 = .43
for ask, ok in ((0.10, True), (0.90, True), (0.09, False), (0.91, False)):
    got = pr.depth_signal([poll(T(13, 18, 0) - 600, T(13, 18, 0), [(0.40, 90)], [(round(1 - ask, 6), 10)])], T(13, 18, 0))
    assert (got[0] == "signal") is ok, ask
D0 = T(13, 18, 0) - 600
for dt, ok in ((0.0, True), (-10.0, True), (-10.1, False), (0.1, False)):
    assert (pr.depth_signal([poll(D0 + dt, T(13, 18, 0), [(0.40, 90)], [(0.60, 10)])], T(13, 18, 0))[0] == "signal") is ok, dt
# the 88c line: a signal with limit 87c (ask .86 + .01) counts, 88c (ask .87 + .01) is skipped
def one(ask):
    tk, ps = win("KXAAA15M-E1", T(13, 18, 0), [(0.40, 90)], [(round(1 - ask, 6), 10)]); return pr.report_place(S(heldout_first=None), {tk: ps}, {})
assert one(0.86)["signals_counted"] == 1 and one(0.87)["signals_counted"] == 0 and one(0.87)["per_day"]["2026-11-13"]["skipped_88c"] == 1
# --- the oicore kind on an invented market, with open interest ---
CB = T(13, 18, 0)
bk = {"KXBBB15M-1": [poll(CB - 175, CB, [(0.15, 20)], [(0.88, 20)]), poll(CB - 171, CB, [(0.15, 20)], [(0.88, 20)])], "KXBBB15M-2": [poll(CB - 175, CB, [(0.15, 20)], [(0.55, 20)]), poll(CB - 171, CB, [(0.15, 20)], [(0.55, 20)])]}
cs = {"KXBBB15M-1": [{"ts": CB - 360, "oi": 1000}, {"ts": CB - 180, "oi": 2000}], "KXBBB15M-2": [{"ts": CB - 360, "oi": 1000}, {"ts": CB - 180, "oi": 2000}]}
O = dict(name="oicore-BBB", kind="oicore", series="KXBBB15M", start_ts=T(13, 0, 0), heldout_first=None, log="R6", band_lo=0.10, band_hi=0.40, T=1000, limit_add=0.0)
ro = pr.report_place(O, bk, cs)
assert ro["per_day"]["2026-11-13"] == {"windows_examined": 2, "signals_counted": 1, "misses": 0, "not_fill_checked": 0, "skipped_88c": 0} and ro["signals_counted"] == 1 and ro["days_with_data"] == 1
assert pr.report_place(dict(O, log="NC15"), bk, cs)["signals_counted"] == 1 and pr.report_place(dict(O, T=1001), bk, cs)["signals_counted"] == 0          # the rise 1,000 is exactly T: T + 1 stops it
slowbk = {"KXBBB15M-1": [bk["KXBBB15M-1"][0], poll(CB - 169, CB, [(0.15, 20)], [(0.88, 20)])]}          # next poll 6 s later: R6 not fill-checked, NC15 filled
assert pr.report_place(O, slowbk, cs)["per_day"]["2026-11-13"]["not_fill_checked"] == 1 and pr.report_place(dict(O, log="NC15"), slowbk, cs)["signals_counted"] == 1
# a cfrti place is named as not built; a missing field or a bad log is refused
assert pr.report_place(dict(name="cfrti", kind="cfrti", series="KXBTC15M", start_ts=0, heldout_first=None, log="R6"), {}, {})["state"].startswith("not built")
for bad in (dict(O, T=None) if False else {k_: v for k_, v in O.items() if k_ != "T"}, {k_: v for k_, v in O.items() if k_ != "heldout_first"}, dict(O, log="nc15")):
    try: pr.report_place(bad, bk, cs); assert 0
    except ValueError: pass
# guard: a HELDOUT_ folder is refused by the loader
with tempfile.TemporaryDirectory() as d:
    hd = os.path.join(d, "HELDOUT_x"); os.makedirs(hd)
    f = os.path.join(hd, "book.csv.gz"); gzip.open(f, "wt").write("t_send_ms\n")
    try: pr.load_books([f]); assert 0
    except SystemExit as e: assert "HELDOUT_" in str(e)
# the whole report wraps the places
assert len(pr.report([S(), O], dict(W, **bk), cs)["places"]) == 2
print("test_place_report: all checks passed")
