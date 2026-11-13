"""Idea Desk B: one held-out folder guard for every script of this desk (standing rule (h)).
A path whose REAL path has a part starting HELDOUT_ is refused, so a link with an innocent name does not get past.
The current folder is tested too.

Since Nov 13, 2026 it also refuses any landed pull run listed in HELDOUT_PULL_RUNS.md (the copy beside this file, kept
equal to the one on main). It refuses BY THE RUN'S FOLDER NAME, as typed and after links resolve: a path with a part
equal to a listed run's folder name. A copy of the run under another folder name, or a single file copied out of it,
is NOT caught. This is a name filter, not a content filter, and it is no proof that a held-out file was not read.
If the list cannot be read, everything is refused."""
import os
import re
import sys

LIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HELDOUT_PULL_RUNS.md")
ROW = re.compile(r"^\|\s*`([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)`\s*\|")


def listed_runs():
    """Run folder names (the last part, <UTC stamp>_<run id>) of every row of the list. Unreadable list: refuse."""
    try:
        lines = open(LIST_FILE, encoding="utf-8").read().splitlines()
    except OSError:
        raise SystemExit("REFUSED: %s cannot be read, so no run can be shown to be clean (standing rule (h))" % LIST_FILE)
    if not any(ln.startswith("| Run folder") for ln in lines):
        raise SystemExit("REFUSED: %s has no table header; the list is not the file this guard expects" % LIST_FILE)
    return {m.group(2) for m in map(ROW.match, lines) if m}


def refuse_heldout(path):
    """Refuses if ANY part of the path as typed (made absolute) or of its real path starts HELDOUT_. There is no bypass:
    a held-out read is a separate, reviewed change to the one scorer that makes it."""
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s lies in or resolves into a HELDOUT_ folder (standing rule (h))" % path)
    runs = listed_runs()
    for p in (os.path.abspath(path), os.path.realpath(path)):
        hit = runs.intersection(p.split(os.sep))
        if hit:
            raise SystemExit("REFUSED: %s is, or lies inside, the landed run %s, which HELDOUT_PULL_RUNS.md lists as held-out material" % (path, sorted(hit)[0]))


def refuse_all(args=None):
    """Call before the first open or glob: tests the current folder and every command-line argument."""
    refuse_heldout(os.getcwd())
    for a in (sys.argv[1:] if args is None else args):
        if isinstance(a, str) and a and not a.startswith("-"):
            refuse_heldout(a)
