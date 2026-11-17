#!/usr/bin/env python3
"""Run CHEAPFLIP once: python3 -I cheapflip_run.py <base dir> [<base dir> ...]  (each base holds <date>/<HHMM>/book.csv.gz and coverage.csv.gz: book15r6 and nc15).
Prints the header (m_carried 7,492,484, m_new 9), the stats line, then one line per band and multiple. An owner-requested descriptive read. The sha256 of the print is committed before it is read."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cheapflip as C


def main(bases, carried=C.M_CARRIED):
    out = C.run(bases, carried)
    print(json.dumps({"m_carried": out["m_carried"], "m_new": out["m_new"], "m_total": out["m_total"], "label": out["label"]}, sort_keys=True))
    print(json.dumps({"stats": out["stats"], "windows": out["windows"]}, sort_keys=True))
    for r in out["table"]:
        print(json.dumps(r, sort_keys=True, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
