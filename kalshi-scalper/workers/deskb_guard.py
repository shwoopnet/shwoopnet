"""Idea Desk B: one held-out folder guard for every script of this desk (standing rule (h)).
A path whose REAL path has a part starting HELDOUT_ is refused, so a link with an innocent name does not get past.
The current folder is tested too. The one approved read sets DESKB_HELDOUT=READ-ONCE by hand."""
import os
import sys


def refuse_heldout(path):
    real = os.path.realpath(path)
    if any(part.upper().startswith("HELDOUT_") for part in real.split(os.sep)) and os.environ.get("DESKB_HELDOUT") != "READ-ONCE":
        raise SystemExit("REFUSED: %s resolves into a HELDOUT_ folder (standing rule (h))" % path)


def refuse_all(args=None):
    """Call before the first open or glob: tests the current folder and every command-line argument."""
    refuse_heldout(os.getcwd())
    for a in (sys.argv[1:] if args is None else args):
        if isinstance(a, str) and a and not a.startswith("-"):
            refuse_heldout(a)
