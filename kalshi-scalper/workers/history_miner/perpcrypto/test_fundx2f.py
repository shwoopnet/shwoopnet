"""Hand cases for the FUNDX2-F forward chain (perps_crypto_load_f.py, perps_crypto_run_f.py, fundx2f_events.py, fundx2f_run.py): invented numbers only."""
import collections, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perps_crypto_load_f as L, fundx2f_events as FF, fundx2f_run as XF, fundx2_run as X
H = 3600; F0, F1 = FF.FWD_START, FF.FWD_END
assert (L.SNAP_START, L.DEV_END, L.BTC_START) == (F0, F1, F0)
# (1) forward loader windows: Nov 16 and Dec 15 are outside; a blank funding ticker refuses
iso = lambda t: __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(t))
cnt = collections.Counter()
rows = [{"ts_utc": iso(t), "ticker": "KXBTCPERP", "bid": "1", "ask": "2", "price": "1.5", "reference_price": "1.4", "funding_cap": "0.01"} for t in (F0 - 1, F0, F1 - 1, F1)]
sr = L.snapshot_rows(rows, cnt); assert [r[0] for r in sr["KXBTCPERP"]] == [F0, F1 - 1] and cnt["snapshot row outside the window (dropped)"] == 2
fr = L.funding_rows([{"ticker": "KXETHPERP", "funding_time": iso(t), "funding_rate": "0.1"} for t in (F0 - 1, F0, F1)], cnt); assert [t for t, _ in fr["KXETHPERP"]] == [F0]
try: L.funding_rows([{"ticker": "", "funding_time": iso(F0), "funding_rate": "0.1"}], cnt); raise AssertionError("blank ticker")
except SystemExit: pass
# (2) forward trades from COMMITTED cut points (lower 10, upper 191 at 5 percent; none for SOL)
cell = lambda q: {"lower": 10.0, "upper": 191.0, "search_n": 200, "has_threshold": True}
doc = {"cuts": {"KXBTCPERP": {"5": cell(5), "10": {"lower": 20.0, "upper": 181.0, "search_n": 200, "has_threshold": True}}, "KXETHPERP": {"5": cell(5), "10": cell(10)}, "KXSOLPERP": {"5": {"lower": None, "upper": None, "search_n": 50, "has_threshold": False}}}}
assert FF.cuts_from(doc, "KXBTCPERP", 0.05) == (10.0, 191.0, 200) and FF.cuts_from(doc, "KXSOLPERP", 0.05) is None and FF.cuts_from(doc, "KXXRPPERP", 0.05) is None
rws = [(F0 - 24 * H + k * H, 99.0, 101.0, None, None, None) for k in range(24 + 24 * 12)]
pr = [(F0 + 6 * H + k * 12 * H, 500.0) for k in range(14)]
two = {"KXBTCPERP": rws, "KXETHPERP": rws}; prs = {"KXBTCPERP": pr, "KXETHPERP": pr}
t = FF.fundx2f_trades(two, prs, doc, (0.05, "fade", 8)); assert len(t) == 28 and all(x["trade"]["side"] == -1 for x in t)
assert FF.fundx2f_trades({"KXSOLPERP": rws}, {"KXSOLPERP": pr}, doc, (0.05, "fade", 8)) == []                 # no threshold: no trade
assert FF.fundx2f_trades(two, {"KXBTCPERP": [(F0 - H, 500.0), (F1, 500.0)], "KXETHPERP": []}, doc, (0.05, "fade", 8)) == []   # prints outside the forward window never trade
# (3) gate: 8 hour holds pass at 4.0 a day, 24 hour holds fail (the 12 h prints overlap one position)
g = XF.gate_counts(two, prs, doc)
assert g["0.05|fade|8"]["trades_first_7_days"] == 28 and g["0.05|fade|8"]["passes"] and not g["0.05|fade|24"]["passes"] and len(g) == 8
sc = XF.score(two, prs, doc, g, 7492500)
assert sc["0.05|fade|8"]["all_six"]["n"] == 28 and "bar" in sc["0.05|fade|8"] and sc["0.05|fade|24"].keys() == {"dropped", "rate_a_day"} and sc["_bh"]["m_total"] == 7492500
# (4) refusals: the wrong thresholds file, no allow line, a missing gate file or the wrong m (before any file opens)
d = tempfile.mkdtemp(); th = os.path.join(d, "T.json"); open(th, "w").write("{}")
try: XF.load(th, th, []); raise AssertionError("wrong thresholds")
except SystemExit as e: assert "thresholds" in str(e)
FF.THRESHOLDS_SHA256 = XF.sha(th); L.ALLOW_FILE = os.path.join(d, "A.md"); open(L.ALLOW_FILE, "w").write("x\n")
try: XF.load(th, th, []); raise AssertionError("no allow line")
except SystemExit as e: assert "REFUSED" in str(e)
gp = os.path.join(d, "G.json"); open(gp, "w").write(json.dumps({"cells": g}))
for args in ([os.path.join(d, "none.json"), "00", "7492500"], [gp, "00" * 32, "7492500"], [gp, XF.sha(gp), "6290676" if X.expected_m() == 7492500 else "7492500"]):
    try: XF.run("score", args, {"thresholds": [th], "funding": [th], "snap": []}); raise AssertionError("must refuse")
    except SystemExit as e: assert "REFUSED" in str(e), str(e)
print("fundx2f: ok")
