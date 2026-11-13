"""Synthetic test for spxfv1.py (Testing Desk build 1). MADE-UP data only: invented bars, quotes and results; no Kalshi, no Databento, no real file.
Hand-worked expectations are in the comments. Run: python3 -W ignore test_spxfv1.py"""
import calendar, csv, gzip, json, math, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxfv1 as s

# --- pure pieces ---
assert abs(s.phi(0) - 0.5) < 1e-15 and abs(s.phi(1) - 0.8413447460685429) < 1e-12
# decide(): YES cheap, edge exactly 5c passes through the 1e-9 tolerance, 4.9c does not
r, why = s.decide(0.20, 0.22, 0.27); assert r[0] == "yes" and abs(r[1] - 0.22) < 1e-12
r, why = s.decide(0.20, 0.22, 0.269); assert r is None and why == "edge under 5c"
# NO cheap: yes_bid .72 -> NO ask .28 ; chance(NO) = 1 - .67 = .33 ; edge .05 exactly
r, why = s.decide(0.72, 0.73, 0.67); assert r[0] == "no" and abs(r[1] - 0.28) < 1e-12 and abs(r[2] - 0.33) < 1e-12
# spread 3c passes, 4c fails; band edges 0.30 in, 0.31 out, 0.05 in, 0.04 out
assert s.decide(0.18, 0.21, 0.9)[0] is not None and s.decide(0.18, 0.22, 0.9)[0] is None
assert s.decide(0.29, 0.30, 0.9)[0] is not None and s.decide(0.30, 0.31, 0.9)[0] is None
assert s.decide(0.04, 0.05, 0.9)[0] is not None and s.decide(0.03, 0.04, 0.9)[0] is None
assert s.decide(None, 0.2, 0.9)[0] is None
assert s.decide(0.91, 0.90, 0.9)[1] == "crossed or locked quote" and s.decide(0.90, 0.90, 0.9)[1] == "crossed or locked quote"          # crossed and locked
assert s.decide(0.89, 0.91, 0.9)[0] is None and s.decide(0.89, 0.91, 0.9)[1] != "crossed or locked quote"
# --- futures_signal: alternating changes +a / -a: sd_1m = a*sqrt(10/9), sd = sd_1m*sqrt(119/60) ---
A = 0.0005; SD = A * math.sqrt(10 / 9) * math.sqrt(119 / 60)
def mk_bars(C, z, iid=1, open_iid=None, drop_open=False, drop=()):
    b = {}
    for j in range(11):
        if j not in drop: b[C - 180 - 60 * j] = (iid, 100.0 if j % 2 == 0 else 100.0 * math.exp(A))
    if not drop_open: b[C - 960] = (iid if open_iid is None else open_iid, 100.0 * math.exp(-z * SD))
    return b
C0 = calendar.timegm((2026, 11, 5, 15, 0, 0))
why, sd, z = s.futures_signal(C0, mk_bars(C0, 1.0)); assert why is None and abs(sd - SD) < 1e-12 and abs(z - 1.0) < 1e-9, (why, sd, z)
assert s.futures_signal(C0, mk_bars(C0, 1.0, open_iid=2))[0] == "roll (instrument id differs)"
assert s.futures_signal(C0, mk_bars(C0, 1.0, drop_open=True))[0] == "no F_open bar"
assert s.futures_signal(C0, mk_bars(C0, 1.0, drop=(0,)))[0] == "no F_now bar"
# 5 bars missing in the middle of changes: 11 bars -> drop j=1,3,5,7,9 leaves 6 bars, no consecutive pairs -> 0 changes: dropped
assert s.futures_signal(C0, mk_bars(C0, 1.0, drop=(1, 3, 5, 7, 9)))[0].startswith("fewer than 6")
# exactly 6 changes present passes: drop the two oldest bars (j=9,10) leaves 9 bars = 8 changes; drop j=10..? keep bars j=0..6 -> 6 changes
b = mk_bars(C0, 1.0, drop=(7, 8, 9, 10)); assert s.futures_signal(C0, b)[0] is None
b = mk_bars(C0, 1.0, drop=(6, 7, 8, 9, 10)); assert s.futures_signal(C0, b)[0].startswith("fewer than 6")          # 5 changes
flat = {C0 - 180 - 60 * j: (1, 100.0) for j in range(11)}; flat[C0 - 960] = (1, 100.0)
assert s.futures_signal(C0, flat)[0] == "sd zero"
mixed = mk_bars(C0, 1.0)
for j in (1, 2, 3, 4, 5): mixed[C0 - 180 - 60 * j] = (2, mixed[C0 - 180 - 60 * j][1])          # five bars on another instrument id: only 4 pairs left on F_now's id
assert s.futures_signal(C0, mixed)[0].startswith("fewer than 6")
mixed = mk_bars(C0, 1.0); mixed[C0 - 180 - 60 * 3] = (2, mixed[C0 - 180 - 60 * 3][1]); assert s.futures_signal(C0, mixed)[0] is None          # one bar: 8 pairs left
try: s.build({"t": {"series": "KXINX15M", "close": C0, "result": "", "event": "e"}}, {}, {}); assert 0
except SystemExit as e: assert "empty result" in str(e)
amb = mk_bars(C0, 1.0); amb[C0 - 180] = s.AMBIG; assert s.futures_signal(C0, amb)[0] == "ambiguous bar"
try: s.build({"t": {"series": "KXINX15M", "close": C0, "result": "yes", "event": "e"}}, {"t": [{"ts": C0 - 120, "bid": .9, "ask": .91}]}, amb); assert 0
except SystemExit as e: assert "STOP" in str(e) and "window t" in str(e) and "ts_event" in str(e)

