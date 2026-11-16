#!/usr/bin/env python3
"""Run a perps_grid FAMILY SPEC on Forensics' 15-name extract with the Testing Desk's second build: loader (allow line needed), the engine's split rule, my driver. Counts first, then the report.
  python3 -I perps15_second_run.py <spec.json> <dir with the two xz extracts> <prior_m>"""
import json, sys
import engine1_perps_driver_second as D
import perps15_second_load as L


def run(spec, directory, prior_m, allow_file=None, xz_sha=None, wall=None):
    series, funding, counts = L.load(directory, allow_file, xz_sha, **({} if wall is None else {"wall": wall}))
    names = [n for n in spec["data"]["ticker_wall"] if n in series]; sp = L.splits({n: series[n] for n in names})
    lines = ["counts " + json.dumps(counts, sort_keys=True), "names " + ",".join(names), "splits " + json.dumps({n: [sp[n][0], L.iso_day(sp[n][1])] for n in sorted(sp)})]
    out = D.run_spec(spec, {n: series[n] for n in sp}, {n: sp[n][2] for n in sp}, {n: funding[n] for n in sp}, prior_m)
    return lines + D.report(out), out


if __name__ == "__main__":
    for l in run(json.load(open(sys.argv[1])), sys.argv[2], int(sys.argv[3]))[0]: print(l)
