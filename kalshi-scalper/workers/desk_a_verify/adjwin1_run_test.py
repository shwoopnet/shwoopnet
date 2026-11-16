"""python3 -I adjwin1_run_test.py : the table prints every try; refuses via the loader with no allow line."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adjwin1 as A, adjwin1_run as R
T = 1790000000
mk = lambda c, mid_last, res="yes": {"series": "KXWTI15M", "close": c, "result": res, "candles": [(c - 840, .49, .51), (c - 60, mid_last - .01, mid_last + .01), (c + 0, .98, 1.0)]}
w = {"KXWTI15M": [mk(T, .85), {"series": "KXWTI15M", "close": T + 900, "result": "yes", "candles": [(T + 60, .49, .51)]}]}
txt = R.table(A.run(w), {"dropped by the cut": 3})
assert "dropped by the cut" in txt and txt.count("arm R") == 6 and txt.count("arm M") == 6 and "no evidence at n = " in txt, txt
assert "KXWTI15M arm R h0 val n=1" in txt.replace("  ", "") or "arm R h0 val n=1" in txt, txt
rr = subprocess.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "adjwin1_run.py"), "/nonexistent"], capture_output=True, text=True)
assert rr.returncode != 0 and "REFUSED" in rr.stdout + rr.stderr, rr
print("ALL OK")
