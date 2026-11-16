"""HOURBRIDGE1 runner (Desk A, Nov 16 2026): loader -> core -> one JSON report (counts and stats only; no per-event rows).
  python3 -I hourbridge_run.py <quote-data checkout> <out.json>"""
import sys, os, json, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import hourbridge_load as L, hourbridge as H
def main(base, out):
    events, counts = L.load(base)
    rep = H.run(events)
    rep["label"] = "HOURBRIDGE1 development read, Bitcoin only, closes 2026-10-28 to before 2026-11-02; upper bound, not fill-checked; 10 contracts; 2c primary (C8); the days are NOT independent of BOOKIMB1, FLOWHR1, MAKERMID1, MAKERTAIL1, ENTRYREPLAY1 block D and CFRTI-B development; one try; no in-history held-out"
    rep["events"] = len(events); rep["loader_counts"] = counts
    rep["rule_hashes"] = {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest()[:16] for f in ("hourbridge.py", "hourbridge_load.py", "hourbridge_run.py", "engine1_core.py")}
    json.dump(rep, open(out, "w"), indent=1, default=str); print("wrote", out, json.dumps(rep["rule_hashes"]))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
