import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_extract_load as L, engine1_batchb2 as B2, engine1_enum as N
tab = json.load(open(sys.argv[2]))["all_series_buckets"]
def fc(sm, name):
    row = tab[sm[0]["series"]]; return {int(b): ((v["c1"], v["c2"]) if v["c1"] is not None else None) for b, v in row.items()}
B2.feature_cuts = fc
wa = L.load(sys.argv[1])[0]
rep = B2.run_family(wa, "ENGB2VSPIKE")
old = json.load(open(sys.argv[3]))
print("search_passes", rep["search_passes"], "run", old["search_passes"], "| validate_bar_passes", rep["validate_bar_passes"], "run", old["validate_bar_passes"])
a = json.dumps(rep["validate_bar_list"], sort_keys=True); b = json.dumps(old["validate_bar_list"], sort_keys=True)
print("validate_bar_list identical to the run's:", a == b)
