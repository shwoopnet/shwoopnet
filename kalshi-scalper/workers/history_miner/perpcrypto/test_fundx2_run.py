"""Hand cases for fundx2_run.py: invented numbers only, no real data and no file loading."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perps_crypto_load as L, fundx2_events as F, fundx2_run as X
H = 3600; S0 = L.SNAP_START
# (1) BTC rows: candle rows before 2026-10-21, snapshot rows from then; candle rows after 10-21 are not used
out = {"snapshots": {"KXBTCPERP": [(S0, 1.0, 2.0, 1.5, 1.4, 0.01), (S0 + H, 1.0, 2.0, 1.5, 1.4, 0.01)], "KXETHPERP": [(S0, 5.0, 6.0, 5.5, 5.4, 0.01)]},
       "btc": [(S0 - 2 * H, 9.0, 10.0, None, None, None), (S0 - H, 9.0, 10.0, None, None, None), (S0, 99.0, 100.0, None, None, None)]}
rb = X.build_rows(out)
assert [r[0] for r in rb["KXBTCPERP"]] == [S0 - 2 * H, S0 - H, S0, S0 + H] and rb["KXBTCPERP"][2][1] == 1.0     # the candle at S0 (99/100) is dropped for the snapshot (1/2)
assert list(rb) == ["KXBTCPERP", "KXETHPERP"]
# (2) gate counts: 14 extreme VALIDATE prints 12 h apart in the first 7 days, two names with the same rows
sp = [(F.SEARCH_START + 28800 * i, (i + 1) / 1000.0) for i in range(200)]
pr = sp + [(S0 + 6 * H + k * 12 * H, 0.5) for k in range(14)]
rows = [(S0 - 24 * H + k * H, 99.0, 101.0, None, None, None) for k in range(24 + 24 * 12)]
R2 = {"KXBTCPERP": rows, "KXETHPERP": rows}; P2 = {"KXBTCPERP": pr, "KXETHPERP": pr}
g = X.gate_counts(R2, P2)
assert g["0.05|fade|8"]["trades_first_7_days"] == 28 and abs(g["0.05|fade|8"]["rate_a_day"] - 4.0) < 1e-9 and g["0.05|fade|8"]["passes"] is True
assert g["0.05|fade|24"]["trades_first_7_days"] == 10 and g["0.05|fade|24"]["passes"] is False          # the 12 h prints overlap the 24 h hold: one position per ticker
assert g["0.1|follow|8"]["passes"] is True and len(g) == 8
# (3) score: only passing cells print outcomes; the dropped ones say counts only
sc = X.score(R2, P2, g, 6290676)
assert "all_six" in sc["0.05|fade|8"] and "btc_apart" in sc["0.05|fade|8"] and "other_five" in sc["0.05|fade|8"] and sc["0.05|fade|8"]["all_six"]["n"] == 28
assert sc["0.05|fade|24"].keys() == {"dropped", "rate_a_day"} and "outcomes not read" in sc["0.05|fade|24"]["dropped"]
assert sc["0.05|fade|8"]["n_by_ticker"] == {"KXBTCPERP": 14, "KXETHPERP": 14}
# (4) score refuses without the committed gate file or with a wrong sha, before any file is opened
d = tempfile.mkdtemp(); gp = os.path.join(d, "G.json"); open(gp, "w").write(json.dumps({"cells": g}))
for args in ([os.path.join(d, "none.json"), "00"], [gp, "00" * 32]):
    try: X.run("score", args + ["6290676"], {"funding": ["x"], "snap": [], "btc": ["x"]}); raise AssertionError("must refuse")
    except SystemExit as e: assert "gate file" in str(e), str(e)
# (5) no allow line: the loader step refuses (no files exist either way)
L.ALLOW_FILE = os.path.join(d, "A.md"); open(L.ALLOW_FILE, "w").write("x\n")
f = os.path.join(d, "f.csv.gz"); open(f, "wb").write(b"x")
try: X.load(f, [], d); raise AssertionError("must refuse")
except (SystemExit, OSError) as e: pass
assert any("many cuts are 0" in h for h in X.HEADER) and any("regime shift" in h for h in X.HEADER) and any("APART" in h for h in X.HEADER)
# (6) day-clustered z and p, BH, the bar flags, and the m refusal
import math, time
mk = lambda day, r: {"ticker": "KXBTCPERP", "funding": 0.0, "trade": {"side": 1, "entry": 1.0, "exit": 1.0 + r + 0.0024 + 0.0004, "adverse": 0.0, "entry_ts": day * 86400, "exit_ts": day * 86400 + 3600}}
# net = r + 0.0024 + 0.0004 - 2 fee - 2 haircut = r  (fee 0.0012, haircut 0.0002)
_net = X.E.net; X.E.net = lambda trd, fee, hc, funding=0.0: trd["exit"] - trd["entry"]            # exact arithmetic for the zero-variance case only
tr = [{"ticker": "KXBTCPERP", "funding": 0.0, "trade": {"entry": 1.0, "exit": 1.5, "entry_ts": d * 86400}} for d in (1, 1, 2, 2)]
st = X.cluster_stats(tr); X.E.net = _net
assert st["mean_return"] == 0.5 and st["n"] == 4 and st["trade_days"] == 2 and st["z"] is None and st["p"] == 0.0          # every day sum of (r - mu) is exactly 0: no variance, z undefined, p 0 for a positive mean
tr2 = [mk(d, r) for d, r in ((1, 0.01), (1, 0.01), (2, 0.03), (2, 0.03))]
s2 = X.cluster_stats(tr2); mu2 = 0.02                                                   # day sums of (r-mu): -0.02, +0.02 -> V = 0.0008; se = sqrt(V)/N = 0.028284/4
z2 = mu2 / (math.sqrt(0.0008) / 4); assert abs(s2["z"] - z2) < 1e-9 and abs(s2["p"] - 0.5 * math.erfc(z2 / math.sqrt(2))) < 1e-12
assert X.cluster_stats([mk(1, 0.01)])["z"] is None and X.cluster_stats([mk(1, 0.01)])["p"] == 1.0
# BH step-up: m_total 100, alpha 0.05: thresholds 0.0005 k; p = {a: 0.0004, b: 0.0011, c: 0.9}: a passes (0.0004 <= 0.0005), b fails (0.0011 > 0.001): only a
assert X.bh_pass({"a": 0.0004, "b": 0.0011, "c": 0.9}, 100) == {"a"}
assert X.bh_pass({"a": 0.0004, "b": 0.0009, "c": 0.9}, 100) == {"a", "b"}                       # b: 0.0009 <= 0.001
assert X.bh_pass({"a": 0.0004, "b": 0.0011}, 6290676) == set()                                  # the real m: nothing passes at these p
# step-up (not step-down): a failing small rank is rescued by a later passing rank
assert X.bh_pass({"a": 0.00055, "b": 0.0009}, 100) == {"a", "b"}
# bar flags: a cell that passes everything, and one that fails only the BH
good = {"taker_h2": {"pf": 1.31, "half1": 1.1, "half2": 1.0}, "taker_h5": {"pf": 1.0}}
f = X.bar_flags(good, {"n": 100, "trade_days": 10}, True); assert f["passes"] is True
f = X.bar_flags(good, {"n": 100, "trade_days": 10}, False); assert f["passes"] is False and [k for k, v in f.items() if not v and k != "passes"] == ["bh_ok"]
assert X.bar_flags(dict(good, taker_h2={"pf": 1.2999999, "half1": 1.1, "half2": 1.0}), {"n": 100, "trade_days": 10}, True)["pf02_ok"] is False      # unrounded
assert X.bar_flags(dict(good, taker_h2={"pf": 1.4, "half1": 0.99, "half2": 1.5}), {"n": 100, "trade_days": 10}, True)["halves_ok"] is False
assert X.bar_flags(good, {"n": 99, "trade_days": 10}, True)["n_ok"] is False and X.bar_flags(good, {"n": 100, "trade_days": 9}, True)["days_ok"] is False
# expected m by run date, and the refusal of any other m
assert X.expected_m(X.M_SWITCH - 1) == 6290676 and X.expected_m(X.M_SWITCH) == 7492500
try: X.run("score", [gp, X.sha(gp), "7492500" if X.expected_m() == 6290676 else "6290676"], {"funding": ["x"], "snap": [], "btc": ["x"]}); raise AssertionError("must refuse another m")
except SystemExit as e: assert "m_total" in str(e), str(e)
# score output carries the z, p, BH and the bar for a passing cell
assert "bar" in sc["0.05|fade|8"] and "z_p_all_six" in sc["0.05|fade|8"] and sc["_bh"]["m_total"] == 6290676
print("fundx2 run: ok")
