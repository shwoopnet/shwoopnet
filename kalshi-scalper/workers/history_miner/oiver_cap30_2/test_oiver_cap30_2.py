"""Checks oiver_cap30_2.py against EXPECTED_BY_HAND.md on inv/windows.csv. Prints MISMATCHES [] when all agree."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oiver_cap30_2 as S

D = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(D, "inv", "windows.csv")
o = S.run("dev", W)
bad = []
exp = {"removed_share": 0.4,
       "counts": {"oi_below": 1, "cheap_skipped": 1, "not_two_sided": 2, "held_out_ignored": 1, "above_cap": 2},
       "parent": {"n": 5, "pf": 1.429194, "net": 0.4925, "mean": 0.0985, "half1_pf": 2.436508, "half2_pf": 1.048048, "net_per_contract_week": 0.4925},
       "version": {"n": 3, "pf": 5.206349, "net": 1.325, "mean": 0.441667, "half1_pf": "inf", "half2_pf": 2.769841, "net_per_contract_week": 1.325},
       "takeover_info": {"pf_lift_ge_0.10": True, "net_week_not_lower": True, "half2_not_worse": True, "signals_ge_60": False},
       "kills_info": {"removed_more_than_half": False, "pf_below_parent": False},
       "label": "no evidence at n = 3"}
for k, v in exp.items():
    if o.get(k) != v:
        bad.append((k, o.get(k), v))


def refused(fn, what):
    try:
        fn()
    except (S.Stop, SystemExit) as e:
        print("refused", what, "->", str(e)[:70]); return
    bad.append(("not refused", what))


refused(lambda: S.run("held", W), "held mode")
hd = os.path.join(tempfile.mkdtemp(), "HELDOUT_x"); os.makedirs(hd)
refused(lambda: S.run("dev", os.path.join(hd, "w.csv")), "HELDOUT_ path")
odd = os.path.join(tempfile.mkdtemp(), "w.csv")
open(odd, "w").write(open(W).read().replace(",yes\n", ",YES\n", 1))
refused(lambda: S.run("dev", odd), "odd result text")
for bad_close, what in ((1789171199, "a row just before the range"), (1794182400, "a row at 2026-11-09T00:00Z")):
    rr = os.path.join(tempfile.mkdtemp(), "w.csv")
    open(rr, "w").write(open(W).read().replace(",1794000900,", ",%d," % bad_close, 1))
    refused(lambda: S.run("dev", rr), what)
import csv as _csv
vv = os.path.join(tempfile.mkdtemp(), "w.csv")
rows = list(_csv.reader(open(W))); hdr = rows[0]
byname = {r[0].split("-")[1]: r for r in rows[1:]}
w11 = list(byname["W1"]); w11[0] = "KXBTC15M-W11"; w11[1] = "1794009000"; w11[hdr.index("result")] = "void"
w12 = list(byname["W3"]); w12[0] = "KXBTC15M-W12"; w12[1] = "1794009900"; w12[hdr.index("result")] = ""
with open(vv, "w", newline="") as f:
    _csv.writer(f, lineterminator="\n").writerows(rows + [w11, w12])
ov = S.run("dev", vv)
want = dict(o["counts"], void_dropped=2)
if ov["counts"] != want or {k: ov[k] for k in ("parent", "version", "removed_share", "label")} != {k: o[k] for k in ("parent", "version", "removed_share", "label")}:
    bad.append(("void variant", ov["counts"]))
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
