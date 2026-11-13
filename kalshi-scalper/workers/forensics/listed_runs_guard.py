#!/usr/bin/env python3
"""Refuses a landed pull run that kalshi-scalper/workers/HELDOUT_PULL_RUNS.md lists as held-out material (standing rule (h); the Head of R&D's order of 2026-11-13, after Auditor B found
that only deskb_guard and polgaph_second.py checked the list). Logic copied from Desk B's guard as described: a run is refused BY ITS FOLDER NAME (the job folder and the dated run folder
under pull/), as typed and after links resolve, for the path itself and every parent; and EVERYTHING is refused if the list cannot be read or holds no run row. It is a name filter, not a
content filter (a copy under another name is not caught by name; a manifest whose job_id and start minute are those of a listed run is refused too).
Use as a library: `from listed_runs_guard import refuse_listed(path)`; or as a pre-run check that changes no scorer's hash: `python3 -I listed_runs_guard.py <path> [<path> ...] && python3 -I scorer.py ...`.
The list is read from kalshi-scalper/workers/HELDOUT_PULL_RUNS.md in the repository root when it exists, else from the byte-equal copy beside this file. No network, no run is opened (only a manifest.json's job_id and start time)."""
import os, sys, json, re, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"), os.path.join(HERE, "HELDOUT_PULL_RUNS.md")]


def _load():
    """-> (path, sha256 of the bytes, runs) of the FIRST copy that holds a run row; one function so the printed hash is always that of the list used."""
    for c in CANDIDATES:
        try: raw = open(c, "rb").read()
        except OSError: continue
        runs = []
        for line in raw.decode("utf-8", "replace").split("\n"):
            cells = [x.strip().strip("`") for x in line.split("|")]
            if len(cells) > 2 and re.match(r"^[A-Za-z0-9_]+/\d{4}-\d\d-\d\dT\d{4}Z_\d+$", cells[1]): runs.append(cells[1])
        if runs: return os.path.normpath(c), hashlib.sha256(raw).hexdigest(), sorted(set(runs))
    raise SystemExit("REFUSED: kalshi-scalper/workers/HELDOUT_PULL_RUNS.md cannot be read or lists no run, so every run is refused (standing rule (h))")


def listed_source():
    """-> (path, sha256) of the list copy used."""
    return _load()[:2]


def listed_runs(): return _load()[2]


def refuse_listed(path):
    runs = listed_runs()
    for p in {os.path.abspath(path), os.path.realpath(path)}:
        parts = p.split(os.sep)
        for run in runs:
            job, stamp = run.split("/")
            if stamp in parts or (job in parts and stamp in p): raise SystemExit("REFUSED: %s is, or lies inside, the landed run %s, listed as held-out material in HELDOUT_PULL_RUNS.md" % (path, run))
    d = os.path.realpath(path)
    for _ in range(3):
        mf = os.path.join(d, "manifest.json")
        if os.path.isfile(mf):
            try: m = json.load(open(mf)); started = str(m.get("started")); job = str((m.get("job") or {}).get("job_id"))
            except Exception: raise SystemExit("REFUSED: the manifest beside %s cannot be read, so it cannot be told apart from a listed run" % path)
            for run in runs:
                j, stamp = run.split("/"); s0 = stamp.split("_")[0]
                if started == s0 and job == j: raise SystemExit("REFUSED: the manifest beside %s is that of the landed run %s (same job and start minute), listed as held-out material" % (path, run))
        d = os.path.dirname(d)


if __name__ == "__main__":
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    for a in sys.argv[1:]: refuse_listed(a)
    src, h = listed_source()
    print("listed_runs_guard: %d path(s) not in HELDOUT_PULL_RUNS.md (%d run(s) listed); list read: %s sha256 %s" % (len(sys.argv) - 1, len(listed_runs()), os.path.relpath(src), h))
