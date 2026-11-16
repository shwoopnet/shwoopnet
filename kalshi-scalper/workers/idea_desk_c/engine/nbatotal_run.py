#!/usr/bin/env python3
"""Run NBATOTAL once: python3 -I nbatotal_run.py <root> <m_carried>. Prints counts first. The print's sha256 is committed before it is read."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbatotal as N

if __name__ == "__main__":
    print(json.dumps(N.run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0), indent=1, sort_keys=True, default=str))
