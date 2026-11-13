#!/usr/bin/env python3
"""CANDLEGAP-2 runner (History Miner, Nov 13, 2026). Runs the FROZEN candlegap.py (sha256 a7178688..., not edited) on another series by setting its module constant SERIES before
calling measure(); nothing else is changed. Usage: python3 -I candlegap2_run.py <wheelbook run folder> <SERIES> <pull folder>..."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
FROZEN = "a7178688ae3a5da635e15e06e10d94f58b47e49bc77509c90eca07eebb9124bd"
if hashlib.sha256(open(os.path.join(HERE, "candlegap.py"), "rb").read()).hexdigest() != FROZEN:
    sys.exit("refused: candlegap.py is not the frozen file")
import candlegap as G
run, series, pull = sys.argv[1], sys.argv[2], sys.argv[3:]
if series not in ("KXLIGAPROMATCH", "KXEBASKETBALLGAME"):
    sys.exit("refused: series not in CANDLEGAP-2's list")
for p in [run] + pull:
    if "HELDOUT_" in os.path.realpath(p) or "HELDOUT_" in os.path.abspath(p):
        sys.exit("refused: HELDOUT_ path")
G.SERIES = series
out = G.measure(run, pull); out["series"] = series
print(json.dumps(out, indent=1))