# --- end to end on an invented run layout ---
def iso(ts): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
def mkrun(d, bodies):
    os.makedirs(d); rows = []
    for i, (rid, body) in enumerate(bodies):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "page": 1, "status": 200, "file": f})
    json.dump({"job": {}, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))
def cs(ts, bid, ask): return {"end_period_ts": ts, "yes_bid": {"close_dollars": "%.4f" % bid}, "yes_ask": {"close_dollars": "%.4f" % ask}, "volume_fp": "1.00"}
T = lambda h, m, d=(2026, 11, 5): calendar.timegm(d + (h, m, 0))
# (name, close, z, bid, ask, result, extra)
W = [("W1", T(15, 0), 1.0, .90, .91, "no", {}),          # NO ask .10, chance(NO) .158655, edge .0587: trade NO, wins
     ("W2", T(15, 15), -1.0, .09, .10, "no", {}),        # YES ask .10, chance .158655: trade YES, loses
     ("W3", T(15, 30), 1.0, .90, .91, "void", {}),       # same as W1, void: price refunded, fee kept
     ("W4", T(15, 45), 0.5, .70, .71, "yes", {}),        # NO ask .30, chance .3085, edge .0085: no trade
     ("W5", T(16, 0), 1.0, .90, .91, "no", {"drop_open": True}),      # no F_open bar
     ("W6", T(16, 15), 1.0, .90, .91, "no", {"open_iid": 2}),         # roll
     ("W7", T(16, 30), 1.0, .90, .91, "no", {"nocandle": True}),      # no decision candle
     ("W8", T(16, 45), 1.0, .90, .94, "no", {}),         # YES spread 4c
     ("W9", T(17, 0), 1.0, .49, .51, "yes", {}),         # tie (YES ask .51 = NO ask .51), counted, ask outside the band: no trade
     ("W10", T(17, 15), 1.0, .91, .90, "no", {}),        # crossed quote: no quote, counted
     ("W11", T(15, 0, (2026, 12, 1)), 1.0, .90, .91, "no", {}),         # closes on the held-out start: never read in dev
     ("X1", T(15, 0, (2026, 11, 6)), 1.0, .90, .91, "no", {"series": "KXBTC15M"})]       # another series: ignored entirely
