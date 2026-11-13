"""Runs resting2.run() on the invented rows in inv/ and checks every figure against expected_by_hand.json (committed first: 46ee8786, re-worked f74eb602); then the refusals.
Tests pass a clock and a temporary marker folder to run() directly; the command line has no clock option. Exit 1 on any mismatch."""
import json, math, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import resting2 as R
E = json.load(open(os.path.join(HERE, "expected_by_hand.json")))
bad = []
def eq(a, b):
    if isinstance(b, float) and not isinstance(a, bool):
        return a is not None and a != "inf" and abs(a - b) <= 2e-6
    return a == b
inv = os.path.join(HERE, "inv")
dm = os.path.join(tempfile.mkdtemp(), "DEPTH1_DONE"); open(dm, "w").write("DEPTH1 READ MADE: invented for the test\n")
nc = os.path.join(tempfile.mkdtemp(), "NC15DEPTH1_SCORER_HASH.txt"); open(nc, "w").write("NC15DEPTH1 SCORER HASH: 00 invented CLEAN by Auditor B test\n")
NOW2 = R.iso("2026-12-05T00:00:00Z")
NOW = R.iso("2026-11-20T00:00:00Z")
o = R.run("V1", "dev", os.path.join(inv, "v1run_signals.csv"), [os.path.join(inv, "v1run")], dm, tempfile.mkdtemp(), NOW)
for k, v in E["V1_dev"]["counts"].items():
    if o["counts"].get(k, 0) != v: bad.append(("V1 count", k, o["counts"].get(k), v))
W = {w["ticker"]: w for w in o["windows"]}
for tk, x in E["V1_dev"]["windows"].items():
    w = W[tk]
    for k, v in x.items():
        got = w.get(k) if k != "v25" else None
        if k == "v25":
            src = [s for s in R.window({"ticker": tk, "close_ts": w["close_ts"]}, R.rd(os.path.join(inv, "v1run"), "book"), R.rd(os.path.join(inv, "v1run"), "trades"),
                   {c["ticker"]: c["result"] for c in R.rd(os.path.join(inv, "v1run"), "coverage")}[tk], R.CFG["V1"])["version"].values()]
            got = src[0]
        if not eq(got, v): bad.append(("V1 window", tk, k, got, v))
for k, v in E["V1_dev"]["report"].items():
    if isinstance(v, dict):
        for kk, vv in v.items():
            if o["report"][k][kk] != vv: bad.append(("V1 bar", kk, o["report"][k][kk], vv))
    elif not eq(o["report"][k], v): bad.append(("V1 report", k, o["report"][k], v))
o2 = R.run("V2", "dev", os.path.join(inv, "v2run_signals.csv"), [os.path.join(inv, "v2run")], None, tempfile.mkdtemp(), NOW2, nc)
for k, v in E["V2_dev"]["counts"].items():
    if o2["counts"].get(k, 0) != v: bad.append(("V2 count", k, o2["counts"].get(k), v))
for k, v in E["V2_dev"]["report"].items():
    if not eq(o2["report"][k], v): bad.append(("V2 report", k, o2["report"][k], v))
def refused(fn, tag):
    try:
        fn()
    except SystemExit as e:
        if not str(e).startswith("REFUSED"): bad.append(("odd refusal", tag, str(e)))
        return
    bad.append(("not refused", tag))
md = tempfile.mkdtemp()
refused(lambda: R.run("V1", "dev", os.path.join(inv, "v1run_signals.csv"), [os.path.join(inv, "v1run")], None, md, NOW), "no DEPTH1 marker")
refused(lambda: R.run("V1", "fwd", os.path.join(inv, "v1run_signals.csv"), [os.path.join(inv, "v1run")], dm, md, R.iso("2026-12-31T23:59:59Z")), "fwd before read date")
R.run("V1", "dev", os.path.join(inv, "v1run_signals.csv"), [os.path.join(inv, "v1run")], dm, md, NOW)
refused(lambda: R.run("V1", "dev", os.path.join(inv, "v1run_signals.csv"), [os.path.join(inv, "v1run")], dm, md, NOW), "second run")
held = os.path.join(tempfile.mkdtemp(), "pull", "POLGAPH_LISTS", "2026-11-13T0627Z_43378777252"); os.makedirs(held)
refused(lambda: R.run("V1", "dev", os.path.join(inv, "v1run_signals.csv"), [held], dm, tempfile.mkdtemp(), NOW), "listed run")
bad_dm = os.path.join(tempfile.mkdtemp(), "D"); open(bad_dm, "w").write("x\n")
refused(lambda: R.run("V1", "dev", os.path.join(inv, "v1run_signals.csv"), [os.path.join(inv, "v1run")], bad_dm, tempfile.mkdtemp(), NOW), "marker without its first line")
refused(lambda: R.run("V2", "dev", os.path.join(inv, "v2run_signals.csv"), [os.path.join(inv, "v2run")], None, tempfile.mkdtemp(), R.iso("2026-12-04T23:59:59Z"), nc), "V2 before Dec 5")
refused(lambda: R.run("V2", "dev", os.path.join(inv, "v2run_signals.csv"), [os.path.join(inv, "v2run")], None, tempfile.mkdtemp(), NOW2, None), "V2 without the NC15DEPTH1 record")
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
