#!/usr/bin/env python3
"""ENGINE1 BATCH B (80 rules) AND BATCH C (68 rules) HELD-OUT EVALUATOR, INDEPENDENT SECOND BUILD (Forensics desk, Nov 17, 2026). Written from ENGINE_BATCHB_HELDOUT_PLAN_NOV16.md (sha256 ca2f0c35...) and ENGINE_BATCHC_HELDOUT_PLAN_NOV16.md (sha256 af3b024e...) ONLY; Desk A's engine1_heldout_run_b.py, run_c, the pooled BH script and any print were not opened. The rule universe is read from MY OWN committed VALIDATE lists (ENGB4XBTC_B2_VALIDATE33.txt, ENGB2_B2_{TS,VS,SW}_VALIDATE.txt, ENGBC_B2_C{1..4}_VALIDATE.txt), which Auditor B matched to Desk A's prints.
Per rule: n (scored entries at 1c), PF 1c and 2c, one sided day clustered p (1c cash, UTC close date), verdict by the floors (74 for KXBTC15M KXETH15M KXXRP15M KXDOGE15M KXGOLD15M, 90 others): n >= floor and PF1c >= 1.3 and PF2c >= 1.0 = 'holds', n < floor = 'no evidence', else 'does not hold'; BH step-up at 5% over m = 80 (batch B) or 68 (batch C) ranking EVERY rule (no-evidence rules included, p = 1 when undefined); per row missing_feature_skips_at_bucket (markets of the series with a valid entry candle at the rule's bucket under its side rule whose feature is missing) and markets_in_window. A pooled step-up over m = 338 is available as pooled_bh() (batch B and C p values plus the 190's).
Cross-series features (btcmom3, ethmom3, goldmom3) read the same-close market of THE TEST SET; a close with no such candle is a counted missing feature, never filled in. Terciles (spread, vspike) come from the archive SEARCH half only.
Modes: --dry <archive>: the TEST set is the archive VALIDATE half and every rule must reproduce its listed n, PF1c, PF2c (n exact, PFs 1e-9); no held-out row is opened. --read <archive> <heldout extract> <print file of Desk A>: refuses unless HELDOUT_PULL_RUNS.md carries a line naming this file, its own sha256 and the extract sha256, hashes the extract, opens Desk A's print FILE only to hash it, and pins its imports.
usage: python3 -I heldout_bc_b2.py <B|C> --dry <archive.sqlite> | <B|C> --read <archive> <heldout.sqlite> <print file> | --selftest"""
import sys, os, json, math, sqlite3, hashlib, collections, calendar
HERE = os.path.dirname(os.path.abspath(__file__))
PINS = {"shadow_rank_b2.py": "32b9580e094f282b302601e838001f0f152a7c01f9bf8c22e19c6c1392462ab6", "engb4xbtc_b2.py": "36cee8055caa9dc7e8d94367d3decbbe61e521d920a76f96a9bfa21f9a67e9e3", "engb_b2_blind.py": "27f91516da4b57d6e4ecde08009379846ae5115483297620055cfa153bb1a65b", "engbc_b2.py": "a0a8d0d1750d389ad26e0646e3e4a57d0385ed38f98865cccc74d44edafb7091"}
EXTRACT_SHA = "20977a1f78c7859f750cc9362e7956da32407d1e1d4b062019e26774f313f6ca"; ALLOW_FILE = os.path.join(HERE, "..", "..", "HELDOUT_PULL_RUNS.md")
def sha_of(path):
    h = hashlib.sha256(); h.update(open(path, "rb").read()); return h.hexdigest()
def check_pins(folder=HERE, pins=None):
    for name, want in (PINS if pins is None else pins).items():
        try: got = sha_of(os.path.join(folder, name))
        except OSError: raise SystemExit("REFUSED: %s cannot be read" % name)
        if got != want: raise SystemExit("REFUSED: %s differs from its pinned sha256" % name)