with tempfile.TemporaryDirectory() as t:
    mrows, crows, bars = [], [], {}
    for name, C, z, bid, ask, res, ex in W:
        ser = ex.get("series", "KXINX15M"); tk = "%s-%s" % (ser, name); ev = "%s-EV%s" % (ser, name)
        mrows.append({"ticker": tk, "event_ticker": ev, "open_time": iso(C - 900), "close_time": iso(C), "result": res, "strike_type": "greater_or_equal", "floor_strike": 5000.0, "volume_fp": "5.00"})
        if not ex.get("nocandle"): crows.append({"market_ticker": tk, "candlesticks": [cs(C - 120, bid, ask), cs(C - 180, 0.5, 0.52)]})
        if "series" not in ex: bars.update(mk_bars(C, z, 1, ex.get("open_iid"), ex.get("drop_open", False)))
    lists, cands = os.path.join(t, "lists"), os.path.join(t, "cands")
    mkrun(lists, [("L1", {"markets": mrows})]); mkrun(cands, [("C1", {"markets": crows})])
    es = os.path.join(t, "es.csv")
    with open(es, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["ts_event", "rtype", "publisher_id", "instrument_id", "open", "high", "low", "close", "volume"])
        for ts in sorted(bars):
            iid, c = bars[ts]; w.writerow([iso(ts).replace("Z", ".000000000Z"), 33, 1, iid, c, c, c, c, 10])
    o = s.dev_read([lists], [cands], es)
    g = o["gate0_counts"]
    assert g["windows_listed"] == 11 and g["ties_yes_ask_equals_no_ask"] == 1 and g["crossed or locked quote"] == 1 and g["cheap side outside 0.05 to 0.30"] == 1 and g["not_in_range_not_read"] == 1 and g["traded"] == 3 and g["void"] == 1, g
    assert g["edge under 5c"] == 1 and g["spread above 3c"] == 1 and g["no F_open bar"] == 1 and g["roll (instrument id differs)"] == 1 and g["no_decision_candle"] == 1 and g["no_trade_signal"] == 4, g
    f = lambda p: 0.07 * p * (1 - p)
    unr = [0.9 - f(0.1), -0.1 - f(0.1), -f(0.1)]          # information only: 0.8937, -0.1063, -0.0063
    gov = o["GOVERNING_fee_rounded_up_per_order"]
    assert o["traded"] == 3 and gov["net"] == round(0.89 - 0.11 - 0.01, 4) == 0.77 and gov["pf"] == round(0.89 / 0.12, 3) == 7.417 and gov["mean"] == round(0.77 / 3, 5), gov
    inf = o["INFORMATION_ONLY_unrounded_fee"]; assert abs(inf["net"] - round(sum(unr), 4)) < 1e-9 and inf["pf"] == round(unr[0] / (-unr[1] - unr[2]), 3) == 7.937, inf
    assert o["scorekit_governing"]["all"] == gov and o["constants"]["tolerance"] == 1e-9 and "rounded UP" in o["constants"]["fee_governing"] and list(o)[0] == "constants"
    assert abs(o["win_rate"] - 0.3333) < 1e-9 and abs(o["mean_price_paid"] - 0.1) < 1e-9
    th = o["date_thirds_governing"]; assert [x["n"] for x in th] == [1, 1, 1] and [x["net"] for x in th] == [0.89, -0.11, -0.01], th          # closes 15:00, 15:15, 15:30
    assert o["kill_flags_read_governing_figure"]["fewer_than_150_traded"] and not o["kill_flags_read_governing_figure"]["cash_pf_under_1_at_n_100_plus"]
    assert o["scorekit_governing"]["label"] == "no evidence at n = 3", o["scorekit_governing"]["label"]
    assert "bar" not in json.dumps(o["gate0_counts"]).lower().replace("no f_open bar", "").replace("no f_now bar", "")
    # held-out: refused before READ_DATE, whatever the files hold
    try: s.heldout_read("nomarker", [lists], [cands], es, now=s.READ_DATE - 1); assert 0
    except SystemExit as e: assert "READ_DATE" in str(e)
    mk = os.path.join(t, "REG.md"); open(mk, "w").write("x\nREAD-ONCE MARKER: NOT READ\n")
    ho = s.heldout_read(mk, [lists], [cands], es, now=s.READ_DATE + 1)
    assert ho["NOT_ENOUGH_DATA"].startswith("1 traded") and "figure" in ho["NOT_ENOUGH_DATA"] and ho["gate0_counts"]["traded"] == 1, ho
    open(mk, "w").write("READ-ONCE MARKER: READ ON 2027-02-27, commit abc\n")
    try: s.heldout_read(mk, [lists], [cands], es, now=s.READ_DATE + 1); assert 0
    except RuntimeError as e: assert "already read" in str(e)
    # a HELDOUT_ folder is refused by the guard
    hl = os.path.join(t, "HELDOUT_x"); os.makedirs(hl)
    try: s.dev_read([hl], [cands], es); assert 0
    except SystemExit as e: assert "HELDOUT_" in str(e)
print("test_spxfv1: all checks passed")
