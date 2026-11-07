"""Plain assert tests for the fast scan harness (src/scalper/scan.py); run with: python tests/test_scan.py. Each states a consequence.
Synthetic data throughout, except the self-test and the perps adapter checks, which use the local data files and are skipped if absent
(they read development regions only; no holdout row is opened by any test)."""
import gzip
import json
import math
import os
import random
import sqlite3
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import scan as S

ROOT = Path(__file__).resolve().parents[1]
TMP = tempfile.mkdtemp(prefix="scan_test_")

# ---- fee: ceil(0.07 x C x p x (1-p) in cents) per ORDER, divided by C for per contract
assert float(S.kalshi_fee_cents(0.5, 1)) == 2.0 and float(S.kalshi_fee_cents(0.9, 1)) == 1.0, "one contract at 50c costs 2c, at 90c 1c (rounded up)"
assert float(S.kalshi_fee_cents(0.5, 10)) == 18.0, "ten contracts at 50c: 17.5c rounds up to 18c for the ORDER (1.8c each, not 2c)"
assert float(S.kalshi_fee_cents(0.5, 4)) == 7.0, "an exact 7.0c product is not rounded up to 8c (the 1e-9 guard)"
ps = np.linspace(0.02, 0.98, 97)
for c in (1, 3, 10, 50):
    assert np.array_equal(S.kalshi_fee_cents(ps, c), np.array([math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) for p in ps])), "vector fee equals the scalar loop"
assert abs(float(S.kalshi_net_cents(1, 0.9, 1)) - (10.0 - 1.0)) < 1e-9 and abs(float(S.kalshi_net_cents(0, 0.9, 1)) + 91.0) < 1e-9, "win +9c net of 1c fee; loss -91c"
# the rounding favours size: per-contract fee at 50c falls from 2c at C=1 to about 1.76c at C=50
assert float(S.kalshi_fee_cents(0.5, 50)) / 50 < float(S.kalshi_fee_cents(0.5, 1)) / 1

# ---- stats helpers
assert S.pf_of([3, -1, 3, -1]) == 3.0 and S.pf_of([1, 2]) == S.PF_CAP and S.pf_of([-1]) == 0.0
v = np.array([1.0, 2.0, -1.0, 3.0]); win = np.array([0, 0, 1, 1]); date = np.array([10, 11, 10, 11])
st = S.stats_from_rows(win, date, v)
assert st["win"][0]["n"] == 2 and st["win"][1]["pf"] == 3.0 and st["win"][2]["n"] == 0 and st["all"]["n"] == 4

# ---- N and the bar are read back from the ledgers
assert abs(S.z_bar(1230489) - 5.364) < 0.01 and S.z_bar(1000) < S.z_bar(10 ** 6), "the bar rises with N"
assert S.n_total() == S.prior_n() + S._count_lines(S.PERPGEN_LEDGER_DIR) + S._count_lines(S.LEDGER_DIR)

# ---- engine equals a plain loop: 300 random rules on a synthetic table, per window n, gross wins and losses
ad = S.SyntheticAdapter(days=24, per_day=300, nfeat=6, plant=True, seed=5)
tab = ad.build_dev()
cuts = S.make_cuts(tab)
ats = S.AtomSet(tab, cuts)
assert (tab.win[tab.date == tab.date.min()] == 0).all() and tab.win.max() == 2
w1 = tab.win == 0
fi = tab.fnames.index("f0")
assert abs(cuts["ALL"]["f0"][2] - float(np.median(tab.X[fi][w1]))) < 1e-5, "cut points come from W1 rows only"
rng = random.Random(1)
rules = [S.draw_rule(rng, ats, tab) for _ in range(300)]
res = S.score_rules(tab, ats, "ALL", rules)
for r, s in zip(rules[:300], res):
    rows, net, nets = tab.outcome(r.dir, r.variant, "ALL")
    m = ats.A[list(r.atoms)][:, rows].all(axis=0)
    for w in range(3):
        mw = m & (tab.win[rows] == w)
        assert s["n"][w] == mw.sum()
        assert abs(s["pos"][w] - net[mw][net[mw] > 0].sum()) < 1e-2 * max(1, abs(s["pos"][w])) + 1e-2
        assert abs(s["neg"][w] + net[mw][net[mw] < 0].sum()) < 1e-2 * max(1, s["neg"][w]) + 1e-2
# a one-atom rule's atom really is its quantile cut
a0 = [i for i, nme in enumerate(ats.names) if nme == "f0:ge:0.75"][0]
assert (ats.A[a0] == (tab.X[fi] >= np.float32(cuts["ALL"]["f0"][3]))).all()
# a missing value makes every atom on that feature false, never true
tab.X[fi][:10] = np.nan
atsn = S.AtomSet(tab, cuts)
assert not atsn.A[[i for i, f in enumerate(atsn.feat_of) if f == "f0"]][:, :10].any(), "NaN: the atom is false"

