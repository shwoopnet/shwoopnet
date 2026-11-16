"""python3 -I engine1_perps_lanes_run_test.py : the census reader on a tiny tab-separated file (both column names), refusals and unknown values."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_perps_lanes_run as R
f = tempfile.mktemp(); open(f, "w").write("ticker\tclass\tpage_max_leverage\tpage_max_source\nKXNVDAPERP\tEquities\t4.5\towner\nKXXOMPERP\tEnergy\tunknown\t\nKXAAPLPERP\tEquities\t4.9x\towner\n")
assert {k: v[0] for k, v in R.read_census(f).items()} == {"KXNVDAPERP": 4.5, "KXAAPLPERP": 4.9}
g = tempfile.mktemp(); open(g, "w").write("ticker\tclass\tpage_max_owner_pasted\nKXMUPERP\tEquities\t3.3\nKXAMDPERP\tEquities\t\n")
assert {k: v[0] for k, v in R.read_census(g).items()} == {"KXMUPERP": 3.3}
h = tempfile.mktemp(); open(h, "w").write("ticker\tclass\tmax_leverage\nKXMUPERP\tEquities\t3.3\n")
try: R.read_census(h); raise AssertionError("accepted a file with no page max column")
except SystemExit: pass
# the real shape: page_max and size_max_known columns; gold's size-specific 17.4x is the leverage used
k = tempfile.mktemp(); open(k, "w").write("ticker\tclass\tpage_max\tpage_max_source\tsize_max_known\nKXGOLDPERP\tMetals\t40\towner\t17.4x at $800 (owner ticket)\nKXNVDAPERP\tEquities\t4.5\towner\t\nKXAAVEPERP\tCrypto\tunknown\tnone\t\n")
c = R.read_census(k); assert c["KXGOLDPERP"][0] == 17.4 and "size-specific" in c["KXGOLDPERP"][1] and c["KXNVDAPERP"] == (4.5, "page max (small-size ceiling), no size-specific figure") and "KXAAVEPERP" not in c
print("CENSUS READER OK")
