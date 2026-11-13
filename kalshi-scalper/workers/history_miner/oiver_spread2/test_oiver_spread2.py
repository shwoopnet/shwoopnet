"""Checks oiver_spread2.py against EXPECTED_BY_HAND.md on inv/windows.csv. Prints MISMATCHES [] when all agree."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oiver_spread2 as S

D = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(D, "inv", "windows.csv")
o = S.run("dev", W)
bad = []
exp = {"removed_share": 0.4,
       "counts": {"oi_below": 1, "cheap_skipped": 1, "no_quote": 2, "held_out_ignored": 1, "spread_wide": 2},
       "parent": {"n": 5, "pf": 1.373198, "net": 0.44, "mean": 0.088, "half1_pf": 2.329231, "half2_pf": 1.009368, "net_per_contract_week": 36.96},
       "version": {"n": 3, "pf": 4.818452, "net": 1.283, "mean": 0.427667, "half1_pf": "inf", "half2_pf": 2.565476, "net_per_contract_week": 107.772},
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
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
