"""EXITS3 supplement (Auditor B's request 15:55Z): share of T exits whose sale price is at or below the entry price, raw and at h = 1c, 2c."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exits3 as X
card, db, out = sys.argv[1:4]
X.hm_guard.refuse_all([db, out])
mk, cd = X.load(db, X.SERIES[card])
n = 0; le = {0: 0, 1: 0, 2: 0}
for t in sorted(mk, key=lambda x: (mk[x][0], x)):
    close, res = mk[t]
    en = X.ENTRY[card](cd.get(t, {}), close)
    if not en or en == "not two-sided":
        continue
    k, b = X.exit_mark(cd.get(t, {}), en["entry_end"], close, en["side"], en["e"], "T")
    if k is None:
        continue
    n += 1
    for h in (0, 1, 2):
        if max(0.01, b - h / 100) <= min(0.99, en["e"] + h / 100) + 1e-9:
            le[h] += 1
json.dump({"card": card, "T_exits": n, "sale_at_or_below_entry": le}, open(out, "w"), indent=1, sort_keys=True)
