#!/usr/bin/env python3
"""Run PERPFUNDCLK1: python3 -I perpfundclk1_run.py <perp-data checkout> [m_carried]. Prints the header, then the STAGE 1 counts (funding rows only), then the verdict or the cells, then the summary.
Stage 1 counts come first and a card under 3 pooled trades a day is parked without opening a candle file. The sha256 of the whole print is committed before it is read."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perpfundclk1 as F


def main(root, carried=6290660):
    out = F.run(root, carried)
    print(json.dumps({"m_carried": out["m_carried"], "m_new": out["m_new"], "m_total": out["m_total"], "label": out["label"]}, sort_keys=True))
    print(json.dumps({"stage1": out["stage1"]}, sort_keys=True, default=str))
    if "verdict" in out:
        print(json.dumps({"verdict": out["verdict"]}, sort_keys=True))
        return
    print(json.dumps({"stage2": out["stage2"]}, sort_keys=True, default=str))
    for r in sorted(out["cells"], key=lambda r: r["cell"]):
        print(json.dumps(r, sort_keys=True, default=str))
    print(json.dumps({"bh_survivors": out["bh_survivors"], "passes": out["passes"]}, sort_keys=True, default=str))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 6290660)
