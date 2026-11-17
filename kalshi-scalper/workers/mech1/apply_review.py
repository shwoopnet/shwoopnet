#!/usr/bin/env python3
"""Applies review_overrides_*.json to MECH_ROWS_B_BATCH3_KEYWORD.json. Overrides 1 to 3 were read from registration paragraphs (confidence hand_read); overrides 4 from the first 300 characters of a registration file (from_ledger_row). Rows without an override stay from_title. Usage: apply_review.py <batch3.json> <out.json>"""
import json, sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema_desk_a_copy as S
rows = json.load(open(sys.argv[1]))["entries"]; ov = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_overrides_*.json"))):
    n = int(os.path.basename(f).split("_")[-1].split(".")[0]); conf = "hand_read" if n <= 3 else "from_ledger_row"
    for k, v in json.load(open(f)).items(): ov[k] = dict(v, **{"confidence": v.get("confidence", conf)})
out = []; changed = 0
for r in rows:
    r = dict(r); o = ov.get(r["id"])
    if o:
        for k, v in o.items():
            if k == "note": r["note"] = v
            else: r[k] = v
        changed += 1
    errs = S.validate_entry(r)
    if errs: raise SystemExit("invalid %s %r" % (r["id"], errs))
    out.append(r)
json.dump({"note": "Desk B batch 3 after review, Nov 17 2026. confidence: hand_read (registration paragraph read), from_ledger_row (first 300 characters of the registration read, signal or side may be partial), from_title (keyword inferred only).", "entries": out}, open(sys.argv[2], "w"), indent=1)
import collections
print("rows %d, overridden %d, by confidence %s" % (len(out), changed, dict(collections.Counter(r["confidence"] for r in out))))