def check_allow(extract_path, allow_file=None, self_path=None):
    allow_file = ALLOW_FILE if allow_file is None else allow_file; self_path = os.path.abspath(__file__) if self_path is None else self_path
    try: lines = open(allow_file).read().splitlines()
    except OSError: raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read")
    need = [os.path.basename(self_path), sha_of(self_path), EXTRACT_SHA]
    if not any(all(n in l for n in need) for l in lines): raise SystemExit("REFUSED: no line of HELDOUT_PULL_RUNS.md names this evaluator, its sha256 and the extract sha256")
    if sha_of(extract_path) != EXTRACT_SHA: raise SystemExit("REFUSED: the extract file does not hash to the allowed sha256")
check_pins(); sys.path.insert(0, HERE)
import shadow_rank_b2 as P
import engb4xbtc_b2 as E
import engb_b2_blind as G
import engbc_b2 as C
R6 = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")
LISTS = {"B": [("ENGB4XBTC_B2_VALIDATE33.txt", "btcmom3", False), ("ENGB2_B2_TS_VALIDATE.txt", None, True), ("ENGB2_B2_VS_VALIDATE.txt", None, True), ("ENGB2_B2_SW_VALIDATE.txt", None, True)],
         "C": [("ENGBC_B2_C1_VALIDATE.txt", "ethmom3", False), ("ENGBC_B2_C2_VALIDATE.txt", "oiacc", False), ("ENGBC_B2_C3_VALIDATE.txt", "todct", False), ("ENGBC_B2_C4_VALIDATE.txt", "goldmom3", False)]}
FEATSER = {"btcmom3": "KXBTC15M", "ethmom3": "KXETH15M", "goldmom3": "KXGOLD15M"}
def load_rules(batch, folder=HERE):
    out = []
    for fn, fname, colon in LISTS[batch]:
        for ln in open(os.path.join(folder, fn)).read().splitlines()[1:]:
            t = ln.split(); fcls = t[4]
            if colon: nm, cl = fcls.split(":"); out.append({"series": t[0], "bucket": int(t[1]), "band": int(t[2]), "side": t[3], "fname": nm, "cls": cl, "exit": t[5], "ln": int(t[6]), "lpf1": float(t[7]), "lpf2": float(t[8])})
            else: out.append({"series": t[0], "bucket": int(t[1]), "band": int(t[2]), "side": t[3], "fname": fname, "cls": fcls, "exit": t[5], "ln": int(t[6]), "lpf1": float(t[7]), "lpf2": float(t[8])})
    return out
def load_markets(path):
    db = sqlite3.connect("file:%s?mode=ro" % path, uri=True); ms = {}
    for tk, ser, close, res in db.execute("select ticker, series, close_ts, result from market"): ms[tk] = P.Mkt(tk, ser, close, res, {})
    for tk, end, b, k, last, v, oi in db.execute("select ticker, end_ts, yes_bid, yes_ask, last, volume, oi from candle"):
        if tk in ms and end <= ms[tk].close: ms[tk].c[end] = (b, k, last, v, oi)
    by = collections.defaultdict(list)
    for m in sorted(ms.values(), key=lambda m: (m.close, m.tk)): by[m.ser].append(m)
    return by
class Cuts:
    def __init__(self, arch_by, ls): self.arch, self.ls, self.cache = arch_by, ls, {}
    def get(self, kind, ser, B):
        k = (kind, ser, B)
        if k not in self.cache:
            vals = []
            for m in self.arch.get(ser, []):
                if m.close >= self.ls[ser]: continue
                e = m.close - B; q = m.c.get(e)
                if q is None or not P.two(q[0], q[1]): continue
                x = P.cents(q[1] - q[0]) if kind == "spread" else G.vspike(m, e)
                if x is not None: vals.append(x)
            self.cache[k] = G.tercile_cuts(vals)
        return self.cache[k]
