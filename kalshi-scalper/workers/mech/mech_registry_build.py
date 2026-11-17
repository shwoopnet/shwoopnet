"""Builds MECH_REGISTRY.json from mech_registry_rows.R and validates every row. python3 -I mech_registry_build.py <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import mech_schema as S, mech_registry_rows as RR
EVIDENCE = {}
def build():
    out = []
    for r in RR.R:
        e = dict(zip(("id", "status", "market", "signal", "clock", "entry", "exit", "side", "source", "confidence"), r[:10]))
        if len(r) > 11: e.update(r[11])
        e["verified"] = (e["confidence"] == "hand_read")
        if len(r) > 10: e["kind"] = r[10]
        else: e["kind"] = "signature"
        errs = S.validate_entry(e)
        if errs: raise SystemExit("INVALID %s: %s" % (e["id"], errs))
        if e["id"] in EVIDENCE: e["evidence_market_scope"] = EVIDENCE[e["id"]]
        out.append(e)
    import glob
    have = {e["id"]: i for i, e in enumerate(out)}
    for f in sorted(glob.glob(os.path.join(here, "desk_b_rows", "*.json"))):
        for e in json.load(open(f))["entries"]:
            e = dict(e); e.setdefault("kind", "signature"); e["verified"] = (e.get("confidence") == "hand_read"); e["source_batch"] = "Desk B " + os.path.basename(f)
            errs = S.validate_entry(e)
            if errs: raise SystemExit("INVALID Desk B row %s: %s" % (e.get("id"), errs))
            if e["id"] in have:
                mine = out[have[e["id"]]]
                if e["verified"] and not mine["verified"]: out[have[e["id"]]] = e        # a hand-read row replaces my unverified one
                continue
            have[e["id"]] = len(out); out.append(e)
    OVERRIDES = {"SPIKE1": dict(market="15m_noncrypto", signal="price_change", clock="fixed_time_to_close", exit="hold_to_settle", side="fade", confidence="hand_read", source="VA Nov 17: 15 minute mid spike (3 sd and 5c in 2 minutes), non-crypto series, buy the cheap side, held"),
                 "SNAPBACK1": dict(clock="any_minute", exit="bracket", confidence="hand_read", source="VA Nov 17: liquidation-cascade fade on the Kalshi BTC and ETH perps (1 hour move of k ATR with open interest down), stop and target, 6 hour time stop"),
                 "MENT1": dict(market="mentions"),
                 "SWING1": dict(market="sports", signal="price_change", clock="any_minute", exit="hold_to_settle", side="fade", confidence="hand_read", source="VA Nov 17 (README line 8383): in-play swing overreaction on college football and MLB game winners, the YES mid falls 0.25 within 5 minutes, buy the faller's cheap side 5c to 30c, held"),
                 "PERPEQ2": dict(clock="time_of_day", confidence="hand_read", source="VA Nov 17 read the registration: sector pair ratio z at 7 grid times 10:00 to 15:55 ET, z of 2, fade the rich leg, 18 hour hold"),
                 "PERPEQ3": dict(clock="any_minute", confidence="hand_read", source="VA Nov 17 read the registration: stock perp premium to its reference in cash hours, samples 09:50 to 15:25 ET, premium of 10 bp or 3 times the spread, fade, exit 90 minutes later"),
                 "PERPEQ4": dict(side="fade", confidence="hand_read", source="VA Nov 17 read the registration: ETF perp against the index perp, grid as PERPEQ2, fade")}
    for e in out:
        if e["id"] in OVERRIDES: e.update(OVERRIDES[e["id"]]); e["verified"] = (e["confidence"] == "hand_read"); e["source_note"] = "field override by Desk A on the VA's second-pass reading"
    ids = [e["id"] for e in out]
    if len(set(ids)) != len(ids): raise SystemExit("duplicate ids")
    return out
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    reg = build(); doc = {"registry": "MECH_REGISTRY v0", "date": "2026-11-17", "spec": "MECHANISM_ENGINE_SPEC.md (rnd-queue 785fe85a4)", "count": len(reg), "signatures": sum(1 for e in reg if e["kind"] == "signature"), "patterns": sum(1 for e in reg if e["kind"] == "pattern"),
        "coverage_note": "v0: README section titles, the 7e declined list, CLAUDE.md strategies and the head of the deflation ledger. NOT the whole ledger (about 300 lines). A row from_title or from_ledger_row was not checked against its rule text; the VA audits on Nov 19.",
        "rows_sha256": hashlib.sha256(json.dumps(reg, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "entries": reg}
    json.dump(doc, open(sys.argv[1], "w"), indent=1); print(doc["count"], "entries,", doc["signatures"], "signatures,", doc["patterns"], "patterns, rows sha", doc["rows_sha256"][:8])
