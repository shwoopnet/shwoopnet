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


# ================================================================== HARNESS v1.1: audit hooks, perps extras
import time as _time
_t_v11 = _time.time()
PERMS = 300


def _frozen_doc(tab, rules, ats, cuts, group="ALL"):
    ca = dict(cuts)
    return dict(frozen_id="TESTAUD", adapter=tab.name, group=group, cuts=ca, cuts_sha256=S.cuts_sha(ca), table_sha256=tab.fingerprint(),
                survivors=[dict(id="x", atoms=[ats.specs[a] for a in r.atoms], dir=r.dir, variant=r.variant) for r in rules])


# ---- synthetic planted edge: every hook passes; the planted survivors collapse into few clusters
pl_ad = S.SyntheticAdapter(days=30, per_day=500, nfeat=6, plant=True, seed=7)
pl_tab = pl_ad.build_dev(); pl_cuts = S.make_cuts(pl_tab); pl_ats = S.AtomSet(pl_tab, pl_cuts)
pl_run = S.run(pl_ad, 4000, 11, ledger_dir=os.path.join(TMP, "led_v11"), out_dir=os.path.join(TMP, "runs"), verbose=False, tab=pl_tab)
assert pl_run["exact_survivors"] >= 1
pl_rules = [S.Rule(tuple(sorted(pl_ats.names.index(S._name_of(sp)) for sp in sv["atoms"])), sv["dir"], sv["variant"]) for sv in pl_run["survivors"]]
doc = _frozen_doc(pl_tab, pl_rules, pl_ats, {**pl_cuts, "_x": 1})
doc["cuts_sha256"] = S.cuts_sha(pl_cuts)
rep = S.audit_frozen(pl_ad, doc, tab=pl_tab, out_dir=False, perms=PERMS)
hk = {h["name"]: h for h in rep["hooks"]}
assert set(hk) >= {"truncation", "fee_stress", "placebo_shuffle", "plain_loop_recompute", "latency_stress", "cluster_dedupe"}, hk.keys()
assert hk["placebo_shuffle"]["passed"] and hk["placebo_shuffle"]["max_p_plus"] <= 2.0 / (1 + PERMS), "planted edge: no shuffled run reaches the observed PF"
assert hk["plain_loop_recompute"]["passed"], hk["plain_loop_recompute"]
assert hk["latency_stress"]["passed"], "a planted edge of +16c survives 1.5c a bar of delay"
assert 1 <= hk["cluster_dedupe"]["independent"] <= len(pl_rules)
assert not rep["failed"], rep["failed"]
assert "SCAN AUDIT TESTAUD" in rep["text"] and "independent survivors" in rep["text"]
# the files are written where asked, json parses, text summary beside it
S.audit_frozen(pl_ad, doc, tab=pl_tab, out_dir=TMP, perms=50)
assert json.load(open(os.path.join(TMP, "SCAN_AUDIT_TESTAUD.json")))["frozen_id"] == "TESTAUD" and os.path.exists(os.path.join(TMP, "SCAN_AUDIT_TESTAUD.txt"))

# ---- placebo: pure noise fails it (rule picks are indistinguishable from shuffled picks), a planted rule passes
nz_ad = S.SyntheticAdapter(days=30, per_day=500, nfeat=6, plant=False, seed=8)
nz_tab = nz_ad.build_dev(); nz_ats = S.AtomSet(nz_tab, S.make_cuts(nz_tab))
rg2 = random.Random(5)
ps_ = [S.placebo_shuffle(nz_tab, nz_ats, "ALL", S.draw_rule(rg2, nz_ats, nz_tab), perms=PERMS, seed=3)["p_plus"] for _ in range(12)]
assert sum(1 for x in ps_ if x < 0.05) <= 2 and float(np.median(ps_)) > 0.2, "noise rules are not rejected by the placebo: %s" % ps_
r_pl = pl_rules[0]
assert S.placebo_shuffle(pl_tab, pl_ats, "ALL", r_pl, perms=PERMS)["passed"]
assert S.placebo_shuffle(pl_tab, pl_ats, "ALL", r_pl, perms=100, seed=9) == S.placebo_shuffle(pl_tab, pl_ats, "ALL", r_pl, perms=100, seed=9), "fixed seed, same answer"
# a noise 'survivor' (best of 300 random rules by weakest window PF) still has an unremarkable placebo p: a single-rule placebo is not selection corrected
rg3 = random.Random(6)
cand = [S.draw_rule(rg3, nz_ats, nz_tab) for _ in range(300)]
sc_ = S.score_rules(nz_tab, nz_ats, "ALL", cand)
best = cand[int(np.argmax([min(x["pf"]) if min(x["n"]) >= 40 else 0 for x in sc_]))]
pb = S.placebo_shuffle(nz_tab, nz_ats, "ALL", best, perms=PERMS, seed=4)
assert pb["observed_pf"] > 1.0 and pb["p_plus"] > 0.001, pb

