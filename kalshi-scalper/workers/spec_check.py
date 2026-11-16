"""spec_check.py (Desk A, Nov 16 2026): checks a FAMILY SPEC file against ENGINE_FAMILY_SPEC_FORMAT.md and prints the rules it will try.
  python3 -I spec_check.py <spec.json>      exit code 0 = complete, 1 = problems printed.
Checks presence and shape only; Auditor B signs the content (data, cuts, look-ahead)."""
import sys, json, re
KINDS = ("grid15m", "perps_grid", "event_rule")
TOP = ("holds", "look_ahead", "sources", "subset_rationale", "halves", "fee_form", "n_floor", "id", "desk", "date_registered", "kind", "card", "needs_new_code", "uniqueness", "data", "split", "costs", "gates", "tries", "prediction", "kill", "kill_fast", "outputs")
BUCKETS = set(range(120, 841, 60)); BANDS = set(range(1, 19)); SIDES15 = {"yes", "no", "cheap", "favourite"}; SIDESP = {"long", "short"}
EX15 = {"H", "T", "S", "B", "M180", "M60"}; EXP = {"T3", "T10", "T15", "T30", "TS15", "TS30", "T60", "T240", "TC", "TO"}
F15 = {"none", "oi3", "oi6", "vol3", "mom1", "mom3", "mom5", "spread"}; FP = {"none", "mom1", "mom3", "mom5", "mom15", "spread", "tod", "orb", "sess"}
FEATURE_OPTIONS = {"none": 1, "oi3": 3, "oi6": 3, "vol3": 3, "mom1": 3, "mom3": 3, "mom5": 3, "spread": 3}
PERP_OPTIONS = {"none": 1, "mom1": 2, "mom3": 2, "mom5": 2, "mom15": 2, "spread": 3, "tod": 5, "orb": 2, "sess": 2}
def check(s):
    p = []
    for k in TOP:
        if k not in s: p.append("missing field: " + k)
    if p: return p, None
    if not re.fullmatch(r"[A-Z0-9]{2,16}", s["id"]): p.append("id must be 2 to 16 capitals or digits")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["date_registered"]): p.append("date_registered must be ISO")
    if s["kind"] not in KINDS: p.append("kind must be one of %s" % (KINDS,)); return p, None
    for k in ("closest_existing", "declined_list_rows_checked", "difference", "family_flag"):
        if k not in s["uniqueness"] or not s["uniqueness"][k]: p.append("uniqueness." + k + " is required")
    for k in ("loader", "loader_sha256", "ticker_wall", "window", "held_out_map_checked_by", "independence_note"):
        if k not in s["data"]: p.append("data." + k + " is required")
    if "loader_sha256" in s["data"] and not re.fullmatch(r"[0-9a-f]{64}", s["data"]["loader_sha256"]): p.append("data.loader_sha256 must be 64 hex characters")
    for h in s["holds"]:
        for k in ("label", "start_epoch", "card", "status"):
            if k not in h: p.append("holds entry missing " + k)
        if not isinstance(h.get("start_epoch"), int): p.append("holds start_epoch must be an integer epoch (re-derive with calendar.timegm)")
        if h.get("end_epoch") is not None and not isinstance(h.get("end_epoch"), int): p.append("holds end_epoch must be an integer epoch or null")
    if not s["holds"]: p.append("holds must list every window the spec touches (an empty table is a claim, say so in a row)")
    if not s["look_ahead"]: p.append("look_ahead must say, for each input, the last timestamp it may use")
    if s["sources"].get("new_host") is not False or not s["sources"].get("names"): p.append("sources must name the data sources and state new_host false")
    if "ceil(round(" not in s["fee_form"]: p.append("fee_form must be the standing ceil(round(...)) form with the void rule")
    if "no evidence" not in s["n_floor"]: p.append("n_floor must carry the standing 'no evidence at n = x' text")
    if s["split"].get("mode") not in ("fixed_dates", "forward_only"): p.append("split.mode must be fixed_dates or forward_only")
    for k in ("min_n", "pf_primary", "pf_secondary", "bh_alpha"):
        if k not in s["gates"]: p.append("gates." + k + " is required")
    if s["gates"].get("pf_primary", 0) < s["gates"].get("pf_secondary", 0): p.append("pf_primary must be at least pf_secondary")
    if not s["prediction"] or not s["kill"]: p.append("prediction and kill must be written")
    rules = None
    if s["kind"] in ("grid15m", "perps_grid"):
        g = s.get("grid")
        if not g: return p + ["grid is required for this kind"], None
        perps = s["kind"] == "perps_grid"
        bk = set(g.get("buckets", [])); bd = set(g.get("bands", [])); sd = set(g.get("side_rules", [])); fl = set(g.get("filters", [])); ex = set(g.get("exits", []))
        if not perps:
            if not bk or not bk <= BUCKETS: p.append("buckets must be a nonempty subset of 120 to 840 step 60")
            if not bd or not bd <= BANDS: p.append("bands must be a nonempty subset of 1 to 18")
        if not sd or not sd <= (SIDESP if perps else SIDES15): p.append("side_rules outside the library")
        if not fl or not fl <= (FP if perps else F15): p.append("filters outside the library (a new one is needs_new_code)")
        if not ex or not ex <= (EXP if perps else EX15): p.append("exits outside the library (a new one is needs_new_code)")
        if not p:
            opts = sum((PERP_OPTIONS if perps else FEATURE_OPTIONS)[f] for f in fl)
            rules = (1 if perps else len(bk) * len(bd)) * len(sd) * len(ex) * opts
    else:
        e = s.get("event")
        if not e or "scorer_plugin" not in e or "scorer_plugin_sha256" not in e: p.append("event.scorer_plugin and its sha256 are required for event_rule")
        pl = s.get("plugin") or {}
        for k in ("file", "sha256", "hand_case_sha256", "auditor_clean_date"):
            if k not in pl: p.append("plugin." + k + " is required for event_rule (a spec cannot name a plugin Auditor B has not cleared)")
        rules = s["tries"].get("rules_this_spec")
    if rules is not None and s["tries"].get("rules_this_spec") != rules: p.append("tries.rules_this_spec is %r, the grid gives %r" % (s["tries"].get("rules_this_spec"), rules))
    return p, rules
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    p, r = check(json.load(open(sys.argv[1])))
    for x in p: print("PROBLEM:", x)
    print("rules this spec will try:", r); sys.exit(1 if p else 0)
