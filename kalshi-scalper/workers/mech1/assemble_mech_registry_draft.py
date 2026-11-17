#!/usr/bin/env python3
"""Assembles MECH_REGISTRY_DRAFT_B.json from build_mech_registry_draft.py's entries file and declined_patterns.json. Usage: assemble_mech_registry_draft.py <entries.json> <declined_patterns.json> <out.json>"""
import json, sys, collections
e = json.load(open(sys.argv[1])); d = json.load(open(sys.argv[2]))
ents = e["entries"]
out = {"note": "MECH_REGISTRY first draft by Desk B (Idea Desk B), Nov 17 2026, for Desk A (schema owner) and the Verification Analyst's audit. NOT signed, NOT reviewed. No outcome number was read or stored.",
       "schema": "the six fields of MECHANISM_ENGINE_SPEC.md (rnd-queue 785fe85a4): market_family, signal_field, clock, entry_type, exit_type, side_rule; values as written in that spec where a keyword matched, else the default shown in `inferred`'s complement",
       "declined_patterns": d["patterns"], "test_entries": ents,
       "counts": {"declined_patterns": len(d["patterns"]), "test_entries": len(ents), "by_status": dict(collections.Counter(x["status"] for x in ents)), "by_confidence": dict(collections.Counter(x["confidence"] for x in ents))}}
json.dump(out, open(sys.argv[3], "w"), indent=1)
print(out["counts"])