def feature_cls(r, m, e, side, fby, cuts):
    f = r["fname"]
    if f in FEATSER: x = C.cross_move(fby.get(f, {}).get(m.close), e); return None if x is None else P.klass(x)
    if f == "oiacc": x = C.oiacc(m, e); return None if x is None else P.klass(x)
    if f == "todct": return C.central_band(e)
    if f in ("oi3", "oi6", "vol3", "mom1", "mom3", "mom5"): x = P.feature(m, e, f, side); return None if x is None else P.klass(x)
    q = m.c[e]
    if f == "spread": cu = cuts.get("spread", m.ser, r["bucket"]); return None if cu is None else G.tclass(P.cents(q[1] - q[0]), cu)
    if f == "vspike":
        x = G.vspike(m, e); cu = cuts.get("vspike", m.ser, r["bucket"]); return None if x is None or cu is None else G.tclass(x, cu)
    if f == "swid": x = G.swid(m, e); return None if x is None else G.sign_class(x)
    raise SystemExit("unknown filter %s" % f)
def nets_for(m, B, side, h, ex):
    return G.nets_ta(m, B, side, h, (ex,))[ex] if ex in ("TA3", "TA5") else E.nets(m, B, side, h)[ex]
def score_rule(r, test_by, fby, cuts):
    ms = test_by.get(r["series"], []); x1, x2, cn = [], [], []; mfs = 0
    for m in ms:
        en = E.entries(m, r["bucket"], r["side"])
        if en is None: continue
        side, ca = en; e = m.close - r["bucket"]; cl = feature_cls(r, m, e, side, fby, cuts)
        if cl is None: mfs += 1; continue
        if ca // 5 != r["band"] or cl != r["cls"]: continue
        a = nets_for(m, r["bucket"], side, 0.01, r["exit"]); b = nets_for(m, r["bucket"], side, 0.02, r["exit"])
        if a is not None: x1.append(a); cn.append((m.close, a))
        if b is not None: x2.append(b)
    n = len(x1); z, p, k = E.pval(cn) if n else (None, 1.0, 0)
    return {"n": n, "pf1": E.pfv(x1) if n else None, "pf2": E.pfv(x2) if n else None, "p": 1.0 if p is None else p, "days": k, "mfs": mfs, "mkts": len(ms)}
def verdict(r, s):
    fl = 74 if r["series"] in R6 else 90
    if s["n"] < fl: return "no evidence at n = %d" % s["n"]
    return "holds" if (s["pf1"] >= 1.3 and s["pf2"] >= 1.0) else "does not hold"
def pooled_bh(plists, m=338):
    ps = [p for pl in plists for p in pl]; return E.bh(ps, m)[0]
def run(batch, test_by, fby, cuts, folder=HERE):
    rules = load_rules(batch, folder); res = [(r, score_rule(r, test_by, fby, cuts)) for r in rules]; m = len(rules)
    k, o = E.bh([s["p"] for _, s in res], m); surv = set(o[:k]); return res, k, surv, m
def feature_maps(by):
    return {f: {m.close: m for m in by.get(s, [])} for f, s in FEATSER.items()}
def selftest():
    assert len(load_rules("B")) == 80 and len(load_rules("C")) == 68
    assert pooled_bh([[0.0001, 0.9], [0.5]], 338) == 1 and pooled_bh([[0.9]], 338) == 0
    r = {"series": "KXBTC15M"}; assert verdict(r, {"n": 73, "pf1": 5, "pf2": 5}).startswith("no evidence") and verdict(r, {"n": 74, "pf1": 1.3, "pf2": 1.0}) == "holds" and verdict(dict(r, series="KXHYPE15M"), {"n": 89, "pf1": 5, "pf2": 5}).startswith("no evidence") and verdict(dict(r, series="KXHYPE15M"), {"n": 90, "pf1": 1.29, "pf2": 5}) == "does not hold"
    d = __import__("tempfile").mkdtemp()
    for nm in PINS: open(os.path.join(d, nm), "w").write("x")
    try: check_pins(d); raise AssertionError("changed imports must refuse")
    except SystemExit: pass
    open(os.path.join(d, "A.md"), "w").write("none\n")
    try: check_allow(os.path.join(d, "A.md"), os.path.join(d, "A.md")); raise AssertionError("no allow line must refuse")
    except SystemExit: pass
    print("selftest ok")
