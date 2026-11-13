"""History Miner: one held-out guard for every reader of this desk (standing rule (h)), copied in logic from Idea Desk B's deskb_guard.py (a199f946).

1. A path whose part, as typed (made absolute) or after links resolve, starts HELDOUT_ is refused.
2. A path with a part EQUAL to the folder name of a landed pull run listed in kalshi-scalper/workers/HELDOUT_PULL_RUNS.md (the copy on this
   branch, kept equal to the one on main) is refused, as typed and after links resolve.
3. If that list cannot be read, or has no table header, EVERYTHING is refused.
The current folder and every command-line argument are tested. This is a name filter, not a content filter: a copy of a run under another folder
name, or one file copied out of it, is not caught, and passing it is no proof that a held-out file was not read."""
import os
import re
import sys

LIST_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "HELDOUT_PULL_RUNS.md")
ROW = re.compile(r"^\|\s*`([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)`\s*\|")


_PRINTED = set()


def listed_runs(list_file=None):
    f = list_file or LIST_FILE
    try:
        raw = open(f, "rb").read()
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        raise SystemExit("REFUSED: %s cannot be read, so no run can be shown to be clean (standing rule (h))" % f)
    if not any(ln.startswith("| Run folder") for ln in lines):
        raise SystemExit("REFUSED: %s has no table header; the list is not the file this guard expects" % f)
    if f not in _PRINTED:      # Head's rule (a): every run's log carries the sha256 of the list copy it read; a run without this line is not counted
        _PRINTED.add(f)
        sys.stderr.write("hm_guard: HELDOUT_PULL_RUNS list read, sha256 %s (%s)\n" % (__import__("hashlib").sha256(raw).hexdigest(), f))
    return {m.group(2) for m in map(ROW.match, lines) if m}


def refuse_heldout(path, list_file=None):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s lies in or resolves into a HELDOUT_ folder (standing rule (h))" % path)
    runs = listed_runs(list_file)
    for p in (os.path.abspath(path), os.path.realpath(path)):
        hit = runs.intersection(p.split(os.sep))
        if hit:
            raise SystemExit("REFUSED: %s is, or lies inside, the landed run %s, which HELDOUT_PULL_RUNS.md lists as held-out material" % (path, sorted(hit)[0]))


def refuse_all(args=None, list_file=None):
    """Call before the first open: tests the current folder and every argument."""
    refuse_heldout(os.getcwd(), list_file)
    for a in (sys.argv[1:] if args is None else args):
        if isinstance(a, str) and a and not a.startswith("-"):
            refuse_heldout(a, list_file)