# ---- plain loop: agrees with the engine, and a defect on either side is loud
r0 = pl_rules[0]
assert S.plain_recompute(pl_ad, pl_tab, pl_ats, "ALL", r0)["passed"]
_ex = S.exact_rule
def _drop_one(tab, ats, group, rule, stress=False):
    st = _ex(tab, ats, group, rule, stress)
    st["rows"] = st["rows"][1:]
    return st
S.exact_rule = _drop_one
try:
    S.plain_recompute(pl_ad, pl_tab, pl_ats, "ALL", r0); raise AssertionError("a trade the engine lost must raise")
except S.AuditMismatch as e:
    assert "trade sets differ" in str(e)
finally:
    S.exact_rule = _ex

# ---- cluster dedupe: identical selections are one cluster, disjoint ones are two
a_hi = pl_ats.names.index("f2:ge:0.90"); a_lo = pl_ats.names.index("f2:le:0.10")
ca = S.Rule((a_hi,), "yes", 360); cb = S.Rule((a_hi,), "no", 360); cc = S.Rule((a_lo,), "yes", 360)
cl = S.cluster_dedupe(pl_ad, pl_tab, pl_ats, "ALL", [ca, cb, cc])
assert cl["independent"] == 2 and sorted(len(c["members"]) for c in cl["clusters"]) == [1, 2], cl
assert S.cluster_dedupe(pl_ad, pl_tab, pl_ats, "ALL", [ca, cc], thr=0.7)["independent"] == 2
assert S.cluster_dedupe(pl_ad, pl_tab, pl_ats, "ALL", [ca, ca])["independent"] == 1

# ---- latency: the fill price moves with the shift (Kalshi-shaped file), and a Kalshi plain loop equals the engine on the test sqlite
S.AtomSet  # noqa
kcuts_ = S.make_cuts(kt); kats = S.AtomSet(kt, kcuts_)
kr = S.Rule((kats.names.index("ask:ge:0.10"),), "yes", 360)
assert S.plain_recompute(ka, kt, kats, "ALL", kr)["passed"], "Kalshi plain loop equals the engine on the test file"
lat = S.latency_stress(ka, kt, kats, "ALL", kr)
base_pf = S.exact_rule(kt, kats, "ALL", kr)["all"]["pf"]
assert abs(lat["shift_1"]["pf_pooled"] - round(base_pf, 3)) < 0.01 and lat["shift_1"]["missed"] == 0, "constant quotes: one minute later is the same fill"
ka.markets[0][4].pop(ka.markets[0][2] - 300, None)             # delete market 0's quote at 5 minutes left: that fill is missed at shift 1
ka._plain_state = None
assert S.latency_stress(ka, kt, kats, "ALL", kr)["shift_1"]["missed"] >= 1
# tamper with a settlement: the engine's table is stale against the plain loop, so the recompute must raise
tk0 = ka.markets[3]; ka.markets[3] = (tk0[0], tk0[1], tk0[2], "no" if tk0[3] == "yes" else "yes", tk0[4]); ka._plain_state = None
try:
    S.plain_recompute(ka, kt, kats, "ALL", kr); raise AssertionError("a flipped settlement must raise")
except S.AuditMismatch:
    pass
ka.markets[3] = tk0; ka._plain_state = None

