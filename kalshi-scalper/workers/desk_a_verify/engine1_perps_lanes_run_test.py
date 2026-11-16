"""python3 -I engine1_perps_lanes_run_test.py : the census reader on a tiny tab-separated file (both column names), refusals and unknown values."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_perps_lanes_run as R
f = tempfile.mktemp(); open(f, "w").write("ticker\tclass\tpage_max_leverage\tpage_max_source\nKXNVDAPERP\tEquities\t4.5\towner\nKXXOMPERP\tEnergy\tunknown\t\nKXAAPLPERP\tEquities\t4.9x\towner\n")
assert R.read_census(f) == {"KXNVDAPERP": 4.5, "KXAAPLPERP": 4.9}
g = tempfile.mktemp(); open(g, "w").write("ticker\tclass\tpage_max_owner_pasted\nKXMUPERP\tEquities\t3.3\nKXAMDPERP\tEquities\t\n")
assert R.read_census(g) == {"KXMUPERP": 3.3}
h = tempfile.mktemp(); open(h, "w").write("ticker\tclass\tmax_leverage\nKXMUPERP\tEquities\t3.3\n")
try: R.read_census(h); raise AssertionError("accepted a file with no page max column")
except SystemExit: pass
print("CENSUS READER OK")
