#!/usr/bin/env python3
"""Run MENTTWIN once: python3 -I menttwin_run.py <root>. Prints counts first, then hold-to-settle at 1c (primary) and 2c, 10 contracts."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_core as K
import menttwin as P

def main(root):
    es, why, npairs = P.entries(root)
    out = {"family": "MENTTWIN", "label": "candle replay, upper bound, not fill-checked", "pairs": npairs, "decisions": why, "n": len(es)}
    for k, h in (("1c", 0.01), ("2c", 0.02)):
        a = K.aggregate(es, "H", h, P.N)
        out[k] = {x: (None if (isinstance(v, float) and v != v) else (round(v, 4) if isinstance(v, float) else v)) for x, v in a.items()}
    p1, p2 = out["1c"], out["2c"]
    ok = (p1["pf"] or 0) >= 1.3 and (p1["half1"] or 0) >= 1.0 and (p1["half2"] or 0) >= 1.0 and (p2["pf"] or 0) >= 1.0
    out["bar"] = ("no evidence at n = %d" % len(es)) if len(es) < 100 else ("PASS (paper bar)" if ok else "fail")
    out["kill_fast"] = (p1["pf"] is not None and p1["pf"] < 1.0)
    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    return out

if __name__ == "__main__":
    main(sys.argv[1])
