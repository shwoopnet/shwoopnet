"""Runs tempblend2.py on rows_madeup.jsonl and checks every figure against expected_by_hand.json (worked out by hand before the first run). Exit 1 on any mismatch."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(tempfile.mkdtemp(), "o.json")
subprocess.run([sys.executable, "-I", os.path.join(HERE, "tempblend2.py"), os.path.join(HERE, "rows_madeup.jsonl"), out], check=True, capture_output=True)
o, e = json.load(open(out)), json.load(open(os.path.join(HERE, "expected_by_hand.json")))
bad, dec = [], {d["city"]: d for d in o["decisions"]}
for c, x in e["per_row"].items():
    if x[0] == "outside windows":
        bad += [c] if c in dec else []
        continue
    d = dec[c]
    if d["status"] != x[0]:
        bad.append((c, d["status"])); continue
    if x[0] == "bet":
        b = d["bet"]
        if (b["side"], b["K"]) != (x[1], x[2]) or abs(b["pnl"] - x[3]) > 1e-9 or (len(x) > 4) != b["void"]:
            bad.append((c, b))
for sec in ("development", "held_out"):
    for k, v in e[sec].items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                ov = o[sec][k][kk]
                if (isinstance(vv, float) and abs(ov - vv) > 1e-6) or (not isinstance(vv, float) and ov != vv):
                    bad.append((sec, k, kk, ov, vv))
        elif o[sec][k] != v:
            bad.append((sec, k, o[sec][k], v))
print("MISMATCHES", bad)
sys.exit(1 if bad else 0)
