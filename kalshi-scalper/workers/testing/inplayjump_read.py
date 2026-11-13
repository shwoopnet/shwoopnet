#!/usr/bin/env python3
"""INPLAYJUMP second-scorer READER for landed folders (Testing Desk). A thin wrapper: it imports the frozen inplayjump_second.py and scorekit.py (both hash-pinned below) and changes nothing in them.
Usage: python3 -I inplayjump_read.py counts <family> --lists <run folders> --candles <run folders>
       python3 -I inplayjump_read.py full   <family> --lists ... --candles ... --clean "scorer=<16 hex>;wrapper=<16 hex>;scorekit=<16 hex>;runs=<folder name>,<folder name>,..."
Families: ESOCCER, ITF_TENNIS, TABLE_TENNIS, CHALLENGER_TENNIS, EBASKETBALL.
`counts` joins and prints no result. (It does load the markets' result field into memory, via scorekit.markets / build_matches, as the loaders do; nothing prints it or uses it.)
`full` is refused without the Auditor B CLEAN string (Rule 16: it must carry the three hashes below and the name of EVERY run folder given), and it runs the counts first: if the family's one-way cost line is above 4c
(registration: a family closed on cost stops there) or its start check says 'start not derivable' (Amendment 1: no result of it is read), it prints the counts and joins NO result.
Known gap, accepted: scorekit's held-out guard is case-sensitive ('HELDOUT_'); its loaders skip a non-200 or truncated row without a word (Auditor B's structure check of each run covers it)."""
import sys, os, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
H = lambda n: hashlib.sha256(open(os.path.join(HERE, n), "rb").read()).hexdigest()
PIN = {"scorer": ("inplayjump_second.py", "87ad2e0179e8fe43"), "scorekit": ("scorekit.py", "02728f2afdfe62a9")}
for key, (fn, pre) in PIN.items():
    if not H(fn).startswith(pre): raise SystemExit("refused: %s is not the frozen build (%s)" % (fn, H(fn)[:16]))
import scorekit as k
import inplayjump_second as ij

a = sys.argv[1:]
if len(a) < 5 or a[0] not in ("counts", "full") or "--lists" not in a or "--candles" not in a: raise SystemExit(__doc__)
mode, fam = a[0], a[1]
flags = sorted(x for x in (a.index("--lists"), a.index("--candles"), a.index("--clean") if "--clean" in a else None) if x is not None)
span = lambda s: a[s + 1: next((e for e in flags if e > s), len(a))]
lists, candles = span(a.index("--lists")), span(a.index("--candles"))
if mode == "full":
    cl = " ".join(span(a.index("--clean"))) if "--clean" in a else ""
    parts = dict(p.split("=", 1) for p in cl.split(";") if "=" in p)
    need = {"scorer": H("inplayjump_second.py")[:16], "wrapper": H("inplayjump_read.py")[:16], "scorekit": H("scorekit.py")[:16]}
    if any(parts.get(x) != v for x, v in need.items()): raise SystemExit("refused: the full read needs the Auditor B CLEAN string carrying scorer, wrapper and scorekit hashes: %s" % need)
    runs = [r for r in parts.get("runs", "").split(",") if r]
    for f in lists + candles:
        if os.path.basename(os.path.normpath(f)) not in runs: raise SystemExit("refused: run folder %s is not named in the CLEAN string" % f)
spec = ij.load_series(); ms, counts = ij.build_matches(spec, lists)
idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candles).items()}
have = [m for m in ms if m["family"] == fam]          # ALL matches listed in the development window (Head ruling Nov 13: the start check counts a match with no candle against it; the placebo order runs over all of them)
with_candles = sum(1 for m in have if any(t in idx for t in m["codes"].values()))
dev = next(f for f in spec["families_ranked_by_events"] if f["family"] == fam)["development"]
sc = ij.start_check(have)
out = {"family": fam, "counts_first": counts, "matches_listed_in_window": len(have), "matches_with_candles": with_candles, "start_check": sc}
rep = ij.family_run(have, idx)[0]; out["report"] = rep
tail = "provisional, one build; selected on development; candle freshness measured on Bitcoin 15 minute only, not on these markets"
if mode == "counts": out["label"] = tail + "; NO result read"
else:
    stop = None
    if fam in sc and not sc[fam]["start_derivable"]: stop = "start not derivable (Amendment 1): no result of this family is read"
    elif rep["cost_over_4c"] is True: stop = "closed on cost (one-way median over every qualifying decision above 4c): the family stops there, no result is read"
    if stop: out["full"] = {"verdict": "STOPPED", "reason": stop}; out["label"] = tail + "; NO result read"
    else: out["full"] = ij.score_family(have, idx, ij.ts_of(dev["closes_from"]), ij.ts_of(dev["closes_before"])); out["label"] = tail
print(json.dumps(out, indent=1, default=str))
