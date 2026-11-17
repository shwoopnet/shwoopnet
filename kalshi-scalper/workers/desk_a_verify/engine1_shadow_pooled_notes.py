"""Adds the pooled-338 step-up flag and a notes field to each shadow list (picks and spec hashes untouched), and prints one line per pick.
  python3 -I engine1_shadow_pooled_notes.py <bh190.json> <batchB print> <batchC print> <list.json> [<list.json> ...]  (lists are rewritten in place)"""
import sys, json
def main(b190, pb, pc, *lists):
    ps = []; keys = []
    for p in (b190, pb, pc):
        for r in json.load(open(p))["rows"]:
            ps.append(r["p"])
            keys.append(None if p == b190 else (r["spec"], r["series"], r["bucket"], r["band"], r["side"], tuple(r["filter"]), r["exit"]))
    m = len(ps); order = sorted(range(m), key=lambda i: (ps[i], i)); k = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= 0.05 * rank / m: k = rank
    surv = {keys[i] for i in order[:k] if keys[i] is not None}
    print("pooled m=%d survivors=%d" % (m, k))
    NOTE = ("Held-out verdicts attached Nov 17 2026 (read n times by ENGINE1 batches; not forward n, not a pass). Pooled step-up over m = 338: 25 survivors, 17 holds. "
            "real start = first runner log after merge; the start_utc in the spec is the earliest, never earlier than the merge. No outcome before that first log counts.")
    for f in lists:
        d = json.load(open(f))
        for s in d["specs"]:
            e = s["spec"]["entry"]; fl = tuple(e["filter"].split(":")); sp = s["spec"].get("found_by_spec") or "ENGB4XBTC"
            key = (sp, s["spec"]["market"], e["seconds_left"], e["price_band_5c"], e["side_rule"], fl, s["spec"]["exit"])
            hv = s.get("heldout_verdict")
            if isinstance(hv, dict):
                hv["pooled338_bh_survivor"] = key in surv
            print("%s  %s  %s  n=%s  pooled338 survivor=%s" % (f[:14], s["spec"]["id"], hv["verdict"] if isinstance(hv, dict) else hv, hv["n"] if isinstance(hv, dict) else "-", key in surv))
        d["notes"] = (d["notes"] + " | " + NOTE) if isinstance(d.get("notes"), str) and d["notes"] else NOTE
        json.dump(d, open(f, "w"), indent=1)
if __name__ == "__main__": main(*sys.argv[1:]) if len(sys.argv) > 4 else sys.exit(__doc__)
