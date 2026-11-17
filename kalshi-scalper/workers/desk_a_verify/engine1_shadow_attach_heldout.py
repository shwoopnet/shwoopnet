"""Attaches the held-out verdicts of the batch B and batch C reads (prints confirmed at 1e-9 by two builds, Auditor B, Nov 17 2026) beside each pick of a shadow list. The spec object (and so spec_sha256) is NOT touched; only the 'heldout_verdict' field changes. Label: 'read n times by ENGINE1 batches' (the 190 first, batch B second, batch C third); the in-print label 'unread by ENGINE1' is superseded by ENGINE1_HELDOUT_BC_HEADER_NOTE_NOV17.md. A held-out verdict is not forward n and not a pass.
  python3 -I engine1_shadow_attach_heldout.py <list.json> <out.json> <batchB print> <batchC print>"""
import sys, json
def main(lst, out, *prints):
    idx = {}
    for p in prints:
        for r in json.load(open(p))["rows"]: idx[(r["spec"], r["series"], r["bucket"], r["band"], r["side"], tuple(r["filter"]), r["exit"])] = r
    d = json.load(open(lst)); miss = 0
    for s in d["specs"]:
        e = s["spec"]["entry"]; f = tuple(e["filter"].split(":")); sp = s["spec"].get("found_by_spec") or "ENGB4XBTC"
        r = idx.get((sp, s["spec"]["market"], e["seconds_left"], e["price_band_5c"], e["side_rule"], f, s["spec"]["exit"]))
        if r is None: miss += 1; s["heldout_verdict"] = "not found in the prints"; continue
        s["heldout_verdict"] = {"verdict": r["verdict"], "n": r["n"], "n_floor": r["n_floor"], "pf_1c": round(r["pf_1c"], 3), "pf_2c": round(r["pf_2c"], 3), "validate_pf_1c": round(r["validate_pf_1c"], 3), "bh_rank_survivor_in_own_read": bool(r["bh_survivor_all"]), "missing_feature_skips_at_bucket": r["missing_feature_skips_at_bucket"], "label": "read n times by ENGINE1 batches (held-out window Oct 3 to Oct 28 or Nov 3); not forward n, not a pass; the in-print 'unread by ENGINE1' is superseded"}
    d["heldout_read"] = "batch B and batch C prints, sha256 89363527 and e47eb90b, confirmed at 1e-9 (Forensics, Auditor B, Nov 17 2026)"
    json.dump(d, open(out, "w"), indent=1); print(out, len(d["specs"]), "picks; not found", miss)
if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:4], *sys.argv[4:])
