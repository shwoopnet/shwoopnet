#!/usr/bin/env python3
"""Guarded entry to the FROZEN candlegap.py (sha256 a7178688..., not edited): runs hm_guard on the current folder and every argument (HELDOUT_ parts
and the runs listed in HELDOUT_PULL_RUNS.md; an unreadable list refuses everything), then hands the same arguments to candlegap.py's own main.
Calling candlegap.py directly stays unguarded by rule (h)'s list; use this wrapper. Usage: as candlegap.py."""
import hashlib, os, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import hm_guard
hm_guard.refuse_all()
FROZEN = "a7178688ae3a5da635e15e06e10d94f58b47e49bc77509c90eca07eebb9124bd"
if hashlib.sha256(open(os.path.join(HERE, "candlegap.py"), "rb").read()).hexdigest() != FROZEN:
    sys.exit("refused: candlegap.py is not the frozen file")
sys.argv[0] = os.path.join(HERE, "candlegap.py")
runpy.run_path(sys.argv[0], run_name="__main__")
