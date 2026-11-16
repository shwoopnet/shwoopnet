#!/usr/bin/env python3
"""Run PERPSCALP2 once: python3 -I perpscalp2_run.py <perp-data checkout> [m_carried]. Prints the header (m_carried, m_new, m_total), the counts block, then one line per cell
(sorted), then the summary. The sha256 of the whole print is committed before it is read."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpscalp2 as P


def main(root, carried=6290660):
    out = P.run(root, carried)
    print(json.dumps({"m_carried": out["m_carried"], "m_new": out["m_new"], "m_total": out["m_total"], "label": out["label"]}, sort_keys=True))
    print(json.dumps({"counts": out["counts"]}, sort_keys=True, default=str))
    for r in sorted(out["cells"], key=lambda r: r["cell"]):
        print(json.dumps(r, sort_keys=True, default=str))
    print(json.dumps({"bh_survivors": out["bh_survivors"], "passes": out["passes"], "maker_only_flags": out["maker_only_flags"]}, sort_keys=True, default=str))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 6290660)
