"""Standing rule (h), version 2 (Desk A, Nov 13, 2026, on the Head of R&D's ask after Auditor B's finding): heldout_guard.py checks only HELDOUT_ folder names; a pull run folder never has one. This file ALSO refuses any run listed in HELDOUT_PULL_RUNS.md (the copy beside the workers folder; re-copy it from main when main's list changes), matched by the run folder name as typed AND after links resolve, and refuses EVERYTHING if the list cannot be read or holds no run.
NOT imported by anything yet: the DEPTH1 chain files import heldout_guard.py and are byte-frozen until the read, so the swap (import this file's refuse_heldout in place of the old one) waits for the Head and Auditor B.
  python3 -I heldout_guard_v2.py selftest"""
import os, re, sys, tempfile
LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HELDOUT_PULL_RUNS.md")
def listed_runs(list_path=None):
    try:
        text = open(list_path or LIST, encoding="utf-8").read()
    except OSError:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md cannot be read, so every folder is refused (standing rule h)")
    runs = set()
    for m in re.finditer(r"^\|\s*`([^`|]+)`", text, re.M):
        name = m.group(1).strip().strip("/")
        if "/" in name: runs.add(name)
    if not runs:
        raise SystemExit("REFUSED: HELDOUT_PULL_RUNS.md lists no run (unreadable shape), so every folder is refused (standing rule h)")
    return runs
def refuse_heldout(path, who="this reader", list_path=None):
    runs = listed_runs(list_path)
    for p in (os.path.abspath(path), os.path.realpath(path)):
        parts = [x for x in p.split(os.sep) if x]
        if any(x.upper().startswith("HELDOUT_") for x in parts):
            raise SystemExit("REFUSED (%s): %s is, or is inside, or points into, a held-out folder (standing rule h)" % (who, path))
        joined = "/".join(parts)
        for r in runs:
            leaf = r.rsplit("/", 1)[1]
            if leaf in parts or joined.endswith(r) or ("/" + r + "/") in ("/" + joined + "/"):
                raise SystemExit("REFUSED (%s): %s is, or is inside, a pull run listed in HELDOUT_PULL_RUNS.md (%s)" % (who, path, r))
def selftest():
    d = tempfile.mkdtemp(); lst = os.path.join(d, "L.md")
    open(lst, "w").write("| Run | Job |\n|---|---|\n| `JOBX/2026-11-13T0627Z_111` | JOBX |\n")
    ok = os.path.join(d, "pull", "JOBX", "2026-11-12T0000Z_222"); os.makedirs(ok)
    bad = os.path.join(d, "pull", "JOBX", "2026-11-13T0627Z_111"); os.makedirs(bad)
    link = os.path.join(d, "innocent"); os.symlink(bad, link)
    refuse_heldout(ok, list_path=lst)
    for shape, p in (("plain", bad), ("nested", os.path.join(bad, "x")), ("symlink", link), ("symlink nested", os.path.join(link, "x"))):
        try: refuse_heldout(p, list_path=lst); raise AssertionError(shape + " not refused")
        except SystemExit: pass
    cwd = os.getcwd(); os.makedirs(os.path.join(bad, "sub"), exist_ok=True); os.chdir(os.path.join(bad, "sub"))
    try:
        try: refuse_heldout(".", list_path=lst); raise AssertionError("relative '.' not refused")
        except SystemExit: pass
    finally: os.chdir(cwd)
    for shape, lp in (("missing list", os.path.join(d, "none.md")),):
        try: refuse_heldout(ok, list_path=lp); raise AssertionError(shape + " not refused")
        except SystemExit: pass
    empty = os.path.join(d, "E.md"); open(empty, "w").write("no table\n")
    try: refuse_heldout(ok, list_path=empty); raise AssertionError("empty list not refused")
    except SystemExit: pass
    h = os.path.join(d, "HELDOUT_X"); os.makedirs(h)
    try: refuse_heldout(h, list_path=lst); raise AssertionError("HELDOUT_ folder not refused")
    except SystemExit: pass
    real = listed_runs(); assert real, "real list empty"
    print("HELDOUT GUARD V2 SELFTEST OK (plain, nested, relative, symlink, nested symlink, missing list, empty list, HELDOUT_ folder); real list holds %d run(s)" % len(real))
if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]: selftest()
    else: sys.exit(__doc__)
