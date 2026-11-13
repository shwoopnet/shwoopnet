#!/usr/bin/env python3
"""INPLAYJUMP second-scorer READER for landed folders (Testing Desk). A thin wrapper: it imports the frozen inplayjump_second.py (sha256 98fbd4ee73adfd08...) and changes nothing in it.
Usage: python3 -I inplayjump_read.py counts <family> --lists <run folders> --candles <run folders>
       python3 -I inplayjump_read.py full   <family> --lists ... --candles ... --clean <auditor B reference>   (the full read joins results; refused without the Auditor B CLEAN reference, Rule 16)
Families: ESOCCER, ITF_TENNIS, TABLE_TENNIS, CHALLENGER_TENNIS, EBASKETBALL. `counts` never reads a result field."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import inplayjump_second as ij

FROZEN_PREFIX = "98fbd4ee73adfd08"
h = hashlib.sha256(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "inplayjump_second.py"), "rb").read()).hexdigest()
if not h.startswith(FROZEN_PREFIX): raise SystemExit("refused: inplayjump_second.py is not the frozen build (%s)" % h[:16])
a = sys.argv[1:]
if len(a) < 5 or a[0] not in ("counts", "full") or "--lists" not in a or "--candles" not in a: raise SystemExit(__doc__)
mode, fam = a[0], a[1]
i, j = a.index("--lists"), a.index("--candles")
cl = a.index("--clean") if "--clean" in a else None
ends = sorted(x for x in (i, j, cl) if x is not None) + [len(a)]
span = lambda s: a[s + 1: next(e for e in ends if e > s)]
lists, candles = span(i), span(j)
if mode == "full" and (cl is None or not span(cl)): raise SystemExit("refused: the full read needs --clean <Auditor B reference> (Rule 16)")
spec = ij.load_series(); ms, counts = ij.build_matches(spec, lists)
idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candles).items()}
have = [m for m in ms if m["family"] == fam and any(t in idx for t in m["codes"].values())]
dev = next(f for f in spec["families_ranked_by_events"] if f["family"] == fam)["development"]
out = {"family": fam, "counts_first": counts, "matches_with_candles": len(have), "start_check": ij.start_check(have)}
if mode == "counts": out["report"] = ij.family_run(have, idx)[0]
else: out["full"] = ij.score_family(have, idx, ij.ts_of(dev["closes_from"]), ij.ts_of(dev["closes_before"]))
out["label"] = "provisional, one build; selected on development; candle freshness measured on Bitcoin 15 minute only, not on these markets" + ("; NO result read" if mode == "counts" else "")
print(json.dumps(out, indent=1, default=str))