# ---- perps extras: leader returns, minutes to funding (synthetic grid, then a real development region)
gl = {"t0": 1_000_000 * 60, "mid": np.exp(np.cumsum(np.full(3000, 1e-4)))}
tt = np.array([gl["t0"] + 1000 * 60, gl["t0"] + 5 * 60, gl["t0"] - 60, gl["t0"] + 4000 * 60, gl["t0"] + 1000 * 60 + 7])
lr = S.leader_ret(gl, tt, 60)
assert abs(lr[0] - 60 * 1e-4 * 1e4) < 1e-2 and np.isnan(lr[1]) and np.isnan(lr[2]) and np.isnan(lr[3]) and np.isnan(lr[4]), "leader value only inside its own region and on a minute"
g2 = {"t0": gl["t0"], "mid": gl["mid"].copy()}; g2["mid"][1001:] = np.nan
assert S.leader_ret(g2, tt[:1], 60)[0] == lr[0], "deleting every leader minute after t leaves the feature unchanged"
day0 = (1_790_000_000 // 86400) * 86400
f_ts = np.array([day0 + h * 3600 + d * 86400 for d in range(3) for h in (4, 12, 20)], dtype=np.int64)
mt = S.mtf_codes(np.array([day0 + 86400 * 1 + 3 * 3600 + 3000, day0 + 86400 + 9 * 3600, day0 + 86400 + 12 * 3600, day0 + 3600, day0 + 86400 + 20 * 3600 - 29 * 60]), f_ts)
assert list(mt) == [0, 2, 3, -1, 0] or list(mt) == [0, 2, 3, -1, 0], list(mt)
assert S.mtf_codes(np.array([day0 + 86400 + 3 * 3600 + 3000]), f_ts[:3])[0] == 0 and S.mtf_codes(np.array([day0 + 86400 + 3 * 3600 + 3000]), f_ts[:0])[0] == -1, "no published funding yet: missing"
assert "extra" in S.PerpAdapter("CRYPTO", None, extra=True).opts and S.PerpAdapter("CRYPTO", None).opts == {"extra": False}

if (ROOT / "data" / "perpgen" / "clean" / "dev").exists():
    pe = S.PerpAdapter("CRYPTO", None, tickers=["KXBTCPERP", "KXETHPERP", "KXSOLPERP"], extra=True)
    pet = pe.build_dev()
    assert pet.fnames == S.FEATS_P + S.FEATS_PX and "mtf" in pet.cats
    for nm, pref in (("KXBTCPERP", "xbtc"), ("KXETHPERP", "xeth")):
        off, m = pe.offsets[nm]
        assert np.isnan(pet.X[pet.fnames.index(pref + "60"), off:off + m]).all(), "a ticker does not lead itself"
    off, m = pe.offsets["KXSOLPERP"]
    assert np.isfinite(pet.X[pet.fnames.index("xbtc60"), off:off + m]).mean() > 0.9, "BTC leads SOL on the discovery dates"
    assert pe.truncation_test(pet, 60, 2)["passed"], "extras use only data at or before the decision"
    assert (pet.cats["mtf"] >= 0).mean() > 0.5
    plain_base = S.PerpAdapter("CRYPTO", None, tickers=["KXBTCPERP", "KXETHPERP"]).build_dev()
    assert plain_base.fnames == S.FEATS_P, "extras are opt-in: v1 atoms and ids are unchanged"
    # plain loop and latency on a real perps development rule
    pcuts = S.make_cuts(pet); pats = S.AtomSet(pet, pcuts)
    prule = S.Rule((pats.names.index("r60:le:0.25"),), "long", 3600)
    assert S.plain_recompute(pe, pet, pats, "CRYPTO", prule)["passed"], "perps plain loop equals the engine (entry, exit, funding, overlap rule)"
    prule2 = S.Rule((pats.names.index("mtf:eq:0"), pats.names.index("xbtc60:ge:0.75")), "short", 14400)
    assert S.plain_recompute(pe, pet, pats, "CRYPTO", prule2)["passed"]
    lat = S.latency_stress(pe, pet, pats, "CRYPTO", prule)
    assert set(lat) == {"shift_1", "shift_2"} and lat["shift_1"]["n_windows"] != [0, 0, 0]

# ---- one real Kalshi development-region rule (closes before 2026-10-28 only; fresh.sqlite, no holdout row is read), every hook end to end
if (ROOT / "data" / "fresh.sqlite").exists():
    fad = S.KalshiAdapter(S.FRESH); ftab = fad.build_dev()
    assert int(ftab.meta["close"].max()) < S.HOLD_FROM_TS
    fcuts = S.make_cuts(ftab); fcuts["_series"] = ftab.meta["series_names"]
    fats = S.AtomSet(ftab, {k: v for k, v in fcuts.items() if not k.startswith("_")})
    frules = [S.Rule((fats.names.index("ask:ge:0.75"),), "yes", 360), S.Rule((fats.names.index("ask:ge:0.75"), fats.names.index("spread:le:0.50")), "yes", 360)]
    fdoc = _frozen_doc(ftab, frules, fats, fcuts)
    frep = S.audit_frozen(fad, fdoc, tab=ftab, out_dir=False, perms=200)
    fh = {h["name"]: h for h in frep["hooks"]}
    assert frep["cuts_match"] and fh["truncation"]["passed"] and fh["plain_loop_recompute"]["passed"], fh["plain_loop_recompute"]
    assert fh["cluster_dedupe"]["independent"] == 1, "the second rule is a subset of the first: one cluster"
    assert fh["latency_stress"]["per_rule"][0]["shift_1"]["n_windows"][0] > 100 and fh["placebo_shuffle"]["per_rule"][0]["perms"] == 200
    print("real dev rule: PF", fh["plain_loop_recompute"]["per_rule"][0]["pf"], "placebo p", fh["placebo_shuffle"]["per_rule"][0]["p_plus"],
          "latency pooled", [fh["latency_stress"]["per_rule"][0][k]["pf_pooled"] for k in ("shift_1", "shift_2")])
print("v1.1 section: %.1fs" % (_time.time() - _t_v11))

print("test_scan: ok")