def main(a):
    if a[0] == "--selftest": return selftest()
    batch = a[0]; mode = a[1]
    if batch not in ("B", "C") or mode not in ("--dry", "--read"): raise SystemExit("usage")
    arch = load_markets(a[2]); ls = {s: calendar.timegm(tuple(int(x) for x in P.LAST_SEARCH[s].split("-")) + (0, 0, 0)) + 86400 for s in arch if s in P.LAST_SEARCH}; cuts = Cuts(arch, ls)
    if mode == "--dry":
        test = {s: [m for m in v if m.close >= ls[s]] for s, v in arch.items() if s in ls}; fby = feature_maps({s: [m for m in v if m.close >= ls[s]] for s, v in arch.items() if s in ls})
        res, k, surv, m = run(batch, test, fby, cuts); bad = 0
        for r, s in res:
            ok = s["n"] == r["ln"] and abs(s["pf1"] - r["lpf1"]) < 1e-9 and abs(s["pf2"] - r["lpf2"]) < 1e-9
            if not ok: bad += 1; print("MISMATCH", r["series"], r["bucket"], r["band"], r["side"], r["fname"], r["cls"], r["exit"], "listed n %d pf %.12f %.12f | mine n %d pf %s %s" % (r["ln"], r["lpf1"], r["lpf2"], s["n"], s["pf1"], s["pf2"]))
        print("DRY batch %s on the archive VALIDATE half: rules %d reproduced %d mismatched %d | BH m %d survivors %d (p of the VALIDATE half, for the compare only)" % (batch, len(res), len(res) - bad, bad, m, k))
        out = os.environ.get("OUTLIST")
        if out: open(out, "w").write("\n".join("%d %s %d %d %s %s:%s %s n %d pf1 %.12f pf2 %.12f p %.12e days %d mfs %d mkts %d %s survivor %s" % (i, r["series"], r["bucket"], r["band"], r["side"], r["fname"], r["cls"], r["exit"], s["n"], s["pf1"], s["pf2"], s["p"], s["days"], s["mfs"], s["mkts"], verdict(r, s), "yes" if i in surv else "no") for i, (r, s) in enumerate(res)) + "\n")
        return
    if len(a) < 5: raise SystemExit("REFUSED: --read needs the held-out extract and Desk A's print file")
    check_allow(a[3]); pb = open(a[4], "rb").read()
    if not pb.strip(): raise SystemExit("REFUSED: Desk A's print file is empty")
    pr_sha = hashlib.sha256(pb).hexdigest(); held = load_markets(a[3]); fby = feature_maps(held)
    res, k, surv, m = run(batch, held, fby, cuts)
    print("label: unread by ENGINE1, seen by earlier development cards | batch", batch, "rules", m, "BH m", m, "survivors", k, "desk_a_print_sha256", pr_sha)
    out = os.environ.get("OUTLIST")
    lines = ["%d %s %d %d %s %s:%s %s n %d pf1 %s pf2 %s p %.12e days %d mfs %d mkts %d %s survivor %s" % (i, r["series"], r["bucket"], r["band"], r["side"], r["fname"], r["cls"], r["exit"], s["n"], "%.12f" % s["pf1"] if s["pf1"] is not None else "-", "%.12f" % s["pf2"] if s["pf2"] is not None else "-", s["p"], s["days"], s["mfs"], s["mkts"], verdict(r, s), "yes" if i in surv else "no") for i, (r, s) in enumerate(res)]
    if out: open(out, "w").write("\n".join(lines) + "\n")
    print(collections.Counter(v.split(" survivor")[0].split(" mkts ")[1].split(" ", 1)[1].split(" at ")[0] for v in lines))
if __name__ == "__main__": main(sys.argv[1:])
