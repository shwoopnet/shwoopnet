"""UNDERDOG2X supplement (Auditor B 16:03Z): how often variant (a) has a 2x trigger at or before close - 180 but no sellable mark from it to close - 180, so it is sold by the time rule (labelled "time")."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import underdog2x as U
folder, out = sys.argv[1:3]
U.hm_guard.refuse_all([folder, out])
mk, cd, _ = U.load(folder)
n_entries = n_trig = n_fall = 0
for t in sorted(mk, key=lambda x: (mk[x][1], x)):
    ser, close, res = mk[t]
    en = U.entry(cd.get(t, {}), close)
    if not en:
        continue
    n_entries += 1
    c = cd[t]; marks = sorted(k for k in c if en["end"] < k <= close - 60)
    trig = next((k for k in marks if k <= close - 180 and U.side_bid(c[k], en["side"]) is not None and U.side_bid(c[k], en["side"]) >= 2 * en["e"] - U.EPS), None)
    if trig is None:
        continue
    n_trig += 1
    if not any(trig <= k <= close - 180 and U.sellable(c[k], en["side"]) for k in marks):
        n_fall += 1
json.dump({"entries": n_entries, "a_2x_trigger_by_close_minus_180": n_trig, "a_trigger_but_sold_by_time_rule": n_fall}, open(out, "w"), indent=1, sort_keys=True)
