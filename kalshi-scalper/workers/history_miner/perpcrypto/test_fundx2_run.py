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
sc = X.score(R2, P2, g)
assert "all_six" in sc["0.05|fade|8"] and "btc_apart" in sc["0.05|fade|8"] and "other_five" in sc["0.05|fade|8"] and sc["0.05|fade|8"]["all_six"]["n"] == 28
assert sc["0.05|fade|24"].keys() == {"dropped", "rate_a_day"} and "outcomes not read" in sc["0.05|fade|24"]["dropped"]
assert sc["0.05|fade|8"]["n_by_ticker"] == {"KXBTCPERP": 14, "KXETHPERP": 14}
# (4) score refuses without the committed gate file or with a wrong sha, before any file is opened
d = tempfile.mkdtemp(); gp = os.path.join(d, "G.json"); open(gp, "w").write(json.dumps({"cells": g}))
for args in ([os.path.join(d, "none.json"), "00"], [gp, "00" * 32]):
    try: X.run("score", args, {"funding": ["x"], "snap": [], "btc": ["x"]}); raise AssertionError("must refuse")
    except SystemExit as e: assert "gate file" in str(e), str(e)
# (5) no allow line: the loader step refuses (no files exist either way)
L.ALLOW_FILE = os.path.join(d, "A.md"); open(L.ALLOW_FILE, "w").write("x\n")
f = os.path.join(d, "f.csv.gz"); open(f, "wb").write(b"x")
try: X.load(f, [], d); raise AssertionError("must refuse")
except (SystemExit, OSError) as e: pass
assert any("many cuts are 0" in h for h in X.HEADER) and any("regime shift" in h for h in X.HEADER) and any("APART" in h for h in X.HEADER)
print("fundx2 run: ok")