# ---- a planted rule is found, with the bar met in each window; pure noise yields nothing; the ledger is written first and counts distinct rules
led = os.path.join(TMP, "led1"); outd = os.path.join(TMP, "runs")
out = S.run(S.SyntheticAdapter(days=30, per_day=500, nfeat=6, plant=True, seed=7), 4000, 11, ledger_dir=led, out_dir=outd, verbose=False)
assert out["rules_scored"] == 4000 and S._count_lines(led) == 4000, "one ledger line per distinct rule scored"
found = [s for s in out["survivors"] if {"f2", "f3"} <= {a["feat"] for a in s["atoms"]} and s["dir"] == "yes"]
assert out["exact_survivors"] >= 1 and found, "the planted f2 high, f3 low rule (or a superset) survives in all three windows"
for s in out["survivors"]:
    assert all(w["pf"] >= 1.5 for w in s["exact"]["win"]), "every survivor has PF 1.5 in each window, float64 exact"
assert out["N_after"] - out["N_before"] == 4000
out2 = S.run(S.SyntheticAdapter(days=30, per_day=500, nfeat=6, plant=True, seed=7), 500, 11, ledger_dir=led, out_dir=outd, verbose=False)
assert S._count_lines(led) == 4500, "a rule already in a ledger is not scored or counted again (same seed repeats nothing)"
nz = S.run(S.SyntheticAdapter(days=30, per_day=500, nfeat=6, plant=False, seed=8), 4000, 12, ledger_dir=os.path.join(TMP, "led2"), out_dir=outd, verbose=False)
assert nz["exact_survivors"] == 0, "no edge, no survivor at the 1.5 bar (%d)" % nz["exact_survivors"]

# ---- ledger before scoring: a crash inside scoring leaves the batch counted
orig = S.score_rules
def boom(*a, **k):
    raise RuntimeError("crash")
S.score_rules = boom
try:
    S.run(S.SyntheticAdapter(days=30, per_day=300, nfeat=5, seed=3), 100, 13, ledger_dir=os.path.join(TMP, "led3"), out_dir=outd, verbose=False, batch=50)
    raise AssertionError("expected crash")
except RuntimeError:
    pass
finally:
    S.score_rules = orig
assert S._count_lines(os.path.join(TMP, "led3")) == 50, "the first batch was in the ledger before the crash"

# ---- look-ahead audit: a feature that reads the future fails the truncation test, a clean one passes
clean = S.SyntheticAdapter(days=10, per_day=200, nfeat=4, seed=2); tc = clean.build_dev()
assert clean.truncation_test(tc, 100, 0)["passed"]
leaky = S.SyntheticAdapter(days=10, per_day=200, nfeat=4, leak=True, seed=2); tl = leaky.build_dev()
r = leaky.truncation_test(tl, 100, 0)
assert not r["passed"] and r["mismatches"] == 100, "all 100 sampled rows of the leaky feature differ once the future is deleted"
hooks = {h.__name__ for h in S.AUDIT_HOOKS}
assert {"audit_truncation", "audit_reverse_control", "audit_fee_stress"} <= hooks

# ---- a Kalshi-shaped sqlite with rows on both sides of the holdout cut
CUT = S.HOLD_FROM_TS
spec = S.KalshiSpec("kalshi15_test", ("t",), None, dev_hi=CUT, hold_lo=CUT, looks=(360,))
db_dir = os.path.join(TMP, "db"); os.makedirs(db_dir)
db = sqlite3.connect(os.path.join(db_dir, "t.sqlite"))
db.executescript("CREATE TABLE market(ticker TEXT PRIMARY KEY, series TEXT, open_ts INTEGER, close_ts INTEGER, result TEXT, strike REAL, n_candles INTEGER);"
                 "CREATE TABLE candle(ticker TEXT, series TEXT, end_ts INTEGER, bid_o REAL, bid_h REAL, bid_l REAL, bid_c REAL, ask_o REAL, ask_h REAL, ask_l REAL,"
                 " ask_c REAL, price_c REAL, volume REAL, oi REAL, PRIMARY KEY(ticker, end_ts));")
rg = random.Random(4)
k = 0
for day in range(-40, 10):                                   # 40 dev days then 10 holdout days
    for slot in range(40):
        close = CUT + day * 86400 + 3600 + slot * 900
        tk = "KXT-%d" % k; k += 1
        p = rg.uniform(0.3, 0.95)
        res = "yes" if rg.random() < p else "no"
        db.execute("INSERT INTO market VALUES(?,?,?,?,?,?,?)", (tk, "KXTEST15M", close - 900, close, res, 1.0, 14))
        for m in range(1, 15):
            db.execute("INSERT INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (tk, "KXTEST15M", close - 60 * m, p - .01, p - .01, p - .01, p - .01, p + .01, p + .01, p + .01,
                                                                             p + .01, p, 5.0, 100.0))
db.commit(); db.close()
ka = S.KalshiAdapter(spec, db_dir=db_dir)
kt = ka.build_dev()
assert int(kt.meta["close"].max()) < CUT, "the dev loader returns no row at or after the holdout cut"
assert set(np.unique(kt.win)) == {0, 1, 2} and len(np.unique(kt.date)) == 40
try:
    ka._read(None, CUT + 86400)
    raise AssertionError("a dev read across the cut must be refused")
