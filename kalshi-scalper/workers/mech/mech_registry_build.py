"""Builds MECH_REGISTRY.json from mech_registry_rows.R and validates every row. python3 -I mech_registry_build.py <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import mech_schema as S, mech_registry_rows as RR
def build():
    out = []
    for r in RR.R:
        e = dict(zip(("id", "status", "market", "signal", "clock", "entry", "exit", "side", "source", "confidence"), r[:10]))
        if len(r) > 10: e["kind"] = r[10]
        else: e["kind"] = "signature"
        errs = S.validate_entry(e)
        if errs: raise SystemExit("INVALID %s: %s" % (e["id"], errs))
        out.append(e)
    ids = [e["id"] for e in out]
    if len(set(ids)) != len(ids): raise SystemExit("duplicate ids")
    return out
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    reg = build(); doc = {"registry": "MECH_REGISTRY v0", "date": "2026-11-17", "spec": "MECHANISM_ENGINE_SPEC.md (rnd-queue 785fe85a4)", "count": len(reg), "signatures": sum(1 for e in reg if e["kind"] == "signature"), "patterns": sum(1 for e in reg if e["kind"] == "pattern"),
        "coverage_note": "v0: README section titles, the 7e declined list, CLAUDE.md strategies and the head of the deflation ledger. NOT the whole ledger (about 300 lines). A row from_title or from_ledger_row was not checked against its rule text; the VA audits on Nov 19.",
        "rows_sha256": hashlib.sha256(json.dumps(reg, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "entries": reg}
    json.dump(doc, open(sys.argv[1], "w"), indent=1); print(doc["count"], "entries,", doc["signatures"], "signatures,", doc["patterns"], "patterns, rows sha", doc["rows_sha256"][:8])
