"""python3 -I engine1_run_test.py : the bar-passer summary on invented rows."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_run as R
L = [dict(series="KXA", side="favourite", exit="H", filter=None, bucket=300, family="x"), dict(series="KXA", side="favourite", exit="B", filter=("oi3", "up"), bucket=300, family="y"), dict(series="KXB", side="yes", exit="H", filter=("spread", "low"), bucket=240, family="x")]
s = R.summarize(L)
assert s["n"] == 3 and s["by_series"] == {"KXA": 2, "KXB": 1} and s["by_exit"] == {"H": 2, "B": 1} and s["by_filter_feature"] == {"none": 1, "oi3": 1, "spread": 1} and s["max_in_one_series_side"] == 2 and s["top_series_side"][0] == "KXA|favourite 2", s
assert R.summarize([])["n"] == 0 and R.summarize([])["max_in_one_series_side"] == 0
print("ALL OK")