except S.Blocked:
    pass
assert ka.truncation_test(kt, 100, 3)["passed"]
u = ka.unseen()
assert u["holdout_markets"] == 400 and u["holdout_from"] == "2026-10-28", u

# ---- freeze, sha256, committed check, guard, read-once
S.GUARD = os.path.join(TMP, "scan", "holdout_guard.json")
os.makedirs(os.path.dirname(S.GUARD))
kcuts = S.make_cuts(kt); kcuts["_series"] = kt.meta["series_names"]
fake_run = dict(adapter=kt.name, group="ALL", N_after=1230489, z_bar=5.36, cuts=kcuts, cuts_sha256=S.cuts_sha(kcuts), table_sha256=kt.fingerprint(), survivors=[
    dict(id="x", atoms=[dict(kind="num", feat="ask", op="ge", q=0.10)], dir="yes", variant=360, deflated=False, exact={})])
rf = os.path.join(TMP, "run.json"); json.dump(fake_run, open(rf, "w"))
fp = S.freeze([rf], "T1", out_dir=TMP)
assert os.path.exists(fp + ".sha256")
try:
    S.freeze([rf], "T1", out_dir=TMP); raise AssertionError("ids are never reused")
except S.Blocked:
    pass
try:
    S.holdout(ka, fp, require_committed=False)
    raise AssertionError("holdout must be locked without the guard file")
except S.Blocked as e:
    assert "guard" in str(e)
assert not os.path.exists(S.GUARD) or "T1|kalshi15_test" not in json.load(open(S.GUARD)).get("used", {})
try:
    S.load_frozen(fp, require_committed=True); raise AssertionError("an uncommitted frozen list is refused")
except S.Blocked:
    pass
json.dump({"unlock": {"T1": {"datasets": ["kalshi15_test"]}}}, open(S.GUARD, "w"))
open(fp, "a").write(" ")                                       # tamper with the frozen list
try:
    S.holdout(ka, fp, require_committed=False); raise AssertionError("a tampered list must not open the holdout")
except S.Blocked as e:
    assert "sha256" in str(e)
assert "used" not in json.load(open(S.GUARD)), "a refused read leaves no use record"
fp2 = S.freeze([rf], "T2", out_dir=TMP)
json.dump({"unlock": {"T2": {"datasets": ["kalshi15_test"]}}}, open(S.GUARD, "w"))
res = S.holdout(ka, fp2, require_committed=False, verbose=False)
assert res["holdout_rows"] > 0 and res["results"][0]["n"] > 0 and res["results"][0]["label"] in ("FALSIFIED", "NOT_ENOUGH_DATA", "LEAD", "CANDIDATE")
assert "T2|kalshi15_test" in json.load(open(S.GUARD))["used"], "the read is recorded"
try:
    S.holdout(ka, fp2, require_committed=False); raise AssertionError("second read")
except S.Blocked as e:
    assert "already read" in str(e)

# ---- the registered figure (README MKTTIME1 gold windows A and B) and the engine, on the real files
if (ROOT / "data" / "book.sqlite").exists() and (ROOT / "data" / "l1b.sqlite").exists():
    assert S.selftest(verbose=False), "self-test: gold L1 windows A and B reproduce the README and the engine equals a plain loop"
    # perps: development region only, look-ahead and overlap checks on two tickers
    if (ROOT / "data" / "perpgen" / "clean" / "dev").exists():
        pa = S.PerpAdapter("CRYPTO", None, tickers=["KXBTCPERP", "KXETHPERP"])
        pt = pa.build_dev()
        assert pt.n > 5000 and pt.win.max() == 2 and set(pt.scope_names) == {"KXBTCPERP", "KXETHPERP"}
        cutd = json.load(open(ROOT / "workers" / "PERPGEN_CUTS.json"))["cuts"]["KXBTCPERP"]["validation_ts"]
        assert int(pt.ts.max()) < cutd + 86400, "discovery only: no row from the validation region without a frozen id"
        assert pa.truncation_test(pt, 60, 1)["passed"], "perp features use only bars at or before the decision"
        pcuts = S.make_cuts(pt); pats = S.AtomSet(pt, pcuts)
        ex = S.exact_rule(pt, pats, "CRYPTO", S.Rule((), "long", 3600))
        sel = ex["rows"]
        ts = pt.ts[sel]; sc = pt.scope[sel]
        for sc_i in np.unique(sc):
            t = ts[sc == sc_i]
            assert (np.diff(t) >= 3600).all(), "one position per ticker: a 1 hour hold leaves at least an hour between entries"
        rows_all = S._prep(pt, "CRYPTO", "long", 3600)[0]
        assert len(sel) < len(rows_all), "the overlap rule removed signals that arrived while a position was open"
        try:
            pa.build_holdout("T9", {})
            raise AssertionError("perps holdout locked")
        except S.Blocked:
            pass

print("test_scan: ok")
